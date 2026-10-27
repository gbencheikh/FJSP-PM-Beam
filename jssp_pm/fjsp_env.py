"""MDP FJSP + maintenance, avec actions représentées comme un ENSEMBLE DE CANDIDATS.

À chaque décision, l'environnement énumère les actions valides (masquage implicite) :
  ('D', j, k) : lancer l'op courante du job j sur la machine libre éligible k
  ('P', -1, k): maintenance préventive sur k
  ('W', -1, -1): attendre jusqu'au prochain événement
Chaque candidat est décrit par un vecteur de F_CAND caractéristiques (job, machine, couple),
toutes normalisées par l'unité de temps u de l'instance. La politique note chaque candidat avec
un réseau partagé : elle est donc indépendante de la taille (n, m) de l'instance.
Récompense : -Δt/u - λp·pannes - λm·M_k/u  (somme des Δt = C_max).
"""
import numpy as np
from .fjsp_sim import FSim
from .simulator import IDLE, PROC, PM, REPAIR, EPS

F_JOB, F_MACH, F_PAIR, F_PMX, F_WX = 6, 13, 6, 3, 2
F_CAND = 3 + F_PAIR + F_JOB + F_MACH + F_PMX + F_WX
F_GLOB = 6 + F_MACH


class FJSPEnv:
    def __init__(self, lam_p=5.0, lam_m=0.05, pm_head_fix=False):
        self.lam_p, self.lam_m = lam_p, lam_m
        # v3 : une machine en PM est vue avec sa marge d'après PM (T_k) dans les calculs EFT
        self.pm_head_fix = pm_head_fix

    def reset(self, inst, rng=None):
        self.inst = inst
        self.sim = FSim(inst, rng)
        P = inst.P
        el = P > 0
        self.pmin = np.where(el, P, np.inf).min(1)
        self.nel = el.sum(1)
        self.fastest = np.where(el, P, np.inf).argmin(1)
        self.u = inst.meta["u"]
        self.L = inst.meta["Lbar"]
        # travail restant (min p) à partir de chaque position de chaque job
        self.suffix = [np.cumsum(self.pmin[ops][::-1])[::-1] for ops in inst.job_ops]
        self.maxops = max(len(o) for o in inst.job_ops)
        # charge potentielle : P_ok / n_elig(o)
        self.pot = np.where(el, P, 0.0) / self.nel[:, None]
        r = self._auto()
        return r

    # ------------------------------------------------------------------
    def candidates(self):
        sim = self.sim
        C = []
        if sim.done():
            return C
        idle = [k for k in range(self.inst.m) if sim.status[k] == IDLE]
        for j in sim.ready_jobs():
            o = sim.cur_op(j)
            for k in idle:
                if self.inst.P[o, k] > 0:
                    C.append(("D", j, k))
        for k in idle:
            if sim.can_pm(k):
                C.append(("P", -1, k))
        if sim.can_wait():
            C.append(("W", -1, -1))
        return C

    def _auto(self):
        r = 0.0
        while not self.sim.done():
            C = self.candidates()
            if any(c[0] != "W" for c in C):
                break
            r -= self.sim.advance() / self.u
        self._C = self.candidates()
        return r

    def step(self, idx):
        sim = self.sim
        b0 = sim.n_breakdowns
        typ, j, k = self._C[idx]
        r = 0.0
        if typ == "D":
            sim.dispatch(j, k)
        elif typ == "P":
            sim.start_pm(k)
            r -= self.lam_m * self.inst.M[k] / self.u
        else:
            r -= sim.advance() / self.u
        r += self._auto()
        r -= self.lam_p * (sim.n_breakdowns - b0)
        return r, sim.done()

    # ------------------------------------------------------------------
    # ce que l'agent sait des dates de fin (surchargé en stochastique : durées apparentes seulement)
    def _fins(self):
        return self.sim.end

    def _prochain_evenement(self):
        return self.sim.next_event_dt()

    def features(self):
        """Retourne (X (C, F_CAND), g (F_GLOB,)) pour les candidats courants self._C."""
        sim, inst, u = self.sim, self.inst, self.u
        m, n = inst.m, inst.n
        wear = sim.wears()
        head = inst.T - wear
        rem = np.where(sim.status != IDLE, self._fins() - sim.t, 0.0)
        head_eft = np.where(sim.status == PM, inst.T, head) if self.pm_head_fix else head
        ready = sim.ready_jobs()
        cur = {j: sim.cur_op(j) for j in ready}
        started = sim.started
        # machines
        Mf = np.zeros((m, F_MACH))
        Mf[np.arange(m), sim.status] = 1.0
        Mf[:, 4] = rem / u
        Mf[:, 5] = wear / inst.T
        Mf[:, 6] = np.clip(head / u, -5, 20)
        Mf[:, 7] = inst.T / u / 10
        Mf[:, 8] = inst.M / u
        Mf[:, 9] = inst.R / u / 10
        Mf[:, 10] = np.clip(self.pot[~started].sum(0) / inst.T, 0, 20) / 5
        if ready:
            ops = np.array([cur[j] for j in ready])
            Mf[:, 11] = (inst.P[ops] > 0).sum(0) / n
            Mf[:, 12] = np.bincount(self.fastest[ops], minlength=m) / n
        # EFT par (op prête, machine) : temps avant dispo + PM si nécessaire + p
        X = np.zeros((len(self._C), F_CAND))
        for i, (typ, j, k) in enumerate(self._C):
            x = X[i]
            x[{"D": 0, "J": 0, "P": 1, "W": 2, "C": 2}[typ]] = 1.0
            b = 3
            if typ in ("D", "J"):
                o = cur[j]
                p = inst.P[o, k]
                el = np.flatnonzero(inst.P[o] > 0)
                pe = inst.P[o, el]
                eft = rem[el] + np.where(pe > head_eft[el] + EPS, inst.M[el], 0.0) + pe
                eft_k = p + (inst.M[k] if p > head_eft[k] + EPS else 0.0)
                x[b:b + 6] = [p / u, (p - self.pmin[o]) / u, float(p <= head[k] + EPS),
                              np.clip((head[k] - p) / u, -5, 20), float(self.fastest[o] == k),
                              (eft_k - eft.min()) / u]
                pos = sim.next_op[j]
                nxt = inst.job_ops[j][pos + 1] if pos + 1 < sim.nops_job[j] else None
                x[b + 6:b + 12] = [(sim.nops_job[j] - pos) / 10, self.suffix[j][pos] / self.L,
                                   self.pmin[o] / u, self.nel[o] / m,
                                   (self.pmin[nxt] / u) if nxt is not None else 0.0,
                                   (sim.t - sim.job_free_since[j]) / u]
            b2 = 3 + F_PAIR + F_JOB
            if typ not in ("W", "C"):
                x[b2:b2 + F_MACH] = Mf[k]
            b3 = b2 + F_MACH
            if typ == "P":
                rel = [cur[jj] for jj in ready if inst.P[cur[jj], k] > 0]
                nofit = np.mean([inst.P[o, k] > head[k] + EPS for o in rel]) if rel else 0.0
                remk = sim.remaining_eligible(k)
                pnext = inst.P[remk, k].min() if len(remk) else 0.0
                x[b3:b3 + 3] = [nofit, pnext / u, float(pnext <= head[k] + EPS)]
            if typ in ("W", "C"):
                x[b3 + 3:b3 + 5] = [self._prochain_evenement() / u, np.mean(sim.status != IDLE)]
        self._etat = dict(Mf=Mf, head=head, rem=rem, wear=wear)   # réutilisé par l'observation graphe
        g = np.concatenate([[sim.t / self.L, sim.n_done / inst.n_ops, n / 20, m / 15,
                             (wear / inst.T).max(), np.mean(sim.status == IDLE)], Mf.mean(0)])
        return X.astype(np.float32), g.astype(np.float32)
