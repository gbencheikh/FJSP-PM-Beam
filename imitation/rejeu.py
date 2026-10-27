"""Rejouer un planning « expert » (issu d'une métaheuristique) dans l'environnement RL.

Un planning expert donne, pour chaque machine, une suite ordonnée d'éléments : opérations et
maintenances. On le rejoue décision par décision dans l'environnement v3 (mode « full ») :

  à chaque décision, les actions « conformes à l'expert » sont :
    - lancer (j, k) si l'opération courante du job j est le prochain élément de la machine k ;
    - maintenance sur k si le prochain élément de k est une maintenance ;
  s'il n'y en a aucune, l'action conforme est ATTENDRE (l'expert laisse la machine libre).

Toutes les actions conformes mènent au même planning final (elles portent sur des machines
différentes et seront toutes lancées au même instant) : on les garde toutes comme « bonnes
réponses » (apprentissage avec plusieurs étiquettes). Le planning rejoué respecte les mêmes
séquences par machine : son C_max est inférieur ou égal à celui de l'expert (au plus tôt).

Résultat : une liste de (observation du réseau, indices des actions conformes) = la « leçon ».
"""
import numpy as np

from jssp_pm.simulator import IDLE, EPS


def sequences(inst, planning):
    """Planning [(k, début, fin, type, job)] -> séquence d'éléments (début, type, job, op) par machine."""
    compteur = [0] * inst.n
    seq = [[] for _ in range(inst.m)]
    for k, a, b, typ, j in sorted(planning, key=lambda s: (s[1], s[0])):
        if typ == 1:
            o = inst.job_ops[j][compteur[j]]
            compteur[j] += 1
            seq[k].append((a, 1, j, o))
        elif typ == 2:
            seq[k].append((a, 2, -1, -1))
    return seq


def rejouer(env, inst, planning, observer=None, seed=0):
    """Rejoue le planning. observer(env) -> observation (ou None pour ne rien enregistrer).
    Retourne (leçon, C_max rejoué, nombre de pannes)."""
    assert env.mode == "full", "le rejeu est écrit pour le mode full"
    env.reset(inst, np.random.default_rng(seed))
    sim = env.sim
    seq = sequences(inst, planning)
    ptr = [0] * inst.m
    lecon = []
    while not sim.done():
        C = env._C
        pos = {c: i for i, c in enumerate(C)}
        conformes = []
        for k in range(inst.m):
            if sim.status[k] != IDLE:
                continue
            # une maintenance devenue inutile (usure nulle) est sautée
            while ptr[k] < len(seq[k]) and seq[k][ptr[k]][1] == 2 and not sim.can_pm(k):
                ptr[k] += 1
            if ptr[k] >= len(seq[k]):
                continue
            _, typ, j, o = seq[k][ptr[k]]
            if typ == 2 and ("P", -1, k) in pos:
                conformes.append(pos[("P", -1, k)])
            elif typ == 1 and not sim.job_finished(j) and sim.cur_op(j) == o and ("D", j, k) in pos:
                conformes.append(pos[("D", j, k)])
        if not conformes:
            if ("W", -1, -1) not in pos:
                raise RuntimeError("rejeu bloqué : planning expert incohérent avec l'environnement")
            conformes = [pos[("W", -1, -1)]]
        if observer is not None:
            lecon.append((observer(env), conformes))
        typ, j, k = C[conformes[0]]
        if typ in ("D", "P"):
            ptr[k] += 1
        env.step(conformes[0])
    m = sim.metrics()
    return lecon, m["cmax"], m["breakdowns"]
