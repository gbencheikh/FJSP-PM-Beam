"""CP-SAT pour l'article 1 : meilleure solution et borne inférieure par instance (régime A, sans panne).

  python cpsat_article1.py --familles Brandimarte Kacem --temps 600 --workers 8
  python cpsat_article1.py --familles HurinkLa --temps 600 --workers 2 --instances-paralleles 4
  python cpsat_article1.py --familles Brandimarte HurinkLa Kacem --facteur-seuil 1000 --temps 600   # FJSP classique

- Modèle à segments (jssp_pm/fjsp_cpsat.py) avec segments="valide" : la borne est une vraie borne
  inférieure (voir la docstring de solve).
- Démarrage à chaud : meilleur planning de la banque pour l'instance (toutes méthodes confondues).
  La borne supérieure imposée (C_max <= C_max du départ) ne change pas la validité de la borne inférieure.
- Avec --facteur-seuil 1000 (FJSP classique, aucune maintenance utile), la borne obtenue est aussi une
  borne inférieure valide du régime A (relaxation : on retire les contraintes d'usure).
Sorties : banque (méthode « CP-SAT », config « temps=..,segments=valide ») et
experiences_article1/resultats/cpsat_bornes.json (statut, C_max, borne, temps, S par machine).
"""
import argparse, json, os, sys
import multiprocessing as mp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jssp_pm.fjsp_cpsat import solve, check
from metaheuristiques.instances import charger_instances
from banque_resultats import banque

REGIME = "A"
SORTIE = os.path.join("experiences_article1", "resultats", "cpsat_bornes.json")


def meilleur_depart(nom, fs):
    lignes = [r for r in banque.charger() if r["instance"] == nom and r["regime"] == REGIME
              and abs(float(r["facteur_seuil"]) - fs) < 1e-9 and r["cmax"] and r["solution"]
              and int(r["pannes"] or 0) == 0]
    for r in sorted(lignes, key=lambda r: float(r["cmax"])):
        plan = banque.planning(r)
        if plan:
            return plan, float(r["cmax"]), f"{r['methode']} [{r['config']}]"
    return None, None, None


def une_instance(args):
    inst, fs, temps, workers = args
    plan, c0, source = meilleur_depart(inst.name, fs)
    r = solve(inst, time_limit=temps, workers=workers, hint=plan, segments="valide")
    if r["cmax"] is not None:
        check(inst, r["segments"])
    r.update(hint_cmax=c0, hint_source=source)
    return inst.name, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "HurinkLa", "Kacem"])
    ap.add_argument("--facteur-seuil", type=float, default=1.0)
    ap.add_argument("--temps", type=int, default=600, help="secondes par instance")
    ap.add_argument("--workers", type=int, default=8, help="fils CP-SAT par instance")
    ap.add_argument("--instances-paralleles", type=int, default=1)
    ap.add_argument("--forcer", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    cache = json.load(open(SORTIE, encoding="utf-8")) if os.path.exists(SORTIE) else {}
    cfg = f"temps={a.temps},segments=valide"
    insts = [i for i in charger_instances(a.familles, regime=REGIME, facteur_seuil=a.facteur_seuil)
             if a.forcer or f"{i.name}|{a.facteur_seuil:g}|{cfg}" not in cache]
    print(f"{len(insts)} instances, {a.temps} s chacune, {a.workers} fils, {a.instances_paralleles} en parallèle", flush=True)
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    # Chien de garde (ajouté le 9/10/2026 : un processus fils figé sous Windows a bloqué E9 pendant 11 h sur Kacem1,
    # résolu en 1 s ailleurs). Si aucun résultat n'arrive pendant `attente` secondes, le groupe de processus est
    # détruit et relancé pour les instances restantes (au plus 3 fois) ; les résultats déjà obtenus sont gardés.
    attente = 3 * a.temps + 600
    restantes = list(insts)
    for essai in range(4):
        if not restantes:
            break
        pool = ctx.Pool(a.instances_paralleles)
        it = pool.imap_unordered(une_instance, [(i, a.facteur_seuil, a.temps, a.workers) for i in restantes])
        faites, bloque = set(), False
        while len(faites) < len(restantes):
            try:
                nom, r = it.next(timeout=attente)
            except mp.TimeoutError:
                bloque = True
                break
            faites.add(nom)
            segs = r.pop("segments", None)
            cache[f"{nom}|{a.facteur_seuil:g}|{cfg}"] = r
            json.dump(cache, open(SORTIE, "w", encoding="utf-8"), indent=1, default=float)
            if r["cmax"] is not None:
                banque.ajouter(nom, REGIME, a.facteur_seuil, "CP-SAT", cfg, 0, r["cmax"], r["pm"], 0, r["time"], segs)
            print(f"{nom} : {r['status']} C_max {r['cmax']} borne {r['bound']:.1f} (départ {r['hint_cmax']}) "
                  f"{r['time']:.0f} s", flush=True)
        pool.terminate(); pool.join()
        restantes = [i for i in restantes if i.name not in faites]
        if bloque:
            print(f"CHIEN DE GARDE : aucun résultat depuis {attente} s ; processus relancés pour "
                  f"{len(restantes)} instance(s) restante(s) (essai {essai + 1})", flush=True)
    if restantes:
        print(f"ÉCHEC : instances non résolues après 4 essais : {[i.name for i in restantes]}", flush=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
