"""Tests du moteur rapide : plannings valides, cohérence avec le simulateur, borne inférieure."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from train_v3 import sample_v3
from jssp_pm.fjsp_env3 import FJSPEnv3
from jssp_pm.moteur_rapide import MoteurRapide
from imitation.rejeu import rejouer


def verifier(inst, segs):
    """Planning complet valide : pas de chevauchement, usure <= T, précédences, toutes les ops."""
    for k in range(inst.m):
        sk = sorted([s for s in segs if s[0] == k], key=lambda s: (s[1], s[2]))
        for a, b in zip(sk, sk[1:]):
            assert b[1] >= a[2] - 1e-6, ("chevauchement", a, b)
        c = 0
        for s in sk:
            if s[3] == 1:
                c += s[2] - s[1]
                assert c <= inst.T[k] + 1e-6, ("usure", k, s)
            elif s[2] > s[1]:
                c = 0
    for j, ops in enumerate(inst.job_ops):
        js = sorted([s for s in segs if s[4] == j and s[3] == 1], key=lambda s: s[1])
        assert len(js) == len(ops)
        fin = 0
        for o, s in zip(ops, js):
            assert inst.P[o, s[0]] > 0 and abs((s[2] - s[1]) - inst.P[o, s[0]]) < 1e-6
            assert s[1] >= fin - 1e-6
            fin = s[2]
    return max(s[2] for s in segs if s[3] == 1)


def test_completions_valides():
    rng = np.random.default_rng(0)
    env = FJSPEnv3("full", True)
    for i in range(4):
        inst = sample_v3(rng, "A", "base" if i % 2 else "large")
        mr = MoteurRapide(inst)
        env.reset(inst)
        pas = 0
        while not env.sim.done():
            if pas % 6 == 1:
                e = mr.etat(env)
                for c in env._C:
                    cm, segs = mr.completer(e, c, avec_planning=True)
                    total = list(env.sim.segments) + e.engages + segs
                    assert abs(verifier(inst, total) - cm) < 1e-6
                    assert mr.borne_inf(e) <= cm + 1e-6
                    assert abs(mr.completer(e, c) - cm) < 1e-9          # même résultat sans planning
                _, cr, _ = rejouer(FJSPEnv3("full", True), inst, total)
                assert cr <= cm + 1e-6                                  # le simulateur confirme
            env.step(int(rng.integers(len(env._C))))
            pas += 1


def test_meme_cmax_que_le_simulateur():
    rng = np.random.default_rng(9)
    env = FJSPEnv3("full", True)
    egal = 0
    for i in range(10):
        inst = sample_v3(rng, "A", "base" if i % 2 else "large")
        mr = MoteurRapide(inst)
        env.reset(inst)
        cm, segs = mr.completer(mr.etat(env), avec_planning=True)
        _, cr, _ = rejouer(FJSPEnv3("full", True), inst, segs)
        assert cr <= cm + 1e-6
        egal += abs(cr - cm) < 1e-6
    assert egal >= 8


def test_pannes_stochastiques():
    inst = sample_v3(np.random.default_rng(1), "A", "large")
    Treel = inst.T[:, None] * np.random.default_rng(0).uniform(0.6, 1.1, (inst.m, 30))
    mr = MoteurRapide(inst, Treel=Treel)
    env = FJSPEnv3("full", True)
    env.reset(inst)
    cm, segs = mr.completer(mr.etat(env), avec_planning=True)
    assert any(s[3] == 3 for s in segs)                 # des pannes apparaissent
    assert cm >= MoteurRapide(inst).completer(mr.etat(env)) - 1e-6


def test_juge_recuit():
    """Le recuit du juge part exactement du planning de l'agent et ne fait jamais pire."""
    from jssp_pm.anticipation import cloner
    rng = np.random.default_rng(3)
    env = FJSPEnv3("full", True)
    for i in range(3):
        inst = sample_v3(rng, "A", "large")
        mr = MoteurRapide(inst)
        env.reset(inst)
        for _ in range(int(rng.integers(5, 60))):
            if env.sim.done():
                break
            env.step(int(rng.integers(len(env._C))))
        if env.sim.done():
            continue
        e = mr.etat(env)
        for c in env._C[:3]:                                  # appliquer puis compléter == compléter l'action
            assert abs(mr.completer(e, c) - mr.completer(mr.appliquer(e, c))) < 1e-6
        e3 = cloner(env)
        while not e3.sim.done():
            e3.step(int(rng.integers(len(e3._C))))
        c, c_dep = mr.valeur_recuit(e, 500, depart=list(e3.sim.segments))
        assert c_dep <= e3.sim.last_completion + 1e-6 and c <= c_dep + 1e-6
