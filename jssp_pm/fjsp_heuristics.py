"""Heuristiques FJSP + maintenance. Dispatch commun : jobs par MWKR (travail restant, min p),
machine par EFT (date de fin la plus tôte). Pour les politiques avec maintenance, l'EFT inclut
M_k si l'op ne tient pas dans la marge T_k - c_k ("EFT sensible à la maintenance").

  RTF      : jamais de PM, EFT sans usure.
  ASAP     : PM dès qu'une machine est libre avec c_k > 0.
  JIT      : PM uniquement quand l'op affectée à k ne tient pas dans la marge.
  JIT+     : JIT + PM opportuniste sur machine libre et sans op affectée si la plus petite op
             restante éligible sur k ne tient plus dans la marge.
"""
import numpy as np
from .simulator import IDLE, EPS


class FHeuristic:
    def __init__(self, mode="jit"):
        self.mode = mode
        self.name = {"rtf": "RTF", "asap": "PM-ASAP", "jit": "PM-JIT", "jitp": "PM-JIT+"}[mode]

    def act(self, env):
        sim, inst = env.sim, env.inst
        C = env._C
        idx = {c: i for i, c in enumerate(C)}
        wear = sim.wears()
        head = inst.T - wear
        rem = np.where(sim.status != IDLE, sim.end - sim.t, 0.0)
        if self.mode == "asap":
            for k in range(inst.m):
                if ("P", -1, k) in idx:
                    return idx[("P", -1, k)]
        ready = sorted(sim.ready_jobs(), key=lambda j: -env.suffix[j][sim.next_op[j]])
        chosen = set()
        for j in ready:
            o = sim.cur_op(j)
            el = np.flatnonzero(inst.P[o] > 0)
            p = inst.P[o, el]
            need = (p > head[el] + EPS) & (self.mode != "rtf")
            eft = rem[el] + np.where(need, inst.M[el], 0.0) + p
            order = el[np.argsort(eft, kind="stable")]
            k = order[0]
            chosen.add(k)
            if sim.status[k] != IDLE:
                continue
            if self.mode != "rtf" and inst.P[o, k] > head[k] + EPS and ("P", -1, k) in idx:
                return idx[("P", -1, k)]
            if ("D", j, k) in idx:
                return idx[("D", j, k)]
        if self.mode == "jitp":
            for k in range(inst.m):
                if k in chosen or ("P", -1, k) not in idx:
                    continue
                remk = sim.remaining_eligible(k)
                if len(remk) and inst.P[remk, k].min() > head[k] + EPS:
                    return idx[("P", -1, k)]
        if ("W", -1, -1) in idx:
            return idx[("W", -1, -1)]
        return next(i for i, c in enumerate(C) if c[0] == "D")


def run(env, policy, inst, seed=0):
    env.reset(inst, np.random.default_rng(seed))
    ret, done = 0.0, env.sim.done()
    while not done:
        r, done = env.step(policy.act(env))
        ret += r
    m = env.sim.metrics()
    m["return"] = ret
    return m, env.sim
