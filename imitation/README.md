# Imitation stage

The policy network is first trained to reproduce schedules of a tuned simulated annealing, then refined by
reinforcement learning (`train_v3.py`). Only generated instances are used: the benchmark instances serve for the final
evaluation only, and the best model is selected on generated validation instances.

| File | Role |
|---|---|
| `experts.py` | Computes the expert schedules (simulated annealing, Taguchi parameters) on generated instances; `experts.jsonl` contains the 2 000 schedules used in the article |
| `rejeu.py` | Replays an expert schedule in the decision process and recovers the actions consistent with it |
| `entrainer.py` | Imitation training (and, with `--iterations`, an expert-iteration variant not used in the article) |
| `filtre_appris.py` | Retraining of the network for the filtering role (companion analysis D5) |
| `eleve_recuit.py`, `auto_amelioration.py` | Earlier attempts not used in the article: dataset aggregation with a simulated-annealing judge, and expert iteration with the search |

Commands used for the article (from the root of the repository):

```bash
python -m imitation.experts --nombre 2000 --evaluations 50000 --parametres reglage_taguchi/parametres_retenus.json --processus 8
python -m imitation.entrainer --reseau candidats --epoques 20 --seed 0 --out models/imitation/cand
python train_v3.py --init models/imitation/cand_best.pt --lr 1e-4 --ppo_steps 300000 --seed 0 --out models/imitation/cand_ft
```

The training log reports the agreement with the expert and the mean greedy makespan on the validation instances.
The graph network of `jssp_pm/fjsp_graphe.py` (option `--reseau graphe`) was explored during development and is not
used in the article.
