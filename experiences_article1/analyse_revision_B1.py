"""Analyse DÉCLARÉE de B1 (PROTOCOLE, entrée du 04/11/2026) : ablation du départage des ex aequo (relecteur indépendant, M4).

Réglages 5×4 et 50×5, 127 instances, référence recuit 50k. Variantes : réseau départagé par l'ordre de génération
(« departage=ordre ») ; filtres simples départagés par leur rang cumulé (« departage=rang »).
(a) réseau-ordre contre le meilleur filtre simple de l'article (départage par ordre) ; (b) réseau de l'article contre le
meilleur filtre simple départagé par rang ; (c) réseau de l'article contre réseau-ordre. Pour (a) et (b) : différences par
réglage (Holm sur 2) et test groupé (moyenne par instance des 2 différences, Wilcoxon ; IC bootstrap simple et par grappes
la01–la40). Règle : le gain du filtre appris est attribué à son rôle de FILTRE si (a) donne un test groupé négatif et
significatif (p < 0,05) ; sinon il est attribué, au moins en partie, au départage. Fréquence des ex aequo à la coupure :
lue dans journaux/B1.log.
  python -m experiences_article1.analyse_revision_B1 -> resultats/revision_B1.md
"""
import os, re, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import charger, wilcoxon, holm, bootstrap_ic, INSTANCES_REGLAGE, BANQUE  # noqa
from metaheuristiques.instances import fichiers  # noqa

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
R = [(5, 4), (50, 5)]


def main():
    noms = [n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte", "HurinkLa", "Kacem"]))
            if n not in INSTANCES_REGLAGE]
    G = [("la", int(m.group(1))) if (m := re.match(r"Hurink[EVR]data(\d+)", n)) else n for n in noms]
    grappes = [[i for i, g in enumerate(G) if g == u] for u in dict.fromkeys(G)]
    v = charger(BANQUE, "A", 1.0)[0]
    ref = {n: np.mean(v[REF][n]) for n in noms}
    ec = lambda k: np.array([100 * (np.mean(v[k][n]) / ref[n] - 1) for n in noms])
    def ic_grappes(d, n=10000):
        r = np.random.default_rng(0); m = [d[np.concatenate([grappes[j] for j in r.integers(0, len(grappes), len(grappes))])].mean() for _ in range(n)]
        return np.percentile(m, 2.5), np.percentile(m, 97.5)
    def best(B, K, suf):
        c = {f: ec((f"Faisceau:filtre-{f}", f"faisceau={B},k={K},filtre={f}{suf}")) for f in ("regle", "fin", "borne")}
        f = min(c, key=lambda x: c[x].mean()); return f, c[f]
    md = ["# B1 — ablation du départage des ex aequo (analyse déclarée)\n", f"{len(noms)} instances ; écart au recuit 50k (%).\n",
          "| Réglage | Réseau (article) | Réseau, départage par ordre | Meilleur filtre (ordre) | Meilleur filtre (rang) |", "|---|---|---|---|---|"]
    A, Bc, C = [], [], []
    for B, K in R:
        en = ec(("RL:imit-ft", f"faisceau={B},k={K}")); eo = ec(("RL:imit-ft", f"faisceau={B},k={K},departage=ordre"))
        f1, e1 = best(B, K, ""); f2, e2 = best(B, K, ",departage=rang")
        md.append(f"| {B}×{K} | {en.mean():+.2f} % | {eo.mean():+.2f} % | {f1} {e1.mean():+.2f} % | {f2} {e2.mean():+.2f} % |")
        A.append(eo - e1); Bc.append(en - e2); C.append(en - eo)
    verdict = None
    for titre, ds in (("(a) réseau départagé par ordre − meilleur filtre (ordre)", A),
                      ("(b) réseau (article) − meilleur filtre départagé par rang", Bc),
                      ("(c) réseau (article) − réseau départagé par ordre", C)):
        ph = holm([wilcoxon(d, np.zeros_like(d)) for d in ds])
        D = np.mean(ds, axis=0); lo, hi = bootstrap_ic(D); glo, ghi = ic_grappes(D); p = wilcoxon(D, np.zeros_like(D))
        md += [f"\n## {titre}\n", "| Réglage | Différence | p Holm (2) |", "|---|---|---|"]
        md += [f"| {B}×{K} | {d.mean():+.3f} | {q:.3g} |" for (B, K), d, q in zip(R, ds, ph)]
        md.append(f"\nTest groupé : {D.mean():+.3f} point, IC 95 % [{lo:+.2f} ; {hi:+.2f}], par grappes [{glo:+.2f} ; {ghi:+.2f}], p = {p:.3g}.")
        if titre.startswith("(a)"):
            verdict = D.mean() < 0 and p < 0.05
    log = os.path.join(ICI, "journaux", "B1.log")
    if os.path.exists(log):
        eg = re.findall(r"ex aequo à la coupure (\d+)/(\d+)", open(log, encoding="utf-8", errors="ignore").read())
        if eg:
            a, b = sum(int(x) for x, _ in eg), sum(int(y) for _, y in eg)
            md.append(f"\nEx aequo sur H à la coupure (B-ième et (B+1)-ième enfants), toutes variantes de B1 : {a}/{b} = {100 * a / max(b, 1):.1f} %.")
    md.append("\n**Verdict (règle déclarée)** : " + ("le gain du filtre appris tient sans le départage → attribué à son rôle de filtre."
                                                    if verdict else "sans le départage, le gain n'est plus établi → attribué, au moins en partie, au départage."))
    open(os.path.join(ICI, "resultats", "revision_B1.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
