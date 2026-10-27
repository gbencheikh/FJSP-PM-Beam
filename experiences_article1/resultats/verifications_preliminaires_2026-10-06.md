# Vérifications préliminaires — 6 octobre 2026 (cloud, 2 cœurs, PyTorch 2.14 CPU)

Résultats indicatifs, hors banque (machine différente). Ils ne remplacent pas les étapes E6 et E8.

## 1. Reproduction de Song et al. (2023), modèle publié save_10_5.pt, Brandimarte Mk01–10
| Mode | Moyenne C_max (nous) | Tableau V de l'article |
|---|---|---|
| Glouton | 201,0 | 201,00 |
| 100 tirages (graine 0) | 190,5 | 190,40 |
Par instance (glouton / 100 tirages) : Mk01 43/42, Mk02 38/35, Mk03 204/204, Mk04 81/69, Mk05 192/183,
Mk06 99/91, Mk07 221/191, Mk08 529/523, Mk09 339/319, Mk10 264/248.
→ le correctif d'une ligne de next_time (evaluer_song.py) est fidèle.

## 2. Ablation « faisceau sans réseau » (régime A, s = 1), Brandimarte
C_max (B = 5 / 20 / 50, toutes les actions évaluées par le moteur, sans réseau) :
Mk1 51/51/51, Mk2 33/33/33, Mk3 219/219/219, Mk4 80/79/79, Mk5 190/190/188, Mk6 74/74/75,
Mk7 161/162/160, Mk8 567/567/567, Mk9 327/328/329, Mk10 243/241/242.
Écart moyen au recuit Taguchi (banque) : sans réseau B=5 −0,36 %, B=50 −0,50 % ;
avec réseau 5×4 −1,00 %, 50×5 −0,98 %.
Temps cloud (B=5) : 0,2 à 3,5 s par instance, nettement moins que l'agent 5×4 (inférence du réseau).
→ la recherche fait l'essentiel du gain ; le réseau ajoute ≈ 0,5 point ; le faisceau sans réseau plafonne.
