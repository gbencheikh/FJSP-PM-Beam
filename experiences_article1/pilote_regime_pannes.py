"""Pilote go/no-go : la prise de risque (laisser tomber en panne) a-t-elle un contenu en déterministe ?

Seuils CONNUS, pannes PERMISES. Politique de maintenance « seuil de décision » θ : maintenance avant une
opération si c_k + p > θ·T_k. θ = 1 : prévention stricte (aucune panne si T_k >= p) ; θ > 1 : on laisse
l'usure franchir T_k, d'où une panne (op arrêtée au seuil, réparation R_k, reprise, usure remise à 0) ;
θ = inf : jamais de maintenance (fonctionnement jusqu'à la panne).
Objectif J_β = C_max + β·u·N_pannes (u = durée moyenne minimale d'une opération).

Pour chaque instance, β et θ :
  - règle : MWKR + EFT (moteur rapide) ;
  - recuit : recuit simulé sur (ordre, machines), objectif J_β, N évaluations, départ = règle.
Le θ retenu par β (meilleur J) dit s'il y a basculement prévention ↔ risque.

Deux jeux de seuils : « A » (protocole de l'article, T_k >= plus longue option : une panne n'est jamais
forcée) et « B » (protocole « stress » du code : seuils plus bas, options plus longues que T_k gardées).

  python -m experiences_article1.pilote_regime_pannes --evaluations 20000
"""
import argparse, csv, math, os, sys, time
import numpy as np
try:                                   # console Windows (cp1252) : ne pas planter sur « − », « ≤ »…
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ICI))
from metaheuristiques.instances import charger_instances
from jssp_pm.moteur_rapide import MoteurRapide, _decoder_etat, _voisin
from jssp_pm.fjsp_env3 import FJSPEnv3

INSTANCES = ["BrandimarteMk1", "BrandimarteMk4", "BrandimarteMk7", "BrandimarteMk10", "HurinkVdata4"]
THETAS = [1.0, 1.25, 1.5, 2.0, math.inf]
REPAIR, PM = 3, 2


def evaluer(mr, e, OS, MS, plan):
    cpt = np.zeros(1, np.int64)
    c = _decoder_etat(e.mf, e.us, e.cyc, e.jr, e.nxt, mr.jdeb, mr.ops, OS, MS, mr.P, mr.Tpol,
                      mr.Treel, mr.Mdur, mr.R, plan, cpt)
    typ = plan[:cpt[0], 3]
    return c, int((typ == REPAIR).sum()), int((typ == PM).sum())


def recuit(mr, e, OS, MS, beta, u, n_eval, graine, p0=0.05, ratio_fin=1e-3):
    rng_seed = np.random.seed(graine)
    plan = np.zeros((20 * mr.inst.n_ops + 8 * mr.inst.m + 16, 5))
    elig, deb, nb = mr._eligibles()
    rem = np.array([mr.ops[mr.jdeb[j] + q] for j in range(mr.inst.n) for q in range(e.nxt[j], mr.jnb[j])],
                   dtype=np.int64)
    J = lambda r: r[0] + beta * u * r[1]
    cur = evaluer(mr, e, OS, MS, plan)
    best, bOS, bMS = cur, OS.copy(), MS.copy()
    OS2, MS2 = OS.copy(), MS.copy()
    d = []
    for _ in range(30):
        if _voisin(OS, MS, rem, elig, deb, nb, OS2, MS2):
            x = J(evaluer(mr, e, OS2, MS2, plan)) - J(cur)
            if x > 0:
                d.append(x)
    T0 = (np.mean(d) if d else 1.0) / -np.log(p0)
    it = 0
    while it < n_eval:
        if not _voisin(OS, MS, rem, elig, deb, nb, OS2, MS2):
            continue
        it += 1
        r = evaluer(mr, e, OS2, MS2, plan)
        delta = J(r) - J(cur)
        if delta <= 0 or np.random.random() < math.exp(-delta / max(T0 * ratio_fin ** (it / n_eval), 1e-12)):
            OS, OS2 = OS2.copy(), OS
            MS, MS2 = MS2.copy(), MS
            cur = r
            if J(r) < J(best):
                best, bOS, bMS = r, OS.copy(), MS.copy()
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluations", type=int, default=20000)
    ap.add_argument("--betas", type=float, nargs="+", default=[0.5, 2.0])
    ap.add_argument("--jeux", nargs="+", default=["A", "B"])
    ap.add_argument("--rho", type=float, default=6.0, help="R_k = ρ·u (protocole : 6) ; diagnostic de sensibilité")
    ap.add_argument("--graines", type=int, nargs="+", default=[0])
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats", "pilote_regime_pannes.csv"))
    a = ap.parse_args()
    lignes = []
    for jeu in a.jeux:
        from metaheuristiques.instances import fichiers, PARAMS
        from jssp_pm.fjsp_instance import load_fjs_v3
        insts = {}
        for f in fichiers(["Brandimarte", "HurinkVdataLa"]):
            if os.path.exists(os.path.join(os.path.dirname(ICI), f)):
                i = load_fjs_v3(os.path.join(os.path.dirname(ICI), f), jeu, rho=a.rho, **PARAMS[jeu])
                insts[i.name] = i
        for nom in INSTANCES:
            if nom not in insts:
                continue
            inst = insts[nom]
            u = float(inst.meta["u"])
            risquees = int(inst.meta.get("risky_options", 0))
            for theta in THETAS:
                mr = MoteurRapide(inst, Tpol=inst.T * theta, Treel=inst.T[:, None])
                env = FJSPEnv3("full", safety=False)
                env.reset(inst)
                e = mr.etat(env)
                c0, segs = mr.completer(e, avec_planning=True)
                OS, MS = mr.suite_depuis_planning(e, segs)
                plan = np.zeros((20 * inst.n_ops + 8 * inst.m + 16, 5))
                regle = evaluer(mr, e, OS, MS, plan)
                for beta in a.betas:
                    for g in a.graines:
                        t0 = time.time()
                        r = recuit(mr, e, OS.copy(), MS.copy(), beta, u, a.evaluations, g)
                        for meth, res in (("MWKR+EFT", regle), ("Recuit", r)):
                            lignes.append(dict(rho=a.rho, jeu=jeu, instance=nom, R_sur_M=float(inst.R[0] / inst.M[0]),
                                               options_risquees=risquees, beta=beta, theta=theta, methode=meth,
                                               graine=g, cmax=res[0], pannes=res[1], maintenances=res[2],
                                               J=res[0] + beta * u * res[1], u=u))
                        print(f"{jeu} {nom} θ={theta} β={beta}: règle C={regle[0]:g} N={regle[1]} PM={regle[2]} | "
                              f"recuit C={r[0]:g} N={r[1]} PM={r[2]} J={r[0] + beta * u * r[1]:.1f} "
                              f"({time.time() - t0:.0f} s)", flush=True)
    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    with open(a.sortie, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0])); w.writeheader(); w.writerows(lignes)
    # synthèse : meilleur θ par (jeu, instance, β, méthode)
    print("\nMeilleur θ (J minimal) :")
    cle = lambda l: (l["jeu"], l["instance"], l["beta"], l["methode"])
    for k in sorted({cle(l) for l in lignes}):
        grp = [l for l in lignes if cle(l) == k]
        b = min(grp, key=lambda l: l["J"])
        p1 = next(l for l in grp if l["theta"] == 1.0)
        print(f"  {k}: θ*={b['theta']} J={b['J']:.1f} (pannes {b['pannes']}, PM {b['maintenances']}) ; "
              f"prévention stricte J={p1['J']:.1f} (pannes {p1['pannes']}) ; gain du risque {100 * (1 - b['J'] / p1['J']):.2f} %")


if __name__ == "__main__":
    main()
