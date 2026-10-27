# controle_phase1 — régime A, facteur de seuil 1

Référence : Recuit simulé [evals=50000,depart=heuristique,params=taguchi]. 30 instances communes (Brandimarte 10, Hurink edata 10, Hurink rdata 10). Banque : `banque_resultats/resultats.csv`.
Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; Wilcoxon apparié par instance, p corrigée de Holm ; V/E/D = victoires / égalités / défaites contre la référence.

| Méthode | Brandimarte | Hurink edata | Hurink rdata | Total | IC 95 % | Médiane | V/E/D | p (Holm) | Temps/inst. (s) | Plannings évalués | Graines |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MWKR+EFT | +10.26 % | +16.71 % | +10.76 % | **+12.57 %** | [+9.85 ; +15.38] | +11.53 % | 0/1/29 | 1.8e-05 | 0.03 | nan | 1 |
| GA (Taguchi, 50k) | +3.86 % | +6.09 % | +4.77 % | **+4.91 %** | [+3.46 ; +6.47] | +4.08 % | 1/2/27 | 3.5e-05 | 39.21 | 50040 | 3 |
| Tabu (Taguchi, 50k) | -0.10 % | +2.28 % | +0.49 % | **+0.89 %** | [+0.31 ; +1.54] | +0.59 % | 5/3/22 | 0.0031 | 18.87 | 50012 | 3 |
| Agent greedy | +2.88 % | +12.88 % | +11.31 % | **+9.03 %** | [+6.53 ; +11.91] | +7.42 % | 1/1/28 | 3.5e-05 | 0.19 | 1 | 1 |
| Agent best of 100 | -0.53 % | +5.23 % | +2.28 % | **+2.33 %** | [+1.13 ; +3.54] | +1.64 % | 3/3/24 | 0.00044 | 14.32 | 100 | 1 |
| Agent + beam 5x4 | -1.00 % | +4.26 % | +0.58 % | **+1.28 %** | [+0.22 ; +2.34] | +0.69 % | 10/3/17 | 0.042 | 5.91 | 4247 | 1 |
| Agent + beam 50x5 | -0.98 % | +3.32 % | -0.05 % | **+0.76 %** | [-0.33 ; +1.82] | +0.20 % | 12/3/15 | 0.072 | 37.77 | 50526 | 1 |
