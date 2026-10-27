"""Moteur rapide : « si je suis dans cette situation et que je fais cette action, quel C_max à la fin ? »

À partir d'un état quelconque de l'environnement (FJSPEnv3), le moteur termine le planning avec une
règle simple, en ~0,1 ms au lieu de 30–85 ms pour le simulateur événementiel. Il sert :
  - à l'agent qui anticipe (évaluer chaque action candidate, branch and bound tronqué) ;
  - plus tard, à la version stochastique (simuler plusieurs futurs possibles).

Règle de complétion (même logique que l'heuristique PM-JIT de fjsp_env3.Heur3) :
  à chaque instant s, parmi les jobs prêts, par ordre de priorité (MWKR par défaut), on lance l'op
  courante sur sa machine EFT (fin au plus tôt, maintenance comprise) si cette machine est libre ;
  si l'op ne tient pas dans la marge d'usure « de décision », maintenance juste avant, commencée
  dès que la machine s'est libérée (jamais avant l'instant présent).
  Sinon on avance au prochain événement.

Préparé pour le stochastique : deux jeux de seuils.
  Tpol[k]      : le seuil que la RÈGLE croit (décision de maintenance) ;
  Treel[k, c]  : le seuil RÉEL du c-ième cycle futur de la machine k (panne si dépassé :
                 réparation R_k, puis reprise de l'op, usure remise à 0) ;
  Mdur[k, c]   : durée réelle de la c-ième maintenance future ; Mpol[k] : durée supposée.
En déterministe (régime A) : Tpol = Treel = T, Mdur = Mpol = M, et il n'y a jamais de panne.

numba (pip install numba) accélère fortement le moteur ; sans numba il fonctionne, en plus lent.
"""
import numpy as np

from .simulator import IDLE, PROC, PM, REPAIR, EPS

try:
    from numba import njit
    NUMBA = True
except ImportError:                      # repli : même code, en Python pur
    NUMBA = False

    def njit(*a, **k):
        if a and callable(a[0]):
            return a[0]
        return lambda f: f

# types d'action forcée au début de la complétion
AUCUNE, LANCER, MAINT, MAINT_PUIS_LANCER, ATTENDRE = 0, 1, 2, 3, 4
CODE = {"D": LANCER, "P": MAINT, "J": MAINT_PUIS_LANCER, "W": ATTENDRE, "C": ATTENDRE}
REGLES = {"MWKR": 0, "MOR": 1, "SPT": 2, "LPT": 3}


@njit(cache=True)
def _ajouter(plan, cpt, k, a, b, typ, j):
    """Écrit un segment dans plan (si plan n'est pas vide) ; cpt[0] = nombre de segments."""
    i = cpt[0]
    if plan.shape[0] > 0:
        plan[i, 0] = k
        plan[i, 1] = a
        plan[i, 2] = b
        plan[i, 3] = typ
        plan[i, 4] = j
    cpt[0] = i + 1


@njit(cache=True)
def _executer(j, k, pm, s, o, P, mf, us, cyc, jr, nxt, Treel, Mdur, R, plan, cpt):
    """Maintenance éventuelle puis op o du job j sur k à partir de s (pannes selon Treel)."""
    C = Treel.shape[1]
    st = 1.0 * s
    if pm:                                      # la maintenance commence dès que la machine est libre
        d = Mdur[k, min(cyc[k], C - 1)]
        debut = mf[k] if mf[k] < s else s
        _ajouter(plan, cpt, k, debut, debut + d, 2, -1)
        st = debut + d if debut + d > s else s
        us[k] = 0.0
        cyc[k] += 1
    reste = 1.0 * P[o, k]
    fini = False
    while not fini:
        marge = Treel[k, min(cyc[k], C - 1)] - us[k]
        if reste <= marge + EPS:
            _ajouter(plan, cpt, k, st, st + reste, 1, j)
            st = st + reste
            us[k] += reste
            fini = True
        else:                                   # panne : l'op s'arrête au seuil, réparation, reprise
            h = 0.0
            if marge > 0.0:
                h = marge
                _ajouter(plan, cpt, k, st, st + h, 1, j)
            st = st + h + R[k]
            _ajouter(plan, cpt, k, st - R[k], st, 3, j)
            us[k] = 0.0
            cyc[k] += 1
            reste = reste - h
    mf[k] = st
    jr[j] = st
    nxt[j] += 1


@njit(cache=True)
def _completer(t, mf0, us0, cyc0, jr0, nxt0, jdeb, jnb, ops, P, reste, pmin,
               Tpol, Mpol, Treel, Mdur, R, regle, a_typ, a_j, a_k, t_attente, plan, opp=False):
    """Termine le planning. Retourne (C_max, nombre de segments écrits dans plan).
    opp=True : maintenance opportuniste (toute machine libre et usée sans op à lancer fait une maintenance)."""
    mf, us, cyc, jr, nxt = mf0.copy(), us0.copy(), cyc0.copy(), jr0.copy(), nxt0.copy()
    m, n = mf.shape[0], jr.shape[0]
    cpt = np.zeros(1, np.int64)
    s = t
    # --- action forcée (celle qu'on évalue)
    if a_typ == LANCER or a_typ == MAINT_PUIS_LANCER:
        o = ops[jdeb[a_j] + nxt[a_j]]
        _executer(a_j, a_k, a_typ == MAINT_PUIS_LANCER, s, o, P, mf, us, cyc, jr, nxt,
                  Treel, Mdur, R, plan, cpt)
    elif a_typ == MAINT:
        d = Mdur[a_k, min(cyc[a_k], Treel.shape[1] - 1)]
        _ajouter(plan, cpt, a_k, s, s + d, 2, -1)
        mf[a_k] = s + d
        us[a_k] = 0.0
        cyc[a_k] += 1
    elif a_typ == ATTENDRE:                 # rien ne démarre avant le prochain événement
        s = max(s, t_attente)
        for k in range(m):
            if mf[k] < s:
                mf[k] = s
        for j in range(n):
            if nxt[j] < jnb[j] and jr[j] < s:
                jr[j] = s
    restants = 0
    for j in range(n):
        restants += jnb[j] - nxt[j]
    # --- règle de complétion
    while restants > 0:
        while True:                       # lancer tout ce qui peut l'être à l'instant s
            bj, bk, bpm, bprio = -1, -1, False, -1e300
            for j in range(n):
                if nxt[j] >= jnb[j] or jr[j] > s + EPS:
                    continue
                o = ops[jdeb[j] + nxt[j]]
                kk, ff, pp = -1, 1e300, False
                for k in range(m):
                    p = P[o, k]
                    if p <= 0:
                        continue
                    besoin = us[k] + p > Tpol[k] + EPS and us[k] > EPS
                    f = max(mf[k] + (Mpol[k] if besoin else 0.0) - s, 0.0) + p
                    if f < ff - EPS:
                        kk, ff, pp = k, f, besoin
                if mf[kk] > s + EPS:          # machine EFT occupée : job ignoré pour l'instant
                    continue
                if regle == 0:
                    prio = reste[o]
                elif regle == 1:
                    prio = float(jnb[j] - nxt[j])
                elif regle == 2:
                    prio = -pmin[o]
                else:
                    prio = pmin[o]
                if prio > bprio + EPS:
                    bj, bk, bpm, bprio = j, kk, pp, prio
            if bj < 0:
                break
            o = ops[jdeb[bj] + nxt[bj]]
            _executer(bj, bk, bpm, s, o, P, mf, us, cyc, jr, nxt, Treel, Mdur, R, plan, cpt)
            restants -= 1
        if restants == 0:
            break
        if opp:                           # temps mort : maintenance sur les machines libres et usées
            for k in range(m):
                if mf[k] <= s + EPS and us[k] > EPS:
                    d = Mdur[k, min(cyc[k], Treel.shape[1] - 1)]
                    _ajouter(plan, cpt, k, s, s + d, 2, -1)
                    mf[k] = s + d
                    us[k] = 0.0
                    cyc[k] += 1
        prochain = 1e300                  # prochain événement
        for k in range(m):
            if mf[k] > s + EPS and mf[k] < prochain:
                prochain = mf[k]
        for j in range(n):
            if nxt[j] < jnb[j] and jr[j] > s + EPS and jr[j] < prochain:
                prochain = jr[j]
        if prochain >= 1e299:
            return 1e300, cpt[0]             # blocage (ne devrait pas arriver)
        s = prochain
    cmax = 0.0
    for j in range(n):
        if jr[j] > cmax:
            cmax = jr[j]
    return cmax, cpt[0]



# ---------------------------------------------------------------------------------------------
# Décodeur et recuit simulé À PARTIR D'UNE SITUATION EN COURS (utilisés par le « juge recuit »)
# Une solution de la suite = OS (ordre des opérations restantes, codé par numéros de jobs ; un
# élément négatif -k-1 = maintenance sur la machine k) et MS (machine choisie pour chaque opération). Décodage : chaque opération au plus tôt après son job
# et sa machine ; maintenance juste avant si elle ne tient pas dans la marge (commencée dès que la
# machine est libre). Mêmes règles que metaheuristiques/codage.py, mais en partant de l'état e.
# ---------------------------------------------------------------------------------------------
@njit(cache=True)
def _decoder_etat(mf0, us0, cyc0, jr0, nxt0, jdeb, ops, OS, MS, P, Tpol, Treel, Mdur, R, plan, cpt):
    mf, us, cyc, jr, nxt = mf0.copy(), us0.copy(), cyc0.copy(), jr0.copy(), nxt0.copy()
    for idx in range(OS.shape[0]):
        j = OS[idx]
        if j < 0:                                 # élément « maintenance sur la machine -j-1 »
            k = -j - 1
            if us[k] > EPS:
                d = Mdur[k, min(cyc[k], Treel.shape[1] - 1)]
                _ajouter(plan, cpt, k, mf[k], mf[k] + d, 2, -1)
                mf[k] += d
                us[k] = 0.0
                cyc[k] += 1
            continue
        o = ops[jdeb[j] + nxt[j]]
        k = MS[o]
        p = P[o, k]
        pm = us[k] + p > Tpol[k] + EPS and us[k] > EPS
        s = jr[j] if jr[j] > mf[k] else mf[k]
        _executer(j, k, pm, s, o, P, mf, us, cyc, jr, nxt, Treel, Mdur, R, plan, cpt)
    cmax = 0.0
    for j in range(jr.shape[0]):
        if jr[j] > cmax:
            cmax = jr[j]
    return cmax


@njit(cache=True)
def _voisin(OS, MS, rem_ops, elig, elig_deb, elig_nb, OS2, MS2):
    """Un voisin au hasard (déplacer une opération dans OS, ou changer sa machine). False si neutre."""
    L = OS.shape[0]
    OS2[:] = OS
    MS2[:] = MS
    if np.random.random() < 0.5:
        if L < 2:
            return False
        i = np.random.randint(L)
        k = np.random.randint(L)
        if OS[i] == OS[k]:
            return False
        v = OS[i]
        if i < k:
            for q in range(i, k):
                OS2[q] = OS[q + 1]
        else:
            for q in range(i, k, -1):
                OS2[q] = OS[q - 1]
        OS2[k] = v
        return True
    o = rem_ops[np.random.randint(rem_ops.shape[0])]
    if elig_nb[o] < 2:
        return False
    k = elig[elig_deb[o] + np.random.randint(elig_nb[o])]
    if k == MS[o]:
        return False
    MS2[o] = k
    return True


@njit(cache=True)
def _recuit_etat(mf, us, cyc, jr, nxt, jdeb, ops, OS0, MS0, rem_ops, elig, elig_deb, elig_nb,
                 P, Tpol, Treel, Mdur, R, n_eval, p0, ratio_fin, graine):
    """Recuit simulé sur la suite du planning (n_eval décodages). Retourne le meilleur C_max."""
    np.random.seed(graine)
    vide = np.zeros((0, 5))
    cpt = np.zeros(1, np.int64)
    OS, MS = OS0.copy(), MS0.copy()
    OS2, MS2 = OS0.copy(), MS0.copy()
    c = _decoder_etat(mf, us, cyc, jr, nxt, jdeb, ops, OS, MS, P, Tpol, Treel, Mdur, R, vide, cpt)
    meilleur = c
    if rem_ops.shape[0] < 2 or n_eval <= 0:
        return meilleur
    # température initiale : une dégradation moyenne acceptée avec la probabilité p0
    somme, nb = 0.0, 0
    for _ in range(30):
        if _voisin(OS, MS, rem_ops, elig, elig_deb, elig_nb, OS2, MS2):
            d = _decoder_etat(mf, us, cyc, jr, nxt, jdeb, ops, OS2, MS2, P, Tpol, Treel, Mdur, R, vide, cpt) - c
            if d > 0:
                somme += d
                nb += 1
    T0 = (somme / nb if nb > 0 else 1.0) / -np.log(p0)
    it, essais = 0, 0
    while it < n_eval and essais < 20 * n_eval:
        essais += 1
        if not _voisin(OS, MS, rem_ops, elig, elig_deb, elig_nb, OS2, MS2):
            continue
        T = T0 * ratio_fin ** (it / n_eval)
        c2 = _decoder_etat(mf, us, cyc, jr, nxt, jdeb, ops, OS2, MS2, P, Tpol, Treel, Mdur, R, vide, cpt)
        it += 1
        d = c2 - c
        if d <= 0 or np.random.random() < np.exp(-d / max(T, 1e-12)):
            OS[:] = OS2
            MS[:] = MS2
            c = c2
            if c < meilleur:
                meilleur = c
    return meilleur


class Etat:
    """Photo compacte d'une situation de l'atelier (tableaux numpy)."""
    __slots__ = ("t", "mf", "us", "cyc", "jr", "nxt", "t_attente", "engages")

    def __init__(self, t, mf, us, cyc, jr, nxt, t_attente, engages):
        self.t, self.mf, self.us, self.cyc, self.jr, self.nxt = t, mf, us, cyc, jr, nxt
        self.t_attente, self.engages = t_attente, engages


class MoteurRapide:
    """Moteur de complétion pour une instance. En déterministe, seuils et durées = ceux de l'instance."""

    def __init__(self, inst, Tpol=None, Mpol=None, Treel=None, Mdur=None):
        self.inst = inst
        P = np.asarray(inst.P, dtype=np.float64)
        self.P = P
        el = P > 0
        self.pmin = np.where(el, P, np.inf).min(1)
        self.jnb = np.array([len(o) for o in inst.job_ops], dtype=np.int64)
        self.jdeb = np.concatenate([[0], np.cumsum(self.jnb)[:-1]]).astype(np.int64)
        self.ops = np.concatenate([np.asarray(o, dtype=np.int64) for o in inst.job_ops])
        self.reste = np.zeros(inst.n_ops)
        for ops in inst.job_ops:
            self.reste[ops] = np.cumsum(self.pmin[ops][::-1])[::-1]
        self.R = np.asarray(inst.R, dtype=np.float64)
        self.Tpol = np.asarray(inst.T if Tpol is None else Tpol, dtype=np.float64)
        self.Mpol = np.asarray(inst.M if Mpol is None else Mpol, dtype=np.float64)
        self.Treel = np.asarray(self.Tpol[:, None] if Treel is None else Treel, dtype=np.float64)
        self.Mdur = np.asarray(self.Mpol[:, None] if Mdur is None else Mdur, dtype=np.float64)
        self._vide = np.zeros((0, 5))

    # ------------------------------------------------------------------ état
    def etat(self, env):
        """Photo de l'état courant de l'environnement (actions déjà engagées comprises)."""
        sim, inst = env.sim, self.inst
        t = float(sim.t)
        mf = np.full(inst.m, t)
        us = np.array([sim.wear(k) for k in range(inst.m)], dtype=np.float64)
        cyc = np.zeros(inst.m, dtype=np.int64)
        jr = np.full(inst.n, t)
        nxt = sim.next_op.astype(np.int64).copy()
        engages = []                      # segments déjà décidés mais pas encore dans sim.segments
        for j in range(inst.n):
            if sim.job_finished(j):
                jr[j] = sim.job_free_since[j]
        for k in range(inst.m):
            st = sim.status[k]
            if st == IDLE:
                continue
            fin = float(sim.end[k])
            if st == PROC:
                j = sim.mjob[k]
                us[k] = sim.wear_base[k] + (fin - sim.phase_start[k])
                if sim.pending[k] > EPS:            # panne en fin de segment (régime B)
                    engages += [(k, fin, fin + self.R[k], REPAIR, j),
                                (k, fin + self.R[k], fin + self.R[k] + sim.pending[k], PROC, j)]
                    fin += self.R[k] + sim.pending[k]
                    us[k] = sim.pending[k]
                    cyc[k] += 1
                jr[j] = fin
                nxt[j] += 1
            elif st == REPAIR:
                j = sim.mjob[k]
                engages.append((k, fin, fin + sim.pending[k], PROC, j))
                fin += sim.pending[k]
                us[k] = sim.pending[k]
                jr[j] = fin
                nxt[j] += 1
            elif st == PM:
                us[k] = 0.0
                j = sim.after_pm[k]
                if j >= 0:                          # macro « maintenance puis op »
                    p = inst.P[sim.cur_op(j), k]
                    engages.append((k, fin, fin + p, PROC, j))
                    fin += p
                    us[k] = p
                    jr[j] = fin
                    nxt[j] += 1
            mf[k] = fin
        t_att = t + sim.next_event_dt() if sim.can_wait() else t
        return Etat(t, mf, us, cyc, jr, nxt, t_att, engages)

    # ------------------------------------------------------------------ complétion
    def completer(self, e, action=("N", -1, -1), regle="MWKR", avec_planning=False, opp=False):
        """C_max obtenu en faisant `action` (candidat de l'environnement) puis en suivant la règle.
        Avec avec_planning=True, retourne aussi les segments ajoutés (k, début, fin, type, job)."""
        typ, j, k = action
        plan = np.zeros((2 * self.inst.n_ops + 4 * self.inst.m + 8, 5)) if avec_planning else self._vide
        cmax, npl = _completer(e.t, e.mf, e.us, e.cyc, e.jr, e.nxt, self.jdeb, self.jnb, self.ops,
                               self.P, self.reste, self.pmin, self.Tpol, self.Mpol, self.Treel, self.Mdur,
                               self.R, REGLES[regle], CODE.get(typ, AUCUNE), int(j), int(k),
                               e.t_attente, plan, bool(opp))
        if not avec_planning:
            return cmax
        segs = [(int(r[0]), float(r[1]), float(r[2]), int(r[3]), int(r[4])) for r in plan[:npl]]
        return cmax, segs

    def appliquer(self, e, action):
        """Situation obtenue en faisant `action` dans la situation e (sans rien compléter)."""
        typ, j, k = action
        mf, us, cyc, jr, nxt = e.mf.copy(), e.us.copy(), e.cyc.copy(), e.jr.copy(), e.nxt.copy()
        t = e.t
        cpt = np.zeros(1, np.int64)
        if typ in ("D", "J"):
            o = self.ops[self.jdeb[j] + nxt[j]]
            _executer(int(j), int(k), typ == "J", t, o, self.P, mf, us, cyc, jr, nxt,
                      self.Treel, self.Mdur, self.R, self._vide, cpt)
        elif typ == "P":
            d = self.Mdur[k, min(cyc[k], self.Mdur.shape[1] - 1)]
            mf[k], us[k] = t + d, 0.0
            cyc[k] += 1
        elif typ in ("W", "C"):
            t = max(t, e.t_attente)
            mf = np.maximum(mf, t)
            rest = nxt < self.jnb
            jr[rest] = np.maximum(jr[rest], t)
        return Etat(t, mf, us, cyc, jr, nxt, t, [])

    def _eligibles(self):
        if not hasattr(self, "_elig"):
            el = [np.flatnonzero(self.P[o] > 0) for o in range(self.inst.n_ops)]
            self._elig = (np.concatenate(el).astype(np.int64),
                          np.concatenate([[0], np.cumsum([len(x) for x in el])[:-1]]).astype(np.int64),
                          np.array([len(x) for x in el], dtype=np.int64))
        return self._elig

    def suite_depuis_planning(self, e, segs):
        """(OS, MS) de la suite du planning `segs` (planning complet ou suite) à partir de la situation e :
        seules les opérations pas encore lancées dans e (position >= e.nxt[j]) sont gardées."""
        par_job = {}
        fins_rep = {(int(s[0]), int(s[4]), round(float(s[2]), 6)) for s in segs if s[3] == REPAIR}
        for k, a, b, typ, j in sorted([s for s in segs if s[3] == PROC], key=lambda s: (s[1], s[0])):
            if (int(k), int(j), round(float(a), 6)) in fins_rep:
                continue                                  # reprise d'une op coupée par une panne
            par_job.setdefault(j, []).append((a, j, k))
        suite, MS = [], np.zeros(self.inst.n_ops, dtype=np.int64)
        for k, a, b, typ, j in segs:                      # maintenances décidées après la situation e
            if typ == PM and a >= e.mf[k] - 1e-9:
                suite.append((a, -1, -int(k) - 1))
        for j, lst in par_job.items():
            lst = sorted(lst)
            for q, (a, _, k) in enumerate(lst[-(self.jnb[j] - e.nxt[j]):] if self.jnb[j] > e.nxt[j] else []):
                pos = e.nxt[j] + q
                MS[self.ops[self.jdeb[j] + pos]] = k
                suite.append((a, pos, j))
        OS = np.array([j for a, pos, j in sorted(suite)], dtype=np.int64)
        return OS, MS

    def valeur_recuit(self, e, evaluations, p0=0.01, ratio_fin=0.01, graine=0, regle="MWKR", depart=None):
        """C_max atteint par un recuit simulé court sur la suite du planning, à partir de la situation e.
        Départ du recuit : `depart` (planning, p. ex. celui que l'agent termine lui-même), sinon la
        complétion du moteur (règle). Retourne (C_max recuit, C_max du départ)."""
        if depart is None:
            _, depart = self.completer(e, avec_planning=True, regle=regle)
        OS, MS = self.suite_depuis_planning(e, depart)
        vide, cpt = self._vide, np.zeros(1, np.int64)
        c_dep = _decoder_etat(e.mf, e.us, e.cyc, e.jr, e.nxt, self.jdeb, self.ops, OS, MS, self.P, self.Tpol,
                              self.Treel, self.Mdur, self.R, vide, cpt)
        if len(OS) < 2:
            return c_dep, c_dep
        c_regle = c_dep
        rem = np.array([self.ops[self.jdeb[j] + q] for j in range(self.inst.n)
                        for q in range(e.nxt[j], self.jnb[j])], dtype=np.int64)
        elig, deb, nb = self._eligibles()
        c = _recuit_etat(e.mf, e.us, e.cyc, e.jr, e.nxt, self.jdeb, self.ops, OS, MS, rem, elig, deb, nb,
                         self.P, self.Tpol, self.Treel, self.Mdur, self.R, int(evaluations),
                         float(p0), float(ratio_fin), int(graine))
        return min(c, c_regle), c_regle

    def evaluer(self, env, regles=("MWKR",)):
        """C_max estimé pour chaque candidat courant de l'environnement (meilleur sur les règles)."""
        e = self.etat(env)
        return [min(self.completer(e, c, r) for r in regles) for c in env._C]

    def borne_inf(self, e):
        """Borne inférieure du C_max depuis l'état e (valable en déterministe, sans panne)."""
        lb = float(e.jr.max())
        charge = 0.0
        for j in range(self.inst.n):
            if e.nxt[j] < self.jnb[j]:
                o = self.ops[self.jdeb[j] + e.nxt[j]]
                lb = max(lb, e.jr[j] + self.reste[o])
                charge += self.reste[o]
        lb = max(lb, (np.maximum(e.mf, e.t).sum() + charge) / self.inst.m)
        return lb
