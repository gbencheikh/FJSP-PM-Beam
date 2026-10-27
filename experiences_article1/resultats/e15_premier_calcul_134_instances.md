# E15 — valeur de la décision de maintenance (ordre et affectation figés)

Politiques : au plus tard (référence), au plus tôt, systématique, source, aléatoire (100 tirages, p = 1/2), recuit sur le placement seul (20000 évaluations, graines [0, 1, 2, 3, 4]). Unité : l'instance ; écart = C_max / C_max(au plus tard) − 1 ; IC bootstrap 95 % ; Wilcoxon apparié, Holm.

Contrôle du redécodage semi-actif : 268/268 plannings source retrouvés avec un C_max ≤ celui de la banque.


## Source : Recuit simulé|evals=50000,depart=heuristique,params=taguchi (134 instances)

| Politique | Écart moyen | IC 95 % | Médiane | V/E/D | p (Holm) | Maint./inst. | Part dans un temps mort | Usure c/T |
|---|---|---|---|---|---|---|---|---|
| Au plus tard (référence) | 0 | | | | | 12.6 | 16 % | 0.92 |
| Au plus tôt | +5.89 % | [+5.29 ; +6.51] | +5.30 % | 0/10/124 | 1.7e-21 | 12.6 | 11 % | 0.77 |
| Systématique | +83.39 % | [+80.76 ; +86.00] | +86.18 % | 0/0/134 | 6.9e-23 | 137.2 | 15 % | 0.14 |
| Source | +0.00 % | [+0.00 ; +0.00] | +0.00 % | 0/134/0 | 1 | 12.6 | 16 % | 0.92 |
| Aléatoire (moyenne) | +48.11 % | [+46.53 ; +49.69] | +49.35 % | 0/0/134 | 6.9e-23 | 69.1 | 14 % | 0.25 |
| Aléatoire (meilleur des tirages) | +32.27 % | [+30.56 ; +33.97] | +32.90 % | 0/2/132 | 1e-22 | 69.1 | 14 % | 0.25 |
| Recuit placement (moyenne des graines) | -0.02 % | [-0.04 ; -0.00] | +0.00 % | 10/124/0 | 0.014 | 13.2 | 16 % | 0.90 |
| Recuit placement (meilleure graine) | -0.02 % | [-0.04 ; -0.01] | +0.00 % | 10/124/0 | 0.014 | 13.2 | 16 % | 0.90 |

Mécanisme — Spearman(part des maintenances dans un temps mort, C_max) par instance, 109 placements : médiane +0.16 ; de signe attendu (négatif) et significatif (p < 0,05) sur 12/134 instances.

Mécanisme — Spearman(nombre de maintenances qui retardent l'opération suivante, C_max) par instance, 109 placements : médiane +0.59 ; de signe attendu (positif) et significatif (p < 0,05) sur 134/134 instances.

Mécanisme — Spearman(nombre total de maintenances, C_max) par instance, 109 placements : médiane +0.66 ; de signe attendu (positif) et significatif (p < 0,05) sur 134/134 instances.

## Source : RL:imit-ft|faisceau=5,k=4 (134 instances)

| Politique | Écart moyen | IC 95 % | Médiane | V/E/D | p (Holm) | Maint./inst. | Part dans un temps mort | Usure c/T |
|---|---|---|---|---|---|---|---|---|
| Au plus tard (référence) | 0 | | | | | 12.9 | 9 % | 0.93 |
| Au plus tôt | +3.10 % | [+2.54 ; +3.67] | +2.82 % | 14/19/101 | 3e-16 | 12.9 | 9 % | 0.75 |
| Systématique | +78.46 % | [+75.62 ; +81.26] | +79.83 % | 0/0/134 | 6.9e-23 | 137.2 | 14 % | 0.14 |
| Source | -1.70 % | [-2.10 ; -1.31] | +0.00 % | 63/69/2 | 5.9e-12 | 13.7 | 13 % | 0.88 |
| Aléatoire (moyenne) | +44.21 % | [+42.41 ; +45.98] | +44.77 % | 0/0/134 | 6.9e-23 | 69.1 | 13 % | 0.26 |
| Aléatoire (meilleur des tirages) | +28.74 % | [+26.93 ; +30.55] | +29.35 % | 0/2/132 | 1e-22 | 69.1 | 13 % | 0.26 |
| Recuit placement (moyenne des graines) | -1.65 % | [-2.04 ; -1.27] | -0.10 % | 68/66/0 | 2.3e-12 | 17.5 | 13 % | 0.80 |
| Recuit placement (meilleure graine) | -1.83 % | [-2.24 ; -1.43] | -0.12 % | 68/66/0 | 2.3e-12 | 17.5 | 13 % | 0.80 |

Mécanisme — Spearman(part des maintenances dans un temps mort, C_max) par instance, 109 placements : médiane +0.20 ; de signe attendu (négatif) et significatif (p < 0,05) sur 6/134 instances.

Mécanisme — Spearman(nombre de maintenances qui retardent l'opération suivante, C_max) par instance, 109 placements : médiane +0.58 ; de signe attendu (positif) et significatif (p < 0,05) sur 134/134 instances.

Mécanisme — Spearman(nombre total de maintenances, C_max) par instance, 109 placements : médiane +0.65 ; de signe attendu (positif) et significatif (p < 0,05) sur 134/134 instances.
