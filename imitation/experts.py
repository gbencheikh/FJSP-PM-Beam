"""Fabriquer les « leçons » : plannings experts sur des instances d'ENTRAÎNEMENT générées.

  python -m imitation.experts --nombre 1000 --evaluations 50000 --processus 10
  python -m imitation.experts --nombre 1000 --parametres reglage_taguchi/parametres_retenus.json

Aucune instance de test (Brandimarte, Hurink) n'est utilisée : les instances sont tirées de la
même distribution que l'entraînement PPO (train_v3.sample_v3), une graine par instance, moitié
« base » (4–15 jobs, 4–10 machines), moitié « large » (10–25 jobs, 4–15 machines).
Expert = recuit simulé (la meilleure métaheuristique sur les benchmarks), départ MWKR+EFT.

Sortie : imitation/experts.jsonl, une ligne par instance :
  {"i", "regime", "dist", "cmax_regle", "cmax", "evaluations", "source", "planning"}
Reprise automatique : les instances déjà traitées (même nombre d'évaluations) sont sautées.
"""
import argparse, json, os, sys, time
import multiprocessing as mp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train_v3 import sample_v3
from jssp_pm.fjsp_env3 import run3
from metaheuristiques import recuit_simule
from metaheuristiques.codage import Budget, decoder, depuis_planning
from regles_priorite.regles import ReglePriorite, environnement

DOSSIER = os.path.dirname(os.path.abspath(__file__))
GRAINE0 = 10_000          # graines des instances d'entraînement (la validation utilise 999)


def instance(i, regime="A"):
    """Instance d'entraînement numéro i (reproductible)."""
    dist = "base" if i % 2 == 0 else "large"
    return sample_v3(np.random.default_rng(GRAINE0 + i), regime, dist), dist


def ameliorer(inst, depart_planning, evaluations, params, graine):
    """Recuit simulé depuis un planning -> (C_max, planning)."""
    c, sol, _ = recuit_simule.resoudre(inst, Budget(evaluations=evaluations), np.random.default_rng(graine),
                                       depart=depuis_planning(inst, depart_planning), **params)
    cmax, _, planning = decoder(inst, *sol, avec_planning=True)
    return cmax, planning


def un_expert(args):
    i, regime, evaluations, params = args
    inst, dist = instance(i, regime)
    _, sim = run3(environnement(), ReglePriorite("MWKR", "EFT"), inst)
    cmax, planning = ameliorer(inst, sim.segments, evaluations, params, i)
    if sim.last_completion <= cmax:                      # l'expert ne fait jamais pire que la règle
        cmax, planning = sim.last_completion, [tuple(s) for s in sim.segments]
    return dict(i=i, regime=regime, dist=dist, cmax_regle=float(sim.last_completion), cmax=float(cmax),
                evaluations=evaluations, source="recuit",
                planning=[[int(k), float(a), float(b), int(t), int(j)] for k, a, b, t, j in planning])


def lire(fichier):
    if not os.path.exists(fichier):
        return []
    with open(fichier, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def parametres_recuit(chemin):
    if not chemin:
        return {}
    with open(chemin, encoding="utf-8") as f:
        return json.load(f).get("Recuit simulé", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", type=int, default=1000)
    ap.add_argument("--debut", type=int, default=0, help="numéro de la première instance")
    ap.add_argument("--regime", default="A")
    ap.add_argument("--evaluations", type=int, default=50000)
    ap.add_argument("--parametres", default=None, help="parametres_retenus.json (Taguchi)")
    ap.add_argument("--processus", type=int, default=2)
    ap.add_argument("--sortie", default=os.path.join(DOSSIER, "experts.jsonl"))
    a = ap.parse_args()
    params = parametres_recuit(a.parametres)
    fait = {(r["i"], r["regime"], r["evaluations"]) for r in lire(a.sortie)}
    taches = [(i, a.regime, a.evaluations, params) for i in range(a.debut, a.debut + a.nombre)
              if (i, a.regime, a.evaluations) not in fait]
    print(f"{len(taches)} instances à traiter (paramètres du recuit : {params or 'défaut'})", flush=True)
    t0 = time.time()
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    with ctx.Pool(a.processus) as pool, open(a.sortie, "a", encoding="utf-8") as f:
        for n, r in enumerate(pool.imap_unordered(un_expert, taches), 1):
            f.write(json.dumps(r) + "\n")
            f.flush()
            if n % 20 == 0 or n == len(taches):
                print(f"  {n}/{len(taches)}  ({(time.time() - t0) / 60:.1f} min)", flush=True)
    R = [r for r in lire(a.sortie) if r["regime"] == a.regime]
    if R:
        g = np.mean([r["cmax"] / r["cmax_regle"] - 1 for r in R])
        print(f"{len(R)} plannings experts ; gain moyen de l'expert sur MWKR+EFT : {100 * g:.1f} %")


if __name__ == "__main__":
    main()
