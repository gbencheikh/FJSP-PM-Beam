"""Table S6 du matériel supplémentaire : règles déclarées, résultats et décisions (rapport v7, point N4).

Les valeurs ne sont pas recalculées : elles sont reprises des rapports d'analyse déclarée (resultats/revision_*.md) et
du journal (PROTOCOLE.md). Pour chaque ligne, le script VÉRIFIE que les chaînes citées figurent textuellement dans le
fichier source ; il s'arrête sinon. Sortie : resultats/tab_decisions.tex.

Usage (depuis jssp_pm/jssp_pm) : python -m experiences_article1.tableau_decisions
"""
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ICI, "resultats")
SORTIE = os.path.join(RES, "tab_decisions.tex")


def src(nom):
    return os.path.join(ICI, nom) if nom == "PROTOCOLE.md" else os.path.join(RES, nom)


# (campagne, question, règle, résultat, décision, [(fichier, chaîne attendue), ...])
DECLAREES = [
    ("R1", "Does the learned filter add to the search?",
     "Network significantly better than the best simple filter (Holm, 12 tests) at $\\geq 3$ of 4 settings",
     "0/4 ($p_{\\mathrm{Holm}} \\geq 0.12$)",
     "Not met: contribution reformulated",
     [("revision_R1R2.md", "0/4 réglages"), ("revision_R1R2.md", "p Holm 0.12")]),
    ("R1", "Beam $50 \\times 5$ against SA 50k",
     "Equivalence if the 90\\,\\% CI of the mean gap lies within $\\pm 1\\,\\%$",
     "$[-0.53, +0.62]\\,\\%$",
     "Equivalent (on average)",
     [("PROTOCOLE.md", "[−0,53 ; +0,62]")]),
    ("R2", "Imitation alone against the final network",
     "No decision rule; Holm over 6 tests reported",
     "Greedy $-23.15$ points; beam $5 \\times 4$ and $10 \\times 4$ significant, $20 \\times 4$ and $50 \\times 5$ not",
     "Reported as such",
     [("revision_R1R2.md", "-23.15"), ("PROTOCOLE.md", "p 0,0036")]),
    ("R4", "Longer maintenances ($\\mu = 3$)",
     "Conclusion of R1 holds if no setting significant against the best of two filters (Holm, 4 tests)",
     "None significant ($p_{\\mathrm{Holm}} \\geq 0.09$); TOST $[-0.87, +0.66]\\,\\%$",
     "R1 holds; equivalent",
     [("revision_R4.md", "le verdict de R1 tient"), ("revision_R4.md", "[-0.87 ; +0.66]"),
      ("revision_R4.md", "| 0.09 |")]),
    ("D1", "Equal budget",
     "(a) $\\geq 3/4$ settings significant (Holm, 4): gain at each setting; (b) only the pooled test: small but consistent",
     "(a) 0/4; (b) $-0.23$ points, $p = 0.025$",
     "Small but consistent gain",
     [("revision_D1D3D4.md", "-0.232 point"), ("revision_D1D3D4.md", "p = 0.0251"),
      ("revision_D1D3D4.md", "(a) 0/4")]),
    ("D3", "Threshold factor 0.7",
     "Rule of R4; TOST $\\pm 1\\,\\%$",
     "None significant; $+0.11\\,\\%$, $[-0.55, +0.76]\\,\\%$",
     "R1 holds; equivalent",
     [("revision_D1D3D4.md", "+0.11 %, IC 90 % [-0.55 ; +0.76]")]),
    ("D3", "Threshold factor 1.5",
     "Rule of R4; TOST $\\pm 1\\,\\%$",
     "None significant; $+0.14\\,\\%$, $[-0.39, +0.66]\\,\\%$",
     "R1 holds; equivalent",
     [("revision_D1D3D4.md", "+0.14 %, IC 90 % [-0.39 ; +0.66]")]),
    ("D4", "Classical problem, $T_k = L_k$",
     "Greedy gap $< 20\\,\\%$: feature scale; $\\geq 50\\,\\%$: change of problem",
     "Greedy $+7.63\\,\\%$",
     "Collapse attributed to the feature scale",
     [("revision_D1D3D4.md", "glouton +7.63 %")]),
    ("D5", "Filter trained for the search",
     "Retrained network retained if better on validation; then pooled test against the final network",
     "No epoch better; difference 0",
     "Conclusions restricted (title)",
     [("revision_D5.md", "Test global : +0.000 point")]),
    ("A1", "Active decoder for SA and TS",
     "Reference weakened by its decoder if SA active better by $> 1$ point with $p_{\\mathrm{Holm}} < 0.05$",
     "$+0.42$ points ($p_{\\mathrm{Holm}} = 1$)",
     "Decoder does not explain the gap",
     [("revision_A1.md", "+0.42 point (p Holm 1)")]),
    ("B1", "Tie-breaking",
     "Gain due to filtering if network (ties by order) $-$ best filter is negative and significant (pooled)",
     "$+0.13$ points, $p = 0.69$",
     "Gain attributed to tie-breaking",
     [("revision_B1.md", "+0.128 point"), ("revision_B1.md", "p = 0.691")]),
    ("B2", "Draw of $\\varphi_k$, seed 1",
     "Rule of R4; TOST $\\pm 1\\,\\%$",
     "Significant at both settings ($p_{\\mathrm{Holm}} = 0.015$, $0.025$); $[-0.84, +0.27]\\,\\%$",
     "R1 does not hold; equivalent",
     [("revision_B2.md", "NE TIENT PAS"), ("revision_B2.md", "0.0152"), ("revision_B2.md", "0.0249"),
      ("revision_B2.md", "[-0.84 ; +0.27]")]),
    ("B2", "Draw of $\\varphi_k$, seed 2",
     "Rule of R4; TOST $\\pm 1\\,\\%$",
     "None significant; $[-0.87, +0.22]\\,\\%$",
     "R1 holds; equivalent",
     [("revision_B2.md", "Conclusion de R1 : TIENT"), ("revision_B2.md", "[-0.87 ; +0.22]")]),
    ("B3", "Song et al., edata and rdata",
     "Rule of the comparison at equal time (Holm, 3 tests)",
     "Beam better by 0.60, 0.78, 1.92\\,\\% ($p_{\\mathrm{Holm}} = 0.062$, $0.016$, $1.2 \\times 10^{-5}$)",
     "Beam better at two of three settings",
     [("revision_B3.md", "0.0621"), ("revision_B3.md", "0.0163"), ("revision_B3.md", "1.19e-05")]),
]

EXPLORATOIRES = [
    ("Pooled test, equal settings, $\\mu = 1$ (R1)", "$-0.27$ points, $p = 0.0024$",
     [("tab_gain_global.tex", "0.0024")]),
    ("Pooled test, equal settings, $\\mu = 3$ (R4)", "$-0.34$ points, $p = 0.032$",
     [("tab_gain_global.tex", "0.032")]),
    ("Holm over the five pooled tests", "Only R1 below 0.05 ($p = 0.012$)",
     [("PROTOCOLE.md", "0,012 ; 0,10")]),
    ("Pooled test at equal budget over clusters (D1)", "$p = 0.033$", [("PROTOCOLE.md", "p = 0,033")]),
    ("Pooled test at equal budget without Kacem (D1)", "$-0.09$ points, $p = 0.09$", [("PROTOCOLE.md", "p = 0,091")]),
    ("Tie-breaking without Kacem (B1)", "Network $-$ filters by rank $p = 0.042$; network $-$ network by order $p = 0.0095$",
     [("PROTOCOLE.md", "p = 0,042"), ("PROTOCOLE.md", "p = 0,0095")]),
    ("Computing time of the filters (D2)", "No decision rule; network better at 5\\,s only on flexible instances",
     [("PROTOCOLE.md", "p Holm 0,026")]),
]


def verifier(lignes):
    cache = {}
    for ligne in lignes:
        for f, s in ligne[-1]:
            if f not in cache:
                cache[f] = open(src(f), encoding="utf-8").read()
            if s not in cache[f]:
                sys.exit(f"ÉCHEC : « {s} » absent de {f} (ligne {ligne[0]})")


def main():
    verifier(DECLAREES)
    verifier(EXPLORATOIRES)
    out = ["% Généré par experiences_article1/tableau_decisions.py — ne pas modifier à la main.",
           "% Valeurs vérifiées contre resultats/revision_*.md, tab_gain_global.tex et PROTOCOLE.md.",
           "\\begin{tabular}{@{}l>{\\raggedright\\arraybackslash}p{3.0cm}>{\\raggedright\\arraybackslash}p{4.2cm}"
           ">{\\raggedright\\arraybackslash}p{3.6cm}>{\\raggedright\\arraybackslash}p{2.6cm}@{}}", "\\toprule",
           "Campaign & Question & Declared rule & Outcome & Decision \\\\", "\\midrule"]
    for c, q, r, o, d, _ in DECLAREES:
        out.append(f"{c} & {q} & {r} & {o} & {d} \\\\")
    out += ["\\midrule",
            "\\multicolumn{5}{@{}l}{\\emph{Analyses computed afterwards (not declared, no decision attached)}} \\\\"]
    for q, o, _ in EXPLORATOIRES:
        out.append(f"-- & \\multicolumn{{2}}{{>{{\\raggedright\\arraybackslash}}p{{7.4cm}}}}{{{q}}} & \\multicolumn{{2}}{{>{{\\raggedright\\arraybackslash}}p{{6.4cm}}}}{{{o}}} \\\\")
    out += ["\\bottomrule", "\\end{tabular}", ""]
    open(SORTIE, "w", encoding="utf-8").write("\n".join(out))
    print(f"{len(DECLAREES)} règles déclarées et {len(EXPLORATOIRES)} analyses exploratoires vérifiées -> {SORTIE}")


if __name__ == "__main__":
    main()
