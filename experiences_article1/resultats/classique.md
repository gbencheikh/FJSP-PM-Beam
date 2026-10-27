# classique — régime A, facteur de seuil 1000

Référence : Recuit simulé [evals=50000,depart=heuristique,params=taguchi]. 123 instances communes (Brandimarte 10, Hurink edata 37, Hurink rdata 36, Hurink vdata 40). Banque : `banque_resultats/resultats.csv`. Exclues (réglage Taguchi) : HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18, HurinkRdata28, HurinkRdata38.
Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; Wilcoxon apparié par instance (égalités exclues : n eff. = nombre de paires non égales), p corrigée de Holm ; V/E/D = victoires / égalités / défaites contre la référence.

| Méthode | Brandimarte | Hurink edata | Hurink rdata | Hurink vdata | Total | IC 95 % | Médiane | V/E/D | n eff. | p (Holm) | Temps/inst. (s) | Plannings évalués | Graines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MWKR+EFT | +6.58 % | +13.83 % | +9.37 % | +2.38 % | **+8.21 %** | [+7.07 ; +9.37] | +7.65 % | 0/6/117 | 117 | 3.7e-20 | 0.02 | nan | 1 |
| TS (50k) | +0.63 % | +1.25 % | +0.96 % | -0.19 % | **+0.65 %** | [+0.40 ; +0.91] | +0.22 % | 32/11/80 | 112 | 9.2e-07 | 15.13 | 50013 | 5 |
| Song et al. greedy | +18.77 % | +12.19 % | +8.00 % | +2.96 % | **+8.49 %** | [+7.14 ; +10.00] | +6.35 % | 3/1/119 | 122 | 2e-20 | 6.52 | nan | 1 |
| Song et al. 100 samples | +10.46 % | +4.90 % | +2.95 % | +0.13 % | **+3.23 %** | [+2.42 ; +4.16] | +1.79 % | 14/6/103 | 117 | 1.1e-15 | 422.42 | nan | 5 |
| Policy, greedy | +100.92 % | +99.53 % | +100.00 % | +98.33 % | **+99.39 %** | [+96.52 ; +102.18] | +102.66 % | 0/0/123 | 123 | 5.7e-21 | 0.94 | 1 | 1 |
| Policy, 100 samples | +44.78 % | +51.95 % | +49.82 % | +34.51 % | **+45.07 %** | [+42.86 ; +47.18] | +47.35 % | 0/0/123 | 123 | 5.7e-21 | 59.16 | 100 | 5 |
| Rule beam B=50 | -0.66 % | +4.52 % | +1.34 % | -0.98 % | **+1.38 %** | [+0.88 ; +1.88] | +0.70 % | 45/6/72 | 117 | 1.5e-06 | 25.69 | 55555 | 1 |
| Policy + beam 5x4 | +2.28 % | +6.48 % | +2.96 % | -0.68 % | **+2.78 %** | [+2.14 ; +3.44] | +2.22 % | 29/7/87 | 116 | 6.6e-11 | 2.62 | 2724 | 1 |
| Policy + beam 50x5 | +0.29 % | +4.61 % | +1.77 % | -0.96 % | **+1.62 %** | [+1.13 ; +2.10] | +0.85 % | 41/8/74 | 115 | 6.2e-07 | 28.07 | 36658 | 1 |

Instances absentes (exclues du tableau) : Song et al. greedy : 4 (Kacem1, Kacem2, Kacem3, Kacem4); Song et al. 100 samples : 4 (Kacem1, Kacem2, Kacem3, Kacem4)
