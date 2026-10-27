"""Agent qui anticipe (réseau + moteur rapide, faisceau élagué) sur les benchmarks -> banque de résultats.

  python anticiper.py --modele models/imitation/cand_ft_best.pt --nom imit-ft --largeur 5 --k 4 --processus 10
  python anticiper.py --modele models/imitation/cand_ft_best.pt --nom imit-ft --largeur 50 --k 5 --processus 10
  python anticiper.py --sans-reseau --nom regle --largeur 5 --processus 10      # recherche sans réseau

--largeur B : nombre de pistes gardées en parallèle ; --k K : actions proposées par le réseau par piste
(0 = toutes). Méthode dans la banque : « RL:<nom> », config « faisceau=B,k=K » ; evaluations = nombre de
plannings complétés par le moteur (comparable aux évaluations des métaheuristiques).
Le tableau final compare au recuit simulé réglé par Taguchi (50 000 évaluations), instance par instance.
"""
import argparse, os, sys
import multiprocessing as mp
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jssp_pm.anticipation import AgentAnticipation
from jssp_pm.reseaux import charger_reseau
from jssp_pm.fjsp_cpsat import check
from metaheuristiques.instances import charger_instances
from banque_resultats import banque

REGIME = "A"
REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
_NET = {}


def une_instance(args):
    inst, chemin, B, K, regles, elagage, doublons = args
    torch.set_num_threads(1)
    if chemin and _NET.get("chemin") != chemin:
        _NET["net"], _NET["chemin"] = charger_reseau(chemin), chemin
    agent = AgentAnticipation(_NET["net"] if chemin else None, B, K, regles=regles,
                              elagage=elagage, doublons=doublons)
    c, plan, st = agent.planifier(inst)
    check(inst, plan)
    return inst.name, c, plan, st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modele", default=None)
    ap.add_argument("--sans-reseau", action="store_true")
    ap.add_argument("--nom", required=True)
    ap.add_argument("--largeur", type=int, default=5)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--regles", nargs="+", default=["MWKR"], choices=["MWKR", "MOR", "SPT", "LPT"])
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "Hurink"])
    ap.add_argument("--facteur-seuil", type=float, default=1.0)
    ap.add_argument("--processus", type=int, default=2)
    ap.add_argument("--sans-elagage", action="store_true", help="ablation : pas d'élagage par borne inférieure")
    ap.add_argument("--sans-doublons", action="store_true", help="ablation : pas de suppression des doublons")
    ap.add_argument("--forcer", action="store_true")
    ap.add_argument("--suffixe", default="", help="suffixe du rapport .md (14/10/2026, E10b : ne pas écraser le rapport de E10)")
    a = ap.parse_args()
    assert a.sans_reseau or a.modele, "donner --modele ou --sans-reseau"
    chemin = None if a.sans_reseau else a.modele
    cfg = f"faisceau={a.largeur},k={a.k if chemin else 0}" + ("" if a.regles == ["MWKR"] else ",regles=" + "+".join(a.regles)) \
        + (",sans_elagage" if a.sans_elagage else "") + (",sans_doublons" if a.sans_doublons else "")
    methode = f"RL:{a.nom}" if chemin else f"Faisceau:{a.nom}"
    instances = charger_instances(a.familles, regime=REGIME, facteur_seuil=a.facteur_seuil)
    deja = banque.cles_existantes()
    taches = [(i, chemin, a.largeur, a.k, tuple(a.regles), not a.sans_elagage, not a.sans_doublons) for i in instances
              if a.forcer or banque.cle(i.name, REGIME, a.facteur_seuil, methode, cfg, 0) not in deja]
    print(f"{len(taches)} instances à lancer ({methode} [{cfg}])", flush=True)
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    with ctx.Pool(a.processus) as pool:
        for nom, c, plan, st in pool.imap_unordered(une_instance, taches):
            npm = sum(1 for s in plan if s[3] == 2)
            banque.ajouter(nom, REGIME, a.facteur_seuil, methode, cfg, 0, c, npm, 0, st["temps_s"], plan,
                           evaluations=st["evaluations"])
            print(f"{nom} : {c:g}  ({st['evaluations']} évaluations, {st['temps_s']:.1f} s)", flush=True)

    # tableau : agent qui anticipe vs recuit simulé Taguchi
    noms = sorted(i.name for i in instances)
    B = [r for r in banque.charger() if r["regime"] == REGIME and float(r["facteur_seuil"]) == a.facteur_seuil
         and r["instance"] in noms]
    val = lambda m, c, n, col="cmax": [float(r[col]) for r in B if r["methode"] == m and r["config"] == c
                                       and r["instance"] == n and r[col] != ""]
    ok = [n for n in noms if val(methode, cfg, n) and val(*REF, n)]
    md = [f"# Agent qui anticipe « {methode} [{cfg}] » face au recuit simulé (Taguchi, 50 000 évaluations)\n"]
    if ok:
        ag = np.array([np.mean(val(methode, cfg, n)) for n in ok])
        sa = np.array([np.mean(val(*REF, n)) for n in ok])
        t_ag = np.mean([np.mean(val(methode, cfg, n, "temps_s")) for n in ok])
        t_sa = np.mean([np.mean(val(*REF, n, "temps_s")) for n in ok])
        ev = np.mean([np.mean(val(methode, cfg, n, "evaluations")) for n in ok])
        d = ag - sa
        md += ["| Famille | Instances | Écart moyen au recuit | V/E/D de l'agent |", "|---|---|---|---|"]
        for fam in ("Brandimarte", "HurinkEdata", "HurinkRdata", "HurinkVdata", "Kacem"):
            idx = [i for i, n in enumerate(ok) if fam in n]
            if idx:
                md.append(f"| {fam} | {len(idx)} | {100 * np.mean(ag[idx] / sa[idx] - 1):+.2f} % | "
                          f"{(d[idx] < -1e-9).sum()}/{(abs(d[idx]) <= 1e-9).sum()}/{(d[idx] > 1e-9).sum()} |")
        md.append(f"| **Total** | {len(ok)} | **{100 * np.mean(ag / sa - 1):+.2f} %** | "
                  f"{(d < -1e-9).sum()}/{(abs(d) <= 1e-9).sum()}/{(d > 1e-9).sum()} |")
        md.append(f"\nTemps moyen par instance : agent {t_ag:.1f} s, recuit {t_sa:.1f} s. "
                  f"Plannings évalués : agent {ev:.0f}, recuit 50 000.")
    else:
        md.append(f"(pas de résultat « {REF[1]} » dans la banque pour comparer)")
    os.makedirs("comparaisons", exist_ok=True)
    fichier = f"comparaisons/anticipation_{a.nom}_{cfg.replace(',', '_').replace('=', '')}{a.suffixe}.md"
    open(fichier, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
