"""EXPLORATOIRE (non déclaré), 04/11/2026 — relecteur indépendant (claude/revue_article1_deterministe_v6.md) : M5 (grappes la01–la40),
M1 (faisceau 50×5 contre recuit par famille), M7 (temps du recuit 50k sur un processus, estimé depuis E10/E10b).
  PYTHONPATH=. python experiences_article1/exploratoire_relecteur2.py"""
import os,re,numpy as np,collections
from experiences_article1.statistiques import charger,BANQUE,INSTANCES_REGLAGE,wilcoxon,famille
from metaheuristiques.instances import fichiers
REF=("Recuit simulé","evals=50000,depart=heuristique,params=taguchi")
noms=[n for n in (os.path.splitext(os.path.basename(f))[0] for f in fichiers(["Brandimarte","HurinkLa","Kacem"])) if n not in INSTANCES_REGLAGE]
def grappe(n):
    m=re.match(r"Hurink[EVR]data(\d+)",n); return ("la",int(m.group(1))) if m else n
G=[grappe(n) for n in noms]; ug=sorted(set(G),key=str); idx={g:[i for i,x in enumerate(G) if x==g] for g in ug}
print("instances",len(noms),"grappes",len(ug))
v,t,ev=charger(BANQUE,"A",1.0)
ec=lambda k: np.array([100*(np.mean(v[k][n])/np.mean(v[REF][n])-1) for n in noms])
def boot_grappe(d,ic=0.95,n=10000):
    r=np.random.default_rng(0); gs=list(idx.values()); m=[]
    for _ in range(n):
        s=r.integers(0,len(gs),len(gs)); ii=np.concatenate([gs[j] for j in s]); m.append(d[ii].mean())
    a=(1-ic)/2; return np.percentile(m,100*a),np.percentile(m,100*(1-a))
def wil_grappe(d):
    g=np.array([d[i].mean() for i in idx.values()]); return wilcoxon(g,np.zeros_like(g))
# M5 : test groupé D1 (budget égal) et R1 avec grappes
D1={"regle":[(6,4),(12,4),(22,4),(55,5)],"fin":[(7,4),(12,4),(24,4),(56,5)],"borne":[(6,4),(12,4),(23,4),(55,5)]}
R=[(5,4),(10,4),(20,4),(50,5)]
for nom,eg in (("R1 même réglage",False),("D1 budget égal",True)):
    ds=[]
    for i,(B,K) in enumerate(R):
        er=ec(("RL:imit-ft",f"faisceau={B},k={K}"))
        c=[ec((f"Faisceau:filtre-{f}",f"faisceau={D1[f][i][0] if eg else B},k={K},filtre={f}")) for f in D1]
        ds.append(er-min(c,key=lambda x:x.mean()))
    D=np.mean(ds,axis=0)
    print(nom,"moy",round(D.mean(),3),"IC95 grappes",[round(x,2) for x in boot_grappe(D)],"IC90 grappes",[round(x,2) for x in boot_grappe(D,0.90)],"Wilcoxon sur grappes p",round(wil_grappe(D),4))
# M1 : TOST par famille du faisceau 50x5 contre recuit, et sans Kacem
e=ec(("RL:imit-ft","faisceau=50,k=5"))
fam=np.array([famille(n) for n in noms])
for f in sorted(set(fam)):
    d=e[fam==f]; r=np.random.default_rng(0); m=d[r.integers(0,len(d),(10000,len(d)))].mean(1)
    print("famille",f,len(d),round(d.mean(),2),"IC90",[round(np.percentile(m,5),2),round(np.percentile(m,95),2)],"W/T/L",(d<-1e-9).sum(),(abs(d)<=1e-9).sum(),(d>1e-9).sum(),"médiane",round(np.median(d),2))
d=e[fam!="Kacem"]; print("sans Kacem",round(d.mean(),2)); print("médiane totale",round(np.median(e),2), "IC90 grappes", [round(x,2) for x in boot_grappe(e,0.90)])
# M7 : temps du recuit 50k sur un processus, estimé depuis les runs à budget de temps (E10/E10b)
for k in v:
    if k[0]=="Recuit simulé" and "budget=" in k[1] and "mono" in k[1]:
        rates=[np.mean(ev[k][n])/float(re.search(r"budget=(\d+)",k[1]).group(1)) for n in ev[k] if ev[k][n]]
        print(k[1], "instances",len(rates),"évals/s moyen",round(np.mean(rates)), "→ temps 50k ≈",round(np.mean([50000/x for x in rates]),1),"s")
