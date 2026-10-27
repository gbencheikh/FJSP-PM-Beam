"""Exporte les paramètres d'usure des instances de l'article 1 (régime A).

Écrit Instances/parametres_usure_regime_A.csv (une ligne par machine) et
Instances/parametres_usure_regime_A.json (une entrée par instance, via fjsp_instance.instance_record).
Les paramètres sont recalculés à partir des fichiers .fjs par le protocole publié
(jssp_pm/fjsp_instance.py, attach_wear_v3, graine 0) : ce fichier sert de référence et de contrôle.

Usage (depuis la racine du dépôt) :
  python -m outils.exporter_instances
"""
import csv, json, os
from metaheuristiques.instances import fichiers, PARAMS
from jssp_pm.fjsp_instance import load_fjs_v3, instance_record
from experiences_article1.statistiques import INSTANCES_REGLAGE

FAMILLES = ["Brandimarte", "HurinkLa", "Kacem"]


def main():
    lignes, enregistrements = [], []
    for f in fichiers(FAMILLES):
        inst = load_fjs_v3(f, "A", **PARAMS["A"])
        rec = instance_record(inst)
        rec["fichier"] = f.replace(os.sep, "/")
        rec["ensemble"] = "reglage_taguchi" if inst.name in INSTANCES_REGLAGE else "test"
        enregistrements.append(rec)
        for k in range(inst.m):
            lignes.append(dict(instance=inst.name, ensemble=rec["ensemble"], machine=k + 1,
                               T=int(inst.T[k]), M=int(inst.M[k]), R=int(inst.R[k])))
    os.makedirs("Instances", exist_ok=True)
    with open("Instances/parametres_usure_regime_A.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lignes[0]))
        w.writeheader(); w.writerows(lignes)
    with open("Instances/parametres_usure_regime_A.json", "w", encoding="utf-8") as fh:
        json.dump(enregistrements, fh, indent=1, ensure_ascii=False)
    n_test = sum(r["ensemble"] == "test" for r in enregistrements)
    print(f"{len(enregistrements)} instances ({n_test} de test), {len(lignes)} machines")


if __name__ == "__main__":
    main()
