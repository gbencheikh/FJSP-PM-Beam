# Banque de résultats

Tous les résultats par instance sont enregistrés ici, une fois pour toutes :

| Fichier | Contenu |
|---|---|
| `resultats.csv` | une ligne par exécution : instance, régime, facteur de seuil, méthode, configuration, graine, C_max, nombre de maintenances, pannes, temps, date, identifiant du planning |
| `solutions.jsonl` | le planning complet de chaque exécution : liste `[machine, début, fin, type, job]`, type 1 = opération, 2 = maintenance, 3 = réparation |
| `banque.py` | lecture / écriture / suppression |

Les scripts `regles_priorite.comparer`, `metaheuristiques.comparer` et `comparer_rl.py` consultent
la banque avant de lancer quoi que ce soit : une exécution déjà présente (même instance, régime,
facteur de seuil, méthode, configuration, graine) n'est jamais relancée. Pour forcer : `--forcer`.

Comparer un nouvel agent RL sans relancer les autres méthodes :

```
python comparer_rl.py --modele models/v3/A_full_s0_best.pt --nom complet-s0
```

Seul l'agent est exécuté ; le tableau `comparaisons/comparaison_seuil1.md` et le fichier
`comparaisons/comparaison_seuil1.csv` (une ligne par instance, une colonne par méthode) sont
reconstruits à partir de la banque.

Lire la banque dans Python :

```python
from banque_resultats import banque
lignes = banque.charger()                                    # liste de dicts
mk1 = [l for l in lignes if l["instance"] == "BrandimarteMk1"]
plan = banque.planning(mk1[0])                               # planning complet
banque.supprimer(lambda l: l["methode"] == "RL:essai")      # retirer des lignes
```

Note : les métaheuristiques sont arrêtées au bout d'un temps donné. Relancées, elles peuvent donner
un C_max légèrement différent (le nombre d'itérations dépend de la vitesse de la machine) : c'est
une raison de plus pour garder les résultats une fois pour toutes.
