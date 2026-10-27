"""Figure de la section 4.5 (Proposition 2, complétude de l'espace d'actions) : les trois étapes de la preuve.

Exemple fictif (aucune donnée expérimentale), 2 jobs x 2 machines, chaque opération a une seule machine éligible :
  O_{1,1} sur M1 (p=4), O_{1,2} sur M2 (p=4), O_{2,1} sur M1 (p=7), O_{2,2} sur M2 (p=2) ;
  T_1 = T_2 = 10, maintenance de durée 2.  Sur M1, 4 + 7 > 10 : une maintenance est nécessaire entre O_{1,1}
  et O_{2,1}. C_max optimal = 15 (vérifié ci-dessous par énumération des ordres sur chaque machine).
(a) Planning optimal de départ : maintenance à usure nulle (M2, t=0), maintenance après la dernière opération
    (M1, t=13), trou inutile avant O_{1,2} (début 8 au lieu de 4). C_max = 15.
(b) Étape 1 : les deux maintenances inutiles sont retirées.
(c) Étape 2 : décalage à gauche, O_{1,2} passe de 8 à 4. C_max inchangé.
(d) Étape 3 : rejeu ; chaque début est une époque de décision (0, 4, 6, 13) ; à 8 (fin de O_{1,2}), seul wait.
Style commun : style_figures.py.

  python -m experiences_article1.figure_preuve_completude   # -> resultats/schema_preuve_completude.pdf|png
"""
import os, sys, itertools
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF   # noqa: E402

F = SF.TAILLE - 1
M, T = 2, 10
P = {(1, 1): 4, (1, 2): 4, (2, 1): 7, (2, 2): 2}          # (job, rang) -> durée
MACH = {(1, 1): 0, (1, 2): 1, (2, 1): 0, (2, 2): 1}       # machine (0 = Machine 1)


def verifier_optimum():
    """Énumère les ordres sur chaque machine (planning semi-actif, maintenance insérée au plus tard dès que
    l'opération suivante dépasserait T). Le minimum doit valoir 15."""
    best = None
    for o1 in itertools.permutations([(1, 1), (2, 1)]):
        for o2 in itertools.permutations([(1, 2), (2, 2)]):
            fin, libre, usure, ok = {}, [0, 0], [0, 0], True
            seqs = [list(o1), list(o2)]
            for _ in range(8):
                for k in (0, 1):
                    if not seqs[k]:
                        continue
                    o = seqs[k][0]
                    pred = (o[0], o[1] - 1)
                    if o[1] > 1 and pred not in fin:
                        continue
                    t = max(libre[k], fin.get(pred, 0))
                    if usure[k] + P[o] > T:
                        t, usure[k] = t + M, 0
                    fin[o] = t + P[o]
                    libre[k], usure[k] = fin[o], usure[k] + P[o]
                    seqs[k].pop(0)
            if len(fin) == 4:
                c = max(fin.values())
                best = c if best is None else min(best, c)
    assert best == 15, best
    return best


def op(ax, k, a, j, i, fantome=False):
    d = P[(j, i)]
    if fantome:
        ax.barh(k, d, left=a, height=0.55, fill=False, edgecolor=SF.ENCRE_2, lw=0.7, ls=(0, (2, 2)), zorder=2)
        return
    ax.barh(k, d, left=a, height=0.55, color=SF.CATEGORIELLE[j - 1], edgecolor=SF.SURFACE, lw=0.8, zorder=2)
    ax.text(a + d / 2, k, f"$O_{{{j},{i}}}$", ha="center", va="center", color=SF.SURFACE, fontsize=F, zorder=3)


def pm(ax, k, a, retiree=False):
    if retiree:
        ax.barh(k, M, left=a, height=0.55, fill=False, edgecolor=SF.ENCRE_2, lw=0.7, ls=(0, (2, 2)), zorder=2)
        ax.text(a + M / 2, k, "×", ha="center", va="center", color=SF.ENCRE_2, fontsize=SF.TAILLE + 2, zorder=3)
    else:
        ax.barh(k, M, left=a, height=0.55, color=SF.GRIS_PM, edgecolor=SF.SURFACE, lw=0.8, hatch="////", zorder=2)


def note(ax, x, k, txt, dy=0.62):
    ax.annotate(txt, xy=(x, k - 0.3), xytext=(x, k - dy), ha="center", va="bottom", fontsize=F,
                color=SF.ENCRE_2, arrowprops=dict(arrowstyle="->", color=SF.ENCRE_2, lw=0.7))


def axe(ax, titre, epoques=None):
    ax.axvline(15, color=SF.ENCRE_2, lw=0.8, ls=(0, (3, 2)), zorder=1)
    ax.text(15.15, 1.55, "$C_{\\max}=15$", ha="left", va="center", fontsize=F, color=SF.ENCRE_2)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Machine 1", "Machine 2"])
    ax.set_xlim(-0.3, 17.5)
    ax.set_ylim(1.75, -1.25)
    ax.set_xticks(epoques if epoques else [0, 5, 10, 15])
    ax.grid(axis="x", color="#e6e5e0", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title(titre, loc="left", fontsize=SF.TAILLE, color=SF.ENCRE)


def base(ax, o12=4):
    op(ax, 0, 0, 1, 1); pm(ax, 0, 4); op(ax, 0, 6, 2, 1)
    op(ax, 1, o12, 1, 2); op(ax, 1, 13, 2, 2)


def main():
    verifier_optimum()
    SF.style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    fig, axs = plt.subplots(4, 1, figsize=(6.6, 6.9), sharex=False)

    ax = axs[0]                                    # (a) planning optimal de départ
    base(ax, o12=8); pm(ax, 1, 0); pm(ax, 0, 13)
    ax.text(2.2, 1, "← maintenance at zero wear", ha="left", va="center", fontsize=F, color=SF.ENCRE_2)
    note(ax, 14, 0, "no operation after")
    ax.annotate("", xy=(4, 1.36), xytext=(8, 1.36), arrowprops=dict(arrowstyle="<->", color=SF.ENCRE_2, lw=0.7))
    ax.text(6, 1.6, "idle gap", ha="center", va="center", fontsize=F, color=SF.ENCRE_2)
    axe(ax, "(a) An optimal schedule")

    ax = axs[1]                                    # (b) étape 1
    base(ax, o12=8); pm(ax, 1, 0, retiree=True); pm(ax, 0, 13, retiree=True)
    note(ax, 7.5, 0, "the maintenance before $O_{2,1}$ is kept: $4+7 > T_1$")
    axe(ax, "(b) Step 1: useless maintenances removed")

    ax = axs[2]                                    # (c) étape 2
    base(ax, o12=4); op(ax, 1, 8, 1, 2, fantome=True)
    ax.annotate("", xy=(4.1, 0.62), xytext=(8.1, 0.62), arrowprops=dict(arrowstyle="->", color=SF.ENCRE, lw=0.9))
    ax.text(4, 1.5, "$O_{1,2}$ now starts at the completion of $O_{1,1}$", ha="left", va="center",
            fontsize=F, color=SF.ENCRE_2)
    axe(ax, "(c) Step 2: activities shifted to the left")

    ax = axs[3]                                    # (d) étape 3
    base(ax, o12=4)
    actions = {0: "launch (1,1)\nwait", 4: "maintain 1\nlaunch (1,2)\nwait", 6: "launch (2,1)\nwait",
               8: "wait", 13: "launch (2,2)\nwait"}
    for t, txt in actions.items():
        ax.axvline(t, color=SF.ENCRE, lw=0.7, ls=(0, (1, 1.5)), zorder=1)
        ax.text(t + 0.12, -0.42, txt, ha="left", va="bottom", fontsize=F - 0.5, color=SF.ENCRE, linespacing=1.05)
    axe(ax, "(d) Step 3: replay at the decision epochs", epoques=[0, 4, 6, 8, 13, 15])
    ax.set_ylim(1.75, -1.55)
    ax.set_xlabel("Time ($T_1 = T_2 = 10$, maintenance duration 2)")

    h = [Patch(color=SF.CATEGORIELLE[0], label="Job 1"), Patch(color=SF.CATEGORIELLE[1], label="Job 2"),
         Patch(facecolor=SF.GRIS_PM, edgecolor=SF.SURFACE, hatch="////", label="Maintenance"),
         Patch(fill=False, edgecolor=SF.ENCRE_2, linestyle=(0, (2, 2)), label="Removed or former position")]
    fig.legend(handles=h, frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.005), fontsize=F)
    fig.tight_layout(rect=(0, 0.035, 1, 1), h_pad=0.9)
    out = os.path.join(ICI, "resultats", "schema_preuve_completude")
    fig.savefig(out + ".pdf")
    fig.savefig(out + ".png", dpi=200)
    print("ok", out)


if __name__ == "__main__":
    main()
