"""Élagage par famille et écart politique / règle sur « borne = incumbent » (lit resultats/taux_elagage.csv ; rien
n'est recalculé sauf la borne inférieure à la racine). Demandé le 7/10/2026 après E6b.

Sorties : experiences_article1/resultats/taux_elagage_par_famille.md|csv
  1. Par famille et réglage : taux d'élagage (moyenne par instance), part « borne = incumbent » (moyenne par
     instance, et poolée sur les enfants élagués).
  2. Politique contre règle, même B : part « borne = incumbent » appariée par instance ; V/E/D (politique plus
     haute / égale / plus basse), Wilcoxon apparié ; Holm sur tous les tests du tableau.
  3. Serrage de l'incumbent : écart du C_max final (politique) à la meilleure borne inférieure disponible
     (max de la borne du moteur à la racine, régime A, et de la borne FJSPLib du FJSP classique, valable aussi
     avec maintenance) ; Spearman avec le taux d'élagage et la part « borne = incumbent ».

  python -m outils.elagage_par_famille
"""
import csv, os, sys
import numpy as np
from scipy.stats import spearmanr, wilcoxon

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from metaheuristiques.instances import charger_instances      # noqa: E402
from jssp_pm.moteur_rapide import MoteurRapide                # noqa: E402
from jssp_pm.fjsp_env3 import FJSPEnv3                        # noqa: E402
from experiences_article1.statistiques import holm            # noqa: E402

RES = os.path.join(RACINE, "experiences_article1", "resultats")
FAMS = [("Brandimarte", "Brandimarte"), ("HurinkEdata", "Hurink edata"), ("HurinkRdata", "Hurink rdata"),
        ("HurinkVdata", "Hurink vdata"), ("Kacem", "Kacem")]
REGLAGES = ["politique 1x4", "politique 5x4", "politique 50x5", "regle 5x0", "regle 50x0"]
PAIRES = [("politique 5x4", "regle 5x0"), ("politique 50x5", "regle 50x0")]


def famille(n):
    return next(l for p, l in FAMS if n.startswith(p))


def main():
    R = list(csv.DictReader(open(os.path.join(RES, "taux_elagage.csv"), encoding="utf-8")))
    D = {(r["reglage"], r["instance"]): r for r in R}
    noms = sorted({r["instance"] for r in R})
    taux = lambda g, n: int(D[(g, n)]["elagues"]) / max(int(D[(g, n)]["examines"]), 1)
    part = lambda g, n: int(D[(g, n)]["elagues_borne_egale"]) / int(D[(g, n)]["elagues"]) if int(D[(g, n)]["elagues"]) else np.nan
    groupes = [("Toutes", [x for x in noms])] + [(l, [x for x in noms if famille(x) == l]) for _, l in FAMS] \
        + [("Hurink (3 jeux)", [x for x in noms if x.startswith("Hurink")])]
    md = [f"# Élagage par famille ({len(noms)} instances, depuis `taux_elagage.csv`)\n",
          "« Borne = incumbent » : enfant élagué dont la borne inférieure égale le meilleur planning connu au moment de la "
          "coupure (au mieux une égalité) ; sinon borne strictement supérieure.\n",
          "## 1. Taux d'élagage et part « borne = incumbent » (moyenne par instance ; entre parenthèses : poolée)\n",
          "| Groupe | n | " + " | ".join(REGLAGES) + " |", "|---|---|" + "---|" * len(REGLAGES)]
    lignes_csv = []
    for nom, L in groupes:
        cel = []
        for g in REGLAGES:
            t = np.mean([taux(g, n) for n in L])
            p = np.nanmean([part(g, n) for n in L])
            el = sum(int(D[(g, n)]["elagues"]) for n in L); eg = sum(int(D[(g, n)]["elagues_borne_egale"]) for n in L)
            cel.append(f"{100*t:.1f} % ; {100*p:.0f} % ({100*eg/max(el,1):.0f} %)")
            lignes_csv.append(dict(groupe=nom, n=len(L), reglage=g, taux_elagage=round(100*t, 2),
                                   part_borne_egale_moy=round(100*p, 1), part_borne_egale_poolee=round(100*eg/max(el, 1), 1)))
        md.append(f"| {nom} | {len(L)} | " + " | ".join(cel) + " |")
    md += ["\nCellule : taux d'élagage ; part « borne = incumbent ».\n",
           "## 2. Politique contre règle (même B), part « borne = incumbent » appariée par instance\n",
           "| Paire | Groupe | n | Politique | Règle | Politique plus haute / égale / plus basse | p | p (Holm) |",
           "|---|---|---|---|---|---|---|---|"]
    tests = []
    for pol, reg in PAIRES:
        for nom, L in groupes:
            a = np.array([part(pol, n) for n in L]); b = np.array([part(reg, n) for n in L])
            ok = ~(np.isnan(a) | np.isnan(b)); a, b = a[ok], b[ok]; d = a - b
            p = float(wilcoxon(a, b).pvalue) if (np.abs(d) > 1e-12).sum() >= 1 and len(d) >= 6 else np.nan
            tests.append([f"{pol} / {reg}", nom, len(a), 100*a.mean(), 100*b.mean(),
                          f"{(d>1e-12).sum()}/{(np.abs(d)<=1e-12).sum()}/{(d<-1e-12).sum()}", p])
    ps = [t[6] for t in tests if not np.isnan(t[6])]
    ph = iter(holm(ps))
    for t in tests:
        h = next(ph) if not np.isnan(t[6]) else np.nan
        md.append(f"| {t[0]} | {t[1]} | {t[2]} | {t[3]:.0f} % | {t[4]:.0f} % | {t[5]} | "
                  + ("–" if np.isnan(t[6]) else f"{t[6]:.2g}") + " | " + ("–" if np.isnan(h) else f"{h:.2g}") + " |")
    md.append("\nTest non fait si n < 6 (Kacem, 4 instances).\n")
    # 3. serrage de l'incumbent
    fjsplib = {r["instance"]: float(r["borne_inf"]) for r in csv.DictReader(open(os.path.join(
        RACINE, "experiences_article1", "meilleurs_connus.csv"), encoding="utf-8")) if r["borne_inf"]}
    # bornes CP-SAT d'E9 (régime A, et FJSP classique = relaxation), ajoutées le 9/10/2026 pour le re-test pré-déclaré
    cps = {}
    fcp = os.path.join(RES, "cpsat_bornes.json")
    if os.path.exists(fcp):
        import json
        for cle, r in json.load(open(fcp, encoding="utf-8")).items():
            if r.get("bound"):
                cps[cle.split("|")[0]] = max(cps.get(cle.split("|")[0], 0.0), float(r["bound"]))
    lb = {}
    for i in charger_instances(["Brandimarte", "HurinkLa", "Kacem"], regime="A", facteur_seuil=1.0):
        if i.name in noms:
            mr = MoteurRapide(i); e = FJSPEnv3("full", safety=True); e.reset(i)
            lb[i.name] = max(float(mr.borne_inf(mr.etat(e))), fjsplib.get(i.name, 0.0), cps.get(i.name, 0.0))
    md += ["## 3. Serrage de l'incumbent\n",
           "Écart = C_max final du faisceau (politique) / meilleure borne inférieure disponible − 1 (max de la borne du moteur "
           "à la racine, de la borne FJSPLib du FJSP classique et des bornes CP-SAT d'E9). C'est une borne SUPÉRIEURE de l'écart à "
           "l'optimum.\n", "| Réglage | Groupe | Écart médian | Spearman(écart, taux d'élagage) | Spearman(écart, part borne = incumbent) |",
           "|---|---|---|---|---|"]
    for g in ("politique 5x4", "politique 50x5"):
        for nom, L in groupes:
            gap = np.array([float(D[(g, n)]["cmax"]) / lb[n] - 1 for n in L])
            t = np.array([taux(g, n) for n in L]); p = np.array([part(g, n) for n in L])
            s1 = spearmanr(gap, t) if len(L) >= 6 else None
            s2 = spearmanr(gap, p, nan_policy="omit") if len(L) >= 6 else None
            f = lambda s: "–" if s is None else f"{s.correlation:+.2f} (p {s.pvalue:.2g})"
            md.append(f"| {g} | {nom} | {100*np.median(gap):.1f} % | {f(s1)} | {f(s2)} |")
    base = os.path.join(RES, "taux_elagage_par_famille")
    with open(base + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lignes_csv[0])); w.writeheader(); w.writerows(lignes_csv)
    open(base + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
