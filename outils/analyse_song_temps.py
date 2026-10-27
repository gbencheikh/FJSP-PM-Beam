"""Analyse PRÉ-DÉCLARÉE de E10s (9/10/2026, avant tout calcul ; PROTOCOLE § 3 quater) : faisceau guidé contre Song et al.
au même temps mur, même cœur, par instance (FJSP classique, Brandimarte + Hurink vdata, 50 instances).
Unité : l'instance (Song : moyenne des graines 0–2). Écart = C_max faisceau / C_max Song − 1. Wilcoxon apparié
bilatéral, égalités exclues ; Holm sur les 3 réglages. Scénario par réglage : A = faisceau significativement
meilleur ; B = non significatif ; C = Song significativement meilleur. Descriptif : « nettement » si |écart| ≥ 2 points.
Rapporté aussi : dépassement de budget de Song (médiane, maximum) et nombre de tirages obtenus.

  python -m outils.analyse_song_temps     # -> experiences_article1/resultats/e10s_song_temps.md|csv
"""
import csv, os, sys
from collections import defaultdict
import numpy as np
from scipy.stats import wilcoxon

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from experiences_article1.statistiques import BANQUE, holm   # noqa: E402

SONG = os.path.join(RACINE, "externe", "resultats_song_temps.csv")
REGLAGES = {"5x4": "faisceau=5,k=4", "10x4": "faisceau=10,k=4", "50x5": "faisceau=50,k=5"}


def main():
    fa = defaultdict(dict)
    for r in csv.DictReader(open(BANQUE, encoding="utf-8")):
        if r["methode"] == "RL:imit-ft-mono" and float(r["facteur_seuil"]) == 1000:
            fa[r["config"]][r["instance"]] = float(r["cmax"])
    so = defaultdict(lambda: defaultdict(list)); dep = defaultdict(list); nt = defaultdict(list)
    for r in csv.DictReader(open(SONG, encoding="utf-8")):
        so[r["reglage"]][r["instance"]].append(float(r["cmax"]))
        dep[r["reglage"]].append(float(r["depassement_s"])); nt[r["reglage"]].append(int(r["n_tirages"]))
    lignes = []
    for nom, cfg in REGLAGES.items():
        noms = sorted(n for n in so[nom] if n in fa[cfg])
        x = np.array([fa[cfg][n] for n in noms]); y = np.array([np.mean(so[nom][n]) for n in noms])
        d = 100 * (x / y - 1)
        p = float(wilcoxon(x, y).pvalue) if (np.abs(x - y) > 1e-9).any() else 1.0
        lignes.append(dict(reglage=nom, instances=len(noms), ecart_moyen=float(d.mean()),
                           V=int((x < y - 1e-9).sum()), E=int((abs(x - y) <= 1e-9).sum()), D=int((x > y + 1e-9).sum()), p=p,
                           tirages_song_median=int(np.median(nt[nom])), depassement_median_s=float(np.median(dep[nom])),
                           depassement_max_s=float(np.max(dep[nom]))))
    for l, ph in zip(lignes, holm([l["p"] for l in lignes])):
        l["p_holm"] = float(ph)
        sig = ph < 0.05
        l["scenario"] = ("A (faisceau meilleur)" if sig and l["V"] > l["D"] else "C (Song meilleur)" if sig else "B (non significatif)")
        l["descriptif"] = "nettement" if abs(l["ecart_moyen"]) >= 2 else ""
    out = os.path.join(RACINE, "experiences_article1", "resultats", "e10s_song_temps")
    with open(out + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0])); w.writeheader(); w.writerows(lignes)
    md = ["# E10s — faisceau guidé contre Song et al. au même temps mur, sur un cœur (FJSP classique)\n",
          "Budget de Song = temps mur du faisceau sur la même instance (E10). Écart = faisceau / Song − 1 ; V/E/D du faisceau ; "
          "Wilcoxon apparié, Holm sur 3 tests.\n",
          "| Faisceau | Instances | Écart moyen | V/E/D | p (Holm) | Scénario | Tirages de Song (médiane) | Dépassement de Song (médiane / max, s) |",
          "|---|---|---|---|---|---|---|---|"]
    md += [f"| {l['reglage']} | {l['instances']} | {l['ecart_moyen']:+.2f} % {l['descriptif']} | {l['V']}/{l['E']}/{l['D']} | "
           f"{l['p_holm']:.2g} | {l['scenario']} | {l['tirages_song_median']} | {l['depassement_median_s']:.1f} / {l['depassement_max_s']:.1f} |"
           for l in lignes]
    open(out + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
