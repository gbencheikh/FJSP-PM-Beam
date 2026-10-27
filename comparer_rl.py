"""Compare un (ou plusieurs) agent(s) RL aux résultats DÉJÀ enregistrés dans la banque
(règles de priorité, métaheuristiques), sans relancer ces méthodes.

  python comparer_rl.py --modele models/v3/A_full_s0_best.pt --nom complet-s0
  python comparer_rl.py --modele models/v3/A_full_s0_best.pt models/v3/A_full_s1_best.pt \
                        --nom complet-s0 complet-s1 --meilleur-de-temps 5

Seul l'agent est exécuté (et seulement s'il n'est pas déjà dans la banque pour cette configuration).
Sorties :
  comparaisons/comparaison_seuil<x>.csv : une ligne par instance, une colonne par méthode (C_max)
  comparaisons/comparaison_seuil<x>.md  : C_max moyen, écart au meilleur connu, victoires de l'agent
"""
import argparse, os, time
import multiprocessing as mp
from collections import defaultdict
import numpy as np
import torch

from jssp_pm.fjsp_env3 import FJSPEnv3, run3
from jssp_pm.fjsp_ppo import PPOPolicy
from jssp_pm.fjsp_cpsat import check
from metaheuristiques.instances import charger_instances
from banque_resultats import banque


from jssp_pm.reseaux import charger_reseau      # lit les réseaux « candidats » et « graphe »


def mode_du_modele(chemin):
    """Le mode d'actions doit être celui de l'entraînement : déduit du nom du fichier."""
    base = os.path.basename(chemin)
    if "pm_only" in base:
        return "pm_only"
    if "dispatch_only" in base:
        return "dispatch_only"
    return "full"


def executer_agent(inst, net, regime, budget=None, graine=0, mode="full", k_max=None, inclure_glouton=True):
    """inclure_glouton=True : le 1er planning est le glouton, puis K-1 tirages (« meilleur de K », historique).
    inclure_glouton=False : K tirages, tous échantillonnés avec rng(graine) (« échantillons=K », symétrique de Song et al.)."""
    env = FJSPEnv3(mode, safety=(regime == "A"))
    t0 = time.time()
    if budget is None and k_max is None:                     # glouton : un seul planning
        m, sim = run3(env, PPOPolicy(net), inst)
        m["evaluations"] = 1
        return m, sim.segments, time.time() - t0
    rng = np.random.default_rng(graine)                      # meilleur de K (nombre fixé ou temps imparti)
    best = None
    k = 0
    while (k < k_max) if k_max is not None else (time.time() - t0 < budget):
        m, sim = run3(env, PPOPolicy(net, greedy=(k == 0 and inclure_glouton), rng=rng), inst, seed=k)
        k += 1
        if best is None or m["cmax"] + 1e6 * m["breakdowns"] < best[0]["cmax"] + 1e6 * best[0]["breakdowns"]:
            best = (m, list(sim.segments))
    best[0]["evaluations"] = k
    return best[0], best[1], time.time() - t0


_NET = {}


def une_tache(args):
    """Une exécution (instance, graine) dans un processus de travail. Le résultat ne dépend que de
    (réseau, instance, graine) : identique quel que soit le nombre de processus ou l'ordre."""
    chemin, inst, regime, g, echantillons, meilleur_de_temps, meilleur_de_k = args
    torch.set_num_threads(1)
    if _NET.get("chemin") != chemin:
        _NET["net"], _NET["chemin"] = charger_reseau(chemin), chemin
    if echantillons is not None:
        m, planning, dt = executer_agent(inst, _NET["net"], regime, None, graine=g, mode=mode_du_modele(chemin),
                                         k_max=echantillons, inclure_glouton=False)
    else:
        m, planning, dt = executer_agent(inst, _NET["net"], regime, meilleur_de_temps,
                                         mode=mode_du_modele(chemin), k_max=meilleur_de_k)
    if m["breakdowns"] == 0:
        check(inst, planning)
    return inst.name, g, m, planning, dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modele", nargs="+", required=True)
    ap.add_argument("--nom", nargs="+", required=True, help="un nom court par modèle")
    ap.add_argument("--regime", default="A", choices=["A", "B"])
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "Hurink"])
    ap.add_argument("--facteur-seuil", type=float, default=1.0)
    ap.add_argument("--meilleur-de-temps", type=float, default=None,
                    help="secondes par instance ; sinon mode glouton (un seul planning)")
    ap.add_argument("--meilleur-de-k", type=int, default=None,
                    help="nombre de plannings échantillonnés par instance (reproductible)")
    ap.add_argument("--echantillons", type=int, default=None,
                    help="K tirages tous échantillonnés (sans le glouton), répétés pour chaque graine de --graines")
    ap.add_argument("--graines", type=int, nargs="+", default=[0],
                    help="graines des tirages (avec --echantillons) ; protocole : 0 1 2 3 4")
    ap.add_argument("--processus", type=int, default=1,
                    help="processus en parallèle (temps par instance alors non comparables : protocole, E10)")
    ap.add_argument("--forcer", action="store_true")
    a = ap.parse_args()
    if a.meilleur_de_temps is not None and a.processus > 1:
        raise SystemExit("--meilleur-de-temps exige --processus 1 (budget en temps)")
    assert len(a.modele) == len(a.nom)
    torch.set_num_threads(1)
    os.makedirs("comparaisons", exist_ok=True)
    instances = charger_instances(a.familles, regime=a.regime, facteur_seuil=a.facteur_seuil)
    if a.echantillons is not None:
        cfg = f"echantillons={a.echantillons}"
    elif a.meilleur_de_k is not None:
        cfg = f"meilleur_de_k={a.meilleur_de_k}"
    elif a.meilleur_de_temps is not None:
        cfg = f"meilleur_de_temps={a.meilleur_de_temps:g}s"
    else:
        cfg = "glouton"
    deja = banque.cles_existantes()
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    for chemin, nom in zip(a.modele, a.nom):
        graines = a.graines if a.echantillons is not None else [0]
        taches = [(chemin, inst, a.regime, g, a.echantillons, a.meilleur_de_temps, a.meilleur_de_k)
                  for inst in instances for g in graines
                  if a.forcer or banque.cle(inst.name, a.regime, a.facteur_seuil, f"RL:{nom}", cfg, g) not in deja]
        print(f"{nom} : {len(taches)} exécutions à lancer, {a.processus} processus", flush=True)
        if a.processus <= 1:
            resultats = map(une_tache, taches)
            pool = None
        else:
            pool = ctx.Pool(a.processus)
            resultats = pool.imap_unordered(une_tache, taches)
        for nom_inst, g, m, planning, dt in resultats:        # écriture dans la banque par le seul processus principal
            banque.ajouter(nom_inst, a.regime, a.facteur_seuil, f"RL:{nom}", cfg, g, m["cmax"], m["pm"],
                           m["breakdowns"], dt, planning, evaluations=m["evaluations"])
            print(nom, nom_inst, f"graine {g}", m["cmax"], flush=True)
        if pool is not None:
            pool.close()
            pool.join()

    # --- tableau comparatif, relu entièrement depuis la banque
    noms = sorted(i.name for i in instances)
    lignes = [r for r in banque.charger() if r["instance"] in noms and r["regime"] == a.regime
              and float(r["facteur_seuil"]) == a.facteur_seuil]
    val = defaultdict(list)                                  # (méthode [config]) -> instance -> [cmax]
    for r in lignes:
        etiquette = r["methode"] + (f" [{r['config']}]" if r["config"] else "")
        val[(etiquette, r["instance"])].append(float(r["cmax"]))
    methodes = sorted({k[0] for k in val if all((k[0], n) in val for n in noms)})
    moy = {(m, n): float(np.mean(val[(m, n)])) for m in methodes for n in noms}
    meilleur = {n: min(moy[(m, n)] for m in methodes) for n in noms}
    with open(f"comparaisons/comparaison_seuil{a.facteur_seuil:g}.csv", "w", encoding="utf-8") as f:
        f.write("instance;meilleur_connu;" + ";".join(methodes) + "\n")
        for n in noms:
            f.write(f"{n};{meilleur[n]:g};" + ";".join(f"{moy[(m, n)]:g}" for m in methodes) + "\n")
    agents = [f"RL:{x} [{cfg}]" for x in a.nom]
    md = [f"# Comparaison — {len(noms)} instances, régime {a.regime}, facteur de seuil {a.facteur_seuil:g}\n",
          "C_max moyen sur les graines disponibles ; écart au meilleur connu = meilleure valeur, toutes méthodes de la banque.\n",
          "| Méthode [configuration] | C_max moyen | Écart moyen au meilleur connu | "
          + " | ".join(f"V/E/D de {x}" for x in a.nom) + " |",
          "|---|---|---|" + "---|" * len(a.nom)]
    for m in sorted(methodes, key=lambda m: np.mean([moy[(m, n)] / meilleur[n] - 1 for n in noms])):
        e = np.mean([moy[(m, n)] / meilleur[n] - 1 for n in noms])
        vs = []
        for ag in agents:
            d = np.array([moy[(ag, n)] - moy[(m, n)] for n in noms])
            vs.append("–" if m == ag else f"{(d < -1e-9).sum()}/{(abs(d) <= 1e-9).sum()}/{(d > 1e-9).sum()}")
        md.append(f"| {m} | {np.mean([moy[(m, n)] for n in noms]):.1f} | {100 * e:+.1f} % | " + " | ".join(vs) + " |")
    md.append("\nV/E/D = victoires / égalités / défaites de l'agent face à la méthode de la ligne, instance par instance.")
    open(f"comparaisons/comparaison_seuil{a.facteur_seuil:g}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
