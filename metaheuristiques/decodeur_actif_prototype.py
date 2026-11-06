"""PROTOTYPE (exploratoire, 04/11/2026, 3e relecture R1) : décodeur ACTIF pour les métaheuristiques.
Chaque opération (ordre de OS, machine de MS) est placée au plus tôt sur sa machine, y compris dans un trou entre deux
activités déjà placées, si (i) elle tient dans le trou après la fin de son prédécesseur de job et (ii) la charge du segment
d'usure (entre deux maintenances) qui contient le trou, augmentée de p, reste ≤ T_k (alors aucune opération du segment ne
dépasse le seuil). Sinon elle est placée en fin de machine, avec une maintenance juste avant si le dernier segment déborde."""
EPS = 1e-9


def decoder_actif(inst, OS, MS, avec_planning=False):
    P, T, M = inst.P, inst.T, inst.M
    prochaine = [0] * inst.n
    fin_job = [0.0] * inst.n
    act = [[] for _ in range(inst.m)]       # (début, fin, type, segment)
    charge = [[0.0] for _ in range(inst.m)] # charge de chaque segment
    n_pm, cmax = 0, 0.0
    for j in OS:
        o = inst.job_ops[j][prochaine[j]]; prochaine[j] += 1
        k = MS[o]; p = float(P[o, k]); r = fin_job[j]
        L = act[k]; place = None
        prec_fin, seg = 0.0, 0
        for i, (s, e, typ, sg) in enumerate(L):
            d = max(r, prec_fin)
            if typ == 1 and d + p <= s + EPS and charge[k][sg] + p <= T[k] + EPS:
                place = (i, d, sg); break
            if typ == 2 and d + p <= s + EPS and charge[k][seg] + p <= T[k] + EPS:
                place = (i, d, seg); break
            prec_fin = e
            seg = sg + 1 if typ == 2 else sg
        if place is None:
            seg = len(charge[k]) - 1
            debut_libre = L[-1][1] if L else 0.0
            if charge[k][seg] + p > T[k] + EPS:
                L.append((debut_libre, debut_libre + M[k], 2, seg)); n_pm += 1
                charge[k].append(0.0); seg += 1; debut_libre += M[k]
            d = max(r, debut_libre)
            L.append((d, d + p, 1, seg)); charge[k][seg] += p
        else:
            i, d, sg = place
            L.insert(i, (d, d + p, 1, sg)); charge[k][sg] += p
        fin_job[j] = d + p if place is None else place[1] + p
        cmax = max(cmax, fin_job[j])
    if avec_planning:
        pl = [(k, s, e, typ, -1) for k in range(inst.m) for (s, e, typ, sg) in act[k]]
        return cmax, n_pm, pl
    return cmax, n_pm
