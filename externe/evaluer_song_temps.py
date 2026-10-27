"""E10s — Song et al. (2023) à BUDGET DE TEMPS ÉGAL à celui du faisceau guidé, sur UN cœur (déclaré le 9/10/2026,
avant tout calcul ; PROTOCOLE § 3 quater).

Pour chaque instance et chaque réglage du faisceau (5×4, 10×4, 50×5), le budget de Song est le temps mur mesuré du
faisceau sur CETTE instance (E10 : FJSP classique, un processus, machine au repos), lu dans budgets_song.csv
(produit par `python -m outils.budgets_song` dans jssp_pm/jssp_pm). Song tire des lots de 20 plannings selon sa
politique (mode échantillonnage de leur code), garde le meilleur, et s'arrête au premier lot qui fait dépasser le
budget (le dépassement est enregistré). Un lot au moins est toujours tiré. 1 fil PyTorch, un processus.
Graines 0, 1, 2 (lot b de la graine g : graine 1000·g + b). Temps mesuré : création de l'environnement comprise.

  cd externe
  python evaluer_song_temps.py --budgets budgets_song.csv --graines 0 1 2      # -> resultats_song_temps.csv
"""
import argparse, csv, os, time
import numpy as np
import torch

import evaluer_song as es            # modèle, environnement et correctif identiques à E8

ICI = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budgets", required=True, help="CSV instance,reglage,budget_s")
    ap.add_argument("--graines", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--lot", type=int, default=20)
    ap.add_argument("--modele", default=os.path.join(es.DEPOT, "model", "save_10_5.pt"))
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats_song_temps.csv"))
    a = ap.parse_args()
    es._preparer(a.modele, 1, False)
    model, env_p = es._CTX["model"], es._CTX["env_p"]
    corr = {r["instance_projet"]: r["instance_song"] for r in csv.DictReader(
        open(os.path.join(ICI, "correspondance_instances_song.csv"))) if r["instance_song"]}
    corr["BrandimarteMk6"] = "Mk06"
    # échauffement non chronométré (premier appel PyTorch), pour ne pas pénaliser la première instance
    f0 = os.path.join(es.DEPOT, "data_test", "Public", "Mk01.fjs")
    nj, nm, _ = es.nums_detec(open(f0).readlines())
    env0 = es.FJSPEnv([f0] * a.lot, dict(env_p, num_jobs=nj, num_mas=nm, batch_size=a.lot), data_source="file")
    es.resoudre(env0, model, True)
    champs = ["instance", "reglage", "budget_s", "graine", "cmax", "temps_s", "n_tirages", "depassement_s"]
    deja = set()
    if os.path.exists(a.sortie):
        deja = {(r["instance"], r["reglage"], r["graine"]) for r in csv.DictReader(open(a.sortie, encoding="utf-8"))}
    else:
        with open(a.sortie, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=champs).writeheader()
    for b in csv.DictReader(open(a.budgets, encoding="utf-8")):
        n, reg, budget = b["instance"], b["reglage"], float(b["budget_s"])
        if n not in corr:
            continue
        f = os.path.join(es.DEPOT, "data_test", "Public", corr[n] + ".fjs")
        for g in a.graines:
            if (n, reg, str(g)) in deja:
                continue
            t0 = time.perf_counter()
            nj, nm, _ = es.nums_detec(open(f).readlines())
            env = es.FJSPEnv([f] * a.lot, dict(env_p, num_jobs=nj, num_mas=nm, batch_size=a.lot), data_source="file")
            best, k = np.inf, 0
            while True:
                es.graine(1000 * g + k); env.reset()
                c, _ = es.resoudre(env, model, True)
                best, k = min(best, c), k + 1
                if time.perf_counter() - t0 >= budget:
                    break
            dt = time.perf_counter() - t0
            ligne = dict(instance=n, reglage=reg, budget_s=round(budget, 3), graine=g, cmax=best, temps_s=round(dt, 3),
                         n_tirages=k * a.lot, depassement_s=round(max(0.0, dt - budget), 3))
            with open(a.sortie, "a", newline="", encoding="utf-8") as fo:
                csv.DictWriter(fo, fieldnames=champs).writerow(ligne)
            print(n, reg, f"graine {g}", best, f"{k * a.lot} tirages, {dt:.1f} s / budget {budget:.1f} s", flush=True)


if __name__ == "__main__":
    main()
