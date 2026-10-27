# ablations — régime A, facteur de seuil 1

Référence : Recuit simulé [evals=50000,depart=heuristique,params=taguchi]. 127 instances communes (Brandimarte 10, Hurink edata 37, Hurink rdata 36, Hurink vdata 40, Kacem 4). Banque : `banque_resultats/resultats.csv`. Exclues (réglage Taguchi) : HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18, HurinkRdata28, HurinkRdata38.
Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; Wilcoxon apparié par instance (égalités exclues : n eff. = nombre de paires non égales), p corrigée de Holm ; V/E/D = victoires / égalités / défaites contre la référence.

| Méthode | Brandimarte | Hurink edata | Hurink rdata | Hurink vdata | Kacem | Total | IC 95 % | Médiane | V/E/D | n eff. | p (Holm) | Temps/inst. (s) | Plannings évalués | Graines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Rule beam B=5 | -0.27 % | +4.88 % | +1.71 % | -2.43 % | -3.32 % | **+1.01 %** | [+0.29 ; +1.75] | +0.79 % | 45/2/80 | 125 | 0.00064 | 15.71 | 5856 | 1 |
| Rule beam B=20 | -0.39 % | +4.14 % | +1.57 % | -2.49 % | -5.59 % | **+0.66 %** | [-0.04 ; +1.34] | +0.57 % | 47/4/76 | 123 | 0.0021 | 45.17 | 24748 | 1 |
| Rule beam B=50 | -0.41 % | +3.91 % | +1.10 % | -2.59 % | -7.51 % | **+0.36 %** | [-0.36 ; +1.04] | +0.28 % | 53/4/70 | 123 | 0.018 | 90.97 | 62100 | 1 |
| Rule beam B=200 | -0.29 % | +3.07 % | +0.85 % | -2.74 % | -7.51 % | **+0.01 %** | [-0.66 ; +0.65] | +0.27 % | 54/4/69 | 123 | 0.044 | 130.42 | 248089 | 1 |
| Untrained net + beam 5x4 | +2.22 % | +6.76 % | +3.31 % | -1.87 % | +16.56 % | **+3.02 %** | [+2.09 ; +3.97] | +2.54 % | 29/2/96 | 125 | 1.8e-08 | 3.18 | 2786 | 1 |
| Untrained net + beam 50x5 | +0.34 % | +4.20 % | +1.52 % | -2.65 % | +16.56 % | **+1.37 %** | [+0.52 ; +2.27] | +0.87 % | 47/2/78 | 125 | 0.0019 | 36.31 | 38812 | 1 |
| Policy + beam 5x4 | -0.96 % | +4.24 % | +2.00 % | -2.31 % | -7.51 % | **+0.76 %** | [-0.01 ; +1.49] | +0.45 % | 47/3/77 | 124 | 0.0012 | 3.57 | 3580 | 1 |
|   without LB pruning | -0.96 % | +4.24 % | +2.00 % | -2.31 % | -7.51 % | **+0.76 %** | [-0.01 ; +1.49] | +0.45 % | 47/3/77 | 124 | 0.0012 | 3.82 | 4025 | 1 |
|   without duplicate removal | -0.18 % | +4.54 % | +2.16 % | -2.14 % | -7.51 % | **+1.01 %** | [+0.26 ; +1.76] | +0.82 % | 46/3/78 | 124 | 0.00021 | 3.52 | 3547 | 1 |
| Policy + beam 50x5 | -0.84 % | +3.17 % | +1.02 % | -2.73 % | -7.51 % | **+0.05 %** | [-0.65 ; +0.71] | +0.07 % | 58/4/65 | 123 | 0.057 | 30.50 | 41326 | 1 |
