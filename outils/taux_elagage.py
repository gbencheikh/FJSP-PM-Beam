"""Taux d'élagage et de doublons du faisceau, instance par instance (vérification de l'ablation E6).

Pour chaque réglage, relance le faisceau (déterministe : mêmes plannings que dans la banque) et relève :
  - enfants      : actions évaluées par le moteur et classées (toutes pistes, toutes étapes) ;
  - examinés     : enfants passés en revue pour entrer dans le faisceau (au plus B retenus par étape) ;
  - élagués      : examinés écartés parce que leur borne inférieure atteint le meilleur planning connu ;
  - doublons     : examinés écartés parce que la même situation est déjà dans le faisceau.
  - élagués remplacés : élagués dont la place dans le faisceau a été prise par un enfant moins bien classé
    (sinon le faisceau de l'étape est simplement plus étroit) ;
  - élagués à borne égale : borne inférieure = meilleur planning COURANT (l'incumbent au moment de la coupure,
    pas le meilleur final de la banque : c'est un certificat, pas une mesure a posteriori) ; la branche pouvait au
    mieux l'égaler. Les autres élagués ont une borne STRICTEMENT SUPÉRIEURE à l'incumbent (la branche ne pouvait
    même pas l'égaler). Aucun enfant élagué n'a une borne inférieure à l'incumbent : c'est la règle de coupure.
Taux = élagués / examinés et doublons / examinés. Rien n'est écrit dans la banque : diagnostic E6b seulement ;
le C_max de la banque reste celui de la recherche AVEC élagage (contrefactuel sans élagage : ablation E6).
Ensemble : les 127 instances de test (134 calculées − 7 de réglage Taguchi, PROTOCOLE § 2).

  python -m outils.taux_elagage --processus 8          # -> experiences_article1/resultats/taux_elagage.csv|md
"""
import argparse, csv, os, sys
import multiprocessing as mp
import numpy as np
import torch

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from jssp_pm.anticipation import AgentAnticipation          # noqa: E402
from jssp_pm.reseaux import charger_reseau                  # noqa: E402
from metaheuristiques.instances import charger_instances    # noqa: E402

MODELE = "models/imitation/cand_ft_best.pt"
REGLAGES = [("politique", MODELE, 1, 4), ("politique", MODELE, 5, 4), ("politique", MODELE, 50, 5),
            ("regle", None, 5, 0), ("regle", None, 50, 0)]
REGLAGE_TAGUCHI = {"HurinkEdata3", "HurinkEdata13", "HurinkEdata23", "HurinkEdata33",
                   "HurinkRdata8", "HurinkRdata18", "HurinkRdata28", "HurinkRdata38"}
_NET = {}


def tache(args):
    nom, chemin, B, K, inst = args
    torch.set_num_threads(1)
    if chemin and _NET.get("chemin") != chemin:
        _NET["net"], _NET["chemin"] = charger_reseau(chemin), chemin
    c, _, st = AgentAnticipation(_NET["net"] if chemin else None, B, K).planifier(inst)
    return dict(reglage=f"{nom} {B}x{K}", instance=inst.name, cmax=c, evaluations=st["evaluations"],
                enfants=st["enfants"], examines=st["examines"], elagues=st["elagages"], doublons=st["doublons"],
                elagues_remplaces=st["elagues_remplaces"], elagues_borne_egale=st["elagues_borne_egale"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "HurinkLa", "Kacem"])
    ap.add_argument("--processus", type=int, default=2)
    ap.add_argument("--sortie", default=os.path.join(RACINE, "experiences_article1", "resultats", "taux_elagage"))
    a = ap.parse_args()
    insts = [i for i in charger_instances(a.familles, regime="A", facteur_seuil=1.0) if i.name not in REGLAGE_TAGUCHI]
    print(f"{len(insts)} instances (réglage Taguchi exclu)", flush=True)
    taches = [(n, ch, B, K, i) for n, ch, B, K in REGLAGES for i in insts]
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    with ctx.Pool(a.processus) as pool:
        lignes = list(pool.imap_unordered(tache, taches))
    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    with open(a.sortie + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0])); w.writeheader(); w.writerows(sorted(lignes, key=lambda l: (l["reglage"], l["instance"])))
    md = [f"# Taux d'élagage et de doublons du faisceau ({len(insts)} instances)\n",
          "Taux = écartés / enfants examinés pour entrer dans le faisceau, moyenne sur les instances.\n",
          "Trois dernières colonnes : part des enfants élagués (tous réunis, toutes instances). « Incumbent » = meilleur "
          "planning complet connu AU MOMENT de la coupure. Remplacés : leur place est prise par un enfant moins bien classé. "
          "Borne = incumbent : la branche pouvait au mieux l'égaler ; borne > incumbent : elle ne pouvait même pas l'égaler "
          "(aucun élagué n'a une borne < incumbent, par la règle de coupure).\n",
          "| Réglage | Enfants évalués / inst. | Examinés / inst. | Taux d'élagage | Instances avec ≥ 1 élagage | Taux de doublons | Instances avec ≥ 1 doublon | Élagués remplacés | Borne = incumbent | Borne > incumbent |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in dict.fromkeys(f"{n} {B}x{K}" for n, _, B, K in REGLAGES):
        L = [l for l in lignes if l["reglage"] == r]
        ex = np.array([max(l["examines"], 1) for l in L])
        el = np.array([l["elagues"] for l in L]); do = np.array([l["doublons"] for l in L])
        tot = max(el.sum(), 1)
        rem = sum(l["elagues_remplaces"] for l in L); ega = sum(l["elagues_borne_egale"] for l in L)
        md.append(f"| {r} | {np.mean([l['enfants'] for l in L]):.0f} | {ex.mean():.0f} | {100 * np.mean(el / ex):.2f} % | "
                  f"{(el > 0).sum()}/{len(L)} | {100 * np.mean(do / ex):.2f} % | {(do > 0).sum()}/{len(L)} | "
                  f"{100 * rem / tot:.1f} % | {100 * ega / tot:.1f} % | {100 * (el.sum() - ega) / tot:.1f} % |")
    open(a.sortie + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
