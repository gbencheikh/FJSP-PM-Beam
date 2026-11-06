"""Analyse DÉCLARÉE de D5 (PROTOCOLE § 3 septies, entrée D5 du 03/11/2026) : filtre appris POUR filtrer.

(A) filtre-appris contre le réseau final (imit-ft), mêmes réglages : Wilcoxon, Holm sur 4, test global (moyenne par instance
    des 4 différences). Règle : « apprendre à filtrer ajoute à la politique » si le test global est significatif (p < 0,05)
    avec une différence négative.
(B) filtre-appris contre le meilleur filtre simple de R1, mêmes réglages : règle de R1 (≥ 3/4 réglages, Holm sur 4) et test global.
  python -m experiences_article1.analyse_revision_D5 -> resultats/revision_D5.md
"""
import os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import charger, wilcoxon, holm, bootstrap_ic, INSTANCES_REGLAGE, BANQUE  # noqa
from metaheuristiques.instances import fichiers  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
R = [(5, 4), (10, 4), (20, 4), (50, 5)]


def main():
    noms = [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"]))
            if n not in INSTANCES_REGLAGE]
    v, _, ev = charger(BANQUE, "A", 1.0)
    ref = {n: np.mean(v[REF][n]) for n in noms}
    ec = lambda k: np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in noms])
    evm = lambda k: float(np.mean([np.mean(ev[k][n]) for n in noms]))
    md = ["# D5 — filtre appris pour filtrer (analyse déclarée)\n", f"{len(noms)} instances ; écart au recuit 50k (%).\n",
          "| Réglage | Filtre appris | Réseau final | Meilleur filtre simple | Plannings (appris / final / simple) |", "|---|---|---|---|---|"]
    A, Bm = [], []
    for B, K in R:
        ea, ef = ec(("RL:filtre-appris", f"faisceau={B},k={K}")), ec(("RL:imit-ft", f"faisceau={B},k={K}"))
        fs = {f: (f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}") for f in ("regle", "fin", "borne")}
        best = min(fs, key=lambda f: ec(fs[f]).mean()); eb = ec(fs[best])
        md.append(f"| {B}×{K} | {ea.mean():+.2f} % | {ef.mean():+.2f} % | {best} {eb.mean():+.2f} % | "
                  f"{evm(('RL:filtre-appris', f'faisceau={B},k={K}')):.0f} / {evm(('RL:imit-ft', f'faisceau={B},k={K}')):.0f} / {evm(fs[best]):.0f} |")
        A.append((ea, ef)); Bm.append((ea, eb, best))
    try:
        g = ec(("RL:filtre-appris", "glouton")).mean(); md.append(f"\nGlouton du filtre appris (descriptif) : {g:+.2f} %.")
    except Exception:
        pass
    for titre, paires in (("(A) contre le réseau final", [(a, b) for a, b in A]), ("(B) contre le meilleur filtre simple", [(a, b) for a, b, _ in Bm])):
        ds = [a - b for a, b in paires]; ps = [wilcoxon(a, b) for a, b in paires]; ph = holm(ps)
        md += [f"\n## {titre}\n", "| Réglage | Différence | IC 95 % | p Holm (4) |", "|---|---|---|---|"]
        nsig = 0
        for (B, K), d, q in zip(R, ds, ph):
            lo, hi = bootstrap_ic(d); nsig += (q < 0.05 and d.mean() < 0)
            md.append(f"| {B}×{K} | {d.mean():+.3f} | [{lo:+.2f} ; {hi:+.2f}] | {q:.3g} |")
        D = np.mean(ds, axis=0); lo, hi = bootstrap_ic(D); pg = wilcoxon(D, np.zeros_like(D))
        md.append(f"\nTest global : {D.mean():+.3f} point, IC 95 % [{lo:+.2f} ; {hi:+.2f}], p = {pg:.3g} ; réglages significatifs : {nsig}/4.")
    open(os.path.join(ICI, "resultats", "revision_D5.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
