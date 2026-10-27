"""Règles de priorité (dispatching) pour le FJSP avec maintenance.

Une règle de priorité construit le planning pas à pas, sans recherche : à chaque instant où une
machine se libère, on regarde les opérations prêtes (celles dont l'opération précédente du job est
terminée) et on choisit :
  1. QUELLE opération lancer, avec une règle d'opération (SPT, LPT, MWKR, ...) ;
  2. SUR QUELLE machine, avec une règle de machine (EFT ou machine la plus rapide).
Maintenance : règle « juste à temps » identique pour toutes. Si l'opération choisie ne tient pas
dans la marge d'usure de la machine (T_k - c_k), on lance d'abord une maintenance préventive sur
cette machine, puis l'opération dès la fin de la maintenance. Aucune panne ne peut se produire.

Règles d'opération (plus petite clé = plus prioritaire) :
  SPT   Shortest Processing Time      : plus petite durée (sur sa machine la plus rapide)
  LPT   Longest Processing Time       : plus grande durée
  MWKR  Most Work Remaining           : job avec le plus de travail restant (durées minimales)
  LWKR  Least Work Remaining          : job avec le moins de travail restant
  MOR   Most Operations Remaining     : job avec le plus d'opérations restantes
  LOR   Least Operations Remaining    : job avec le moins d'opérations restantes
  FIFO  First In First Out            : opération prête depuis le plus longtemps
  WSPT  Weighted SPT                  : durée / poids du job. Les fichiers .fjs n'ont pas de poids :
                                        par défaut poids = 1 (identique à SPT) ; passez `poids=`.
Règles de machine :
  EFT   Earliest Finish Time : machine qui finira l'opération le plus tôt (attente + maintenance
        éventuelle + durée) ;
  SPTM  machine la plus rapide pour cette opération.
"""
import numpy as np
from jssp_pm.fjsp_env3 import FJSPEnv3
from jssp_pm.simulator import IDLE, PM, EPS


def _pmin(env, j):
    o = env.sim.cur_op(j)
    row = env.inst.P[o]
    return row[row > 0].min()


REGLES_OPERATION = {
    "SPT": lambda env, j, poids: _pmin(env, j),
    "LPT": lambda env, j, poids: -_pmin(env, j),
    "MWKR": lambda env, j, poids: -env.suffix[j][env.sim.next_op[j]],
    "LWKR": lambda env, j, poids: env.suffix[j][env.sim.next_op[j]],
    "MOR": lambda env, j, poids: -(env.sim.nops_job[j] - env.sim.next_op[j]),
    "LOR": lambda env, j, poids: env.sim.nops_job[j] - env.sim.next_op[j],
    "FIFO": lambda env, j, poids: env.sim.job_free_since[j],
    "WSPT": lambda env, j, poids: _pmin(env, j) / (poids[j] if poids is not None else 1.0),
}


def machine_eft(env, j):
    sim, inst = env.sim, env.inst
    o = sim.cur_op(j)
    el = np.flatnonzero(inst.P[o] > 0)
    usure = sim.wears()
    marge = np.where(sim.status == PM, inst.T, inst.T - usure)
    attente = np.where(sim.status != IDLE, sim.end - sim.t, 0.0)
    p = inst.P[o, el]
    fin = attente[el] + np.where(p > marge[el] + EPS, inst.M[el], 0.0) + p
    return int(el[np.argmin(fin)])


def machine_plus_rapide(env, j):
    o = env.sim.cur_op(j)
    row = env.inst.P[o]
    el = np.flatnonzero(row > 0)
    return int(el[np.argmin(row[el])])


REGLES_MACHINE = {"EFT": machine_eft, "SPTM": machine_plus_rapide}


class ReglePriorite:
    """Politique « règle d'opération + règle de machine », utilisable avec run3()."""

    def __init__(self, regle_op="SPT", regle_machine="EFT", poids=None):
        self.cle = REGLES_OPERATION[regle_op]
        self.choix_machine = REGLES_MACHINE[regle_machine]
        self.poids = poids
        self.name = f"{regle_op}+{regle_machine}"

    def act(self, env):
        idx = {c: i for i, c in enumerate(env._C)}
        prets = sorted(env.sim.ready_jobs(), key=lambda j: (self.cle(env, j, self.poids), j))
        for j in prets:
            k = self.choix_machine(env, j)
            if env.sim.status[k] != IDLE:
                continue                                   # la machine choisie est occupée : attendre
            if ("D", j, k) in idx:
                return idx[("D", j, k)]                    # l'opération tient : on la lance
            if ("J", j, k) in idx:
                return idx[("J", j, k)]                    # maintenance puis opération
        if ("W", -1, -1) in idx:
            return idx[("W", -1, -1)]                      # rien à lancer : avancer le temps
        return 0


def environnement():
    """Environnement en mode « dispatch seul » : la maintenance suit la règle juste à temps."""
    return FJSPEnv3("dispatch_only", safety=True)
