"""Analyse DÉCLARÉE (PROTOCOLE § 3 septies, 02/11/2026) des campagnes D1, D3 et D4 de la 2e révision.

D1 : budget égal entre filtres (B' ajusté) ; (a) réseau contre meilleur filtre, Holm sur 4 ; (b) test global (moyenne
     par instance des 4 différences au meilleur filtre) ; (c) idem contre le filtre a priori `regle` ; effet minimal détectable.
D3 : facteur de seuil 0,7 et 1,5 : même règle que R4 (Holm sur 4) ; TOST ±1 % du faisceau 50×5 ; test global (b).
D4 : T_k = L_k : écart du glouton, des tirages et des faisceaux au recuit 50k du problème classique ; règle 20 % / 50 %.
  python -m experiences_article1.analyse_revision_D1D3D4 -> resultats/revision_D1D3D4.md
"""
import os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE)
from experiences_article1.statistiques import charger, wilcoxon, holm, bootstrap_ic, INSTANCES_REGLAGE, BANQUE  # noqa
from metaheuristiques.instances import fichiers  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
NOMS = [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"]))
        if n not in INSTANCES_REGLAGE]
D1 = {"regle": [(6, 4), (12, 4), (22, 4), (55, 5)], "fin": [(7, 4), (12, 4), (24, 4), (56, 5)],
      "borne": [(6, 4), (12, 4), (23, 4), (55, 5)]}
RESEAU = [(5, 4), (10, 4), (20, 4), (50, 5)]


def ic90(d, n=10000):
    r = np.random.default_rng(0); m = d[r.integers(0, len(d), (n, len(d)))].mean(1)
    return float(np.percentile(m, 5)), float(np.percentile(m, 95))


def outils(banque, fs, ref_banque=None, ref_fs=None):
    v, _, ev = charger(banque, "A", fs)
    vr = charger(ref_banque, "A", ref_fs)[0] if ref_banque else v
    ref = {n: np.mean(vr[REF][n]) for n in NOMS}
    def ec(k):
        assert all(n in v[k] for n in NOMS), k
        return np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in NOMS])
    def evals(k):
        return float(np.mean([np.mean(ev[k][n]) for n in NOMS]))
    return ec, evals


def mde(d):
    return 2.8 * d.std(ddof=1) / np.sqrt(len(d))


def main():
    md = ["# 2e révision — D1, D3, D4 (analyse déclarée, PROTOCOLE § 3 septies)\n",
          f"{len(NOMS)} instances de test. Écart = C_max / recuit 50k − 1 (%). Différence = réseau − filtre (négatif : réseau meilleur).\n"]
    # ---------------- D1
    ec, evals = outils(BANQUE, 1.0)
    md += ["## D1 — filtres à budget égal (μ = 1)\n",
           "| Réglage réseau | Plannings réseau | Filtre (B') | Plannings filtre | Ratio | Écart réseau | Écart filtre |",
           "|---|---|---|---|---|---|---|"]
    rows = []
    for i, (B, K) in enumerate(RESEAU):
        kr = ("RL:imit-ft", f"faisceau={B},k={K}"); er, Er = ec(kr), evals(kr)
        for f, BK in D1.items():
            b, k = BK[i]; kf = (f"Faisceau:filtre-{f}", f"faisceau={b},k={k},filtre={f}")
            ef, Ef = ec(kf), evals(kf)
            rows.append(dict(r=(B, K), f=f, bf=(b, k), er=er, ef=ef, Er=Er, Ef=Ef))
            md.append(f"| {B}×{K} | {Er:.0f} | {f} ({b}×{k}) | {Ef:.0f} | {Ef / Er:.3f} | {er.mean():+.2f} % | {ef.mean():+.2f} % |")
    def bloc(titre, choix):
        sel = []
        for (B, K) in RESEAU:
            g = [x for x in rows if x["r"] == (B, K)]
            sel.append(choix(g))
        ds = [x["er"] - x["ef"] for x in sel]
        ps = [wilcoxon(x["er"], x["ef"]) for x in sel]
        ph = holm(ps)
        out = [f"\n### {titre}\n", "| Réglage | Filtre | Différence | IC 95 % | IC 90 % | V/E/D | p brut | p Holm (4) | effet min. détectable |",
               "|---|---|---|---|---|---|---|---|---|"]
        nsig = 0
        for x, d, p, q in zip(sel, ds, ps, ph):
            a, b = bootstrap_ic(d); c, e = ic90(d)
            nsig += (q < 0.05 and d.mean() < 0)
            out.append(f"| {x['r'][0]}×{x['r'][1]} | {x['f']} ({x['bf'][0]}×{x['bf'][1]}) | {d.mean():+.3f} | [{a:+.2f} ; {b:+.2f}] | "
                       f"[{c:+.2f} ; {e:+.2f}] | {int((d < -1e-9).sum())}/{int((abs(d) <= 1e-9).sum())}/{int((d > 1e-9).sum())} | "
                       f"{p:.3g} | {q:.3g} | {mde(d):.2f} |")
        D = np.mean(ds, axis=0); a, b = bootstrap_ic(D); pg = wilcoxon(D, np.zeros_like(D))
        out.append(f"\nTest global (moyenne par instance des 4 différences) : {D.mean():+.3f} point, IC 95 % [{a:+.2f} ; {b:+.2f}], "
                   f"Wilcoxon p = {pg:.3g}. Réglages significatifs (Holm sur 4) : {nsig}/4.")
        return out, nsig, pg, D.mean()
    o1, n1, p1, g1 = bloc("(a)+(b) Réseau contre le meilleur filtre à budget égal", lambda g: min(g, key=lambda x: x["ef"].mean()))
    o2, n2, p2, g2 = bloc("(c) Réseau contre le filtre a priori `regle` à budget égal", lambda g: [x for x in g if x["f"] == "regle"][0])
    md += o1 + o2
    verdict = ("apport significatif réglage par réglage" if n1 >= 3 else
               "gain faible mais constant" if p1 < 0.05 else "pas d'apport")
    md.append(f"\n**Verdict D1 (règle déclarée)** : (a) {n1}/4, (b) p = {p1:.3g} → **{verdict}**.\n")
    # ---------------- D3
    md.append("## D3 — facteur de seuil 0,7 et 1,5 (réseau non réentraîné)\n")
    for fs in (0.7, 1.5):
        ec3, ev3 = outils(BANQUE, fs)
        lignes, ds_best = [], []
        for B, K in [(5, 4), (50, 5)]:
            er = ec3(("RL:imit-ft", f"faisceau={B},k={K}"))
            fl = {f: ec3((f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}")) for f in ("regle", "borne")}
            for f, ef in fl.items():
                lignes.append(dict(r=(B, K), f=f, er=er, ef=ef, p=wilcoxon(er, ef)))
            best = min(fl, key=lambda f: fl[f].mean()); ds_best.append(er - fl[best])
        for x, q in zip(lignes, holm([x["p"] for x in lignes])):
            x["ph"] = q
        md += [f"\n### Facteur {fs:g}\n", "| Réglage | Filtre | Écart réseau | Écart filtre | Différence | IC 95 % | p Holm (4) |", "|---|---|---|---|---|---|---|"]
        ok = True
        for (B, K) in [(5, 4), (50, 5)]:
            g = [x for x in lignes if x["r"] == (B, K)]
            best = min(g, key=lambda x: x["ef"].mean())
            ok &= not (best["ph"] < 0.05 and (best["er"] - best["ef"]).mean() < 0)
            for x in g:
                d = x["er"] - x["ef"]; a, b = bootstrap_ic(d)
                md.append(f"| {B}×{K} | {x['f']}{' (meilleur)' if x is best else ''} | {x['er'].mean():+.2f} % | {x['ef'].mean():+.2f} % | "
                          f"{d.mean():+.2f} | [{a:+.2f} ; {b:+.2f}] | {x['ph']:.3g} |")
        e50 = ec3(("RL:imit-ft", "faisceau=50,k=5")); c, e = ic90(e50)
        D = np.mean(ds_best, axis=0); a, b = bootstrap_ic(D)
        md.append(f"\nVerdict (règle de R4) : la conclusion de R1 {'TIENT' if ok else 'NE TIENT PAS'}. "
                  f"TOST ±1 % du faisceau 50×5 : écart {e50.mean():+.2f} %, IC 90 % [{c:+.2f} ; {e:+.2f}] → "
                  f"{'équivalent' if -1 <= c and e <= 1 else 'non établi'}. Test global (2 réglages) : {D.mean():+.3f}, "
                  f"IC 95 % [{a:+.2f} ; {b:+.2f}], p = {wilcoxon(D, np.zeros_like(D)):.3g}.")
    # ---------------- D4
    TKLK = os.path.join(RACINE, "banque_resultats", "resultats_TkLk.csv")
    ec4, _ = outils(TKLK, 1.0, ref_banque=BANQUE, ref_fs=1000.0)
    ecC, _ = outils(BANQUE, 1000.0)
    md += ["\n## D4 — problème classique avec T_k = L_k (référence : recuit 50k du problème classique)\n",
           "| Méthode | T_k = L_k | × 1000 (rappel) |", "|---|---|---|"]
    for lab, k in [("Glouton", ("RL:imit-ft", "glouton")), ("100 tirages", ("RL:imit-ft", "echantillons=100")),
                   ("Faisceau 5×4", ("RL:imit-ft", "faisceau=5,k=4")), ("Faisceau 50×5", ("RL:imit-ft", "faisceau=50,k=5")),
                   ("Filtre regle 5×4", ("Faisceau:filtre-regle", "faisceau=5,k=4,filtre=regle")),
                   ("Filtre regle 50×5", ("Faisceau:filtre-regle", "faisceau=50,k=5,filtre=regle"))]:
        try:
            c = f"{ecC(k).mean():+.2f} %"
        except AssertionError:
            c = "—"
        md.append(f"| {lab} | {ec4(k).mean():+.2f} % | {c} |")
    g = ec4(("RL:imit-ft", "glouton")).mean()
    md.append(f"\n**Verdict D4 (règle déclarée)** : glouton {g:+.2f} % → " +
              ("effondrement à ×1000 attribué à l'échelle des features (10.7 / 11.3 à réécrire)" if g < 20 else
               "interprétation « hors distribution » conservée" if g >= 50 else "les deux causes à présenter"))
    open(os.path.join(ICI, "resultats", "revision_D1D3D4.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
