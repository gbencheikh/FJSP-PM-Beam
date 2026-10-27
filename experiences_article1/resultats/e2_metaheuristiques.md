# e2_metaheuristiques — régime A, facteur de seuil 1

Référence : Recuit simulé [evals=50000,depart=heuristique,params=taguchi]. 127 instances communes (Brandimarte 10, Hurink edata 37, Hurink rdata 36, Hurink vdata 40, Kacem 4). Banque : `banque_resultats/resultats.csv`. Exclues (réglage Taguchi) : HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18, HurinkRdata28, HurinkRdata38.
Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; Wilcoxon apparié par instance (égalités exclues : n eff. = nombre de paires non égales), p corrigée de Holm ; V/E/D = victoires / égalités / défaites contre la référence.

| Méthode | Brandimarte | Hurink edata | Hurink rdata | Hurink vdata | Kacem | Total | IC 95 % | Médiane | V/E/D | n eff. | p (Holm) | Temps/inst. (s) | Plannings évalués | Graines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GA (50k) | +4.10 % | +5.47 % | +6.69 % | +6.64 % | +4.05 % | **+6.03 %** | [+5.17 ; +6.89] | +4.81 % | 2/3/122 | 124 | 1.6e-21 | 35.61 | 50040 | 5 |
| TS (50k) | +0.07 % | +1.54 % | +1.13 % | -0.57 % | +2.04 % | **+0.66 %** | [+0.32 ; +1.00] | +0.27 % | 40/8/79 | 119 | 0.00011 | 19.96 | 50013 | 5 |
| SA (50k) | +0.00 % | +0.00 % | +0.00 % | +0.00 % | +0.00 % | **+0.00 %** | [+0.00 ; +0.00] | +0.00 % | 0/127/0 | 0 | 1 | 20.45 | 50000 | 5 |
