"""Figure de la section 5.3 : un pas du faisceau avec B = 3, K = 2 (demande de Ghita, 22/10/2026).

Exemple fictif (aucune donnée expérimentale). Gauche : développement (trois états retenus, deux actions sur trois
développées chacune) et évaluation (H, LB). Droite : sélection, enfants classés par H croissant :
  s'21 H 50 LB 44 -> retenu ; s'11 H 52 LB 45 -> retenu (égalité avec s'22, log-probabilité plus grande) ;
  s'22 H 52 -> identique à s'11, écarté ; s'31 H 54 LB 50 >= Ĉ = 50 -> élagué ; s'12 H 55 LB 47 -> retenu ;
  s'32 H 56 -> non examiné (faisceau plein).  Ĉ = 50 après l'évaluation (complétion de s'21).
Version précédente (B = K = 2) : archives_code_6oct/figure_faisceau_B2K2_2026-10-22.py.

  python -m experiences_article1.figure_faisceau   # -> resultats/schema_faisceau.pdf|png
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF   # noqa: E402
from experiences_article1.figures_methode import boite, fleche, toile, sauver, BLEU, BLEU_C, VERT_C, GRIS_C  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

F = SF.TAILLE
GRIS_T = "#9a9994"
ENFANTS = {  # nom : (parent, probabilité, H, LB)
    "11": (1, "0.6", 52, 45), "12": (1, "0.3", 55, 47),
    "21": (2, "0.5", 50, 44), "22": (2, "0.4", 52, 46),
    "31": (3, "0.7", 54, 50), "32": (3, "0.2", 56, 48)}
ORDRE = [("21", "kept", "ok"), ("11", "kept", "ok"), ("22", "identical to $s_{11}'$: discarded", "dup"),
         ("31", "$LB \\geq \\hat C$: pruned", "elag"), ("12", "kept ($\\mathcal{B}$ now full)", "ok"),
         ("32", "not examined", "non")]


def main():
    SF.style()
    fig, ax = toile(7.2, 5.0, 15.0, 9.6)
    ax.set_ylim(-1.1, 9.6)
    ax.text(2.3, 9.45, "(i) Expansion and (ii) evaluation", ha="center", va="top", fontsize=F, fontweight="bold")
    ax.text(9.0, 9.45, "(iii) Selection, by increasing $H$", ha="center", va="top", fontsize=F, fontweight="bold")
    ax.text(13.9, 9.45, "New $\\mathcal{B}$", ha="center", va="top", fontsize=F, fontweight="bold")

    # --- arbre : 3 états, 2 enfants développés chacun, 1 action non développée
    ypar = {1: 7.4, 2: 4.6, 3: 1.8}
    yenf = {}
    for p, yc in ypar.items():
        boite(ax, 0.0, yc - 0.4, 1.0, 0.8, f"$s_{p}$", fc=GRIS_C)
        ys = (yc + 0.75, yc - 0.45)
        for (nom, (pp, pr, h, lb)), y in zip([(n, v) for n, v in ENFANTS.items() if v[0] == p], ys):
            yenf[nom] = y
            boite(ax, 2.0, y - 0.38, 2.6, 0.76, f"$s_{{{nom}}}'$:  $H = {h}$,  $LB = {lb}$", fc=VERT_C, fs=F - 1.5)
            fleche(ax, 1.0, yc, 2.0, y)
            ax.text(1.45, (yc + y) / 2 + (0.1 if y > yc else -0.32), pr, ha="center", fontsize=F - 2.5,
                    color=SF.ENCRE_2)
        ax.annotate("", xy=(1.85, yc - 1.15), xytext=(1.0, yc - 0.25),
                    arrowprops=dict(arrowstyle="-|>", color=GRIS_T, lw=0.7, ls=(0, (2, 2)), mutation_scale=7))
        ax.text(1.95, yc - 1.15, "0.1: not expanded", fontsize=F - 2.5,
                va="center", color=GRIS_T)

    # --- tableau de sélection
    x0, w = 5.4, 7.1
    ax.text(x0 + 0.35, 8.55, "rank", fontsize=F - 1.5, color=SF.ENCRE_2, va="center")
    ax.text(x0 + 1.25, 8.55, "state", fontsize=F - 1.5, color=SF.ENCRE_2, va="center")
    ax.text(x0 + 2.35, 8.55, "$H$", fontsize=F - 1.5, color=SF.ENCRE_2, va="center")
    ax.text(x0 + 3.0, 8.55, "$LB$", fontsize=F - 1.5, color=SF.ENCRE_2, va="center")
    ax.text(x0 + 3.85, 8.55, "decision", fontsize=F - 1.5, color=SF.ENCRE_2, va="center")
    ykept = {}
    for r, (nom, txt, typ) in enumerate(ORDRE):
        y = 7.8 - r * 1.1
        fc = {"ok": BLEU_C, "dup": "white", "elag": "white", "non": "#f4f4f2"}[typ]
        ax.add_patch(Rectangle((x0, y - 0.4), w, 0.8, fc=fc, ec="#b9b8b3", lw=0.7,
                               ls="-" if typ == "ok" else (0, (3, 2))))
        _, _, h, lb = ENFANTS[nom]
        col = SF.ENCRE if typ in ("ok",) else SF.ENCRE_2
        for dx, t in ((0.5, f"{r + 1}"), (1.3, f"$s_{{{nom}}}'$"), (2.35, f"{h}"), (3.05, f"{lb}")):
            ax.text(x0 + dx, y, t, fontsize=F - 1, va="center", color=col)
        ax.text(x0 + 3.85, y, txt, fontsize=F - 1.5, va="center", color=col)
        if typ == "ok":
            ykept[nom] = y
    # --- nouveau faisceau
    for nom, y in ykept.items():
        boite(ax, 13.3, y - 0.38, 1.2, 0.76, f"$s_{{{nom}}}'$", fc=BLEU, ec=BLEU, fs=F - 0.5)
        ax.texts[-1].set_color(SF.SURFACE)
        fleche(ax, x0 + w, y, 13.3, y)
    # --- note
    ax.text(7.5, -1.05, "Arrows of (i): probabilities under $\\pi_\\theta$; the $K = 2$ most probable actions are expanded.\n"
            "Incumbent after (ii): $\\hat C = 50$ (completion of $s_{21}'$). Ties in $H$ are broken by decreasing log-probability.",
            ha="center", va="bottom", fontsize=F - 1.5, color=SF.ENCRE_2)
    sauver(fig, "schema_faisceau")


if __name__ == "__main__":
    main()
