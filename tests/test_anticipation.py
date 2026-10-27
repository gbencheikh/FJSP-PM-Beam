"""Test de l'agent qui anticipe : planning valide, jamais pire que l'agent glouton."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_v3 import sample_v3
from jssp_pm.anticipation import AgentAnticipation
from jssp_pm.reseaux import creer_reseau
from jssp_pm.fjsp_env3 import FJSPEnv3, run3
from jssp_pm.fjsp_ppo import PPOPolicy
from test_moteur import verifier


def test_anticipation():
    net = creer_reseau("candidats")
    net.eval()
    for s in range(3):
        inst = sample_v3(np.random.default_rng(s), "A", "base")
        glouton = run3(FJSPEnv3("full", True), PPOPolicy(net), inst)[0]["cmax"]
        for B, K, n in [(1, 1, net), (3, 2, net), (2, 0, None)]:
            c, plan, st = AgentAnticipation(n, B, K).planifier(inst)
            assert abs(verifier(inst, plan) - c) < 1e-6
            if n is not None:
                assert c <= glouton + 1e-6
