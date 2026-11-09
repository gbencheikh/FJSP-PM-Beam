# ablations_caie — régime A, facteur de seuil 1

Référence : Recuit simulé [evals=50000,depart=heuristique,params=taguchi]. 127 instances communes (Brandimarte 10, Hurink edata 37, Hurink rdata 36, Hurink vdata 40, Kacem 4). Banque : `banque_resultats/resultats.csv`. Exclues (réglage Taguchi) : HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18, HurinkRdata28, HurinkRdata38.
Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; Wilcoxon apparié par instance (égalités exclues : n eff. = nombre de paires non égales), p corrigée de Holm ; V/E/D = victoires / égalités / défaites contre la référence. Opt. prouvé atteint = instances à optimum prouvé (meilleur connu = meilleure borne valide : FJSPLib, CP-SAT) où la moyenne des graines de la méthode atteint l'optimum.

| Méthode | Brandimarte | Hurink edata | Hurink rdata | Hurink vdata | Kacem | Total | IC 95 % | Médiane | V/E/D | n eff. | p (Holm) | Opt. prouvé atteint | Temps/inst. (s) | Plannings évalués | Graines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *Flexibilité (part des machines éligibles)* | 0.36 | 0.15 | 0.26 | 0.48 | 1.00 | 0.33 | | | | | | | | | |
| Beam without filter, B=5 | -0.27 % | +4.88 % | +1.71 % | -2.43 % | -3.32 % | **+1.01 %** | [+0.29 ; +1.75] | +0.79 % | 45/2/80 | 125 | 0.00056 | 5/19 | 15.71 | 5856 | 1 |
| Beam without filter, B=20 | -0.39 % | +4.14 % | +1.57 % | -2.49 % | -5.59 % | **+0.66 %** | [-0.04 ; +1.34] | +0.57 % | 47/4/76 | 123 | 0.0021 | 6/19 | 45.17 | 24748 | 1 |
| Beam without filter, B=50 | -0.41 % | +3.91 % | +1.10 % | -2.59 % | -7.51 % | **+0.36 %** | [-0.36 ; +1.04] | +0.28 % | 53/4/70 | 123 | 0.018 | 8/19 | 90.97 | 62100 | 1 |
| Beam without filter, B=200 | -0.29 % | +3.07 % | +0.85 % | -2.74 % | -7.51 % | **+0.01 %** | [-0.66 ; +0.65] | +0.27 % | 54/4/69 | 123 | 0.044 | 9/19 | 130.42 | 248089 | 1 |
| Policy + beam 5x4 | -0.96 % | +4.24 % | +2.00 % | -2.31 % | -7.51 % | **+0.76 %** | [-0.01 ; +1.49] | +0.45 % | 47/3/77 | 124 | 0.001 | 7/19 | 3.57 | 3580 | 1 |
|   without LB pruning | -0.96 % | +4.24 % | +2.00 % | -2.31 % | -7.51 % | **+0.76 %** | [-0.01 ; +1.49] | +0.45 % | 47/3/77 | 124 | 0.001 | 7/19 | 3.82 | 4025 | 1 |
|   without duplicate removal | -0.18 % | +4.54 % | +2.16 % | -2.14 % | -7.51 % | **+1.01 %** | [+0.26 ; +1.76] | +0.82 % | 46/3/78 | 124 | 0.00019 | 5/19 | 3.52 | 3547 | 1 |
| Policy + beam 50x5 | -0.84 % | +3.17 % | +1.02 % | -2.73 % | -7.51 % | **+0.05 %** | [-0.65 ; +0.71] | +0.07 % | 58/4/65 | 123 | 0.057 | 9/19 | 30.50 | 41326 | 1 |
