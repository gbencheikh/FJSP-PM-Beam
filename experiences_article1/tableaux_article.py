"""Tableaux LaTeX de l'article 1 produits à partir des fichiers de résultats (22/10/2026).

Ne recalcule rien : met en forme les sorties des scripts d'analyse déjà exécutés.
  tab_budget.tex      <- resultats/tests_qualite_budget.csv      (tests par budget en évaluations, Holm sur 14 tests)
  tab_temps.tex       <- resultats/tests_qualite_temps.md         (E10, 54 instances) et tests_qualite_temps_E10b.md (36)
  tab_cpsat.tex       <- resultats/e9b.csv                       (CP-SAT seul contre le faisceau, budgets appariés, Holm par groupe)
  tab_song.tex        <- resultats/e10s_song_temps.csv           (Song et al. au même temps mur, un cœur, Holm sur 3 tests)
  tab_maintenance.tex <- resultats/e15.md                         (placement des maintenances, séquences du faisceau 5x4)

  python -m experiences_article1.tableaux_article [--resultats DOSSIER]
"""
import argparse, csv, os, re

TIMES = '$\\times$'   # hors des f-strings (compatibilité Python < 3.12)

ICI = os.path.dirname(os.path.abspath(__file__))


def pval(p):
    p = float(p)
    if p >= 0.01:
        from decimal import Decimal, ROUND_HALF_UP
        return "1" if p >= 0.995 else str(Decimal(str(p)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    m, e = f"{p:.1e}".split("e")
    return f"${m} \\times 10^{{{int(e)}}}$"


def lignes_md(chemin, entete):
    """Lignes du premier tableau markdown dont l'en-tête commence par `entete`."""
    out, dedans = [], False
    for l in open(chemin, encoding="utf8"):
        l = l.strip()
        if l.startswith("| " + entete):
            dedans = True
            continue
        if dedans:
            if not l.startswith("|"):
                break
            if set(l.replace("|", "").strip()) <= set("-: "):
                continue
            out.append([c.strip() for c in l.strip("|").split("|")])
    return out


def pct(s):
    return s.replace("%", "").replace(" ", "").replace("nettement", "")


def tab_budget(R):
    rows = list(csv.DictReader(open(os.path.join(R, "tests_qualite_budget.csv"), encoding="utf8")))
    t = ["% Produit par experiences_article1/tableaux_article.py — source : resultats/tests_qualite_budget.csv",
         "\\begin{tabular}{llrrrrrr}", "\\toprule",
         "Method & Budget & Beam (evaluations) & Gap beam & Gap method & Difference & W/T/L & $p_{\\mathrm{Holm}}$ \\\\",
         "\\midrule"]
    nom = {"SA": "SA", "TS": "TS"}
    for i, r in enumerate(rows):
        if i == 7:
            t.append("\\midrule")
        t.append(f"{nom[r['metaheuristique']]} & {int(r['budget']):,} & {r['faisceau'].replace('×', TIMES)} "
                 f"({int(r['plannings_faisceau']):,}) & {float(r['ecart_faisceau_pct']):+.2f} & "
                 f"{float(r['ecart_mh_pct']):+.2f} & {float(r['diff_pct']):+.2f} & {r['V']}/{r['E']}/{r['D']} & "
                 f"{pval(r['p_holm'])} \\\\".replace(",", "\\,"))
    t += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(t)


def tab_temps(R):
    t = ["% Produit par experiences_article1/tableaux_article.py — sources : resultats/tests_qualite_temps.md (E10, 54 instances),",
         "% resultats/tests_qualite_temps_E10b.md (E10b, 36 instances) ; Holm sur 12 tests par sous-ensemble",
         "\\begin{tabular}{llrrrrrr}", "\\toprule",
         "Method & Budget (s) & Beam (mean time, s) & Gap beam & Gap method & Difference & W/T/L & $p_{\\mathrm{Holm}}$ \\\\"]
    for f, titre in (("tests_qualite_temps.md", "Brandimarte, Kacem, Hurink vdata (54 instances)"),
                     ("tests_qualite_temps_E10b.md", "Hurink edata and rdata (36 instances)")):
        t += ["\\midrule", f"\\multicolumn{{8}}{{l}}{{\\emph{{{titre}}}}} \\\\"]
        for c in lignes_md(os.path.join(R, f), "Méta."):
            meta, b, fa, ef, em, d, ic, ved, p = c
            m = re.match(r"(\S+) \(([\d.]+) s\)", fa)
            t.append(f"{meta} & {b} & {m.group(1).replace('×', TIMES)} ({m.group(2)}) & {pct(ef)} & {pct(em)} & "
                     f"{pct(d)} & {ved} & {pval(p)} \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(t)


def tab_maintenance(R):
    src = open(os.path.join(R, "e15.md"), encoding="utf8").read()
    bloc = src.split("## Source : RL:imit-ft|faisceau=5,k=4")[1]
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".md")          # fichier temporaire hors du dépôt
    os.close(fd)
    open(tmp, "w", encoding="utf8").write(bloc)
    rows = lignes_md(tmp, "Politique")
    os.remove(tmp)
    trad = {"Au plus tard (référence)": "Latest (reference)", "Au plus tôt": "Earliest", "Systématique": "Before every operation",
            "Source": "Beam search $5 \\times 4$", "Aléatoire (moyenne)": "Random (mean of 100)",
            "Aléatoire (meilleur des tirages)": "Random (best of 100)",
            "Recuit placement (moyenne des graines)": "SA on positions (mean of 5 seeds)",
            "Recuit placement (meilleure graine)": "SA on positions (best seed)"}
    t = ["% Produit par experiences_article1/tableaux_article.py — source : resultats/e15.md (séquences du faisceau 5x4, 127 instances)",
         "\\begin{tabular}{lrrrrrr}", "\\toprule",
         "Placement & Gap & 95\\% CI & W/T/L & $p_{\\mathrm{Holm}}$ & Maint./inst. & Wear ratio \\\\", "\\midrule"]
    for c in rows:
        pol, ec, ic, med, ved, p, nm, tm, us = c
        if pol.startswith("Au plus tard"):
            t.append(f"{trad[pol]} & 0 & & & & {nm} & {us} \\\\")
            continue
        ic2 = ic.replace("%", "").replace(" ", "").replace(";", ", ")
        t.append(f"{trad[pol]} & {pct(ec)} & {ic2} & {ved} & {pval(p)} & {nm} & {us} \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(t)


def tab_cpsat(R):
    rows = list(csv.DictReader(open(os.path.join(R, "e9b.csv"), encoding="utf8")))
    t = ["% Produit par experiences_article1/tableaux_article.py — source : resultats/e9b.csv (127 instances ;",
         "% échec = défaite de CP-SAT ; écart sur les instances résolues ; Holm par groupe de 3 tests)",
         "\\begin{tabular}{lrrrrrr}", "\\toprule",
         "Beam setting & Time (s) & Threads & Unsolved & Gap of CP-SAT (\\%) & W/T/L of CP-SAT & $p_{\\mathrm{Holm}}$ \\\\",
         "\\midrule"]
    for i, r in enumerate(rows):
        if i == 3:
            t.append("\\midrule")
        t.append(f"{r['faisceau'].replace('x', TIMES)} & {r['budget_s']} & {r['fils']} & {r['echecs']} & "
                 f"{float(r['ecart_moyen']):+.1f} & {r['V_cpsat']}/{r['E']}/{r['D_cpsat']} & {pval(r['p_holm'])} \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(t)


def tab_song(R):
    rows = list(csv.DictReader(open(os.path.join(R, "e10s_song_temps.csv"), encoding="utf8")))
    t = ["% Produit par experiences_article1/tableaux_article.py — source : resultats/e10s_song_temps.csv",
         "% (FJSP classique, 50 instances Brandimarte + Hurink vdata ; écart = faisceau / Song - 1 ; Holm sur 3 tests)",
         "\\begin{tabular}{lrrrrr}", "\\toprule",
         "Beam setting & Gap beam vs Song (\\%) & W/T/L of the beam & $p_{\\mathrm{Holm}}$ & "
         "Samples of Song (median) & Overrun of Song, median / max (s) \\\\", "\\midrule"]
    for r in rows:
        t.append(f"{r['reglage'].replace('x', TIMES)} & {float(r['ecart_moyen']):+.2f} & {r['V']}/{r['E']}/{r['D']} & "
                 f"{pval(r['p_holm'])} & {r['tirages_song_median']} & "
                 f"{float(r['depassement_median_s']):.1f} / {float(r['depassement_max_s']):.1f} \\\\")
    t += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resultats", default=os.path.join(ICI, "resultats"))
    ap.add_argument("--sortie", default=None)
    a = ap.parse_args()
    S = a.sortie or a.resultats
    for nom, f in (("tab_budget", tab_budget), ("tab_temps", tab_temps), ("tab_cpsat", tab_cpsat), ("tab_song", tab_song),
                   ("tab_maintenance", tab_maintenance)):
        open(os.path.join(S, nom + ".tex"), "w", encoding="utf8").write(f(a.resultats) + "\n")
        print("ok", nom)


if __name__ == "__main__":
    main()
