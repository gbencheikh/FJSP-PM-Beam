# Réglage des métaheuristiques par la méthode de Taguchi

Tableau orthogonal L9 ; 8 instances de réglage (HurinkEdata3, HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18, HurinkRdata28, HurinkRdata38) ; graines [0, 1] ; 50000 évaluations par exécution ; départ MWKR+EFT.
Réponse : C_max relatif à MWKR+EFT (plus petit = meilleur). S/N = −10·log10(moyenne des y²), plus grand = meilleur et plus stable.

## Algorithme génétique

### Les 9 essais du tableau L9

| Essai | population | p_croisement | p_mutation | elite | C_max relatif moyen | S/N (dB) |
|---|---|---|---|---|---|---|
| 1 | 30 | 0.6 | 0.05 | 1 | 0.9148 | 0.762 |
| 2 | 30 | 0.8 | 0.1 | 2 | 0.9119 | 0.786 |
| 3 | 30 | 0.95 | 0.2 | 5 | 0.9162 | 0.745 |
| 4 | 60 | 0.6 | 0.1 | 5 | 0.9136 | 0.772 |
| 5 | 60 | 0.8 | 0.2 | 1 | 0.9173 | 0.729 |
| 6 | 60 | 0.95 | 0.05 | 2 | 0.9078 | 0.825 |
| 7 | 100 | 0.6 | 0.2 | 2 | 0.9253 | 0.660 |
| 8 | 100 | 0.8 | 0.05 | 5 | 0.9044 | 0.855 |
| 9 | 100 | 0.95 | 0.1 | 1 | 0.9092 | 0.793 |

### Effet de chaque niveau (S/N moyen, dB) et contribution

| Paramètre | Niveau 1 | Niveau 2 | Niveau 3 | Écart max. | Contribution (ANOVA) | Niveau retenu |
|---|---|---|---|---|---|---|
| p_mutation | 0.05 : 0.814 | 0.1 : 0.784 | 0.2 : 0.711 | 0.103 | 65.3 % | **0.05** |
| p_croisement | 0.6 : 0.731 | 0.8 : 0.790 | 0.95 : 0.788 | 0.059 | 25.9 % | **0.8** |
| elite | 1 : 0.761 | 2 : 0.757 | 5 : 0.791 | 0.034 | 8.1 % | **5** |
| population | 30 : 0.764 | 60 : 0.775 | 100 : 0.769 | 0.011 | 0.7 % | **60** |

## Recherche tabou

### Les 9 essais du tableau L9

| Essai | n_voisins | tenure | C_max relatif moyen | S/N (dB) |
|---|---|---|---|---|
| 1 | 20 | 6 | 0.8790 | 1.095 |
| 2 | 20 | 12 | 0.8830 | 1.059 |
| 3 | 20 | 24 | 0.8730 | 1.150 |
| 4 | 40 | 6 | 0.8750 | 1.138 |
| 5 | 40 | 12 | 0.8801 | 1.092 |
| 6 | 40 | 24 | 0.8797 | 1.095 |
| 7 | 80 | 6 | 0.8752 | 1.139 |
| 8 | 80 | 12 | 0.8786 | 1.105 |
| 9 | 80 | 24 | 0.8830 | 1.063 |

### Effet de chaque niveau (S/N moyen, dB) et contribution

| Paramètre | Niveau 1 | Niveau 2 | Niveau 3 | Écart max. | Contribution (ANOVA) | Niveau retenu |
|---|---|---|---|---|---|---|
| tenure | 6 : 1.124 | 12 : 1.085 | 24 : 1.103 | 0.038 | 26.1 % | **6** |
| n_voisins | 20 : 1.101 | 40 : 1.108 | 80 : 1.102 | 0.007 | 1.0 % | **40** |

Part non expliquée par les paramètres (interactions + bruit) : 72.9 %.

## Recuit simulé

### Les 9 essais du tableau L9

| Essai | p0 | ratio_fin | C_max relatif moyen | S/N (dB) |
|---|---|---|---|---|
| 1 | 0.3 | 0.01 | 0.8706 | 1.175 |
| 2 | 0.3 | 0.001 | 0.8668 | 1.217 |
| 3 | 0.3 | 0.0001 | 0.8667 | 1.216 |
| 4 | 0.5 | 0.01 | 0.8779 | 1.109 |
| 5 | 0.5 | 0.001 | 0.8749 | 1.142 |
| 6 | 0.5 | 0.0001 | 0.8724 | 1.165 |
| 7 | 0.8 | 0.01 | 0.8888 | 0.994 |
| 8 | 0.8 | 0.001 | 0.8730 | 1.156 |
| 9 | 0.8 | 0.0001 | 0.8734 | 1.153 |

### Effet de chaque niveau (S/N moyen, dB) et contribution

| Paramètre | Niveau 1 | Niveau 2 | Niveau 3 | Écart max. | Contribution (ANOVA) | Niveau retenu |
|---|---|---|---|---|---|---|
| p0 | 0.3 : 1.202 | 0.5 : 1.139 | 0.8 : 1.101 | 0.102 | 44.2 % | **0.3** |
| ratio_fin | 0.01 : 1.093 | 0.001 : 1.171 | 0.0001 : 1.178 | 0.085 | 38.0 % | **0.0001** |

Part non expliquée par les paramètres (interactions + bruit) : 17.8 %.

## Confirmation

| Méthode | Paramètres retenus | S/N prédit | S/N obtenu (retenus) | S/N par défaut | C_max relatif retenus | C_max relatif défaut | Décision |
|---|---|---|---|---|---|---|---|
| Algorithme génétique | population=60, p_croisement=0.8, p_mutation=0.05, elite=5 | 0.861 | 0.770 | 0.786 | 0.9143 | 0.9118 | défaut conservé |
| Recherche tabou | n_voisins=40, tenure=6 | 1.128 | 1.138 | 1.092 | 0.8750 | 0.8801 | retenus |
| Recuit simulé | p0=0.3, ratio_fin=0.0001 | 1.233 | 1.216 | 1.142 | 0.8667 | 0.8749 | retenus |

Si le S/N obtenu est proche du S/N prédit, l'hypothèse de Taguchi (peu d'interactions entre paramètres) est raisonnable. Si les paramètres retenus ne battent pas les valeurs par défaut, les valeurs par défaut sont conservées dans parametres_retenus.json.
