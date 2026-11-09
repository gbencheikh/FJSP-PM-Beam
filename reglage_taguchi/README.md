# Taguchi tuning of the metaheuristics

The parameters of the genetic algorithm, the tabu search and the simulated annealing are tuned systematically, with
few runs, by a Taguchi design.

1. Each parameter is tested at three levels.
2. An L9 orthogonal array selects 9 combinations (instead of 81 for four parameters), so that each level of each
   parameter is tested equally often.
3. The runs use eight Hurink instances that are excluded from the test set (edata 3, 13, 23, 33 and rdata 8, 18, 28,
   38; edata 3 is mt20): the parameters are not tuned on the test instances.
4. Measure: makespan divided by that of the MWKR rule with earliest finishing time; "smaller is better"
   signal-to-noise ratio.
5. For each parameter, the level with the best signal-to-noise ratio is kept; an analysis of variance gives the
   influence of each parameter.
6. Confirmation: the retained combination is run again and compared with the default values, which are kept if it does
   not do better.

```bash
python -m reglage_taguchi.taguchi --processus 8
```

The script resumes where it stopped if it is interrupted.

| File | Content |
|---|---|
| `essais.csv` | Every run (method, trial, parameters, instance, seed, makespan) |
| `rapport.md` | L9 arrays, level effects, analysis of variance, confirmation |
| `parametres_retenus.json` | Parameters retained for each method |
