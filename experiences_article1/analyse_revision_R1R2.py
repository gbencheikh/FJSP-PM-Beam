"""Analyse DÉCLARÉE (PROTOCOLE § 3 sexies) des campagnes R1 (filtre non appris) et R2 (imitation seule).

R1 : pour chaque (B, K) ∈ {(5,4), (10,4), (20,4), (50,5)}, réseau final (RL:imit-ft) contre chaque filtre non appris
     (regle, fin, borne) : écart au recuit 50k par instance, différence d'écart, IC bootstrap 95 %, V/E/D, Wilcoxon apparié,
     Holm sur les 12 tests. Règle : le filtre appris « apporte » s'il est significativement meilleur que le MEILLEUR
     filtre non appris (écart moyen le plus bas au même réglage) pour au moins 3 des 4 réglages.
R2 : réseau d'imitation seule (RL:imit-seule) contre réseau final aux mêmes réglages (glouton, 100 tirages × 5 graines,
     4 faisceaux), Holm sur 6 tests.
Secondaire : écart moyen et plannings évalués de toutes les variantes (courbe qualité / évaluations).

  python -m experiences_article1.analyse_revision_R1R2   -> resultats/revision_R1R2.md|csv
"""
import csv, os, sys
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import (charger, bootstrap_ic, wilcoxon, holm, famille,   # noqa: E402
                                               INSTANCES_REGLAGE, BANQUE)
from metaheuristiques.instances import fichiers                                                  # noqa: E402

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
REGLAGES = [(5, 4), (10, 4), (20, 4), (50, 5)]
FILTRES = ["regle", "fin", "borne"]


def main():
    v, t, ev = charger(BANQUE, "A", 1.0)
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"])]
    noms = [n for n in noms if n not in INSTANCES_REGLAGE]
    m = lambda k, n: float(np.mean(v[k][n]))
    def ecarts(k):
        manq = [n for n in noms if n not in v[k]]
        assert not manq, (k, len(manq))
        return np.array([100 * (m(k, n) / m(REF, n) - 1) for n in noms])
    def evals(k):
        return float(np.mean([np.mean(ev[k][n]) for n in noms if ev[k].get(n)])) if ev.get(k) else float("nan")

    lignes, md = [], [f"# Révision — R1 (filtre non appris) et R2 (imitation seule)\n",
                      f"{len(noms)} instances de test ; référence : recuit simulé Taguchi, 50 000 évaluations. "
                      "Écart = C_max / référence − 1 (moyenne des graines). Différence = écart du réseau final − écart de l'autre "
                      "(négatif : le réseau final est meilleur). IC bootstrap 95 % sur les instances ; Wilcoxon apparié ; Holm.\n"]

    # ---------- R1
    tests = []
    for B, K in REGLAGES:
        kr = ("RL:imit-ft", f"faisceau={B},k={K}")
        er = ecarts(kr)
        for f in FILTRES:
            kf = (f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}")
            ef = ecarts(kf)
            d = er - ef
            tests.append(dict(groupe="R1", reglage=f"{B}x{K}", autre=f"filtre {f}", ecart_reseau=er.mean(),
                              ecart_autre=ef.mean(), diff=d.mean(), ic=bootstrap_ic(d), V=int((d < -1e-9).sum()),
                              E=int((abs(d) <= 1e-9).sum()), D=int((d > 1e-9).sum()), p=wilcoxon(er, ef),
                              eval_reseau=evals(kr), eval_autre=evals(kf)))
    ph = holm([x["p"] for x in tests])
    for x, p in zip(tests, ph):
        x["p_holm"] = p
    md += ["## R1 — réseau final contre filtres non appris (Holm sur 12 tests)\n",
           "| B × K | Filtre | Écart réseau | Écart filtre | Différence | IC 95 % | V/E/D (réseau) | p Holm | Plannings réseau | Plannings filtre |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for x in tests:
        md.append(f"| {x['reglage']} | {x['autre']} | {x['ecart_reseau']:+.2f} % | {x['ecart_autre']:+.2f} % | "
                  f"{x['diff']:+.2f} | [{x['ic'][0]:+.2f} ; {x['ic'][1]:+.2f}] | {x['V']}/{x['E']}/{x['D']} | "
                  f"{x['p_holm']:.2g} | {x['eval_reseau']:.0f} | {x['eval_autre']:.0f} |")
    # règle de décision : meilleur filtre par réglage
    md += ["\n**Règle déclarée** : comparaison au meilleur filtre non appris de chaque réglage.\n",
           "| B × K | Meilleur filtre | Réseau significativement meilleur ? |", "|---|---|---|"]
    n_ok = 0
    for B, K in REGLAGES:
        g = [x for x in tests if x["reglage"] == f"{B}x{K}"]
        best = min(g, key=lambda x: x["ecart_autre"])
        ok = best["p_holm"] < 0.05 and best["diff"] < 0
        n_ok += ok
        md.append(f"| {B}x{K} | {best['autre']} ({best['ecart_autre']:+.2f} %) | "
                  f"{'oui' if ok else 'non'} (différence {best['diff']:+.2f}, p Holm {best['p_holm']:.2g}) |")
    md.append(f"\n**Verdict R1** : réseau significativement meilleur que le meilleur filtre non appris pour {n_ok}/4 réglages "
              f"→ {'le filtre appris apporte (≥ 3/4)' if n_ok >= 3 else 'critère NON atteint (< 3/4) : contribution à reformuler'}.\n")
    # par famille (descriptif) pour le meilleur filtre
    md += ["### Par famille (descriptif) : écart au recuit, réseau / meilleur filtre de chaque réglage\n",
           "| B × K | Famille | n | Réseau | " + " | ".join(f"filtre {f}" for f in FILTRES) + " |",
           "|---|---|---|---|" + "---|" * len(FILTRES)]
    fam = np.array([famille(n) for n in noms])
    for B, K in REGLAGES:
        er = ecarts(("RL:imit-ft", f"faisceau={B},k={K}"))
        ef = {f: ecarts((f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}")) for f in FILTRES}
        for F in dict.fromkeys(fam):
            i = fam == F
            md.append(f"| {B}x{K} | {F} | {i.sum()} | {er[i].mean():+.2f} % | " +
                      " | ".join(f"{ef[f][i].mean():+.2f} %" for f in FILTRES) + " |")

    # ---------- R2
    paires = [("glouton", "glouton"), ("echantillons=100", "echantillons=100")] + \
             [(f"faisceau={B},k={K}", f"faisceau={B},k={K}") for B, K in REGLAGES]
    t2 = []
    for c_ft, c_il in paires:
        kf, ki = ("RL:imit-ft", c_ft), ("RL:imit-seule", c_il)
        ef_, ei = ecarts(kf), ecarts(ki)
        d = ef_ - ei
        t2.append(dict(groupe="R2", reglage=c_ft, autre="imitation seule", ecart_reseau=ef_.mean(), ecart_autre=ei.mean(),
                       diff=d.mean(), ic=bootstrap_ic(d), V=int((d < -1e-9).sum()), E=int((abs(d) <= 1e-9).sum()),
                       D=int((d > 1e-9).sum()), p=wilcoxon(ef_, ei), eval_reseau=evals(kf), eval_autre=evals(ki)))
    for x, p in zip(t2, holm([x["p"] for x in t2])):
        x["p_holm"] = p
    md += ["\n## R2 — réseau final (imitation + PPO) contre imitation seule (Holm sur 6 tests)\n",
           "| Réglage | Écart final | Écart imitation seule | Différence | IC 95 % | V/E/D (final) | p Holm |",
           "|---|---|---|---|---|---|---|"]
    for x in t2:
        md.append(f"| {x['reglage']} | {x['ecart_reseau']:+.2f} % | {x['ecart_autre']:+.2f} % | {x['diff']:+.2f} | "
                  f"[{x['ic'][0]:+.2f} ; {x['ic'][1]:+.2f}] | {x['V']}/{x['E']}/{x['D']} | {x['p_holm']:.2g} |")

    # ---------- courbe qualité / évaluations (secondaire)
    md += ["\n## Qualité / plannings évalués (secondaire)\n", "| Variante | Réglage | Écart moyen | Plannings évalués |",
           "|---|---|---|---|"]
    variantes = [("Réseau final", "RL:imit-ft", "faisceau={B},k={K}"), ("Imitation seule", "RL:imit-seule", "faisceau={B},k={K}")] + \
                [(f"Filtre {f}", f"Faisceau:filtre-{f}", "faisceau={B},k={K},filtre=" + f) for f in FILTRES]
    courbe = []
    for nom, meth, cfg in variantes:
        for B, K in REGLAGES:
            k = (meth, cfg.format(B=B, K=K))
            courbe.append((nom, f"{B}x{K}", ecarts(k).mean(), evals(k)))
    for B in (5, 20, 50, 100, 200):
        k = ("Faisceau:regle", f"faisceau={B},k=0")
        if all(n in v[k] for n in noms):
            courbe.append(("Sans filtre (toutes les actions)", f"{B}x tout", ecarts(k).mean(), evals(k)))
    for nom, r, e, n in courbe:
        md.append(f"| {nom} | {r} | {e:+.2f} % | {n:.0f} |")

    out = os.path.join(ICI, "resultats", "revision_R1R2")
    open(out + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    with open(out + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["groupe", "reglage", "autre", "ecart_reseau", "ecart_autre", "diff", "ic_bas", "ic_haut", "V", "E", "D",
                    "p", "p_holm", "eval_reseau", "eval_autre"])
        for x in tests + t2:
            w.writerow([x["groupe"], x["reglage"], x["autre"], f"{x['ecart_reseau']:.4f}", f"{x['ecart_autre']:.4f}",
                        f"{x['diff']:.4f}", f"{x['ic'][0]:.4f}", f"{x['ic'][1]:.4f}", x["V"], x["E"], x["D"],
                        f"{x['p']:.3g}", f"{x['p_holm']:.3g}", f"{x['eval_reseau']:.0f}", f"{x['eval_autre']:.0f}"])
    print("\n".join(md))


if __name__ == "__main__":
    main()
