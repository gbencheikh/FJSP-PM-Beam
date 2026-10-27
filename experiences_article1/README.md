# Expériences de l'article 1 (cas déterministe)

Protocole figé : `PROTOCOLE.md` (validé le 6/10/2026). Plan d'ensemble : document de projet
`claude/plan_article1_deterministe.md`.

## Lancer (Windows, depuis le dossier du projet, environnement activé)
```
python -m experiences_article1.lancer --liste
python -m experiences_article1.lancer --etape E0 E1 E4 E6 --processus 8   # contrôles, règles, agent seul, ablations
python -m experiences_article1.lancer --etape E5 E15 --processus 8        # grille du faisceau (sensibilité), valeur de la maintenance
python -m experiences_article1.lancer --etape E7 E8 --processus 8         # FJSP classique, Song et al.
python -m experiences_article1.lancer --etape E9 --processus 8            # CP-SAT, la nuit
python -m experiences_article1.lancer --etape E10 --processus 1           # mesures de temps : machine au repos, secteur branché
python -m experiences_article1.lancer --etape E11 E12 E13 E14 --processus 8
```
**Ordre suivi** (modifié le 6/10/2026) : E2 (fait) → E0, E1, E4, E6 → E5, E15 → E7, E8 → E9 (nuit) → E10 (machine au repos) → E11, E12 → E13, E14. P1 : relance facultative du pilote.
Pourquoi E2 en premier : la validation du protocole autorisait E2 tout de suite (elle ne dépendait d'aucune des deux corrections), alors que E4 et E5 attendaient l'inscription de la règle de sélection du faisceau et des graines de l'agent ; E2 était aussi l'étape la plus longue sans intervention.
**Seules contraintes d'ordre réelles** : E15 après E2 et E5 (elle lit leurs plannings) ; E14 après E5 ; E12 après E11 ; E10 seule, machine au repos ; une seule campagne à la fois (une seule fenêtre). Les autres étapes sont indépendantes et leurs réglages sont déclarés d'avance : leur ordre ne change aucun résultat.
Chaque étape reprend où elle s'est arrêtée. Journaux : `journaux/`.

## Produire les tableaux
```
python -m experiences_article1.statistiques --methodes experiences_article1/methodes_principal.json --nom principal
python -m experiences_article1.statistiques --methodes experiences_article1/methodes_ablations.json --nom ablations
python -m experiences_article1.statistiques --methodes experiences_article1/methodes_classique.json --facteur-seuil 1000 --nom classique
python -m experiences_article1.statistiques --methodes experiences_article1/methodes_graines.json --nom graines
```
Sorties : `resultats/<nom>.md|.csv|.tex|_boxplots.png|.pdf`. Le script signale les instances manquantes.

## Fichiers ajoutés ou modifiés le 6/10/2026 (copies d'origine dans `../archives_code_6oct/`)
- `jssp_pm/anticipation.py`, `anticiper.py` : options `--sans-elagage`, `--sans-doublons` (comportement par défaut inchangé).
- `metaheuristiques/instances.py` : familles `HurinkLa`, `HurinkEdataLa`, `HurinkRdataLa`, `HurinkVdataLa` (la01–la40) ; `Hurink` (ancien sous-ensemble de 20) inchangé.
- `jssp_pm/fjsp_cpsat.py` : option `segments="valide"` (borne inférieure prouvée) ; défaut inchangé.
- `cpsat_article1.py` (nouveau) ; `outils/reseau_aleatoire.py` (nouveau) ; `hybride_rl_mh.py` : option `--depart-banque`.
- `../../externe/evaluer_song.py` : évaluation du modèle publié de Song et al.
- `comparer_rl.py` : option `--processus` (agent seul en parallèle ; résultats identiques à l'exécution en un processus, vérifié sur Brandimarte : 20/20 tirages et 10/10 gloutons identiques). Utilisée par E4, E7, E12.
- `pilote_regime_pannes.py` (pilote go/no-go, verdict dans `resultats/pilote_regime_pannes.md`) ; `e15_maintenance.py` (E15, PROTOCOLE § 3 bis).
