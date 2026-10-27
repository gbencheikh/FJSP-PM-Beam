"""Figure 1 de l'article 1 : exemple illustratif de la section Problème.

Instance : Table 1 de Bencheikh & Bettayeb (GOL'24, LNNS 1105, 2024) — 3 jobs, 2 machines, 13 opérations.
Usure : Delta_k = mu_k × temps de traitement, seuil lambda = 0,7, mu = (0,07 ; 0,05)  =>  T_k = lambda/mu_k = (10 ; 14)
dans nos unités (temps de traitement cumulé). Durée de maintenance M = 2 (cas de leur Fig. 1(c)).

Trois plannings, tous calculés ici (rien n'est recopié) :
  (a) optimum du FJSP classique (usure ignorée, T = +inf) — CP-SAT, 1 fil, graine 0 ;
  (b) deux temps : affectation et ordres de (a) conservés, maintenance insérée juste à temps
      (au plus tard avant l'opération qui franchirait le seuil), puis décalage à gauche ;
  (c) optimum conjoint — modèle CP de la section 3.2 (segments « valide », Proposition 1).
Chaque planning est vérifié par fjsp_cpsat.check (chevauchements, usure ≤ T_k ; (a) exclu, il viole l'usure)
et les précédences sont vérifiées ici.

  python -m experiences_article1.figure_exemple     # -> resultats/exemple_illustratif.pdf|png|json
"""
import json, os, sys
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from jssp_pm.fjsp_instance import FInstance                     # noqa: E402
from jssp_pm import fjsp_cpsat as CP                             # noqa: E402
from experiences_article1 import style_figures as SF            # noqa: E402

# Table 1 de Bencheikh & Bettayeb (2024) ; 0 = machine non éligible
P_M1 = [5, 3, 3, 4,   0, 5, 4, 4, 3,   0, 5, 0, 4]
P_M2 = [0, 4, 5, 3,   5, 0, 4, 0, 0,   3, 0, 5, 0]
JOB_OPS = [[0, 1, 2, 3], [4, 5, 6, 7, 8], [9, 10, 11, 12]]
LAMBDA, MU, DUREE_PM = 0.7, (0.07, 0.05), 2


def instance(T):
    return FInstance(P=np.array([P_M1, P_M2]).T, job_ops=JOB_OPS, T=np.asarray(T, float),
                     M=np.full(2, float(DUREE_PM)), R=np.full(2, 6.0), name="BencheikhBettayeb2024_T1")


def ops_par_job(segs):
    """(machine, début) de chaque opération, dans l'ordre des jobs."""
    res = {}
    for j, ops in enumerate(JOB_OPS):
        js = sorted([s for s in segs if s[4] == j and s[3] == SF.PROC], key=lambda s: s[1])
        assert len(js) == len(ops)
        for i, (o, s) in enumerate(zip(ops, js)):
            res[o] = s
    return res


def verifier_precedences(inst, segs):
    po = ops_par_job(segs)
    for ops in JOB_OPS:
        for a, b in zip(ops, ops[1:]):
            assert po[b][1] >= po[a][2], ("précédence", a, b)
    for o, (k, a, b, t, j) in po.items():
        assert inst.P[o, int(k)] > 0 and b - a == inst.P[o, int(k)], ("éligibilité/durée", o)


def deux_temps(inst, segs):
    """Affectation et ordre machine de segs conservés ; maintenance juste à temps ; décalage à gauche."""
    po = ops_par_job(segs)
    seq = {k: sorted([o for o in po if po[o][0] == k], key=lambda o: po[o][1]) for k in range(inst.m)}
    pos, libre, usure, fin, out = [0] * inst.m, [0.0] * inst.m, [0.0] * inst.m, {}, []
    while len(fin) < len(po):
        avance = False
        for k in range(inst.m):
            if pos[k] >= len(seq[k]):
                continue
            o = seq[k][pos[k]]
            j = next(j for j, ops in enumerate(JOB_OPS) if o in ops)
            i = JOB_OPS[j].index(o)
            if i > 0 and JOB_OPS[j][i - 1] not in fin:
                continue
            debut = max(libre[k], fin[JOB_OPS[j][i - 1]] if i > 0 else 0.0)
            p = float(inst.P[o, k])
            if usure[k] + p > inst.T[k]:
                d = max(libre[k], debut - inst.M[k])
                out.append((k, d, d + inst.M[k], SF.PM, -1))
                debut, usure[k] = max(debut, d + inst.M[k]), 0.0
            out.append((k, debut, debut + p, SF.PROC, j))
            libre[k], usure[k], fin[o], pos[k], avance = debut + p, usure[k] + p, debut + p, pos[k] + 1, True
        assert avance, "blocage"
    return out


def etiquettes(segs):
    lab = {}
    for j, ops in enumerate(JOB_OPS):
        js = sorted([s for s in segs if s[4] == j and s[3] == SF.PROC], key=lambda s: s[1])
        for i, s in enumerate(js):
            lab[(s[0], s[1])] = f"$O_{{{j + 1},{i + 1}}}$"
    return lab


def main():
    T = [round(LAMBDA / m) for m in MU]                 # (10, 14)
    inst = instance(T)
    sans_usure = instance([1e6, 1e6])
    ra = CP.solve(sans_usure, time_limit=30, workers=1, segments="valide", graine=0, second_phase=False)
    a = [(int(s[0]), float(s[1]), float(s[2]), int(s[3]), int(s[4])) for s in ra["segments"] if s[3] == SF.PROC]     # aucune PM utile quand T = +inf
    b = deux_temps(inst, a)
    rc = CP.solve(inst, time_limit=60, workers=1, segments="valide", graine=0)
    c = [(int(s[0]), float(s[1]), float(s[2]), int(s[3]), int(s[4])) for s in rc["segments"]]
    for s in (b, c):
        CP.check(inst, s)
    for s in (a, b, c):
        verifier_precedences(inst, s)
    cm = lambda s: max(x[2] for x in s if x[3] == SF.PROC)
    npm = lambda s: sum(1 for x in s if x[3] == SF.PM and x[1] < cm(s))
    res = dict(instance="Bencheikh & Bettayeb (2024), Table 1", T=T, M=DUREE_PM,
               a=dict(statut=ra["status"], cmax=cm(a), pm=0, depassements=len(SF.depassements(a, inst.T)), segments=a),
               b=dict(cmax=cm(b), pm=npm(b), segments=b),
               c=dict(statut=rc["status"], cmax=cm(c), pm=npm(c), borne=rc["bound"], segments=c))
    os.makedirs(os.path.join(ICI, "resultats"), exist_ok=True)
    base = os.path.join(ICI, "resultats", "exemple_illustratif")
    json.dump(res, open(base + ".json", "w", encoding="utf-8"), indent=1, default=float)

    SF.style()
    import matplotlib.pyplot as plt
    xmax = max(cm(s) for s in (a, b, c)) + 1
    fig, axes = plt.subplots(3, 1, figsize=(6.4, 4.3), sharex=True)
    titres = [f"(a) Classical FJSP optimum, wear ignored: $C_{{\\max}}$ = {cm(a):g} (infeasible)",
              f"(b) Two-stage: sequences of (a), maintenance inserted just in time: $C_{{\\max}}$ = {cm(b):g}",
              f"(c) Joint optimum (CP model): $C_{{\\max}}$ = {cm(c):g}"]
    for ax, s, t, dep in zip(axes, (a, b, c), titres, (True, False, False)):
        SF.gantt(ax, s, inst, titre=t, noms_ops=etiquettes(s), xmax=xmax, marquer_depassements=dep)
        ax.set_yticklabels([f"Machine {k + 1} ($T_{{{k + 1}}}$ = {T[k]})" for k in range(inst.m)])
    axes[-1].set_xlabel("Time")
    SF.legende(fig, inst.n, depassement=True, loc="lower center", bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print(f"(a) FJSP {ra['status']} Cmax={cm(a):g}, dépassements={res['a']['depassements']}")
    print(f"(b) deux temps Cmax={cm(b):g}, PM={npm(b)}")
    print(f"(c) conjoint {rc['status']} Cmax={cm(c):g}, PM={npm(c)}, borne={rc['bound']:g}")


if __name__ == "__main__":
    main()
