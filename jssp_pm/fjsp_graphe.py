"""Réseau de graphe pour le FJSP avec maintenance (piste 3).

Idée : au lieu de noter chaque action isolément (CandNet), le réseau regarde tout l'atelier comme
un GRAPHE et fait circuler l'information avant de décider.

  Nœuds « opération » : toutes les opérations pas encore terminées
      (en cours / prête / future, durées, travail restant du job, date de début au plus tôt…)
  Nœuds « machine »   : état, usure, marge avant seuil, T_k, M_k, R_k, charge potentielle…
  Arêtes opération–machine : une arête par machine éligible, avec la durée p_ok, « tient dans la
      marge d'usure ? », marge restante après l'opération, « machine la plus rapide ? »
  Arêtes opération–opération : précédence dans le job (précédente / suivante).

Chaque couche de passage de messages :
  - chaque machine agrège, par attention, les opérations qui peuvent passer chez elle
    (elle « voit » la file d'attente qui la concerne et l'usure qu'elle va subir) ;
  - chaque opération agrège, par attention, ses machines possibles, puis ses voisines dans le job.
Après 2 couches, l'embedding d'une opération dépend de la charge des machines concurrentes et de
l'état des autres jobs. Même principe que les réseaux de graphe hétérogènes récents pour le FJSP
(p. ex. Song et al., 2023), étendu ici à l'usure et à la maintenance.

Les actions restent les mêmes candidats que l'environnement v3 (lancer, maintenance, attendre) :
score(candidat) = ψ([caractéristiques du candidat, embedding de son opération, de sa machine,
de l'arête], contexte global). Même interface que CandNet : observe / collate / forward.
Le réseau est indépendant de la taille de l'instance (aucune dimension ne dépend de n ou m).
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .fjsp_env import F_CAND, F_GLOB, F_MACH
from .fjsp_ppo import mlp
from .simulator import IDLE, EPS

F_OP, F_ARETE = 9, 5


# ---------------------------------------------------------------------------- observation
def _structure(env):
    """Tableaux constants d'une instance (mis en cache sur l'environnement)."""
    inst = env.inst
    c = getattr(env, "_graphe_cache", None)
    if c is not None and c[0] is inst:
        return c[1]
    op_job = np.zeros(inst.n_ops, int)
    op_pos = np.zeros(inst.n_ops, int)
    cum = []
    for j, ops in enumerate(inst.job_ops):
        op_job[ops] = j
        op_pos[ops] = np.arange(len(ops))
        cum.append(np.concatenate([[0.0], np.cumsum(env.pmin[ops])]))
    el = inst.P > 0
    pmean = np.where(el, inst.P, 0).sum(1) / env.nel
    s = dict(op_job=op_job, op_pos=op_pos, cum=cum, el=el, pmean=pmean)
    env._graphe_cache = (inst, s)
    return s


def observer(env):
    X, g = env.features()
    sim, inst, u, L = env.sim, env.inst, env.u, env.L
    st = _structure(env)
    op_job, op_pos, cum = st["op_job"], st["op_pos"], st["cum"]
    head = env._etat["head"]
    nxt = sim.next_op[op_job]
    U = np.flatnonzero(op_pos >= nxt)                     # opérations non terminées
    idx = -np.ones(inst.n_ops, int)
    idx[U] = np.arange(len(U))
    jU, pU = op_job[U], op_pos[U]
    busy = sim.job_busy[jU]
    courant = pU == sim.next_op[jU]
    # date (relative) à laquelle chaque job sera libre
    libre = np.zeros(inst.n)
    for k in range(inst.m):
        if sim.mjob[k] >= 0:
            libre[sim.mjob[k]] = max(libre[sim.mjob[k]], sim.end[k] - sim.t + sim.pending[k])
        j = sim.after_pm[k]
        if j >= 0:
            libre[j] = max(libre[j], sim.end[k] - sim.t + inst.P[sim.cur_op(j), k])
    debut = np.array([sim.next_op[j] + (1 if sim.job_busy[j] else 0) for j in range(inst.n)])
    lb = np.array([0.0 if c else libre[j] + cum[j][p] - cum[j][debut[j]]
                   for j, p, c in zip(jU, pU, courant)])
    Fo = np.zeros((len(U), F_OP), np.float32)
    Fo[:, 0] = courant & busy
    Fo[:, 1] = courant & ~busy
    Fo[:, 2] = ~courant
    Fo[:, 3] = env.pmin[U] / u
    Fo[:, 4] = st["pmean"][U] / u
    Fo[:, 5] = env.nel[U] / inst.m
    Fo[:, 6] = [env.suffix[j][p] / L for j, p in zip(jU, pU)]
    Fo[:, 7] = (sim.nops_job[jU] - pU) / 10
    Fo[:, 8] = np.clip(lb / L, 0, 5)
    # arêtes opération–machine
    A = st["el"][U]
    P = inst.P[U]
    E = np.zeros((len(U), inst.m, F_ARETE), np.float32)
    E[..., 0] = P / u
    E[..., 1] = (P - env.pmin[U][:, None]) / u
    E[..., 2] = P <= head[None, :] + EPS
    E[..., 3] = np.clip((head[None, :] - P) / u, -5, 20) / 5
    E[np.arange(len(U)), env.fastest[U], 4] = 1.0
    E *= A[..., None]
    # précédence
    pred = np.array([idx[inst.job_ops[j][p - 1]] if p > sim.next_op[j] else -1 for j, p in zip(jU, pU)], int)
    succ = np.array([idx[inst.job_ops[j][p + 1]] if p + 1 < sim.nops_job[j] else -1 for j, p in zip(jU, pU)],
                    int)
    # candidats -> (opération, machine)
    co = np.full(len(env._C), -1, int)
    cm = np.full(len(env._C), -1, int)
    for i, (typ, j, k) in enumerate(env._C):
        if typ in ("D", "J"):
            co[i] = idx[sim.cur_op(j)]
        if k >= 0:
            cm[i] = k
    return dict(X=X, g=g, Fo=Fo, Fm=env._etat["Mf"].astype(np.float32), E=E, A=A,
                pred=pred.astype(int), succ=succ, co=co, cm=cm)


def collate(obs):
    B = len(obs)
    C = max(len(o["X"]) for o in obs)
    O = max(max(len(o["Fo"]) for o in obs), 1)
    M = max(len(o["Fm"]) for o in obs)
    Xc = np.zeros((B, C, F_CAND), np.float32)
    Cm = np.zeros((B, C), bool)
    Fo = np.zeros((B, O, F_OP), np.float32)
    Om = np.zeros((B, O), bool)
    Fm = np.zeros((B, M, F_MACH), np.float32)
    Mm = np.zeros((B, M), bool)
    E = np.zeros((B, O, M, F_ARETE), np.float32)
    A = np.zeros((B, O, M), bool)
    pred = -np.ones((B, O), np.int64)
    succ = -np.ones((B, O), np.int64)
    co = -np.ones((B, C), np.int64)
    cm = -np.ones((B, C), np.int64)
    for b, o in enumerate(obs):
        c, n, m = len(o["X"]), len(o["Fo"]), len(o["Fm"])
        Xc[b, :c], Cm[b, :c] = o["X"], True
        Fo[b, :n], Om[b, :n] = o["Fo"], True
        Fm[b, :m], Mm[b, :m] = o["Fm"], True
        E[b, :n, :m], A[b, :n, :m] = o["E"], o["A"]
        pred[b, :n], succ[b, :n] = o["pred"], o["succ"]
        co[b, :c], cm[b, :c] = o["co"], o["cm"]
    G = np.stack([o["g"] for o in obs])
    t = torch.from_numpy
    return (t(Xc), t(Cm), t(G), t(Fo), t(Om), t(Fm), t(Mm), t(E), t(A), t(pred), t(succ), t(co), t(cm))


# ---------------------------------------------------------------------------- réseau
def _prendre(h, index):
    """h (B,N,H), index (B,K) avec -1 = absent -> (B,K,H) (zéros si absent)."""
    ok = (index >= 0).unsqueeze(-1).float()
    i = index.clamp(min=0).unsqueeze(-1).expand(-1, -1, h.shape[-1])
    return torch.gather(h, 1, i) * ok


class Couche(nn.Module):
    """Un tour de passage de messages opérations <-> machines (+ précédence)."""

    def __init__(self, h):
        super().__init__()
        self.att_m = nn.ModuleDict(dict(q=nn.Linear(h, 1), k=nn.Linear(h, 1), e=nn.Linear(F_ARETE, 1)))
        self.val_m = nn.ModuleDict(dict(v=nn.Linear(h, h), e=nn.Linear(F_ARETE, h)))
        self.att_o = nn.ModuleDict(dict(q=nn.Linear(h, 1), k=nn.Linear(h, 1), e=nn.Linear(F_ARETE, 1)))
        self.val_o = nn.ModuleDict(dict(v=nn.Linear(h, h), e=nn.Linear(F_ARETE, h)))
        self.maj_m = mlp(2 * h, h, h, 1)
        self.maj_o = mlp(4 * h, h, h, 1)
        self.ln_m, self.ln_o = nn.LayerNorm(h), nn.LayerNorm(h)

    def forward(self, ho, hm, E, A, pred, succ):
        # machines <- opérations éligibles (attention sur les opérations)
        s = self.att_m["q"](hm).squeeze(-1)[:, None, :] + self.att_m["k"](ho) + self.att_m["e"](E).squeeze(-1)
        s = F.leaky_relu(s, 0.2).masked_fill(~A, -1e9)
        a = torch.softmax(s, 1) * A.any(1, keepdim=True).float()
        msg_m = torch.einsum("bom,boh->bmh", a, self.val_m["v"](ho)) + \
            self.val_m["e"](torch.einsum("bom,bomf->bmf", a, E))
        # opérations <- machines éligibles (attention sur les machines)
        s = self.att_o["q"](ho) + self.att_o["k"](hm).squeeze(-1)[:, None, :] + self.att_o["e"](E).squeeze(-1)
        s = F.leaky_relu(s, 0.2).masked_fill(~A, -1e9)
        a = torch.softmax(s, 2) * A.any(2, keepdim=True).float()
        msg_o = torch.einsum("bom,bmh->boh", a, self.val_o["v"](hm)) + \
            self.val_o["e"](torch.einsum("bom,bomf->bof", a, E))
        ho2 = self.ln_o(ho + self.maj_o(torch.cat([ho, msg_o, _prendre(ho, pred), _prendre(ho, succ)], -1)))
        hm2 = self.ln_m(hm + self.maj_m(torch.cat([hm, msg_m], -1)))
        return ho2, hm2


class GrapheNet(nn.Module):
    type = "graphe"

    def __init__(self, h=64, couches=2):
        super().__init__()
        self.kwargs = dict(h=h, couches=couches)
        self.emb_o = mlp(F_OP, h, h, 1)
        self.emb_m = mlp(F_MACH, h, h, 1)
        self.couches = nn.ModuleList([Couche(h) for _ in range(couches)])
        self.emb_c = mlp(F_CAND + 2 * h + F_ARETE, h, h, 1)
        self.emb_g = mlp(F_GLOB, h, h, 1)
        self.psi_c = nn.Linear(h, h)
        self.psi_ctx = nn.Linear(4 * h, h, bias=False)
        self.psi_out = nn.Sequential(nn.Tanh(), nn.Linear(h, h), nn.Tanh(), nn.Linear(h, 1))
        self.v = mlp(4 * h, h, 1, 2)

    observe = staticmethod(observer)
    collate = staticmethod(collate)

    def forward(self, Xc, Cm, G, Fo, Om, Fm, Mm, E, A, pred, succ, co, cm):
        ho = torch.tanh(self.emb_o(Fo)) * Om.unsqueeze(-1).float()
        hm = torch.tanh(self.emb_m(Fm)) * Mm.unsqueeze(-1).float()
        for c in self.couches:
            ho, hm = c(ho, hm, E, A, pred, succ)
            ho = ho * Om.unsqueeze(-1).float()
            hm = hm * Mm.unsqueeze(-1).float()
        B, C = co.shape
        # caractéristiques de l'arête (opération, machine) de chaque candidat
        M = E.shape[2]
        lin = (co.clamp(min=0) * M + cm.clamp(min=0))
        Ef = E.reshape(B, -1, F_ARETE)
        e_c = torch.gather(Ef, 1, lin.unsqueeze(-1).expand(-1, -1, F_ARETE)) * \
            ((co >= 0) & (cm >= 0)).unsqueeze(-1).float()
        z = torch.cat([Xc, _prendre(ho, co), _prendre(hm, cm), e_c], -1)
        ec = torch.tanh(self.emb_c(z))
        mc = Cm.unsqueeze(-1).float()
        moy = lambda h, m: (h * m).sum(1) / m.sum(1).clamp(min=1)
        ctx = torch.cat([torch.tanh(self.emb_g(G)), moy(ec, mc), moy(ho, Om.unsqueeze(-1).float()),
                         moy(hm, Mm.unsqueeze(-1).float())], -1)
        logits = self.psi_out(self.psi_c(ec) + self.psi_ctx(ctx).unsqueeze(1)).squeeze(-1)
        return logits.masked_fill(~Cm, -1e9), self.v(ctx).squeeze(-1)
