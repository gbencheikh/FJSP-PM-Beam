"""Calibrage absolu (2e relecture, N2 ; 03/11/2026) -> resultats/tab_bornes.tex

Par famille (127 instances de test) : nombre d'optima prouvés (régime A), écart moyen à la meilleure borne inférieure
valide (régime A) du meilleur planning connu, du recuit 50k (moyenne de 5 graines) et du faisceau guidé 5×4 et 50×5 ; puis,
sur le problème classique, écart moyen au meilleur connu (FJSPLib ou nos calculs) du recuit et du tabou 50k.
Sources : resultats/meilleurs_connus_article.csv (outils/table_meilleurs_connus.py) et banque_resultats/resultats.csv.
"""
import csv, os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import charger, BANQUE, INSTANCES_REGLAGE, famille  # noqa
from metaheuristiques.instances import fichiers  # noqa

SA = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
TS = ("Recherche tabou", "evals=50000,depart=heuristique,params=taguchi")
CPS = ("CP-SAT", "temps=600,segments=valide")   # 3e relecture (R2) : CP-SAT à départ chaud, 600 s, 2 fils (E9)
FAMS = ["Brandimarte", "Hurink edata", "Hurink rdata", "Hurink vdata", "Kacem"]


def main():
    noms = [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"]))
            if n not in INSTANCES_REGLAGE]
    mc = {}
    for r in csv.DictReader(open(os.path.join(ICI, "resultats", "meilleurs_connus_article.csv"), encoding="utf-8")):
        mc[(r["instance"], r["regime"])] = r
    vA = charger(BANQUE, "A", 1.0)[0]; vC = charger(BANQUE, "A", 1000.0)[0]
    gap = lambda x, b: 100 * (x / b - 1)
    rows = []
    for fam in FAMS + ["All"]:
        N = [n for n in noms if fam == "All" or famille(n) == fam]
        lbA = {n: float(mc[(n, "A")]["borne_inf"]) for n in N}
        opt = sum(mc[(n, "A")]["statut"] == "optimum prouvé" for n in N)
        bkA = np.mean([gap(float(mc[(n, "A")]["meilleur_cmax"]), lbA[n]) for n in N])
        g = lambda v, k, ref: np.mean([gap(np.mean(v[k][n]), ref[n]) for n in N])
        bkC = {n: float(mc[(n, "classique")]["meilleur_cmax"]) for n in N}
        Nc = [n for n in N if n in vA[CPS]]
        cps = np.mean([gap(min(vA[CPS][n]), lbA[n]) for n in Nc]) if Nc else float("nan")
        rows.append((fam, len(N), opt, bkA, cps, g(vA, SA, lbA), g(vA, ("RL:imit-ft", "faisceau=5,k=4"), lbA),
                     g(vA, ("RL:imit-ft", "faisceau=50,k=5"), lbA), g(vC, SA, bkC), g(vC, TS, bkC)))
    t = ["% Généré par experiences_article1/tableau_bornes.py — ne pas modifier à la main.",
         "\\begin{tabular}{@{}lrrrrrrrrr@{}}", "\\toprule",
         " & & \\multicolumn{6}{c}{With maintenance: gap to the lower bound (\\%)} & \\multicolumn{2}{c}{Classical: gap to best known (\\%)} \\\\",
         "\\cmidrule(lr){3-8}\\cmidrule(l){9-10}",
         "Family & $n$ & Optima & Best known & CP-SAT$^{*}$ & SA 50k & Beam $5 \\times 4$ & Beam $50 \\times 5$ & SA 50k & TS 50k \\\\", "\\midrule"]
    for i, (fam, n, opt, *vals) in enumerate(rows):
        if fam == "All":
            t.append("\\midrule")
        t.append(f"{fam} & {n} & {opt} & " + " & ".join("--" if x != x else f"{x:.2f}" for x in vals) + " \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    txt = "\n".join(t) + "\n"
    open(os.path.join(ICI, "resultats", "tab_bornes.tex"), "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
