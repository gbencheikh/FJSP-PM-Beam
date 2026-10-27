"""Lance AG, recherche tabou et recuit simulé à budget de temps égal et enregistre chaque résultat
dans la banque (banque_resultats/resultats.csv + le planning dans banque_resultats/solutions/).

  python -m metaheuristiques.comparer --evaluations 20000          # budget reproductible (recommandé)
  python -m metaheuristiques.comparer --budget 10 --graines 0 1 2
  python -m metaheuristiques.comparer --familles Brandimarte --budget 5 --depart aleatoire
  python -m metaheuristiques.comparer --forcer             # relancer même si déjà dans la banque
  python -m metaheuristiques.comparer --evaluations 50000 --parametres reglage_taguchi/parametres_retenus.json
  python -m metaheuristiques.comparer --methodes "Recuit simulé" --evaluations 50000 ...   # une seule méthode
                                                           # paramètres réglés par Taguchi (config « ,params=taguchi »)

Une exécution (instance, méthode, facteur de seuil, budget, départ, graine) déjà présente dans la
banque n'est pas relancée : on peut interrompre le script et le relancer, il reprend où il en était.
Départ : « heuristique » (solution de la règle MWKR+EFT, par défaut) ou « aleatoire ».
"""
import argparse, json, os, sys, time
import multiprocessing as mp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jssp_pm.fjsp_env3 import run3
from jssp_pm.fjsp_cpsat import check
from metaheuristiques import genetique, tabou, recuit_simule
from metaheuristiques.codage import decoder, depuis_planning, Budget
from metaheuristiques.instances import charger_instances
from regles_priorite.regles import ReglePriorite, environnement
from banque_resultats import banque

METHODES = {"Algorithme génétique": genetique, "Recherche tabou": tabou, "Recuit simulé": recuit_simule}
REGIME = "A"


def config(budget, evaluations, depart, etiquette_params=""):
    base = f"evals={evaluations}" if evaluations is not None else f"budget={budget:g}s"
    return f"{base},depart={depart}" + (f",params={etiquette_params}" if etiquette_params else "")


def reutiliser_defaut(a, instances, cfg, params, deja):
    """Si les paramètres réglés d'une méthode sont exactement ses valeurs par défaut, le résultat
    est identique (même graine, même départ, même budget) à celui déjà calculé sans --parametres :
    on recopie ces lignes sous la nouvelle configuration au lieu de tout relancer."""
    if not a.parametres or a.forcer:
        return
    cfg0 = config(a.budget, a.evaluations, a.depart)
    noms = {i.name for i in instances}
    for nom in a.methodes:
        if params.get(nom, {}) and params[nom] != METHODES[nom].PARAMS_DEFAUT:
            continue
        n = 0
        for r in banque.charger():
            if (r["methode"] == nom and r["config"] == cfg0 and r["regime"] == REGIME and r["instance"] in noms
                    and float(r["facteur_seuil"]) == a.facteur_seuil and int(r["graine"]) in a.graines
                    and banque.cle(r["instance"], REGIME, a.facteur_seuil, nom, cfg, r["graine"]) not in deja):
                banque.ajouter(r["instance"], REGIME, a.facteur_seuil, nom, cfg, int(r["graine"]), float(r["cmax"]),
                               int(r["maintenances"]), int(r["pannes"]), float(r["temps_s"]), banque.planning(r),
                               evaluations=int(r["evaluations"]) if r.get("evaluations") else None)
                n += 1
        if n:
            print(f"{nom} : paramètres réglés = valeurs par défaut -> {n} résultats repris de « {cfg0} »", flush=True)


def une_execution(args):
    inst, nom, graine, budget, evaluations, depart, params = args
    rng = np.random.default_rng(1000 + graine)
    sol0 = None
    if depart == "heuristique":
        _, sim = run3(environnement(), ReglePriorite("MWKR", "EFT"), inst)
        sol0 = depuis_planning(inst, sim.segments)
    t0 = time.time()
    b = Budget(evaluations=evaluations) if evaluations is not None else Budget(secondes=budget)
    cout, sol, info = METHODES[nom].resoudre(inst, b, rng, depart=sol0, **params)
    cmax, npm, planning = decoder(inst, *sol, avec_planning=True)
    check(inst, planning)                                   # planning valide, aucune panne
    return inst.name, nom, graine, cmax, npm, time.time() - t0, planning, info["evaluations"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "Hurink"])
    ap.add_argument("--budget", type=float, default=10.0, help="secondes par instance et par exécution")
    ap.add_argument("--evaluations", type=int, default=None,
                    help="nombre de plannings évalués par exécution (remplace --budget ; reproductible)")
    ap.add_argument("--graines", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--depart", choices=["heuristique", "aleatoire"], default="heuristique")
    ap.add_argument("--facteur-seuil", type=float, default=1.0)
    ap.add_argument("--processus", type=int, default=2)
    ap.add_argument("--parametres", default=None,
                    help="fichier JSON {méthode: {paramètre: valeur}} (ex. reglage_taguchi/parametres_retenus.json)")
    ap.add_argument("--etiquette-params", default="taguchi",
                    help="nom ajouté à la config dans la banque quand --parametres est utilisé")
    ap.add_argument("--methodes", nargs="+", default=list(METHODES), choices=list(METHODES),
                    help="méthodes à lancer (par défaut les trois)")
    ap.add_argument("--forcer", action="store_true")
    ap.add_argument("--sortie", default="resultats_metaheuristiques")
    a = ap.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    instances = charger_instances(a.familles, regime=REGIME, facteur_seuil=a.facteur_seuil)
    params = {}
    if a.parametres:
        with open(a.parametres, encoding="utf-8") as f:
            params = json.load(f)
        print("Paramètres utilisés :", params, flush=True)
    cfg = config(a.budget, a.evaluations, a.depart, a.etiquette_params if a.parametres else "")
    deja = banque.cles_existantes()
    reutiliser_defaut(a, instances, cfg, params, deja)
    deja = banque.cles_existantes()
    taches = [(i, nom, g, a.budget, a.evaluations, a.depart, params.get(nom, {}))
              for i in instances for nom in a.methodes for g in a.graines
              if a.forcer or banque.cle(i.name, REGIME, a.facteur_seuil, nom, cfg, g) not in deja]
    print(f"{len(taches)} exécutions à lancer (les autres sont déjà dans la banque).", flush=True)
    with mp.get_context("spawn" if os.name == "nt" else "fork").Pool(a.processus) as pool:
        for r in pool.imap_unordered(une_execution, taches):
            banque.ajouter(r[0], REGIME, a.facteur_seuil, r[1], cfg, r[2], r[3], r[4], 0, r[5], r[6],
                           evaluations=r[7])
            print(r[0], r[1], r[2], r[3], flush=True)

    # récapitulatif relu depuis la banque
    noms = sorted(i.name for i in instances)
    lignes = [r for r in banque.charger() if r["instance"] in noms and r["regime"] == REGIME
              and float(r["facteur_seuil"]) == a.facteur_seuil and r["config"] == cfg
              and r["methode"] in METHODES and int(r["graine"]) in a.graines]
    presentes = [m for m in METHODES if all(any(r["instance"] == n and r["methode"] == m for r in lignes)
                                            for n in noms)]
    moy = {(n, m): np.mean([float(r["cmax"]) for r in lignes if r["instance"] == n and r["methode"] == m])
           for n in noms for m in presentes}
    meilleur = {n: min(float(r["cmax"]) for r in lignes if r["instance"] == n and r["methode"] in presentes)
                for n in noms} if presentes else {}
    txt_budget = f"{a.evaluations} évaluations" if a.evaluations is not None else f"{a.budget:g} s"
    md = [f"# Métaheuristiques — {len(noms)} instances, {txt_budget} par exécution, "
          f"{len(a.graines)} graines, départ {a.depart}, facteur de seuil {a.facteur_seuil:g}\n",
          "| Méthode | C_max moyen | Écart moyen à la meilleure solution trouvée | Écart-type entre graines | Nb de fois meilleure (moyenne des graines) |",
          "|---|---|---|---|---|"]
    for m in presentes:
        e = np.array([moy[(n, m)] / meilleur[n] - 1 for n in noms])
        par_graine = [np.mean([float(r["cmax"]) / meilleur[r["instance"]] - 1 for r in lignes
                               if r["methode"] == m and int(r["graine"]) == g]) for g in a.graines]
        gagne = sum(1 for n in noms if moy[(n, m)] <= min(moy[(n, mm)] for mm in presentes) + 1e-9)
        md.append(f"| {m} | {np.mean([moy[(n, m)] for n in noms]):.1f} | {100 * e.mean():+.1f} % | "
                  f"{100 * np.std(par_graine):.1f} pt | {gagne} |")
    fichier = f"{a.sortie}/resume_{cfg.replace(',', '_').replace('=', '')}_seuil{a.facteur_seuil:g}.md"
    open(fichier, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
