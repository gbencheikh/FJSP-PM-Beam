"""Figure de l'article C&IE (09/11/2026) : écart moyen au recuit Taguchi 50 000 en fonction du nombre de plannings
évalués, pour le faisceau guidé par la politique apprise, le recuit et la recherche tabou (un seul panneau).
Mêmes données et mêmes règles que figure_qualite_budget.py (127 instances, moyenne des graines par instance) ; les
filtres simples, le faisceau sans filtre et le réseau non entraîné sont exclus (article B et matériel supplémentaire).

  python -m experiences_article1.figure_qualite_budget_caie      # -> resultats/qualite_budget_caie.pdf|png|csv
"""
import csv, os, re, sys
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1.statistiques import charger, BANQUE, INSTANCES_REGLAGE, moyenne_instances   # noqa: E402
from metaheuristiques.instances import fichiers                                  # noqa: E402

REF = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")
FAM = ["Brandimarte", "HurinkLa", "Kacem"]
SERIES = [
    ("Policy-guided beam search", "#2a78d6", "o", lambda m, c: m == "RL:imit-ft" and re.fullmatch(r"faisceau=\d+,k=\d+", c)),
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
            e = float(re.search(r"evals=(\d+)", c).group(1)) if m in ("Recuit simulé", "Recherche tabou") \
                else moyenne_instances(ev[(m, c)], noms)
            points.append((lab, c, e, gap))
    base = os.path.join(ICI, "resultats", "qualite_budget_caie")
    with open(base + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["serie", "config", "plannings_evalues_moyens", "ecart_moyen_pct", "instances"])
        for p in sorted(points):
            w.writerow([p[0], p[1], round(p[2], 1), round(p[3], 3), len(noms)])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["pdf.fonttype"] = 42
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.axhline(0, color="#c3c2b7", lw=1, zorder=0)
    for lab, col, mk, _ in SERIES:
        pts = sorted((e, g, c) for l, c, e, g in points if l == lab)
        if not pts:
            continue
        if lab.startswith("Policy"):
            ligne = [(e, g) for e, g, c in pts if c.endswith(",k=4")]   # trait : réglages K = 4 ; autres K en marqueurs
            ax.plot(*zip(*ligne), color=col, lw=2, zorder=3)
            ax.scatter([p[0] for p in pts], [p[1] for p in pts], color=col, marker=mk, s=40, edgecolor="white",
                       linewidth=1.0, zorder=4, label=lab)
            for e, g, c in pts:
                if c in ("faisceau=5,k=4", "faisceau=50,k=5"):
                    B, K = re.findall(r"\d+", c)
                    ax.annotate(f"{B}×{K}", (e, g), textcoords="offset points", xytext=(0, -14), ha="center",
                                fontsize=8, color="#0b0b0b", zorder=6,
                                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
        else:
            es, gs = [p[0] for p in pts], [p[1] for p in pts]
            if len(pts) > 1:
                ax.plot(es, gs, color=col, lw=2, zorder=2)
            ax.scatter(es, gs, color=col, marker=mk, s=40, edgecolor="white", linewidth=1.5, zorder=4, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel("Complete schedules evaluated per instance (log scale)")
    ax.set_ylabel("Mean gap to tuned SA, 50k evaluations (%)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="#e8e7e2", lw=0.8)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print(f"{len(points)} points, {len(noms)} instances -> {base}.pdf|png|csv")


if __name__ == "__main__":
    main()
