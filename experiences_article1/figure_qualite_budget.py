"""Figure : qualité (écart moyen au recuit Taguchi 50 000) en fonction du nombre de plannings évalués.

Lue entièrement dans la banque (mêmes règles que statistiques.py : 127 instances, réglage Taguchi exclu,
moyenne des graines par instance). Séries :
  - faisceau guidé par la politique apprise (grille E5),
  - faisceau sans réseau (règle seule, E6),
  - faisceau guidé par un réseau non entraîné (E6),
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
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.axhline(0, color="#c3c2b7", lw=1, zorder=0)
    for lab, col, mk, _ in SERIES:
        pts = sorted((e, g, c) for l, c, e, g in points if l == lab)
        if not pts:
            continue
        if lab == "Policy-guided beam":          # trait : configurations K = 4 ; autres K en marqueurs seuls
            k4 = [(e, g) for e, g, c in pts if c.endswith(",k=4")]
            ax.plot(*zip(*k4), color=col, lw=2, zorder=3)
            ax.scatter([e for e, g, c in pts], [g for e, g, c in pts], color=col, marker=mk, s=40,
                       edgecolor="white", linewidth=1.5, zorder=4, label=lab)
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
    ax.set_xlabel("Complete schedules evaluated per instance (log scale)")   # inférence du réseau non comptée
    ax.set_ylabel("Mean gap to tuned SA, 50k evaluations (%)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e8e7e2", lw=0.8)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print(f"{len(points)} points, {len(noms)} instances -> {base}.pdf|png|csv")


if __name__ == "__main__":
    main()
