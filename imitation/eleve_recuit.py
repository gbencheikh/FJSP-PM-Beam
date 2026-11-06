"""L'agent, élève du recuit simulé, dans SES propres situations (DAgger avec juge recuit).

  python -m imitation.eleve_recuit --init models/imitation/cand_ft_best.pt --out models/eleve/cand \
         --evaluations 10000 --taux 0.1 --processus 10

Principe, à chaque tour :
  1. l'agent construit ses plannings (glouton) sur de NOUVELLES instances d'entraînement ;
  2. à une partie des décisions, tirées au hasard (--taux), on JUGE ses meilleures actions possibles
     (--k actions proposées par le réseau, + celle qu'il a choisie) :
        pour chaque action : on la fait, l'agent termine le planning lui-même, puis un recuit simulé
        court (--evaluations) améliore cette fin de planning, tout ce qui précède restant fixé ;
     la valeur d'une action = le C_max obtenu. Ce juge est toujours au moins aussi bon que l'agent
     (le recuit part du planning de l'agent) ;
  3. le réseau apprend : préférer les actions les mieux jugées (préférences graduées, --temperature)
     et estimer avec sa « tête de valeur » le C_max atteignable depuis la situation ;
  4. on recommence avec le réseau amélioré, sur de nouvelles instances.
Le recuit est interrogé sur les situations de l'élève, pas sur les siennes : l'agent apprend à
corriger ses propres erreurs, avec un professeur qui suppose une suite bien jouée.

Mesures affichées à chaque tour :
  gain_juge          : de combien la meilleure action jugée bat l'action choisie par l'agent (moyenne) ;
  agent_deja_meilleur: part des situations jugées où l'agent avait déjà choisi la meilleure action ;
  validation_glouton : C_max moyen de l'agent seul sur la validation synthétique (critère principal) ;
  validation_recherche : idem avec anticipation (faisceau --largeur, --k-recherche), si demandé.
Sorties : <out>_best.pt (agent seul), <out>_best_recherche.pt, <out>_log.json, <out>_lecons.jsonl.
"""
import argparse, json, os, sys, time
import multiprocessing as mp
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train_v3 import val_set_v3
from jssp_pm.fjsp_env3 import FJSPEnv3, run3
from jssp_pm.fjsp_ppo import PPOPolicy
from jssp_pm.anticipation import AgentAnticipation, cloner
from jssp_pm.moteur_rapide import MoteurRapide
from jssp_pm.reseaux import charger_reseau, sauver_reseau
from imitation.experts import instance, lire

BASE_IDS = 3_000_000          # numéros des instances d'entraînement de cette boucle
RSCALE = 0.1                  # même échelle que train_v3 pour la tête de valeur
_CACHE = {}


def _net(chemin):
    torch.set_num_threads(1)
    cle = (chemin, os.path.getmtime(chemin))
    if _CACHE.get("cle") != cle:
        _CACHE["net"], _CACHE["cle"] = charger_reseau(chemin), cle
    return _CACHE["net"]


def une_lecon(args):
    """Trajectoire gloutonne de l'agent sur une instance + jugement par recuit de quelques décisions."""
    i, regime, chemin, E, taux, K, p0, rf = args
    net = _net(chemin)
    pol = PPOPolicy(net)
    inst, _ = instance(i, regime)
    mr = MoteurRapide(inst)
    env = FJSPEnv3("full", True)
    env.reset(inst)
    rng = np.random.default_rng(i)
    actions, jugements = [], []
    while not env.sim.done():
        with torch.no_grad():
            logits = net(*net.collate([net.observe(env)]))[0][0].numpy()
        ag = int(np.argmax(logits))
        C = env._C
        if len(C) > 1 and rng.random() < taux:
            cand = list(range(len(C))) if K <= 0 or len(C) <= K else [int(x) for x in np.argsort(-logits)[:K]]
            if ag not in cand:
                cand.append(ag)
            graine = int(rng.integers(1 << 30))            # même tirage pour toutes les actions comparées
            vals = []
            for a in cand:
                e2 = cloner(env)
                e2.step(a)
                if e2.sim.done():
                    vals.append(float(e2.sim.last_completion))
                    continue
                ea = mr.etat(e2)
                e3 = cloner(e2)
                while not e3.sim.done():                    # l'agent termine lui-même
                    e3.step(pol.act(e3))
                c, _ = mr.valeur_recuit(ea, E, p0=p0, ratio_fin=rf, graine=graine, depart=list(e3.sim.segments))
                vals.append(float(c))
            jugements.append(dict(d=len(actions), cand=cand, vals=vals, t=float(env.sim.t)))
        actions.append(ag)
        env.step(ag)
    gains = [j["vals"][j["cand"].index(actions[j["d"]])] / min(j["vals"]) - 1 for j in jugements]
    return dict(i=i, regime=regime, actions=actions, jugements=jugements, cmax_glouton=float(env.sim.last_completion),
                gain=float(np.mean(gains)) if gains else 0.0,
                deja=float(np.mean([g <= 1e-9 for g in gains])) if gains else 1.0)


def une_validation(args):
    v, regime, chemin, B, K = args
    net = _net(chemin)
    if _CACHE.get("V") is None:
        _CACHE["V"] = val_set_v3(regime)
    inst = _CACHE["V"][v]
    g = run3(FJSPEnv3("full", True), PPOPolicy(net), inst)[0]["cmax"]
    c = AgentAnticipation(net, B, K).planifier(inst)[0] if B > 0 else np.nan
    return v, g, c


def donnees(net, recs, regime, temperature):
    """Rejoue les trajectoires et construit (observation, actions jugées, préférences, cible de valeur)."""
    out = []
    env = FJSPEnv3("full", True)
    for r in recs:
        inst, _ = instance(r["i"], regime)
        jug = {j["d"]: j for j in r["jugements"]}
        env.reset(inst)
        for d, a in enumerate(r["actions"]):
            if d in jug:
                j = jug[d]
                v = np.array(j["vals"])
                q = np.exp(-100 * (v / v.min() - 1) / temperature)
                out.append((net.observe(env), j["cand"], q / q.sum(), -(v.min() - env.sim.t) / env.u * RSCALE))
            env.step(a)
    return out


def apprendre(net, opt, D, rng, lot, poids_valeur, epoques):
    net.train()
    P, ACC = [], []
    for _ in range(epoques):
        perm = rng.permutation(len(D))
        for s in range(0, len(D), lot):
            b = [D[i] for i in perm[s:s + lot]]
            logits, v = net(*net.collate([x[0] for x in b]))
            logp = torch.log_softmax(logits, -1)
            Q = torch.zeros_like(logits)
            for n, x in enumerate(b):
                Q[n, x[1]] = torch.tensor(x[2], dtype=torch.float32)
            pol = -(Q * logp).sum(-1).mean()
            val = ((v - torch.tensor([x[3] for x in b], dtype=torch.float32)) ** 2).mean()
            loss = pol + poids_valeur * val
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
            choix = logits.argmax(-1)                      # accord : l'agent choisit une des meilleures actions
            ACC.append(float((Q.gather(1, choix[:, None])[:, 0] >= Q.max(-1).values - 1e-6).float().mean()))
            P.append(float(pol.detach()))
    net.eval()
    return float(np.mean(P)), float(np.mean(ACC))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", required=True, help="modèle de départ (p. ex. models/imitation/cand_ft_best.pt)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--regime", default="A")
    ap.add_argument("--evaluations", type=int, default=10000, help="évaluations du recuit pour CHAQUE jugement")
    ap.add_argument("--taux", type=float, default=0.1, help="part des décisions jugées (tirées au hasard)")
    ap.add_argument("--k", type=int, default=3, help="actions jugées par décision (+ celle de l'agent ; 0 = toutes)")
    ap.add_argument("--p0", type=float, default=0.01, help="recuit du juge : acceptation initiale")
    ap.add_argument("--ratio-fin", type=float, default=0.01, help="recuit du juge : température finale / initiale")
    ap.add_argument("--temperature", type=float, default=1.0,
                    help="préférences : une action pire de x %% pèse exp(-x/temperature)")
    ap.add_argument("--iterations", type=int, default=10)
    ap.add_argument("--instances", type=int, default=200, help="nouvelles instances par tour")
    ap.add_argument("--memoire", type=int, default=3, help="tours dont on garde les leçons")
    ap.add_argument("--epoques", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--lot", type=int, default=256)
    ap.add_argument("--poids-valeur", type=float, default=0.5)
    ap.add_argument("--largeur", type=int, default=5, help="validation avec anticipation (0 = sans)")
    ap.add_argument("--k-recherche", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--processus", type=int, default=2)
    a = ap.parse_args()
    torch.manual_seed(a.seed)
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    rng = np.random.default_rng(a.seed)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    net = charger_reseau(a.init)
    opt = torch.optim.Adam(net.parameters(), lr=a.lr)
    courant = a.out + "_courant.pt"
    fichier = a.out + "_lecons.jsonl"
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    log, t0 = [], time.time()
    par_tour = {}
    for r in lire(fichier):
        if r.get("evaluations") == a.evaluations:
            par_tour.setdefault(r["tour"], []).append(r)

    with ctx.Pool(a.processus) as pool:
        def valider():
            sauver_reseau(net, courant)
            res = list(pool.imap_unordered(une_validation, [(v, a.regime, courant, a.largeur, a.k_recherche)
                                                            for v in range(24)]))
            return float(np.mean([r[1] for r in res])), float(np.mean([r[2] for r in res]))

        g, c = valider()
        meilleur_g, meilleur_c = g, c
        sauver_reseau(net, a.out + "_best.pt")
        sauver_reseau(net, a.out + "_best_recherche.pt")
        log.append(dict(tour=0, validation_glouton=round(g, 2), validation_recherche=round(c, 2)))
        print(json.dumps(log[-1], ensure_ascii=False), flush=True)
        for it in range(1, a.iterations + 1):
            if len(par_tour.get(it, [])) < a.instances:      # 1-2) trajectoires + jugements
                sauver_reseau(net, courant)
                ids = [BASE_IDS + 100_000 * a.seed + it * a.instances + q for q in range(a.instances)]
                taches = [(i, a.regime, courant, a.evaluations, a.taux, a.k, a.p0, a.ratio_fin) for i in ids]
                nouveaux = []
                with open(fichier, "a", encoding="utf-8") as f:
                    for n, r in enumerate(pool.imap_unordered(une_lecon, taches), 1):
                        r.update(tour=it, evaluations=a.evaluations)
                        f.write(json.dumps(r) + "\n")
                        f.flush()
                        nouveaux.append(r)
                        if n % 20 == 0:
                            print(f"  tour {it} : {n}/{len(taches)} instances jugées "
                                  f"({(time.time() - t0) / 60:.1f} min)", flush=True)
                par_tour[it] = nouveaux
            nouveaux = par_tour[it][:a.instances]
            # 3) apprentissage sur les leçons des derniers tours
            recs = [r for t in range(max(1, it - a.memoire + 1), it + 1) for r in par_tour.get(t, [])[:a.instances]]
            D = donnees(net, recs, a.regime, a.temperature)
            p, acc = apprendre(net, opt, D, rng, a.lot, a.poids_valeur, a.epoques)
            g, c = valider()
            info = dict(tour=it, situations_jugees=len(D),
                        gain_juge=round(float(np.mean([r["gain"] for r in nouveaux])), 4),
                        agent_deja_meilleur=round(float(np.mean([r["deja"] for r in nouveaux])), 3),
                        perte=round(p, 4), accord=round(acc, 3),
                        validation_glouton=round(g, 2), validation_recherche=round(c, 2),
                        minutes=round((time.time() - t0) / 60, 1))
            if g < meilleur_g:
                meilleur_g = g
                sauver_reseau(net, a.out + "_best.pt")
                info["meilleur"] = True
            if c < meilleur_c:
                meilleur_c = c
                sauver_reseau(net, a.out + "_best_recherche.pt")
                info["meilleur_recherche"] = True
            log.append(info)
            print(json.dumps(info, ensure_ascii=False), flush=True)
            json.dump(log, open(a.out + "_log.json", "w"), indent=1, ensure_ascii=False)
    print(f"meilleur agent seul        : {a.out}_best.pt (validation {meilleur_g:.2f})")
    print(f"meilleur avec anticipation : {a.out}_best_recherche.pt (validation {meilleur_c:.2f})")


if __name__ == "__main__":
    main()
