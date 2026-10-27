"""Schémas de la section Method de l'article 1 (14/10/2026). Purement explicatifs : aucun chiffre expérimental,
sauf ceux qui décrivent la méthode (2 000 plannings experts, 33 et 19 descripteurs), repris de article.tex § 5.
  1. vue d'ensemble : entraînement hors ligne, puis recherche au moment de décider ;
  2. réseau à notation de candidats (CandNet, jssp_pm/fjsp_ppo.py) ;
  3. un pas du faisceau B × K sur un exemple fictif (B = K = 2) : complétion, tri, élagage, doublon.
Style commun : style_figures.py.

  python -m experiences_article1.figures_methode   # -> resultats/schema_methode_{ensemble,reseau,faisceau}.pdf|png
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
BLEU, BLEU_C = SF.CATEGORIELLE[0], "#d6e6f8"
ORANGE_C, VERT_C, GRIS_C = "#fbe0d4", "#d3f0e4", "#ecebe8"


def boite(ax, x, y, w, h, txt, fc=GRIS_C, ec=SF.ENCRE_2, fs=F, lw=0.8, ls="-", gras=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=lw,
                                ls=ls, zorder=2))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, color=SF.ENCRE, zorder=3,
            fontweight="bold" if gras else "normal")


def fleche(ax, x0, y0, x1, y1, txt=None, ls="-", dx=0.0, dy=0.08):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=SF.ENCRE_2, lw=0.9, ls=ls, shrinkA=1, shrinkB=1), zorder=1)
    if txt:
        ax.text((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, txt, ha="center", va="bottom", fontsize=F - 1.5,
                color=SF.ENCRE_2)


def toile(w, h, xmax, ymax):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def sauver(fig, nom):
    base = os.path.join(ICI, "resultats", nom)
    fig.savefig(base + ".pdf", bbox_inches="tight")
    fig.savefig(base + ".png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("ok", base)


# ------------------------------------------------------------------ 0. MDP : boucle agent-environnement et instants de décision
def mdp():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 2.6), gridspec_kw=dict(width_ratios=[1.1, 1]))
    ax = a1
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    boite(ax, 0.1, 2.9, 3.1, 2.1, "Environment\nevent-driven\nsimulator", fc=VERT_C, fs=F - 1)
    boite(ax, 6.8, 2.9, 3.1, 2.1, "Agent\n" r"policy $\pi_\theta(a \mid s)$", fc=BLEU_C, fs=F - 1)
    fleche(ax, 3.2, 4.45, 6.8, 4.45)
    ax.text(5.0, 4.6, r"state $s_t$, valid" "\n" r"actions $\mathcal{A}(s_t)$", ha="center", va="bottom",
            fontsize=F - 1.5, color=SF.ENCRE_2)
    fleche(ax, 6.8, 3.45, 3.2, 3.45)
    ax.text(5.0, 3.3, r"action $a_t$", ha="center", va="top", fontsize=F - 1.5, color=SF.ENCRE_2)
    ax.annotate("", xy=(8.35, 2.9), xytext=(1.65, 2.9),
                arrowprops=dict(arrowstyle="-|>", color=SF.ENCRE_2, lw=0.9, ls="--",
                                connectionstyle="arc3,rad=0.4"), zorder=1)
    ax.text(5.0, 1.15, r"reward $r_t = -\Delta t / u$", ha="center", fontsize=F - 1.5, color=SF.ENCRE_2)
    ax.text(5.0, 0.05, r"episode return $\sum_t r_t = -C_{\max}/u$", ha="center", fontsize=F - 1.5, color=SF.ENCRE)
    ax.set_title("(a) Agent–environment loop", loc="left", fontsize=F, color=SF.ENCRE)
    ax = a2
    seg = [(0, 0, 4, 0), (0, 5, 8, 2), (1, 0, 3, 2), (1, 3, 5, 3), (1, 5, 8, 0)]
    for k, a, b, j in seg:
        ax.barh(k, b - a, left=a, height=0.5, color=SF.CATEGORIELLE[j], edgecolor=SF.SURFACE, lw=0.8, zorder=2)
    ax.barh(0, 1, left=4, height=0.5, color=SF.GRIS_PM, edgecolor=SF.SURFACE, lw=0.8, hatch="////", zorder=2)
    for t in (0, 3, 4, 5):
        ax.axvline(t, color=SF.ENCRE_2, lw=0.7, ls=(0, (2, 2)), zorder=1)
        ax.plot(t, -0.5, marker="v", ms=4, color=SF.ENCRE, zorder=3)
    ax.text(5.4, -0.5, "decision epochs", fontsize=F - 1.5, color=SF.ENCRE, va="center")
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Machine 1", "Machine 2"], fontsize=F - 1)
    ax.set_ylim(1.5, -0.9); ax.set_xlim(-0.2, 8.5)
    ax.set_xticks([0, 3, 4, 5, 8])
    ax.set_xlabel("Time", fontsize=F - 1)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.set_title("(b) Decision epochs", loc="left", fontsize=F, color=SF.ENCRE)
    fig.tight_layout(w_pad=1.5)
    sauver(fig, "schema_methode_mdp")


# ------------------------------------------------------------------ 1. vue d'ensemble
def ensemble():
    fig, ax = toile(6.6, 2.9, 13.2, 5.8)
    # bandeaux
    ax.add_patch(FancyBboxPatch((0.05, 3.05), 13.1, 2.65, boxstyle="round,pad=0,rounding_size=0.1",
                                fc="#f7f7f5", ec="none", zorder=0))
    ax.add_patch(FancyBboxPatch((0.05, 0.05), 13.1, 2.75, boxstyle="round,pad=0,rounding_size=0.1",
                                fc="#f7f7f5", ec="none", zorder=0))
    ax.text(0.25, 5.45, "Offline training (once, on generated instances)", fontsize=F, color=SF.ENCRE,
            fontweight="bold", va="center")
    ax.text(0.25, 2.55, "At decision time (each instance to solve)", fontsize=F, color=SF.ENCRE,
            fontweight="bold", va="center")
    y, h = 3.55, 1.25
    boite(ax, 0.25, y, 1.9, h, "Generated\ninstances", fs=F - 1)
    boite(ax, 2.55, y, 2.3, h, "Tuned simulated\nannealing:\nexpert schedules", fc=ORANGE_C, fs=F - 1)
    boite(ax, 5.25, y, 1.65, h, "Step 1\nimitation", fc=BLEU_C)
    boite(ax, 7.3, y, 1.65, h, "Step 2\nPPO", fc=BLEU_C)
    boite(ax, 9.35, y, 1.65, h, "Step 3\nself-\nimitation", fc=BLEU_C)
    boite(ax, 11.35, y, 1.65, h, r"Policy" "\n" r"network $\pi_\theta$" "\n(frozen)", fc=BLEU, ec=BLEU)
    ax.texts[-1].set_color(SF.SURFACE)
    for x0, x1 in ((2.15, 2.6), (4.8, 5.25), (6.9, 7.3), (8.95, 9.35), (11.0, 11.35)):
        fleche(ax, x0, y + h / 2, x1, y + h / 2)
    # bas
    yb, hb = 0.55, 1.5
    boite(ax, 0.25, yb + 0.15, 1.9, 1.2, "Instance\nto solve", fs=F - 1)
    boite(ax, 2.75, yb + 0.85, 3.3, 0.85, r"$\pi_\theta$: which $K$ actions" "\nare worth trying?", fc=BLEU_C, fs=F - 1)
    boite(ax, 2.75, yb - 0.25, 3.3, 0.85, "Fast engine: completes\nthe schedule, lower bound", fc=VERT_C, fs=F - 1)
    boite(ax, 7.0, yb, 2.9, hb, r"Beam search $B \times K$:" "\nkeeps the $B$ best\npartial schedules", fc=GRIS_C, fs=F - 1)
    boite(ax, 10.8, yb + 0.15, 2.3, 1.2, "Schedule:\nbest complete\nschedule found", fs=F - 1)
    fleche(ax, 2.15, yb + 0.75, 7.0, yb + 0.75)
    fleche(ax, 6.05, yb + 1.27, 7.0, yb + 1.05)
    fleche(ax, 6.05, yb + 0.17, 7.0, yb + 0.45)
    fleche(ax, 9.9, yb + 0.75, 10.8, yb + 0.75)
    fleche(ax, 12.17, y, 12.17, 2.9, ls="--")
    ax.annotate("", xy=(4.45, yb + 1.7), xytext=(12.17, 2.9),
                arrowprops=dict(arrowstyle="-|>", color=SF.ENCRE_2, lw=0.9, ls="--",
                                connectionstyle="angle,angleA=180,angleB=90,rad=0"), zorder=1)
    sauver(fig, "schema_methode_ensemble")


# ------------------------------------------------------------------ 2. réseau
def reseau():
    fig, ax = toile(6.6, 2.8, 13.2, 5.6)
    ax.text(1.25, 5.3, "Candidate actions", ha="center", fontsize=F, color=SF.ENCRE, fontweight="bold")
    noms = [r"launch $O_{j,i}$ on $k$", r"maintain $k'$", "wait"]
    ys = [4.25, 3.3, 2.35]
    for yy, n in zip(ys, noms):
        boite(ax, 0.1, yy, 2.3, 0.75, n + "\n(33 features)", fs=F - 1.5)
        boite(ax, 2.9, yy, 1.0, 0.75, r"$\phi_c$", fc=BLEU_C)
        boite(ax, 4.4, yy, 0.9, 0.75, r"$e_c$", fc="white")
        fleche(ax, 2.4, yy + 0.375, 2.9, yy + 0.375)
        fleche(ax, 3.9, yy + 0.375, 4.4, yy + 0.375)
        fleche(ax, 5.3, yy + 0.375, 6.1, 3.35)
    boite(ax, 0.1, 0.45, 2.3, 0.85, "global state\n(19 features)", fs=F - 1.5)
    boite(ax, 2.9, 0.5, 1.0, 0.75, r"$\phi_g$", fc=BLEU_C)
    boite(ax, 4.4, 0.5, 0.9, 0.75, r"$e_g$", fc="white")
    fleche(ax, 2.4, 0.88, 2.9, 0.88)
    fleche(ax, 3.9, 0.88, 4.4, 0.88)
    boite(ax, 6.1, 2.95, 1.5, 0.8, r"mean $\bar e$", fc="white")
    boite(ax, 8.2, 3.0, 2.0, 1.9, r"$\psi([e_c, e_g, \bar e])$" "\nsame network\nfor every $c$", fc=BLEU_C, fs=F - 1.5)
    fleche(ax, 5.3, 4.62, 8.2, 4.62, txt=r"$e_c$ of each candidate", dy=0.05)
    fleche(ax, 7.6, 3.35, 8.2, 3.6)
    fleche(ax, 5.3, 0.88, 8.2, 3.1)
    boite(ax, 10.6, 3.4, 1.0, 1.1, "score\n$z_c$", fc="white", fs=F - 1)
    boite(ax, 11.95, 3.4, 1.2, 1.1, "softmax\n" r"$\pi_\theta(c\,|\,s)$", fc=BLEU, ec=BLEU, fs=F - 1.5)
    ax.texts[-1].set_color(SF.SURFACE)
    fleche(ax, 10.2, 3.95, 10.6, 3.95)
    fleche(ax, 11.6, 3.95, 11.95, 3.95)
    boite(ax, 9.6, 0.45, 3.5, 0.95, r"value head $V([e_g, \bar e])$" "\n(used in training only)", fc="white", ls="--", fs=F - 1.5)
    fleche(ax, 6.85, 2.95, 9.6, 1.2, ls="--")
    fleche(ax, 5.3, 0.7, 9.6, 0.7, ls="--")
    sauver(fig, "schema_methode_reseau")


# ------------------------------------------------------------------ 3. un pas du faisceau
def faisceau():
    fig, ax = toile(6.6, 3.6, 13.2, 7.2)
    ax.text(0.9, 6.85, r"Beam, $B = 2$", ha="center", fontsize=F - 0.5, fontweight="bold", color=SF.ENCRE)
    ax.text(5.4, 6.85, r"$K = 2$ children each, completed by the engine", ha="center", fontsize=F - 0.5,
            fontweight="bold", color=SF.ENCRE)
    ax.text(11.85, 6.85, "New beam", ha="center", fontsize=F - 0.5, fontweight="bold", color=SF.ENCRE)
    boite(ax, 0.1, 4.3, 1.6, 0.9, r"$P_1$", fc=GRIS_C)
    boite(ax, 0.1, 1.5, 1.6, 0.9, r"$P_2$", fc=GRIS_C)
    # (y, enfant, C, borne, statut, type)
    E = [(5.3, r"$P_1 + a_1$", 58, 51, "4th: kept", "ok"),
         (3.85, r"$P_1 + a_2$", 54, 49, r"2nd: same state as $P_2 + a_3$:" "\nmerged", "dup"),
         (2.4, r"$P_2 + a_3$", 54, 49, "1st: kept", "ok"),
         (0.95, r"$P_2 + a_4$", 55, 54, "3rd: pruned, bound" "\n" r"$54 \geq$ incumbent $54$", "elag")]
    for (yy, n, c, lb, st, typ) in E:
        fc = BLEU_C if typ == "ok" else "white"
        boite(ax, 2.4, yy, 1.7, 0.85, n, fc=fc, ls="-" if typ == "ok" else "--", fs=F - 1)
        boite(ax, 4.5, yy, 2.0, 0.85, f"$C = {c}$\nbound ${lb}$", fc=VERT_C, fs=F - 1.5)
        fleche(ax, 4.1, yy + 0.42, 4.5, yy + 0.42)
        ax.text(6.7, yy + 0.42, st, fontsize=F - 1.5, color=SF.ENCRE if typ == "ok" else SF.ENCRE_2, va="center")
    for (yp, ys) in ((4.75, (5.72, 4.27)), (1.95, (2.82, 1.37))):
        for y2 in ys:
            fleche(ax, 1.7, yp, 2.4, y2)
    boite(ax, 10.9, 4.3, 1.9, 0.9, r"$P_2 + a_3$", fc=BLEU, ec=BLEU, fs=F - 1)
    ax.texts[-1].set_color(SF.SURFACE)
    boite(ax, 10.9, 1.5, 1.9, 0.9, r"$P_1 + a_1$", fc=BLEU, ec=BLEU, fs=F - 1)
    ax.texts[-1].set_color(SF.SURFACE)
    ax.text(6.6, 0.15, r"Children are examined by increasing $C$ (ties: higher log-probability first) until $B$ are kept;"
            "\n" r"incumbent = best complete schedule found so far ($C = 54$).", ha="center", va="bottom",
            fontsize=F - 1.5, color=SF.ENCRE_2)
    sauver(fig, "schema_methode_faisceau")


if __name__ == "__main__":
    SF.style()
    mdp()
    ensemble()
    reseau()
    faisceau()
