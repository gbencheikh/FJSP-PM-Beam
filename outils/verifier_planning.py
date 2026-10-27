"""Independent feasibility check of a schedule for the FJSP with wear and preventive maintenance (regime A).

A schedule is a list of tuples (machine, start, end, type, job):
  machine : 0-based machine index ;
  type    : 1 = operation, 2 = preventive maintenance (job = -1) ;
  job     : 0-based job index. The operations of a job are identified by their order of start times.

Checks: every operation of every job is processed exactly once, on an eligible machine, for its processing
time; precedence inside each job; no overlap on a machine; every maintenance lasts M_k; the cumulative wear
of a machine (processing time since its last maintenance) never exceeds T_k (safety condition c_k + p <= T_k).
Returns the makespan. Raises ValueError with an explicit message otherwise.

Usage:
  from outils.verifier_planning import verifier
  cmax = verifier(inst, schedule)          # inst from jssp_pm.fjsp_instance.load_fjs_v3
"""
EPS = 1e-6


def verifier(inst, planning):
    planning = [tuple(s) for s in planning]
    for k, a, b, t, j in planning:
        if not (0 <= int(k) < inst.m):
            raise ValueError(f"unknown machine {k}")
        if b < a - EPS:
            raise ValueError(f"negative duration {(k, a, b, t, j)}")
        if int(t) not in (1, 2):
            raise ValueError(f"type {t} not allowed in regime A (1 = operation, 2 = maintenance)")
    # operations of each job
    for j, ops in enumerate(inst.job_ops):
        js = sorted([s for s in planning if int(s[3]) == 1 and int(s[4]) == j], key=lambda s: s[1])
        if len(js) != len(ops):
            raise ValueError(f"job {j}: {len(js)} operations scheduled, {len(ops)} expected")
        fin = 0.0
        for o, (k, a, b, t, _) in zip(ops, js):
            p = inst.P[o, int(k)]
            if p <= 0:
                raise ValueError(f"job {j}, operation {o}: machine {k} is not eligible")
            if abs((b - a) - p) > EPS:
                raise ValueError(f"job {j}, operation {o}: duration {b - a} instead of {p}")
            if a < fin - EPS:
                raise ValueError(f"job {j}, operation {o}: starts at {a} before its predecessor ends ({fin})")
            fin = b
    # machines: overlaps, maintenance durations, wear
    for k in range(inst.m):
        sk = sorted([s for s in planning if int(s[0]) == k], key=lambda s: (s[1], s[2]))
        for x, y in zip(sk, sk[1:]):
            if y[1] < x[2] - EPS:
                raise ValueError(f"machine {k}: overlap between {x} and {y}")
        usure = 0.0
        for _, a, b, t, _ in sk:
            if int(t) == 2:
                if abs((b - a) - inst.M[k]) > EPS:
                    raise ValueError(f"machine {k}: maintenance of length {b - a} instead of {inst.M[k]}")
                usure = 0.0
            else:
                usure += b - a
                if usure > inst.T[k] + EPS:
                    raise ValueError(f"machine {k}: wear {usure} exceeds threshold {inst.T[k]} at t = {a}")
    return max(s[2] for s in planning if int(s[3]) == 1)
