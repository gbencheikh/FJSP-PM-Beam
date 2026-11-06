"""Figure : qualité (écart moyen au recuit Taguchi 50 000) en fonction du nombre de plannings évalués.

Lue entièrement dans la banque (mêmes règles que statistiques.py : 127 instances, réglage Taguchi exclu,
moyenne des graines par instance). Séries :
  - faisceau guidé par la politique apprise (grille E5),
  - faisceau sans réseau (règle seule, E6),
  - faisceau guidé par un réseau non entraîné (E6),
  - faisceau guidé par les trois filtres simples (R1, ajouté le 02/11/2026 ; panneau (b) : zoom sur la zone des faisceaux),
  - recuit et tabou (point à 50 000 évaluations, E2 ; courbe complète quand E3 est dans la banque).
Une série n'apparaît que si toutes ses instances sont présentes. Axe : plannings COMPLETS évalués ; le coût
d'inférence du réseau n'est pas compté (à dire dans la légende de la figure ; comparaison en temps : E10).

  python -m experiences_article1.figure_qualite_budget            # -> resultats/qualite_budget.pdf|png|csv
"""
import csv, os, re, sys
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import charger, BANQUE, INSTANCES_REGLAGE, moyenne_instances   # noqa: E402
from metaheuristiques.instances import fichiers                                  # noqa: E402

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
FAM = ["Brandimarte", "HurinkLa", "Kacem"]
# couleurs : palette catégorielle de référence (validée : scripts/validate_palette.js, mode clair)
SERIES = [
    ("Policy-guided beam", "#2a78d6", "o", lambda m, c: m == "RL:imit-ft" and re.fullmatch(r"faisceau=\d+,k=\d+", c)),
    ("Rule-only beam (no network)", "#eb6834", "s", lambda m, c: m == "Faisceau:regle" and re.fullmatch(r"faisceau=\d+,k=0", c)),
    ("Untrained-network beam", "#1baf7a", "^", lambda m, c: m == "RL:aleatoire-g0" and re.fullmatch(r"faisceau=\d+,k=\d+", c)),
    ("Priority-rule filter", "#eda100", "P", lambda m, c: m == "Faisceau:filtre-regle"),
    ("Earliest-finish filter", "#e87ba4", "X", lambda m, c: m == "Faisceau:filtre-fin"),
    ("Lower-bound filter", "#008300", "d", lambda m, c: m == "Faisceau:filtre-borne"),
    ("Simulated annealing", "#52514e", "D", lambda m, c: m == "Recuit simulé" and re.fullmatch(r"evals=\d+,depart=heuristique,params=taguchi", c)),
    ("Tabu search", "#8a8984", "v", lambda m, c: m == "Recherche tabou" and re.fullmatch(r"evals=\d+,depart=heuristique,params=taguchi", c)),
]


def main():
    v, t, ev = charger(BANQUE, "A", 1.0)
    noms = [os.path.splitext(os.path.basename(f))[0] for f in fichiers(FAM)]
    noms = [n for n in noms if n not in INSTANCES_REGLAGE]
    ref = np.array([np.mean(v[REF][n]) for n in noms])
    points = []
    for lab, col, mk, filtre in SERIES:
        for (m, c), d in v.items():
            if not filtre(m, c) or not all(n in d for n in noms):
                continue
            x = np.array([np.mean(d[n]) for n in noms])
            gap = 100 * np.mean(x / ref - 1)
            if m in ("Recuit simulé", "Recherche tabou"):
                e = float(re.search(r"evals=(\d+)", c).group(1))
            else:
                e = moyenne_instances(ev[(m, c)], noms)
            points.append((lab, c, e, gap))
    os.makedirs(os.path.join(ICI, "resultats"), exist_ok=True)
    base = os.path.join(ICI, "resultats", "qualite_budget")
    with open(base + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["serie", "config", "plannings_evalues_moyens", "ecart_moyen_pct", "instances"])
        for p in sorted(points):
            w.writerow([p[0], p[1], round(p[2], 1), round(p[3], 3), len(noms)])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["axes.unicode_minus"] = False   # signe moins visible dans le PDF (2e relecture, Figure 9b)
    plt.rcParams["pdf.fonttype"] = 42
    FILTRES = ("Priority-rule filter", "Earliest-finish filter", "Lower-bound filter")
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))
    for i, ax in enumerate(axes):
        zoom = i == 1
        ax.axhline(0, color="#c3c2b7", lw=1, zorder=0)
        for lab, col, mk, _ in SERIES:
            if zoom and lab in ("Rule-only beam (no network)", "Untrained-network beam"):
                continue
            pts = sorted((e, g, c) for l, c, e, g in points if l == lab)
            if not pts:
                continue
            ls = "--" if lab in FILTRES else "-"
            R1 = ("faisceau=5,k=4", "faisceau=10,k=4", "faisceau=20,k=4", "faisceau=50,k=5")
            if zoom and lab == "Policy-guided beam":   # (b) : mêmes 4 réglages que les filtres (R1)
                pts = [p for p in pts if p[2] in R1]
            if lab == "Policy-guided beam" or lab in FILTRES:   # trait : K = 4 et 50x5 ; autres K en marqueurs seuls
                ligne = [(e, g) for e, g, c in pts if ",k=4" in c or "faisceau=50,k=5" in c]
                if lab == "Policy-guided beam" and not zoom:
                    ligne = [(e, g) for e, g, c in pts if c.endswith(",k=4")]
                ax.plot(*zip(*ligne), color=col, lw=2, ls=ls, zorder=3)
                ax.scatter([e for e, g, c in pts], [g for e, g, c in pts], color=col, marker=mk,
                           s=60 if mk in "PXd" else 40, edgecolor="white", linewidth=1.0, zorder=4, label=lab)
                if lab == "Policy-guided beam":
                    for e, g, c in pts:
                        if c in ("faisceau=5,k=4", "faisceau=50,k=5"):
                            B, K = re.findall(r"\d+", c)
                            ax.annotate(f"{B}×{K}", (e, g), textcoords="offset points", xytext=(0, -14),
                                        ha="center", fontsize=8, color="#0b0b0b", zorder=6,
                                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
            else:
                es, gs = [p[0] for p in pts], [p[1] for p in pts]
                if len(pts) > 1:
                    ax.plot(es, gs, color=col, lw=2, zorder=2)
                ax.scatter(es, gs, color=col, marker=mk, s=40, edgecolor="white", linewidth=1.5, zorder=4, label=lab)
        ax.set_xscale("log")
        ax.set_xlabel("Complete schedules evaluated per instance (log scale)")   # inférence du filtre non comptée
        if zoom:
            ax.set_xlim(2000, 60000)
            ax.set_ylim(-0.4, 1.8)
            ax.set_title("(b) Beam settings 5×4, 10×4, 20×4, 50×5: learned and simple filters", fontsize=9, loc="left")
        else:
            ax.set_ylabel("Mean gap to tuned SA, 50k evaluations (%)")
            ax.set_title("(a) All methods", fontsize=9, loc="left")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.grid(axis="y", color="#e8e7e2", lw=0.8)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=8, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print(f"{len(points)} points, {len(noms)} instances -> {base}.pdf|png|csv")


if __name__ == "__main__":
    main()
