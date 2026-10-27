"""Méthode hybride (piste 4) : l'agent RL construit un planning, une métaheuristique l'améliore.

  python hybride_rl_mh.py --modele models/v3/A_full_s0_best.pt --nom complet-s0 --processus 10
  python hybride_rl_mh.py --modele models/imitation/cand_best.pt --nom imit --meilleur-de-k 100 \
         --parametres reglage_taguchi/parametres_retenus.json --processus 10

Pour chaque instance (Brandimarte + Hurink) et chaque graine :
  1. l'agent produit un planning (glouton, ou meilleur de K tirages avec --meilleur-de-k) ;
  2. le recuit simulé / la recherche tabou démarre de ce planning, avec le même budget
     d'évaluations que dans metaheuristiques/comparer.py ;
  3. le résultat va dans la banque : méthode « RL:<nom> + <métaheuristique> »,
     config « evals=<N>,depart=agent[,k=K][,params=...] ».
Les K plannings de l'agent sont ajoutés au nombre d'évaluations enregistré (comparaison honnête).

Le tableau final compare, instance par instance, l'hybride à la MÊME métaheuristique partie de
MWKR+EFT (déjà dans la banque : lancez d'abord metaheuristiques/comparer.py avec le même budget).
"""
import argparse, json, os, sys, time
import multiprocessing as mp
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jssp_pm.fjsp_cpsat import check
from jssp_pm.reseaux import charger_reseau
from metaheuristiques import genetique, tabou, recuit_simule
from metaheuristiques.codage import Budget, decoder, depuis_planning
from metaheuristiques.instances import charger_instances
from comparer_rl import executer_agent, mode_du_modele
from banque_resultats import banque

METHODES = {"Recuit simulé": recuit_simule, "Recherche tabou": tabou, "Algorithme génétique": genetique}
REGIME = "A"
_NET = {}


def depart_banque(nom, fs, methode, config):
    """Planning (et coût en évaluations) d'une méthode déjà dans la banque, p. ex. l'agent qui anticipe."""
    for r in banque.charger():
        if (r["instance"] == nom and r["regime"] == REGIME and abs(float(r["facteur_seuil"]) - fs) < 1e-9
                and r["methode"] == methode and r["config"] == config and r["solution"]):
            plan = banque.planning(r)
            if plan:
                return plan, dict(cmax=float(r["cmax"]), evaluations=int(float(r["evaluations"] or 0)))
    raise KeyError(f"{methode} [{config}] absent de la banque pour {nom}")


def une_execution(args):
    inst, chemin, nom_mh, graine, evaluations, k, params, depart = args
    torch.set_num_threads(1)
    t0 = time.time()
    if depart:                                   # départ = planning déjà calculé (temps non recompté ici)
        planning_agent, m = depart_banque(inst.name, inst.meta.get("T_scale", 1.0), *depart)
    else:
        if _NET.get("chemin") != chemin:
            _NET["net"], _NET["chemin"] = charger_reseau(chemin), chemin
        m, planning_agent, _ = executer_agent(inst, _NET["net"], REGIME, graine=graine,
                                              mode=mode_du_modele(chemin), k_max=k)
    rng = np.random.default_rng(1000 + graine)
    cout, sol, info = METHODES[nom_mh].resoudre(inst, Budget(evaluations=evaluations), rng,
                                                depart=depuis_planning(inst, planning_agent), **params)
    cmax, npm, planning = decoder(inst, *sol, avec_planning=True)
    check(inst, planning)
    return (inst.name, nom_mh, graine, cmax, npm, time.time() - t0, planning,
            info["evaluations"] + m["evaluations"], m["cmax"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modele", default=None)
    ap.add_argument("--depart-banque", default=None,
                    help="« méthode|config » d'un planning de la banque comme départ (p. ex. « RL:imit-ft|faisceau=5,k=4 »)")
    ap.add_argument("--nom", required=True)
    ap.add_argument("--methodes", nargs="+", default=["Recuit simulé", "Recherche tabou"])
    ap.add_argument("--evaluations", type=int, default=50000)
    ap.add_argument("--graines", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--meilleur-de-k", type=int, default=None)
    ap.add_argument("--parametres", default=None)
    ap.add_argument("--etiquette-params", default="taguchi")
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "Hurink"])
    ap.add_argument("--facteur-seuil", type=float, default=1.0)
    ap.add_argument("--processus", type=int, default=2)
    ap.add_argument("--forcer", action="store_true")
    a = ap.parse_args()
    params = {}
    if a.parametres:
        with open(a.parametres, encoding="utf-8") as f:
            params = json.load(f)
    suffixe = (f",params={a.etiquette_params}" if a.parametres else "")
    assert a.modele or a.depart_banque, "donner --modele ou --depart-banque"
    depart = tuple(a.depart_banque.split("|", 1)) if a.depart_banque else None
    cfg = (f"evals={a.evaluations},depart=" + (f"banque:{depart[1]}" if depart else "agent")
           + (f",k={a.meilleur_de_k}" if a.meilleur_de_k and not depart else "") + suffixe)
    cfg_ref = f"evals={a.evaluations},depart=heuristique" + suffixe
    instances = charger_instances(a.familles, regime=REGIME, facteur_seuil=a.facteur_seuil)
    deja = banque.cles_existantes()
    meth = lambda nom_mh: f"RL:{a.nom} + {nom_mh}"
    taches = [(i, a.modele, nm, g, a.evaluations, a.meilleur_de_k, params.get(nm, {}), depart)
              for i in instances for nm in a.methodes for g in a.graines
              if a.forcer or banque.cle(i.name, REGIME, a.facteur_seuil, meth(nm), cfg, g) not in deja]
    print(f"{len(taches)} exécutions à lancer (les autres sont déjà dans la banque).", flush=True)
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    with ctx.Pool(a.processus) as pool:
        for r in pool.imap_unordered(une_execution, taches):
            banque.ajouter(r[0], REGIME, a.facteur_seuil, meth(r[1]), cfg, r[2], r[3], r[4], 0, r[5], r[6],
                           evaluations=r[7])
            print(f"{r[0]} {r[1]} graine {r[2]} : agent {r[8]:g} -> {r[3]:g}", flush=True)

    # tableau : hybride vs même métaheuristique partie de MWKR+EFT
    noms = sorted(i.name for i in instances)
    B = [r for r in banque.charger() if r["regime"] == REGIME and float(r["facteur_seuil"]) == a.facteur_seuil
         and r["instance"] in noms and int(r["graine"]) in a.graines]
    md = [f"# Hybride agent « {a.nom} » + métaheuristique — {a.evaluations} évaluations, graines {a.graines}\n",
          "| Métaheuristique | C_max moyen (départ MWKR+EFT) | C_max moyen (départ agent) | Écart | V/E/D de l'hybride |",
          "|---|---|---|---|---|"]
    for nm in a.methodes:
        moy = lambda meth_, c, n: [float(r["cmax"]) for r in B if r["methode"] == meth_ and r["config"] == c
                                   and r["instance"] == n]
        ref = {n: moy(nm, cfg_ref, n) for n in noms}
        hyb = {n: moy(meth(nm), cfg, n) for n in noms}
        ok = [n for n in noms if ref[n] and hyb[n]]
        if not ok:
            md.append(f"| {nm} | (pas de résultat « {cfg_ref} » dans la banque) | | | |")
            continue
        r_ = np.array([np.mean(ref[n]) for n in ok])
        h_ = np.array([np.mean(hyb[n]) for n in ok])
        d = h_ - r_
        md.append(f"| {nm} | {r_.mean():.1f} | {h_.mean():.1f} | {100 * np.mean(h_ / r_ - 1):+.2f} % | "
                  f"{(d < -1e-9).sum()}/{(abs(d) <= 1e-9).sum()}/{(d > 1e-9).sum()} ({len(ok)} instances) |")
    md.append("\nV/E/D = victoires / égalités / défaites de l'hybride, instance par instance (moyenne des graines).")
    os.makedirs("comparaisons", exist_ok=True)
    open(f"comparaisons/hybride_{a.nom}_seuil{a.facteur_seuil:g}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
