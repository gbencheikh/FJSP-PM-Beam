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
    def __init__(self, net=None, largeur=5, k=4, regles=("MWKR",), mode="full", elagage=True, doublons=True):
        """net=None : pas de réseau, toutes les actions sont évaluées par le moteur (k ignoré).
        elagage=False : pas d'abandon des branches par borne inférieure (ablation).
        doublons=False : pas de suppression des situations identiques (ablation)."""
        self.net, self.B, self.K, self.regles, self.mode = net, largeur, k, tuple(regles), mode
        self.elagage, self.doublons = elagage, doublons

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
        n_elag_subst = n_elag_egal = 0          # diagnostic E6b seulement (aucun effet sur la recherche)
        # « meilleur » ci-dessous = incumbent au moment de la coupure (certificat), jamais le meilleur final
        faisceau = [(env0, 0.0)]
        while faisceau:
            envs = [e for e, _ in faisceau]
            logps = self._logp(envs)
            enfants = []
            for i, (e, lp) in enumerate(faisceau):
                C = e._C
                lpi = logps[i]
                if self.net is None or self.K <= 0 or len(C) <= self.K:
                    choix = range(len(C))
                else:
                    choix = np.argsort(-lpi)[:self.K]
                et = mr.etat(e)
                for a in choix:
                    vals = [mr.completer(et, C[a], r) for r in self.regles]
                    n_eval += len(vals)
                    c = min(vals)
                    if c < meilleur - EPS:          # nouveau meilleur planning complet
                        r = self.regles[int(np.argmin(vals))]
                        _, segs = mr.completer(et, C[a], r, avec_planning=True)
                        meilleur, plan = c, list(e.sim.segments) + et.engages + segs
                        t_coupure = e.sim.t          # après cet instant, le planning suit la règle du moteur
                    enfants.append((c, -(lp + lpi[a]), i, int(a)))
            enfants.sort()
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
                     temps_s=time.time() - t0,
                     t_coupure=float(t_coupure))
        return float(meilleur), plan, stats
