# principal_provisoire — régime A, facteur de seuil 1

Référence : Recuit simulé [evals=50000,depart=heuristique,params=taguchi]. 127 instances communes (Brandimarte 10, Hurink edata 37, Hurink rdata 36, Hurink vdata 40, Kacem 4). Banque : `banque_resultats/resultats.csv`. Exclues (réglage Taguchi) : HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18, HurinkRdata28, HurinkRdata38.
Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; Wilcoxon apparié par instance (égalités exclues : n eff. = nombre de paires non égales), p corrigée de Holm ; V/E/D = victoires / égalités / défaites contre la référence. Opt. prouvé atteint = instances à optimum prouvé (meilleur connu = meilleure borne valide : FJSPLib, CP-SAT) où la moyenne des graines de la méthode atteint l'optimum.

| Méthode | Brandimarte | Hurink edata | Hurink rdata | Hurink vdata | Kacem | Total | IC 95 % | Médiane | V/E/D | n eff. | p (Holm) | Opt. prouvé atteint | Temps/inst. (s) | Plannings évalués | Graines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Flexibilité (part des machines éligibles)* | 0.36 | 0.15 | 0.26 | 0.48 | 1.00 | 0.33 | | | | | | | | | |
| MWKR+EFT | +10.39 % | +16.92 % | +15.38 % | +12.68 % | +8.25 % | **+14.36 %** | [+12.76 ; +16.03] | +13.28 % | 0/2/125 | 125 | 2.1e-21 | 0/19 | 0.04 | nan | 1 |
| GA (50k) | +4.10 % | +5.47 % | +6.69 % | +6.64 % | +4.05 % | **+6.03 %** | [+5.17 ; +6.89] | +4.81 % | 2/3/122 | 124 | 3.2e-21 | 0/19 | 35.58 | 50040 | 5 |
| TS (50k) | +0.07 % | +1.54 % | +1.13 % | -0.57 % | +2.04 % | **+0.66 %** | [+0.32 ; +1.00] | +0.27 % | 40/8/79 | 119 | 0.00017 | 2/19 | 20.06 | 50013 | 5 |
| Policy, greedy | +2.97 % | +12.32 % | +9.44 % | +1.66 % | +9.42 % | **+7.32 %** | [+6.18 ; +8.47] | +6.72 % | 10/3/114 | 124 | 1e-17 | 0/19 | 0.18 | 1 | 1 |
| Policy, 100 samples x 5 seeds | -0.42 % | +4.70 % | +3.92 % | -0.74 % | +0.28 % | **+2.22 %** | [+1.57 ; +2.84] | +1.92 % | 21/4/102 | 123 | 1e-11 | 0/19 | 21.81 | 100 | 5 |
| Policy + beam 5x4 | -0.96 % | +4.24 % | +2.00 % | -2.31 % | -7.51 % | **+0.76 %** | [-0.01 ; +1.49] | +0.45 % | 47/3/77 | 124 | 0.00034 | 7/19 | 3.57 | 3580 | 1 |
| Policy + beam 50x5 | -0.84 % | +3.17 % | +1.02 % | -2.73 % | -7.51 % | **+0.05 %** | [-0.65 ; +0.71] | +0.07 % | 58/4/65 | 123 | 0.057 | 9/19 | 30.50 | 41326 | 1 |
