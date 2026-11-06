"""Tableaux LaTeX de la révision (R1–R4) pour la section Results — 02/11/2026.

Lit la banque principale (μ = 1) et la banque μ = 3 ; mêmes définitions que analyse_revision_R1R2.py,
analyse_revision_R3.py et analyse_revision_R4.py (écart au recuit Taguchi 50k, moyenne des graines, 127 instances).
  python -m experiences_article1.tableaux_revision
  -> resultats/tab_filtres.tex (écarts et plannings évalués de toutes les variantes de filtre)
  -> resultats/tab_tests_filtres.tex (tests déclarés R1, R2, R4)
"""
import os, sys
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE)
from experiences_article1.statistiques import (charger, bootstrap_ic, wilcoxon, holm,  # noqa: E402
                                               INSTANCES_REGLAGE, BANQUE)
from metaheuristiques.instances import fichiers                                       # noqa: E402

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
BANQUE_MU3 = os.path.join(RACINE, "banque_resultats", "resultats_mu3.csv")
SORTIE = os.path.join(ICI, "resultats")
TIMES = "$\\times$"
REGLAGES = [(5, 4), (10, 4), (20, 4), (50, 5)]
NOM_FILTRE = {"regle": "Priority rule", "fin": "Earliest finish time", "borne": "Lower bound"}


def noms_test():
    n = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"])]
    return [x for x in n if x not in INSTANCES_REGLAGE]


def outils(banque):
    v, t, ev = charger(banque, "A", 1.0)
    noms = noms_test()
    def ecarts(k):
        if k not in v or any(n not in v[k] for n in noms):
            return None
        return np.array([100 * (np.mean(v[k][n]) / np.mean(v[REF][n]) - 1) for n in noms])
    def evals(k):
        if k not in ev or any(not ev[k].get(n) for n in noms):
            return None
        return float(np.mean([np.mean(ev[k][n]) for n in noms]))
    return ecarts, evals


def pct(x):
    return "--" if x is None else f"{x:+.2f}".replace("-", "$-$")


def p_txt(p):
    if p >= 0.001:
        return f"{p:.2g}"
    e = int(np.floor(np.log10(p)))
    return f"${p / 10 ** e:.1f} \\times 10^{{{e}}}$"


def tab_filtres():
    ecarts, evals = outils(BANQUE)
    lignes = [("Network, seed 0", "RL:imit-ft", "", True), ("Network, seed 1", "RL:imit-ft-g1", "", True),
              ("Network, seed 2", "RL:imit-ft-g2", "", True), ("Network, imitation only", "RL:imit-seule", "", True),
              ("Network, random parameters", "RL:aleatoire-g0", "", True)]
    lignes += [(NOM_FILTRE[f], f"Faisceau:filtre-{f}", f",filtre={f}", False) for f in ("regle", "fin", "borne")]
    t = ["\\begin{tabular}{@{}lcccccc@{}}", "\\toprule",
         "Filter & Greedy & 100 samples & " + " & ".join(f"${B} \\times {K}$" for B, K in REGLAGES) + " \\\\",
         "\\midrule"]
    for i, (lab, m, suf, reseau) in enumerate(lignes):
        if i == 5:
            t.append("\\midrule")
        cells = []
        for c in ("glouton", "echantillons=100"):
            e = ecarts((m, c)) if reseau else None
            cells.append(pct(None if e is None else e.mean()))
        for B, K in REGLAGES:
            k = (m, f"faisceau={B},k={K}{suf}")
            e, n = ecarts(k), evals(k)
            cells.append("--" if e is None else f"{pct(e.mean())} ({n / 1000:.1f})")
        t.append(f"{lab} & " + " & ".join(cells) + " \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    return t


def test(ecarts, ka, kb):
    a, b = ecarts(ka), ecarts(kb)
    d = a - b
    return dict(d=d.mean(), ic=bootstrap_ic(d), V=int((d < -1e-9).sum()), E=int((abs(d) <= 1e-9).sum()),
                D=int((d > 1e-9).sum()), p=wilcoxon(a, b), eb=b.mean())


def tab_tests():
    t = ["\\begin{tabular}{@{}llrcrc@{}}", "\\toprule",
         "Setting & Compared with & Difference & 95\\,\\% CI & W/T/L & $p_{\\mathrm{Holm}}$ \\\\", "\\midrule"]
    ic = lambda x: f"[{pct(x['ic'][0])}, {pct(x['ic'][1])}]"
    ligne = lambda r, autre, x: (f"{r} & {autre} & {pct(x['d'])} & {ic(x)} & {x['V']}/{x['E']}/{x['D']} & "
                                 f"{p_txt(x['ph'])} \\\\")
    # (a) R1 : réseau contre le meilleur filtre simple (Holm sur les 12 tests)
    ecarts, _ = outils(BANQUE)
    r1 = []
    for B, K in REGLAGES:
        for f in ("regle", "fin", "borne"):
            x = test(ecarts, ("RL:imit-ft", f"faisceau={B},k={K}"), (f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}"))
            r1.append(dict(x, r=(B, K), f=f))
    for x, p in zip(r1, holm([x["p"] for x in r1])):
        x["ph"] = p
    t.append("\\multicolumn{6}{@{}l}{\\emph{(a) Network against the best simple filter, $\\mu = 1$ (Holm over 12 tests)}} \\\\")
    for B, K in REGLAGES:
        best = min([x for x in r1 if x["r"] == (B, K)], key=lambda x: x["eb"])
        t.append(ligne(f"${B} \\times {K}$", NOM_FILTRE[best["f"]], best))
    # (b) R2 : réseau final contre imitation seule (Holm sur 6 tests)
    r2 = []
    for c, lab in [("glouton", "Greedy"), ("echantillons=100", "100 samples")] + \
                  [(f"faisceau={B},k={K}", f"${B} \\times {K}$") for B, K in REGLAGES]:
        r2.append(dict(test(ecarts, ("RL:imit-ft", c), ("RL:imit-seule", c)), lab=lab))
    for x, p in zip(r2, holm([x["p"] for x in r2])):
        x["ph"] = p
    t += ["\\midrule", "\\multicolumn{6}{@{}l}{\\emph{(b) Final network against imitation only, $\\mu = 1$ (Holm over 6 tests)}} \\\\"]
    t += [ligne(x["lab"], "Imitation only", x) for x in r2]
    # (c) R4 : μ = 3, réseau contre regle et borne (Holm sur 4 tests)
    ecarts3, _ = outils(BANQUE_MU3)
    r4 = []
    for B, K in [(5, 4), (50, 5)]:
        for f in ("regle", "borne"):
            x = test(ecarts3, ("RL:imit-ft", f"faisceau={B},k={K}"), (f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}"))
            r4.append(dict(x, r=(B, K), f=f))
    for x, p in zip(r4, holm([x["p"] for x in r4])):
        x["ph"] = p
    t += ["\\midrule", "\\multicolumn{6}{@{}l}{\\emph{(c) Network against simple filters, $\\mu = 3$, no retraining (Holm over 4 tests)}} \\\\"]
    t += [ligne(f"${x['r'][0]} \\times {x['r'][1]}$", NOM_FILTRE[x["f"]], x) for x in r4]
    t += ["\\bottomrule", "\\end{tabular}"]
    return t


def main():
    for nom, f in [("tab_filtres.tex", tab_filtres), ("tab_tests_filtres.tex", tab_tests)]:
        txt = "% Généré par experiences_article1/tableaux_revision.py — ne pas modifier à la main.\n" + "\n".join(f()) + "\n"
        with open(os.path.join(SORTIE, nom), "w", encoding="utf-8") as fh:
            fh.write(txt)
        print(txt)


if __name__ == "__main__":
    main()
