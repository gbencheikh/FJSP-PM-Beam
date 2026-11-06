"""Analyse DÉCLARÉE de R4 (PROTOCOLE § 3 sexies, précisée le 29/10/2026) : maintenance longue (mu = 3), banque séparée
banque_resultats/resultats_mu3.csv, réseau entraîné avec mu = 1 (non réentraîné).

Principal : pour (B, K) ∈ {(5,4), (50,5)}, réseau (RL:imit-ft) contre chaque filtre (regle, borne) : écart au recuit 50k
(moyenne de 3 graines) par instance, différence, IC bootstrap 95 %, V/E/D, Wilcoxon apparié, Holm sur 4 tests.
Règle : le verdict de R1 « tient » si le réseau n'est significativement meilleur que le meilleur des deux filtres à aucun
des 2 réglages ; sinon on rapporte un changement de régime (l'apport du filtre appris dépend de la durée de maintenance).
Secondaire : équivalence ±1 % (IC bootstrap 90 %) du faisceau guidé 50×5 au recuit ; nombre moyen de maintenances.

  python -m experiences_article1.analyse_revision_R4   -> resultats/revision_R4.md
"""
import os, sys
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE)
from experiences_article1.statistiques import charger, bootstrap_ic, wilcoxon, holm, INSTANCES_REGLAGE  # noqa: E402
from metaheuristiques.instances import fichiers  # noqa: E402

BANQUE_MU3 = os.path.join(RACINE, "banque_resultats", "resultats_mu3.csv")
REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
REGLAGES = [(5, 4), (50, 5)]
FILTRES = ["regle", "borne"]


def ic90(x, n=10000, g=0):
    r = np.random.default_rng(g)
    m = x[r.integers(0, len(x), (n, len(x)))].mean(1)
    return float(np.percentile(m, 5)), float(np.percentile(m, 95))


def main():
    v, t, ev = charger(BANQUE_MU3, "A", 1.0)
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"])]
    noms = [n for n in noms if n not in INSTANCES_REGLAGE]
    def ec(k):
        manq = [n for n in noms if n not in v[k]]
        assert not manq, (k, len(manq))
        return np.array([100 * (np.mean(v[k][n]) / np.mean(v[REF][n]) - 1) for n in noms])
    rows = []
    for B, K in REGLAGES:
        er = ec(("RL:imit-ft", f"faisceau={B},k={K}"))
        for f in FILTRES:
            ef = ec((f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}"))
            d = er - ef
            rows.append(dict(r=f"{B}x{K}", f=f, er=er.mean(), ef=ef.mean(), d=d.mean(), ic=bootstrap_ic(d),
                             V=int((d < -1e-9).sum()), E=int((abs(d) <= 1e-9).sum()), D=int((d > 1e-9).sum()),
                             p=wilcoxon(er, ef)))
    for x, p in zip(rows, holm([x["p"] for x in rows])):
        x["ph"] = p
    md = ["# R4 — maintenance longue (mu = 3), réseau non réentraîné\n",
          f"{len(noms)} instances de test ; référence : recuit Taguchi 50k (moyenne de 3 graines), même banque mu = 3.\n",
          "| B × K | Filtre | Écart réseau | Écart filtre | Différence | IC 95 % | V/E/D (réseau) | p Holm |",
          "|---|---|---|---|---|---|---|---|"]
    for x in rows:
        md.append(f"| {x['r']} | {x['f']} | {x['er']:+.2f} % | {x['ef']:+.2f} % | {x['d']:+.2f} | "
                  f"[{x['ic'][0]:+.2f} ; {x['ic'][1]:+.2f}] | {x['V']}/{x['E']}/{x['D']} | {x['ph']:.2g} |")
    ok = []
    for B, K in REGLAGES:
        g = [x for x in rows if x["r"] == f"{B}x{K}"]
        best = min(g, key=lambda x: x["ef"])
        ok.append(best["ph"] < 0.05 and best["d"] < 0)
        md.append(f"\nMeilleur filtre à {B}x{K} : {best['f']} ; réseau significativement meilleur : {'oui' if ok[-1] else 'non'}.")
    md.append(f"\n**Verdict R4** : {'le verdict de R1 tient' if not any(ok) else 'changement de régime : le filtre appris apporte avec mu = 3'}.\n")
    e = ec(("RL:imit-ft", "faisceau=50,k=5"))
    lo, hi = ic90(e)
    md.append(f"Équivalence ±1 % (faisceau guidé 50×5 contre recuit) : écart {e.mean():+.2f} %, IC 90 % [{lo:+.2f} ; {hi:+.2f}] "
              f"→ {'oui' if lo > -1 and hi < 1 else 'non'}.\n")
    md.append("Maintenances moyennes par instance (moyenne des graines) :")
    import csv
    pm = {}
    for r in csv.DictReader(open(BANQUE_MU3, encoding="utf-8")):
        if r["instance"] in noms:
            pm.setdefault((r["methode"], r["config"]), []).append(float(r["maintenances"]))
    for k, x in sorted(pm.items()):
        md.append(f"- {k[0]} [{k[1]}] : {np.mean(x):.1f}")
    out = os.path.join(ICI, "resultats", "revision_R4.md")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
