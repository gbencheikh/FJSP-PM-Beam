# Metaheuristics

Three methods solve the same problem with the same encoding and the same decoder.

| File | Content |
|---|---|
| `genetique.py` | Genetic algorithm |
| `tabou.py` | Tabu search |
| `recuit_simule.py` | Simulated annealing, with a geometric temperature schedule over the fraction of the budget consumed |
| `codage.py` | Encoding (operation sequence and machine assignment), semi-active decoder with maintenance inserted at the latest feasible position, active decoder (option `FJSP_DECODEUR=actif`), neighbourhoods, budgets |
| `instances.py` | Loading of the `.fjs` files and of the wear parameters |
| `comparer.py` | Runs the methods on the benchmark instances and records the results in the bank |
| `decodeur_actif_prototype.py` | Prototype of the active decoder (exploratory) |

The budget is a number of evaluated schedules (`--evaluations`, used in the article) or a time limit (`--budget`, in
seconds). Every decoded schedule is feasible: no overlap, and the wear never exceeds the threshold between two
maintenances. The parameters tuned by the Taguchi design are in `reglage_taguchi/parametres_retenus.json`.

```bash
python -m metaheuristiques.comparer --evaluations 50000 --parametres reglage_taguchi/parametres_retenus.json --graines 0 1 2 3 4 --processus 8
```

Using one method alone:

```python
import numpy as np
from metaheuristiques import recuit_simule
from metaheuristiques.codage import Budget
from metaheuristiques.instances import charger_instances
inst = charger_instances(["Brandimarte"])[0]
cmax, (OS, MS), info = recuit_simule.resoudre(inst, budget=Budget(evaluations=50000), rng=np.random.default_rng(0))
```
