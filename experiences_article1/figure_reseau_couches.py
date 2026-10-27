"""Figure 5.1 de l'article 1 : architecture du réseau de politique, couche par couche (demande de Ghita, 21/10/2026).

Remplace dans l'article schema_methode_reseau (figures_methode.py, conservé). Architecture lue dans
jssp_pm/fjsp_ppo.py (CandNet, h = 128 ; mlp(i, h, o, depth) = depth x [Linear, Tanh] + Linear) :
  phi_c = mlp(33, 128, 128, 1) puis tanh -> e_a     phi_g = mlp(19, 128, 128, 1) puis tanh -> e_g
  ē = moyenne des e_a sur A(s) (masquée)
  psi : Linear(384 -> 128) [= psi_c(e_a) + psi_gp([e_g, ē]), sans biais pour psi_gp], Tanh, Linear(128, 128), Tanh, Linear(128, 1)
  nu  = mlp(256, 128, 1, 2) : Linear(256, 128), Tanh, Linear(128, 128), Tanh, Linear(128, 1)
Le nombre de paramètres est calculé ci-dessous à partir de ces couches (torch absent de cette machine).
Style commun : style_figures.py.

  python -m experiences_article1.figure_reseau_couches   # -> resultats/schema_reseau_couches.pdf|png
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF   # noqa: E402
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, FancyBboxPatch

F = SF.TAILLE - 0.5
H = 128
# couches linéaires (entrée, sortie, biais) par module, d'après fjsp_ppo.py
COUCHES = {
    "phi_c": [(33, H, 1), (H, H, 1)],
    "phi_g": [(19, H, 1), (H, H, 1)],
    "psi": [(H, H, 1), (2 * H, H, 0), (H, H, 1), (H, 1, 1)],     # psi_c, psi_gp (sans biais), psi_out
    "nu": [(2 * H, H, 1), (H, H, 1), (H, 1, 1)],
}


def n_parametres():
    par = {k: sum(i * o + b * o for i, o, b in v) for k, v in COUCHES.items()}
    return par, sum(par.values())


COUL = {"in": "#ecebe8", "fc": "#d6e6f8", "emb": SF.CATEGORIELLE[0], "pool": "#d3f0e4", "out": "#fbe0d4"}


def hauteur(d):
    return 0.32 * d ** 0.4


def bloc(ax, x, y, d, kind, w=0.42, ls="-", z=3):
    """Couche dessinée en pseudo-3D, centrée verticalement en y ; hauteur croissante avec la dimension d."""
    h = hauteur(d)
    dx, dy = 0.22, 0.16
    fc = COUL[kind]
    ax.add_patch(Polygon([(x, y + h / 2), (x + dx, y + h / 2 + dy), (x + w + dx, y + h / 2 + dy), (x + w, y + h / 2)],
                         closed=True, fc=fc, ec=SF.ENCRE_2, lw=0.6, ls=ls, zorder=z, alpha=0.75))
    ax.add_patch(Polygon([(x + w, y - h / 2), (x + w + dx, y - h / 2 + dy), (x + w + dx, y + h / 2 + dy), (x + w, y + h / 2)],
                         closed=True, fc=fc, ec=SF.ENCRE_2, lw=0.6, ls=ls, zorder=z, alpha=0.55))
    ax.add_patch(Rectangle((x, y - h / 2), w, h, fc=fc, ec=SF.ENCRE_2, lw=0.7, ls=ls, zorder=z + 0.1))
    return x + w + dx, h


def legende_bloc(ax, x, y, h, haut, bas=None, w=0.42):
    ax.text(x + w / 2 + 0.11, y + h / 2 + 0.3, haut, ha="center", va="bottom", fontsize=F - 0.5, color=SF.ENCRE)
    if bas:
        ax.text(x + w / 2 + 0.11, y - h / 2 - 0.15, bas, ha="center", va="top", fontsize=F - 1, color=SF.ENCRE_2)


def fl(ax, x0, y0, x1, y1, ls="-"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=SF.ENCRE_2, lw=0.8, ls=ls,
                shrinkA=0, shrinkB=0, mutation_scale=7), zorder=1)


def ligne(ax, xs, ys, ls="-"):
    ax.plot(xs, ys, color=SF.ENCRE_2, lw=0.8, ls=ls, zorder=1)


def branche(ax, x, y, d_in, nom_in, nom_out, ombres=0):
    """Entrée -> FC+tanh -> FC+tanh -> embedding. Retourne l'abscisse de sortie."""
    for o in range(ombres, 0, -1):                     # copies décalées : même réseau pour chaque action
        xx = x + 0.12 * o
        yy = y + 0.12 * o
        for (xi, d, k) in ((xx, d_in, "in"), (xx + 2.0, H, "fc"), (xx + 4.0, H, "fc"), (xx + 6.0, H, "emb")):
            bloc(ax, xi, yy, d, k, ls=(0, (2, 2)), z=2 - 0.1 * o)
    x1, h = bloc(ax, x, y, d_in, "in")
    legende_bloc(ax, x, y, h, nom_in, f"{d_in}")
    fl(ax, x1, y, x + 2.0, y)
    x2, h = bloc(ax, x + 2.0, y, H, "fc")
    legende_bloc(ax, x + 2.0, y, h, "FC\ntanh", f"{d_in}→{H}")
    fl(ax, x2, y, x + 4.0, y)
    x3, h = bloc(ax, x + 4.0, y, H, "fc")
    legende_bloc(ax, x + 4.0, y, h, "FC\ntanh", f"{H}→{H}")
    fl(ax, x3, y, x + 6.0, y)
    x4, h = bloc(ax, x + 6.0, y, H, "emb")
    legende_bloc(ax, x + 6.0, y, h, nom_out, f"{H}")
    return x4


def tete(ax, x, y, d_in, sortie, segments, pointilles=False):
    """Concaténation (segments colorés) -> FC+tanh -> FC+tanh -> FC -> sortie."""
    ls = (0, (3, 2)) if pointilles else "-"
    h = hauteur(d_in)
    n = len(segments)
    w = 0.42
    for i, lab in enumerate(segments):                 # concaténation : un segment par vecteur
        y0 = y + h / 2 - (i + 1) * h / n
        ax.add_patch(Rectangle((x, y0), w, h / n, fc=COUL["emb"], ec=SF.SURFACE, lw=0.8, zorder=3, alpha=0.9 - 0.2 * i))
        ax.text(x - 0.08, y0 + h / (2 * n), lab, ha="right", va="center", fontsize=F - 1, color=SF.ENCRE)
    ax.add_patch(Rectangle((x, y - h / 2), w, h, fill=False, ec=SF.ENCRE_2, lw=0.7, ls=ls, zorder=4))
    ax.text(x + w / 2, y + h / 2 + 0.3, "concat", ha="center", va="bottom", fontsize=F - 0.5, color=SF.ENCRE)
    ax.text(x + w / 2, y - h / 2 - 0.15, f"{d_in}", ha="center", va="top", fontsize=F - 1, color=SF.ENCRE_2)
    xs = x + w
    pas = 2.2
    for i, (din, dout, nom) in enumerate([(d_in, H, "FC\ntanh"), (H, H, "FC\ntanh"), (H, 1, "FC")]):
        fl(ax, xs if i == 0 else xe, y, x + pas * (i + 1), y, ls=ls)
        xe, hh = bloc(ax, x + pas * (i + 1), y, dout if dout > 1 else 1, "fc" if dout > 1 else "out", ls=ls)
        legende_bloc(ax, x + pas * (i + 1), y, hh, nom, f"{din}→{dout}")
    fl(ax, xe, y, xe + 0.45, y, ls=ls)
    ax.text(xe + 0.5, y, sortie, ha="left", va="center", fontsize=F + 0.5, color=SF.ENCRE)
    return h, xe


def groupe(ax, x, y, w, h, titre, ls="-"):
    """Cadre d'un des cinq composants du réseau, titre en haut à gauche."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.2", fc="#f7f7f5",
                                ec="#b9b8b3", lw=0.8, ls=ls, zorder=0))
    ax.text(x + 0.2, y + h - 0.12, titre, ha="left", va="top", fontsize=F, color=SF.ENCRE, fontweight="bold", zorder=5)


def main():
    SF.style()
    par, total = n_parametres()
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    ax.set_xlim(-0.3, 27.2)
    ax.set_ylim(-0.35, 11.6)
    ax.axis("off")
    ya, yp, yg = 8.0, 5.2, 2.0                          # lignes : actions, moyenne, état

    xa = branche(ax, 0.6, ya, 33, "$x_a$", "$e_a$", ombres=2)
    groupe(ax, -0.15, ya - 1.95, 7.75, 5.4, r"(i) Action encoder $\phi_c$")
    ax.text(0.05, ya + 2.85, r"same weights for every $a \in \mathcal{A}(s)$", ha="left", va="top", fontsize=F - 1, color=SF.ENCRE_2, zorder=5)
    xg = branche(ax, 0.6, yg, 19, "$x_g$", "$e_g$")
    groupe(ax, -0.15, yg - 1.95, 7.75, 4.6, r"(ii) State encoder $\phi_g$")

    # moyenne sur A(s)
    xm = 8.0
    groupe(ax, xm - 0.25, yp - 1.85, 3.75, 4.6, "(iii) Aggregation")
    ligne(ax, [xa - 0.05, xa + 0.25, xa + 0.25], [ya - 0.6, ya - 0.6, yp + 0.55])
    fl(ax, xa + 0.25, yp + 0.55, xm, yp + 0.2)
    ax.add_patch(FancyBboxPatch((xm, yp - 0.55), 1.7, 1.1, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=COUL["pool"], ec=SF.ENCRE_2, lw=0.7, zorder=3))
    ax.text(xm + 0.85, yp, "mean\nover $\\mathcal{A}(s)$", ha="center", va="center", fontsize=F - 1.5, zorder=4)
    fl(ax, xm + 1.7, yp, xm + 2.2, yp)
    xe_, h = bloc(ax, xm + 2.2, yp, H, "emb")
    legende_bloc(ax, xm + 2.2, yp, h, r"$\bar e$", f"{H}")

    # têtes
    xt = 13.4
    hp, xfin = tete(ax, xt, ya, 3 * H, r"$z_\theta(s,a)$", [r"$e_a$", r"$\bar e$", r"$e_g$"])
    hv, _ = tete(ax, xt, yg, 2 * H, r"$V_\theta(s)$", [r"$\bar e$", r"$e_g$"], pointilles=True)
    groupe(ax, xt - 0.95, ya - 2.4, 27.0 - (xt - 0.95), 5.85, r"(iv) Policy head $\psi$")
    groupe(ax, xt - 0.95, yg - 2.15, 23.4 - (xt - 0.95), 5.15, r"(v) Value head $\nu$ (training only)", ls=(0, (3, 2)))
    # e_a -> segment haut de la tête ψ
    fl(ax, xa, ya + hp / 3, xt - 0.65, ya + hp / 3)
    # ē -> segments (milieu de ψ, haut de ν)
    xb = 12.2
    ligne(ax, [xe_, xb, xb], [yp, yp, ya])
    fl(ax, xb, ya, xt - 0.55, ya)
    ligne(ax, [xb, xb], [yp, yg + hv / 4])
    fl(ax, xb, yg + hv / 4, xt - 0.55, yg + hv / 4)
    # e_g -> segments (bas de ψ, bas de ν)
    xc = 11.75
    ligne(ax, [xg, xc, xc], [yg - hv / 4, yg - hv / 4, ya - hp / 3])
    fl(ax, xc, ya - hp / 3, xt - 0.55, ya - hp / 3)
    fl(ax, xc, yg - hv / 4, xt - 0.55, yg - hv / 4)
    # softmax, à droite du score
    xs0 = xfin + 3.3
    fl(ax, xs0 - 0.45, ya, xs0, ya)
    ax.add_patch(FancyBboxPatch((xs0, ya - 0.6), 2.6, 1.2, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=SF.CATEGORIELLE[0], ec=SF.CATEGORIELLE[0], lw=0.7, zorder=3))
    ax.text(xs0 + 1.3, ya, "softmax\n$\\pi_\\theta(a \\mid s)$", ha="center", va="center",
            fontsize=F - 1, color=SF.SURFACE, zorder=4)

    ax.text(27.0, 0.4, f"{total:,} parameters".replace(",", " "), ha="right", va="bottom", fontsize=F - 1,
            color=SF.ENCRE_2)
    out = os.path.join(ICI, "resultats", "schema_reseau_couches")
    fig.savefig(out + ".pdf", bbox_inches="tight")
    fig.savefig(out + ".png", dpi=220, bbox_inches="tight")
    print("ok", out, par, total)


if __name__ == "__main__":
    main()
