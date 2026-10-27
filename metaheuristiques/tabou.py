"""Recherche tabou pour le FJSP avec maintenance.

Principe : on part d'une solution et, à chaque itération, on examine un échantillon de voisins
(déplacer une opération dans OS, ou changer sa machine). On va vers le MEILLEUR voisin, même s'il est
moins bon que la solution actuelle (ce qui permet de sortir des optimums locaux). Pour ne pas
revenir en arrière, le mouvement effectué devient « tabou » pendant `tenure` itérations, sauf s'il
mène à une solution meilleure que la meilleure jamais trouvée (critère d'aspiration).
"""
import time
import numpy as np
from .codage import decoder, machines_eligibles, solution_aleatoire, voisin, Budget

PARAMS_DEFAUT = dict(n_voisins=40, tenure=12)


def resoudre(inst, budget, rng, depart=None, n_voisins=40, tenure=12):
    budget = Budget.depuis(budget)
    elig = machines_eligibles(inst)
    OS, MS = (list(depart[0]), np.array(depart[1])) if depart is not None else solution_aleatoire(inst, rng, elig)
    cout = decoder(inst, OS, MS)[0]
    meilleur, meilleur_cout = (list(OS), MS.copy()), cout
    tabous, it, vides = {}, 0, 0
    while not budget.fini() and vides < 1000:
        it += 1
        choix = None
        for _ in range(n_voisins):
            v = voisin(inst, OS, MS, rng, elig)
            if v is None:
                continue
            os2, ms2, attr = v
            c = decoder(inst, os2, ms2)[0]
            budget.compter()
            est_tabou = tabous.get(attr, -1) >= it
            if (not est_tabou or c < meilleur_cout) and (choix is None or c < choix[0]):
                choix = (c, os2, ms2, attr)
        if choix is None:
            vides += 1          # garde-fou : aucun voisin utile
            continue
        vides = 0
        cout, OS, MS, attr = choix
        MS = np.array(MS)
        tabous[attr] = it + tenure
        if cout < meilleur_cout:
            meilleur_cout, meilleur = cout, (list(OS), MS.copy())
    return meilleur_cout, meilleur, dict(iterations=it, **budget.bilan())
