# Experiments

| File or folder | Content |
|---|---|
| `lancer.py` | Launcher: every experiment is a step (`--liste` lists them with their estimated cost; `--essai` prints the commands without running them). Each step resumes where it stopped, writes its log in `journaux/<step>.log` and appends a line to `journaux/executions.jsonl` (date, machine, fingerprint of the code, command, duration, return code) |
| `PROTOCOLE.md` | Protocol log, in French: instances, seeds, budgets, statistics and the decision rules of every campaign, each entry dated before the corresponding computations |
| `statistiques.py` | Comparison tables: gap to the reference, bootstrap confidence intervals, wins/ties/losses, Wilcoxon tests with Holm's correction (`--methodes <file.json> --nom <name>`) |
| `methodes_*.json` | Lists of the methods compared in each table |
| `tests_qualite_budget.py`, `tests_qualite_temps.py` | Tests at equal budgets in evaluations and in wall-clock time |
| `e15_maintenance.py` | Value of the maintenance decisions for fixed sequences |
| `tableaux_article.py`, `tableau_bornes.py`, `tableaux_caie.py` | LaTeX tables of the article |
| `figure_*.py`, `figures_methode.py`, `style_figures.py`, `animation_gantt.py` | Figures and animation |
| `analyse_revision_*.py`, `exploratoire_*.py`, `tableaux_revision*.py`, `tableau_gain_global.py`, `tableau_decisions.py` | Companion analyses (see the main README) |
| `pilote_regime_pannes.py` | Pilot study on letting machines break down, which led to the regime without breakdowns used here |
| `resultats/` | Outputs: tables (`.md`, `.csv`, `.tex`), figures and analysis reports |
| `journaux/` | Logs of all campaigns |

The correspondence between the tables and figures of the article and the scripts is given in the main README.
