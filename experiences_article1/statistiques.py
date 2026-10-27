"""Tableaux et tests statistiques de l'article 1, produits UNIQUEMENT depuis la banque de résultats.

Aucun chiffre de l'article n'est recopié à la main : tout tableau vient de ce script.

Unité statistique : l'instance (protocole figé, experiences_article1/PROTOCOLE.md).
  - valeur d'une méthode sur une instance = moyenne de ses graines ;
  - écart relatif à la référence = valeur / référence − 1 (référence : recuit Taguchi 50 000 évaluations) ;
  - IC à 95 % de l'écart moyen par bootstrap sur les instances (10 000 rééchantillonnages, graine 0) ;
  - Wilcoxon signé apparié par instance (méthode vs référence), bilatéral, correction de Holm sur
    l'ensemble des comparaisons du tableau ; victoires / égalités / défaites.

  python -m experiences_article1.statistiques --methodes experiences_article1/methodes_principal.json \
         --familles Brandimarte HurinkLa Kacem --facteur-seuil 1 --nom principal

Sorties dans experiences_article1/resultats/<nom>_* : .md (lecture), .csv (données), .tex (article),
boxplots .png / .pdf.
"""
import argparse, csv, json, os, sys
from collections import defaultdict

import numpy as np
try:                                   # console Windows (cp1252) : ne pas planter sur « − », « ≤ »…
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE)
from metaheuristiques.instances import fichiers   # noqa: E402

BANQUE = os.path.join(RACINE, "banque_resultats", "resultats.csv")
# Instances de réglage Taguchi des métaheuristiques (reglage_taguchi/taguchi.py, INSTANCES_REGLAGE) : jamais dans
# les tableaux de test. 7 d'entre elles tombent dans Hurink la01–la40 (fichiers 4 à 43) ; HurinkEdata3 (mt20) non.
INSTANCES_REGLAGE = ["HurinkEdata3", "HurinkEdata13", "HurinkEdata23", "HurinkEdata33",
                     "HurinkRdata8", "HurinkRdata18", "HurinkRdata28", "HurinkRdata38"]
SONG = os.path.join(RACINE, "externe", "resultats_song.csv")
FAMILLES_AFFICHAGE = [("Brandimarte", "Brandimarte"), ("HurinkEdata", "Hurink edata"),
                      ("HurinkRdata", "Hurink rdata"), ("HurinkVdata", "Hurink vdata"), ("Kacem", "Kacem")]


def famille(nom):
    for prefixe, lab in FAMILLES_AFFICHAGE:
        if nom.startswith(prefixe):
            return lab
    return "Autre"


def charger(banque, regime, facteur_seuil, song=None):
    """{(methode, config): {instance: [valeurs]}}, et de même pour les temps et les évaluations
    (par instance : les moyennes se font ensuite sur les seules instances analysées)."""
    v, t, ev = (defaultdict(lambda: defaultdict(list)) for _ in range(3))
    for r in csv.DictReader(open(banque, encoding="utf-8")):
        if r["regime"] != regime or abs(float(r["facteur_seuil"]) - facteur_seuil) > 1e-9 or r["cmax"] == "":
            continue
        k = (r["methode"], r["config"])
        v[k][r["instance"]].append(float(r["cmax"]))
        if r["temps_s"]:
            t[k][r["instance"]].append(float(r["temps_s"]))
        if r.get("evaluations"):
            ev[k][r["instance"]].append(float(r["evaluations"]))
    if song and os.path.exists(song) and facteur_seuil >= 1000:   # Song et al. : FJSP classique seulement
        for r in csv.DictReader(open(song, encoding="utf-8")):
            k = ("Song et al. (2023)", r["mode"])
            v[k][r["instance"]].append(float(r["cmax"]))
            t[k][r["instance"]].append(float(r["temps_s"]))
    return v, t, ev


def moyenne_instances(d, noms):
    """Moyenne sur les instances analysées de la moyenne par instance (nan si une instance manque)."""
    if not all(d.get(n) for n in noms):
        return float("nan")
    return float(np.mean([np.mean(d[n]) for n in noms]))


CPSAT = os.path.join(ICI, "resultats", "cpsat_bornes.json")


def optimums_prouves(v, facteur_seuil, externe):
    """Instances à optimum prouvé : meilleur C_max connu (banque, toutes méthodes et graines ; + FJSPLib en FJSP
    classique) = meilleure borne inférieure valide (FJSPLib, CP-SAT régime A, CP-SAT classique = relaxation).
    Ajouté le 9/10/2026. Retourne {instance: optimum}."""
    lb = defaultdict(float)
    if os.path.exists(externe):
        for r in csv.DictReader(open(externe, encoding="utf-8")):
            if r["borne_inf"]:
                lb[r["instance"]] = max(lb[r["instance"]], float(r["borne_inf"]))
    if os.path.exists(CPSAT):
        for cle, r in json.load(open(CPSAT, encoding="utf-8")).items():
            nom, fs = cle.split("|")[:2]
            if (float(fs) == facteur_seuil or float(fs) >= 1000) and r.get("bound"):
                lb[nom] = max(lb[nom], float(r["bound"]))
    meilleur = {}
    for (m, c), d in v.items():
        if m.startswith("Song") or m == "FJSPLib borne inf" or (m == "FJSPLib meilleur connu" and facteur_seuil < 1000):
            continue
        for n, x in d.items():
            meilleur[n] = min(meilleur.get(n, np.inf), min(x))
    return {n: b for n, b in meilleur.items() if lb[n] > 0 and b <= lb[n] + 1e-9}


def bootstrap_ic(x, n=10000, graine=0):
    rng = np.random.default_rng(graine)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    m = x[idx].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def wilcoxon(a, b):
    """p bilatérale du test signé de Wilcoxon apparié (égalités exclues, méthode de Pratt non utilisée)."""
    from scipy.stats import wilcoxon as w
    d = np.asarray(a) - np.asarray(b)
    if np.all(np.abs(d) < 1e-9):
        return 1.0
    return float(w(a, b, zero_method="wilcox", alternative="two-sided").pvalue)


def holm(p):
    p = np.asarray(p, float)
    ordre = np.argsort(p)
    ajust = np.empty_like(p)
    courant = 0.0
    for rang, i in enumerate(ordre):
        courant = max(courant, (len(p) - rang) * p[i])
        ajust[i] = min(1.0, courant)
    return ajust


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--methodes", required=True, help="JSON : liste de {label, methode, config}")
    ap.add_argument("--ref", default="Recuit simulé|evals=50000,depart=heuristique,params=taguchi",
                    help="méthode|config de référence")
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "HurinkLa", "Kacem"])
    ap.add_argument("--regime", default="A")
    ap.add_argument("--facteur-seuil", type=float, default=1.0)
    ap.add_argument("--banque", default=BANQUE)
    ap.add_argument("--song", default=SONG)
    ap.add_argument("--externe", default=os.path.join(ICI, "meilleurs_connus.csv"),
                    help="bornes FJSPLib (FJSP classique ; la borne inf. vaut aussi pour le régime A, voir PROTOCOLE)")
    ap.add_argument("--inclure-reglage", action="store_true",
                    help="garder les instances du réglage Taguchi (exclues par défaut : protocole § 2)")
    ap.add_argument("--nom", required=True)
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats"))
    a = ap.parse_args()

    spec = json.load(open(a.methodes, encoding="utf-8"))
    ref_m, ref_c = a.ref.split("|", 1)
    v, t, ev = charger(a.banque, a.regime, a.facteur_seuil, a.song)
    if os.path.exists(a.externe):          # FJSPLib : utilisables comme référence (--ref "FJSPLib meilleur connu|")
        for r in csv.DictReader(open(a.externe, encoding="utf-8")):
            v[("FJSPLib meilleur connu", "")][r["instance"]] = [float(r["meilleur_connu"])]
            v[("FJSPLib borne inf", "")][r["instance"]] = [float(r["borne_inf"])]
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(a.familles)]
    exclues = [x for x in noms if x in INSTANCES_REGLAGE] if not a.inclure_reglage else []
    noms = [x for x in noms if x not in exclues]
    cles = [(s["methode"], s["config"]) for s in spec]
    manquants = {s["label"]: [n for n in noms if n not in v[(s["methode"], s["config"])]] for s in spec}
    manquants["référence"] = [n for n in noms if n not in v[(ref_m, ref_c)]]
    commun = [n for n in noms if all(n in v[k] for k in cles + [(ref_m, ref_c)])]
    if not commun:
        sys.exit(f"aucune instance commune ; manquants : { {k: len(x) for k, x in manquants.items()} }")
    ref = np.array([np.mean(v[(ref_m, ref_c)][n]) for n in commun])
    fam = np.array([famille(n) for n in commun])

    opt = optimums_prouves(v, a.facteur_seuil, a.externe)
    prouves = [n for n in commun if n in opt]
    lignes, pvals = [], []
    for s, k in zip(spec, cles):
        x = np.array([np.mean(v[k][n]) for n in commun])
        gap = 100 * (x / ref - 1)
        ic = bootstrap_ic(gap)
        d = x - ref
        p = wilcoxon(x, ref)
        pvals.append(p)
        par_fam = {lab: float(gap[fam == lab].mean()) for _, lab in FAMILLES_AFFICHAGE if (fam == lab).any()}
        lignes.append(dict(label=s["label"], methode=k[0], config=k[1], n=len(commun),
                           ecart=float(gap.mean()), ic_bas=ic[0], ic_haut=ic[1], mediane=float(np.median(gap)),
                           V=int((d < -1e-9).sum()), E=int((np.abs(d) <= 1e-9).sum()), D=int((d > 1e-9).sum()),
                           n_eff=int((np.abs(d) > 1e-9).sum()),
                           p=p, temps_s=moyenne_instances(t[k], commun),
                           evaluations=moyenne_instances(ev[k], commun),
                           graines=int(np.mean([len(v[k][n]) for n in commun])), par_famille=par_fam, gaps=gap,
                           opt_atteint=sum(np.mean(v[k][n]) <= opt[n] + 1e-9 for n in prouves)))
    for l, ph in zip(lignes, holm(pvals)):
        l["p_holm"] = float(ph)

    os.makedirs(a.sortie, exist_ok=True)
    base = os.path.join(a.sortie, a.nom)
    fams = [lab for _, lab in FAMILLES_AFFICHAGE if (fam == lab).any()]
    # 15/10/2026 : flexibilité = part moyenne des machines éligibles par opération (fichier .fjs), moyennée sur les
    # instances analysées de chaque famille ; ligne d'en-tête du tableau (descriptif, aucune influence sur les tests).
    from jssp_pm.fjsp_instance import parse_fjs
    chemins = {os.path.splitext(os.path.basename(f))[0]: f for f in fichiers(a.familles)}
    def _flex(n):
        P, _ = parse_fjs(os.path.join(RACINE, chemins[n]))
        return float((P > 0).sum(1).mean() / P.shape[1])
    fl_inst = {n: _flex(n) for n in commun}
    flex = {f: float(np.mean([fl_inst[n] for n in commun if famille(n) == f])) for f in fams}
    flex_tout = float(np.mean(list(fl_inst.values())))
    json.dump(dict(par_famille=flex, toutes=flex_tout, definition="part moyenne des machines éligibles par opération"),
              open(os.path.join(a.sortie, a.nom + "_flexibilite.json"), "w", encoding="utf-8"), indent=1)
    md = [f"# {a.nom} — régime {a.regime}, facteur de seuil {a.facteur_seuil:g}\n",
          f"Référence : {ref_m} [{ref_c}]. {len(commun)} instances communes"
          + (f" ({len(noms)} de test − {len(noms) - len(commun)} absentes chez au moins une méthode, voir la note)"
             if len(commun) < len(noms) else "") + " "
          f"({', '.join(f'{f} {int((fam == f).sum())}' for f in fams)}). Banque : `{os.path.relpath(a.banque, RACINE)}`."
          + (f" Exclues (réglage Taguchi) : {', '.join(exclues)}." if exclues else ""),
          "Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; "
          "Wilcoxon apparié par instance (égalités exclues : n eff. = nombre de paires non égales), p corrigée de Holm ; "
          "V/E/D = victoires / égalités / défaites contre la référence. Opt. prouvé atteint = instances à optimum prouvé "
          "(meilleur connu = meilleure borne valide : FJSPLib, CP-SAT) où la moyenne des graines de la méthode atteint l'optimum.\n",
          "| Méthode | " + " | ".join(fams) + " | Total | IC 95 % | Médiane | V/E/D | n eff. | p (Holm) | Opt. prouvé atteint | Temps/inst. (s) | Plannings évalués | Graines |",
          "|---|" + "---|" * (len(fams) + 10)]
    md.append("| *Flexibilité (part des machines éligibles)* | " + " | ".join(f"{flex[f]:.2f}" for f in fams)
              + f" | {flex_tout:.2f} |" + " |" * 9)
    for l in lignes:
        md.append(f"| {l['label']} | " + " | ".join(f"{l['par_famille'].get(f, float('nan')):+.2f} %" for f in fams)
                  + f" | **{l['ecart']:+.2f} %** | [{l['ic_bas']:+.2f} ; {l['ic_haut']:+.2f}] | {l['mediane']:+.2f} % | "
                  f"{l['V']}/{l['E']}/{l['D']} | {l['n_eff']} | {l['p_holm']:.2g} | {l['opt_atteint']}/{len(prouves)} | {l['temps_s']:.2f} | {l['evaluations']:.0f} | {l['graines']} |")
    exclus = {k: x for k, x in manquants.items() if x}
    if exclus:
        md.append("\nInstances absentes (exclues du tableau) : " +
                  "; ".join(f"{k} : {len(x)} ({', '.join(x[:5])}{'…' if len(x) > 5 else ''})" for k, x in exclus.items()))
        if any(k.startswith("Song") for k in exclus) and all(n.startswith("Kacem") for k, x in exclus.items() for n in x):
            md.append("Kacem ne fait pas partie des instances publiées avec le modèle de Song et al. (2023) : la comparaison "
                      "porte sur les instances de test communes aux deux jeux, les instances de réglage Taguchi restant exclues.")
    open(base + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")

    with open(base + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["label", "methode", "config", "instance", "famille", "valeur", "reference", "ecart_pct", "graines"])
        for l, k in zip(lignes, cles):
            for n, g in zip(commun, l["gaps"]):
                w.writerow([l["label"], k[0], k[1], n, famille(n), np.mean(v[k][n]),
                            np.mean(v[(ref_m, ref_c)][n]), round(float(g), 4), len(v[k][n])])

    tex = ["% Produit par experiences_article1/statistiques.py — ne pas modifier à la main",
           f"% {len(commun)} instances communes sur {len(noms)} de test"
           + (f" ; absentes : {', '.join(sorted(set(n for x in exclus.values() for n in x)))}" if exclus else ""),
           f"% source : {os.path.relpath(a.banque, RACINE)} ; référence {ref_m} [{ref_c}]",
           "\\begin{tabular}{l" + "r" * (len(fams) + 5) + "}", "\\toprule",
           "Method & " + " & ".join(fams) + " & All & 95\\% CI & W/T/L & $n_{\\mathrm{eff}}$ & $p_{\\mathrm{Holm}}$ \\\\", "\\midrule",
           "\\emph{Flexibility} & " + " & ".join(f"{flex[f]:.2f}" for f in fams) + f" & {flex_tout:.2f}" + " &" * 4 + " \\\\", "\\midrule"]
    for l in lignes:
        tex.append(f"{l['label']} & " + " & ".join(f"{l['par_famille'].get(f, float('nan')):+.2f}" for f in fams)
                   + f" & {l['ecart']:+.2f} & [{l['ic_bas']:+.2f}, {l['ic_haut']:+.2f}] & {l['V']}/{l['E']}/{l['D']} & {l['n_eff']} & "
                   f"{l['p_holm']:.2g} \\\\")
    tex += ["\\bottomrule", "\\end{tabular}"]
    open(base + ".tex", "w", encoding="utf-8").write("\n".join(tex) + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, len(fams), figsize=(3.2 * len(fams), 3.6), sharey=True, squeeze=False)
        for ax, f in zip(axes[0], fams):
            ax.boxplot([l["gaps"][fam == f] for l in lignes], vert=True, showmeans=True)
            ax.axhline(0, color="0.5", lw=0.8, ls="--")
            ax.set_title(f, fontsize=9)
            ax.set_xticks(range(1, len(lignes) + 1), [l["label"] for l in lignes], rotation=60, ha="right", fontsize=7)
        axes[0][0].set_ylabel("Gap to reference (%)")
        fig.tight_layout()
        fig.savefig(base + "_boxplots.png", dpi=200)
        fig.savefig(base + "_boxplots.pdf")
    except ImportError:
        print("matplotlib absent : pas de boxplots")
    print("\n".join(md))


if __name__ == "__main__":
    main()
