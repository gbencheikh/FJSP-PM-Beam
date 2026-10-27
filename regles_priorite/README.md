# Règles de priorité — FJSP avec maintenance préventive

Une règle = une règle d'opération (quelle opération lancer) + une règle de machine (sur quelle
machine). La maintenance suit pour toutes la même règle « juste à temps » : si l'opération ne tient
pas dans la marge d'usure de la machine, maintenance d'abord, puis l'opération.

| Règle d'opération | Choisit l'opération prête… |
|---|---|
| SPT | la plus courte |
| LPT | la plus longue |
| MWKR | dont le job a le plus de travail restant |
| LWKR | dont le job a le moins de travail restant |
| MOR | dont le job a le plus d'opérations restantes |
| LOR | dont le job a le moins d'opérations restantes |
| FIFO | prête depuis le plus longtemps |
| WSPT | la plus courte rapportée au poids du job (poids = 1 par défaut : les .fjs n'en ont pas) |

| Règle de machine | Choisit… |
|---|---|
| EFT | la machine qui terminera l'opération le plus tôt (attente + maintenance éventuelle + durée) |
| SPTM | la machine la plus rapide pour cette opération |

```
python -m regles_priorite.comparer
python -m regles_priorite.comparer --familles Brandimarte --facteur-seuil 0.7
```

Ajouter une règle : une ligne dans `REGLES_OPERATION` (fichier `regles.py`), une fonction
`clé(env, job, poids)` — la plus petite clé est la plus prioritaire.
