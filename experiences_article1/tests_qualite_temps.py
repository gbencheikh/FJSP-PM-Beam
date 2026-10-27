"""Tests appariés par point de TEMPS (E10, un processus, machine au repos) — même règle que tests_qualite_budget.py (E3t) :
pour chaque budget b (1, 2, 5, 10, 20, 40 s) du recuit et du tabou en mode « mono », on compare au faisceau guidé
« RL:imit-ft-mono » dont le temps mur moyen (réseau compris) est le plus grand SANS dépasser b. Écarts au recuit
50 000 évaluations ; Wilcoxon apparié par instance ; Holm sur tous les tests. Sous-ensemble = instances de E10.

  python -m experiences_article1.tests_qualite_temps                      # E10 (54 instances) -> resultats/tests_qualite_temps.md
  python -m experiences_article1.tests_qualite_temps --sous-ensemble E10b  # E10b (36) -> resultats/tests_qualite_temps_E10b.md
  python -m experiences_article1.tests_qualite_temps --sous-ensemble union # descriptif (90) -> ..._union.md

14/10/2026 : option --sous-ensemble (E10b). Le défaut reproduit exactement l'analyse E10 (instances de E10 seulement),
même quand la banque contient aussi les mesures de E10b.
"""
import argparse, csv, os, sys
from collections import defaultdict
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import BANQUE, wilcoxon, holm, bootstrap_ic   # noqa: E402
from metaheuristiques.instances import fichiers                                        # noqa: E402

SOUS_ENSEMBLES = {"E10": ["Brandimarte", "Kacem", "HurinkVdataLa"],
                  "E10b": ["HurinkEdataLaPair", "HurinkRdataLaPair"]}
SOUS_ENSEMBLES["union"] = SOUS_ENSEMBLES["E10"] + SOUS_ENSEMBLES["E10b"]

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sous-ensemble", choices=list(SOUS_ENSEMBLES), default="E10")
    se = ap.parse_args().sous_ensemble
    cible = {os.path.splitext(os.path.basename(f))[0] for f in fichiers(SOUS_ENSEMBLES[se])}
    v, t = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(BANQUE, encoding="utf-8")):
        if r["regime"] == "A" and float(r["facteur_seuil"]) == 1 and r["cmax"]:
            k = (r["methode"], r["config"])
            v[k][r["instance"]].append(float(r["cmax"])); t[k][r["instance"]].append(float(r["temps_s"]))
    noms = sorted(n for n in v[("RL:imit-ft-mono", "faisceau=5,k=4")] if n in cible)
    moy = lambda k: np.array([np.mean(v[k][n]) for n in noms])
    tm = lambda k: float(np.mean([np.mean(t[k][n]) for n in noms]))
    ref = moy(REF)
    fx = sorted((tm(k), k) for k in v if k[0] == "RL:imit-ft-mono" and all(n in v[k] for n in noms))
    rows = []
    for mh, lab in (("Recuit simulé", "SA"), ("Recherche tabou", "TS")):
        for b in (1, 2, 5, 10, 20, 40):
            ks = [k for k in v if k[0] == mh and k[1].startswith(f"budget={b}s,") and "mono" in k[1]]
            if not ks:
                continue
            k = ks[0]
            ok = [f for f in fx if f[0] <= b]
            if not ok:
                continue
            tf, kf = ok[-1]
            xf, xm = moy(kf), moy(k)
            d = 100 * (xf / xm - 1)
            rows.append(dict(mh=lab, b=b, f=kf[1], tf=tf, ef=100 * np.mean(xf / ref - 1), em=100 * np.mean(xm / ref - 1),
                             d=d.mean(), ic=bootstrap_ic(d), V=int((xf < xm - 1e-9).sum()),
                             E=int((abs(xf - xm) <= 1e-9).sum()), D=int((xf > xm + 1e-9).sum()), p=wilcoxon(xf, xm)))
    for r, ph in zip(rows, holm([r["p"] for r in rows])):
        r["ph"] = ph
    md = [f"# {se} — tests par point de TEMPS (un processus, machine au repos), {len(noms)} instances\n",
          "Appariement (même règle que E3t) : faisceau guidé au plus grand temps moyen ≤ budget de la métaheuristique. "
          f"Écarts au recuit 50 000 évaluations (même sous-ensemble). Wilcoxon apparié, Holm sur {len(rows)} tests. "
          "Coût du réseau INCLUS (temps mur).\n",
          "| Méta. | Budget (s) | Faisceau (temps moyen) | Écart faisceau | Écart méta. | Diff. | IC 95 % | V/E/D | p (Holm) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['mh']} | {r['b']} | {r['f'].replace('faisceau=', '').replace(',k=', '×')} ({r['tf']:.2f} s) | "
                  f"{r['ef']:+.2f} % | {r['em']:+.2f} % | {r['d']:+.2f} % | [{r['ic'][0]:+.2f} ; {r['ic'][1]:+.2f}] | "
                  f"{r['V']}/{r['E']}/{r['D']} | {r['ph']:.2g} |")
    open(os.path.join(ICI, "resultats", "tests_qualite_temps.md" if se == "E10" else f"tests_qualite_temps_{se}.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
