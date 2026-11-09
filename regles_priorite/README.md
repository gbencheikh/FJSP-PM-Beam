# Dispatching rules

A rule combines an operation rule (which ready operation to start) with a machine rule (on which machine). Maintenance
follows the same just-in-time rule for all: if the operation does not fit within the remaining wear margin of the
machine, the machine is maintained first.

| Operation rule | Chooses the ready operation… |
|---|---|
| SPT | with the shortest processing time |
| LPT | with the longest processing time |
| MWKR | whose job has the most remaining work |
| LWKR | whose job has the least remaining work |
| MOR | whose job has the most remaining operations |
| LOR | whose job has the fewest remaining operations |
| FIFO | that has been ready the longest |
| WSPT | with the shortest processing time divided by the weight of its job (weight 1 by default) |

| Machine rule | Chooses… |
|---|---|
| EFT | the machine on which the operation finishes earliest (waiting, maintenance if needed, processing) |
| SPTM | the fastest machine for the operation |

```bash
python -m regles_priorite.comparer
python -m regles_priorite.comparer --familles Brandimarte --facteur-seuil 0.7
```

To add a rule, add an entry to `REGLES_OPERATION` in `regles.py`: a function `key(env, job, weight)`, the smallest key
having the highest priority.
