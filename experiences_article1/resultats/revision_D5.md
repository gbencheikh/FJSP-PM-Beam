# D5 — filtre appris pour filtrer (analyse déclarée)

127 instances ; écart au recuit 50k (%).

| Réglage | Filtre appris | Réseau final | Meilleur filtre simple | Plannings (appris / final / simple) |
|---|---|---|---|---|
| 5×4 | +0.76 % | +0.76 % | regle +1.07 % | 3580 / 3580 / 3269 |
| 10×4 | +0.34 % | +0.34 % | regle +0.83 % | 7161 / 7161 / 6467 |
| 20×4 | +0.27 % | +0.27 % | regle +0.50 % | 14240 / 14240 / 13035 |
| 50×5 | +0.05 % | +0.05 % | borne +0.10 % | 41326 / 41326 / 38086 |

Glouton du filtre appris (descriptif) : +7.32 %.

## (A) contre le réseau final

| Réglage | Différence | IC 95 % | p Holm (4) |
|---|---|---|---|
| 5×4 | +0.000 | [+0.00 ; +0.00] | 1 |
| 10×4 | +0.000 | [+0.00 ; +0.00] | 1 |
| 20×4 | +0.000 | [+0.00 ; +0.00] | 1 |
| 50×5 | +0.000 | [+0.00 ; +0.00] | 1 |

Test global : +0.000 point, IC 95 % [+0.00 ; +0.00], p = 1 ; réglages significatifs : 0/4.

## (B) contre le meilleur filtre simple

| Réglage | Différence | IC 95 % | p Holm (4) |
|---|---|---|---|
| 5×4 | -0.304 | [-0.67 ; +0.06] | 0.199 |
| 10×4 | -0.489 | [-0.83 ; -0.17] | 0.0712 |
| 20×4 | -0.223 | [-0.50 ; +0.04] | 0.198 |
| 50×5 | -0.054 | [-0.30 ; +0.18] | 0.641 |

Test global : -0.268 point, IC 95 % [-0.49 ; -0.06], p = 0.00236 ; réglages significatifs : 0/4.
