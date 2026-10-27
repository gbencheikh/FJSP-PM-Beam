"""Apprentissage par imitation des métaheuristiques, puis « itération experte » (pistes 2 + 4).

Étape 1 — imitation (clonage de comportement) :
  le réseau apprend à choisir, à chaque décision, l'action que l'expert (recuit simulé) a prise.
  python -m imitation.entrainer --reseau candidats --out models/imitation/cand
  python -m imitation.entrainer --reseau graphe    --out models/imitation/graphe

Étape 2 — itération experte (optionnelle, --iterations N) : à chaque tour,
  a) l'agent construit un planning sur de NOUVELLES instances d'entraînement ;
  b) le recuit simulé AMÉLIORE ce planning (départ = planning de l'agent) ;
  c) l'agent imite ces plannings améliorés, puis on recommence.
  L'agent apprend ainsi à corriger ses propres erreurs (il voit des situations qu'il crée
  lui-même, pas seulement celles de l'expert). L'écart « recuit − agent » mesuré à chaque tour
  montre ce qui reste à gagner.
  python -m imitation.entrainer --init models/imitation/cand_best.pt --iterations 10 --out models/imitation/cand_it

Étape 3 (conseillée) — affiner par renforcement : train_v3.py --init <modèle>_best.pt.

Le modèle retenu est celui qui obtient le meilleur C_max moyen (glouton) sur la validation
synthétique de train_v3 (jamais sur les benchmarks). Sorties : <out>_best.pt, <out>_log.json.
"""
import argparse, json, os, sys, time
import multiprocessing as mp
from types import SimpleNamespace
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train_v3 import val_set_v3, evaluate
from jssp_pm.fjsp_env3 import FJSPEnv3, run3
from jssp_pm.fjsp_ppo import PPOPolicy
from jssp_pm.reseaux import creer_reseau, charger_reseau, sauver_reseau, lire_etat
from imitation.rejeu import rejouer
from imitation.experts import instance, ameliorer, lire, parametres_recuit, DOSSIER

RSCALE = 0.1          # même échelle de récompense que train_v3 (pour pré-entraîner la valeur)


# ---------------------------------------------------------------------------- leçons
def lecons(net, env, recs, regime):
    """Rejoue les plannings experts et renvoie [(obs, actions conformes, cible de valeur)]."""
    out = []
    for r in recs:
        inst, _ = instance(r["i"], regime)
        lec, cmax, _ = rejouer(env, inst, r["planning"], observer=lambda e: (net.observe(e), e.sim.t, e.u))
        coupure = r.get("t_coupure", np.inf) if r.get("apprendre_avant_coupure") else np.inf
        out += [(ob, y, -(cmax - t) / u * RSCALE) for (ob, t, u), y in lec if t < coupure - 1e-9]
    return out


def perte(net, lot, poids_valeur):
    logits, v = net(*net.collate([x[0] for x in lot]))
    Y = torch.zeros_like(logits, dtype=torch.bool)
    for b, x in enumerate(lot):
        Y[b, x[1]] = True
    # plusieurs bonnes réponses : on maximise la probabilité totale des actions conformes
    pol = (torch.logsumexp(logits, -1) - torch.logsumexp(logits.masked_fill(~Y, -1e9), -1)).mean()
    cible = torch.tensor([x[2] for x in lot], dtype=torch.float32)
    val = ((v - cible) ** 2).mean()
    acc = (Y[torch.arange(len(lot)), logits.argmax(-1)]).float().mean()
    return pol + poids_valeur * val, float(pol.detach()), float(acc)


def epoque(net, opt, env, recs, rng, a):
    net.train()
    ordre = rng.permutation(len(recs))
    P, ACC = [], []
    for s in range(0, len(recs), a.bloc):                     # bloc d'instances -> leçons mélangées
        L = lecons(net, env, [recs[i] for i in ordre[s:s + a.bloc]], a.regime)
        perm = rng.permutation(len(L))
        for s2 in range(0, len(L), a.lot):
            loss, p, acc = perte(net, [L[i] for i in perm[s2:s2 + a.lot]], a.poids_valeur)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
            P.append(p)
            ACC.append(acc)
    net.eval()
    return float(np.mean(P)), float(np.mean(ACC))


# ---------------------------------------------------------------------------- itération experte
_NET = {}


def un_tour(args):
    """Agent glouton -> planning ; recuit simulé depuis ce planning -> planning amélioré."""
    i, regime, chemin, evaluations, params = args
    torch.set_num_threads(1)
    if _NET.get("chemin") != (chemin, os.path.getmtime(chemin)):
        _NET["net"], _NET["chemin"] = charger_reseau(chemin), (chemin, os.path.getmtime(chemin))
    inst, dist = instance(i, regime)
    m, sim = run3(FJSPEnv3("full", safety=(regime == "A")), PPOPolicy(_NET["net"]), inst)
    agent = [tuple(s) for s in sim.segments]
    cmax, planning = m["cmax"], agent
    if m["breakdowns"] == 0:
        c2, p2 = ameliorer(inst, agent, evaluations, params, i)
        if c2 < cmax:
            cmax, planning = c2, p2
    return dict(i=i, regime=regime, dist=dist, cmax_agent=float(m["cmax"]), cmax=float(cmax),
                evaluations=evaluations, source="iteration",
                planning=[[int(k), float(a), float(b), int(t), int(j)] for k, a, b, t, j in planning])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reseau", default="candidats", choices=["candidats", "graphe"])
    ap.add_argument("--init", default="", help="partir d'un modèle existant (type lu dans le fichier)")
    ap.add_argument("--experts", nargs="+", default=[os.path.join(DOSSIER, "experts.jsonl")])
    ap.add_argument("--out", required=True)
    ap.add_argument("--regime", default="A")
    ap.add_argument("--epoques", type=int, default=None,
                    help="passes d'imitation (défaut : 20, ou 0 si --init est donné)")
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lot", type=int, default=256)
    ap.add_argument("--bloc", type=int, default=32, help="instances rejouées ensemble avant mélange")
    ap.add_argument("--poids-valeur", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=0)
    # itération experte
    ap.add_argument("--iterations", type=int, default=0)
    ap.add_argument("--nouvelles", type=int, default=100, help="nouvelles instances par itération")
    ap.add_argument("--evals-expert", type=int, default=20000)
    ap.add_argument("--epoques-iteration", type=int, default=2)
    ap.add_argument("--parametres", default=None, help="parametres_retenus.json (Taguchi)")
    ap.add_argument("--processus", type=int, default=2)
    a = ap.parse_args()
    if a.epoques is None:
        a.epoques = 0 if a.init else 20
    torch.manual_seed(a.seed)
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    rng = np.random.default_rng(a.seed)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    env = FJSPEnv3("full", safety=(a.regime == "A"))
    cfg = SimpleNamespace(mode="full", regime=a.regime, beta=0.0)
    V = val_set_v3(a.regime)
    net = charger_reseau(a.init) if a.init else creer_reseau(a.reseau)
    recs = [r for f in a.experts for r in lire(f) if r["regime"] == a.regime]
    print(f"{len(recs)} plannings experts ; réseau « {net.type} »", flush=True)
    opt = torch.optim.Adam(net.parameters(), lr=a.lr)
    log, t0 = [], time.time()
    meilleur = evaluate(net, V, cfg)[0] if a.init else np.inf
    if a.init:
        sauver_reseau(net, a.out + "_best.pt")
        print(f"départ : validation {meilleur:.2f}", flush=True)

    def bilan(**info):
        nonlocal meilleur
        c, bd = evaluate(net, V, cfg)
        info.update(validation=c, pannes=bd, minutes=round((time.time() - t0) / 60, 1))
        if c < meilleur:
            meilleur = c
            sauver_reseau(net, a.out + "_best.pt")
            info["meilleur"] = True
        log.append(info)
        print(json.dumps(info, ensure_ascii=False), flush=True)
        json.dump(log, open(a.out + "_log.json", "w"), indent=1, ensure_ascii=False)

    # 1) imitation
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, max(a.epoques, 1))
    for e in range(1, a.epoques + 1):
        p, acc = epoque(net, opt, env, recs, rng, a)
        sched.step()
        bilan(phase="imitation", epoque=e, perte=round(p, 4), accord_expert=round(acc, 4))

    # 2) itération experte
    if a.iterations:
        net.load_state_dict(lire_etat(a.out + "_best.pt"))
        for g in opt.param_groups:
            g["lr"] = a.lr / 5
        fichier_it = a.out + "_iteration.jsonl"
        params = parametres_recuit(a.parametres)
        ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
        courant = a.out + "_courant.pt"
        for it in range(1, a.iterations + 1):
            sauver_reseau(net, courant)
            base = 1_000_000 + 100_000 * a.seed + it * a.nouvelles     # instances jamais vues
            taches = [(base + k, a.regime, courant, a.evals_expert, params) for k in range(a.nouvelles)]
            with ctx.Pool(a.processus) as pool:
                nouveaux = list(pool.imap_unordered(un_tour, taches))
            with open(fichier_it, "a", encoding="utf-8") as f:
                for r in nouveaux:
                    f.write(json.dumps(r) + "\n")
            ecart = float(np.mean([r["cmax_agent"] / r["cmax"] - 1 for r in nouveaux]))
            recs += nouveaux
            for _ in range(a.epoques_iteration):
                p, acc = epoque(net, opt, env, recs, rng, a)
            bilan(phase="iteration", iteration=it, perte=round(p, 4), accord_expert=round(acc, 4),
                  ecart_agent_vs_recuit=round(ecart, 4), plannings=len(recs))
    print(f"meilleur modèle : {a.out}_best.pt (validation {meilleur:.2f})")


if __name__ == "__main__":
    main()
