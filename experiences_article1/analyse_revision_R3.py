"""Analyse de R3 (PROTOCOLE § 3 sexies) : graines d'entraînement 0, 1, 2 du réseau (imitation puis PPO puis auto-imitation,
sélection du meilleur point sur la validation). Déclaré : dispersion sur 3 graines de l'écart au recuit 50k (faisceau 5×4
et 50×5 ; ajoutés : glouton, 100 tirages). Exploratoire (non déclaré, présenté comme tel) : chaque graine contre le meilleur
filtre non appris de R1 au même réglage (Wilcoxon, Holm sur 6 tests) ; équivalence ±1 % (IC bootstrap 90 %) au réglage 50×5.

  python -m experiences_article1.analyse_revision_R3   -> resultats/revision_R3.md
"""
import os, sys
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import charger, bootstrap_ic, wilcoxon, holm, INSTANCES_REGLAGE, BANQUE  # noqa
from metaheuristiques.instances import fichiers  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
GRAINES = [("0", "RL:imit-ft"), ("1", "RL:imit-ft-g1"), ("2", "RL:imit-ft-g2")]
CONFIGS = [("glouton", "glouton"), ("100 tirages", "echantillons=100"), ("faisceau 5x4", "faisceau=5,k=4"),
           ("faisceau 50x5", "faisceau=50,k=5")]
MEILLEUR_FILTRE = {"faisceau=5,k=4": ("Faisceau:filtre-regle", "faisceau=5,k=4,filtre=regle"),
                   "faisceau=50,k=5": ("Faisceau:filtre-borne", "faisceau=50,k=5,filtre=borne")}


def ic90(x, n=10000, g=0):
    r = np.random.default_rng(g)
    m = x[r.integers(0, len(x), (n, len(x)))].mean(1)
    return float(np.percentile(m, 5)), float(np.percentile(m, 95))


def main():
    v, t, ev = charger(BANQUE, "A", 1.0)
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"])]
    noms = [n for n in noms if n not in INSTANCES_REGLAGE]
    m = lambda k, n: float(np.mean(v[k][n]))
    def cm(k):
        manq = [n for n in noms if n not in v[k]]
        assert not manq, (k, len(manq))
        return np.array([m(k, n) for n in noms])
    ref = cm(REF)
    md = ["# R3 — trois graines d'entraînement\n", f"{len(noms)} instances de test ; écart au recuit Taguchi 50k.\n",
          "## Dispersion (déclaré)\n", "| Réglage | Graine 0 | Graine 1 | Graine 2 | Moyenne | Étendue |", "|---|---|---|---|---|---|"]
    for lab, c in CONFIGS:
        g = [100 * np.mean(cm((meth, c)) / ref - 1) for _, meth in GRAINES]
        md.append(f"| {lab} | " + " | ".join(f"{x:+.2f} %" for x in g) + f" | {np.mean(g):+.2f} % | {max(g) - min(g):.2f} pt |")
    md += ["\n## Contre le meilleur filtre non appris de R1 (exploratoire, Holm sur 6 tests)\n",
           "| Réglage | Graine | Écart réseau | Écart filtre | Différence | IC 95 % | p brut | p Holm |", "|---|---|---|---|---|---|---|---|"]
    rows = []
    for c, kf in MEILLEUR_FILTRE.items():
        ef = 100 * (cm(kf) / ref - 1)
        for gr, meth in GRAINES:
            er = 100 * (cm((meth, c)) / ref - 1)
            d = er - ef
            rows.append([c, gr, er.mean(), ef.mean(), d.mean(), bootstrap_ic(d), wilcoxon(er, ef)])
    for r, p in zip(rows, holm([r[6] for r in rows])):
        md.append(f"| {r[0]} | {r[1]} | {r[2]:+.2f} % | {r[3]:+.2f} % | {r[4]:+.2f} | [{r[5][0]:+.2f} ; {r[5][1]:+.2f}] | "
                  f"{r[6]:.2g} | {p:.2g} |")
    md += ["\n## Équivalence ±1 % au recuit, faisceau 50×5 (exploratoire pour les graines 1 et 2)\n",
           "| Graine | Écart moyen | IC 90 % | Dans ±1 % ? |", "|---|---|---|---|"]
    for gr, meth in GRAINES:
        e = 100 * (cm((meth, "faisceau=50,k=5")) / ref - 1)
        lo, hi = ic90(e)
        md.append(f"| {gr} | {e.mean():+.2f} % | [{lo:+.2f} ; {hi:+.2f}] | {'oui' if lo > -1 and hi < 1 else 'non'} |")
    out = os.path.join(ICI, "resultats", "revision_R3.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
