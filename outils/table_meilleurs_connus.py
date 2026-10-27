"""Table de référence des meilleurs plannings connus et des bornes, instance par instance, avec provenance
(demandée le 9/10/2026 ; supplément de l'article 1, base de l'article 2).

Pour chaque instance (134 calculées ; colonne « test » = hors instances de réglage Taguchi) et chaque régime :
  - régime A (s = 1, maintenance) : meilleur C_max de la banque (toutes méthodes, toutes graines), méthode, réglage,
    graine, date ; meilleure borne inférieure valide et sa source (FJSPLib = borne du FJSP classique, valable avec
    maintenance ; CP-SAT régime A ; CP-SAT classique = relaxation) ; statut « optimum prouvé » si les deux coïncident.
  - FJSP classique (s = 1000) : idem, plus le meilleur connu FJSPLib (source et date) ; un C_max de la banque
    strictement inférieur au meilleur connu FJSPLib est signalé « plus bas que FJSPLib » (à vérifier avant toute
    revendication : planning dans banque_resultats/solutions.jsonl, vérifié par check()).
Sorties : experiences_article1/resultats/meilleurs_connus_article.csv|md

  python -m outils.table_meilleurs_connus
"""
import csv, json, os, sys
from collections import Counter

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from metaheuristiques.instances import fichiers                          # noqa: E402
from experiences_article1.statistiques import INSTANCES_REGLAGE, BANQUE   # noqa: E402

RES = os.path.join(RACINE, "experiences_article1", "resultats")
EXT = os.path.join(RACINE, "experiences_article1", "meilleurs_connus.csv")


def main():
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"])]
    fj = {r["instance"]: r for r in csv.DictReader(open(EXT, encoding="utf-8"))}
    cps = json.load(open(os.path.join(RES, "cpsat_bornes.json"), encoding="utf-8"))
    bornes_cp = {}
    for cle, r in cps.items():
        nom, fs = cle.split("|")[:2]
        if r.get("bound"):
            k = (nom, "A" if float(fs) == 1 else "classique")
            bornes_cp[k] = max(bornes_cp.get(k, 0.0), float(r["bound"]))
    meilleur = {}
    for r in csv.DictReader(open(BANQUE, encoding="utf-8")):
        if r["regime"] != "A" or not r["cmax"] or int(r["pannes"] or 0) > 0:
            continue
        fs = float(r["facteur_seuil"])
        if fs not in (1.0, 1000.0):
            continue
        k = (r["instance"], "A" if fs == 1 else "classique")
        c = float(r["cmax"])
        if k not in meilleur or c < meilleur[k]["cmax"] or (c == meilleur[k]["cmax"] and r["date"] < meilleur[k]["date"]):
            meilleur[k] = dict(cmax=c, methode=r["methode"], config=r["config"], graine=r["graine"], date=r["date"][:10])
    lignes = []
    for n in noms:
        f = fj.get(n, {})
        for reg in ("A", "classique"):
            m = meilleur.get((n, reg))
            if not m:
                continue
            cands = {}
            if f.get("borne_inf"):
                cands[f"FJSPLib ({f.get('source_borne', '')}, {f.get('date_borne', '')})"] = float(f["borne_inf"])
            if (n, "A") in bornes_cp and reg == "A":
                cands["CP-SAT régime A (E9, 600 s)"] = bornes_cp[(n, "A")]
            if (n, "classique") in bornes_cp:
                cands["CP-SAT classique (E9, 600 s)" + (" — relaxation" if reg == "A" else "")] = bornes_cp[(n, "classique")]
            src, lb = max(cands.items(), key=lambda x: x[1]) if cands else ("", 0.0)
            ub, ub_src = m["cmax"], f"{m['methode']} [{m['config']}] graine {m['graine']} ({m['date']})"
            note = ""
            if reg == "classique" and f.get("meilleur_connu"):
                bks = float(f["meilleur_connu"])
                if bks < ub:
                    ub, ub_src = bks, f"FJSPLib ({f.get('source_meilleur', '')}, {f.get('date_meilleur', '')})"
                elif m["cmax"] < bks:
                    note = f"plus bas que FJSPLib ({bks:g}, {f.get('source_meilleur', '')}, {f.get('date_meilleur', '')}) : à vérifier"
            statut = "optimum prouvé" if lb > 0 and ub <= lb + 1e-9 else (f"ouvert (écart {100 * (ub / lb - 1):.1f} %)" if lb else "ouvert")
            lignes.append(dict(instance=n, test="non" if n in INSTANCES_REGLAGE else "oui", regime=reg,
                               meilleur_cmax=f"{ub:g}", source_meilleur=ub_src, borne_inf=f"{lb:g}", source_borne=src,
                               statut=statut, note=note))
    base = os.path.join(RES, "meilleurs_connus_article")
    with open(base + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lignes[0])); w.writeheader(); w.writerows(lignes)
    md = ["# Meilleurs plannings connus et bornes inférieures, avec provenance\n",
          "Généré par `outils/table_meilleurs_connus.py` depuis la banque, `cpsat_bornes.json` et `meilleurs_connus.csv` "
          "(FJSPLib). Régime A = avec maintenance (s = 1) ; classique = s = 1000.\n"]
    for reg in ("A", "classique"):
        L = [l for l in lignes if l["regime"] == reg and l["test"] == "oui"]
        st = Counter("optimum prouvé" if l["statut"] == "optimum prouvé" else "ouvert" for l in L)
        md.append(f"- {reg} : {len(L)} instances de test ; optimum prouvé {st['optimum prouvé']}, ouvertes {st['ouvert']} ; "
                  f"meilleur connu produit par : {dict(Counter(l['source_meilleur'].split(' [')[0] for l in L).most_common(6))} ; "
                  f"plus bas que FJSPLib : {sum(1 for l in L if l['note'])}")
    md += ["\n| Instance | Test | Régime | Meilleur C_max | Source | Borne inf. | Source de la borne | Statut | Note |",
           "|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {l['instance']} | {l['test']} | {l['regime']} | {l['meilleur_cmax']} | {l['source_meilleur']} | "
           f"{l['borne_inf']} | {l['source_borne']} | {l['statut']} | {l['note']} |" for l in lignes]
    open(base + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md[:5]))


if __name__ == "__main__":
    main()
