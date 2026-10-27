"""E9b — CP-SAT SEUL (sans démarrage à chaud) comme méthode concurrente, à budgets de temps fixés (décidé le 9/10/2026,
budgets déclarés AVANT tout calcul, voir PROTOCOLE § 3 ter).

Pourquoi : en E9, CP-SAT démarré à chaud depuis le meilleur planning de la banque et laissé 600 s améliore ce planning
sur 78/121 instances ; un relecteur demandera ce que fait CP-SAT seul à temps comparable.

Réglages (identiques pour toutes les instances) :
  - même modèle que E9 (jssp_pm/fjsp_cpsat.py, segments="valide"), AUCUN planning de départ, aucune borne sup. imposée ;
  - seconde phase (réduction du nombre de maintenances à C_max fixé) désactivée : le budget est entièrement consacré au C_max ;
  - graine 0 ; principal : 1 fil (même ressource que le recuit, le tabou et le faisceau), budgets 1, 2, 5, 10, 20, 40 s
    (mêmes budgets que E10) ; sensibilité : 8 fils, 5 et 40 s ;
  - UN SEUL processus, machine au repos (temps mesurés comme E10) ; temps rapporté = construction du modèle + résolution.
Sorties : banque (méthode « CP-SAT seul », config « temps=Xs,fils=W,sans_depart »), C_max vérifié par check().
Si aucune solution n'est trouvée dans le budget : ligne enregistrée dans experiences_article1/resultats/e9b_sans_solution.csv
(pas dans la banque) ; dans les tableaux, compter ces cas comme « sans solution » (jamais imputés).

  python cpsat_sans_depart.py                     # tout (≈ 4 à 5 h + budgets appariés), APRÈS E10
  python cpsat_sans_depart.py --familles Kacem    # essai
"""
import argparse, csv, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jssp_pm.fjsp_cpsat import solve, check          # noqa: E402
from metaheuristiques.instances import charger_instances   # noqa: E402
from banque_resultats import banque                  # noqa: E402

REGLAGES = [(1, t) for t in (1, 2, 5, 10, 20, 40)] + [(8, 5), (8, 40)]
# Budgets APPARIÉS (règle déclarée le 9/10/2026, PROTOCOLE § 3 ter) : temps murs moyens du faisceau 5×4, 10×4 et 50×5
# mesurés par E10 (un processus, machine au repos), arrondis à la seconde ; écrits dans ce fichier à la sortie d'E10,
# puis figés. Chaque budget apparié est calculé en 1 fil (primaire) et en 8 fils (secondaire).
APPARIES = os.path.join("experiences_article1", "budgets_e9b.json")
SANS_SOL = os.path.join("experiences_article1", "resultats", "e9b_sans_solution.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "HurinkLa", "Kacem"])
    ap.add_argument("--facteur-seuil", type=float, default=1.0)
    a = ap.parse_args()
    insts = charger_instances(a.familles, regime="A", facteur_seuil=a.facteur_seuil)
    deja = banque.cles_existantes()
    sans = set()
    if os.path.exists(SANS_SOL):
        sans = {(r["instance"], r["config"]) for r in csv.DictReader(open(SANS_SOL, encoding="utf-8"))}
    reglages = list(REGLAGES)
    if os.path.exists(APPARIES):
        import json
        for t in json.load(open(APPARIES, encoding="utf-8")).values():
            reglages += [(1, int(t)), (8, int(t))]
    else:
        print(f"ATTENTION : {APPARIES} absent (E10 pas encore fait) : budgets appariés non calculés", flush=True)
    reglages = list(dict.fromkeys(reglages))
    print(f"{len(insts)} instances × {len(reglages)} réglages : {reglages}", flush=True)
    for w, t in reglages:
        cfg = f"temps={t}s,fils={w},sans_depart"
        for inst in insts:
            if banque.cle(inst.name, "A", a.facteur_seuil, "CP-SAT seul", cfg, 0) in deja or (inst.name, cfg) in sans:
                continue
            t0 = time.perf_counter()
            r = solve(inst, time_limit=t, workers=w, hint=None, second_phase=False, segments="valide", graine=0)
            dt = time.perf_counter() - t0                     # construction du modèle + résolution
            if r["cmax"] is None:
                nouveau = not os.path.exists(SANS_SOL)
                with open(SANS_SOL, "a", newline="", encoding="utf-8") as f:
                    wr = csv.writer(f)
                    if nouveau:
                        wr.writerow(["instance", "facteur_seuil", "config", "statut", "borne", "temps_s"])
                    wr.writerow([inst.name, a.facteur_seuil, cfg, r["status"], r["bound"], round(dt, 2)])
                print(f"{cfg} {inst.name} : {r['status']} (aucune solution) {dt:.1f} s", flush=True)
                continue
            check(inst, r["segments"])
            banque.ajouter(inst.name, "A", a.facteur_seuil, "CP-SAT seul", cfg, 0, r["cmax"], r["pm"], 0, dt,
                           r["segments"])
            print(f"{cfg} {inst.name} : {r['status']} C_max {r['cmax']} borne {r['bound']:.1f} {dt:.1f} s", flush=True)


if __name__ == "__main__":
    main()
