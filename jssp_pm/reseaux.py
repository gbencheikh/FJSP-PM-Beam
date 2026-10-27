"""Choix, sauvegarde et chargement des réseaux de politique.

  « candidats » : CandNet (réseau d'origine, caractéristiques calculées à la main)
  « graphe »    : GrapheNet (réseau de graphe opérations–machines, piste 3)

Tous les réseaux ont la même interface :
  obs = net.observe(env)          état courant -> observation (numpy)
  lot = net.collate([obs, ...])   liste d'observations -> tenseurs
  logits, valeur = net(*lot)

Format de fichier : {"type", "kwargs", "etat"}. Les anciens fichiers (state_dict brut d'un
CandNet, p. ex. models/v3/*_best.pt) sont toujours lisibles.
"""
import torch

from .fjsp_ppo import CandNet
from .fjsp_graphe import GrapheNet

RESEAUX = {"candidats": CandNet, "graphe": GrapheNet}


def creer_reseau(type="candidats", **kwargs):
    return RESEAUX[type](**kwargs)


def sauver_reseau(net, chemin):
    torch.save(dict(type=net.type, kwargs=net.kwargs, etat=net.state_dict()), chemin)


def lire_etat(chemin):
    d = torch.load(chemin, weights_only=False)
    return d["etat"] if isinstance(d, dict) and "etat" in d else d


def charger_reseau(chemin):
    d = torch.load(chemin, weights_only=False)
    if isinstance(d, dict) and "etat" in d:
        net = RESEAUX[d["type"]](**d["kwargs"])
        net.load_state_dict(d["etat"])
    else:
        net = CandNet()
        net.load_state_dict(d)
    net.eval()
    return net
