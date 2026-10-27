"""Modèle exact CP-SAT du FJSP avec maintenance préventive (sans panne).

Idée : la ligne de temps de chaque machine k est découpée en segments s = 0..S_k-1 séparés
par des maintenances PM_{k,s}. Chaque op choisit un couple (machine, segment) ; la somme des
durées d'un segment est ≤ T_k (seuil jamais franchi => aucune panne) ; toutes les ops du
segment s finissent avant PM_{k,s}, qui finit avant les ops du segment s+1.
Donne l'optimum (ou une borne) parmi les plannings sans panne — référence pour l'agent.
"""
import math
import numpy as np
from ortools.sat.python import cp_model


def _temps_det(solver):
    """Temps déterministe de CP-SAT (nom de l'accesseur variable selon la version d'OR-Tools)."""
    for nom in ("deterministic_time", "DeterministicTime"):
        f = getattr(solver, nom, None)
        if f is not None:
            return float(f() if callable(f) else f)
    return float("nan")


def solve(inst, time_limit=60, workers=2, S_extra=1, hint=None, second_phase=True, segments="historique", graine=None):
    """segments="historique" : S_k = ceil(charge/T_k) + S_extra (choix d'origine ; la borne n'est alors
    valide que pour les plannings à au plus S_k segments).
    segments="valide" : S_k = min(nb d'options sur k, 2·ceil(charge/T_k) + 1). Il existe toujours un planning
    optimal où deux segments consécutifs d'une machine ont une charge cumulée > T_k (sinon on supprime la
    maintenance qui les sépare sans rien décaler) ; donc floor(S/2)·T_k < charge et S <= 2·ceil(charge/T_k) + 1 :
    la borne CP-SAT est une vraie borne inférieure du problème sans panne."""
    P = inst.P.astype(int)
    T = inst.T.astype(int)
    Md = inst.M.astype(int)
    n_ops, m = P.shape
    model = cp_model.CpModel()
    H = int(sum(P[o][P[o] > 0].max() for o in range(n_ops)) + Md.max() * n_ops)
    # nombre de segments : charge max possible / T + marge
    S = []
    for k in range(m):
        load = P[:, k][P[:, k] > 0].sum()
        if segments == "valide":
            S.append(min(2 * int(math.ceil(load / T[k])) + 1, int((P[:, k] > 0).sum())) or 1)
        else:
            S.append(min(int(math.ceil(load / T[k])) + S_extra, int((P[:, k] > 0).sum())) or 1)
        if hint is not None:   # assez de segments pour représenter le planning de démarrage à chaud
            npm_k = sum(1 for (kk, a, b, t, j) in hint if kk == k and t == 2)
            S[-1] = max(S[-1], npm_k + 1)
    start = [model.NewIntVar(0, H, f"s{o}") for o in range(n_ops)]
    end = [model.NewIntVar(0, H, f"e{o}") for o in range(n_ops)]
    mach_iv = [[] for _ in range(m)]
    seg_x = {}   # (o,k,s) -> bool
    for o in range(n_ops):
        lits = []
        for k in np.flatnonzero(P[o] > 0):
            for s in range(S[k]):
                x = model.NewBoolVar(f"x{o}_{k}_{s}")
                iv = model.NewOptionalIntervalVar(start[o], int(P[o, k]), end[o], x, f"i{o}_{k}_{s}")
                mach_iv[k].append(iv)
                seg_x[(o, k, s)] = x
                lits.append(x)
        model.AddExactlyOne(lits)
    # précédences
    for ops in inst.job_ops:
        for a, b in zip(ops, ops[1:]):
            model.Add(start[b] >= end[a])
    pm_vars = {}
    for k in range(m):
        # capacité d'usure par segment
        for s in range(S[k]):
            terms = [(int(P[o, k]), x) for (o, kk, ss), x in seg_x.items() if kk == k and ss == s]
            if terms:
                model.Add(sum(p * x for p, x in terms) <= int(T[k]))
        prev_y = None
        for s in range(S[k] - 1):
            y = model.NewBoolVar(f"y{k}_{s}")
            ps = model.NewIntVar(0, H, f"ps{k}_{s}")
            pe = model.NewIntVar(0, H, f"pe{k}_{s}")
            iv = model.NewOptionalIntervalVar(ps, int(Md[k]), pe, y, f"pm{k}_{s}")
            mach_iv[k].append(iv)
            pm_vars[(k, s)] = (y, ps, pe)
            if prev_y is not None:
                model.AddImplication(y, prev_y)
                model.Add(ps >= pm_vars[(k, s - 1)][2]).OnlyEnforceIf(y)
            prev_y = y
            for (o, kk, ss), x in seg_x.items():
                if kk != k:
                    continue
                if ss == s:
                    model.Add(end[o] <= ps).OnlyEnforceIf([x, y])
                elif ss == s + 1:
                    model.AddImplication(x, y)
                    model.Add(start[o] >= pe).OnlyEnforceIf(x)
        model.AddNoOverlap(mach_iv[k])
    if hint is not None:
        _add_hint(model, inst, hint, seg_x, pm_vars, start, S, end)
    cmax = model.NewIntVar(0, H, "cmax")
    for ops in inst.job_ops:
        model.Add(cmax >= end[ops[-1]])
    ys = [v[0] for v in pm_vars.values()]
    # phase 1 : min C_max ; phase 2 : C_max fixé, min nombre de PM
    if hint is not None:
        hc = max(b for (k, a, b, t, j) in hint if t == 1)
        model.Add(cmax <= int(round(hc)))   # borne sup. valide : le planning du hint
        model.AddHint(cmax, int(round(hc)))
    model.Minimize(cmax)
    solver = cp_model.CpSolver()
    solver.parameters.repair_hint = hint is not None
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    if graine is not None:                     # ajouté le 9/10/2026 (E9b) ; défaut inchangé
        solver.parameters.random_seed = int(graine)
    st = solver.Solve(model)
    res = dict(status=solver.StatusName(st), cmax=None, bound=solver.BestObjectiveBound(),
               time=solver.WallTime(), temps_deterministe=_temps_det(solver),
               segments=segments, S=[int(x) for x in S])
    def extract():
        segs = []
        for (o, k, s), x in seg_x.items():
            if solver.Value(x):
                job = next(j for j, ops in enumerate(inst.job_ops) if o in ops)
                segs.append((int(k), solver.Value(start[o]), solver.Value(end[o]), 1, job))
        for (k, s), (y, ps, pe) in pm_vars.items():
            if solver.Value(y):
                segs.append((int(k), solver.Value(ps), solver.Value(pe), 2, -1))
        return dict(cmax=int(solver.Value(cmax)),
                    pm=int(sum(solver.Value(v[0]) for v in pm_vars.values())), segments=segs)

    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        res.update(extract())          # solution de la phase 1
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) and second_phase:
        model.Add(cmax <= res["cmax"])
        model.Minimize(sum(ys))
        model.ClearHints()
        for o in range(n_ops):
            model.AddHint(start[o], solver.Value(start[o]))
        solver.parameters.max_time_in_seconds = max(10, time_limit // 4)
        st2 = solver.Solve(model)
        if st2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            res.update(extract())      # même C_max, moins de PM
        res["time"] += solver.WallTime()
    return res


def check(inst, segs):
    """Vérifie un planning (k, début, fin, type, job) : chevauchements, précédences, usure <= T."""
    for k in range(inst.m):
        sk = sorted([s for s in segs if s[0] == k], key=lambda s: s[1])
        c = 0
        for a, b in zip(sk, sk[1:]):
            assert b[1] >= a[2], ("overlap", a, b)
        for s in sk:
            if s[3] == 1:
                c += s[2] - s[1]
                assert c <= inst.T[k] + 1e-9, ("wear", k, s)
            else:
                c = 0
    return True


def _add_hint(model, inst, segs, seg_x, pm_vars, start, S, end=None):
    """Démarrage à chaud depuis un planning simulé (liste (k, début, fin, type, job))."""
    PROC_, PM_ = 1, 2
    pms = {k: sorted(a for kk, a, b, t, j in segs if kk == k and t == PM_) for k in range(inst.m)}
    chosen = {}
    for j, ops in enumerate(inst.job_ops):
        js = sorted([s for s in segs if s[4] == j and s[3] == PROC_], key=lambda s: s[1])
        if len(js) != len(ops):
            return  # planning avec panne (op scindée) : pas de hint
        for o, (k, a, b, t, _) in zip(ops, js):
            s = sum(1 for p in pms[k] if p < a)
            if s >= S[k] or (o, k, s) not in seg_x:
                return
            chosen[o] = (k, s, a)
    for key, x in seg_x.items():
        o, k, s = key
        model.AddHint(x, chosen[o][:2] == (k, s))
    for o, (k, s, a) in chosen.items():
        model.AddHint(start[o], int(round(a)))
        if end is not None:
            model.AddHint(end[o], int(round(a + inst.P[o, k])))
    for (k, s), (y, ps, pe) in pm_vars.items():
        model.AddHint(y, s < len(pms[k]))
        if s < len(pms[k]):
            model.AddHint(ps, int(round(pms[k][s])))
            model.AddHint(pe, int(round(pms[k][s] + inst.M[k])))
