import sys, time, numpy as np
sys.path.insert(0, "/home/claude/d5"); sys.path.insert(0, "/home/claude")
from metaheuristiques.instances import charger_instances
from metaheuristiques import recuit_simule, codage
from metaheuristiques.codage import Budget
from decodeur_actif import decoder_actif
import os; os.chdir("/home/claude/d5")
fs = float(sys.argv[1])
insts = charger_instances(["Kacem"], facteur_seuil=fs)
for inst in insts[:7] if len(sys.argv) < 3 else insts:
    res = {}
    for nom, dec in (("semi", codage.decoder), ("actif", decoder_actif)):
        recuit_simule.decoder = dec
        cs = []; t0 = time.time()
        for g in range(3):
            c, sol, _ = recuit_simule.resoudre(inst, Budget(evaluations=50000), np.random.default_rng(g), p0=0.3, ratio_fin=1e-4)
            cs.append(c)
        res[nom] = (cs, round(time.time() - t0, 1))
    print(inst.name, res, flush=True)
