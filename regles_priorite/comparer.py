"""Lance les règles de priorité sur les instances et enregistre chaque résultat dans la banque.

  python -m regles_priorite.comparer                       # Brandimarte + Hurink + Kacem, seuil ×1
  python -m regles_priorite.comparer --facteur-seuil 0.7
  python -m regles_priorite.comparer --forcer              # relancer même si déjà dans la banque

Une (instance, règle, facteur de seuil) déjà présente dans banque_resultats/resultats.csv n'est pas
relancée. Le planning de chaque exécution est sauvegardé dans banque_resultats/solutions/.
Le tableau récapitulatif est relu depuis la banque (resultats_regles/resume_seuil<x>.md).
"""
import argparse, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jssp_pm.fjsp_env3 import run3
from jssp_pm.fjsp_cpsat import check
from regles_priorite.regles import ReglePriorite, REGLES_OPERATION, REGLES_MACHINE, environnement
from metaheuristiques.instances import charger_instances
from banque_resultats import banque

REGIME = "A"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "Hurink", "Kacem"])
    ap.add_argument("--facteur-seuil", type=float, default=1.0)
    ap.add_argument("--forcer", action="store_true")
    ap.add_argument("--sortie", default="resultats_regles")
    a = ap.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    instances = charger_instances(a.familles, regime=REGIME, facteur_seuil=a.facteur_seuil)
    regles = [ReglePriorite(o, m) for m in REGLES_MACHINE for o in REGLES_OPERATION if o != "WSPT"]
    env = environnement()
    deja = banque.cles_existantes()
    lancees = 0
    for inst in instances:
        for r in regles:
            if not a.forcer and banque.cle(inst.name, REGIME, a.facteur_seuil, r.name) in deja:
                continue
            t0 = time.time()
            m, sim = run3(env, r, inst)
            check(inst, sim.segments)                      # planning valide, aucune panne
            banque.ajouter(inst.name, REGIME, a.facteur_seuil, r.name, "", 0, m["cmax"], m["pm"],
                           m["breakdowns"], time.time() - t0, sim.segments)
            lancees += 1
    print(f"{lancees} exécutions lancées, les autres étaient déjà dans la banque.")

    # récapitulatif relu depuis la banque
    noms = {i.name for i in instances}
    lignes = [r for r in banque.charger() if r["instance"] in noms and r["regime"] == REGIME
              and float(r["facteur_seuil"]) == a.facteur_seuil and r["methode"] in {x.name for x in regles}]
    table = {(r["instance"], r["methode"]): float(r["cmax"]) for r in lignes}
    noms = sorted(noms)
    meilleur = {n: min(table[(n, r.name)] for r in regles) for n in noms}
    res = []
    for r in regles:
        c = np.array([table[(n, r.name)] for n in noms])
        e = np.array([table[(n, r.name)] / meilleur[n] - 1 for n in noms])
        res.append((e.mean(), r.name, c.mean(), int((e <= 1e-9).sum())))
    res.sort()
    md = [f"# Règles de priorité — {len(noms)} instances, facteur de seuil {a.facteur_seuil:g}\n",
          "| Rang | Règle (opération + machine) | C_max moyen | Écart moyen à la meilleure règle | Nb de fois meilleure |",
          "|---|---|---|---|---|"]
    for i, (e, nom, c, nb) in enumerate(res, 1):
        md.append(f"| {i} | {nom} | {c:.1f} | {100 * e:+.1f} % | {nb} |")
    open(f"{a.sortie}/resume_seuil{a.facteur_seuil:g}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
