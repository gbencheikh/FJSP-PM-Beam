"""D5 (2e révision, déclaré dans PROTOCOLE § 3 septies, entrée « D5 ») : apprendre au réseau à FILTRER.

Le réseau final (imitation + PPO, graine 0) a été entraîné à agir seul. Dans la recherche, son rôle est différent : garder,
parmi les actions valides d'une situation, les K que la complétion classerait le mieux. D5 change seulement la CIBLE
d'apprentissage ; architecture, caractéristiques, moteur de complétion et recherche sont inchangés.

1) générer : sur des instances d'ENTRAÎNEMENT (train_v3.sample_v3, graines 2 000 000 + i, moitié « base », moitié « large »,
   jamais de benchmark), on exécute le faisceau 5×4 guidé par le réseau final et, pour chaque situation s du faisceau
   (retenue avec la probabilité --proba-etat), on calcule pour TOUTES les actions valides a la valeur H(s'(s,a)) de la
   complétion (MoteurRapide.completer, règle MWKR), exprimée en unités u.
   python -m imitation.filtre_appris generer --instances 300 --processus 8
2) entraîner : départ = réseau final ; perte = entropie croisée entre π_θ(·|s) et q(a|s) ∝ exp(−(H_a − min H)/τ), τ = 1
   (en unités u) ; Adam, lr 1e-4, 10 époques, lots de 256 ; la tête de valeur n'est pas entraînée (inutile au filtre).
   Modèle retenu : meilleure époque selon le C_max moyen du faisceau 5×4 guidé par le réseau sur les 24 instances de
   validation (val_set_v3), jamais sur les benchmarks.
   python -m imitation.filtre_appris entrainer
Sorties : imitation/filtre_donnees/*.pt ; models/filtre/filtre_best.pt, filtre_log.json.
"""
import argparse, glob, json, os, sys, time
import multiprocessing as mp
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train_v3 import sample_v3, val_set_v3            # noqa: E402
from jssp_pm.anticipation import AgentAnticipation   # noqa: E402
from jssp_pm.moteur_rapide import MoteurRapide       # noqa: E402
from jssp_pm.reseaux import charger_reseau, sauver_reseau   # noqa: E402

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
DONNEES = os.path.join(ICI, "filtre_donnees")
MODELE_INIT = os.path.join(RACINE, "models", "imitation", "cand_ft_best.pt")
SORTIE = os.path.join(RACINE, "models", "filtre", "filtre")
GRAINE0 = 2_000_000


class Collecteur(AgentAnticipation):
    """Faisceau du réseau final ; enregistre (observation, H de toutes les actions) des situations visitées."""

    def __init__(self, net, proba, rng, **kw):
        super().__init__(net, **kw)
        self.proba, self.rng, self.lecons = proba, rng, []

    def planifier(self, inst):
        self._mr = MoteurRapide(inst)
        return super().planifier(inst)

    def _logp(self, envs):
        for e in envs:
            if len(e._C) > 1 and self.rng.random() < self.proba:
                et = self._mr.etat(e)
                H = np.array([self._mr.completer(et, c, "MWKR") for c in e._C], dtype=np.float64) / e.u
                self.lecons.append((self.net.observe(e), H.astype(np.float32)))
        return super()._logp(envs)


def une_instance(args):
    i, proba = args
    torch.set_num_threads(1)
    fichier = os.path.join(DONNEES, f"lecons_{i:05d}.pt")
    if os.path.exists(fichier):
        return i, -1, 0.0
    t0 = time.time()
    dist = "base" if i % 2 == 0 else "large"
    inst = sample_v3(np.random.default_rng(GRAINE0 + i), "A", dist)
    ag = Collecteur(charger_reseau(MODELE_INIT), proba, np.random.default_rng(i), largeur=5, k=4)
    ag.planifier(inst)
    torch.save(ag.lecons, fichier)
    return i, len(ag.lecons), time.time() - t0


def generer(a):
    os.makedirs(DONNEES, exist_ok=True)
    ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
    with ctx.Pool(a.processus) as pool:
        for i, n, dt in pool.imap_unordered(une_instance, [(i, a.proba_etat) for i in range(a.instances)]):
            print(f"instance {i} : {n} situations, {dt:.1f} s", flush=True)


def perte(net, lot, tau):
    logits, _ = net(*net.collate([x[0] for x in lot]))
    Q = torch.zeros_like(logits)
    for b, (_, H) in enumerate(lot):
        h = torch.from_numpy(H)
        Q[b, :len(h)] = torch.softmax(-(h - h.min()) / tau, -1)
    logp = torch.log_softmax(logits, -1)
    l = -(Q * logp).sum(-1).mean()
    # accord : l'action préférée du réseau est-elle parmi les meilleures complétions ?
    top = logits.argmax(-1)
    acc = np.mean([float(H[int(top[b])] <= H.min() + 1e-6) for b, (_, H) in enumerate(lot)])
    return l, float(l.detach()), acc


def valider(net, V):
    ag = AgentAnticipation(net, largeur=5, k=4)
    return float(np.mean([ag.planifier(inst)[0] for inst in V]))


def entrainer(a):
    torch.manual_seed(a.seed)
    rng = np.random.default_rng(a.seed)
    L = []
    for f in sorted(glob.glob(os.path.join(DONNEES, "lecons_*.pt"))):
        L += torch.load(f, weights_only=False)
    print(f"{len(L)} situations", flush=True)
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    net = charger_reseau(MODELE_INIT)
    V = val_set_v3("A")
    best = valider(net, V)
    log = [dict(epoque=0, validation_faisceau_5x4=best)]
    sauver_reseau(net, SORTIE + "_best.pt")
    print(json.dumps(log[-1]), flush=True)
    opt = torch.optim.Adam([p for n, p in net.named_parameters() if not n.startswith("v.")], lr=a.lr)
    t0 = time.time()
    for ep in range(1, a.epoques + 1):
        net.train()
        perm = rng.permutation(len(L))
        P, ACC = [], []
        for s in range(0, len(L), a.lot):
            loss, p, acc = perte(net, [L[i] for i in perm[s:s + a.lot]], a.tau)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step(); P.append(p); ACC.append(acc)
        net.eval()
        c = valider(net, V)
        info = dict(epoque=ep, perte=round(float(np.mean(P)), 4), accord=round(float(np.mean(ACC)), 4),
                    validation_faisceau_5x4=c, minutes=round((time.time() - t0) / 60, 1))
        if c < best:
            best, info["meilleur"] = c, True
            sauver_reseau(net, SORTIE + "_best.pt")
        log.append(info)
        print(json.dumps(info), flush=True)
        json.dump(log, open(SORTIE + "_log.json", "w"), indent=1)
    print(f"retenu : {SORTIE}_best.pt (validation faisceau 5×4 {best:.2f})")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("generer"); g.add_argument("--instances", type=int, default=300)
    g.add_argument("--proba-etat", type=float, default=0.5); g.add_argument("--processus", type=int, default=8)
    e = sp.add_parser("entrainer"); e.add_argument("--epoques", type=int, default=10)
    e.add_argument("--lr", type=float, default=1e-4); e.add_argument("--lot", type=int, default=256)
    e.add_argument("--tau", type=float, default=1.0); e.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    generer(a) if a.cmd == "generer" else entrainer(a)


if __name__ == "__main__":
    main()
