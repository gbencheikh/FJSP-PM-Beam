# Révision — R1 (filtre non appris) et R2 (imitation seule)

127 instances de test ; référence : recuit simulé Taguchi, 50 000 évaluations. Écart = C_max / référence − 1 (moyenne des graines). Différence = écart du réseau final − écart de l'autre (négatif : le réseau final est meilleur). IC bootstrap 95 % sur les instances ; Wilcoxon apparié ; Holm.

## R1 — réseau final contre filtres non appris (Holm sur 12 tests)

| B × K | Filtre | Écart réseau | Écart filtre | Différence | IC 95 % | V/E/D (réseau) | p Holm | Plannings réseau | Plannings filtre |
|---|---|---|---|---|---|---|---|---|---|
| 5x4 | filtre regle | +0.76 % | +1.07 % | -0.30 | [-0.67 ; +0.06] | 59/25/43 | 0.21 | 3580 | 3269 |
| 5x4 | filtre fin | +0.76 % | +1.42 % | -0.66 | [-1.08 ; -0.27] | 79/19/29 | 0.00054 | 3580 | 2899 |
| 5x4 | filtre borne | +0.76 % | +1.16 % | -0.39 | [-0.80 ; -0.02] | 69/20/38 | 0.16 | 3580 | 3094 |
| 10x4 | filtre regle | +0.34 % | +0.83 % | -0.49 | [-0.83 ; -0.17] | 58/26/43 | 0.12 | 7161 | 6467 |
| 10x4 | filtre fin | +0.34 % | +0.88 % | -0.54 | [-0.88 ; -0.23] | 69/25/33 | 0.008 | 7161 | 6004 |
| 10x4 | filtre borne | +0.34 % | +0.91 % | -0.57 | [-1.00 ; -0.19] | 65/22/40 | 0.16 | 7161 | 6266 |
| 20x4 | filtre regle | +0.27 % | +0.50 % | -0.22 | [-0.50 ; +0.04] | 60/28/39 | 0.21 | 14240 | 13035 |
| 20x4 | filtre fin | +0.27 % | +0.79 % | -0.52 | [-0.89 ; -0.20] | 68/23/36 | 0.015 | 14240 | 12273 |
| 20x4 | filtre borne | +0.27 % | +0.71 % | -0.44 | [-0.86 ; -0.06] | 61/30/36 | 0.21 | 14240 | 12749 |
| 50x5 | filtre regle | +0.05 % | +0.26 % | -0.21 | [-0.47 ; +0.04] | 65/25/37 | 0.098 | 41326 | 37679 |
| 50x5 | filtre fin | +0.05 % | +0.33 % | -0.28 | [-0.51 ; -0.07] | 62/24/41 | 0.098 | 41326 | 37438 |
| 50x5 | filtre borne | +0.05 % | +0.10 % | -0.05 | [-0.30 ; +0.18] | 55/30/42 | 0.64 | 41326 | 38086 |

**Règle déclarée** : comparaison au meilleur filtre non appris de chaque réglage.

| B × K | Meilleur filtre | Réseau significativement meilleur ? |
|---|---|---|
| 5x4 | filtre regle (+1.07 %) | non (différence -0.30, p Holm 0.21) |
| 10x4 | filtre regle (+0.83 %) | non (différence -0.49, p Holm 0.12) |
| 20x4 | filtre regle (+0.50 %) | non (différence -0.22, p Holm 0.21) |
| 50x5 | filtre borne (+0.10 %) | non (différence -0.05, p Holm 0.64) |

**Verdict R1** : réseau significativement meilleur que le meilleur filtre non appris pour 0/4 réglages → critère NON atteint (< 3/4) : contribution à reformuler.

### Par famille (descriptif) : écart au recuit, réseau / meilleur filtre de chaque réglage

| B × K | Famille | n | Réseau | filtre regle | filtre fin | filtre borne |
|---|---|---|---|---|---|---|
| 5x4 | Brandimarte | 10 | -0.96 % | +0.20 % | +0.15 % | -0.86 % |
| 5x4 | Hurink edata | 37 | +4.24 % | +4.65 % | +4.76 % | +4.72 % |
| 5x4 | Hurink rdata | 36 | +2.00 % | +1.84 % | +2.51 % | +1.68 % |
| 5x4 | Hurink vdata | 40 | -2.31 % | -2.29 % | -2.18 % | -2.20 % |
| 5x4 | Kacem | 4 | -7.51 % | -3.32 % | -0.03 % | +2.09 % |
| 10x4 | Brandimarte | 10 | -1.09 % | -0.53 % | -0.45 % | -0.99 % |
| 10x4 | Hurink edata | 37 | +3.30 % | +4.56 % | +3.95 % | +4.13 % |
| 10x4 | Hurink rdata | 36 | +1.68 % | +1.63 % | +1.98 % | +1.59 % |
| 10x4 | Hurink vdata | 40 | -2.45 % | -2.35 % | -2.30 % | -2.31 % |
| 10x4 | Kacem | 4 | -7.51 % | -5.59 % | -2.30 % | +2.09 % |
| 20x4 | Brandimarte | 10 | -1.14 % | -0.49 % | +0.03 % | -1.24 % |
| 20x4 | Hurink edata | 37 | +3.78 % | +3.72 % | +4.04 % | +3.88 % |
| 20x4 | Hurink rdata | 36 | +1.08 % | +1.37 % | +1.68 % | +1.38 % |
| 20x4 | Hurink vdata | 40 | -2.56 % | -2.42 % | -2.52 % | -2.48 % |
| 20x4 | Kacem | 4 | -7.51 % | -5.59 % | -2.30 % | +2.09 % |
| 50x5 | Brandimarte | 10 | -0.84 % | -0.96 % | -0.37 % | -0.97 % |
| 50x5 | Hurink edata | 37 | +3.17 % | +3.73 % | +3.52 % | +3.41 % |
| 50x5 | Hurink rdata | 36 | +1.02 % | +0.83 % | +1.22 % | +0.69 % |
| 50x5 | Hurink vdata | 40 | -2.73 % | -2.58 % | -2.65 % | -2.64 % |
| 50x5 | Kacem | 4 | -7.51 % | -5.59 % | -5.59 % | -5.59 % |

## R2 — réseau final (imitation + PPO) contre imitation seule (Holm sur 6 tests)

| Réglage | Écart final | Écart imitation seule | Différence | IC 95 % | V/E/D (final) | p Holm |
|---|---|---|---|---|---|---|
| glouton | +7.32 % | +30.47 % | -23.15 | [-30.19 ; -16.80] | 99/2/26 | 1.2e-14 |
| echantillons=100 | +2.22 % | +7.43 % | -5.21 | [-7.10 ; -3.75] | 120/3/4 | 8.1e-21 |
| faisceau=5,k=4 | +0.76 % | +1.17 % | -0.41 | [-0.65 ; -0.17] | 62/26/39 | 0.011 |
| faisceau=10,k=4 | +0.34 % | +0.93 % | -0.59 | [-0.96 ; -0.27] | 63/27/37 | 0.0036 |
| faisceau=20,k=4 | +0.27 % | +0.56 % | -0.29 | [-0.56 ; -0.02] | 59/30/38 | 0.073 |
| faisceau=50,k=5 | +0.05 % | +0.11 % | -0.06 | [-0.35 ; +0.23] | 54/25/48 | 0.35 |

## Qualité / plannings évalués (secondaire)

| Variante | Réglage | Écart moyen | Plannings évalués |
|---|---|---|---|
| Réseau final | 5x4 | +0.76 % | 3580 |
| Réseau final | 10x4 | +0.34 % | 7161 |
| Réseau final | 20x4 | +0.27 % | 14240 |
| Réseau final | 50x5 | +0.05 % | 41326 |
| Imitation seule | 5x4 | +1.17 % | 3775 |
| Imitation seule | 10x4 | +0.93 % | 7445 |
| Imitation seule | 20x4 | +0.56 % | 14911 |
| Imitation seule | 50x5 | +0.11 % | 42869 |
| Filtre regle | 5x4 | +1.07 % | 3269 |
| Filtre regle | 10x4 | +0.83 % | 6467 |
| Filtre regle | 20x4 | +0.50 % | 13035 |
| Filtre regle | 50x5 | +0.26 % | 37679 |
| Filtre fin | 5x4 | +1.42 % | 2899 |
| Filtre fin | 10x4 | +0.88 % | 6004 |
| Filtre fin | 20x4 | +0.79 % | 12273 |
| Filtre fin | 50x5 | +0.33 % | 37438 |
| Filtre borne | 5x4 | +1.16 % | 3094 |
| Filtre borne | 10x4 | +0.91 % | 6266 |
| Filtre borne | 20x4 | +0.71 % | 12749 |
| Filtre borne | 50x5 | +0.10 % | 38086 |
| Sans filtre (toutes les actions) | 5x tout | +1.01 % | 5856 |
| Sans filtre (toutes les actions) | 20x tout | +0.66 % | 24748 |
| Sans filtre (toutes les actions) | 50x tout | +0.36 % | 62100 |
| Sans filtre (toutes les actions) | 100x tout | +0.15 % | 126090 |
| Sans filtre (toutes les actions) | 200x tout | +0.01 % | 248089 |
