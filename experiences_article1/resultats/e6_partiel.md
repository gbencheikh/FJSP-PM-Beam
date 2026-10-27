# e6_partiel — régime A, facteur de seuil 1

Référence : Recuit simulé [evals=50000,depart=heuristique,params=taguchi]. 127 instances communes (Brandimarte 10, Hurink edata 37, Hurink rdata 36, Hurink vdata 40, Kacem 4). Banque : `banque_resultats/resultats.csv`. Exclues (réglage Taguchi) : HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18, HurinkRdata28, HurinkRdata38.
Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; Wilcoxon apparié par instance (égalités exclues : n eff. = nombre de paires non égales), p corrigée de Holm ; V/E/D = victoires / égalités / défaites contre la référence.

| Méthode | Brandimarte | Hurink edata | Hurink rdata | Hurink vdata | Kacem | Total | IC 95 % | Médiane | V/E/D | n eff. | p (Holm) | Temps/inst. (s) | Plannings évalués | Graines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MWKR+EFT | +10.39 % | +16.92 % | +15.38 % | +12.68 % | +8.25 % | **+14.36 %** | [+12.76 ; +16.03] | +13.28 % | 0/2/125 | 125 | 3.9e-21 | 0.04 | nan | 1 |
| TS (50k) | +0.07 % | +1.54 % | +1.13 % | -0.57 % | +2.04 % | **+0.66 %** | [+0.32 ; +1.00] | +0.27 % | 40/8/79 | 119 | 0.00044 | 19.96 | 50013 | 5 |
| Policy, greedy | +2.97 % | +12.32 % | +9.44 % | +1.66 % | +9.42 % | **+7.32 %** | [+6.18 ; +8.47] | +6.72 % | 10/3/114 | 124 | 2.4e-17 | 0.18 | 1 | 1 |
| Policy, 100 samples x5 | -0.42 % | +4.70 % | +3.92 % | -0.74 % | +0.28 % | **+2.22 %** | [+1.57 ; +2.84] | +1.92 % | 21/4/102 | 123 | 2.8e-11 | 21.63 | 100 | 5 |
| Rule beam B=5 | -0.27 % | +4.88 % | +1.71 % | -2.43 % | -3.32 % | **+1.01 %** | [+0.29 ; +1.75] | +0.79 % | 45/2/80 | 125 | 0.00056 | 15.39 | 5810 | 1 |
| Rule beam B=20 | -0.39 % | +4.14 % | +1.57 % | -2.49 % | -5.59 % | **+0.66 %** | [-0.04 ; +1.34] | +0.57 % | 47/4/76 | 123 | 0.0021 | 44.91 | 24538 | 1 |
| Rule beam B=50 | -0.41 % | +3.91 % | +1.10 % | -2.59 % | -7.51 % | **+0.36 %** | [-0.36 ; +1.04] | +0.28 % | 53/4/70 | 123 | 0.018 | 90.27 | 61660 | 1 |
| Rule beam B=100 | -0.51 % | +3.41 % | +0.97 % | -2.66 % | -7.51 % | **+0.15 %** | [-0.54 ; +0.80] | +0.36 % | 51/4/72 | 123 | 0.018 | 66.45 | 125231 | 1 |
| Rule beam B=200 | -0.29 % | +3.07 % | +0.85 % | -2.74 % | -7.51 % | **+0.01 %** | [-0.66 ; +0.65] | +0.27 % | 54/4/69 | 123 | 0.022 | 129.47 | 246441 | 1 |
| Untrained net 5x4 | +2.22 % | +6.76 % | +3.31 % | -1.87 % | +16.56 % | **+3.02 %** | [+2.09 ; +3.97] | +2.54 % | 29/2/96 | 125 | 1.8e-08 | 3.16 | 2779 | 1 |
| Untrained net 50x5 | +0.34 % | +4.20 % | +1.52 % | -2.65 % | +16.56 % | **+1.37 %** | [+0.52 ; +2.27] | +0.87 % | 47/2/78 | 125 | 0.0019 | 36.21 | 38931 | 1 |
| Policy 5x4 no pruning | -0.96 % | +4.24 % | +2.00 % | -2.31 % | -7.51 % | **+0.76 %** | [-0.01 ; +1.49] | +0.45 % | 47/3/77 | 124 | 0.001 | 3.79 | 4008 | 1 |
| Policy 5x4 no dedup | -0.18 % | +4.54 % | +2.16 % | -2.14 % | -7.51 % | **+1.01 %** | [+0.26 ; +1.76] | +0.82 % | 46/3/78 | 124 | 0.00021 | 3.51 | 3551 | 1 |
