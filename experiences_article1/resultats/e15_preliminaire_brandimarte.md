# E15 — valeur de la décision de maintenance (ordre et affectation figés)

Politiques : au plus tard (référence), au plus tôt, systématique, source, aléatoire (100 tirages, p = 1/2), recuit sur le placement seul (20000 évaluations, graines [0, 1, 2, 3, 4]). Unité : l'instance ; écart = C_max / C_max(au plus tard) − 1 ; IC bootstrap 95 % ; Wilcoxon apparié, Holm.

Contrôle du redécodage semi-actif : 20/20 plannings source retrouvés avec un C_max ≤ celui de la banque.


## Source : Recuit simulé|evals=50000,depart=heuristique,params=taguchi (10 instances)

| Politique | Écart moyen | IC 95 % | Médiane | V/E/D | p (Holm) | Maint./inst. | Part dans un temps mort | Usure c/T |
|---|---|---|---|---|---|---|---|---|
| Au plus tard (référence) | 0 | | | | | 16.9 | 18 % | 0.91 |
| Au plus tôt | +2.41 % | [+1.14 ; +3.80] | +1.74 % | 0/2/8 | 0.031 | 16.9 | 17 % | 0.76 |
| Systématique | +72.57 % | [+60.63 ; +82.62] | +77.90 % | 0/0/10 | 0.014 | 133.7 | 19 % | 0.16 |
| Source | +0.00 % | [+0.00 ; +0.00] | +0.00 % | 0/10/0 | 1 | 16.9 | 18 % | 0.91 |
| Aléatoire (moyenne) | +36.29 % | [+28.94 ; +42.28] | +40.43 % | 0/0/10 | 0.014 | 68.4 | 18 % | 0.29 |
| Aléatoire (meilleur des tirages) | +22.70 % | [+16.44 ; +28.14] | +24.93 % | 0/0/10 | 0.014 | 68.4 | 18 % | 0.29 |
| Recuit placement (moyenne des graines) | +0.00 % | [+0.00 ; +0.00] | +0.00 % | 0/10/0 | 1 | 16.9 | 18 % | 0.91 |
| Recuit placement (meilleure graine) | +0.00 % | [+0.00 ; +0.00] | +0.00 % | 0/10/0 | 1 | 16.9 | 18 % | 0.91 |

Mécanisme — Spearman(part des maintenances dans un temps mort, C_max) par instance, 109 placements : médiane +0.14 ; de signe attendu (négatif) et significatif (p < 0,05) sur 2/10 instances.

Mécanisme — Spearman(nombre de maintenances qui retardent l'opération suivante, C_max) par instance, 109 placements : médiane +0.64 ; de signe attendu (positif) et significatif (p < 0,05) sur 10/10 instances.

Mécanisme — Spearman(nombre total de maintenances, C_max) par instance, 109 placements : médiane +0.71 ; de signe attendu (positif) et significatif (p < 0,05) sur 10/10 instances.

## Source : RL:imit-ft|faisceau=5,k=4 (10 instances)

| Politique | Écart moyen | IC 95 % | Médiane | V/E/D | p (Holm) | Maint./inst. | Part dans un temps mort | Usure c/T |
|---|---|---|---|---|---|---|---|---|
| Au plus tard (référence) | 0 | | | | | 16.0 | 14 % | 0.91 |
| Au plus tôt | +0.72 % | [-0.04 ; +1.59] | +0.00 % | 1/5/4 | 0.5 | 16.0 | 17 % | 0.74 |
| Systématique | +69.77 % | [+54.57 ; +82.61] | +73.31 % | 0/0/10 | 0.014 | 133.7 | 18 % | 0.15 |
| Source | -1.10 % | [-2.10 ; -0.21] | +0.00 % | 4/6/0 | 0.5 | 16.8 | 19 % | 0.87 |
| Aléatoire (moyenne) | +33.99 % | [+25.22 ; +41.23] | +37.96 % | 0/0/10 | 0.014 | 68.3 | 17 % | 0.28 |
| Aléatoire (meilleur des tirages) | +21.30 % | [+13.36 ; +28.34] | +25.91 % | 0/1/9 | 0.02 | 68.3 | 17 % | 0.28 |
| Recuit placement (moyenne des graines) | -1.00 % | [-1.88 ; -0.21] | +0.00 % | 4/6/0 | 0.5 | 19.6 | 15 % | 0.80 |
| Recuit placement (meilleure graine) | -1.10 % | [-2.10 ; -0.21] | +0.00 % | 4/6/0 | 0.5 | 19.6 | 15 % | 0.80 |

Mécanisme — Spearman(part des maintenances dans un temps mort, C_max) par instance, 109 placements : médiane +0.11 ; de signe attendu (négatif) et significatif (p < 0,05) sur 1/10 instances.

Mécanisme — Spearman(nombre de maintenances qui retardent l'opération suivante, C_max) par instance, 109 placements : médiane +0.60 ; de signe attendu (positif) et significatif (p < 0,05) sur 10/10 instances.

Mécanisme — Spearman(nombre total de maintenances, C_max) par instance, 109 placements : médiane +0.68 ; de signe attendu (positif) et significatif (p < 0,05) sur 10/10 instances.
