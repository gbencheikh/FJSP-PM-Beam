"""Gantt de la section Résultats : plannings de quatre méthodes sur une même instance (régime A).

Les plannings sont CALCULÉS par le code du projet au moment de l'exécution (option --banque pour les relire
dans la banque à la place) :
  (a) politique seule, glouton             comparer_rl.executer_agent (réseau models/imitation/cand_ft_best.pt)
  (b) politique + faisceau 50 x 5           jssp_pm.anticipation.AgentAnticipation (même réseau)
  (c) recuit simulé, 50 000 évaluations     metaheuristiques.comparer.une_execution (paramètres Taguchi, graine 0,
                                            départ MWKR+EFT) — identique à la campagne E2
  (d) CP-SAT, 600 s (E9)                   relu dans la banque par défaut : le recalcul demande 600 s et, en temps
                                            court, CP-SAT laisse des maintenances inutiles (deuxième phase non terminée).
                                            Avec --cpsat S : jssp_pm.fjsp_cpsat.solve (segments « valide », 2 fils),
                                            démarré à chaud depuis le meilleur des plannings (a)-(c), comme dans E9.
Chaque planning est vérifié par outils/verifier_planning.py et comparé à la valeur de la banque (contrôle de
reproductibilité, affiché à l'écran et écrit dans le .json).

  python -m experiences_article1.figure_gantt_resultats                       # instance BrandimarteMk1
  python -m experiences_article1.figure_gantt_resultats --cpsat 600                # recalcule aussi CP-SAT
  python -m experiences_article1.figure_gantt_resultats --banque              # relire la banque, sans calcul
  -> resultats/gantt_resultats_<instance>.pdf|png|json
"""
import argparse, json, os, sys, time

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE)
from banque_resultats import banque                                    # noqa: E402
from metaheuristiques.instances import charger_instances               # noqa: E402
from outils.verifier_planning import verifier                          # noqa: E402
from experiences_article1 import style_figures as SF                   # noqa: E402

MODELE = os.path.join(RACINE, "models", "imitation", "cand_ft_best.pt")
TAGUCHI = os.path.join(RACINE, "reglage_taguchi", "parametres_retenus.json")
SA = ("Recuit simulé", "evals=50000,depart=heuristique,params=taguchi")


def calculer(inst, cpsat_s=None):
    """Les quatre plannings, calculés par le code du projet."""
    import torch
    from jssp_pm.reseaux import charger_reseau
    from jssp_pm.anticipation import AgentAnticipation
    from jssp_pm import fjsp_cpsat as CP
    from comparer_rl import executer_agent
    from metaheuristiques.comparer import une_execution
    torch.set_num_threads(1)
    net = charger_reseau(MODELE)
    out = []
    t0 = time.time()
    _, segs, _ = executer_agent(inst, net, "A")
    out.append(("(a) Policy, greedy", ("RL:imit-ft", "glouton"), list(segs), time.time() - t0))
    t0 = time.time()
    _, segs, _ = AgentAnticipation(net, 50, 5).planifier(inst)
    out.append(("(b) Policy + beam search 50 $\\times$ 5", ("RL:imit-ft", "faisceau=50,k=5"), list(segs), time.time() - t0))
    params = json.load(open(TAGUCHI, encoding="utf-8"))
    t0 = time.time()
    r = une_execution((inst, SA[0], 0, None, 50000, "heuristique", params.get(SA[0], {})))
    out.append(("(c) Simulated annealing, 50,000 evaluations", SA, list(r[6]), time.time() - t0))
    if not cpsat_s:                                   # (d) relu dans la banque (E9, 600 s)
        out.append(relire(inst)[3])
        return out
    depart = min((o[2] for o in out), key=lambda sg: max(x[2] for x in sg if x[3] == 1))
    t0 = time.time()
    rc = CP.solve(inst, time_limit=cpsat_s, workers=2, segments="valide", graine=0, hint=depart)
    statut = "optimal" if rc["status"] == "OPTIMAL" else f"{cpsat_s:g} s, bound {rc['bound']:g}"
    out.append((f"(d) CP-SAT, warm start ({statut})", ("CP-SAT", None), list(rc["segments"]), time.time() - t0))
    return out


def relire(inst):
    """Les quatre plannings, relus dans la banque (aucun calcul)."""
    lignes = [r for r in banque.charger() if r["instance"] == inst.name and r["regime"] == "A"
              and r["facteur_seuil"] == "1" and r.get("solution") and r["graine"] == "0"]
    out = []
    for titre, (m, c) in [("(a) Policy, greedy", ("RL:imit-ft", "glouton")),
                          ("(b) Policy + beam search 50 $\\times$ 5", ("RL:imit-ft", "faisceau=50,k=5")),
                          ("(c) Simulated annealing, 50,000 evaluations", SA),
                          ("(d) CP-SAT, 600 s", ("CP-SAT", None))]:
        r = [x for x in lignes if x["methode"] == m and (c is None or x["config"] == c)][0]
        out.append((titre + " (proven optimum)" if m == "CP-SAT" and est_optimum(inst.name, float(r["cmax"])) else titre,
                    (m, c), [tuple(s) for s in banque.planning(r)], 0.0))
    return out


def est_optimum(nom, cmax):
    """Optimum prouvé selon resultats/meilleurs_connus_article.csv (régime A)."""
    import csv
    f = os.path.join(ICI, "resultats", "meilleurs_connus_article.csv")
    if not os.path.exists(f):
        return False
    for r in csv.DictReader(open(f, encoding="utf-8")):
        if r["instance"] == nom and r["regime"] == "A":
            return r["statut"] == "optimum prouvé" and abs(float(r["meilleur_cmax"]) - cmax) < 1e-9
    return False


def valeur_banque(nom, m, c):
    v = [float(r["cmax"]) for r in banque.charger() if r["instance"] == nom and r["regime"] == "A"
         and r["facteur_seuil"] == "1" and r["methode"] == m and (c is None or r["config"] == c) and r["graine"] == "0"]
    return v[0] if v else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", default="BrandimarteMk1")
    ap.add_argument("--cpsat", type=float, default=None,
                    help="recalculer CP-SAT avec cette limite (s) ; par défaut, planning CP-SAT 600 s relu dans la banque")
    ap.add_argument("--banque", action="store_true", help="relire les plannings dans la banque au lieu de les calculer")
    a = ap.parse_args()
    inst = [i for i in charger_instances(["Brandimarte", "HurinkLa", "Kacem"], regime="A") if i.name == a.instance][0]
    plans = relire(inst) if a.banque else calculer(inst, a.cpsat)

    res, lignes = {}, []
    for titre, (m, c), segs, t in plans:
        segs = [(int(k), float(x), float(y), int(ty), int(j)) for k, x, y, ty, j in segs]
        cmax = verifier(inst, segs)
        n_pm = sum(1 for s in segs if s[3] == SF.PM and s[1] < cmax)
        ref = valeur_banque(inst.name, m, c)
        res[titre] = dict(methode=m, config=c, cmax=cmax, maintenances=n_pm, temps_s=round(t, 2),
                          cmax_banque=ref, segments=segs)
        lignes.append((titre, segs, cmax, n_pm))
        print(f"{titre}: Cmax = {cmax:g}, {n_pm} maintenances, {t:.1f} s ; banque : {ref}")
    base = os.path.join(ICI, "resultats", f"gantt_resultats_{inst.name}")
    json.dump(dict(instance=inst.name, source="banque" if a.banque else "calcul", T=[int(x) for x in inst.T],
                   M=[int(x) for x in inst.M], plannings=res),
              open(base + ".json", "w", encoding="utf-8"), indent=1, default=float)

    SF.style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    xmax = max(p[2] for p in lignes) + 1
    fig, axes = plt.subplots(len(lignes), 1, figsize=(6.4, 1.45 * len(lignes) + 0.5), sharex=True)
    for ax, (titre, segs, cmax, n_pm) in zip(axes, lignes):
        SF.gantt(ax, segs, inst, titre=f"{titre}: $C_{{\\max}}$ = {cmax:g}, {n_pm} maintenances", xmax=xmax, petite_police=SF.TAILLE - 3.5)
        ax.set_yticklabels([f"M{k + 1} ($T$ = {int(inst.T[k])})" for k in range(inst.m)])
    axes[-1].set_xlabel("Time")
    if inst.n > len(SF.CATEGORIELLE):
        h = [Patch(color=SF.couleur_job(0, inst.n), label="Operation (job number in the bar)"),
             Patch(facecolor=SF.GRIS_PM, edgecolor=SF.SURFACE, hatch="////", label="Preventive maintenance")]
        fig.legend(handles=h, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.005))
    else:
        SF.legende(fig, inst.n, loc="lower center", bbox_to_anchor=(0.5, -0.005))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=200)
    print("->", base + ".pdf")


if __name__ == "__main__":
    main()
