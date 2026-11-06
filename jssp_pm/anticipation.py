"""Agent qui anticipe : réseau + moteur rapide, recherche en faisceau avec élagage (branch and bound tronqué).

Principe (arbre de décisions = situations de l'atelier, branches = actions) :
  - on garde en parallèle les B meilleures pistes (le « faisceau ») ;
  - pour chaque piste, le RÉSEAU propose ses K actions les plus probables (K = 0 : toutes les actions) ;
  - le MOTEUR RAPIDE termine le planning après chaque action (règle MWKR+EFT+PM) : c'est une
    estimation du C_max de la branche, et en même temps un planning complet valide ;
  - on garde les B branches les mieux estimées, puis on recommence à la décision suivante.

Élagage :
  - borne supérieure = meilleur planning complet vu jusqu'ici (issu d'une complétion ou d'une piste
    terminée) ; une branche dont la borne inférieure l'atteint déjà est abandonnée ;
  - dominance : deux pistes qui mènent à la même situation (mêmes décisions dans un autre ordre,
    p. ex. lancer A puis B ou B puis A au même instant) ne sont gardées qu'une fois.

Résultat : le meilleur planning complet rencontré. stats["t_coupure"] = instant à partir duquel ce
planning suit la règle du moteur (inf si la recherche l'a construit jusqu'au bout). Budget = nombre de complétions du moteur
(comparable aux « évaluations » des métaheuristiques).
B = 1, K = 1 : l'agent glouton habituel, avec en plus le meilleur planning complété en route.
"""
import copy
import time
import numpy as np
import torch

from .fjsp_env3 import FJSPEnv3
from .moteur_rapide import MoteurRapide

EPS = 1e-9


def cloner(env):
    """Copie d'un environnement (l'instance est partagée, pas copiée)."""
    e = copy.copy(env)
    e.sim = copy.deepcopy(env.sim, memo={id(env.inst): env.inst})
    e._C = list(env._C)
    return e


def cle(e):
    """Signature d'une situation (pour repérer les doublons)."""
    return (e.t, e.nxt.tobytes(), np.round(e.mf, 6).tobytes(), np.round(e.us, 6).tobytes(),
            np.round(e.jr, 6).tobytes())


class AgentAnticipation:
    def __init__(self, net=None, largeur=5, k=4, regles=("MWKR",), mode="full", elagage=True, doublons=True,
                 filtre=None, departage=None):
        """net=None : pas de réseau, toutes les actions sont évaluées par le moteur (k ignoré), sauf si filtre est donné.
        filtre (révision du 27/10/2026, contrôle « filtre non appris ») : net=None et les K actions gardées par piste
        sont choisies par une règle au lieu du réseau :
          "regle" : priorité du moteur de complétion (MWKR, puis fin au plus tôt ; maintenance classée comme le job
                    qu'elle débloque si la machine est la machine EFT de ce job et doit être maintenue avant ; attente en dernier) ;
          "fin"   : fin au plus tôt de l'action (lancement : t + p ; maintenance : t + M_k ; attente en dernier) ;
          "borne" : borne inférieure (moteur_rapide.borne_inf) de la situation obtenue après l'action.
        Le départage du classement des enfants n'utilise alors aucune probabilité (comme sans réseau).
        elagage=False : pas d'abandon des branches par borne inférieure (ablation).
        doublons=False : pas de suppression des situations identiques (ablation)."""
        self.net, self.B, self.K, self.regles, self.mode = net, largeur, k, tuple(regles), mode
        self.elagage, self.doublons = elagage, doublons
        assert filtre in (None, "regle", "fin", "borne") and (filtre is None or net is None)
        self.filtre = filtre
        # Départage des ex aequo sur H à la sélection (relecteur indépendant, M4 ; ablation B1 déclarée le 04/11/2026) :
        #   None   : comportement de l'article (réseau : log-probabilité cumulée ; filtre simple : ordre de génération)
        #   "ordre": ordre de génération, aussi avec le réseau
        #   "rang" : filtre simple départagé par son rang cumulé (somme des rangs des actions choisies dans son classement)
        assert departage in (None, "ordre", "rang") and not (departage == "rang" and filtre is None)
        self.departage = departage

    def _scores_filtre(self, e, et, mr):
        """Score (plus grand = meilleur) de chaque candidat de e._C pour le filtre non appris."""
        C, sim, inst = e._C, e.sim, e.inst
        t = float(sim.t)
        BAS = -1e18
        sc = np.full(len(C), BAS)
        if self.filtre == "borne":
            for a, c in enumerate(C):
                sc[a] = -mr.borne_inf(mr.appliquer(et, c))
            return sc
        # « regle » : JIT, la maintenance prend la priorité du job dont la machine EFT doit être maintenue
        pm_prio = {}
        if self.filtre == "regle":
            from .fjsp_env3 import eft_choice
            for j in sim.ready_jobs():
                k, besoin = eft_choice(e, j)
                if besoin:
                    pm_prio[k] = max(pm_prio.get(k, BAS), float(e.suffix[j][sim.next_op[j]]))
        for a, (typ, j, k) in enumerate(C):
            if typ == "D":
                o = sim.cur_op(j)
                fin = t + float(inst.P[o, k])
                sc[a] = (float(e.suffix[j][sim.next_op[j]]) * 1e6 - fin) if self.filtre == "regle" else -fin
            elif typ == "P":
                if self.filtre == "regle":
                    sc[a] = pm_prio[k] * 1e6 - (t + float(inst.M[k])) if k in pm_prio else BAS / 2
                else:
                    sc[a] = -(t + float(inst.M[k]))
        return sc

    @torch.no_grad()
    def _logp(self, envs):
        if self.net is None:
            return [np.zeros(len(e._C)) for e in envs]
        logits, _ = self.net(*self.net.collate([self.net.observe(e) for e in envs]))
        out = []
        for i, e in enumerate(envs):
            l = logits[i, :len(e._C)]
            out.append(torch.log_softmax(l, -1).numpy())
        return out

    def planifier(self, inst):
        """Retourne (C_max, planning [(k, début, fin, type, job)], statistiques)."""
        t0 = time.time()
        mr = MoteurRapide(inst)
        env0 = FJSPEnv3(self.mode, safety=True)
        env0.reset(inst)
        meilleur, plan, t_coupure = np.inf, None, np.inf
        n_eval = n_elag = n_doublons = n_exam = n_enfants = 0
        n_elag_subst = n_elag_egal = 0
        n_coupures = n_egal_coupure = 0          # diagnostic E6b seulement (aucun effet sur la recherche)
        # « meilleur » ci-dessous = incumbent au moment de la coupure (certificat), jamais le meilleur final
        faisceau = [(env0, 0.0)]
        while faisceau:
            envs = [e for e, _ in faisceau]
            logps = self._logp(envs)
            enfants = []
            for i, (e, lp) in enumerate(faisceau):
                C = e._C
                lpi = logps[i]
                et = mr.etat(e)
                if self.filtre is not None and self.K > 0 and len(C) > self.K:
                    choix = np.argsort(-self._scores_filtre(e, et, mr), kind="stable")[:self.K]
                    if self.departage == "rang":           # « log-probabilité » fictive = − rang dans le classement du filtre
                        lpi = np.zeros(len(C))
                        lpi[choix] = -np.arange(len(choix), dtype=float)
                elif self.net is None or self.K <= 0 or len(C) <= self.K:
                    choix = range(len(C))
                else:
                    choix = np.argsort(-lpi)[:self.K]
                for a in choix:
                    vals = [mr.completer(et, C[a], r) for r in self.regles]
                    n_eval += len(vals)
                    c = min(vals)
                    if c < meilleur - EPS:          # nouveau meilleur planning complet
                        r = self.regles[int(np.argmin(vals))]
                        _, segs = mr.completer(et, C[a], r, avec_planning=True)
                        meilleur, plan = c, list(e.sim.segments) + et.engages + segs
                        t_coupure = e.sim.t          # après cet instant, le planning suit la règle du moteur
                    cle_dep = 0.0 if self.departage == "ordre" else -(lp + lpi[a])
                    enfants.append((c, cle_dep, i, int(a)))
            enfants.sort()
            # fréquence des ex aequo à la coupure : l'enfant classé B-ième et le suivant ont-ils le même H ?
            if len(enfants) > self.B:
                n_coupures += 1
                n_egal_coupure += abs(enfants[self.B - 1][0] - enfants[self.B][0]) <= EPS
            n_enfants += len(enfants)
            nouveau, vus = [], set()
            elag_niveau = 0
            for c, mlp, i, a in enfants:
                if len(nouveau) >= self.B:
                    break
                n_exam += 1                          # enfant examiné pour entrer dans le faisceau
                e2 = cloner(faisceau[i][0])
                e2.step(a)
                if e2.sim.done():
                    cm = e2.sim.last_completion
                    if cm < meilleur - EPS:
                        meilleur, plan, t_coupure = cm, list(e2.sim.segments), np.inf
                    continue
                et2 = mr.etat(e2)
                k2 = cle(et2)
                if self.doublons and k2 in vus:
                    n_doublons += 1
                    continue
                vus.add(k2)
                if self.elagage:
                    lb = mr.borne_inf(et2)
                    if lb >= meilleur - EPS:
                        n_elag += 1
                        elag_niveau += 1
                        if lb <= meilleur + EPS:     # borne = meilleur connu : la branche peut au mieux l'égaler
                            n_elag_egal += 1
                        continue
                nouveau.append((e2, -mlp))
            # élagués dont la place a été prise par un enfant moins bien classé (sinon : faisceau simplement plus étroit)
            n_elag_subst += min(elag_niveau, max(0, len(nouveau) + elag_niveau - self.B))
            faisceau = nouveau
        stats = dict(evaluations=n_eval, elagages=n_elag, doublons=n_doublons, examines=n_exam, enfants=n_enfants,
                     elagues_remplaces=n_elag_subst, elagues_borne_egale=n_elag_egal,
                     coupures=n_coupures, egalites_coupure=n_egal_coupure,
                     temps_s=time.time() - t0,
                     t_coupure=float(t_coupure))
        return float(meilleur), plan, stats
