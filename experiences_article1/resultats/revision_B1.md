# B1 — ablation du départage des ex aequo (analyse déclarée)

127 instances ; écart au recuit 50k (%).

| Réglage | Réseau (article) | Réseau, départage par ordre | Meilleur filtre (ordre) | Meilleur filtre (rang) |
|---|---|---|---|---|
| 5×4 | +0.76 % | +1.21 % | regle +1.07 % | borne +1.20 % |
| 50×5 | +0.05 % | +0.21 % | borne +0.10 % | borne +0.13 % |

## (a) réseau départagé par ordre − meilleur filtre (ordre)

| Réglage | Différence | p Holm (2) |
|---|---|---|
| 5×4 | +0.146 | 0.744 |
| 50×5 | +0.110 | 0.534 |

Test groupé : +0.128 point, IC 95 % [-0.12 ; +0.38], par grappes [-0.10 ; +0.37], p = 0.691.

## (b) réseau (article) − meilleur filtre départagé par rang

| Réglage | Différence | p Holm (2) |
|---|---|---|
| 5×4 | -0.434 | 0.0381 |
| 50×5 | -0.077 | 0.367 |

Test groupé : -0.255 point, IC 95 % [-0.51 ; -0.01], par grappes [-0.53 ; -0.02], p = 0.01.

## (c) réseau (article) − réseau départagé par ordre

| Réglage | Différence | p Holm (2) |
|---|---|---|
| 5×4 | -0.450 | 0.0577 |
| 50×5 | -0.165 | 0.0577 |

Test groupé : -0.307 point, IC 95 % [-0.52 ; -0.11], par grappes [-0.54 ; -0.10], p = 0.00432.

Ex aequo sur H à la coupure (B-ième et (B+1)-ième enfants), toutes variantes de B1 : 169787/199053 = 85.3 %.

**Verdict (règle déclarée)** : sans le départage, le gain n'est plus établi → attribué, au moins en partie, au départage.
