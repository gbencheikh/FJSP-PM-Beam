"""Chargement des instances augmentées (fichiers .fjs + paramètres de maintenance).

Le fichier .fjs donne : jobs, opérations, machines compatibles, durées. On y ajoute, pour chaque
machine k : un seuil d'usure T_k, une durée de maintenance M_k et une durée de réparation R_k
(voir jssp_pm/fjsp_instance.py, fonction attach_wear_v3, et results_v3/instances_maintenance.csv).
"""
import glob
from jssp_pm.fjsp_instance import load_fjs_v3

HURINK_IDX = [1, 6, 11, 16, 21, 26, 31, 36, 41, 46]   # sous-ensemble historique (phase 1, 30 instances)
# Article 1 : la01–la40 des trois jeux de Hurink = fichiers 4 à 43 (1–3 = mt06, mt10, mt20 ; 44+ = autres).
# Correspondance vérifiée fichier par fichier avec les instances de Song et al. (externe/correspondance_instances_song.csv).
HURINK_LA = list(range(4, 44))
# Instances de réglage Taguchi (copie de experiences_article1/statistiques.INSTANCES_REGLAGE, sans import circulaire)
REGLAGE_TAGUCHI = {"HurinkEdata3", "HurinkEdata13", "HurinkEdata23", "HurinkEdata33",
                   "HurinkRdata8", "HurinkRdata18", "HurinkRdata28", "HurinkRdata38"}
PARAMS = {"A": dict(tau=0.5, kappa=3.0), "B": dict(tau=0.25, kappa=1.5)}


def fichiers(familles):
    f = []
    if "Brandimarte" in familles:
        f += [f"Instances/1_Brandimarte/BrandimarteMk{i}.fjs" for i in range(1, 11)]
    if "Hurink" in familles:
        f += [f"Instances/2b_Hurink_edata/HurinkEdata{i}.fjs" for i in HURINK_IDX]
        f += [f"Instances/2c_Hurink_rdata/HurinkRdata{i}.fjs" for i in HURINK_IDX]
    for jeu, fam in (("2b_Hurink_edata", "HurinkEdata"), ("2c_Hurink_rdata", "HurinkRdata"),
                     ("2d_Hurink_vdata", "HurinkVdata")):
        if "HurinkLa" in familles or fam + "La" in familles:
            f += [f"Instances/{jeu}/{fam}{i}.fjs" for i in HURINK_LA]
    # E10b (déclaré le 14/10/2026) : une instance sur deux de Hurink edata / rdata la01–la40 (fichiers d'indice pair
    # 4, 6, ..., 42 = la01, la03, ..., la39), instances de réglage Taguchi exclues (Rdata 8, 18, 28, 38) -> 20 + 16 = 36.
    for fam, jeu in (("HurinkEdata", "2b_Hurink_edata"), ("HurinkRdata", "2c_Hurink_rdata")):
        if fam + "LaPair" in familles:
            f += [f"Instances/{jeu}/{fam}{i}.fjs" for i in HURINK_LA if i % 2 == 0 and f"{fam}{i}" not in REGLAGE_TAGUCHI]
    if "Kacem" in familles:
        f += sorted(glob.glob("Instances/5_Kacem/*.fjs"))
    return list(dict.fromkeys(f))          # sans doublon si deux familles se recouvrent (Hurink et HurinkLa)


def charger_instances(familles=("Brandimarte", "Hurink", "Kacem"), regime="A", facteur_seuil=1.0):
    """Variable d'environnement FJSP_MU (R4, 29/10/2026) : durée de maintenance M_k = max(1, round(mu·u)) ;
    défaut 1 (protocole de l'article). Avec FJSP_MU ≠ 1, la banque utilise un fichier séparé (banque.py)."""
    import os
    mu = float(os.environ.get("FJSP_MU", "1"))
    # B2 (relecteur indépendant, M10 ; déclaré le 04/11/2026) : FJSP_GRAINE_PHI = g -> autre tirage des facteurs φ_k
    # (graine du protocole : 0 ; banque séparée resultats_phi<g>.csv, voir banque.py)
    graine_phi = int(os.environ.get("FJSP_GRAINE_PHI", "0"))
    insts = [load_fjs_v3(f, regime, T_scale=facteur_seuil, mu=mu, seed=graine_phi, **PARAMS[regime])
             for f in fichiers(familles) if os.path.exists(f)]
    # D4 (déclaré le 02/11/2026, 2e relecture M9) : FJSP_TK_LK=1 -> T_k = L_k, charge totale des opérations éligibles
    # sur k : la maintenance n'est jamais nécessaire (problème classique) mais les features restent à l'échelle usuelle.
    if os.environ.get("FJSP_TK_LK") == "1":
        import numpy as np
        for inst in insts:
            inst.T = np.array([max(1.0, float(inst.P[inst.P[:, k] > 0, k].sum())) for k in range(inst.m)])
    return insts
