"""Tables de l'article C&IE (version courte, angle application ; 09/11/2026), calculées depuis les banques :
  resultats/tab_familles_caie.tex : par famille, écart du faisceau guidé 50×5 au recuit 50k (moyenne, médiane, IC 90 %,
      V/E/D) — même calcul que tab_familles.tex, sans la colonne du filtre appris (réservée à l'article B).
  resultats/tab_robustesse_caie.tex : variantes du générateur (μ = 3, facteurs de seuil 0,7 et 1,5, tirages de φ_k
      graines 1 et 2) : écart du faisceau guidé 5×4 et 50×5 au recuit 50k de la même variante, IC 90 % et équivalence
      (TOST ±1 %) du 50×5. Chaque variante a sa propre banque ou son propre facteur de seuil ; référence = recuit 50k de
      la variante (moyenne des graines).
  python -m experiences_article1.tableaux_caie
"""
import os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI); sys.path.insert(0, RACINE)
from experiences_article1.statistiques import charger, BANQUE, INSTANCES_REGLAGE, famille  # noqa
from metaheuristiques.instances import fichiers  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
NET = "RL:imit-ft"
BANQUES = os.path.join(RACINE, "banque_resultats")


def noms_de(fam):
    return [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(fam)) if n not in INSTANCES_REGLAGE]


def pct(x):
    return f"{x:+.2f}".replace("-", "$-$")


def ic90(d):
    r = np.random.default_rng(0)
    m = d[r.integers(0, len(d), (10000, len(d)))].mean(1)
    return np.percentile(m, 5), np.percentile(m, 95)


def ecarts(v, noms, k):
    ref = {n: np.mean(v[REF][n]) for n in noms}
    return np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in noms])


def familles():
    noms = noms_de(["Brandimarte", "HurinkLa", "Kacem"])
    v = charger(BANQUE, "A", 1.0)[0]
    e = ecarts(v, noms, (NET, "faisceau=50,k=5"))
    fam = np.array([famille(n) for n in noms])
    t = ["% Généré par experiences_article1/tableaux_caie.py — ne pas modifier à la main.",
         "\\begin{tabular}{@{}lrrrcr@{}}", "\\toprule",
         "Family & $n$ & Mean (\\%) & Median (\\%) & 90\\,\\% CI & W/T/L \\\\", "\\midrule"]
    for f in ["Brandimarte", "Hurink edata", "Hurink rdata", "Hurink vdata", "Kacem", "All"]:
        m = np.ones(len(noms), bool) if f == "All" else fam == f
        d = e[m]; lo, hi = ic90(d)
        if f == "All":
            t.append("\\midrule")
        t.append(f"{f} & {m.sum()} & {pct(d.mean())} & {pct(float(np.median(d)))} & [{pct(lo)}, {pct(hi)}] & "
                 f"{(d < -1e-9).sum()}/{(abs(d) <= 1e-9).sum()}/{(d > 1e-9).sum()} \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    return t


VARIANTES = [  # (libellé, fichier de banque, facteur de seuil)
    ("Protocol ($\\mu = 1$, factor 1, seed 0)", "resultats.csv", 1.0),
    ("Longer maintenances ($\\mu = 3$)", "resultats_mu3.csv", 1.0),
    ("Thresholds $\\times 0.7$", "resultats.csv", 0.7),
    ("Thresholds $\\times 1.5$", "resultats.csv", 1.5),
    ("Other draw of $\\varphi_k$ (seed 1)", "resultats_phi1.csv", 1.0),
    ("Other draw of $\\varphi_k$ (seed 2)", "resultats_phi2.csv", 1.0),
]


def robustesse():
    noms = noms_de(["Brandimarte", "HurinkLa", "Kacem"])
    t = ["% Généré par experiences_article1/tableaux_caie.py — ne pas modifier à la main.",
         "\\begin{tabular}{@{}lrrcc@{}}", "\\toprule",
         " & Beam $5 \\times 4$ & \\multicolumn{3}{c}{Beam $50 \\times 5$} \\\\", "\\cmidrule(lr){2-2}\\cmidrule(l){3-5}",
         "Instance generator & Mean gap (\\%) & Mean gap (\\%) & 90\\,\\% CI & Equivalent ($\\pm 1\\,\\%$) \\\\", "\\midrule"]
    for lab, fich, fs in VARIANTES:
        v = charger(os.path.join(BANQUES, fich), "A", fs)[0]
        e5 = ecarts(v, noms, (NET, "faisceau=5,k=4"))
        e50 = ecarts(v, noms, (NET, "faisceau=50,k=5"))
        lo, hi = ic90(e50)
        eq = "yes" if (lo > -1 and hi < 1) else "no"
        t.append(f"{lab} & {pct(e5.mean())} & {pct(e50.mean())} & [{pct(lo)}, {pct(hi)}] & {eq} \\\\")
        print(f"{lab}: 5x4 {e5.mean():+.2f} ; 50x5 {e50.mean():+.2f} [{lo:+.2f}, {hi:+.2f}] ({len(noms)} instances)")
    t += ["\\bottomrule", "\\end{tabular}"]
    return t


def main():
    for nom, f in (("tab_familles_caie.tex", familles), ("tab_robustesse_caie.tex", robustesse)):
        txt = "\n".join(f()) + "\n"
        open(os.path.join(ICI, "resultats", nom), "w", encoding="utf-8").write(txt)
        print(txt)


if __name__ == "__main__":
    main()
