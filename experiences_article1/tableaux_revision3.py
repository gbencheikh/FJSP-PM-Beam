"""Tables de la 3e relecture (04/11/2026), générées depuis les banques :
  resultats/tab_classique_TkLk.tex : problème classique, seuils ×1000 contre T_k = L_k (123 instances sans Kacem, comme
      Results/classique.tex ; référence : recuit 50k du problème classique) — R6.
  resultats/tab_temps_filtres.tex : temps moyen par instance (un processus) et écart au recuit 50k, réseau et filtres
      simples, sous-ensembles E10 et E10b (campagne D2) — N3/R6.
  python -m experiences_article1.tableaux_revision3
"""
import os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI); sys.path.insert(0, RACINE)
from experiences_article1.statistiques import charger, BANQUE, INSTANCES_REGLAGE  # noqa
from metaheuristiques.instances import fichiers  # noqa
from experiences_article1.lancer import SOUS_ENSEMBLE_TEMPS, SOUS_ENSEMBLE_TEMPS_B  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
TIMES = "$\\times$"


def noms_de(fam):
    return [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(fam)) if n not in INSTANCES_REGLAGE]


def pct(x):
    return "--" if x is None else f"{x:+.2f}".replace("-", "$-$")


def classique():
    noms = noms_de(["Brandimarte", "HurinkLa"])
    vc = charger(BANQUE, "A", 1000.0)[0]
    vt = charger(os.path.join(RACINE, "banque_resultats", "resultats_TkLk.csv"), "A", 1.0)[0]
    ref = {n: np.mean(vc[REF][n]) for n in noms}
    def ec(v, k):
        return float(np.mean([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in noms])) if k in v and all(n in v[k] for n in noms) else None
    L = [("Greedy policy", ("RL:imit-ft", "glouton")), ("Best of 100 samples", ("RL:imit-ft", "echantillons=100")),
         (f"Guided beam 5{TIMES}4", ("RL:imit-ft", "faisceau=5,k=4")), (f"Guided beam 50{TIMES}5", ("RL:imit-ft", "faisceau=50,k=5")),
         (f"Priority-rule filter 5{TIMES}4", ("Faisceau:filtre-regle", "faisceau=5,k=4,filtre=regle")),
         (f"Priority-rule filter 50{TIMES}5", ("Faisceau:filtre-regle", "faisceau=50,k=5,filtre=regle"))]
    t = ["% Généré par experiences_article1/tableaux_revision3.py — ne pas modifier à la main.",
         "\\begin{tabular}{@{}lrr@{}}", "\\toprule", "Method & Thresholds $\\times 1\\,000$ & $T_k = L_k$ \\\\", "\\midrule"]
    t += [f"{lab} & {pct(ec(vc, k))} & {pct(ec(vt, k))} \\\\" for lab, k in L]
    t += ["\\bottomrule", "\\end{tabular}"]
    return t


def temps():
    v, tt, _ = charger(BANQUE, "A", 1.0)
    R = [(5, 4), (10, 4), (20, 4), (50, 5)]
    t = ["% Généré par experiences_article1/tableaux_revision3.py — ne pas modifier à la main.",
         "\\begin{tabular}{@{}llrrrr@{}}", "\\toprule",
         "Instances & Filter & " + " & ".join(f"${B} \\times {K}$" for B, K in R) + " \\\\", "\\midrule"]
    for lab, fam in (("Brandimarte, Kacem, vdata (54)", SOUS_ENSEMBLE_TEMPS), ("edata, rdata (36)", SOUS_ENSEMBLE_TEMPS_B)):
        noms = noms_de(fam)
        ref = {n: np.mean(v[REF][n]) for n in noms}
        for i, (nom, m, suf) in enumerate([("Network", "RL:imit-ft-mono", ""), ("Priority rule", "Faisceau:filtre-regle-mono", ",filtre=regle"),
                                           ("Earliest finish", "Faisceau:filtre-fin-mono", ",filtre=fin"), ("Lower bound", "Faisceau:filtre-borne-mono", ",filtre=borne")]):
            cells = []
            for B, K in R:
                k = (m, f"faisceau={B},k={K}{suf}")
                tm = np.mean([np.mean(tt[k][n]) for n in noms]); g = np.mean([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in noms])
                cells.append(f"{tm:.2f}\\,s ({pct(g)})")
            t.append(f"{lab if i == 0 else ''} & {nom} & " + " & ".join(cells) + " \\\\")
        t.append("\\midrule" if fam is SOUS_ENSEMBLE_TEMPS else "\\bottomrule")
    t.append("\\end{tabular}")
    return t


def familles():
    """Relecteur indépendant (M1) : par famille, écart du faisceau 50×5 au recuit 50k (moyenne, médiane, IC 90 %, V/E/D) et gain
    groupé du réseau sur le meilleur filtre simple à budget égal (D1 ; moyenne par instance des 4 différences)."""
    from experiences_article1.statistiques import famille
    noms = noms_de(["Brandimarte", "HurinkLa", "Kacem"])
    v = charger(BANQUE, "A", 1.0)[0]
    ref = {n: np.mean(v[REF][n]) for n in noms}
    ec = lambda k: np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in noms])
    e = ec(("RL:imit-ft", "faisceau=50,k=5"))
    D1 = {"regle": [(6, 4), (12, 4), (22, 4), (55, 5)], "fin": [(7, 4), (12, 4), (24, 4), (56, 5)], "borne": [(6, 4), (12, 4), (23, 4), (55, 5)]}
    ds = []
    for i, (B, K) in enumerate([(5, 4), (10, 4), (20, 4), (50, 5)]):
        er = ec(("RL:imit-ft", f"faisceau={B},k={K}"))
        c = [ec((f"Faisceau:filtre-{f}", f"faisceau={D1[f][i][0]},k={K},filtre={f}")) for f in D1]
        ds.append(er - min(c, key=lambda x: x.mean()))
    D = np.mean(ds, axis=0)
    fam = np.array([famille(n) for n in noms])
    def ic90(d):
        r = np.random.default_rng(0); m = d[r.integers(0, len(d), (10000, len(d)))].mean(1)
        return np.percentile(m, 5), np.percentile(m, 95)
    t = ["% Généré par experiences_article1/tableaux_revision3.py — ne pas modifier à la main.",
         "\\begin{tabular}{@{}lrrrcrr@{}}", "\\toprule",
         " & & \\multicolumn{4}{c}{Beam $50 \\times 5$ against SA 50k (\\%)} & Learned filter \\\\",
         "\\cmidrule(lr){3-6}",
         "Family & $n$ & Mean & Median & 90\\,\\% CI & W/T/L & gain (points) \\\\", "\\midrule"]
    for f in ["Brandimarte", "Hurink edata", "Hurink rdata", "Hurink vdata", "Kacem", "All"]:
        m = np.ones(len(noms), bool) if f == "All" else fam == f
        d = e[m]; lo, hi = ic90(d)
        if f == "All":
            t.append("\\midrule")
        t.append(f"{f} & {m.sum()} & {pct(d.mean())} & {pct(float(np.median(d)))} & [{pct(lo)}, {pct(hi)}] & "
                 f"{(d < -1e-9).sum()}/{(abs(d) <= 1e-9).sum()}/{(d > 1e-9).sum()} & {pct(D[m].mean())} \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    return t


def main():
    for nom, f in (("tab_classique_TkLk.tex", classique), ("tab_temps_filtres.tex", temps), ("tab_familles.tex", familles)):
        txt = "\n".join(f()) + "\n"
        open(os.path.join(ICI, "resultats", nom), "w", encoding="utf-8").write(txt)
        print(txt)


if __name__ == "__main__":
    main()
