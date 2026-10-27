"""Animation (GIF) de la construction d'un planning, décision après décision, pour le README du dépôt.

Le planning est celui de la politique + faisceau 50 x 5, calculé par figure_gantt_resultats.py et lu dans
resultats/gantt_resultats_<instance>.json (lancer d'abord ce script). Le processus de décision avance dans le
temps : les décisions du planning retenu sont donc rejouées dans l'ordre des dates de début (une image par
lancement d'opération ou de maintenance). À droite : usure cumulée c_k de chaque machine rapportée à son seuil T_k
(remise à zéro par la maintenance).

  python -m experiences_article1.figure_gantt_resultats
  python -m experiences_article1.animation_gantt [--instance BrandimarteMk1] [--sortie docs/beam_search_mk01.gif]
"""
import argparse, json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF        # noqa: E402

PROC, PM = SF.PROC, SF.PM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default="BrandimarteMk1")
    ap.add_argument("--panneau", default="(b)", help="préfixe du planning dans le .json : (a), (b), (c) ou (d)")
    ap.add_argument("--sortie", default=None)
    ap.add_argument("--ms", type=int, default=170, help="durée d'une image (ms)")
    a = ap.parse_args()
    d = json.load(open(os.path.join(ICI, "resultats", f"gantt_resultats_{a.instance}.json"), encoding="utf-8"))
    titre_src, P = [(k, v) for k, v in d["plannings"].items() if k.startswith(a.panneau)][0]
    T, m = d["T"], len(d["T"])
    segs = sorted([tuple(s) for s in P["segments"]], key=lambda s: (s[1], s[3], s[0]))
    cmax = max(s[2] for s in segs if s[3] == PROC)
    segs = [s for s in segs if not (s[3] == PM and s[1] >= cmax)]          # maintenances finales inutiles
    opt = [v["cmax"] for k, v in d["plannings"].items() if k.startswith("(d)")]
    sortie = a.sortie or os.path.join(ICI, "resultats", f"animation_{a.instance}.gif")

    SF.style()
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Patch
    fig = plt.figure(figsize=(8.0, 3.0), dpi=100)
    gs = fig.add_gridspec(1, 2, width_ratios=[5.2, 1.0], wspace=0.08)
    ax, au = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    xmax = cmax + 2

    def dessiner(n):
        ax.clear(); au.clear()
        faits = segs[:n]
        t = faits[-1][1] if faits else 0.0
        for i, (k, x, y, ty, j) in enumerate(faits):
            dernier = (i == n - 1) and n < len(segs)          # contour noir : décision qui vient d'être prise
            if ty == PM:
                ax.barh(k, y - x, left=x, height=0.62, color=SF.GRIS_PM, edgecolor=SF.ENCRE if dernier else SF.SURFACE,
                        linewidth=1.6 if dernier else 1.0, hatch="////", zorder=2)
            else:
                ax.barh(k, y - x, left=x, height=0.62, color=SF.CATEGORIELLE[0],
                        edgecolor=SF.ENCRE if dernier else SF.SURFACE, linewidth=1.6 if dernier else 1.0, zorder=2)
                ax.text((x + y) / 2, k, str(j + 1), ha="center", va="center", color=SF.SURFACE,
                        fontsize=SF.TAILLE - 1 if y - x >= 1.5 else SF.TAILLE - 3.5, zorder=3)
        fini = n == len(segs)
        if not fini:
            ax.axvline(t, color=SF.CATEGORIELLE[1], lw=1.2, zorder=4)
        else:
            ax.axvline(cmax, color=SF.ENCRE_2, lw=0.9, ls=(0, (3, 2)), zorder=1)
        ax.set_xlim(0, xmax); ax.set_ylim(m - 0.5, -0.6)
        ax.set_yticks(range(m)); ax.set_yticklabels([f"M{k + 1}" for k in range(m)])
        ax.set_xlabel("Time")
        ax.grid(axis="x", color="#e6e5e0", lw=0.6, zorder=0); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        if fini:
            txt = f"$C_{{\\max}}$ = {cmax:g}" + (f"   (proven optimum: {opt[0]:g})" if opt else "")
        else:
            txt = f"decision {n}/{len(segs)},  t = {t:g}"
        ax.set_title(f"{a.instance}, policy-guided beam search 50 $\\times$ 5:  {txt}", loc="left",
                     fontsize=SF.TAILLE + 1, color=SF.ENCRE)
        # usure au moment de la dernière décision (lancements déjà décidés comptés, comme dans le MDP)
        usure = [0.0] * m
        for (k, x, y, ty, j) in faits:
            usure[k] = 0.0 if ty == PM else usure[k] + (y - x)
        for k in range(m):
            f = usure[k] / T[k]
            au.barh(k, 1.0, color="#ecebe6", height=0.62, zorder=1)
            au.barh(k, f, color=SF.CATEGORIELLE[1] if f > 0.8 else SF.CATEGORIELLE[2], height=0.62, zorder=2)
            au.text(1.04, k, f"{usure[k]:g}/{T[k]}", va="center", fontsize=SF.TAILLE - 1.5, color=SF.ENCRE_2)
        au.axvline(1.0, color=SF.ENCRE, lw=1.0)
        au.set_xlim(0, 1.45); au.set_ylim(m - 0.5, -0.6)
        au.set_yticks([]); au.set_xticks([])
        au.set_title("Wear $c_k / T_k$", fontsize=SF.TAILLE, color=SF.ENCRE)
        for s in ("top", "right", "left", "bottom"):
            au.spines[s].set_visible(False)
        h = [Patch(color=SF.CATEGORIELLE[0], label="Operation (job number)"),
             Patch(facecolor=SF.GRIS_PM, edgecolor=SF.SURFACE, hatch="////", label="Preventive maintenance")]
        ax.legend(handles=h, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=SF.TAILLE - 1)

    images = list(range(0, len(segs) + 1)) + [len(segs)] * 14       # pause sur le planning final
    anim = FuncAnimation(fig, dessiner, frames=images, interval=a.ms)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.87, bottom=0.25)
    os.makedirs(os.path.dirname(os.path.abspath(sortie)), exist_ok=True)
    anim.save(sortie, writer=PillowWriter(fps=1000 / a.ms))
    print(f"{titre_src} : {len(segs)} décisions, C_max = {cmax:g} -> {sortie}")


if __name__ == "__main__":
    main()
