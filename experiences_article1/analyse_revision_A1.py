"""Analyse DÉCLARÉE de A1 (PROTOCOLE, entrée du 04/11/2026) : décodeur actif contre semi-actif pour recuit et tabou.

14 instances (Brandimarte, Kacem), 50 000 évaluations, départ heuristique, Taguchi, graines 0–4, régime A et classique.
Par méthode et par régime : écart moyen au meilleur connu (meilleurs_connus_article.csv), nombre d'instances à l'optimum
prouvé (moyenne des graines), différence actif − semi-actif par instance (moyenne des graines), Wilcoxon, Holm sur 4 tests.
Règle : si le recuit à décodeur actif est meilleur de plus de 1 point en moyenne avec p Holm < 0,05 en régime A, la
référence est jugée affaiblie par son décodeur (texte et, si possible, campagne étendue) ; sinon, l'article indique que le
décodeur n'explique pas l'écart du recuit (Kacem, Brandimarte).
  python -m experiences_article1.analyse_revision_A1 -> resultats/revision_A1.md
"""
import csv, os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import charger, wilcoxon, holm, bootstrap_ic, BANQUE  # noqa
from metaheuristiques.instances import fichiers  # noqa


def main():
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "Kacem"])]
    mc = {(r["instance"], r["regime"]): r for r in csv.DictReader(open(os.path.join(ICI, "resultats", "meilleurs_connus_article.csv"), encoding="utf-8"))}
    md = ["# A1 — décodeur actif contre semi-actif (analyse déclarée)\n", f"{len(noms)} instances (Brandimarte, Kacem) ; graines 0–4.\n",
          "| Régime | Méthode | Écart semi-actif | Écart actif | Optima semi / actif | Différence | IC 95 % | p Holm (4) |", "|---|---|---|---|---|---|---|---|"]
    rows = []
    for reg, fs in (("A", 1.0), ("classique", 1000.0)):
        v = charger(BANQUE, "A", fs)[0]
        bk = {n: float(mc[(n, reg)]["meilleur_cmax"]) for n in noms}
        opt = {n: mc[(n, reg)]["statut"] == "optimum prouvé" for n in noms}
        for m in ("Recuit simulé", "Recherche tabou"):
            ks = (m, "evals=50000,depart=heuristique,params=taguchi")
            ka = (m, "evals=50000,depart=heuristique,params=taguchi-actif")
            es = np.array([100 * (np.mean(v[ks][n]) / bk[n] - 1) for n in noms])
            ea = np.array([100 * (np.mean(v[ka][n]) / bk[n] - 1) for n in noms])
            os_ = sum(opt[n] and np.mean(v[ks][n]) <= bk[n] + 1e-9 for n in noms)
            oa = sum(opt[n] and np.mean(v[ka][n]) <= bk[n] + 1e-9 for n in noms)
            rows.append(dict(reg=reg, m=m, es=es, ea=ea, os=os_, oa=oa, p=wilcoxon(ea, es)))
    for x, q in zip(rows, holm([x["p"] for x in rows])):
        d = x["ea"] - x["es"]; lo, hi = bootstrap_ic(d); x["ph"] = q; x["d"] = d.mean()
        md.append(f"| {x['reg']} | {x['m']} | {x['es'].mean():+.2f} % | {x['ea'].mean():+.2f} % | {x['os']} / {x['oa']} | "
                  f"{d.mean():+.2f} | [{lo:+.2f} ; {hi:+.2f}] | {q:.3g} |")
    sa = [x for x in rows if x["reg"] == "A" and x["m"] == "Recuit simulé"][0]
    affaibli = sa["d"] < -1 and sa["ph"] < 0.05
    md.append(f"\n**Verdict (règle déclarée)** : différence du recuit en régime A {sa['d']:+.2f} point (p Holm {sa['ph']:.3g}) → "
              + ("référence affaiblie par son décodeur." if affaibli else "le décodeur n'explique pas l'écart du recuit."))
    open(os.path.join(ICI, "resultats", "revision_A1.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
