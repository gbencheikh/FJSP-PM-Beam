"""Figure de la section 3.3 (Proposition 1, nombre de segments) : deux schémas côte à côte (décision de Ghita, 13/10).

(a) Preuve : fusion des segments voisins trop légers. Exemple fictif : T_k = 10, maintenance de durée 2,
    charges 4 | 3 | 8 | 2 | 7 -> 7 | 10 | 7 ; aucune opération ne bouge, le temps libéré reste inoccupé.
(b) Exemple : trois opérations de durée 6, T = 10 ; toute paire de segments voisins pèse déjà 12 > 10, aucune
    fusion ; N = 3 = 2*ceil(18/10) - 1 (borne atteinte) alors que ceil(18/10) = 2.
Exemples purement illustratifs (aucune donnée expérimentale). Style commun : style_figures.py.
Remplace figure_preuve_segments.py et figure_contre_exemple_segments.py dans l'article (conservés).

  python -m experiences_article1.figure_segments   # -> resultats/schema_segments.pdf|png
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF   # noqa: E402

M = 2
F = SF.TAILLE - 1      # petite police des annotations


def op(ax, y, a, d, lab=None):
    ax.barh(y, d, left=a, height=0.5, color=SF.CATEGORIELLE[0], edgecolor=SF.SURFACE, lw=0.8, zorder=2)
    if lab:
        ax.text(a + d / 2, y, lab, ha="center", va="center", color=SF.SURFACE, fontsize=F)


def pm(ax, y, a, retiree=False):
    if retiree:
        ax.barh(y, M, left=a, height=0.5, fill=False, edgecolor=SF.ENCRE_2, lw=0.7, ls=(0, (2, 2)), zorder=2)
    else:
        ax.barh(y, M, left=a, height=0.5, color=SF.GRIS_PM, edgecolor=SF.SURFACE, lw=0.8, hatch="////", zorder=2)


def accolade(ax, y, a, b, txt):
    yb = y + 0.38
    ax.plot([a, a, b, b], [yb + 0.06, yb + 0.14, yb + 0.14, yb + 0.06], color=SF.ENCRE, lw=0.7)
    ax.text((a + b) / 2, yb + 0.2, txt, ha="center", va="top", fontsize=F, color=SF.ENCRE)


def note(ax, x, y_bar, txt):
    ax.annotate(txt, xy=(x, y_bar - 0.27), xytext=(x, y_bar - 0.62), ha="center", va="center", fontsize=F,
                color=SF.ENCRE_2, arrowprops=dict(arrowstyle="->", color=SF.ENCRE_2, lw=0.7))


def nettoyer(ax, xmax, ticks):
    ax.set_xlim(-0.5, xmax)
    ax.set_yticks([])
    ax.set_xticks(ticks)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)


def panneau_preuve(ax):
    segs = [[(0, 4)], [(6, 3)], [(11, 5), (16, 3)], [(21, 2)], [(25, 4), (29, 3)]]
    pms, retirees = [4, 9, 19, 23], {0, 2}
    for y, ret in ((0, set()), (1.3, retirees)):
        for s in segs:
            for a, d in s:
                op(ax, y, a, d)
        for i, a in enumerate(pms):
            pm(ax, y, a, retiree=i in ret)
    for (a, b, c) in [(0, 4, "4"), (6, 9, "3"), (11, 19, "8"), (21, 23, "2"), (25, 32, "7")]:
        accolade(ax, 0, a, b, c)
    for (a, b, c) in [(0, 9, "7"), (11, 23, "10"), (25, 32, "7")]:
        accolade(ax, 1.3, a, b, c)
    note(ax, pms[0] + M / 2, 0, "4+3 ≤ 10")
    note(ax, pms[2] + M / 2, 0, "8+2 ≤ 10")
    y = 2.35
    ax.plot([0, 0, 23, 23], [y - 0.08, y, y, y - 0.08], color=SF.ENCRE, lw=0.7)
    ax.text(11.5, y + 0.06, r"pair (1,2): $7+10 > T_k$", ha="center", va="top", fontsize=F, color=SF.ENCRE)
    for yy, t in ((0, "initial"), (1.3, "merged"), (2.27, "pairs")):
        ax.text(-1.0, yy, t, ha="right", va="center", fontsize=F, color=SF.ENCRE)
    nettoyer(ax, 32.5, [0, 10, 20, 30])
    ax.set_ylim(2.9, -0.95)
    ax.set_xlabel("Time ($T_k = 10$)")
    ax.set_title("(a) Merging light consecutive segments", loc="left", fontsize=SF.TAILLE, color=SF.ENCRE)


def panneau_exemple(ax):
    for i, a in enumerate([0, 8, 16]):
        op(ax, 0, a, 6, f"$O_{{1,{i + 1}}}$")
        accolade(ax, 0, a, a + 6, "6")
    for a in (6, 14):
        pm(ax, 0, a)
        note(ax, a + M / 2, 0, "6+6 > 10")
    ax.text(11, 1.55, "no merge possible\n" r"$N = 3 = 2\lceil 18/10\rceil - 1$" "\n" r"whereas $\lceil 18/10\rceil = 2$",
            ha="center", va="center", fontsize=F, color=SF.ENCRE)
    nettoyer(ax, 22.5, [0, 6, 8, 14, 16, 22])
    ax.set_ylim(2.9, -0.95)
    ax.set_xlabel("Time ($T = 10$)")
    ax.set_title("(b) No merge possible", loc="left", fontsize=SF.TAILLE, color=SF.ENCRE)


def main():
    SF.style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.6), gridspec_kw=dict(width_ratios=[1.45, 1]))
    panneau_preuve(a1)
    panneau_exemple(a2)
    h = [Patch(color=SF.CATEGORIELLE[0], label="Operation"),
         Patch(facecolor=SF.GRIS_PM, edgecolor=SF.SURFACE, hatch="////", label="Maintenance"),
         Patch(fill=False, edgecolor=SF.ENCRE_2, linestyle=(0, (2, 2)), label="Removed maintenance (time left idle)")]
    fig.legend(handles=h, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.01), fontsize=F)
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=2.5)
    base = os.path.join(ICI, "resultats", "schema_segments")
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print("ok", base)


if __name__ == "__main__":
    main()
