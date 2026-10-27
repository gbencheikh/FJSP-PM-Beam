"""Instances FJSP (format .fjs Brandimarte/Kacem) + protocole de paramètres d'usure.

Format .fjs :
  ligne 1 : n m [flex moyenne]
  ligne j : nb_ops, puis pour chaque op : k, (machine, durée) x k   (machines indexées à partir de 1)

Les benchmarks ne contiennent ni T_k, ni M_k, ni R_k. Protocole reproductible (dérivé de l'instance) :
  u        = moyenne sur les ops de min_k p_ok          (unité de temps de l'instance)
  L̄        = (Σ_ops min_k p_ok) / m = n_ops·u/m       charge moyenne par machine
  T_k      = f_k · max(τ·L̄, κ·u),  f_k ~ U[0.8, 1.2] tiré avec une graine fixe (seuils spécifiques)
  M_k      = max(1, round(μ·u)),   R_k = max(1, round(ρ·u))
Par défaut τ = 0.5 (≈ 1 à 2 maintenances par machine), κ = 3 (au moins ~3 ops entre deux
maintenances, utile pour les petites instances type Kacem1), μ = 1, ρ = 6.
Couple (op, k) avec p_ok > T_k : jugé incompatible (l'op ne peut pas passer sur k sans panne,
même juste après maintenance) -> retiré des options. Si une op perd toutes ses options, on relève
le seuil de sa machine la plus rapide à p (T_k := p), pour garder l'instance faisable.
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class FInstance:
    P: np.ndarray            # (n_ops_tot, m) durée ; 0 = machine non éligible
    job_ops: list            # job_ops[j] = liste des ids d'op globaux, dans l'ordre
    T: np.ndarray
    M: np.ndarray
    R: np.ndarray
    stochastic: bool = False
    name: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def n(self):
        return len(self.job_ops)

    @property
    def m(self):
        return self.P.shape[1]

    @property
    def n_ops(self):
        return self.P.shape[0]

    def elig(self, o):
        return np.flatnonzero(self.P[o] > 0)


def parse_fjs(path):
    tok = open(path).read().split()
    it = iter(tok)
    n, m = int(next(it)), int(next(it))
    first_line = open(path).readline().split()
    if len(first_line) > 2:
        next(it)  # flexibilité moyenne
    rows, job_ops = [], []
    for j in range(n):
        k_ops = int(next(it))
        ids = []
        for _ in range(k_ops):
            row = np.zeros(m)
            for _ in range(int(next(it))):
                mach, p = int(next(it)) - 1, float(next(it))
                row[mach] = p
            ids.append(len(rows))
            rows.append(row)
        job_ops.append(ids)
    return np.array(rows), job_ops


def attach_wear(P, job_ops, tau=0.5, mu=1.0, rho=6.0, seed=0, stochastic=False, name="",
                hetero=(0.8, 1.2), kappa=3.0, T_scale=1.0):
    P_orig, P = P, P.copy()
    m = P.shape[1]
    rng = np.random.default_rng(seed)
    minp = np.array([row[row > 0].min() for row in P])
    u = minp.mean()
    Lbar = minp.sum() / m
    f = rng.uniform(*hetero, size=m)
    T = np.maximum(np.round(T_scale * f * max(tau * Lbar, kappa * u)), 1.0)
    for o in range(P.shape[0]):
        el = P[o] > 0
        ok = el & (P[o] <= T)
        if not ok.any():
            k = np.flatnonzero(el)[np.argmin(P[o][el])]
            T[k] = P[o, k]
    P[(P > T[None, :])] = 0.0
    M = np.full(m, max(1.0, float(round(mu * u))))
    R = np.full(m, max(1.0, float(round(rho * u))))
    return FInstance(P, job_ops, T, M, R, stochastic, name,
                     dict(tau=tau, mu=mu, rho=rho, kappa=kappa, T_scale=T_scale, u=u, Lbar=Lbar, seed=seed,
                          removed_options=int(((P_orig > 0) & (P == 0)).sum())))


def load_fjs(path, **kw):
    P, job_ops = parse_fjs(path)
    import os
    return attach_wear(P, job_ops, name=os.path.splitext(os.path.basename(path))[0], **kw)


def generate_fjsp(rng, n, m, ops_range=(2, 8), p_range=(1, 20), tau=0.5, mu=1.0, rho=6.0,
                  stochastic=False, kappa=3.0, T_scale=1.0):
    """FJSP aléatoire : flexibilité U[1,m], durée de base U[p], variation ±50 % par machine."""
    rows, job_ops = [], []
    for j in range(n):
        ids = []
        for _ in range(int(rng.integers(ops_range[0], ops_range[1] + 1))):
            k = int(rng.integers(1, m + 1))
            mach = rng.choice(m, k, replace=False)
            base = rng.integers(p_range[0], p_range[1] + 1)
            row = np.zeros(m)
            row[mach] = np.maximum(1, np.round(base * rng.uniform(0.5, 1.5, size=k)))
            ids.append(len(rows))
            rows.append(row)
        job_ops.append(ids)
    return attach_wear(np.array(rows), job_ops, tau, mu, rho, seed=int(rng.integers(1 << 30)),
                       stochastic=stochastic, kappa=kappa, T_scale=T_scale)


# ---------------------------------------------------------------------------
# Protocole v3 (article) : options machine d'origine CONSERVÉES, deux régimes.
#
#   base_k = s · f_k · max(τ·L̄, κ·u),  f_k ~ U[0.8, 1.2] (graine publiée)
#   Régime A « faisable » : T_k = max(round(base_k), pmax_k), pmax_k = plus longue option
#       éligible sur k. Toute opération tient sur toute machine éligible juste après une PM :
#       un planning sans panne existe toujours, et le filtre de sécurité garantit 0 panne.
#   Régime B « stress »   : T_k = max(round(base_k), 1). Les options p_ok > T_k sont gardées :
#       les choisir provoque une panne certaine. Si une op n'a AUCUNE option sûre, on relève
#       T de sa machine la plus rapide à p (un planning sans panne existe donc toujours).
#   M_k = max(1, round(μ·u)), R_k = max(1, round(ρ·u)).
# ---------------------------------------------------------------------------
def attach_wear_v3(P, job_ops, regime="A", tau=0.5, kappa=3.0, mu=1.0, rho=6.0, seed=0,
                   T_scale=1.0, hetero=(0.8, 1.2), stochastic=False, name=""):
    P = P.copy()
    n_ops, m = P.shape
    el = P > 0
    minp = np.where(el, P, np.inf).min(1)
    u = float(minp.mean())
    Lbar = float(minp.sum() / m)
    rng = np.random.default_rng(seed)
    f = rng.uniform(*hetero, size=m)
    base = T_scale * f * max(tau * Lbar, kappa * u)
    pmax_k = np.array([P[el[:, k], k].max() if el[:, k].any() else 1.0 for k in range(m)])
    if regime == "A":
        T = np.maximum(np.round(base), pmax_k)
    elif regime == "B":
        T = np.maximum(np.round(base), 1.0)
        for o in range(n_ops):
            if not (el[o] & (P[o] <= T)).any():
                k = np.flatnonzero(el[o])[np.argmin(P[o][el[o]])]
                T[k] = P[o, k]
    else:
        raise ValueError(regime)
    M = np.full(m, max(1.0, float(round(mu * u))))
    R = np.full(m, max(1.0, float(round(rho * u))))
    risky = int((el & (P > T[None, :])).sum())
    return FInstance(P, job_ops, T.astype(float), M, R, stochastic, name,
                     dict(protocol="v3", regime=regime, tau=tau, kappa=kappa, mu=mu, rho=rho,
                          T_scale=T_scale, seed=seed, f=f.tolist(), u=u, Lbar=Lbar,
                          risky_options=risky, options=int(el.sum())))


def load_fjs_v3(path, regime="A", **kw):
    import os
    P, job_ops = parse_fjs(path)
    return attach_wear_v3(P, job_ops, regime=regime,
                          name=os.path.splitext(os.path.basename(path))[0], **kw)


def generate_fjsp_v3(rng, n, m, regime="A", ops_range=(2, 8), p_range=(1, 20), tau=0.5,
                     kappa=3.0, mu=1.0, rho=6.0, T_scale=1.0, stochastic=False):
    rows, job_ops = [], []
    for j in range(n):
        ids = []
        for _ in range(int(rng.integers(ops_range[0], ops_range[1] + 1))):
            k = int(rng.integers(1, m + 1))
            mach = rng.choice(m, k, replace=False)
            base = rng.integers(p_range[0], p_range[1] + 1)
            row = np.zeros(m)
            row[mach] = np.maximum(1, np.round(base * rng.uniform(0.5, 1.5, size=k)))
            ids.append(len(rows))
            rows.append(row)
        job_ops.append(ids)
    return attach_wear_v3(np.array(rows), job_ops, regime, tau, kappa, mu, rho,
                          seed=int(rng.integers(1 << 30)), T_scale=T_scale, stochastic=stochastic)


def instance_record(inst):
    """Paramètres de maintenance publiables d'une instance (pour l'annexe de l'article)."""
    d = dict(name=inst.name, n=inst.n, m=inst.m, n_ops=inst.n_ops,
             T=[int(x) for x in inst.T], M=[int(x) for x in inst.M], R=[int(x) for x in inst.R])
    d.update({k: v for k, v in inst.meta.items()})
    return d
