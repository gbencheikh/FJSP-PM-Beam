# Comparaison — 134 instances, régime A, facteur de seuil 1000

C_max moyen sur les graines disponibles ; écart au meilleur connu = meilleure valeur, toutes méthodes de la banque.

| Méthode [configuration] | C_max moyen | Écart moyen au meilleur connu | V/E/D de imit-ft |
|---|---|---|---|
| Recuit simulé [evals=50000,depart=heuristique,params=taguchi] | 894.7 | +0.3 % | 0/0/134 |
| Recherche tabou [evals=50000,depart=heuristique,params=taguchi] | 901.0 | +1.0 % | 0/0/134 |
| MWKR+EFT | 968.3 | +8.6 % | 0/0/134 |
| MOR+EFT | 980.8 | +10.2 % | 0/0/134 |
| FIFO+EFT | 998.1 | +11.5 % | 0/0/134 |
| SPT+EFT | 1085.9 | +22.6 % | 9/0/125 |
| LPT+EFT | 1112.3 | +24.9 % | 7/0/127 |
| LOR+EFT | 1157.7 | +30.8 % | 12/0/122 |
| LWKR+EFT | 1187.7 | +34.4 % | 17/0/117 |
| RL:imit-ft [echantillons=100] | 1288.7 | +46.6 % | – |
| RL:imit-ft [glouton] | 1780.6 | +100.2 % | 134/0/0 |
| MOR+SPTM | 2030.0 | +123.2 % | 84/0/50 |
| MWKR+SPTM | 2028.9 | +123.4 % | 84/0/50 |
| FIFO+SPTM | 2064.6 | +126.9 % | 86/1/47 |
| SPT+SPTM | 2135.9 | +134.6 % | 93/0/41 |
| LPT+SPTM | 2202.7 | +141.6 % | 98/0/36 |
| LOR+SPTM | 2251.5 | +147.4 % | 102/0/32 |
| LWKR+SPTM | 2265.5 | +149.3 % | 104/0/30 |

V/E/D = victoires / égalités / défaites de l'agent face à la méthode de la ligne, instance par instance.
