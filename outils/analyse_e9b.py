"""Analyse PRÉ-DÉCLARÉE d'E9b (règles fixées le 9/10/2026, avant tout calcul ; PROTOCOLE § 3 ter).

Primaire (ressources égales) : CP-SAT seul, 1 fil, au budget apparié de chaque faisceau déclaré (5×4, 10×4, 50×5 ;
budgets = temps murs moyens mesurés par E10, `experiences_article1/budgets_e9b.json`) contre ce faisceau, sur les
127 instances de test. Secondaire (observation complémentaire, jamais mêlée au primaire) : même chose avec 8 fils.
  - Instance sans solution pour CP-SAT dans le budget = DÉFAITE de CP-SAT, de rang maximal dans le Wilcoxon
    (différence plus grande que toute différence observée) ; nombre d'échecs rapporté par budget.
  - Écart moyen = C_max CP-SAT / C_max faisceau − 1, sur les instances résolues seulement (n indiqué).
  - Wilcoxon apparié bilatéral par instance (égalités exclues) ; Holm sur les 3 tests primaires ; Holm séparé sur
    les 3 tests secondaires.
  - Scénario, par test primaire : A = CP-SAT significativement MOINS bon (p Holm < 0,05) ; B = non significatif ;
    C = CP-SAT significativement MEILLEUR. Descriptif seulement : « nettement » si |écart moyen| ≥ 2 points.
Sortie : experiences_article1/resultats/e9b.md|csv

  python -m outils.analyse_e9b
"""
import csv, json, os, sys
from collections import defaultdict
import numpy as np
from scipy.stats import wilcoxon

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from experiences_article1.statistiques import BANQUE, INSTANCES_REGLAGE, holm   # noqa: E402
from metaheuristiques.instances import fichiers                                # noqa: E402

RES = os.path.join(RACINE, "experiences_article1", "resultats")
FAISCEAUX = {"5x4": "faisceau=5,k=4", "10x4": "faisceau=10,k=4", "50x5": "faisceau=50,k=5"}


def main():
    budgets = json.load(open(os.path.join(RACINE, "experiences_article1", "budgets_e9b.json"), encoding="utf-8"))
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"])]
    noms = [n for n in noms if n not in INSTANCES_REGLAGE]
    v = defaultdict(dict)
    for r in csv.DictReader(open(BANQUE, encoding="utf-8")):
        if r["regime"] == "A" and float(r["facteur_seuil"]) == 1 and r["cmax"]:
            v[(r["methode"], r["config"])].setdefault(r["instance"], []).append(float(r["cmax"]))
    lignes = []
    for fils, role in ((1, "primaire"), (8, "secondaire")):
        tests = []
        for nomf, cfg in FAISCEAUX.items():
            t = int(budgets[nomf])
            cp = v[("CP-SAT seul", f"temps={t}s,fils={fils},sans_depart")]
            fa = v[("RL:imit-ft", cfg)]
            res = [n for n in noms if n in cp]
            ech = [n for n in noms if n not in cp]
            d = np.array([100 * (np.mean(cp[n]) / np.mean(fa[n]) - 1) for n in res])
            dmax = np.abs(d).max() if len(d) else 0.0
            dw = np.concatenate([d, np.full(len(ech), dmax + 1.0)])     # échec = défaite de rang maximal
            p = float(wilcoxon(dw).pvalue) if (np.abs(dw) > 1e-9).any() else 1.0
            tests.append(dict(role=role, faisceau=nomf, budget_s=t, fils=fils, resolues=len(res), echecs=len(ech),
                              ecart_moyen=float(d.mean()) if len(d) else float("nan"),
                              V_cpsat=int((dw < -1e-9).sum()), E=int((np.abs(dw) <= 1e-9).sum()),
                              D_cpsat=int((dw > 1e-9).sum()), p=p))
        for tt, ph in zip(tests, holm([x["p"] for x in tests])):
            tt["p_holm"] = float(ph)
            sig = ph < 0.05
            tt["scenario"] = ("C (CP-SAT meilleur)" if sig and tt["V_cpsat"] > tt["D_cpsat"] else
                              "A (CP-SAT moins bon)" if sig else "B (non significatif)") if role == "primaire" else "–"
            tt["descriptif"] = "nettement" if abs(tt["ecart_moyen"]) >= 2 else ""
        lignes += tests
    with open(os.path.join(RES, "e9b.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lignes[0])); w.writeheader(); w.writerows(lignes)
    md = ["# E9b — CP-SAT seul contre le faisceau guidé, budgets appariés (analyse pré-déclarée)\n",
          "Écart = C_max CP-SAT / C_max faisceau − 1 sur les instances résolues ; échec = défaite de CP-SAT de rang maximal ; "
          "Wilcoxon apparié, Holm par groupe (primaire 1 fil ; secondaire 8 fils).\n",
          "| Analyse | Faisceau | Budget (s) | Fils | Résolues | Échecs | Écart moyen (résolues) | CP-SAT V/E/D | p (Holm) | Scénario |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for l in lignes:
        md.append(f"| {l['role']} | {l['faisceau']} | {l['budget_s']} | {l['fils']} | {l['resolues']} | {l['echecs']} | "
                  f"{l['ecart_moyen']:+.2f} % {l['descriptif']} | {l['V_cpsat']}/{l['E']}/{l['D_cpsat']} | {l['p_holm']:.2g} | {l['scenario']} |")
    open(os.path.join(RES, "e9b.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
