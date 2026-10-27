"""Tests appariés par point de budget de la courbe qualité / plannings (amendement 3 du 7/10/2026).

Règle d'appariement (fixée le 7/10/2026, conservatrice pour le faisceau) : pour chaque métaheuristique M (recuit,
tabou) et chaque budget b de E3/E2 (2 000 … 200 000 évaluations), on compare M à b au faisceau guidé de la grille
dont le nombre moyen de plannings complets évalués (sur les 127 instances) est le plus grand SANS dépasser b :
le faisceau n'a jamais plus de budget que la métaheuristique. Unité : l'instance (moyenne des graines de M) ;
Wilcoxon apparié bilatéral, égalités exclues ; Holm sur l'ensemble des tests du graphique (recuit et tabou).
Écarts exprimés comme dans la figure : au recuit Taguchi 50 000. « Plannings évalués » = plannings COMPLETS
évalués (complétions du moteur pour le faisceau, solutions décodées pour M) ; le coût d'inférence du réseau
n'est pas compté (→ E10, temps mur).

  python -m experiences_article1.tests_qualite_budget     # -> resultats/tests_qualite_budget.md|csv
"""
import csv, os, re, sys
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import (charger, BANQUE, INSTANCES_REGLAGE, moyenne_instances,   # noqa: E402
                                               wilcoxon, holm, bootstrap_ic)
from metaheuristiques.instances import fichiers                                                     # noqa: E402

FAM = ["Brandimarte", "HurinkLa", "Kacem"]
REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
MH = {"Recuit simulé": "SA", "Recherche tabou": "TS"}


def main():
    v, _, ev = charger(BANQUE, "A", 1.0)
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(FAM)]
    noms = [n for n in noms if n not in INSTANCES_REGLAGE]
    moy = lambda k: np.array([np.mean(v[k][n]) for n in noms])
    ref = moy(REF)
    faisceaux = []
    for (m, c), d in v.items():
        if m == "RL:imit-ft" and re.fullmatch(r"faisceau=\d+,k=\d+", c) and all(n in d for n in noms):
            faisceaux.append((moyenne_instances(ev[(m, c)], noms), c))
    faisceaux.sort()
    lignes = []
    for (m, c), d in sorted(v.items()):
        mm = re.fullmatch(r"evals=(\d+),depart=heuristique,params=taguchi", c)
        if m not in MH or not mm or not all(n in d for n in noms):
            continue
        b = int(mm.group(1))
        ok = [f for f in faisceaux if f[0] <= b]
        if not ok:
            continue
        e_f, c_f = ok[-1]
        xf, xm = moy(("RL:imit-ft", c_f)), moy((m, c))
        dlt = 100 * (xf / xm - 1)
        lignes.append(dict(mh=MH[m], budget=b, faisceau=c_f.replace("faisceau=", "").replace(",k=", "×"),
                           plannings_faisceau=round(e_f), ecart_faisceau=100 * np.mean(xf / ref - 1),
                           ecart_mh=100 * np.mean(xm / ref - 1), diff=float(np.mean(dlt)),
                           ic=bootstrap_ic(dlt), V=int((xf < xm - 1e-9).sum()), E=int((abs(xf - xm) <= 1e-9).sum()),
                           D=int((xf > xm + 1e-9).sum()), p=wilcoxon(xf, xm)))
    for l, ph in zip(lignes, holm([l["p"] for l in lignes])):
        l["p_holm"] = float(ph)
    lignes.sort(key=lambda l: (l["mh"], l["budget"]))
    base = os.path.join(ICI, "resultats", "tests_qualite_budget")
    with open(base + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metaheuristique", "budget", "faisceau", "plannings_faisceau", "ecart_faisceau_pct", "ecart_mh_pct",
                    "diff_pct", "ic_bas", "ic_haut", "V", "E", "D", "p", "p_holm", "instances"])
        for l in lignes:
            w.writerow([l["mh"], l["budget"], l["faisceau"], l["plannings_faisceau"], round(l["ecart_faisceau"], 3),
                        round(l["ecart_mh"], 3), round(l["diff"], 3), round(l["ic"][0], 3), round(l["ic"][1], 3),
                        l["V"], l["E"], l["D"], f"{l['p']:.3g}", f"{l['p_holm']:.3g}", len(noms)])
    md = [f"# Tests par point de budget — faisceau guidé contre recuit (SA) et tabou (TS), {len(noms)} instances\n",
          "Appariement : faisceau de la grille au plus grand nombre moyen de plannings complets évalués ≤ budget de la "
          "métaheuristique. Écarts au recuit 50k ; « diff » = C_max faisceau / C_max métaheuristique − 1 (moyenne sur les "
          "instances, IC bootstrap 95 %) ; V/E/D du faisceau ; Wilcoxon apparié, Holm sur les "
          f"{len(lignes)} tests. Coût d'inférence du réseau non compté (voir E10).\n",
          "| Méta. | Budget | Faisceau (plannings) | Écart faisceau | Écart méta. | Diff. | IC 95 % | V/E/D | p (Holm) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for l in lignes:
        md.append(f"| {l['mh']} | {l['budget']:,} | {l['faisceau']} ({l['plannings_faisceau']:,}) | {l['ecart_faisceau']:+.2f} % | "
                  f"{l['ecart_mh']:+.2f} % | {l['diff']:+.2f} % | [{l['ic'][0]:+.2f} ; {l['ic'][1]:+.2f}] | "
                  f"{l['V']}/{l['E']}/{l['D']} | {l['p_holm']:.2g} |".replace(",", " "))
    open(base + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
