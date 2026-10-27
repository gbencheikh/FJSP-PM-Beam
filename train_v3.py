"""Pipeline d'entraînement v3 (article) : PPO puis auto-amélioration, pour un (régime, mode, β, graine).

  python train_v3.py --regime A --mode full --seed 0 --out models/v3/A_full_s0
  python train_v3.py --regime B --mode full --beta 2 --seed 0 --out models/v3/B_full_b2_s0
  python train_v3.py --reseau graphe --seed 0 --out models/graphe/A_full_s0     # réseau de graphe
  python train_v3.py --init models/imitation/bc_best.pt --ppo_steps 0 --out ...   # affiner un modèle

Régime A : filtre de sécurité, objectif C_max.  Régime B : pas de filtre, objectif C_max + β·u·pannes.
La sélection de modèle se fait uniquement sur une validation synthétique (jamais sur les benchmarks).
"""
import argparse, json, os, time
import numpy as np
import torch

from jssp_pm.fjsp_instance import generate_fjsp_v3
from jssp_pm.fjsp_env3 import FJSPEnv3, Heur3, run3
from jssp_pm.fjsp_ppo import PPOPolicy
from jssp_pm.reseaux import creer_reseau, sauver_reseau, lire_etat

TAU = {"A": (0.3, 0.8), "B": (0.15, 0.4)}
KAPPA = {"A": 3.0, "B": 1.5}


def sample_v3(rng, regime, dist="mix"):
    if dist == "mix":
        dist = "base" if rng.random() < 0.5 else "large"
    if dist == "large":
        n, m, ops = int(rng.integers(10, 26)), int(rng.integers(4, 16)), (4, 15)
    else:
        n, m, ops = int(rng.integers(4, 16)), int(rng.integers(4, 11)), (2, 10)
    return generate_fjsp_v3(rng, n, m, regime=regime, ops_range=ops,
                            tau=float(rng.uniform(*TAU[regime])), kappa=KAPPA[regime],
                            mu=float(rng.uniform(0.5, 1.5)), rho=float(rng.uniform(4, 8)),
                            T_scale=float(rng.uniform(0.7, 1.5)))


def val_set_v3(regime, k=24, seed=999):
    rng = np.random.default_rng(seed)
    return [sample_v3(rng, regime, "base") for _ in range(k // 2)] + \
           [sample_v3(rng, regime, "large") for _ in range(k // 2)]


def make_env(a):
    return FJSPEnv3(a.mode, safety=(a.regime == "A"), beta=a.beta)


def evaluate(net, insts, a):
    env, pol = make_env(a), PPOPolicy(net)
    R = [run3(env, pol, i)[0] for i in insts]
    return float(np.mean([r["objective"] for r in R])), float(np.mean([r["breakdowns"] for r in R]))


def teachers(a):
    rules = ["jit", "jitp"] + (["rtf"] if a.regime == "B" and a.mode == "full" else [])
    return [Heur3(r) for r in rules]


def ppo_phase(net, a, rng, V, log, ref):
    opt = torch.optim.Adam(net.parameters(), lr=a.lr)
    gamma, lam, clip, vf_c, epochs, mb = 0.998, 0.95, 0.2, 0.5, 4, 512
    envs = [make_env(a) for _ in range(a.envs)]
    for e in envs:
        e.reset(sample_v3(rng, a.regime, a.ppo_dist), rng)
    steps, next_eval, best, t0 = 0, 0, np.inf, time.time()
    if a.ppo_steps <= 0:                      # pas de PPO (reprise depuis --init)
        sauver_reseau(net, a.out + "_ppo_best.pt")
        return evaluate(net, V, a)[0]
    while steps < a.ppo_steps:
        buf = [[] for _ in envs]
        for _ in range(a.horizon):
            feats = [net.observe(e) for e in envs]
            with torch.no_grad():
                logits, val = net(*net.collate(feats))
                d = torch.distributions.Categorical(logits=logits)
                act = d.sample()
                logp = d.log_prob(act)
            for i, e in enumerate(envs):
                r, done = e.step(int(act[i]))
                buf[i].append((feats[i], int(act[i]), float(logp[i]), float(val[i]), r * a.rscale, done))
                if done:
                    e.reset(sample_v3(rng, a.regime, a.ppo_dist), rng)
        steps += a.envs * a.horizon
        feats = [net.observe(e) for e in envs]
        with torch.no_grad():
            _, last_v = net(*net.collate(feats))
        data = []
        for i, traj in enumerate(buf):
            adv, nv = 0.0, float(last_v[i])
            for (ob, ac, lp, v, r, dn) in reversed(traj):
                if dn:
                    nv, adv = 0.0, 0.0
                delta = r + gamma * nv - v
                adv = delta + gamma * lam * adv
                data.append((ob, ac, lp, adv, adv + v))
                nv = v
        A = np.array([x[3] for x in data])
        A = (A - A.mean()) / (A.std() + 1e-8)
        for _ in range(epochs):
            perm = rng.permutation(len(data))
            for s in range(0, len(data), mb):
                idx = perm[s:s + mb]
                ac = torch.tensor([data[i][1] for i in idx])
                old = torch.tensor([data[i][2] for i in idx])
                adv = torch.tensor(A[idx], dtype=torch.float32)
                ret = torch.tensor([data[i][4] for i in idx], dtype=torch.float32)
                logits, v = net(*net.collate([data[i][0] for i in idx]))
                d = torch.distributions.Categorical(logits=logits)
                ratio = torch.exp(d.log_prob(ac) - old)
                pl = -torch.min(ratio * adv, torch.clamp(ratio, 1 - clip, 1 + clip) * adv).mean()
                loss = pl + vf_c * ((v - ret) ** 2).mean() - a.ent * d.entropy().mean()
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5)
                opt.step()
        if steps >= next_eval:
            next_eval += a.eval_every
            c, bd = evaluate(net, V, a)
            log.append(dict(phase="ppo", step=steps, objective=c, breakdowns=bd, ref=ref,
                            gap=c / ref - 1, minutes=(time.time() - t0) / 60))
            print(json.dumps(log[-1]), flush=True)
            if c < best:
                best = c
                sauver_reseau(net, a.out + "_ppo_best.pt")
    net.load_state_dict(lire_etat(a.out + "_ppo_best.pt"))
    return best


def rejouer_actions(env, net, inst, seed, actions):
    """Rejoue une suite d'actions pour enregistrer les observations du réseau."""
    env.reset(inst, np.random.default_rng(seed))
    traj = []
    for act in actions:
        traj.append((net.observe(env), act))
        env.step(act)
    return traj


def rollout(env, policy, inst, seed):
    env.reset(inst, np.random.default_rng(seed))
    traj, done = [], env.sim.done()
    while not done:
        if hasattr(policy, "net"):
            ob = policy.net.observe(env)
            act = policy.act_obs(ob)
        else:
            ob, act = None, policy.act(env)
        traj.append((ob, act))
        _, done = env.step(act)
    return env.objective(), traj


def sil_phase(net, a, rng, V, log, ref, best_val):
    opt = torch.optim.Adam(net.parameters(), lr=a.sil_lr)
    env = make_env(a)
    T = teachers(a)
    replay, t0 = [], time.time()
    sauver_reseau(net, a.out + "_best.pt")
    best = best_val
    for it in range(1, a.sil_iters + 1):
        data, gains = [], []
        net.eval()
        for _ in range(a.sil_batch):
            inst = sample_v3(rng, a.regime)
            s = int(rng.integers(1 << 30))
            cands = [rollout(env, t, inst, s) for t in T]
            h = min(c[0] for c in cands)
            cands.append(rollout(env, PPOPolicy(net), inst, s))
            srng = np.random.default_rng(s)
            for i in range(a.sil_K):
                cands.append(rollout(env, PPOPolicy(net, greedy=False, rng=srng, temperature=a.sil_temp),
                                     inst, s + i + 1))
            greedy_obj = cands[len(T)][0]
            bst = min(cands, key=lambda c: c[0])
            gains.append(bst[0] / h - 1)
            if bst[0] < greedy_obj * (1 - a.sil_min_gain):   # imiter seulement une amélioration nette
                if bst[1] and bst[1][0][0] is None:            # trajectoire d'une règle : observer au rejeu
                    bst = (bst[0], rejouer_actions(env, net, inst, s, [x[1] for x in bst[1]]))
                data += bst[1]
        replay = (replay + [data])[-a.sil_replay:]
        D = [x for d in replay for x in d]
        if not D:
            continue
        net.train()
        for _ in range(a.sil_epochs):
            perm = rng.permutation(len(D))
            for s0 in range(0, len(D), 256):
                idx = perm[s0:s0 + 256]
                y = torch.tensor([D[i][1] for i in idx])
                logits, _ = net(*net.collate([D[i][0] for i in idx]))
                loss = torch.nn.functional.cross_entropy(logits, y)
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5)
                opt.step()
        net.eval()
        c, bd = evaluate(net, V, a)
        log.append(dict(phase="sil", iter=it, objective=c, breakdowns=bd, ref=ref, gap=c / ref - 1,
                        teacher_gain=float(np.mean(gains)), minutes=(time.time() - t0) / 60))
        print(json.dumps(log[-1]), flush=True)
        if c < best:
            best = c
            sauver_reseau(net, a.out + "_best.pt")
        elif c > best * (1 + a.sil_rollback):           # dérive : retour au meilleur modèle
            net.load_state_dict(lire_etat(a.out + "_best.pt"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", default="A", choices=["A", "B"])
    ap.add_argument("--mode", default="full", choices=["full", "pm_only", "dispatch_only"])
    ap.add_argument("--beta", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--init", default="")
    ap.add_argument("--reseau", default="candidats", choices=["candidats", "graphe"])
    ap.add_argument("--taille", type=int, default=None, help="largeur des couches (128 candidats, 64 graphe)")
    ap.add_argument("--ppo_steps", type=int, default=500_000)
    ap.add_argument("--envs", type=int, default=16)
    ap.add_argument("--horizon", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--ent", type=float, default=0.01)
    ap.add_argument("--rscale", type=float, default=0.1)
    ap.add_argument("--eval_every", type=int, default=50_000)
    ap.add_argument("--sil_iters", type=int, default=8)
    ap.add_argument("--sil_batch", type=int, default=48)
    ap.add_argument("--sil_K", type=int, default=12)
    ap.add_argument("--sil_replay", type=int, default=4)
    ap.add_argument("--sil_lr", type=float, default=5e-5)
    ap.add_argument("--sil_epochs", type=int, default=2)
    ap.add_argument("--sil_temp", type=float, default=0.5)
    ap.add_argument("--sil_min_gain", type=float, default=0.005)
    ap.add_argument("--sil_rollback", type=float, default=0.01)
    ap.add_argument("--ppo_dist", default="base", choices=["base", "mix", "large"])
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    torch.set_num_threads(1)
    torch.manual_seed(a.seed)
    rng = np.random.default_rng(a.seed)
    V = val_set_v3(a.regime)
    henv = make_env(a)
    ref = float(np.mean([min(run3(henv, t, i)[0]["objective"] for t in teachers(a)) for i in V]))
    if a.init:                                   # le type de réseau est lu dans le fichier
        from jssp_pm.reseaux import charger_reseau
        net = charger_reseau(a.init)
        net.train()
    else:
        net = creer_reseau(a.reseau, **({"h": a.taille} if a.taille else {}))
    log = []
    json.dump(vars(a), open(a.out + "_config.json", "w"), indent=1)
    best = ppo_phase(net, a, rng, V, log, ref)
    sil_phase(net, a, rng, V, log, ref, best)
    json.dump(log, open(a.out + "_log.json", "w"), indent=1)


if __name__ == "__main__":
    main()
