# 2e révision — D1, D3, D4 (analyse déclarée, PROTOCOLE § 3 septies)

127 instances de test. Écart = C_max / recuit 50k − 1 (%). Différence = réseau − filtre (négatif : réseau meilleur).

## D1 — filtres à budget égal (μ = 1)

| Réglage réseau | Plannings réseau | Filtre (B') | Plannings filtre | Ratio | Écart réseau | Écart filtre |
|---|---|---|---|---|---|---|
| 5×4 | 3580 | regle (6×4) | 3881 | 1.084 | +0.76 % | +1.11 % |
| 5×4 | 3580 | fin (7×4) | 4210 | 1.176 | +0.76 % | +1.03 % |
| 5×4 | 3580 | borne (6×4) | 3768 | 1.052 | +0.76 % | +1.13 % |
| 10×4 | 7161 | regle (12×4) | 7690 | 1.074 | +0.34 % | +0.83 % |
| 10×4 | 7161 | fin (12×4) | 7255 | 1.013 | +0.34 % | +0.86 % |
| 10×4 | 7161 | borne (12×4) | 7582 | 1.059 | +0.34 % | +0.78 % |
| 20×4 | 14240 | regle (22×4) | 14307 | 1.005 | +0.27 % | +0.46 % |
| 20×4 | 14240 | fin (24×4) | 14567 | 1.023 | +0.27 % | +0.75 % |
| 20×4 | 14240 | borne (23×4) | 14810 | 1.040 | +0.27 % | +0.64 % |
| 50×5 | 41326 | regle (55×5) | 41382 | 1.001 | +0.05 % | +0.20 % |
| 50×5 | 41326 | fin (56×5) | 42187 | 1.021 | +0.05 % | +0.22 % |
| 50×5 | 41326 | borne (55×5) | 41863 | 1.013 | +0.05 % | +0.09 % |

### (a)+(b) Réseau contre le meilleur filtre à budget égal

| Réglage | Filtre | Différence | IC 95 % | IC 90 % | V/E/D | p brut | p Holm (4) | effet min. détectable |
|---|---|---|---|---|---|---|---|---|
| 5×4 | fin (7×4) | -0.261 | [-0.65 ; +0.09] | [-0.57 ; +0.03] | 62/28/37 | 0.159 | 0.317 | 0.52 |
| 10×4 | borne (12×4) | -0.438 | [-0.86 ; -0.06] | [-0.79 ; -0.12] | 65/23/39 | 0.0241 | 0.0964 | 0.57 |
| 20×4 | regle (22×4) | -0.188 | [-0.45 ; +0.06] | [-0.40 ; +0.02] | 58/32/37 | 0.0698 | 0.209 | 0.37 |
| 50×5 | borne (55×5) | -0.042 | [-0.29 ; +0.19] | [-0.24 ; +0.16] | 50/36/41 | 0.746 | 0.746 | 0.34 |

Test global (moyenne par instance des 4 différences) : -0.232 point, IC 95 % [-0.45 ; -0.04], Wilcoxon p = 0.0251. Réglages significatifs (Holm sur 4) : 0/4.

### (c) Réseau contre le filtre a priori `regle` à budget égal

| Réglage | Filtre | Différence | IC 95 % | IC 90 % | V/E/D | p brut | p Holm (4) | effet min. détectable |
|---|---|---|---|---|---|---|---|---|
| 5×4 | regle (6×4) | -0.345 | [-0.70 ; -0.01] | [-0.64 ; -0.07] | 63/26/38 | 0.0545 | 0.174 | 0.48 |
| 10×4 | regle (12×4) | -0.484 | [-0.86 ; -0.13] | [-0.79 ; -0.19] | 55/25/47 | 0.0661 | 0.174 | 0.51 |
| 20×4 | regle (22×4) | -0.188 | [-0.45 ; +0.06] | [-0.40 ; +0.02] | 58/32/37 | 0.0698 | 0.174 | 0.37 |
| 50×5 | regle (55×5) | -0.152 | [-0.42 ; +0.11] | [-0.37 ; +0.06] | 62/25/40 | 0.0436 | 0.174 | 0.37 |

Test global (moyenne par instance des 4 différences) : -0.292 point, IC 95 % [-0.52 ; -0.08], Wilcoxon p = 0.00225. Réglages significatifs (Holm sur 4) : 0/4.

**Verdict D1 (règle déclarée)** : (a) 0/4, (b) p = 0.0251 → **gain faible mais constant**.

## D3 — facteur de seuil 0,7 et 1,5 (réseau non réentraîné)


### Facteur 0.7

| Réglage | Filtre | Écart réseau | Écart filtre | Différence | IC 95 % | p Holm (4) |
|---|---|---|---|---|---|---|
| 5×4 | regle (meilleur) | +1.14 % | +1.41 % | -0.28 | [-0.63 ; +0.06] | 0.96 |
| 5×4 | borne | +1.14 % | +1.49 % | -0.36 | [-0.83 ; +0.09] | 0.96 |
| 50×5 | regle (meilleur) | +0.11 % | +0.48 % | -0.37 | [-0.71 ; -0.05] | 0.101 |
| 50×5 | borne | +0.11 % | +0.54 % | -0.43 | [-0.76 ; -0.12] | 0.0719 |

Verdict (règle de R4) : la conclusion de R1 TIENT. TOST ±1 % du faisceau 50×5 : écart +0.11 %, IC 90 % [-0.55 ; +0.76] → équivalent. Test global (2 réglages) : -0.325, IC 95 % [-0.59 ; -0.09], p = 0.025.

### Facteur 1.5

| Réglage | Filtre | Écart réseau | Écart filtre | Différence | IC 95 % | p Holm (4) |
|---|---|---|---|---|---|---|
| 5×4 | regle (meilleur) | +0.85 % | +1.06 % | -0.21 | [-0.55 ; +0.12] | 1 |
| 5×4 | borne | +0.85 % | +1.15 % | -0.30 | [-0.70 ; +0.07] | 0.424 |
| 50×5 | regle | +0.14 % | +0.31 % | -0.17 | [-0.52 ; +0.18] | 1 |
| 50×5 | borne (meilleur) | +0.14 % | +0.28 % | -0.14 | [-0.43 ; +0.14] | 1 |

Verdict (règle de R4) : la conclusion de R1 TIENT. TOST ±1 % du faisceau 50×5 : écart +0.14 %, IC 90 % [-0.39 ; +0.66] → équivalent. Test global (2 réglages) : -0.175, IC 95 % [-0.43 ; +0.06], p = 0.132.

## D4 — problème classique avec T_k = L_k (référence : recuit 50k du problème classique)

| Méthode | T_k = L_k | × 1000 (rappel) |
|---|---|---|
| Glouton | +7.63 % | +99.61 % |
| 100 tirages | +3.50 % | +45.95 % |
| Faisceau 5×4 | +1.70 % | +2.53 % |
| Faisceau 50×5 | +0.80 % | +1.40 % |
| Filtre regle 5×4 | +2.08 % | — |
| Filtre regle 50×5 | +1.23 % | — |

**Verdict D4 (règle déclarée)** : glouton +7.63 % → effondrement à ×1000 attribué à l'échelle des features (10.7 / 11.3 à réécrire)
