"""Simulateur à événements discrets : JSSP + usure cumulée + pannes par seuil + maintenance préventive.

Hypothèses du modèle (voir README) :
  H1  T_k spécifique à chaque machine.
  H2  M_k, R_k déterministes par défaut ; option stochastique : durée ~ nominale * U[0.5, 1.5].
  H3  Maintenance préventive (PM) seulement sur machine libre, non préemptive, remet c_k à 0.
  H4  Le compteur c_k ne progresse que pendant le traitement actif (pas pendant l'attente,
      la PM ou la réparation).
  H5  Panne dès que c_k dépasserait T_k (c_k > T_k). Atteindre exactement T_k en fin
      d'opération n'est pas une panne, mais toute opération suivante en provoquera une.
  H6  Panne pendant une opération : l'opération est INTERROMPUE puis REPRISE (preempt-resume)
      après réparation, pour la durée restante. c_k = 0 après réparation.
  H7  C_max = date de fin de la dernière opération (une PM encore en cours ne compte pas).
"""
import numpy as np

IDLE, PROC, PM, REPAIR = 0, 1, 2, 3
EPS = 1e-9


class Sim:
    def __init__(self, inst, rng=None):
        self.inst = inst
        self.rng = rng if rng is not None else np.random.default_rng()
        n, m = inst.n, inst.m
        self.t = 0.0
        self.next_op = np.zeros(n, dtype=int)     # index de l'op courante / prochaine
        self.job_busy = np.zeros(n, dtype=bool)   # op de j en cours (y compris en réparation)
        self.status = np.zeros(m, dtype=int)
        self.end = np.zeros(m)                    # fin de la phase courante
        self.mjob = -np.ones(m, dtype=int)
        self.wear_base = np.zeros(m)              # usure au début de la phase courante
        self.phase_start = np.zeros(m)
        self.pending = np.zeros(m)                # durée restante à reprendre après panne
        # comptabilité
        self.busy_time = np.zeros((m, 4))         # temps passé par statut
        self.n_breakdowns = 0
        self.n_pm = 0
        self.pm_log = []      # dicts : k, t, wear_ratio, queue_nonempty, headroom, next_p
        self.segments = []    # (k, start, end, type, job)
        self.last_completion = 0.0
        # précalcul : durée restante non démarrée par machine
        self.rem_load = inst.machine_load().astype(float)

    # ------------------------------------------------------------------ état
    def wear(self, k):
        if self.status[k] == PROC:
            return self.wear_base[k] + (self.t - self.phase_start[k])
        return self.wear_base[k]

    def done(self):
        return bool(np.all(self.next_op >= self.inst.n_ops))

    def job_finished(self, j):
        return self.next_op[j] >= self.inst.n_ops

    def job_machine(self, j):
        return self.inst.route[j, self.next_op[j]]

    def job_p(self, j):
        return self.inst.proc[j, self.next_op[j]]

    def can_dispatch(self, j):
        return (not self.job_finished(j)) and (not self.job_busy[j]) \
            and self.status[self.job_machine(j)] == IDLE

    def can_pm(self, k):
        return self.status[k] == IDLE and self.wear(k) > EPS and self.rem_load[k] > EPS

    def can_wait(self):
        return bool(np.any(self.status != IDLE))

    def ready_jobs_for(self, k):
        return [j for j in range(self.inst.n)
                if not self.job_finished(j) and not self.job_busy[j] and self.job_machine(j) == k]

    # ---------------------------------------------------------------- actions
    def dispatch(self, j):
        assert self.can_dispatch(j), f"dispatch invalide j={j}"
        k = self.job_machine(j)
        p = self.job_p(j)
        self.job_busy[j] = True
        self.rem_load[k] -= p
        self._start_proc(k, j, p)

    def _start_proc(self, k, j, p):
        head = self.inst.T[k] - self.wear_base[k]
        self.status[k] = PROC
        self.phase_start[k] = self.t
        self.mjob[k] = j
        if p <= head + EPS:
            self.end[k] = self.t + p
            self.pending[k] = 0.0
        else:  # la panne surviendra quand c_k atteint T_k
            self.end[k] = self.t + max(head, 0.0)
            self.pending[k] = p - max(head, 0.0)
        self.segments.append((k, self.t, self.end[k], PROC, j))

    def start_pm(self, k):
        assert self.can_pm(k), f"PM invalide k={k}"
        c = self.wear(k)
        ready = self.ready_jobs_for(k)
        nxt = self._next_op_on(k)
        self.pm_log.append(dict(k=k, t=self.t, wear_ratio=c / self.inst.T[k],
                                queue_nonempty=len(ready) > 0,
                                headroom=self.inst.T[k] - c, next_p=nxt,
                                necessary=(nxt is not None and nxt > self.inst.T[k] - c + EPS)))
        dur = self._dur(self.inst.M[k])
        self.status[k] = PM
        self.phase_start[k] = self.t
        self.end[k] = self.t + dur
        self.n_pm += 1
        self.segments.append((k, self.t, self.end[k], PM, -1))
        return dur

    def _next_op_on(self, k):
        """Durée de la prochaine op qui sera traitée sur k (la plus proche en nombre d'étapes)."""
        best, best_d = None, 10 ** 9
        for j in range(self.inst.n):
            start = self.next_op[j] + (1 if self.job_busy[j] else 0)
            for o in range(start, self.inst.n_ops):
                if self.inst.route[j, o] == k:
                    d = o - start
                    if d < best_d:
                        best, best_d = self.inst.proc[j, o], d
                    break
        return best

    def _dur(self, nominal):
        if self.inst.stochastic:
            return float(np.round(nominal * self.rng.uniform(0.5, 1.5), 2))
        return float(nominal)

    def advance(self):
        """Avance au prochain événement ; retourne Δt."""
        active = self.status != IDLE
        assert active.any(), "aucun événement futur"
        t_next = float(self.end[active].min())
        dt = t_next - self.t
        for k in range(self.inst.m):
            self.busy_time[k, self.status[k]] += dt
        self.busy_time[:, IDLE] += 0  # (idle compté en fin d'épisode)
        self.t = t_next
        for k in np.where(active & (self.end <= t_next + EPS))[0]:
            self._finish_phase(k)
        return dt

    def _finish_phase(self, k):
        s = self.status[k]
        if s == PROC:
            self.wear_base[k] += self.t - self.phase_start[k]
            j = self.mjob[k]
            if self.pending[k] > EPS:            # panne
                self.n_breakdowns += 1
                self.status[k] = REPAIR
                self.phase_start[k] = self.t
                self.end[k] = self.t + self._dur(self.inst.R[k])
                self.segments.append((k, self.t, self.end[k], REPAIR, j))
            else:                                # opération terminée
                self.next_op[j] += 1
                self.job_busy[j] = False
                self.status[k] = IDLE
                self.mjob[k] = -1
                self.last_completion = self.t
        elif s == REPAIR:                        # reprise de l'op interrompue
            self.wear_base[k] = 0.0
            self._start_proc(k, self.mjob[k], self.pending[k])
        elif s == PM:
            self.wear_base[k] = 0.0
            self.status[k] = IDLE

    # --------------------------------------------------------------- métriques
    def metrics(self):
        cmax = self.last_completion
        bt = self.busy_time
        idle = cmax * self.inst.m - bt[:, PROC].sum() - bt[:, PM].sum() - bt[:, REPAIR].sum()
        wr = [p["wear_ratio"] for p in self.pm_log]
        return dict(cmax=cmax, breakdowns=self.n_breakdowns, pm=self.n_pm,
                    idle=max(idle, 0.0), pm_time=bt[:, PM].sum(), repair_time=bt[:, REPAIR].sum(),
                    wear_at_pm=float(np.mean(wr)) if wr else np.nan,
                    pm_necessary=float(np.mean([p["necessary"] for p in self.pm_log])) if wr else np.nan,
                    pm_in_idle=float(np.mean([not p["queue_nonempty"] for p in self.pm_log])) if wr else np.nan)
