# Élagage par famille (127 instances, depuis `taux_elagage.csv`)

« Borne = incumbent » : enfant élagué dont la borne inférieure égale le meilleur planning connu au moment de la coupure (au mieux une égalité) ; sinon borne strictement supérieure.

## 1. Taux d'élagage et part « borne = incumbent » (moyenne par instance ; entre parenthèses : poolée)

| Groupe | n | politique 1x4 | politique 5x4 | politique 50x5 | regle 5x0 | regle 50x0 |
|---|---|---|---|---|---|---|
| Toutes | 127 | 3.4 % ; 54 % (49 %) | 4.6 % ; 58 % (54 %) | 6.1 % ; 61 % (56 %) | 6.2 % ; 54 % (48 %) | 6.4 % ; 51 % (44 %) |
| Brandimarte | 10 | 2.5 % ; 78 % (71 %) | 2.7 % ; 92 % (89 %) | 2.9 % ; 81 % (78 %) | 3.9 % ; 74 % (60 %) | 3.3 % ; 65 % (53 %) |
| Hurink edata | 37 | 2.1 % ; 72 % (68 %) | 2.8 % ; 66 % (66 %) | 4.2 % ; 76 % (76 %) | 2.4 % ; 82 % (80 %) | 3.0 % ; 71 % (68 %) |
| Hurink rdata | 36 | 2.6 % ; 55 % (54 %) | 3.3 % ; 55 % (52 %) | 4.1 % ; 61 % (56 %) | 3.5 % ; 42 % (38 %) | 4.3 % ; 51 % (45 %) |
| Hurink vdata | 40 | 3.5 % ; 25 % (19 %) | 5.3 % ; 41 % (36 %) | 7.5 % ; 41 % (34 %) | 7.3 % ; 35 % (33 %) | 7.0 % ; 29 % (29 %) |
| Kacem | 4 | 24.0 % ; 92 % (93 %) | 30.3 % ; 95 % (95 %) | 36.3 % ; 81 % (78 %) | 60.8 % ; 62 % (56 %) | 57.8 % ; 51 % (43 %) |
| Hurink (3 jeux) | 113 | 2.7 % ; 50 % (45 %) | 3.9 % ; 54 % (50 %) | 5.4 % ; 59 % (54 %) | 4.5 % ; 52 % (45 %) | 4.8 % ; 50 % (43 %) |

Cellule : taux d'élagage ; part « borne = incumbent ».

## 2. Politique contre règle (même B), part « borne = incumbent » appariée par instance

| Paire | Groupe | n | Politique | Règle | Politique plus haute / égale / plus basse | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| politique 5x4 / regle 5x0 | Toutes | 127 | 58 % | 54 % | 55/23/49 | 0.41 | 1 |
| politique 5x4 / regle 5x0 | Brandimarte | 10 | 92 % | 74 % | 6/3/1 | 0.031 | 0.25 |
| politique 5x4 / regle 5x0 | Hurink edata | 37 | 66 % | 82 % | 9/11/17 | 0.022 | 0.2 |
| politique 5x4 / regle 5x0 | Hurink rdata | 36 | 55 % | 42 % | 19/5/12 | 0.16 | 1 |
| politique 5x4 / regle 5x0 | Hurink vdata | 40 | 41 % | 35 % | 17/4/19 | 0.69 | 1 |
| politique 5x4 / regle 5x0 | Kacem | 4 | 95 % | 62 % | 4/0/0 | – | – |
| politique 5x4 / regle 5x0 | Hurink (3 jeux) | 113 | 54 % | 52 % | 45/20/48 | 0.98 | 1 |
| politique 50x5 / regle 50x0 | Toutes | 127 | 61 % | 51 % | 70/12/45 | 0.0026 | 0.032 |
| politique 50x5 / regle 50x0 | Brandimarte | 10 | 81 % | 65 % | 5/2/3 | 0.2 | 1 |
| politique 50x5 / regle 50x0 | Hurink edata | 37 | 76 % | 71 % | 18/4/15 | 0.59 | 1 |
| politique 50x5 / regle 50x0 | Hurink rdata | 36 | 61 % | 51 % | 17/6/13 | 0.16 | 1 |
| politique 50x5 / regle 50x0 | Hurink vdata | 40 | 41 % | 29 % | 27/0/13 | 0.012 | 0.12 |
| politique 50x5 / regle 50x0 | Kacem | 4 | 81 % | 51 % | 3/0/1 | – | – |
| politique 50x5 / regle 50x0 | Hurink (3 jeux) | 113 | 59 % | 50 % | 62/10/41 | 0.011 | 0.12 |

Test non fait si n < 6 (Kacem, 4 instances).

## 3. Serrage de l'incumbent

Écart = C_max final du faisceau (politique) / meilleure borne inférieure disponible − 1 (max de la borne du moteur à la racine, de la borne FJSPLib du FJSP classique et des bornes CP-SAT d'E9). C'est une borne SUPÉRIEURE de l'écart à l'optimum.

| Réglage | Groupe | Écart médian | Spearman(écart, taux d'élagage) | Spearman(écart, part borne = incumbent) |
|---|---|---|---|---|
| politique 5x4 | Toutes | 12.0 % | -0.24 (p 0.0056) | +0.01 (p 0.9) |
| politique 5x4 | Brandimarte | 8.0 % | -0.15 (p 0.68) | -0.58 (p 0.082) |
| politique 5x4 | Hurink edata | 16.1 % | -0.48 (p 0.0028) | -0.20 (p 0.23) |
| politique 5x4 | Hurink rdata | 15.9 % | -0.06 (p 0.73) | +0.17 (p 0.32) |
| politique 5x4 | Hurink vdata | 8.0 % | +0.54 (p 0.00032) | -0.08 (p 0.63) |
| politique 5x4 | Kacem | 0.0 % | – | – |
| politique 5x4 | Hurink (3 jeux) | 12.1 % | -0.19 (p 0.047) | +0.10 (p 0.28) |
| politique 50x5 | Toutes | 11.1 % | -0.29 (p 0.00092) | +0.07 (p 0.44) |
| politique 50x5 | Brandimarte | 9.4 % | -0.05 (p 0.88) | -0.58 (p 0.078) |
| politique 50x5 | Hurink edata | 14.4 % | -0.48 (p 0.0026) | -0.03 (p 0.87) |
| politique 50x5 | Hurink rdata | 13.9 % | +0.01 (p 0.96) | +0.21 (p 0.23) |
| politique 50x5 | Hurink vdata | 7.6 % | +0.51 (p 0.00071) | -0.30 (p 0.056) |
| politique 50x5 | Kacem | 0.0 % | – | – |
| politique 50x5 | Hurink (3 jeux) | 11.3 % | -0.24 (p 0.0097) | +0.18 (p 0.061) |
