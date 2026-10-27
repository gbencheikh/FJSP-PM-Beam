# Learned action filtering for decision-time search in flexible job shop scheduling with preventive maintenance

Code, data, trained network and raw results of the article

> G. Bencheikh *et al.*, *Learned action filtering for decision-time search in flexible job shop scheduling with
> preventive maintenance*, submitted to *Computers & Operations Research*, 2026. *(Reference to be completed.)*

The repository contains everything needed to **reproduce every table and figure of the article** from the raw
results, to **re-run any experiment**, and to **evaluate a new method under the same protocol** (same instances,
same feasibility check, same reference, same statistics).

## Problem in one paragraph

Flexible job shop (each operation can run on several machines, with machine-dependent processing times) in which
every machine accumulates wear while processing. An operation of length *p* may start on machine *k* only if the
wear *c_k* satisfies *c_k + p ≤ T_k*; a preventive maintenance of length *M_k* resets the wear to zero. The objective
is the makespan. Production and maintenance are scheduled jointly (regime A of the code: thresholds known, no
breakdown).

## Method in one paragraph

A policy network scores the candidate actions of each state (launch an operation on a machine, maintain a machine,
wait). It is trained by imitation of a tuned simulated annealing, then by PPO (and a self-imitation stage). At
decision time, the network guides a beam search of width *B* that keeps the *K* best actions of each node; every
partial schedule is completed by a fast heuristic (Numba, ≈ 0.1 ms per completion) and pruned by a lower bound.

## Repository layout

| Path | Content |
|---|---|
| `jssp_pm/` | Core library: instances and wear protocol (`fjsp_instance.py`), event simulator and MDP (`fjsp_sim.py`, `fjsp_env.py`, `fjsp_env3.py`), policy network (`reseaux.py`), PPO (`fjsp_ppo.py`), completion engine and lower bound (`moteur_rapide.py`), beam search (`anticipation.py`), CP-SAT model with maintenance segments (`fjsp_cpsat.py`) |
| `anticiper.py` | Policy-guided (or rule-guided) beam search on benchmark instances |
| `comparer_rl.py` | Policy alone: greedy and best of *N* samples |
| `train_v3.py` | PPO and self-imitation stages |
| `imitation/` | Expert schedules (`experts.jsonl`, 2 000 schedules of simulated annealing) and imitation stage |
| `metaheuristiques/` | Simulated annealing, tabu search, genetic algorithm (same encoding and decoder) |
| `reglage_taguchi/` | Taguchi tuning of the metaheuristics and retained parameters |
| `regles_priorite/` | Dispatching rules |
| `cpsat_article1.py`, `cpsat_sans_depart.py` | CP-SAT with and without warm start (bounds, proven optima, CP-SAT alone) |
| `hybride_rl_mh.py` | Simulated annealing started from the beam-search schedule |
| `externe/` | Scripts used to evaluate the published model of Song et al. (2023) on the same instances |
| `outils/` | Ablation tools, analyses, **independent schedule checker** (`verifier_planning.py`), instance export |
| `experiences_article1/` | Experiment launcher (`lancer.py`, steps E0–E15), statistics, tables and figure scripts, pre-registered protocol (`PROTOCOLE.md`), execution logs (`journaux/`), result tables and figures (`resultats/`) |
| `banque_resultats/` | **Raw results**: one line per run (`resultats.csv`, 23 096 runs) and the complete schedule of every run (`solutions.jsonl.gz`) |
| `models/imitation/` | Trained networks (`cand_ft_best.pt` is the network used in the article) and training logs |
| `Instances/` | Benchmark files (Brandimarte, Hurink edata/rdata/vdata, Kacem) and their wear parameters |
| `resultats_metaheuristiques/`, `resultats_regles/`, `comparaisons/` | Per-campaign summaries |

Internal file names, comments and some method labels are in French. Method labels used in the raw results:
`Recuit simulé` = simulated annealing, `Recherche tabou` = tabu search, `Algorithme génétique` = genetic algorithm,
`RL:imit-ft` = trained policy, `Faisceau:regle` = beam search without network, `RL:aleatoire-g0` = untrained network.
In configurations, `glouton` = greedy, `echantillons` = samples, `faisceau=B,k=K` = beam search *B* × *K*.

## Installation

Tested with Python 3.11 on Windows 11 (CPU only; no GPU is needed).

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m pytest -q tests          # unit tests of the simulator, completion engine and beam search
```

All commands are run from the root of the repository. The schedules of the raw results are shipped compressed;
they are decompressed automatically (≈ 96 MB) the first time `banque_resultats` is imported.

## Instances

The article uses 134 public instances: Brandimarte Mk01–Mk10, Hurink edata, rdata and vdata la01–la40, and Kacem
(four instances). Seven Hurink instances serve for the Taguchi tuning of the metaheuristics and are excluded from
all analyses, which leaves **127 test instances**.

The benchmark files contain no wear parameters. They are added by a reproducible protocol
(`jssp_pm/fjsp_instance.py`, function `attach_wear_v3`, regime A, seed 0): with *u* the mean of the shortest
processing times and *L̄* the mean machine load,
*T_k* = max(round(*f_k* · max(0.5 *L̄*, 3 *u*)), longest eligible operation on *k*), *f_k* ~ U[0.8, 1.2];
*M_k* = max(1, round(*u*)). The resulting values are listed in `Instances/parametres_usure_regime_A.csv`
(one line per machine) and `Instances/parametres_usure_regime_A.json` (one entry per instance, with its role:
test or Taguchi tuning). They can be regenerated with `python -m outils.exporter_instances`.

```python
from metaheuristiques.instances import charger_instances
instances = charger_instances(["Brandimarte", "HurinkLa", "Kacem"], regime="A")   # 134 instances
inst = instances[0]          # inst.P (operations × machines, 0 = not eligible), inst.job_ops, inst.T, inst.M
```

## Reproducing the tables and figures (minutes, from the raw results)

The statistics are recomputed from `banque_resultats/resultats.csv`; no number is copied by hand.

| Article | Command | Output in `experiences_article1/resultats/` |
|---|---|---|
| Main table (gap to SA 50k, bootstrap CI, W/T/L, Wilcoxon–Holm) | `python -m experiences_article1.statistiques --methodes experiences_article1/methodes_principal_sans_hybride.json --nom principal_provisoire` | `principal_provisoire.md/.csv/.tex` |
| Ablations | `python -m experiences_article1.statistiques --methodes experiences_article1/methodes_ablations.json --nom ablations` | `ablations.*` |
| Classical FJSP (no wear) | `python -m experiences_article1.statistiques --methodes experiences_article1/methodes_classique.json --facteur-seuil 1000 --nom classique` | `classique.*` |
| Quality versus budget (schedules evaluated) | `python -m experiences_article1.tests_qualite_budget` then `python -m experiences_article1.figure_qualite_budget` | `tests_qualite_budget.*`, `qualite_budget.pdf` |
| Quality versus wall-clock time (E10, E10b) | `python -m experiences_article1.tests_qualite_temps` and `--sous-ensemble E10b` | `tests_qualite_temps*.md` |
| CP-SAT alone (E9b) | `python -m outils.analyse_e9b` | `e9b.*` |
| Song et al. at equal time (E10s) | `python -m outils.analyse_song_temps` | `e10s_song_temps.*` |
| Value of the maintenance decision (E15) | `python -m experiences_article1.lancer --etape E15` (reads the schedules of the bank) | `e15.*` |
| LaTeX tables of the article | `python -m experiences_article1.tableaux_article` | `tab_*.tex` |
| Method figures | `python -m experiences_article1.figure_<name>` (`modele_cp`, `preuve_completude`, `reseau_couches`, `entrainement`, `faisceau`, …) | `schema_*.pdf/.png` |

## Re-running the experiments

Every experiment is a numbered step of `experiences_article1/lancer.py`; the settings of each step were declared
before the test campaign (see `experiences_article1/PROTOCOLE.md`, in French).

```bash
python -m experiences_article1.lancer --liste                         # steps and estimated cost
python -m experiences_article1.lancer --etape E2 --essai              # print the commands without running them
python -m experiences_article1.lancer --etape E4 E5 --processus 8     # run
```

| Step | Content |
|---|---|
| E0 | Unit tests and machine information |
| E1 | Dispatching rules |
| E2, E3 | Metaheuristics (Taguchi parameters) at 2 000 to 200 000 evaluations, 3–5 seeds |
| E4 | Policy alone: greedy, best of 100 samples × 5 seeds |
| E5, E5b | Policy-guided beam search, grid of *B* × *K* |
| E6 | Ablations: beam without network, untrained network, no pruning, no duplicate removal |
| E7, E8 | Classical FJSP; published model of Song et al. |
| E9, E9b | CP-SAT 600 s (bounds and proven optima); CP-SAT alone at the budgets of the beam search |
| E10, E10b, E10s | Wall-clock time, one process, idle machine (54 and 36 instances; Song et al. at equal time) |
| E11–E14 | Additional training seeds, threshold sensitivity, hybrid (declared, not run for the article; `methodes_principal.json` includes the hybrid of E14) |
| E15 | Value of the maintenance decision, sequences fixed |

**Important.** The scripts never re-run a configuration that is already in the result bank (same instance, method,
configuration and seed). To re-run an existing configuration, either use a new method name (`--nom`) or move
`banque_resultats/resultats.csv` and `solutions.jsonl` aside to start from an empty bank. Wall-clock times are
meaningful only for steps E9b, E10, E10b and E10s, run on a single process on an idle machine.

Example: policy-guided beam search 5 × 4 on the Brandimarte instances, under a new name:

```bash
python anticiper.py --modele models/imitation/cand_ft_best.pt --nom demo --largeur 5 --k 4 --familles Brandimarte --processus 2
```

## Training the network from scratch

```bash
python -m imitation.experts --nombre 2000 --evaluations 50000 --parametres reglage_taguchi/parametres_retenus.json --processus 8   # optional: experts.jsonl is provided
python -m imitation.entrainer --reseau candidats --epoques 20 --seed 0 --out models/imitation/cand
python train_v3.py --init models/imitation/cand_best.pt --lr 1e-4 --ppo_steps 300000 --seed 0 --out models/imitation/cand_ft
```

Training uses generated instances only; no benchmark instance is used for training, validation or model
selection. The hyperparameters are those of `models/imitation/cand_ft_config.json`, `imitation/entrainer.py` and
`train_v3.py`. On a laptop CPU (Intel Core i5-1235U), the imitation stage takes about 6 min per epoch and the PPO
stage about 11 min.

## Evaluating a new method under the same protocol

1. Produce a schedule for each instance as a list of `(machine, start, end, type, job)` (0-based machine and job;
   `type` 1 = operation, 2 = maintenance with `job = -1`).
2. Check it with the independent checker, which verifies eligibility, processing times, precedences, overlaps,
   maintenance durations and the wear condition, and returns the makespan:
3. Record it in the result bank, with its number of evaluated schedules if relevant:

```python
from metaheuristiques.instances import charger_instances
from outils.verifier_planning import verifier
from banque_resultats import banque

for inst in charger_instances(["Brandimarte", "HurinkLa", "Kacem"], regime="A"):
    schedule = my_method(inst)                               # your method
    cmax = verifier(inst, schedule)                          # raises ValueError if infeasible
    n_pm = sum(1 for s in schedule if s[3] == 2)
    banque.ajouter(inst.name, "A", 1.0, "MyMethod", "budget=50000", 0, cmax, n_pm, 0,
                   temps_s=0.0, planning=schedule, evaluations=50000)
```

4. Add `{"label": "My method", "methode": "MyMethod", "config": "budget=50000"}` to a copy of
   `experiences_article1/methodes_principal_sans_hybride.json` and run `experiences_article1.statistiques` with it. The method is
   then compared with all other methods on the 127 test instances, with the same reference (simulated annealing,
   50 000 evaluations, Taguchi parameters), bootstrap confidence intervals, win/tie/loss counts and paired
   Wilcoxon tests with Holm correction. Proven optima and lower bounds come from the CP-SAT runs in the bank.

## Song et al. (2023) baseline

The published model of Song et al. is not included. To re-run steps E8 and E10s, clone their repository
(Apache-2.0) into `externe/fjsp-drl` and install `externe/requirements_song.txt`:

```bash
git clone https://github.com/songwenas12/fjsp-drl externe/fjsp-drl
```

Their results on our instances are provided in `externe/resultats_song.csv` and `externe/resultats_song_temps.csv`.

## Hardware and software used for the article

Intel Core i5-1235U (12 logical cores), Windows 11, Python 3.11.9, PyTorch 2.14.0 (CPU), NumPy 2.4.6, Numba 0.68.0,
SciPy 1.17.1, OR-Tools 9.15.6755. The environment of every run is logged in
`experiences_article1/journaux/executions.jsonl`.

## License and citation

Code released under the MIT License (see `LICENSE`). The benchmark instance files are public benchmarks from the
literature (Brandimarte 1993; Hurink et al. 1994; Kacem et al. 2002) and remain subject to their original terms.
If you use this repository, please cite the article (see `CITATION.cff`).
