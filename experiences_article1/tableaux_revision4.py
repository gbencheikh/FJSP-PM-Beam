"""Tables du relecteur indépendant (04/11/2026), générées depuis les banques :
  resultats/tab_departage.tex : ablation du départage des ex aequo (B1) ;
  resultats/tab_tirages_phi.tex : tirages des facteurs φ_k (protocole, graines 1 et 2 ; B2) ;
  resultats/tab_gain_global.tex est complété par tableau_gain_global.py (inchangé).
  python -m experiences_article1.tableaux_revision4
"""
import os, re, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI); sys.path.insert(0, RACINE)
from experiences_article1.statistiques import charger, BANQUE, INSTANCES_REGLAGE, wilcoxon, bootstrap_ic, famille  # noqa
from metaheuristiques.instances import fichiers  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
NOMS = [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"])) if n not in INSTANCES_REGLAGE]
G = [("la", int(m.group(1))) if (m := re.match(r"Hurink[EVR]data(\d+)", n)) else n for n in NOMS]
GRAPPES = [[i for i, g in enumerate(G) if g == u] for u in dict.fromkeys(G)]
SANS_KACEM = np.array([famille(n) != "Kacem" for n in NOMS])


def pct(x):
    return f"{x:+.2f}".replace("-", "$-$")


def p_txt(p):
    return f"{p:.2g}" if p >= 0.001 else f"${p / 10 ** int(np.floor(np.log10(p))):.1f} \\times 10^{{{int(np.floor(np.log10(p)))}}}$"


def ic_grappes(d, n=10000):
    r = np.random.default_rng(0)
    m = [d[np.concatenate([GRAPPES[j] for j in r.integers(0, len(GRAPPES), len(GRAPPES))])].mean() for _ in range(n)]
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def outil(banque):
    v = charger(banque, "A", 1.0)[0]; ref = {n: np.mean(v[REF][n]) for n in NOMS}
    return lambda k: np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in NOMS])


def best(ec, B, K, suf="", fs=("regle", "fin", "borne")):
    c = [ec((f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}{suf}")) for f in fs]
    return min(c, key=lambda x: x.mean())


def ligne_test(lab, ds):
    D = np.mean(ds, axis=0); lo, hi = ic_grappes(D); p = wilcoxon(D, np.zeros_like(D))
    Dk = D[SANS_KACEM]; pk = wilcoxon(Dk, np.zeros_like(Dk))
    return (f"{lab} & {' & '.join(pct(d.mean()) for d in ds)} & {pct(D.mean())} & [{pct(lo)}, {pct(hi)}] & {p_txt(p)} & "
            f"{pct(Dk.mean())} & {p_txt(pk)} \\\\")


ENTETE = ["\\begin{tabular}{@{}lrrrcrrr@{}}", "\\toprule",
          " & \\multicolumn{2}{c}{Difference (points)} & \\multicolumn{3}{c}{Pooled, 127 instances} & \\multicolumn{2}{c}{Without Kacem} \\\\",
          "\\cmidrule(lr){2-3}\\cmidrule(lr){4-6}\\cmidrule(l){7-8}",
          "Comparison & $5 \\times 4$ & $50 \\times 5$ & Mean & 95\\,\\% CI (clusters) & $p$ & Mean & $p$ \\\\", "\\midrule"]


def departage():
    ec = outil(BANQUE); R = [(5, 4), (50, 5)]
    net = lambda B, K, s="": ec(("RL:imit-ft", f"faisceau={B},k={K}{s}"))
    t = ["% Généré par experiences_article1/tableaux_revision4.py — ne pas modifier à la main."] + ENTETE
    t.append(ligne_test("Network (ties by log-probability) $-$ best filter (ties by order)", [net(B, K) - best(ec, B, K) for B, K in R]))
    t.append(ligne_test("Network (ties by order) $-$ best filter (ties by order)", [net(B, K, ",departage=ordre") - best(ec, B, K) for B, K in R]))
    t.append(ligne_test("Network (ties by log-probability) $-$ best filter (ties by rank)", [net(B, K) - best(ec, B, K, ",departage=rang") for B, K in R]))
    t.append(ligne_test("Network (ties by log-probability) $-$ network (ties by order)", [net(B, K) - net(B, K, ",departage=ordre") for B, K in R]))
    t += ["\\bottomrule", "\\end{tabular}"]
    return t


def tirages():
    R = [(5, 4), (50, 5)]
    t = ["% Généré par experiences_article1/tableaux_revision4.py — ne pas modifier à la main."] + ENTETE
    for lab, b in (("Protocol draw (seed 0)", BANQUE), ("Draw with seed 1", os.path.join(RACINE, "banque_resultats", "resultats_phi1.csv")),
                   ("Draw with seed 2", os.path.join(RACINE, "banque_resultats", "resultats_phi2.csv"))):
        ec = outil(b)
        t.append(ligne_test(lab, [ec(("RL:imit-ft", f"faisceau={B},k={K}")) - best(ec, B, K, fs=("regle", "borne")) for B, K in R]))
    t += ["\\bottomrule", "\\end{tabular}"]
    return t


def main():
    for nom, f in (("tab_departage.tex", departage), ("tab_tirages_phi.tex", tirages)):
        txt = "\n".join(f()) + "\n"
        open(os.path.join(ICI, "resultats", nom), "w", encoding="utf-8").write(txt)
        print(txt)


if __name__ == "__main__":
    main()
