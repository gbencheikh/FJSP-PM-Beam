"""Analyse DÉCLARÉE de B3 (PROTOCOLE, entrée du 04/11/2026) : faisceau guidé contre Song et al. au même temps mur, même
cœur, sur Hurink edata et rdata (36 instances de E10b, problème classique, seuils ×1000 comme E10s). Même protocole et même
règle que E10s : unité = instance (Song : moyenne des graines 0–2) ; écart = C_max faisceau / C_max Song − 1 ; Wilcoxon apparié
bilatéral ; Holm sur les 3 réglages ; scénario A (faisceau significativement meilleur), B (non significatif), C (Song meilleur).
  python -m experiences_article1.analyse_revision_B3 -> resultats/revision_B3.md
"""
import csv, os, sys
from collections import defaultdict
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI); sys.path.insert(0, RACINE)
from experiences_article1.statistiques import BANQUE, holm, wilcoxon, bootstrap_ic  # noqa: E402

SONG = os.path.join(RACINE, "externe", "resultats_song_temps_E10b.csv")
REGLAGES = {"5x4": "faisceau=5,k=4", "10x4": "faisceau=10,k=4", "50x5": "faisceau=50,k=5"}


def main():
    fa = defaultdict(dict)
    for r in csv.DictReader(open(BANQUE, encoding="utf-8")):
        if r["methode"] == "RL:imit-ft-mono" and float(r["facteur_seuil"]) == 1000:
            fa[r["config"]][r["instance"]] = float(r["cmax"])
    so = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(SONG, encoding="utf-8")):
        so[r["reglage"]][r["instance"]].append(float(r["cmax"]))
    rows = []
    for reg, cfg in REGLAGES.items():
        noms = sorted(n for n in so[reg] if n in fa[cfg])
        d = np.array([100 * (fa[cfg][n] / np.mean(so[reg][n]) - 1) for n in noms])
        rows.append(dict(reg=reg, n=len(noms), d=d, p=wilcoxon(d, np.zeros_like(d))))
    md = ["# B3 — faisceau guidé contre Song et al. au même temps (Hurink edata et rdata)\n",
          "| Réglage | Instances | Écart moyen | IC 95 % | V/E/D (faisceau) | p Holm | Scénario |", "|---|---|---|---|---|---|---|"]
    for x, q in zip(rows, holm([x["p"] for x in rows])):
        lo, hi = bootstrap_ic(x["d"]); m = x["d"].mean()
        sc = "A" if (q < 0.05 and m < 0) else "C" if (q < 0.05 and m > 0) else "B"
        md.append(f"| {x['reg']} | {x['n']} | {m:+.2f} % | [{lo:+.2f} ; {hi:+.2f}] | {(x['d'] < -1e-9).sum()}/{(abs(x['d']) <= 1e-9).sum()}/"
                  f"{(x['d'] > 1e-9).sum()} | {q:.3g} | {sc} |")
    open(os.path.join(ICI, "resultats", "revision_B3.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
