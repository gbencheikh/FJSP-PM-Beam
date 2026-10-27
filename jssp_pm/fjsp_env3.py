"""Environnement v3 (article) : objectif explicite, filtre de sécurité, modes d'ablation.

Objectif optimisé (et récompense exactement alignée) :
    J_β = C_max + β · u · N_pannes          r_t = -Δt/u - β · ΔN_pannes
  - pas de pénalité de PM : son coût en temps est déjà dans C_max ;
  - régime A (faisable) : filtre de sécurité => N_pannes = 0, donc J = C_max exactement ;
  - régime B (stress) : pas de filtre, β ∈ {0, 2, 10} testés (sensibilité).

Filtre de sécurité (safety=True) : un lancement (j, k) n'est proposé que si p_ok ≤ T_k - c_k.

Modes (même état, même réseau, seul l'ensemble d'actions change) :
  full          : lancer (j, k) | PM sur k | attendre                       -> agent complet
  pm_only       : PM sur k | CONTINUER (le répartiteur fixe MWKR+EFT lance tout ce qu'il peut,
                  sinon on avance au prochain événement)                  -> maintenance apprise seule
  dispatch_only : lancer (j, k) | lancer (j, k) après une PM juste-à-temps (macro) | attendre
                                                                         -> dispatch appris seul,
                  maintenance fixée à la règle JIT (PM seulement si l'op choisie ne tient pas)
"""
import numpy as np
from .fjsp_env import FJSPEnv
from .fjsp_sim import FSim
from .simulator import IDLE, PM, EPS


def eft_choice(env, j):
    """Machine EFT sensible à la maintenance pour l'op courante de j.
    Retourne (k*, doit_faire_PM)."""
    sim, inst = env.sim, env.inst
    o = sim.cur_op(j)
    el = np.flatnonzero(inst.P[o] > 0)
    wear = sim.wears()
    head = np.where(sim.status == PM, inst.T, inst.T - wear)
    rem = np.where(sim.status != IDLE, sim.end - sim.t, 0.0)
    p = inst.P[o, el]
    need = p > head[el] + EPS
    eft = rem[el] + np.where(need, inst.M[el], 0.0) + p
    i = int(np.argmin(eft))
    return int(el[i]), bool(need[i])


def mwkr_order(env):
    sim = env.sim
    return sorted(sim.ready_jobs(), key=lambda j: -env.suffix[j][sim.next_op[j]])


class FJSPEnv3(FJSPEnv):
    def __init__(self, mode="full", safety=True, beta=0.0):
        super().__init__(lam_p=beta, lam_m=0.0, pm_head_fix=True)
        assert mode in ("full", "pm_only", "dispatch_only")
        self.mode, self.safety, self.beta = mode, safety, beta

    # ------------------------------------------------------------ candidats
    def _fits(self, j, k):
        o = self.sim.cur_op(j)
        return self.inst.P[o, k] <= self.inst.T[k] - self.sim.wear(k) + EPS

    def _dispatcher_moves(self):
        """Lancements que ferait le répartiteur fixe (MWKR + EFT) maintenant, sans PM."""
        moves, sim = [], self.sim
        for j in mwkr_order(self):
            k, need = eft_choice(self, j)
            if sim.status[k] == IDLE and not need and all(k != kk for _, kk in moves):
                moves.append((j, k))
        return moves

    def candidates(self):
        sim, inst = self.sim, self.inst
        C = []
        if sim.done():
            return C
        idle = [k for k in range(inst.m) if sim.status[k] == IDLE]
        if self.mode in ("full", "dispatch_only"):
            for j in sim.ready_jobs():
                o = sim.cur_op(j)
                for k in idle:
                    if inst.P[o, k] <= 0:
                        continue
                    if not self.safety or self._fits(j, k):
                        C.append(("D", j, k))
                    elif self.mode == "dispatch_only" and sim.wear(k) > EPS:
                        C.append(("J", j, k))
        if self.mode in ("full", "pm_only"):
            for k in idle:
                if sim.can_pm(k):
                    C.append(("P", -1, k))
        if self.mode == "pm_only":
            if self._dispatcher_moves() or sim.can_wait():
                C.append(("C", -1, -1))
        elif sim.can_wait():
            C.append(("W", -1, -1))
        return C

    def _auto(self):
        r = 0.0
        while not self.sim.done():
            C = self.candidates()
            if len(C) == 1 and C[0][0] in ("W", "C"):
                r += self._apply(C[0])
                continue
            if not C:
                raise RuntimeError("aucune action valide")
            break
        self._C = self.candidates()
        return r

    def _apply(self, c):
        typ, j, k = c
        sim = self.sim
        if typ == "D":
            sim.dispatch(j, k)
            return 0.0
        if typ == "J":
            sim.start_pm_then(k, j)
            return 0.0
        if typ == "P":
            sim.start_pm(k)
            return 0.0
        if typ == "C":
            moves = self._dispatcher_moves()
            if moves:
                while moves:
                    for jj, kk in moves:
                        sim.dispatch(jj, kk)
                    moves = self._dispatcher_moves()
                return 0.0
        return -sim.advance() / self.u   # "W" ou "C" sans lancement possible

    def step(self, idx):
        b0 = self.sim.n_breakdowns
        r = self._apply(self._C[idx])
        r += self._auto()
        r -= self.beta * (self.sim.n_breakdowns - b0)
        return r, self.sim.done()

    def objective(self):
        m = self.sim.metrics()
        return m["cmax"] + self.beta * self.u * m["breakdowns"]


# ------------------------------------------------------------ heuristiques v3
class Heur3:
    """Heuristiques exprimées dans l'espace d'actions de chaque mode.
       jit  : PM uniquement quand l'op affectée (EFT) ne tient pas.
       jitp : jit + PM opportuniste sur une machine libre non choisie dont plus aucune op
              restante éligible ne tient.
       asap : PM dès qu'une machine est libre avec c_k > 0 (mode full seulement).
       rtf  : jamais de PM (mode full, sans filtre de sécurité seulement)."""

    def __init__(self, rule="jitp"):
        self.rule = rule
        self.name = {"jit": "PM-JIT", "jitp": "PM-JIT+", "asap": "PM-ASAP", "rtf": "RTF"}[rule]

    def act(self, env):
        C = env._C
        idx = {c: i for i, c in enumerate(C)}
        sim, inst = env.sim, env.inst
        if env.mode == "full" and self.rule == "asap":
            for k in range(inst.m):
                if ("P", -1, k) in idx:
                    return idx[("P", -1, k)]
        chosen = set()
        if env.mode in ("full", "dispatch_only"):
            for j in mwkr_order(env):
                if self.rule == "rtf":
                    o = sim.cur_op(j)
                    el = np.flatnonzero(inst.P[o] > 0)
                    rem = np.where(sim.status != IDLE, sim.end - sim.t, 0.0)
                    k = int(el[np.argmin(rem[el] + inst.P[o, el])])
                    need = False
                else:
                    k, need = eft_choice(env, j)
                chosen.add(k)
                if sim.status[k] != IDLE:
                    continue
                if need and ("J", j, k) in idx:
                    return idx[("J", j, k)]
                if need and ("P", -1, k) in idx:
                    return idx[("P", -1, k)]
                if ("D", j, k) in idx:
                    return idx[("D", j, k)]
        else:  # pm_only : la PM est la seule décision, le dispatch est fixé
            for j in mwkr_order(env):
                k, need = eft_choice(env, j)
                chosen.add(k)
                if sim.status[k] == IDLE and need and ("P", -1, k) in idx:
                    return idx[("P", -1, k)]
        if self.rule == "jitp" and env.mode in ("full", "pm_only"):
            for k in range(inst.m):
                if k in chosen or ("P", -1, k) not in idx:
                    continue
                remk = sim.remaining_eligible(k)
                if len(remk) and inst.P[remk, k].min() > inst.T[k] - sim.wear(k) + EPS:
                    return idx[("P", -1, k)]
        for key in (("C", -1, -1), ("W", -1, -1)):
            if key in idx:
                return idx[key]
        return 0


def run3(env, policy, inst, seed=0):
    env.reset(inst, np.random.default_rng(seed))
    done = env.sim.done()
    while not done:
        _, done = env.step(policy.act(env))
    m = env.sim.metrics()
    m["objective"] = env.objective()
    return m, env.sim
