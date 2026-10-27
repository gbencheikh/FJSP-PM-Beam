# Métaheuristiques — FJSP avec maintenance préventive

Trois méthodes qui résolvent le même problème, avec le même codage et le même décodage :

| Fichier | Méthode | Paramètres par défaut |
|---|---|---|
| `genetique.py` | Algorithme génétique | population 60, croisement 0,8, mutation 0,1, élitisme 2 |
| `tabou.py` | Recherche tabou | 40 voisins par itération, durée tabou 12 |
| `recuit_simule.py` | Recuit simulé | probabilité initiale d'accepter une dégradation 0,5, refroidissement géométrique sur le temps |
| `codage.py` | Codage OS/MS, décodage avec maintenance, voisinage | – |
| `instances.py` | Chargement des instances .fjs + paramètres de maintenance | – |
| `comparer.py` | Comparaison à budget de temps égal | – |

Toutes les méthodes s'arrêtent quand le budget de temps est écoulé, et tous les plannings sont
vérifiés (pas de chevauchement, usure ≤ seuil entre deux maintenances, donc aucune panne).

```
python -m metaheuristiques.comparer --budget 10 --graines 0 1 2
python -m metaheuristiques.comparer --familles Brandimarte --budget 5 --depart aleatoire --facteur-seuil 0.7
```

Utiliser une méthode seule :

```python
import numpy as np
from metaheuristiques import recuit_simule
from metaheuristiques.instances import charger_instances
inst = charger_instances(["Brandimarte"])[0]
cmax, (OS, MS), info = recuit_simule.resoudre(inst, budget_s=10, rng=np.random.default_rng(0))
```
