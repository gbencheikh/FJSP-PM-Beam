"""Recuit simulé pour le FJSP avec maintenance.

Principe : on part d'une solution et on tire un voisin au hasard (déplacer une opération dans OS ou
changer sa machine). S'il est meilleur, on l'accepte. S'il est moins bon de Δ, on l'accepte quand
même avec la probabilité exp(-Δ / température). La température baisse au fil du temps : au début on
explore beaucoup (on accepte souvent des dégradations), à la fin on n'accepte presque plus que des
améliorations.

Température initiale : calibrée pour qu'une dégradation « moyenne » soit acceptée avec une
probabilité p0 (0,5 par défaut) au départ. Refroidissement géométrique indexé sur l'avancement du
budget f ∈ [0, 1] (temps écoulé ou évaluations faites) : T = T0 · (T_fin / T0)^f, T_fin = T0 / 1000.
"""
import math
import time
import numpy as np
from .codage import decoder, machines_eligibles, solution_aleatoire, voisin, Budget

PARAMS_DEFAUT = dict(p0=0.5, ratio_fin=1e-3)


def calibrer_temperature(inst, OS, MS, cout, rng, elig, p0, n=100):
    degr = []
    for _ in range(n):
        v = voisin(inst, OS, MS, rng, elig)
        if v is None:
            continue
        d = decoder(inst, v[0], v[1])[0] - cout
        if d > 0:
            degr.append(d)
    moyenne = np.mean(degr) if degr else 1.0
    return -moyenne / math.log(p0)


def resoudre(inst, budget, rng, depart=None, p0=0.5, ratio_fin=1e-3):
    budget = Budget.depuis(budget)
    elig = machines_eligibles(inst)
    OS, MS = (list(depart[0]), np.array(depart[1])) if depart is not None else solution_aleatoire(inst, rng, elig)
    cout = decoder(inst, OS, MS)[0]
    meilleur, meilleur_cout = (list(OS), MS.copy()), cout
    T0 = calibrer_temperature(inst, OS, MS, cout, rng, elig, p0)
    it = acceptes = vides = 0
    while not budget.fini() and vides < 10000:
        temperature = T0 * ratio_fin ** budget.fraction()
        v = voisin(inst, OS, MS, rng, elig)
        if v is None:
            vides += 1          # garde-fou : instance sans voisin utile
            continue
        vides = 0
        it += 1
        c = decoder(inst, v[0], v[1])[0]
        budget.compter()
        d = c - cout
        if d <= 0 or rng.random() < math.exp(-d / max(temperature, 1e-12)):
            OS, MS, cout = v[0], np.array(v[1]), c
            acceptes += 1
            if cout < meilleur_cout:
                meilleur_cout, meilleur = cout, (list(OS), MS.copy())
    return meilleur_cout, meilleur, dict(iterations=it, acceptes=acceptes, T0=T0, **budget.bilan())
