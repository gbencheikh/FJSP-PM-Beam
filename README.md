# Decision-time search for the flexible job shop with preventive maintenance: what does a learned filter add?

Code, data and raw results of the article of the same title (G. Bencheikh, submitted to *Computers & Operations
Research*, November 2026). The repository contains everything needed to **reproduce every table and figure of the
article and of its Supplementary Material** from the raw results, to **re-run any experiment**, and to **evaluate a
new method under the same protocol** (same instances, feasibility check, reference and statistics).

## The question and the answer

A flexible job shop in which every machine accumulates wear while processing: an operation of length *p* may start
on machine *k* only if its wear *c_k* satisfies *c_k + p ≤ T_k*, and a preventive maintenance of length *M_k* resets
the wear to zero. Production and maintenance are scheduled jointly; the objective is the makespan.

The method is a **filtered beam search** (Ow & Morton, 1988). At each node, a *filter* keeps the *K* most promising
actions (launch an operation on a machine, maintain a machine, wait); each kept action is evaluated by completing the
schedule with a priority rule (MWKR, Numba, ≈ 0.1 ms per completion); duplicate states and states whose lower bound
cannot improve on the best schedule are discarded. The filter is interchangeable: either a **policy network** trained
by imitation of a tuned simulated annealing and refined by PPO, or one of **three simple filters** (priority rule,
earliest finish time, lower bound), all other components being identical. The article asks what learning adds.

On 127 public benchmark instances extended with wear parameters:

- the guided beam search is equivalent on average to a tuned simulated annealing within ±1 % while evaluating fewer
  schedules, although not in less time;
- most of this comes from the search: filtering saves six to nine times the evaluations of an unfiltered search, and
  simple filters achieve most of this saving;
- the learned policy adds a small gain (0.2 to 0.5 points of makespan), constant in sign but not significant in every
  campaign; an ablation shows that it comes from **breaking ties** between states of equal completion value (85 % of
  the selections), not from choosing the actions to evaluate.

<p align="center">
  <img src="docs/beam_search_mk01.gif" width="800" alt="Construction of a schedule on Brandimarte Mk01 by the policy-guided beam search">
</p>

*Schedule found by the policy-guided beam search (50 × 5) on Brandimarte Mk01, replayed decision by decision
(black outline: last decision). Right: wear of each machine relative to its threshold, reset by preventive
maintenance. Makespan 51; proven optimum 50.*

## Repository layout

| Path | Content |
|---|---|
| `jssp_pm/` | Core library: instances and wear protocol (`fjsp_instance.py`), event simulator and MDP (`fjsp_sim.py`, `fjsp_env3.py`), policy network (`reseaux.py`), PPO (`fjsp_ppo.py`), completion engine and lower bound (`moteur_rapide.py`), beam search with interchangeable filter and tie-breaking (`anticipation.py`), CP-SAT model with maintenance segments (`fjsp_cpsat.py`) |
| `anticiper.py` | Beam search on benchmark instances: `--modele` (network), `--filtre regle\|fin\|borne` (simple filters), `--departage ordre\|rang` (tie-breaking ablation) |
| `comparer_rl.py` | Policy alone: greedy and best of *N* samples |
| `train_v3.py` | PPO and self-imitation stages |
| `imitation/` | Expert schedules (`experts.jsonl`, 2 000 schedules of simulated annealing), imitation stage (`entrainer.py`), filter trained for the search (`filtre_appris.py`, experiment D5), earlier attempts mentioned in the article (`eleve_recuit.py`, `auto_amelioration.py`) |
| `metaheuristiques/` | Simulated annealing, tabu search, genetic algorithm (one encoding; semi-active decoder, active decoder `decoder_actif` for experiment A1) |
| `reglage_taguchi/`, `regles_priorite/` | Taguchi tuning of the metaheuristics; dispatching rules |
| `cpsat_article1.py`, `cpsat_sans_depart.py` | CP-SAT with and without warm start (bounds, proven optima, CP-SAT alone) |
| `externe/` | Evaluation of the published model of Song et al. (2023) on our instances, and its results |
| `outils/` | **Independent schedule checker** (`verifier_planning.py`), analyses, time measurements, instance export |
| `experiences_article1/` | Experiment launcher (`lancer.py`), analysis and table scripts, protocol log (`PROTOCOLE.md`), execution logs (`journaux/`), result tables and figures (`resultats/`) |
| `banque_resultats/` | **Raw results**: one line per run and the complete schedule of every run (see below) |
| `models/` | Trained networks (see below) |
| `Instances/` | Benchmark files and their wear parameters |

Internal file names, comments and the protocol log are in French. Method labels in the raw results:
`Recuit simulé` = simulated annealing, `Recherche tabou` = tabu search, `Algorithme génétique` = genetic algorithm,
`RL:imit-ft` = trained policy (final network), `Faisceau:regle` = beam search without filter,
`RL:aleatoire-g0` = untrained network. In configurations: `glouton` = greedy, `echantillons` = samples,
`faisceau=B,k=K` = beam search *B* × *K*, `filtre=regle|fin|borne` = simple filter (priority rule, earliest finish,
lower bound), `departage=ordre|rang` = tie-breaking by order of generation or by cumulative rank.

### Raw results

| File | Content |
|---|---|
| `banque_resultats/resultats.csv` + `solutions.jsonl.gz` | Protocol of the article (35 418 runs) |
| `resultats_mu3.csv` + `solutions_mu3.jsonl.gz` | Longer maintenances, μ = 3 (R4) |
| `resultats_TkLk.csv` + `solutions_TkLk.jsonl.gz` | Classical problem with T_k = L_k (D4) |
| `resultats_phi1.csv`, `resultats_phi2.csv` + schedules | Two other draws of the threshold factors φ_k (B2) |

The separate banks are selected by environment variables (`FJSP_MU=3`, `FJSP_TK_LK=1`, `FJSP_GRAINE_PHI=1|2`), so
that runs of different protocols are never mixed. Schedules are decompressed automatically the first time
`banque_resultats` is imported.

### Networks

| File | Role in the article |
|---|---|
| `models/imitation/cand_ft_best.pt` | **Final network** (seed 0, after PPO), used in all main results |
| `models/imitation/cand_best.pt` | Imitation alone (training stages) |
| `models/imitation/cand_ft_g1_best.pt`, `cand_ft_g2_best.pt` | Training seeds 1 and 2 (after self-imitation); `cand_g*_best.pt` and `cand_ft_g*_ppo_best.pt` are the intermediate stages |
| `models/aleatoire/cand_aleatoire_g0.pt` | Untrained network (ablation) |
| `models/filtre/filtre_best.pt` | Filter trained for the search (D5); no epoch improved the validation, so the final network was retained |

## Installation

Tested with Python 3.11 on Windows 11 (CPU only; no GPU is needed).

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m pytest -q tests          # unit tests of the simulator, completion engine and beam search
```

All commands are run from the root of the repository.

## Instances

The article uses 134 public instances: Brandimarte Mk01–Mk10, Hurink edata, rdata and vdata la01–la40, and Kacem
(four instances). Seven Hurink instances serve for the Taguchi tuning of the metaheuristics and are excluded from
all analyses, which leaves **127 test instances**.

The benchmark files contain no wear parameters. They are added by a reproducible protocol
(`jssp_pm/fjsp_instance.py`, function `attach_wear_v3`, regime A, seed 0): with *u* the mean of the shortest
processing times and *L̄* the mean machine load,
*T_k* = max(round(*φ_k* · max(0.5 *L̄*, 3 *u*)), longest eligible operation on *k*), *φ_k* ~ U[0.8, 1.2];
*M_k* = max(1, round(*u*)). The values are listed in `Instances/parametres_usure_regime_A.csv` and
`Instances/parametres_usure_regime_A.json`, and can be regenerated with `python -m outils.exporter_instances`.

```python
from metaheuristiques.instances import charger_instances
instances = charger_instances(["Brandimarte", "HurinkLa", "Kacem"], regime="A")   # 134 instances
inst = instances[0]          # inst.P (operations × machines, 0 = not eligible), inst.job_ops, inst.T, inst.M
```

## Reproducing the tables and figures (minutes, from the raw results)

No number is copied by hand: every table is produced by a script from the raw results or from the reports of the
analysis scripts. Outputs go to `experiences_article1/resultats/`. Commands are `python -m experiences_article1.<script>`
unless stated otherwise.

| Article | Script | Output |
|---|---|---|
| Table 3 (families) and Table 15 (classical problem, T_k = L_k) | `tableaux_revision3` | `tab_familles.tex`, `tab_classique_TkLk.tex` |
| Table 4 (main comparison) | `statistiques --methodes experiences_article1/methodes_principal_sans_hybride.json --nom principal_provisoire` | `principal_provisoire.*` |
| Table 5 (equal budget in evaluations), Table 12 (equal time), Table 13 (maintenance placement), Table 14 (Song et al.) | `tableaux_article` | `tab_budget.tex`, `tab_temps.tex`, `tab_maintenance.tex`, `tab_song.tex` |
| Table 6 (lower bounds, proven optima, best known) | `tableau_bornes` | `tab_bornes.tex` |
| Table 7 (gain of the learned filter, pooled tests) | `tableau_gain_global` | `tab_gain_global.tex` |
| Table 8 (tie-breaking ablation) and Table 11 (draws of φ_k) | `tableaux_revision4` | `tab_departage.tex`, `tab_tirages_phi.tex` |
| Tables 9 and 10 (filters, declared tests) | `tableaux_revision` | `tab_filtres.tex`, `tab_tests_filtres.tex` |
| Table 15 (classical problem, ×1000) | `statistiques --methodes experiences_article1/methodes_classique.json --facteur-seuil 1000 --nom classique` | `classique.*` |
| Figure 7 (quality versus evaluations) | `tests_qualite_budget` then `figure_qualite_budget` | `tests_qualite_budget.*`, `qualite_budget.pdf` |
| Figure 6 (schedules on Mk01) | `figure_gantt_resultats` | `gantt_resultats_BrandimarteMk1.pdf` |
| Figures 1–5, 8, 9 (models, method, proofs) | `figure_modele_cp`, `figures_methode`, `figure_reseau_couches`, `figure_faisceau`, `figure_segments`, `figure_preuve_completude` | `schema_*.pdf` |
| Supplementary Table S3 (time of the filters) | `tableaux_revision3` | `tab_temps_filtres.tex` |
| Supplementary Table S4 (ablations) | `statistiques --methodes experiences_article1/methodes_ablations.json --nom ablations` | `ablations.*` |
| Supplementary Table S5 (CP-SAT at equal time) | `tableaux_article` | `tab_cpsat.tex` |
| Supplementary Table S6 (declared rules, outcomes, decisions) | `tableau_decisions` (checks every value against the reports) | `tab_decisions.tex` |
| Supplementary Figure S1 (training) | `figure_entrainement` | `schema_entrainement.pdf` |

The analysis reports read by the table scripts are produced by `analyse_revision_<campaign>` (R1R2, R3, R4, D1D3D4,
D2, D5, A1, B1, B2, B3) → `resultats/revision_<campaign>.md`; the intermediate analyses of the initial campaigns by
`tests_qualite_budget`, `tests_qualite_temps` (`--sous-ensemble E10b`, `union`), `outils.analyse_e9b`,
`outils.analyse_song_temps` and step E15 of `lancer`. Analyses that were computed after the corresponding campaign,
and are reported as such in the article, are in `exploratoire_N1_filtres.py` and `exploratoire_relecteur2.py`.

## Re-running the experiments

Every experiment is a step of `experiences_article1/lancer.py`. The settings and decision rules of each step were
written in `experiences_article1/PROTOCOLE.md` (in French) **before** the corresponding computations; each entry
of the log is dated.

```bash
python -m experiences_article1.lancer --liste                         # steps and estimated cost
python -m experiences_article1.lancer --etape R1 --essai              # print the commands without running them
python -m experiences_article1.lancer --etape D1 D3 --processus 8     # run
```

| Step | Content |
|---|---|
| E0–E15 | Initial campaigns: unit tests, dispatching rules, metaheuristics at 2 000 to 200 000 evaluations, policy alone, beam grid, ablations, classical problem, Song et al., CP-SAT, wall-clock time (one process), training seeds, value of maintenance decisions |
| R1 | Beam search with the three simple filters, same settings as the network |
| R2, R3 | Imitation alone; training seeds 1 and 2 |
| R4 | Longer maintenances (μ = 3) |
| D1 | Simple filters at equal budget in evaluations |
| D2 | Computing time of the filters (one process, idle machine) and cost of the expert schedules |
| D3 | Threshold factors 0.7 and 1.5 |
| D4 | Classical problem with T_k = L_k |
| D5 | Filter trained for the search |
| A1 | Active decoder for simulated annealing and tabu search |
| B1 | Tie-breaking ablation |
| B2, B2b | Two other draws of the factors φ_k |
| B3 | Song et al. at equal time on Hurink edata and rdata |

**Important.** The scripts never re-run a configuration that is already in the result bank (same instance, method,
configuration and seed). To re-run an existing configuration, use a new method name (`--nom`) or move the bank files
aside to start from an empty bank. Wall-clock times are meaningful only for the steps run on a single process on an
idle machine (E9b, E10, E10b, E10s, D2, B3).

Example: beam search 5 × 4 guided by the network, then by the priority-rule filter, on the Brandimarte instances:

```bash
python anticiper.py --modele models/imitation/cand_ft_best.pt --nom demo --largeur 5 --k 4 --familles Brandimarte --processus 2
python anticiper.py --filtre regle --nom demo-regle --largeur 5 --k 4 --familles Brandimarte --processus 2
```

## Training the network from scratch

```bash
python -m imitation.experts --nombre 2000 --evaluations 50000 --parametres reglage_taguchi/parametres_retenus.json --processus 8   # optional: experts.jsonl is provided
python -m imitation.entrainer --reseau candidats --epoques 20 --seed 0 --out models/imitation/cand
python train_v3.py --init models/imitation/cand_best.pt --lr 1e-4 --ppo_steps 300000 --seed 0 --out models/imitation/cand_ft
```

Training uses generated instances only; no benchmark instance is used for training, validation or model selection.
Hyperparameters: `models/imitation/cand_ft_config.json`, `imitation/entrainer.py`, `train_v3.py` (Supplementary
Table S2). On a laptop CPU (Intel Core i5-1235U), the imitation stage takes about 6 min per epoch and the PPO stage
about 11 min. Computing the 2 000 expert schedules takes about 2.4 h of CPU (`outils/temps_experts.py`).

## Evaluating a new method under the same protocol

1. Produce a schedule for each instance as a list of `(machine, start, end, type, job)` (0-based machine and job;
   `type` 1 = operation, 2 = maintenance with `job = -1`).
2. Check it with the independent checker, which verifies eligibility, processing times, precedences, overlaps,
   maintenance durations and the wear condition, and returns the makespan.
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
   `experiences_article1/methodes_principal_sans_hybride.json` and run `experiences_article1.statistiques` with it.
   The method is then compared with all other methods on the 127 test instances, with the same reference (simulated
   annealing, 50 000 evaluations, Taguchi parameters), bootstrap confidence intervals, win/tie/loss counts and paired
   Wilcoxon tests with Holm's correction. Proven optima and lower bounds come from the CP-SAT runs in the bank.

## Song et al. (2023) baseline

The published model of Song et al. is not included. To re-run steps E8, E10s and B3, clone their repository
(Apache-2.0) into `externe/fjsp-drl` and install `externe/requirements_song.txt`:

```bash
git clone https://github.com/songwenas12/fjsp-drl externe/fjsp-drl
```

Their results on our instances are provided in `externe/resultats_song.csv`, `externe/resultats_song_temps.csv` and
`externe/resultats_song_temps_E10b.csv`.

## Hardware and software used for the article

Intel Core i5-1235U (12 logical cores), Windows 11, Python 3.11.9, PyTorch 2.14.0 (CPU), NumPy 2.4.6, Numba 0.68.0,
SciPy 1.17.1, OR-Tools 9.15.6755. The environment of every run is logged in
`experiences_article1/journaux/executions.jsonl`.

## License and citation

Code released under the MIT License (see `LICENSE`). The benchmark instance files are public benchmarks from the
literature (Brandimarte 1993; Hurink et al. 1994; Kacem et al. 2002) and remain subject to their original terms.
If you use this repository, please cite the article (see `CITATION.cff`).
