"""L'agent apprend de ses propres anticipations (itération experte avec recherche, principe d'AlphaZero).

  python -m imitation.auto_amelioration --init models/imitation/cand_ft_best.pt --out models/auto/cand --processus 10

À chaque tour :
  1. sur N NOUVELLES instances d'entraînement (générées, jamais les benchmarks), l'agent planifie
     en anticipant (faisceau de B pistes, K actions proposées par le réseau, moteur rapide) ;
  2. on garde le meilleur planning trouvé par cette recherche (jamais pire que l'agent seul) ;
  3. le réseau apprend à proposer directement les décisions de ces plannings (rejeu décision par
     décision, comme l'imitation) — seulement celles prises par la recherche, pas la fin du
     planning complétée par la règle du moteur (sauf --tout-apprendre) ; on garde les plannings
     des derniers tours (--memoire) ;
  4. on recommence avec le réseau amélioré : ses propositions sont meilleures, donc la recherche
     trouve mieux, donc la leçon suivante est meilleure.

Différence avec l'imitation du recuit : le professeur est l'agent lui-même + un peu de recherche.
Les plannings restent proches de ce qu'il sait faire et ne diffèrent qu'aux décisions où la
recherche a trouvé mieux : il apprend à corriger SES erreurs.

Mesures affichées à chaque tour :
  glouton_vs_recherche : C_max de l'agent seul / C_max de la recherche − 1, sur les instances du tour
                         (doit diminuer : le réseau « absorbe » la recherche) ;
  validation_glouton   : C_max moyen de l'agent seul sur la validation synthétique (24 instances) ;
  validation_recherche : idem avec anticipation (B, K) — c'est le critère du meilleur modèle.
Sorties : <out>_best.pt (meilleur en anticipation), <out>_best_glouton.pt, <out>_log.json,
          <out>_plannings.jsonl (tous les plannings de la recherche, pour reprise).
"""
import argparse, json, os, sys, time
import multiprocessing as mp
from types import SimpleNamespace
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train_v3 import val_set_v3
from jssp_pm.fjsp_env3 import FJSPEnv3, run3
from jssp_pm.fjsp_ppo import PPOPolicy
from jssp_pm.anticipation import AgentAnticipation
from jssp_pm.reseaux import charger_reseau, sauver_reseau
from imitation.experts import instance, lire
from imitation.entrainer import epoque

BASE_IDS = 2_000_000          # numéros des instances d'entraînement de cette boucle (jamais vues ailleurs)
_CACHE = {}


def _net(chemin):
    torch.set_num_threads(1)
    cle = (chemin, os.path.getmtime(chemin))
    if _CACHE.get("cle") != cle:
        _CACHE["net"], _CACHE["cle"] = charger_reseau(chemin), cle
    return _CACHE["net"]


def un_planning(args):
    """Agent seul + agent qui anticipe sur une instance d'entraînement -> meilleur planning."""
    i, regime, chemin, B, K, coupure = args
    net = _net(chemin)
    inst, dist = instance(i, regime)
    glouton = run3(FJSPEnv3("full", True), PPOPolicy(net), inst)[0]["cmax"]
    c, plan, st = AgentAnticipation(net, B, K).planifier(inst)
    return dict(i=i, regime=regime, dist=dist, cmax=float(c), cmax_glouton=float(glouton),
                evaluations=st["evaluations"], source="recherche", t_coupure=st["t_coupure"],
                apprendre_avant_coupure=coupure,
                planning=[[int(k), float(a), float(b), int(t), int(j)] for k, a, b, t, j in plan])


def une_validation(args):
    """Validation : agent seul et agent qui anticipe sur une instance de la validation synthétique."""
    v, regime, chemin, B, K = args
    net = _net(chemin)
    if _CACHE.get("V") is None:
        _CACHE["V"] = val_set_v3(regime)
    inst = _CACHE["V"][v]
    g = run3(FJSPEnv3("full", True), PPOPolicy(net), inst)[0]["cmax"]
    c, _, _ = AgentAnticipation(net, B, K).planifier(inst)
    return v, g, c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", required=True, help="modèle de départ (p. ex. models/imitation/cand_ft_best.pt)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--regime", default="A")
    ap.add_argument("--iterations", type=int, default=15)
    ap.add_argument("--instances", type=int, default=500, help="nouvelles instances par tour")
    ap.add_argument("--largeur", type=int, default=5)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--memoire", type=int, default=3, help="nombre de tours dont on garde les plannings")
    ap.add_argument("--epoques", type=int, default=2, help="passes d'apprentissage par tour")
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--lot", type=int, default=256)
    ap.add_argument("--bloc", type=int, default=32)
    ap.add_argument("--poids-valeur", type=float, default=0.5)
    ap.add_argument("--tout-apprendre", action="store_true",
                    help="apprendre aussi les décisions de la règle du moteur (fin des plannings)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--processus", type=int, default=2)
    a = ap.parse_args()
    torch.manual_seed(a.seed)
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    rng = np.random.default_rng(a.seed)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    env = FJSPEnv3("full", safety=(a.regime == "A"))
    net = charger_reseau(a.init)
    opt = torch.optim.Adam(net.parameters(), lr=a.lr)
    courant = a.out + "_courant.pt"
    fichier_plans = a.out + "_plannings.jsonl"
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    cfg = SimpleNamespace(regime=a.regime, bloc=a.bloc, lot=a.lot, poids_valeur=a.poids_valeur)
    log, t0 = [], time.time()
    meilleur = meilleur_g = np.inf

    def valider(pool):
        sauver_reseau(net, courant)
        res = list(pool.imap_unordered(une_validation, [(v, a.regime, courant, a.largeur, a.k) for v in range(24)]))
        return float(np.mean([r[1] for r in res])), float(np.mean([r[2] for r in res]))

    # plannings déjà calculés (reprise après interruption)
    anciens = lire(fichier_plans)
    par_tour = {}
    for r in anciens:
        par_tour.setdefault(r["tour"], []).append(r)
    with ctx.Pool(a.processus) as pool:
        g, c = valider(pool)
        meilleur, meilleur_g = c, g
        sauver_reseau(net, a.out + "_best.pt")
        sauver_reseau(net, a.out + "_best_glouton.pt")
        log.append(dict(tour=0, validation_glouton=round(g, 2), validation_recherche=round(c, 2)))
        print(json.dumps(log[-1], ensure_ascii=False), flush=True)
        for it in range(1, a.iterations + 1):
            # 1) recherche sur de nouvelles instances
            if it in par_tour and len(par_tour[it]) >= a.instances:
                nouveaux = par_tour[it][:a.instances]
            else:
                sauver_reseau(net, courant)
                ids = [BASE_IDS + 100_000 * a.seed + it * a.instances + q for q in range(a.instances)]
                nouveaux = list(pool.imap_unordered(un_planning, [(i, a.regime, courant, a.largeur, a.k, not a.tout_apprendre)
                                                                for i in ids]))
                with open(fichier_plans, "a", encoding="utf-8") as f:
                    for r in nouveaux:
                        r["tour"] = it
                        f.write(json.dumps(r) + "\n")
                par_tour[it] = nouveaux
            ecart = float(np.mean([r["cmax_glouton"] / r["cmax"] - 1 for r in nouveaux]))
            # 2) apprentissage sur les plannings des derniers tours
            recs = [r for t in range(max(1, it - a.memoire + 1), it + 1) for r in par_tour.get(t, [])]
            for _ in range(a.epoques):
                p, acc = epoque(net, opt, env, recs, rng, cfg)
            # 3) validation
            g, c = valider(pool)
            info = dict(tour=it, glouton_vs_recherche=round(ecart, 4), perte=round(p, 4), accord=round(acc, 4),
                        validation_glouton=round(g, 2), validation_recherche=round(c, 2),
                        minutes=round((time.time() - t0) / 60, 1))
            if c < meilleur:
                meilleur = c
                sauver_reseau(net, a.out + "_best.pt")
                info["meilleur"] = True
            if g < meilleur_g:
                meilleur_g = g
                sauver_reseau(net, a.out + "_best_glouton.pt")
                info["meilleur_glouton"] = True
            log.append(info)
            print(json.dumps(info, ensure_ascii=False), flush=True)
            json.dump(log, open(a.out + "_log.json", "w"), indent=1, ensure_ascii=False)
    print(f"meilleur modèle (anticipation) : {a.out}_best.pt, validation {meilleur:.2f}")
    print(f"meilleur modèle (agent seul)   : {a.out}_best_glouton.pt, validation {meilleur_g:.2f}")


if __name__ == "__main__":
    main()
