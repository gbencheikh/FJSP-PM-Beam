# Comparaison — 134 instances, régime A, facteur de seuil 1

C_max moyen sur les graines disponibles ; écart au meilleur connu = meilleure valeur, toutes méthodes de la banque.

| Méthode [configuration] | C_max moyen | Écart moyen au meilleur connu | V/E/D de imit-ft |
|---|---|---|---|
| Recuit simulé [evals=50000,depart=heuristique,params=taguchi] | 969.8 | +0.7 % | 21/4/109 |
| Recherche tabou [evals=50000,depart=heuristique,params=taguchi] | 976.4 | +1.4 % | 24/3/107 |
| RL:imit-ft [echantillons=100] | 994.9 | +3.0 % | – |
| Algorithme génétique [evals=50000,depart=heuristique,params=taguchi] | 1030.4 | +6.8 % | 97/4/33 |
| RL:imit-ft [glouton] | 1040.4 | +8.1 % | 124/2/8 |
| MWKR+EFT | 1104.0 | +15.2 % | 132/2/0 |
| MOR+EFT | 1119.0 | +16.7 % | 132/1/1 |
| FIFO+EFT | 1163.8 | +21.1 % | 131/2/1 |
| LPT+EFT | 1266.4 | +32.3 % | 134/0/0 |
| SPT+EFT | 1260.1 | +32.3 % | 134/0/0 |
| LOR+EFT | 1335.7 | +39.7 % | 134/0/0 |
| LWKR+EFT | 1365.9 | +43.2 % | 134/0/0 |
| MOR+SPTM | 2262.9 | +132.4 % | 134/0/0 |
| MWKR+SPTM | 2259.1 | +132.6 % | 134/0/0 |
| FIFO+SPTM | 2301.4 | +136.6 % | 134/0/0 |
| SPT+SPTM | 2387.0 | +145.2 % | 134/0/0 |
| LPT+SPTM | 2464.1 | +152.9 % | 134/0/0 |
| LOR+SPTM | 2514.0 | +158.3 % | 134/0/0 |
| LWKR+SPTM | 2525.8 | +159.8 % | 134/0/0 |

V/E/D = victoires / égalités / défaites de l'agent face à la méthode de la ligne, instance par instance.
