"""Réseau NON entraîné (poids aléatoires), même architecture qu'un modèle de référence.

Sert à l'ablation « faisceau guidé par un réseau non entraîné » : si l'anticipation fait aussi bien
avec ce réseau qu'avec le réseau entraîné, ce n'est pas l'apprentissage qui guide la recherche.

  python -m outils.reseau_aleatoire --ref models/imitation/cand_ft_best.pt --graine 0 --out models/aleatoire/cand_aleatoire_g0.pt
"""
import argparse, os, sys
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jssp_pm.reseaux import charger_reseau, creer_reseau, sauver_reseau


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="models/imitation/cand_ft_best.pt")
    ap.add_argument("--graine", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ref = charger_reseau(a.ref)
    torch.manual_seed(a.graine)
    net = creer_reseau(ref.type, **ref.kwargs)        # initialisation par défaut de PyTorch
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    sauver_reseau(net, a.out)
    n = sum(p.numel() for p in net.parameters())
    print(f"réseau {ref.type} non entraîné, {n} paramètres, graine {a.graine} -> {a.out}")


if __name__ == "__main__":
    main()
