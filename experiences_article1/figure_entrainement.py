"""Figure de la section 5.2 (Training) : les trois étapes d'estimation de theta et la sélection sur la validation
(demande de Ghita, 21/10/2026). Schéma de méthode : aucun résultat, seulement les réglages décrits dans le texte
(2 000 plannings experts ; 300 000 décisions PPO ; 8 tours x 48 instances, 12 tirages à T = 0,5, 2 règles,
gain >= 0,5 %, 4 derniers tours ; 24 instances de validation), repris de models/imitation/cand_ft_config.json
et imitation/entrainer.py. Style commun : style_figures.py.

  python -m experiences_article1.figure_entrainement   # -> resultats/schema_entrainement.pdf|png
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF   # noqa: E402
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

F = SF.TAILLE
BLEU_C, ORANGE_C, VERT_C, GRIS_C = "#d6e6f8", "#fbe0d4", "#d3f0e4", "#ecebe8"


def boite(ax, x, y, w, h, titre, corps=None, fc=GRIS_C, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc,
                                ec=SF.ENCRE_2, lw=0.8, ls=ls, zorder=2))
    if corps:
        ax.text(x + w / 2, y + h - 0.18, titre, ha="center", va="top", fontsize=F, fontweight="bold",
                color=SF.ENCRE, zorder=3)
        ax.text(x + w / 2, y + h - 0.62, corps, ha="center", va="top", fontsize=F - 1.5, color=SF.ENCRE,
                zorder=3, linespacing=1.35)
    else:
        ax.text(x + w / 2, y + h / 2, titre, ha="center", va="center", fontsize=F - 1, color=SF.ENCRE, zorder=3,
                linespacing=1.3)


def fl(ax, x0, y0, x1, y1, txt=None, ls="-", dy=0.12, ha="center"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=SF.ENCRE_2, lw=0.9,
                ls=ls, shrinkA=1, shrinkB=1, mutation_scale=9), zorder=1)
    if txt:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, txt, ha=ha, va="bottom", fontsize=F - 1, color=SF.ENCRE)


def main():
    SF.style()
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.set_xlim(0, 15.6)
    ax.set_ylim(0, 8.2)
    ax.axis("off")

    # sources de données (rangée haute)
    yS, hS = 6.35, 1.35
    boite(ax, 0.2, yS, 4.5, hS, "Tuned simulated annealing\n2 000 expert schedules\non generated instances", fc=ORANGE_C)
    boite(ax, 5.55, yS, 4.5, hS, "Episodes of $\\pi_\\theta$ in the MDP\ngenerated instances (base)", fc=GRIS_C)
    boite(ax, 10.9, yS, 4.5, hS, "Candidate schedules: greedy,\n12 samples ($T = 0.5$), 2 rules;\nbest kept if gain $\\geq 0.5\\,\\%$",
          fc=GRIS_C)

    # trois étapes
    yE, hE, wE = 3.1, 2.55, 4.5
    xs = [0.2, 5.55, 10.9]
    boite(ax, xs[0], yE, wE, hE, "Stage 1: imitation",
          "replay of each expert schedule;\nconsistent actions $C^*(s)$\n"
          "loss $\\mathcal{L}_{\\mathrm{IL}}$: $-\\log \\Sigma_{a \\in C^*(s)}\\, \\pi_\\theta(a \\mid s)$\n+ value regression", fc=BLEU_C)
    boite(ax, xs[1], yE, wE, hE, "Stage 2: PPO",
          "300 000 decisions\nadvantages $\\hat A_t$ by GAE\nfrom $\\delta_t$ with $V = V_\\theta$\n"
          "clipped objective $\\mathcal{L}_{\\mathrm{PPO}}$", fc=BLEU_C)
    boite(ax, xs[2], yE, wE, hE, "Stage 3: self-imitation",
          "8 rounds of 48 instances\ncross-entropy on the decisions\nof the best candidate schedules\n"
          "(last 4 rounds retained)", fc=BLEU_C)
    for x in xs:
        fl(ax, x + wE / 2, yS, x + wE / 2, yE + hE)
    # enchaînement des paramètres
    fl(ax, xs[0] + wE, yE + hE / 2, xs[1], yE + hE / 2, "$\\theta_1$")
    fl(ax, xs[1] + wE, yE + hE / 2, xs[2], yE + hE / 2, "$\\theta_2$")
    ax.text(0.2, yE + hE / 2, "", fontsize=F)

    # validation et sélection
    yV, hV = 0.15, 1.6
    boite(ax, 3.2, yV, 9.2, hV, "Model selection on validation instances\n"
          "$\\theta^*$: the parameters with the smallest\nvalidation makespan among $\\theta_1, \\theta_2, \\theta_3$", fc=VERT_C)
    for x, lab in zip(xs, ("$\\theta_1$", "$\\theta_2$", "$\\theta_3$")):
        xc = x + wE / 2
        xv = min(max(xc, 3.6), 12.0)
        fl(ax, xc, yE, xv, yV + hV, ls=(0, (3, 2)))
        ax.text(xc + 0.12, yE - 0.55, lab, ha="left", va="center", fontsize=F - 0.5, color=SF.ENCRE)
    fl(ax, 12.4, yV + hV / 2, 13.6, yV + hV / 2)
    ax.text(13.7, yV + hV / 2, "$\\theta^*$:\nnetwork used\nin the beam search", ha="left", va="center",
            fontsize=F - 1, color=SF.ENCRE)

    out = os.path.join(ICI, "resultats", "schema_entrainement")
    fig.savefig(out + ".pdf", bbox_inches="tight")
    fig.savefig(out + ".png", dpi=220, bbox_inches="tight")
    print("ok", out)


if __name__ == "__main__":
    main()
