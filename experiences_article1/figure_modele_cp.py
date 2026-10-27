"""Figure de la section 3.2 (modèle CP) : segments, maintenances et usure d'une machine (demande de Ghita, 16/10/2026).

Exemple fictif (aucune donnée expérimentale) : une machine k, T_k = 10, M_k = 2, N_k = 4 segments.
  Segment 1 : O_{1,1} [0,4), O_{2,2} [5,10)       charge 9  ; maintenance y_{k,1} = 1, pi_{k,1} = 10
  Segment 2 : O_{3,1} [12,15), O_{1,3} [16,23)    charge 10 (= T_k, hypothèse v) ; y_{k,2} = 1, pi_{k,2} = 23
  Segment 3 : O_{2,3} [25,29)                     charge 4  ; y_{k,3} = 0
  Segment 4 : vide (contrainte cp:after : x_{.,k,4} = 1 imposerait y_{k,3} = 1)
Panneau haut : Gantt de la machine ; panneau bas : usure c_k(t) (croît pendant le traitement, constante à l'arrêt,
remise à zéro à la fin de la maintenance). Style commun : style_figures.py.

  python -m experiences_article1.figure_modele_cp   # -> resultats/schema_modele_cp.pdf|png
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from experiences_article1 import style_figures as SF   # noqa: E402

F = SF.TAILLE - 1
T, M = 10, 2
OPS = [(1, 1, 0, 4), (2, 2, 5, 10), (3, 1, 12, 15), (1, 3, 16, 23), (2, 3, 25, 29)]   # (job, rang, début, fin)
PMS = [10, 23]
SEGS = [(0, 10, 1, 9), (12, 23, 2, 10), (25, 29, 3, 4)]                                # (début, fin, s, charge)


def courbe_usure():
    evts = sorted([(a, b, "op") for (_, _, a, b) in OPS] + [(p, p + M, "pm") for p in PMS])
    xs, ys, c, t = [0], [0], 0, 0
    for a, b, typ in evts:
        xs.append(a); ys.append(c)
        if typ == "op":
            c += b - a
            xs.append(b); ys.append(c)
        else:
            xs.append(b); ys.append(c)
            c = 0
            xs.append(b); ys.append(c)
    xs.append(32); ys.append(c)
    return xs, ys


def main():
    SF.style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    fig, (ag, au) = plt.subplots(2, 1, figsize=(6.6, 3.5), sharex=True, gridspec_kw=dict(height_ratios=[1.25, 1]))

    # --- Gantt de la machine k
    for (j, i, a, b) in OPS:
        ag.barh(0, b - a, left=a, height=0.5, color=SF.CATEGORIELLE[j - 1], edgecolor=SF.SURFACE, lw=0.8, zorder=2)
        ag.text((a + b) / 2, 0, f"$O_{{{j},{i}}}$", ha="center", va="center", color=SF.SURFACE, fontsize=F, zorder=3)
    for s, p in enumerate(PMS, start=1):
        ag.barh(0, M, left=p, height=0.5, color=SF.GRIS_PM, edgecolor=SF.SURFACE, lw=0.8, hatch="////", zorder=2)
        ag.annotate(f"$\\pi_{{k,{s}}}$", xy=(p, 0.27), xytext=(p, 0.62), ha="center", va="center", fontsize=F,
                    color=SF.ENCRE_2, arrowprops=dict(arrowstyle="->", color=SF.ENCRE_2, lw=0.7))
        ag.text(p + M / 2, -0.33, f"$y_{{k,{s}}}=1$", ha="center", va="bottom", fontsize=F, color=SF.ENCRE_2)
    for (a, b, s, ch) in SEGS:
        y = -0.62
        ag.plot([a, a, b, b], [y + 0.08, y, y, y + 0.08], color=SF.ENCRE, lw=0.7)
        ag.text((a + b) / 2, y - 0.06, f"segment {s}: load ${ch}" + (r" = T_k$" if ch == T else r" \leq T_k$"),
                ha="center", va="bottom", fontsize=F, color=SF.ENCRE)
    ag.text(29.6, 0, "$y_{k,3}=0$: segment 4 empty", ha="left", va="center", fontsize=F, color=SF.ENCRE_2)
    ag.set_yticks([0]); ag.set_yticklabels(["Machine $k$"])
    ag.set_ylim(0.85, -1.05)
    for s_ in ("top", "right"):
        ag.spines[s_].set_visible(False)
    ag.grid(axis="x", color="#e6e5e0", lw=0.6, zorder=0); ag.set_axisbelow(True)

    # --- usure c_k(t)
    xs, ys = courbe_usure()
    au.plot(xs, ys, color=SF.ENCRE, lw=1.2, zorder=3)
    au.axhline(T, color=SF.CATEGORIELLE[7], lw=0.9, ls=(0, (3, 2)), zorder=2)
    au.text(0.2, T + 0.5, "threshold $T_k$", ha="left", va="bottom", fontsize=F, color=SF.CATEGORIELLE[7])
    for p in PMS:
        au.axvspan(p, p + M, color=SF.GRIS_PM, alpha=0.18, lw=0, zorder=1)
    au.annotate("reset at the end\nof the maintenance", xy=(25, 0.3), xytext=(27.0, 6.2), ha="left", va="center",
                fontsize=F, color=SF.ENCRE_2, arrowprops=dict(arrowstyle="->", color=SF.ENCRE_2, lw=0.7))
    au.set_ylabel("Wear $c_k$")
    au.set_ylim(-0.5, 12.5); au.set_yticks([0, 5, 10])
    au.set_xlim(-0.5, 36.5); au.set_xticks([0, 5, 10, 12, 15, 20, 23, 25, 29])
    au.set_xlabel("Time ($T_k = 10$, $M_k = 2$, $N_k = 4$)")
    for s_ in ("top", "right"):
        au.spines[s_].set_visible(False)
    au.grid(axis="x", color="#e6e5e0", lw=0.6, zorder=0); au.set_axisbelow(True)

    h = [Patch(color=SF.CATEGORIELLE[j], label=f"Job {j + 1}") for j in range(3)]
    h.append(Patch(facecolor=SF.GRIS_PM, edgecolor=SF.SURFACE, hatch="////", label="Maintenance"))
    fig.legend(handles=h, frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.01), fontsize=F)
    fig.tight_layout(rect=(0, 0.06, 1, 1), h_pad=0.4)
    out = os.path.join(ICI, "resultats", "schema_modele_cp")
    fig.savefig(out + ".pdf"); fig.savefig(out + ".png", dpi=200)
    print("ok", out)


if __name__ == "__main__":
    main()
