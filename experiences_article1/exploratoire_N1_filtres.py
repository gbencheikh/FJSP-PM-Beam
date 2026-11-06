"""EXPLORATOIRE (non déclaré), 02/11/2026 — 2e rapport de relecture, point N1 : Holm sur 4 (meilleur filtre),
filtre a priori (regle), test global (moyenne des 4 différences par instance), IC 90 %, effet minimal détectable."""
import os,sys,numpy as np
sys.path.insert(0,".")
from experiences_article1.statistiques import charger,wilcoxon,holm,bootstrap_ic,INSTANCES_REGLAGE,BANQUE
from metaheuristiques.instances import fichiers
REF=("Recuit simulé","evals=50000,depart=heuristique,params=taguchi")
noms=[os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte","HurinkLa","Kacem"])]
noms=[n for n in noms if n not in INSTANCES_REGLAGE]
def outil(b):
    v,t,ev=charger(b,"A",1.0)
    ec=lambda k: np.array([100*(np.mean(v[k][n])/np.mean(v[REF][n])-1) for n in noms])
    return ec
def ic90(d,n=10000):
    r=np.random.default_rng(0); m=d[r.integers(0,len(d),(n,len(d)))].mean(1); return np.percentile(m,5),np.percentile(m,95)
ec=outil(BANQUE)
R=[(5,4),(10,4),(20,4),(50,5)]
print("== mu=1 : réseau contre meilleur filtre, Holm sur 4 ; IC90 ; contre 'regle' (filtre a priori)")
ds,ps,pr,dr=[],[],[],[]
for B,K in R:
    er=ec(("RL:imit-ft",f"faisceau={B},k={K}"))
    fs={f:ec((f"Faisceau:filtre-{f}",f"faisceau={B},k={K},filtre={f}")) for f in ("regle","fin","borne")}
    best=min(fs,key=lambda f:fs[f].mean()); d=er-fs[best]; ds.append(d); ps.append(wilcoxon(er,fs[best]))
    dr.append(er-fs["regle"]); pr.append(wilcoxon(er,fs["regle"]))
    print(B,K,best,round(d.mean(),3),"IC90",[round(x,2) for x in ic90(d)],"p brut",round(ps[-1],4))
print("Holm4 meilleur:",[round(x,3) for x in holm(ps)])
print("Holm4 regle:",[round(x,3) for x in holm(pr)], "diffs",[round(d.mean(),2) for d in dr])
D=np.mean(ds,axis=0); print("global (moyenne des 4 diff par instance) :",round(D.mean(),3),"IC95",[round(x,2) for x in bootstrap_ic(D)],"p",wilcoxon(D,np.zeros_like(D)))
# puissance : écart-type des différences
for (B,K),d in zip(R,ds): print(B,K,"sd diff",round(d.std(ddof=1),2),"effet min détectable ~",round(2.8*d.std(ddof=1)/np.sqrt(len(d)),2))
