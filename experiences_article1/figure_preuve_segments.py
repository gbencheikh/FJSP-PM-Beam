"""Schéma explicatif de la preuve de la Proposition 1 (nombre de segments suffisant), section 3.3 de l'article 1.

Exemple fictif (purement illustratif, aucune donnée expérimentale) : une machine k, seuil T_k = 10,
maintenance de durée 2, cinq segments de charges 4 | 3 | 8 | 2 | 7.
  (a) planning de départ (quelconque : la fusion vaut pour tout planning) ;
  (b) après fusion des paires consécutives de charge totale <= T_k (4+3 = 7, 8+2 = 10) : on supprime la
      maintenance qui les sépare SANS déplacer aucune opération (le temps libéré reste inoccupé) ;
  (c) argument de comptage : deux segments consécutifs pèsent ensemble plus que T_k.
Style commun : style_figures.py.

  python -m experiences_article1.figure_preuve_segments   # -> resultats/schema_preuve_segments.pdf|png
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF   # noqa: E402

T, M = 10, 2
# opérations (début, durée) groupées par segment ; maintenances entre segments
SEGMENTS = [[(0, 4)], [(6, 3)], [(11, 5), (16, 3)], [(21, 2)], [(25, 4), (29, 3)]]
PM = [4, 9, 19, 23]                 # début des maintenances (durée M)
SUPPRIMEES = {0, 2}                 # maintenances supprimées : entre seg. 1-2 (4+3) et seg. 3-4 (8+2)


def boite(ax, y, a, d, **kw):
    ax.barh(y, d, left=a, height=0.5, **kw)


def ligne(ax, y, pms_actives, pms_suppr, groupes, titre):
    for seg in SEGMENTS:
        for a, d in seg:
            boite(ax, y, a, d, color=SF.CATEGORIELLE[0], edgecolor=SF.SURFACE, linewidth=1.0, zorder=2)
    for idx, a in enumerate(PM):
        if idx in pms_actives:
            boite(ax, y, a, M, color=SF.GRIS_PM, edgecolor=SF.SURFACE, linewidth=1.0, hatch="////", zorder=2)
        elif idx in pms_suppr:
            boite(ax, y, a, M, fill=False, edgecolor=SF.ENCRE_2, linewidth=0.8, linestyle=(0, (2, 2)), zorder=2)
    # accolades de segment et charges
    for (deb, fin, charge) in groupes:
        yb = y + 0.38
        ax.plot([deb, deb, fin, fin], [yb + 0.08, yb + 0.16, yb + 0.16, yb + 0.08], color=SF.ENCRE, lw=0.8)
        ax.text((deb + fin) / 2, yb + 0.22, f"load {charge}", ha="center", va="top", fontsize=SF.TAILLE - 0.5,
                color=SF.ENCRE)
    ax.text(-0.6, y, titre, ha="right", va="center", fontsize=SF.TAILLE, color=SF.ENCRE)


def main():
    SF.style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    tous = set(range(len(PM)))
    # (a) départ : 5 segments
    ga = [(0, 4, 4), (6, 9, 3), (11, 19, 8), (21, 23, 2), (25, 32, 7)]
    ligne(ax, 0, tous, set(), ga, "(a) initial schedule")
    # (b) après fusions : 3 segments, mêmes dates
    gb = [(0, 9, 7), (11, 23, 10), (25, 32, 7)]
    ligne(ax, 1.25, tous - SUPPRIMEES, SUPPRIMEES, gb, "(b) after merging")
    # maintenances à supprimer, signalées au-dessus de (a)
    for idx, txt in ((0, "4 + 3 = 7 ≤ 10"), (2, "8 + 2 = 10 ≤ 10")):
        x = PM[idx] + M / 2
        ax.annotate(txt, xy=(x, -0.27), xytext=(x, -0.62), ha="center", va="center",
                    fontsize=SF.TAILLE - 1, color=SF.ENCRE_2,
                    arrowprops=dict(arrowstyle="->", color=SF.ENCRE_2, lw=0.8))
    # (c) comptage par paires
    y = 2.35
    ax.plot([0, 0, 23, 23], [y - 0.1, y, y, y - 0.1], color=SF.ENCRE, lw=0.8)
    ax.text(11.5, y + 0.05, r"pair (1,2): $7 + 10 > T_k$", ha="center", va="top", fontsize=SF.TAILLE - 0.5,
            color=SF.ENCRE)
    ax.plot([25, 25, 32, 32], [y - 0.1, y, y, y - 0.1], color=SF.ENCRE, lw=0.8)
    ax.text(28.5, y + 0.05, "segment 3", ha="center", va="top", fontsize=SF.TAILLE - 0.5, color=SF.ENCRE)
    ax.text(-0.6, y - 0.12, "(c) counting", ha="right", va="center", fontsize=SF.TAILLE, color=SF.ENCRE)
    ax.set_xlim(-0.5, 33)
    ax.set_ylim(2.6, -0.8)
    ax.set_yticks([])
    ax.set_xlabel("Time on machine $k$  ($T_k = 10$)")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    from matplotlib.patches import Patch
    h = [Patch(color=SF.CATEGORIELLE[0], label="Operation"),
         Patch(facecolor=SF.GRIS_PM, edgecolor=SF.SURFACE, hatch="////", label="Maintenance"),
         Patch(fill=False, edgecolor=SF.ENCRE_2, linestyle=(0, (2, 2)), label="Removed maintenance (time left idle)")]
    fig.legend(handles=h, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    base = os.path.join(ICI, "resultats", "schema_preuve_segments")
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print("ok", base)


if __name__ == "__main__":
    main()
