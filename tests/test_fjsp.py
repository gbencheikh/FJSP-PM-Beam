import glob
import numpy as np
from jssp_pm.fjsp_instance import load_fjs, generate_fjsp, parse_fjs
from jssp_pm.fjsp_env import FJSPEnv
from jssp_pm.fjsp_heuristics import FHeuristic, run
from jssp_pm.fjsp_cpsat import check, solve
from jssp_pm.simulator import PROC


def test_parse_kacem1():
    P, job_ops = parse_fjs("Instances/5_Kacem/Kacem1.fjs")
    assert P.shape == (12, 5) and [len(o) for o in job_ops] == [3, 3, 4, 2]
    assert P[5, 3] == 54 and P[0, 0] == 2  # op 3 du job 2 sur M4 ; op 1 du job 1 sur M1


def valid(inst, sim):
    for j, ops in enumerate(inst.job_ops):
        segs = sorted([s for s in sim.segments if s[4] == j and s[3] == PROC], key=lambda s: s[1])
        assert segs[0][1] >= 0
    for k in range(inst.m):
        sk = sorted([s for s in sim.segments if s[0] == k], key=lambda s: s[1])
        for a, b in zip(sk, sk[1:]):
            assert b[1] >= a[2] - 1e-9


def test_random_policy_reward_identity():
    rng = np.random.default_rng(0)
    for t in range(60):
        inst = generate_fjsp(rng, int(rng.integers(3, 9)), int(rng.integers(2, 7)),
                             stochastic=bool(t % 2))
        env = FJSPEnv(lam_p=0, lam_m=0)
        ret = env.reset(inst, rng)
        done = env.sim.done()
        while not done:
            X, g = env.features()
            assert X.shape[0] == len(env._C) > 0 and np.isfinite(X).all() and np.isfinite(g).all()
            r, done = env.step(int(rng.integers(len(env._C))))
            ret += r
        assert abs(-ret * inst.meta["u"] - env.sim.metrics()["cmax"]) < 1e-6
        valid(inst, env.sim)


def test_jit_no_breakdown_on_benchmarks():
    env = FJSPEnv()
    for f in glob.glob("Instances/*/*.fjs"):
        inst = load_fjs(f)
        m, sim = run(env, FHeuristic("jitp"), inst)
        assert m["breakdowns"] == 0
        check(inst, sim.segments)


def test_cpsat_kacem1():
    r = solve(load_fjs("Instances/5_Kacem/Kacem1.fjs"), time_limit=30)
    assert r["status"] == "OPTIMAL" and r["cmax"] >= 11  # >= optimum sans maintenance
