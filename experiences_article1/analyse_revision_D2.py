"""Analyse DÉCLARÉE de D2 (PROTOCOLE § 3 septies) : temps des filtres simples (un processus, machine au repos).

Par sous-ensemble (E10 : Brandimarte, Kacem, Hurink vdata, 54 instances ; E10b : une instance sur deux de Hurink edata et
rdata, 36) : temps moyen par instance de chaque réglage (réseau : RL:imit-ft-mono ; filtres : Faisceau:filtre-*-mono).
Pour chaque limite (1, 2, 5, 10, 20, 40 s) : faisceau guidé par le réseau = réglage le plus large dont le temps moyen
(sur le sous-ensemble) ≤ limite ; faisceau à filtre simple = même règle pour chaque filtre, puis meilleur filtre (écart moyen
au recuit 50k le plus bas). Wilcoxon apparié, Holm sur les limites, par sous-ensemble. Aucune règle de décision.
  python -m experiences_article1.analyse_revision_D2 -> resultats/revision_D2.md
"""
import os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import charger, wilcoxon, holm, bootstrap_ic, INSTANCES_REGLAGE, BANQUE  # noqa
from metaheuristiques.instances import fichiers  # noqa
from experiences_article1.lancer import SOUS_ENSEMBLE_TEMPS, SOUS_ENSEMBLE_TEMPS_B  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
LIMITES = [1, 2, 5, 10, 20, 40]
R = [(5, 4), (10, 4), (20, 4), (50, 5)]


def main():
    v, t, _ = charger(BANQUE, "A", 1.0)
    md = ["# D2 — temps des filtres simples (analyse déclarée)\n"]
    for lab, fam in (("E10 (Brandimarte, Kacem, Hurink vdata)", SOUS_ENSEMBLE_TEMPS), ("E10b (Hurink edata/rdata, 1 sur 2)", SOUS_ENSEMBLE_TEMPS_B)):
        noms = [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(fam)) if n not in INSTANCES_REGLAGE]
        ref = {n: np.mean(v[REF][n]) for n in noms}
        ec = lambda k: np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in noms])
        tm = lambda k: float(np.mean([np.mean(t[k][n]) for n in noms]))
        series = {"réseau": {f"{B}x{K}": ("RL:imit-ft-mono", f"faisceau={B},k={K}") for B, K in [(1, 4)] + R}}
        for f in ("regle", "fin", "borne"):
            series[f] = {f"{B}x{K}": (f"Faisceau:filtre-{f}-mono", f"faisceau={B},k={K},filtre={f}") for B, K in R}
        md += [f"\n## {lab} — {len(noms)} instances\n", "| Filtre | " + " | ".join(f"{B}×{K}" for B, K in R) + " |",
               "|---|" + "---|" * len(R)]
        for s, d in series.items():
            md.append(f"| {s} | " + " | ".join(f"{tm(d[f'{B}x{K}']):.2f} s ({ec(d[f'{B}x{K}']).mean():+.2f} %)" for B, K in R) + " |")
        rows = []
        for L in LIMITES:
            def choix(d):
                ok = [(tm(k), c) for c, k in d.items() if tm(k) <= L]
                return max(ok)[1] if ok else None
            cr = choix(series["réseau"])
            cf = {f: choix(series[f]) for f in ("regle", "fin", "borne")}
            cf = {f: c for f, c in cf.items() if c}
            if not cr or not cf:
                rows.append((L, cr, None, None, None, None)); continue
            bf = min(cf, key=lambda f: ec(series[f][cf[f]]).mean())
            er, ef = ec(series["réseau"][cr]), ec(series[bf][cf[bf]])
            rows.append((L, cr, f"{bf} {cf[bf]}", er, ef, wilcoxon(er, ef)))
        ps = holm([r[5] for r in rows if r[5] is not None]); it = iter(ps)
        md += ["\n| Limite | Réseau (réglage) | Meilleur filtre (réglage) | Écart réseau | Écart filtre | Différence | IC 95 % | p Holm |",
               "|---|---|---|---|---|---|---|---|"]
        for L, cr, cf, er, ef, p in rows:
            if p is None:
                md.append(f"| {L} s | {cr} | {cf} | — | — | — | — | — |"); continue
            d = er - ef; lo, hi = bootstrap_ic(d)
            md.append(f"| {L} s | {cr} | {cf} | {er.mean():+.2f} % | {ef.mean():+.2f} % | {d.mean():+.2f} | [{lo:+.2f} ; {hi:+.2f}] | {next(it):.3g} |")
    open(os.path.join(ICI, "resultats", "revision_D2.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
