"""Algorithme génétique (AG) pour le FJSP avec maintenance.

Principe : on fait évoluer une population de solutions (OS, MS).
  - sélection par tournoi binaire (on tire 2 solutions, on garde la meilleure) ;
  - croisement POX sur OS (on garde les positions d'un sous-ensemble de jobs du parent 1 et on
    complète dans l'ordre du parent 2) et croisement uniforme sur MS ;
  - mutation : échange de deux positions dans OS, réaffectation de quelques machines ;
  - élitisme : les meilleures solutions passent telles quelles à la génération suivante.
S'arrête quand le budget est épuisé : secondes, ou nombre d'évaluations (voir codage.Budget).
"""
import time
import numpy as np
from .codage import decoder, machines_eligibles, solution_aleatoire, Budget

PARAMS_DEFAUT = dict(population=60, p_croisement=0.8, p_mutation=0.1, elite=2)


def croisement_pox(p1, p2, rng, n_jobs):
    garder = set(rng.choice(n_jobs, max(1, n_jobs // 2), replace=False).tolist())
    enfant = [j if j in garder else None for j in p1]
    reste = iter([j for j in p2 if j not in garder])
    return [j if j is not None else next(reste) for j in enfant]


def resoudre(inst, budget, rng, depart=None, population=60, p_croisement=0.8, p_mutation=0.1,
             elite=2):
    budget = Budget.depuis(budget)
    elig = machines_eligibles(inst)
    pop = [(list(depart[0]), np.array(depart[1]))] if depart is not None else []
    while len(pop) < population:
        pop.append(solution_aleatoire(inst, rng, elig))
    cout = [decoder(inst, os, ms)[0] for os, ms in pop]
    budget.compter(len(pop))
    b = int(np.argmin(cout))
    meilleur, meilleur_cout = (list(pop[b][0]), pop[b][1].copy()), cout[b]
    generations = 0
    while not budget.fini():
        ordre = np.argsort(cout)
        nouvelle = [(list(pop[i][0]), pop[i][1].copy()) for i in ordre[:elite]]
        while len(nouvelle) < population:
            a, c = (min(rng.choice(population, 2, replace=False), key=lambda i: cout[i]) for _ in range(2))
            (os1, ms1), (os2, ms2) = pop[a], pop[c]
            if rng.random() < p_croisement:
                os_e = croisement_pox(os1, os2, rng, inst.n)
                ms_e = np.where(rng.random(inst.n_ops) < 0.5, ms1, ms2)
            else:
                os_e, ms_e = list(os1), ms1.copy()
            if rng.random() < p_mutation:
                i, k = rng.choice(len(os_e), 2, replace=False)
                os_e[i], os_e[k] = os_e[k], os_e[i]
            for o in np.flatnonzero(rng.random(inst.n_ops) < p_mutation / 2):
                ms_e[o] = rng.choice(elig[o])
            nouvelle.append((os_e, ms_e))
        pop = nouvelle
        cout = [decoder(inst, os, ms)[0] for os, ms in pop]
        budget.compter(len(pop))
        generations += 1
        b = int(np.argmin(cout))
        if cout[b] < meilleur_cout:
            meilleur_cout, meilleur = cout[b], (list(pop[b][0]), pop[b][1].copy())
    return meilleur_cout, meilleur, dict(generations=generations, **budget.bilan())
