# Rendre l'agent RL plus performant : imitation, hybride, réseau de graphe

Trois pistes, qui se combinent :

| Piste | Idée | Fichiers |
|---|---|---|
| 2. Imitation | l'agent apprend à reproduire les décisions du recuit simulé | `imitation/experts.py`, `imitation/entrainer.py`, `imitation/rejeu.py` |
| 4. Hybride | le planning de l'agent sert de point de départ au recuit / tabou | `hybride_rl_mh.py` ; itération experte dans `imitation/entrainer.py` |
| 3. Réseau de graphe | le réseau voit tout l'atelier (opérations ↔ machines) avant de décider | `jssp_pm/fjsp_graphe.py`, option `--reseau graphe` |

Les deux réseaux (`candidats` = l'ancien, `graphe` = le nouveau) s'utilisent partout de la même
façon. Le type est enregistré dans le fichier du modèle ; les anciens modèles `models/v3/*.pt`
restent lisibles.

**Pas de fuite vers les tests** : l'imitation se fait uniquement sur des instances générées
(même distribution que l'entraînement PPO). Brandimarte et Hurink ne servent qu'à l'évaluation
finale. Le choix du meilleur modèle se fait sur la validation synthétique.

## Recette (Windows, depuis le dossier du projet, environnement activé)

Étape 0 — attendre la fin de Taguchi, pour que le recuit « expert » utilise les bons paramètres.

Étape 1 — plannings experts (environ 1 h avec 10 processus ; reprend si interrompu) :
```
python -m imitation.experts --nombre 2000 --evaluations 50000 --parametres reglage_taguchi/parametres_retenus.json --processus 10
```

Étape 2 — imitation. Les deux réseaux peuvent tourner en même temps (deux fenêtres) :
```
python -m imitation.entrainer --reseau candidats --epoques 20 --out models/imitation/cand
python -m imitation.entrainer --reseau graphe    --epoques 20 --out models/imitation/graphe
```
À suivre dans l'affichage : `accord_expert` (part des décisions identiques à l'expert) et
`validation` (C_max moyen glouton sur la validation ; l'agent PPO actuel est autour de 175).

Étape 3 — itération experte : l'agent propose, le recuit améliore, l'agent imite, on recommence :
```
python -m imitation.entrainer --init models/imitation/cand_best.pt --iterations 10 --nouvelles 200 --evals-expert 20000 --parametres reglage_taguchi/parametres_retenus.json --processus 8 --out models/imitation/cand_it
```
`ecart_agent_vs_recuit` = ce que le recuit gagne encore sur l'agent. S'il diminue, l'agent se
rapproche de la métaheuristique.

Étape 4 — affinage par renforcement (PPO puis auto-imitation), avec un taux d'apprentissage réduit :
```
python train_v3.py --init models/imitation/cand_it_best.pt --lr 1e-4 --ppo_steps 300000 --out models/imitation/cand_ft
```
Pour entraîner le réseau graphe directement par PPO (sans imitation), ce qui est plus lent et
part de beaucoup plus loin :
```
python train_v3.py --reseau graphe --out models/graphe/A_full_s0
```

Étape 5 — évaluation sur les benchmarks (résultats dans la banque) :
```
python comparer_rl.py --modele models/imitation/cand_ft_best.pt --nom imit-cand
python comparer_rl.py --modele models/imitation/cand_ft_best.pt --nom imit-cand --meilleur-de-k 100
python hybride_rl_mh.py --modele models/imitation/cand_ft_best.pt --nom imit-cand --parametres reglage_taguchi/parametres_retenus.json --processus 10
```
L'hybride se compare à la même métaheuristique partie de MWKR+EFT, avec le même budget et les
mêmes paramètres : lancez d'abord `metaheuristiques/comparer.py --evaluations 50000 --parametres ...`.

## Premiers constats (petits tests dans le cloud)
- Le rejeu d'un planning expert redonne exactement son C_max (vérifié ; test automatique).
- Sur 300 plannings experts et 10 passes, l'imitation atteint 191 en validation. L'agent PPO actuel
  est à 175 et le recuit à environ 160 : il faut plus de données, l'itération experte et l'affinage PPO.
  Quelques minutes d'affinage PPO ont déjà ramené le modèle imité de 190 à 184.
- L'agent reproduit bien le **type** de décision (lancer / attendre / maintenance), mais se trompe
  souvent sur **quel** job mettre sur quelle machine (62 % d'accord) : c'est là que le réseau graphe,
  qui voit la concurrence entre jobs et machines, doit aider.
- L'agent actuel `A_full_s0` fait moins bien que MWKR+EFT sur Brandimarte : l'hybride partant de lui
  est donc moins bon que le recuit partant de MWKR+EFT. Il faut un meilleur agent d'abord (étapes 1–4).
