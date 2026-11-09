# Result bank

Every run is recorded once and for all.

| File | Content |
|---|---|
| `resultats.csv` | One line per run: instance, regime, threshold factor, method, configuration, seed, makespan, number of maintenances, breakdowns (always 0 here), running time, date, identifier of the schedule, number of evaluated schedules |
| `solutions.jsonl.gz` | The complete schedule of every run: list of `[machine, start, end, type, job]`, type 1 = operation, 2 = maintenance |
| `resultats_mu3.csv`, `resultats_phi1.csv`, `resultats_phi2.csv`, `resultats_TkLk.csv` (+ schedules) | Variants of the instance generator, kept in separate banks (see the main README) |
| `banque.py` | Reading, writing and deleting lines |

The schedules are decompressed automatically (`solutions*.jsonl`) the first time the module is imported.

The comparison scripts (`regles_priorite.comparer`, `metaheuristiques.comparer`, `comparer_rl.py`, `anticiper.py`)
read the bank before running anything: a run that is already present (same instance, regime, threshold factor,
method, configuration and seed) is never repeated. Use `--forcer` to run it again.

Reading the bank in Python:

```python
from banque_resultats import banque
lignes = banque.charger()                                    # list of dicts, one per run
mk1 = [l for l in lignes if l["instance"] == "BrandimarteMk1"]
plan = banque.planning(mk1[0])                               # complete schedule of a run
banque.supprimer(lambda l: l["methode"] == "RL:essai")      # remove lines
```

Metaheuristics stopped by a time limit (steps E10, E10b) may give a slightly different makespan when re-run, because
the number of iterations depends on the speed of the computer: one more reason to keep the results.
