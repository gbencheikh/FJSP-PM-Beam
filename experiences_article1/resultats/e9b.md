# E9b — CP-SAT seul contre le faisceau guidé, budgets appariés (analyse pré-déclarée)

Écart = C_max CP-SAT / C_max faisceau − 1 sur les instances résolues ; échec = défaite de CP-SAT de rang maximal ; Wilcoxon apparié, Holm par groupe (primaire 1 fil ; secondaire 8 fils).

| Analyse | Faisceau | Budget (s) | Fils | Résolues | Échecs | Écart moyen (résolues) | CP-SAT V/E/D | p (Holm) | Scénario |
|---|---|---|---|---|---|---|---|---|---|
| primaire | 5x4 | 1 | 1 | 24 | 103 | +173.88 % nettement | 0/1/126 | 3.5e-25 | A (CP-SAT moins bon) |
| primaire | 10x4 | 2 | 1 | 37 | 90 | +189.70 % nettement | 0/1/126 | 3.6e-24 | A (CP-SAT moins bon) |
| primaire | 50x5 | 9 | 1 | 73 | 54 | +145.27 % nettement | 2/2/123 | 1.3e-22 | A (CP-SAT moins bon) |
| secondaire | 5x4 | 1 | 8 | 25 | 102 | +127.18 % nettement | 0/1/126 | 4.4e-25 | – |
| secondaire | 10x4 | 2 | 8 | 34 | 93 | +113.30 % nettement | 0/1/126 | 2.1e-24 | – |
| secondaire | 50x5 | 9 | 8 | 74 | 53 | +118.63 % nettement | 4/2/121 | 1.6e-22 | – |
