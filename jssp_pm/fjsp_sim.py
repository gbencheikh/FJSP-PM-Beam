"""Simulateur FJSP + usure/pannes/maintenance. Mêmes hypothèses H1–H7 que simulator.py ;
la seule différence est que l'affectation machine de chaque opération est une décision
(prise au moment du lancement, parmi les machines éligibles et libres)."""
import numpy as np
from .simulator import IDLE, PROC, PM, REPAIR, EPS


class FSim:
    def __init__(self, inst, rng=None):
        self.inst = inst
        self.rng = rng if rng is not None else np.random.default_rng()
        n, m = inst.n, inst.m
        self.nops_job = np.array([len(o) for o in inst.job_ops])
        self.t = 0.0
        self.next_op = np.zeros(n, dtype=int)
        self.job_busy = np.zeros(n, dtype=bool)
        self.status = np.zeros(m, dtype=int)
        self.end = np.zeros(m)
        self.mjob = -np.ones(m, dtype=int)
        self.wear_base = np.zeros(m)
        self.phase_start = np.zeros(m)
        self.pending = np.zeros(m)
        self.busy_time = np.zeros((m, 4))
        self.n_breakdowns = 0
        self.n_pm = 0
        self.pm_log, self.segments = [], []
        self.last_completion = 0.0
        self.started = np.zeros(inst.n_ops, dtype=bool)
        self.n_done = 0
        self.job_free_since = np.zeros(n)
        self.after_pm = -np.ones(m, dtype=int)   # v3 : job à lancer sur k à la fin de sa PM

    # état ----------------------------------------------------------------
    def wear(self, k):
        if self.status[k] == PROC:
            return self.wear_base[k] + (self.t - self.phase_start[k])
        return self.wear_base[k]

    def wears(self):
        return np.array([self.wear(k) for k in range(self.inst.m)])

    def done(self):
        return self.n_done >= self.inst.n_ops

    def job_finished(self, j):
        return self.next_op[j] >= self.nops_job[j]

    def cur_op(self, j):
        return self.inst.job_ops[j][self.next_op[j]]

    def ready_jobs(self):
        return [j for j in range(self.inst.n) if not self.job_finished(j) and not self.job_busy[j]]

    def can_dispatch(self, j, k):
        return (not self.job_finished(j)) and (not self.job_busy[j]) and self.status[k] == IDLE \
            and self.inst.P[self.cur_op(j), k] > 0

    def remaining_eligible(self, k):
        """Ops non démarrées éligibles sur k."""
        return np.flatnonzero((~self.started) & (self.inst.P[:, k] > 0))

    def can_pm(self, k):
        return self.status[k] == IDLE and self.wear(k) > EPS and len(self.remaining_eligible(k)) > 0

    def can_wait(self):
        return bool(np.any(self.status != IDLE))

    # actions --------------------------------------------------------------
    def dispatch(self, j, k):
        assert self.can_dispatch(j, k), (j, k)
        o = self.cur_op(j)
        self.started[o] = True
        self.job_busy[j] = True
        self._start_proc(k, j, self.inst.P[o, k])

    def _start_proc(self, k, j, p):
        head = self.inst.T[k] - self.wear_base[k]
        self.status[k] = PROC
        self.phase_start[k] = self.t
        self.mjob[k] = j
        if p <= head + EPS:
            self.end[k], self.pending[k] = self.t + p, 0.0
        else:
            h = max(head, 0.0)
            self.end[k], self.pending[k] = self.t + h, p - h
        self.segments.append((k, self.t, self.end[k], PROC, j))

    def start_pm(self, k):
        assert self.can_pm(k), k
        c = self.wear(k)
        ready_here = [j for j in self.ready_jobs() if self.inst.P[self.cur_op(j), k] > 0]
        self.pm_log.append(dict(k=k, t=self.t, wear_ratio=c / self.inst.T[k],
                                queue_nonempty=len(ready_here) > 0))
        dur = self._dur(self.inst.M[k])
        self.status[k] = PM
        self.phase_start[k] = self.t
        self.end[k] = self.t + dur
        self.n_pm += 1
        self.segments.append((k, self.t, self.end[k], PM, -1))

    def start_pm_then(self, k, j):
        """Macro « maintenance juste à temps » : PM sur k puis op courante de j sur k dès la fin
        de la PM (le job est réservé pendant la PM)."""
        assert self.status[k] == IDLE and not self.job_busy[j] and self.inst.P[self.cur_op(j), k] > 0
        self.start_pm(k)
        self.started[self.cur_op(j)] = True
        self.job_busy[j] = True
        self.after_pm[k] = j

    def _dur(self, nominal):
        if self.inst.stochastic:
            return float(np.round(nominal * self.rng.uniform(0.5, 1.5), 2))
        return float(nominal)

    def next_event_dt(self):
        act = self.status != IDLE
        return float(self.end[act].min() - self.t) if act.any() else 0.0

    def advance(self):
        active = self.status != IDLE
        assert active.any()
        t_next = float(self.end[active].min())
        dt = t_next - self.t
        for k in range(self.inst.m):
            self.busy_time[k, self.status[k]] += dt
        self.t = t_next
        for k in np.where(active & (self.end <= t_next + EPS))[0]:
            self._finish_phase(k)
        return dt

    def _finish_phase(self, k):
        s = self.status[k]
        if s == PROC:
            self.wear_base[k] += self.t - self.phase_start[k]
            j = self.mjob[k]
            if self.pending[k] > EPS:
                self.n_breakdowns += 1
                self.status[k] = REPAIR
                self.phase_start[k] = self.t
                self.end[k] = self.t + self._dur(self.inst.R[k])
                self.segments.append((k, self.t, self.end[k], REPAIR, j))
            else:
                self.next_op[j] += 1
                self.job_busy[j] = False
                self.job_free_since[j] = self.t
                self.status[k] = IDLE
                self.mjob[k] = -1
                self.n_done += 1
                self.last_completion = self.t
        elif s == REPAIR:
            self.wear_base[k] = 0.0
            self._start_proc(k, self.mjob[k], self.pending[k])
        elif s == PM:
            self.wear_base[k] = 0.0
            self.status[k] = IDLE
            j = self.after_pm[k]
            if j >= 0:
                self.after_pm[k] = -1
                self._start_proc(k, j, self.inst.P[self.cur_op(j), k])

    def metrics(self):
        cmax = self.last_completion
        bt = self.busy_time
        idle = cmax * self.inst.m - bt[:, PROC].sum() - bt[:, PM].sum() - bt[:, REPAIR].sum()
        wr = [p["wear_ratio"] for p in self.pm_log]
        return dict(cmax=cmax, breakdowns=self.n_breakdowns, pm=self.n_pm, idle=max(idle, 0.0),
                    proc_time=bt[:, PROC].sum(),
                    wear_at_pm=float(np.mean(wr)) if wr else float("nan"),
                    pm_in_idle=float(np.mean([not p["queue_nonempty"] for p in self.pm_log])) if wr else float("nan"))
