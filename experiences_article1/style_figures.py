"""Style commun des figures de l'article 1 (exemple de la section 3 et Gantt de la section Résultats).

Une seule source pour les couleurs et le dessin des Gantt, afin que toutes les figures se ressemblent.
Palette : catégorielle de référence (mode clair, validée par validate_palette.js, déjà utilisée par
figure_qualite_budget.py). Ordre fixe, jamais recyclé : au-delà de 8 jobs, toutes les opérations prennent
la couleur 1 et seul le numéro du job (écrit dans la barre) les distingue.
Maintenance : gris neutre hachuré (texture à 45°), lisible en impression noir et blanc.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

CATEGORIELLE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GRIS_PM = "#8a8984"
ENCRE = "#0b0b0b"
ENCRE_2 = "#52514e"
SURFACE = "#ffffff"
PROC, PM = 1, 2
TAILLE = 8   # taille de police par défaut (identique à figure_qualite_budget.py)


def style():
    plt.rcParams.update({"font.size": TAILLE, "axes.edgecolor": ENCRE_2, "axes.labelcolor": ENCRE,
                         "xtick.color": ENCRE_2, "ytick.color": ENCRE_2, "hatch.color": SURFACE,
                         "hatch.linewidth": 0.8, "pdf.fonttype": 42, "ps.fonttype": 42})


def couleur_job(j, n_jobs):
    return CATEGORIELLE[j] if n_jobs <= len(CATEGORIELLE) else CATEGORIELLE[0]


def depassements(segs, T):
    """Premier instant où l'usure cumulée de chaque machine dépasse son seuil (au-delà, la machine
    serait en panne : on ne marque donc que le premier franchissement)."""
    out = []
    for k in range(len(T)):
        c = 0.0
        for (kk, a, b, typ, j) in sorted([s for s in segs if s[0] == k], key=lambda s: s[1]):
            if typ == PM:
                c = 0.0
                continue
            if c + (b - a) > T[k] + 1e-9:
                out.append((k, a + max(T[k] - c, 0.0)))
                break
            c += b - a
    return out


def gantt(ax, segs, inst, titre=None, noms_ops=None, xmax=None, marquer_depassements=False, petite_police=None):
    """segs : liste (machine, début, fin, type, job) — type 1 = opération, 2 = maintenance.
    noms_ops : dict optionnel (machine, début) -> étiquette (ex. 'O$_{2,3}$') ; sinon numéro du job."""
    n_jobs = inst.n
    cmax = max(s[2] for s in segs if s[3] == PROC)
    for (k, a, b, typ, j) in segs:
        if typ == PM:
            b = min(b, cmax)     # une maintenance après la dernière opération ne compte pas (H7)
            if b <= a:
                continue
            ax.barh(k, b - a, left=a, height=0.62, color=GRIS_PM, edgecolor=SURFACE, linewidth=1.0,
                    hatch="////", zorder=2)
        else:
            ax.barh(k, b - a, left=a, height=0.62, color=couleur_job(j, n_jobs), edgecolor=SURFACE,
                    linewidth=1.0, zorder=2)
            lab = noms_ops.get((k, a)) if noms_ops else str(j + 1)
            if lab and b - a >= 1.5:
                ax.text((a + b) / 2, k, lab, ha="center", va="center", fontsize=TAILLE - 1, color=SURFACE, zorder=3)
            elif lab and petite_police and b - a >= 0.9:      # barres courtes (durée 1) : étiquette en petit
                ax.text((a + b) / 2, k, lab, ha="center", va="center", fontsize=petite_police, color=SURFACE, zorder=3)
    if marquer_depassements:
        for (k, t) in depassements(segs, inst.T):
            ax.plot([t, t], [k - 0.42, k + 0.42], color=ENCRE, lw=1.2, zorder=4)
            ax.plot(t, k - 0.47, marker="v", ms=5, color=ENCRE, zorder=4)
    ax.axvline(cmax, color=ENCRE_2, lw=0.8, ls=(0, (3, 2)), zorder=1)
    ax.set_yticks(range(inst.m))
    ax.set_yticklabels([f"Machine {k + 1}" for k in range(inst.m)])
    ax.set_ylim(inst.m - 0.5, -0.6)
    if xmax is not None:
        ax.set_xlim(0, xmax)
    ax.grid(axis="x", color="#e6e5e0", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if titre:
        ax.set_title(titre, loc="left", fontsize=TAILLE + 1, color=ENCRE)
    return cmax


def legende(fig, n_jobs, depassement=False, **kw):
    h = [Patch(color=couleur_job(j, n_jobs), label=f"Job {j + 1}") for j in range(min(n_jobs, len(CATEGORIELLE)))]
    h.append(Patch(facecolor=GRIS_PM, edgecolor=SURFACE, hatch="////", label="Maintenance"))
    if depassement:
        h.append(Line2D([], [], color=ENCRE, marker="v", lw=1.2, ms=5, label="Wear threshold first exceeded"))
    fig.legend(handles=h, frameon=False, ncol=len(h), **kw)
