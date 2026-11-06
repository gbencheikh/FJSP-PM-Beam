"""Codage commun aux métaheuristiques (FJSP avec maintenance, régime faisable).

Une solution = deux listes :
  OS (ordre des opérations) : liste de numéros de jobs ; le job j apparaît autant de fois qu'il a
       d'opérations. La k-ième apparition de j désigne sa k-ième opération.
       Exemple Kacem1 : [2, 0, 3, 0, 1, ...] = op1 du job 2, op1 du job 0, op1 du job 3, op2 du job 0...
  MS (affectation machine) : MS[o] = machine choisie pour l'opération o (numéro global d'opération).

Décodage (transformer OS + MS en planning) : on place les opérations dans l'ordre de OS, chacune le
plus tôt possible (après l'opération précédente de son job et après la fin de sa machine). Si
l'opération ne tient pas dans la marge d'usure de la machine (T_k - c_k), on insère d'abord une
maintenance préventive (durée M_k) dès que la machine est libre, ce qui remet l'usure à 0.
Le résultat respecte toutes les règles du simulateur : aucune panne.
"""
import os
import numpy as np

EPS = 1e-9


def decoder(inst, OS, MS, avec_planning=False):
    """Retourne (C_max, nombre de maintenances[, planning])."""
    P, T, M = inst.P, inst.T, inst.M
    prochaine = [0] * inst.n          # prochaine opération de chaque job
    fin_job = [0.0] * inst.n          # date de fin de la dernière opération du job
    fin_machine = [0.0] * inst.m      # date à laquelle la machine est libre
    usure = [0.0] * inst.m
    n_pm, cmax = 0, 0.0
    planning = [] if avec_planning else None
    for j in OS:
        o = inst.job_ops[j][prochaine[j]]
        prochaine[j] += 1
        k = MS[o]
        p = P[o, k]
        if usure[k] + p > T[k] + EPS:               # ne tient pas : maintenance d'abord
            debut_pm = fin_machine[k]
            fin_machine[k] = debut_pm + M[k]
            usure[k] = 0.0
            n_pm += 1
            if avec_planning:
                planning.append((k, debut_pm, fin_machine[k], 2, -1))
        debut = max(fin_job[j], fin_machine[k])
        fin = debut + p
        fin_job[j] = fin_machine[k] = fin
        usure[k] += p
        cmax = max(cmax, fin)
        if avec_planning:
            planning.append((k, debut, fin, 1, j))
    return (cmax, n_pm, planning) if avec_planning else (cmax, n_pm)


def decoder_actif(inst, OS, MS, avec_planning=False):
    """Décodeur ACTIF (3e relecture, R1 ; déclaré le 04/11/2026, campagne A1) : chaque opération, dans l'ordre de OS,
    est placée au plus tôt sur sa machine, y compris dans un trou entre deux activités déjà placées, si elle y tient après
    la fin de son prédécesseur de job ET si la charge du segment d'usure (entre deux maintenances) qui contient le trou,
    augmentée de sa durée, reste <= T_k (alors aucune opération du segment ne dépasse le seuil). Sinon elle est placée en
    fin de machine, avec une maintenance juste avant si le dernier segment déborde (comme le décodeur semi-actif)."""
    P, T, M = inst.P, inst.T, inst.M
    prochaine = [0] * inst.n
    fin_job = [0.0] * inst.n
    act = [[] for _ in range(inst.m)]        # (début, fin, type, segment, job)
    charge = [[0.0] for _ in range(inst.m)]
    n_pm, cmax = 0, 0.0
    for j in OS:
        o = inst.job_ops[j][prochaine[j]]
        prochaine[j] += 1
        k = MS[o]
        p = float(P[o, k])
        r = fin_job[j]
        L = act[k]
        place, prec_fin, seg = None, 0.0, 0
        for i, (s, e, typ, sg, _) in enumerate(L):
            d = max(r, prec_fin)
            seg_trou = sg if typ == 1 else seg      # un trou avant une maintenance appartient au segment courant
            if d + p <= s + EPS and charge[k][seg_trou] + p <= T[k] + EPS:
                place = (i, d, seg_trou)
                break
            prec_fin = e
            seg = sg + 1 if typ == 2 else sg
        if place is None:
            seg = len(charge[k]) - 1
            libre = L[-1][1] if L else 0.0
            if charge[k][seg] + p > T[k] + EPS:
                L.append((libre, libre + float(M[k]), 2, seg, -1))
                n_pm += 1
                charge[k].append(0.0)
                seg += 1
                libre += float(M[k])
            d = max(r, libre)
            L.append((d, d + p, 1, seg, j))
        else:
            i, d, seg = place
            L.insert(i, (d, d + p, 1, seg, j))
        charge[k][seg] += p
        fin_job[j] = d + p
        cmax = max(cmax, d + p)
    if avec_planning:
        planning = [(k, s, e, typ, jj) for k in range(inst.m) for (s, e, typ, _, jj) in act[k]]
        return cmax, n_pm, planning
    return cmax, n_pm


# Choix du décodeur pour TOUTES les métaheuristiques (variable lue à l'import ; défaut : semi-actif, protocole de l'article)
decoder_semi_actif = decoder
if os.environ.get("FJSP_DECODEUR") == "actif":
    decoder = decoder_actif


def machines_eligibles(inst):
    return [np.flatnonzero(inst.P[o] > 0) for o in range(inst.n_ops)]


def solution_aleatoire(inst, rng, elig=None):
    elig = elig or machines_eligibles(inst)
    OS = [j for j, ops in enumerate(inst.job_ops) for _ in ops]
    rng.shuffle(OS)
    # moitié des opérations sur leur machine la plus rapide, moitié au hasard
    MS = np.array([e[np.argmin(inst.P[o, e])] if rng.random() < 0.5 else rng.choice(e)
                   for o, e in enumerate(elig)])
    return list(OS), MS


def depuis_planning(inst, planning):
    """Convertit un planning (heuristique, agent) en (OS, MS) pour démarrer une recherche."""
    ops = sorted([s for s in planning if s[3] == 1], key=lambda s: (s[1], s[0]))
    OS, MS, compteur = [], np.zeros(inst.n_ops, dtype=int), [0] * inst.n
    for k, debut, fin, typ, j in ops:
        o = inst.job_ops[j][compteur[j]]
        compteur[j] += 1
        MS[o] = k
        OS.append(j)
    return OS, MS


def voisin(inst, OS, MS, rng, elig):
    """Un voisin au hasard : déplacer une opération dans OS, ou changer la machine d'une opération.
    Retourne (OS', MS', attribut du mouvement) ou None si le mouvement est neutre."""
    if rng.random() < 0.5:
        i, k = rng.choice(len(OS), 2, replace=False)
        if OS[i] == OS[k]:
            return None
        OS2 = list(OS)
        j = OS2.pop(i)
        OS2.insert(k, j)
        return OS2, MS, ("deplacement", j, int(k))
    o = int(rng.integers(inst.n_ops))
    if len(elig[o]) < 2:
        return None
    k = int(rng.choice(elig[o]))
    if k == MS[o]:
        return None
    MS2 = MS.copy()
    MS2[o] = k
    return OS, MS2, ("machine", o, k)


class Budget:
    """Critère d'arrêt commun : un temps (secondes) OU un nombre d'évaluations (plannings décodés).

    Le budget en évaluations donne le même résultat sur n'importe quel ordinateur (et que les
    calculs tournent en série ou en parallèle) : c'est celui à privilégier pour une comparaison
    publiée. Le budget en secondes dépend de la vitesse de la machine.
    """

    def __init__(self, secondes=None, evaluations=None):
        assert (secondes is None) != (evaluations is None), "donner secondes OU evaluations"
        import time
        self.secondes, self.evaluations = secondes, evaluations
        self._time = time.time
        self.t0 = time.time()
        self.n = 0

    @staticmethod
    def depuis(budget):
        """Accepte un Budget ou un nombre de secondes (compatibilité)."""
        return budget if isinstance(budget, Budget) else Budget(secondes=float(budget))

    def compter(self, n=1):
        self.n += n

    def fraction(self):
        if self.evaluations is not None:
            return min(1.0, self.n / self.evaluations)
        return min(1.0, (self._time() - self.t0) / self.secondes)

    def fini(self):
        return self.fraction() >= 1.0

    def bilan(self):
        return dict(evaluations=self.n, temps_s=self._time() - self.t0)
