"""Schéma du contre-exemple de la section 3.3 (facteur 2 de la Proposition 1 indispensable).

Exemple fictif, illustratif : un job de trois opérations de durée 6 sur une machine, T = 10, maintenance de
durée 2. Deux segments voisins pèsent déjà 12 > 10 : aucune fusion n'est possible (la boucle de la preuve
s'arrête sans rien faire), et il faut 3 segments alors que ceil(18/10) = 2 ; la borne 2*ceil(18/10) - 1 = 3
est atteinte. Style commun : style_figures.py.

  python -m experiences_article1.figure_contre_exemple_segments   # -> resultats/schema_contre_exemple_segments.pdf|png
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF   # noqa: E402

M = 2
OPS = [0, 8, 16]          # débuts des trois opérations de durée 6
PMS = [6, 14]             # débuts des deux maintenances


def main():
    SF.style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    fig, ax = plt.subplots(figsize=(6.4, 1.8))
    for i, a in enumerate(OPS):
        ax.barh(0, 6, left=a, height=0.5, color=SF.CATEGORIELLE[0], edgecolor=SF.SURFACE, lw=1.0, zorder=2)
        ax.text(a + 3, 0, f"$O_{{1,{i + 1}}}$", ha="center", va="center", color=SF.SURFACE, fontsize=SF.TAILLE)
        yb = 0.38
        ax.plot([a, a, a + 6, a + 6], [yb + 0.08, yb + 0.16, yb + 0.16, yb + 0.08], color=SF.ENCRE, lw=0.8)
        ax.text(a + 3, yb + 0.22, f"segment {i + 1}: load 6", ha="center", va="top", fontsize=SF.TAILLE - 0.5,
                color=SF.ENCRE)
    for a in PMS:
        ax.barh(0, M, left=a, height=0.5, color=SF.GRIS_PM, edgecolor=SF.SURFACE, lw=1.0, hatch="////", zorder=2)
    for a in PMS:   # chaque paire de segments voisins pèse déjà plus que T
        ax.annotate("6 + 6 = 12 > 10\nno merge", xy=(a + M / 2, -0.27), xytext=(a + M / 2, -0.75),
                    ha="center", va="center", fontsize=SF.TAILLE - 1, color=SF.ENCRE_2,
                    arrowprops=dict(arrowstyle="->", color=SF.ENCRE_2, lw=0.8))
    ax.text(23.0, 0, r"$N = 3 > \lceil 18/10 \rceil = 2$" "\n" r"$N = 2\lceil 18/10 \rceil - 1$",
            ha="left", va="center", fontsize=SF.TAILLE, color=SF.ENCRE)
    ax.set_xlim(-0.5, 29)
    ax.set_ylim(0.85, -1.05)
    ax.set_yticks([])
    ax.set_xlabel("Time on the machine  ($T = 10$)", x=11.25 / 29.5)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([0, 6, 8, 14, 16, 22])
    ax.spines["bottom"].set_bounds(0, 22)
    h = [Patch(color=SF.CATEGORIELLE[0], label="Operation"),
         Patch(facecolor=SF.GRIS_PM, edgecolor=SF.SURFACE, hatch="////", label="Maintenance")]
    fig.legend(handles=h, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    base = os.path.join(ICI, "resultats", "schema_contre_exemple_segments")
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print("ok", base)


if __name__ == "__main__":
    main()
