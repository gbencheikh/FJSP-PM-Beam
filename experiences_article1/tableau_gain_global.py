"""Table « gain du filtre appris sur le meilleur filtre simple » (2e révision, 03/11/2026) -> resultats/tab_gain_global.tex

Une ligne par campagne : différence moyenne (réseau − meilleur filtre simple, en points) à chaque réglage, puis test global
(moyenne par instance des différences, Wilcoxon, IC bootstrap 95 %). Lignes « déclarées » : D1 (budget égal), D3 (facteur 0,7
et 1,5) ; lignes exploratoires (†) : R1 (mêmes réglages) et R4 (μ = 3), dont le test global n'avait pas été déclaré.
"""
import os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI); sys.path.insert(0, RACINE)
from experiences_article1.statistiques import charger, wilcoxon, bootstrap_ic, INSTANCES_REGLAGE, BANQUE  # noqa
from metaheuristiques.instances import fichiers  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
NOMS = [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"]))
        if n not in INSTANCES_REGLAGE]
MU3 = os.path.join(RACINE, "banque_resultats", "resultats_mu3.csv")
R4 = [(5, 4), (10, 4), (20, 4), (50, 5)]
D1 = {"regle": [(6, 4), (12, 4), (22, 4), (55, 5)], "fin": [(7, 4), (12, 4), (24, 4), (56, 5)], "borne": [(6, 4), (12, 4), (23, 4), (55, 5)]}


def ligne(banque, fs, reglages, filtres, budget_egal=False):
    v = charger(banque, "A", fs)[0]
    ref = {n: np.mean(v[REF][n]) for n in NOMS}
    ec = lambda k: np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in NOMS])
    ds = []
    for i, (B, K) in enumerate(reglages):
        er = ec(("RL:imit-ft", f"faisceau={B},k={K}"))
        cand = []
        for f in filtres:
            b, k = D1[f][i] if budget_egal else (B, K)
            cand.append(ec((f"Faisceau:filtre-{f}", f"faisceau={b},k={k},filtre={f}")))
        best = min(cand, key=lambda x: x.mean())
        ds.append(er - best)
    D = np.mean(ds, axis=0)
    lo, hi = bootstrap_ic(D)
    return [d.mean() for d in ds], D.mean(), lo, hi, wilcoxon(D, np.zeros_like(D))


def f2(x):
    return f"{x:+.2f}".replace("-", "$-$")


def p_txt(p):
    return f"{p:.2g}" if p >= 0.001 else f"${p:.1e}".replace("e-0", " \\times 10^{-") + "}$"


def main():
    L = [("Same settings, $\\mu = 1$\\textsuperscript{\\dag}", ligne(BANQUE, 1.0, R4, ("regle", "fin", "borne")), 4),
         ("Equal budget, $\\mu = 1$", ligne(BANQUE, 1.0, R4, ("regle", "fin", "borne"), budget_egal=True), 4),
         ("Same settings, $\\mu = 3$\\textsuperscript{\\dag}", ligne(MU3, 1.0, [(5, 4), (50, 5)], ("regle", "borne")), 2),
         ("Same settings, threshold factor 0.7", ligne(BANQUE, 0.7, [(5, 4), (50, 5)], ("regle", "borne")), 2),
         ("Same settings, threshold factor 1.5", ligne(BANQUE, 1.5, [(5, 4), (50, 5)], ("regle", "borne")), 2)]
    t = ["% Généré par experiences_article1/tableau_gain_global.py — ne pas modifier à la main.",
         "\\begin{tabular}{@{}lccccccc@{}}", "\\toprule",
         "Campaign & $5 \\times 4$ & $10 \\times 4$ & $20 \\times 4$ & $50 \\times 5$ & Global & 95\\,\\% CI & $p$ \\\\", "\\midrule"]
    for lab, (ds, g, lo, hi, p), n in L:
        cells = [f2(x) for x in ds] if n == 4 else [f2(ds[0]), "--", "--", f2(ds[1])]
        t.append(f"{lab} & " + " & ".join(cells) + f" & {f2(g)} & [{f2(lo)}, {f2(hi)}] & {p_txt(p)} \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    txt = "\n".join(t) + "\n"
    open(os.path.join(ICI, "resultats", "tab_gain_global.tex"), "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
