# e2_vs_borne_fjsplib — régime A, facteur de seuil 1

Référence : FJSPLib borne inf []. 127 instances communes (Brandimarte 10, Hurink edata 37, Hurink rdata 36, Hurink vdata 40, Kacem 4). Banque : `banque_resultats/resultats.csv`. Exclues (réglage Taguchi) : HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18, HurinkRdata28, HurinkRdata38.
Écart = valeur / référence − 1 (moyenne des graines par instance) ; IC bootstrap 95 % sur les instances ; Wilcoxon apparié par instance (égalités exclues : n eff. = nombre de paires non égales), p corrigée de Holm ; V/E/D = victoires / égalités / défaites contre la référence.

| Méthode | Brandimarte | Hurink edata | Hurink rdata | Hurink vdata | Kacem | Total | IC 95 % | Médiane | V/E/D | n eff. | p (Holm) | Temps/inst. (s) | Plannings évalués | Graines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GA (50k) | +25.04 % | +19.10 % | +20.62 % | +18.00 % | +12.60 % | **+19.45 %** | [+18.01 ; +20.90] | +20.00 % | 0/0/127 | 127 | 4.2e-22 | 35.61 | 50040 | 5 |
| TS (50k) | +19.91 % | +14.69 % | +14.28 % | +10.00 % | +10.58 % | **+13.38 %** | [+12.35 ; +14.43] | +12.27 % | 0/0/127 | 127 | 4.2e-22 | 19.96 | 50013 | 5 |
| SA (50k) | +19.84 % | +12.96 % | +13.01 % | +10.67 % | +8.51 % | **+12.65 %** | [+11.65 ; +13.70] | +11.54 % | 0/1/126 | 126 | 4.2e-22 | 20.45 | 50000 | 5 |
