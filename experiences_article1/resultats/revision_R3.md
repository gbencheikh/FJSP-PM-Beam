# R3 — trois graines d'entraînement

127 instances de test ; écart au recuit Taguchi 50k.

## Dispersion (déclaré)

| Réglage | Graine 0 | Graine 1 | Graine 2 | Moyenne | Étendue |
|---|---|---|---|---|---|
| glouton | +7.32 % | +12.38 % | +7.85 % | +9.18 % | 5.06 pt |
| 100 tirages | +2.22 % | +2.57 % | +1.41 % | +2.07 % | 1.15 pt |
| faisceau 5x4 | +0.76 % | +0.81 % | +0.80 % | +0.79 % | 0.05 pt |
| faisceau 50x5 | +0.05 % | +0.07 % | +0.00 % | +0.04 % | 0.06 pt |

## Contre le meilleur filtre non appris de R1 (exploratoire, Holm sur 6 tests)

| Réglage | Graine | Écart réseau | Écart filtre | Différence | IC 95 % | p brut | p Holm |
|---|---|---|---|---|---|---|---|
| faisceau=5,k=4 | 0 | +0.76 % | +1.07 % | -0.30 | [-0.67 ; +0.06] | 0.099 | 0.6 |
| faisceau=5,k=4 | 1 | +0.81 % | +1.07 % | -0.26 | [-0.63 ; +0.11] | 0.25 | 1 |
| faisceau=5,k=4 | 2 | +0.80 % | +1.07 % | -0.27 | [-0.67 ; +0.11] | 0.26 | 1 |
| faisceau=50,k=5 | 0 | +0.05 % | +0.10 % | -0.05 | [-0.30 ; +0.18] | 0.64 | 1 |
| faisceau=50,k=5 | 1 | +0.07 % | +0.10 % | -0.04 | [-0.29 ; +0.20] | 0.67 | 1 |
| faisceau=50,k=5 | 2 | +0.00 % | +0.10 % | -0.10 | [-0.39 ; +0.19] | 0.29 | 1 |

## Équivalence ±1 % au recuit, faisceau 50×5 (exploratoire pour les graines 1 et 2)

| Graine | Écart moyen | IC 90 % | Dans ±1 % ? |
|---|---|---|---|
| 0 | +0.05 % | [-0.53 ; +0.62] | oui |
| 1 | +0.07 % | [-0.51 ; +0.62] | oui |
| 2 | +0.00 % | [-0.56 ; +0.54] | oui |
