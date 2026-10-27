"""PPO avec politique à scoring de candidats (indépendante de la taille de l'instance).

  e_c  = φ_c(x_c)                  embedding de chaque candidat (action valide)
  e_g  = φ_g(g)                    embedding du contexte global
  ē    = moyenne des e_c           résumé de l'ensemble des candidats
  logit(c) = ψ([e_c, e_g, ē])      π(·|s) = softmax sur les seuls candidats valides
  V(s)     = v([e_g, ē])
"""
import numpy as np
import torch
import torch.nn as nn

from .fjsp_env import F_CAND, F_GLOB


def mlp(i, h, o, depth=2):
    layers, d = [], i
    for _ in range(depth):
        layers += [nn.Linear(d, h), nn.Tanh()]
        d = h
    layers.append(nn.Linear(d, o))
    return nn.Sequential(*layers)


class CandNet(nn.Module):
    """Réseau « candidats » : chaque action est notée à partir de ses caractéristiques calculées
    à la main (pas de vue d'ensemble de l'atelier)."""
    type = "candidats"

    def __init__(self, h=128, f_cand=F_CAND, f_glob=F_GLOB):
        super().__init__()
        self.kwargs = dict(h=h) if (f_cand, f_glob) == (F_CAND, F_GLOB) else dict(h=h, f_cand=f_cand, f_glob=f_glob)
        self.phi_c = mlp(f_cand, h, h, 1)
        self.phi_g = mlp(f_glob, h, h, 1)
        # première couche de ψ décomposée : W[e_c, e_g, ē] = W_c e_c + (W_g e_g + W_p ē)
        self.psi_c = nn.Linear(h, h)
        self.psi_gp = nn.Linear(2 * h, h, bias=False)
        self.psi_out = nn.Sequential(nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))
        self.v = mlp(2 * h, h, 1, 2)

    def forward(self, X, mask, G):
        """X (B,C,F) ; mask (B,C) bool ; G (B,Fg) -> logits (B,C), value (B,)"""
        ec = torch.tanh(self.phi_c(X))
        eg = torch.tanh(self.phi_g(G))
        mf = mask.float().unsqueeze(-1)
        pooled = (ec * mf).sum(1) / mf.sum(1).clamp(min=1)
        ctx = torch.cat([eg, pooled], -1)
        z = self.psi_c(ec) + self.psi_gp(ctx).unsqueeze(1)
        logits = self.psi_out(z).squeeze(-1).masked_fill(~mask, -1e9)
        value = self.v(ctx).squeeze(-1)
        return logits, value


    # interface commune à tous les réseaux (voir jssp_pm/reseaux.py)
    @staticmethod
    def observe(env):
        return env.features()

    @staticmethod
    def collate(obs):
        Xt, Mt, Gt = pad([o[0] for o in obs], [o[1] for o in obs])
        return Xt, Mt, Gt


def pad(Xs, Gs):
    B = len(Xs)
    C = max(len(x) for x in Xs)
    X = np.zeros((B, C, Xs[0].shape[-1] if len(Xs[0].shape) == 2 else F_CAND), np.float32)
    M = np.zeros((B, C), bool)
    for i, x in enumerate(Xs):
        X[i, :len(x)] = x
        M[i, :len(x)] = True
    return torch.from_numpy(X), torch.from_numpy(M), torch.from_numpy(np.stack(Gs))


class PPOPolicy:
    """Wrapper d'inférence compatible avec fjsp_heuristics.run()."""

    def __init__(self, net, greedy=True, name="PPO", rng=None, temperature=1.0):
        self.net, self.greedy, self.name = net, greedy, name
        self.rng = rng or np.random.default_rng(0)
        self.temperature = temperature

    def act(self, env):
        return self.act_obs(self.net.observe(env))

    @torch.no_grad()
    def act_obs(self, obs):
        logits, _ = self.net(*self.net.collate([obs]))
        if self.greedy:
            return int(logits[0].argmax())
        p = torch.softmax(logits[0] / self.temperature, -1).numpy().astype(np.float64)
        return int(self.rng.choice(len(p), p=p / p.sum()))
