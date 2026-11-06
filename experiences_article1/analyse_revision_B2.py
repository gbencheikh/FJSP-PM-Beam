"""Analyse DÉCLARÉE de B2 (PROTOCOLE, entrée du 04/11/2026) : deux autres tirages des facteurs φ_k (graines 1 et 2 ; protocole :
graine 0). Pour chaque tirage, banque resultats_phi<g>.csv : même règle que R4 (réseau contre filtres regle et borne, 5×4 et
50×5, Holm sur 4 ; la conclusion de R1 tient si le réseau ne bat significativement le meilleur des deux filtres à aucun
réglage), TOST ±1 % du faisceau 50×5 contre le recuit 50k (graines 0–2), test groupé (moyenne des 2 différences au meilleur filtre).
  python -m experiences_article1.analyse_revision_B2 -> resultats/revision_B2.md
"""
import os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI); sys.path.insert(0, RACINE)
from experiences_article1.statistiques import charger, wilcoxon, holm, bootstrap_ic, INSTANCES_REGLAGE  # noqa
from metaheuristiques.instances import fichiers  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")


def ic90(d, n=10000):
    r = np.random.default_rng(0); m = d[r.integers(0, len(d), (n, len(d)))].mean(1)
    return np.percentile(m, 5), np.percentile(m, 95)


def main():
    noms = [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"]))
            if n not in INSTANCES_REGLAGE]
    md = ["# B2 — autres tirages des facteurs φ_k (analyse déclarée)\n"]
    for g in (1, 2):
        v = charger(os.path.join(RACINE, "banque_resultats", f"resultats_phi{g}.csv"), "A", 1.0)[0]
        ref = {n: np.mean(v[REF][n]) for n in noms}
        ec = lambda k: np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in noms])
        rows, ds = [], []
        for B, K in [(5, 4), (50, 5)]:
            er = ec(("RL:imit-ft", f"faisceau={B},k={K}"))
            fl = {f: ec((f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}")) for f in ("regle", "borne")}
            for f, ef in fl.items():
                rows.append(dict(r=(B, K), f=f, er=er, ef=ef, p=wilcoxon(er, ef)))
            ds.append(er - min(fl.values(), key=lambda x: x.mean()))
        for x, q in zip(rows, holm([x["p"] for x in rows])):
            x["ph"] = q
        md += [f"\n## Tirage φ (graine {g})\n", "| Réglage | Filtre | Écart réseau | Écart filtre | Différence | p Holm (4) |", "|---|---|---|---|---|---|"]
        ok = True
        for B, K in [(5, 4), (50, 5)]:
            gr = [x for x in rows if x["r"] == (B, K)]; b = min(gr, key=lambda x: x["ef"].mean())
            ok &= not (b["ph"] < 0.05 and (b["er"] - b["ef"]).mean() < 0)
            md += [f"| {B}×{K} | {x['f']}{' (meilleur)' if x is b else ''} | {x['er'].mean():+.2f} % | {x['ef'].mean():+.2f} % | "
                   f"{(x['er'] - x['ef']).mean():+.2f} | {x['ph']:.3g} |" for x in gr]
        e50 = ec(("RL:imit-ft", "faisceau=50,k=5")); lo, hi = ic90(e50)
        D = np.mean(ds, axis=0); a, b = bootstrap_ic(D)
        md.append(f"\nConclusion de R1 : {'TIENT' if ok else 'NE TIENT PAS'}. TOST ±1 % (50×5 contre recuit) : {e50.mean():+.2f} %, "
                  f"IC 90 % [{lo:+.2f} ; {hi:+.2f}] → {'équivalent' if -1 <= lo and hi <= 1 else 'non établi'}. Test groupé : "
                  f"{D.mean():+.3f}, IC 95 % [{a:+.2f} ; {b:+.2f}], p = {wilcoxon(D, np.zeros_like(D)):.3g}.")
    open(os.path.join(ICI, "resultats", "revision_B2.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
