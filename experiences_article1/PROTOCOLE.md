# Protocole expérimental figé — article 1 (cas déterministe)

Version 1, 6 octobre 2026. **Validé par Ghita le 6 octobre 2026** (après les corrections datées du journal). Toute modification ultérieure est
datée ici, avec sa raison, et les résultats concernés sont recalculés.

## 1. Problème et régime
- **La maintenance préventive est au cœur de l'article 1.** Chaque machine k s'use en travaillant (usure
  cumulée c_k) ; une maintenance de durée M_k remet l'usure à zéro ; l'usure ne doit jamais dépasser le seuil
  T_k, connu. L'agent décide conjointement **quel job, sur quelle machine, et quand maintenir** (actions :
  lancer, maintenir, attendre). Objectif : C_max, maintenances comprises. Le compromis est réel : maintenir
  trop tôt multiplie les arrêts, trop tard bloque des opérations ; une maintenance bien placée tombe dans un
  temps mort et ne coûte rien.
- **Régime A** : un filtre de sécurité interdit de lancer une opération qui ferait dépasser T_k. Il n'y a donc
  **aucune panne** (pas de réparation R_k), et β, qui ne pénalise que les pannes, n'intervient pas.
  Les pannes, la réparation et β relèvent de l'article 1b (seuils inconnus).
- Extension des benchmarks : `attach_wear_v3` (jssp_pm/fjsp_instance.py), τ = 0,5, κ = 3, μ = 1, ρ = 6,
  f_k ~ U[0,8 ; 1,2] (graine publiée), facteur de seuil s = 1. Options machine d'origine conservées.
- **Expérience de contrôle seulement** (E7) : FJSP classique, obtenu avec s = 1000 (seuils si grands que la
  maintenance ne sert plus). Elle sert à (i) se comparer à Song et al., dont le problème n'a pas de maintenance,
  et (ii) vérifier que notre méthode reste bonne quand la maintenance disparaît. Une maintenance inutile hors
  chemin critique peut y apparaître sans changer le C_max. Ce n'est pas le cas d'étude de l'article.
- Pannes permises avec seuils connus : testé par un pilote go/no-go le 6/10/2026 (`resultats/pilote_regime_pannes.md`).
  Verdict NO-GO, confirmé avec 5 graines au cas le plus favorable (R = u) : à β = 0, la panne ne paie
  significativement que sur 1 instance sur 5 (Mk10, −1,3 %, p = 0,012 après Bonferroni) — cas limite où une panne
  n'est qu'une maintenance gratuite placée exactement au seuil, au milieu d'une opération (une préemption) ;
  dès β = 0,5, la prévention domine sur 5/5 (meilleur θ > 1 : +0,5 à +41 %). Hors article 1 ; présenté en
  sous-section ou annexe comme justification du régime A et transition vers 1b.

## 2. Instances d'évaluation (127 = 134 − 7)
**Correction du 6/10/2026** : 7 des 8 instances de réglage Taguchi des métaheuristiques (Hurink edata 13, 23, 33 et
rdata 8, 18, 28, 38 ; `reglage_taguchi/taguchi.py`) font partie de la01–la40. Elles sont **exclues de tous les
tableaux de test** (exclusion par défaut dans `statistiques.py`, option `--inclure-reglage` pour les voir à part) ;
les campagnes les calculent quand même (coût négligeable), ce qui n'a aucun effet sur les autres résultats.
Test : 127 instances = Brandimarte 10 + Hurink edata 37 + rdata 36 + vdata 40 + Kacem 4.
| Famille | Fichiers | Nombre |
|---|---|---|
| Brandimarte | Mk01–Mk10 | 10 |
| Hurink edata, rdata, vdata | la01–la40 = fichiers 4 à 43 (`HURINK_LA`) | 120 |
| Kacem | 1–4 | 4 |
Correspondance fichier par fichier avec les instances de Song et al. : `externe/correspondance_instances_song.csv`
(129 sur 130 identiques ; Mk06 : en-tête 10 machines chez nous, 15 chez eux, données identiques — les 5 machines
supplémentaires ne sont éligibles pour aucune opération ; sans effet sur le C_max, mais f_k et L̄ du protocole
d'usure sont calculés sur 10 machines).
Entraînement : uniquement des instances générées (graines disjointes) ; aucun benchmark ne sert au réglage.

## 3. Méthodes et budgets
- Règles de priorité : 6 règles de job × 2 règles de machine, maintenance juste avant dépassement.
- Métaheuristiques (AG, tabou, recuit) : paramètres Taguchi (`reglage_taguchi/parametres_retenus.json`),
  départ MWKR+EFT, **5 graines** (0–4).
- Budget principal = **plannings évalués** (indépendant de la machine) : 50 000 ; courbe à
  2 000 / 5 000 / 10 000 / 20 000 / 50 000 / 100 000 / 200 000 (recuit et tabou, 3 graines).
- **Faisceau (avec ou sans réseau) — critère de tri** : chaque action candidate est jugée par la valeur du planning
  que le moteur rapide obtient en la jouant puis en complétant avec la règle MWKR + EFT + maintenance juste à
  temps (heuristique écrite à la main) ; on garde les B meilleures (C_max complété croissant). Avec réseau : le
  réseau ne retient que ses K actions les plus probables par piste et départage les égalités par la
  log-probabilité cumulée. Sans réseau : toutes les actions sont évaluées, égalités départagées par l'ordre des
  candidats (arbitraire mais déterministe). Le réseau joue donc deux rôles mesurables : filtre de candidats (K)
  et départage. Ce critère est écrit tel quel dans l'article.
- **Réglages principaux du faisceau PRÉ-DÉCLARÉS : 5 × 4 et 50 × 5.** Origine, dite telle quelle dans l'article :
  d'après la banque de résultats, ce sont les deux seuls réglages essayés en phase 1 (bilan du 1/10/2026 : un réglage
  « rapide » et un réglage « long », évalués sur 30 benchmarks qui font partie des 134 instances calculées) ; ils n'ont
  été choisis parmi aucune grille (confirmé par Ghita le 6/10/2026 : aucun autre réglage essayé, ni dans la banque ni en dehors). Ce sont les seuls réglages du tableau principal. La grille E5 complète
  (11 réglages) est une **figure de sensibilité, pas un menu** : aucun réglage ne peut être promu après coup au vu
  des résultats sur les instances de test. Même règle pour les ablations (E6) : chaque variante est rapportée à ses
  réglages déclarés ici.
- **Hasard et graines de l'agent** :
  - glouton et faisceau : **déterministes à réseau fixé** (vérifié : deux exécutions du faisceau 5 × 4 sur Mk1–Mk3
    donnent des plannings identiques, au segment près) ; une exécution par réseau ;
  - tirages : **100 plannings tous échantillonnés** selon la politique (sans le glouton), générateur
    `numpy.random.default_rng(g)`, **graines g = 0 à 4** (5 répétitions), valeur d'une instance = moyenne sur les
    5 graines du meilleur des 100 (config « echantillons=100 ») ; symétrique de Song et al. : 100 tirages par graine,
    `torch.manual_seed(g)`, g = 0 à 4 ; leur glouton est déterministe (1 exécution) comme le nôtre ;
  - l'ancienne configuration « meilleur_de_k=100 » (glouton + 99 tirages, graine 0) reste dans la banque comme
    historique ; elle n'est pas utilisée dans l'article ;
  - variance d'entraînement : 3 réseaux (graines d'entraînement 0, 1, 2 ; E11–E12).
- **Nombre de graines** : 5 pour les métaheuristiques du tableau principal (E2), 3 pour la courbe en évaluations
  (E3) et la sensibilité (E13). Les valeurs du point 50 000 de la courbe et du tableau principal peuvent donc
  différer légèrement ; l'article le dit explicitement.
- Agent : réseau `models/imitation/cand_ft_best.pt` (graine d'entraînement 0) + graines 1 et 2 (E11) ;
  glouton, meilleur de 100 tirages, faisceau B × K ; le nombre de plannings complétés par le moteur rapide est
  enregistré (comparable aux évaluations des métaheuristiques).
- **Temps** : mesuré à part, sur un seul processus, machine au repos, sous-ensemble de 54 instances
  (Brandimarte, Kacem, Hurink vdata la01–40), recuit et tabou à 1 / 2 / 5 / 10 / 20 / 40 s (E10).
  Les temps des campagnes parallèles ne sont jamais rapportés comme temps de calcul.
  Raison : processeur hybride (cœurs P et E, i5-1235U) et charge des exécutions parallèles ; c'est la cause
  probable de l'anomalie « recuit 10 s moins bon que 5 s » de `comparaisons/comparaison_seuil1.md`.
- CP-SAT : 600 s par instance, modèle à segments avec S_k = min(nb d'options, 2·⌈charge/T_k⌉ + 1)
  (borne inférieure prouvée valide, voir `jssp_pm/fjsp_cpsat.py`), démarrage à chaud depuis le meilleur
  planning de la banque. **Borne inférieure rapportée = max(borne CP-SAT régime A, borne CP-SAT du FJSP
  classique, borne du moteur rapide à la racine, borne inférieure FJSPLib).** La borne FJSPLib du FJSP classique
  est valide pour le régime A : mêmes options machine (s = 1, aucune option retirée), la maintenance ne fait
  qu'ajouter des contraintes. Jamais « optimal » sauf statut OPTIMAL.
- Song et al. (2023) : modèle publié `save_10_5.pt` (le meilleur sur les benchmarks d'après leur tableau V),
  glouton (déterministe) et 100 tirages × 5 graines ; FJSP classique uniquement.
  Contrôle de fidélité : moyenne glouton sur Mk01–10 = 201,00 = leur tableau V (vérifié le 6/10/2026).

## 3 bis. E15 — valeur de la décision de maintenance (`experiences_article1/e15_maintenance.py`)
- Question : à ordre des opérations et affectation FIGÉS, combien vaut le seul placement des maintenances ?
- Sources de séquences : planning de la banque du recuit Taguchi 50 000 (graine 0) et de l'agent 5×4, calculé
  sur les 134 instances, analysé sur les 127 de test (§ 2 ; après E2 et E5) ; les maintenances sont retirées, séquences machines et affectation gardées.
- Recalcul semi-actif ; une maintenance placée avant une opération commence à la fin de l'opération précédente ;
  une maintenance obligatoire est ajoutée si l'opération ne tient pas dans la marge (tout reste faisable).
- Politiques : au plus tard (juste à temps, référence) ; au plus tôt (même nombre minimal, positions au plus tôt) ;
  systématique (avant chaque opération) ; source (positions choisies par le recuit ou l'agent) ;
  **aléatoire** (politique nulle : chaque position facultative avec probabilité 1/2, 100 tirages, graines 0–99 ;
  moyenne et meilleur des tirages) ; **recuit sur le placement seul** (vecteur binaire des positions
  facultatives, voisin = bascule d'une position, objectif C_max, 20 000 évaluations, graines 0–4, départ au plus
  tard ; T0 : dégradation moyenne acceptée avec p = 0,05, fin à 10⁻³ T0) — borne pratique de E15.
- Mesures : C_max, nombre de maintenances, nombre et part de maintenances dans un temps mort (la maintenance ne
  retarde pas l'opération suivante : le job de celle-ci n'est prêt qu'après la fin de la maintenance), nombre de
  maintenances qui retardent l'opération suivante, usure moyenne c/T au moment de la maintenance.
- Statistiques : unité = instance ; écart à « au plus tard » ; IC bootstrap ; Wilcoxon apparié + Holm ; V/E/D.
- Mécanisme : par instance, Spearman entre chaque variable explicative et C_max, calculé **sur les placements de
  cette instance seulement** : 109 placements par instance (100 tirages aléatoires + 4 politiques + 5 graines du
  recuit), le nombre de positions facultatives variant d'une instance à l'autre ; ce n'est pas un échantillon global ;
  médiane des corrélations, nombre d'instances de signe attendu et p < 0,05 ; nuage groupé en C_max normalisé.
- Contrôle : le redécodage du planning source doit redonner un C_max ≤ celui de la banque (sinon instance signalée).


## 3 ter. E9b — CP-SAT seul, sans démarrage à chaud (déclaré le 9/10/2026, précisé le même jour avec Ghita, AVANT tout calcul)
Script : `cpsat_sans_depart.py` ; analyse : `outils/analyse_e9b.py` (écrite avant les données).
- **Méthode** : même modèle que E9 (segments « valide »), aucun planning de départ, aucune borne supérieure imposée,
  seconde phase (réduction des maintenances) désactivée, graine 0. Un seul processus, machine au repos ; temps =
  construction du modèle + résolution. **E9b passe APRÈS E10.**
- **Budgets appariés (comparaison qui porte la décision)** : temps murs moyens du faisceau guidé 5 × 4, 10 × 4 et
  50 × 5 mesurés par E10 sur la machine de référence, arrondis à la seconde, écrits dans
  `experiences_article1/budgets_e9b.json` à la sortie d'E10 puis figés. Grille 1/2/5/10/20/40 s : courbe
  qualité / temps seulement (mêmes budgets que recuit et tabou en E10).
- **Analyse primaire (ressources égales, porte la thèse)** : CP-SAT 1 fil au budget apparié contre le faisceau
  correspondant, 127 instances, Wilcoxon apparié par instance, Holm sur les 3 tests.
- **Analyse secondaire (observation complémentaire, jamais mêlée à la primaire)** : 8 fils aux mêmes budgets
  appariés (et 5 / 40 s), Holm séparé ; formulation : « avec 8 fois le calcul par cœur, CP-SAT … ».
- **Échecs** : instance sans solution dans le budget = DÉFAITE de CP-SAT, de rang maximal dans le Wilcoxon ;
  nombre d'échecs rapporté par budget ; écart moyen calculé sur les instances résolues (n indiqué). Justification :
  c'est l'argument du régime rapide (le faisceau renvoie toujours un planning).
- **Règle d'interprétation, par test primaire** :
  A = CP-SAT significativement MOINS bon (p Holm < 0,05) → régime rapide renforcé : « à ressources égales et en
  quelques secondes, la recherche guidée bat recuit, tabou et un solveur CP générique », avec la réserve sur le
  modèle CP ;
  B = non significatif → « à ressources égales, CP-SAT seul est statistiquement indistinguable du faisceau » ; la
  thèse se limite aux métaheuristiques pour la qualité, et à la robustesse (échecs) pour CP-SAT ;
  C = CP-SAT significativement MEILLEUR → thèse limitée explicitement aux métaheuristiques ; écrire que CP-SAT fait
  mieux à temps égal.
  Descriptif seulement : « nettement » si |écart moyen| ≥ 2 points.
- **Second modèle CP (intervalles optionnels)** : option déclenchée, pas engagement (≈ 1–2 jours + une nuit). Écart
  très grand en A → limite dite en une phrase ; écart modéré (ou B) → contre-expérience attendue, à faire.


## 3 quinquies. E10b — mesures de temps sur Hurink edata / rdata (déclaré le 14/10/2026, avec Ghita, AVANT tout calcul)
But : vérifier si le résultat en temps de E10 (faisceau significativement meilleur que recuit et tabou de 1 à 40 s)
tient hors du sous-ensemble de E10, que l'on sait favorable au faisceau.
- **Instances** : une instance sur deux de Hurink edata et rdata la01–la40 (fichiers d'indice pair 4, 6, …, 42, soit
  la01, la03, …, la39), instances de réglage Taguchi exclues (rdata 8, 18, 28, 38) : 20 edata + 16 rdata = **36**.
  Choix mécanique fixé avant les données (familles `HurinkEdataLaPair`, `HurinkRdataLaPair` de `metaheuristiques/instances.py`).
- **Méthodes et réglages : identiques à E10** — recuit et tabou Taguchi en mode mono (1, 2, 5, 10, 20, 40 s ; graines
  0–2) ; faisceau guidé `imit-ft-mono` 1×4, 5×4, 10×4, 20×4, 50×5. Faisceaux à règle NON repris (ablation, hors test).
  Un seul processus, machine au repos, même machine que E10. Commande : `python -m experiences_article1.lancer --etape E10b`.
- **Analyse (même règle que E10, `tests_qualite_temps.py --sous-ensemble E10b`)** : par budget b de la métaheuristique,
  faisceau guidé au plus grand temps moyen ≤ b ; Wilcoxon apparié par instance ; Holm sur l'ensemble des tests ;
  écarts au recuit 50 000 évaluations. **Primaire = les 36 instances de E10b seules.** Union E10 + E10b (90 instances)
  = descriptif seulement (`--sous-ensemble union`), jamais utilisé pour décider.
- **Règles d'interprétation (fixées maintenant)** :
  * faisceau significativement meilleur (p Holm < 0,05) à TOUS les budgets sur E10b → on peut écrire « en temps, le
    faisceau est meilleur de 1 à 40 s » sur les deux sous-ensembles (90 des 127 instances), en le disant ainsi ;
  * sinon → la phrase en temps est restreinte, budget par budget, aux points où le test est significatif sur CHACUN des
    deux sous-ensembles ; un point significatif dans l'autre sens est rapporté tel quel (« le recuit est meilleur à b s
    sur edata / rdata ») ; les points non significatifs sont dits « indistinguables ».
  * Le temps moyen du faisceau sur E10b est rapporté (il peut différer de E10 ; l'appariement se fait sur E10b).

## 3 quater. E10s — Song et al. au même temps mur que le faisceau, sur un cœur (déclaré le 9/10/2026, avant tout calcul)
Scripts : `outils/budgets_song.py`, `../../externe/evaluer_song_temps.py`, analyse `outils/analyse_song_temps.py`.
- Terrain : FJSP classique (s = 1000), sous-ensemble de temps sans Kacem (absent chez Song) : Brandimarte + Hurink
  vdata = 50 instances. Les deux méthodes sur UN cœur (1 fil PyTorch pour Song), un processus, machine au repos.
- Faisceau guidé 5 × 4, 10 × 4, 50 × 5 mesuré par E10 en FJSP classique ; **budget de Song = temps mur du faisceau
  sur la même instance**. Song tire des lots de 20 plannings (leur mode échantillonnage, modèle publié 10 × 5), garde
  le meilleur, s'arrête au premier lot qui fait dépasser le budget (au moins un lot) ; dépassement rapporté (il avantage
  Song). Graines 0–2 ; échauffement PyTorch non chronométré.
- Analyse : unité = instance (Song : moyenne des graines) ; Wilcoxon apparié, Holm sur 3 tests. A = faisceau
  significativement meilleur ; B = non significatif ; C = Song significativement meilleur. « Nettement » si
  |écart| ≥ 2 points (descriptif). Formulation : « au même temps de calcul sur un cœur de processeur » ; jamais
  « Song nécessite du calcul parallèle » (leur code tourne en lots, conçu pour GPU : limite à dire — sur GPU, les
  deux méthodes seraient plus rapides et le rapport pourrait changer ; non testé, pas de GPU sur la machine).

## 4. Statistiques (`experiences_article1/statistiques.py`)
- Unité : **l'instance** ; valeur = moyenne des graines.
- Mesure principale : écart relatif au recuit Taguchi 50 000 évaluations (même instance, même régime).
  Mesures secondaires : écart à la borne inférieure, au meilleur connu de la littérature (FJSP classique).
- IC 95 % de l'écart moyen : bootstrap sur les instances, 10 000 tirages, graine 0.
- Test : Wilcoxon signé apparié par instance, bilatéral, égalités exclues ; correction de Holm sur toutes les
  comparaisons d'un même tableau. Victoires / égalités / défaites.
- Distributions : boîtes à moustaches par famille (obligatoires dans l'article).
- Le **n effectif** du Wilcoxon (paires non égales) est rapporté dans chaque tableau (colonne « n eff. »), en
  particulier pour les familles à nombreuses égalités (Kacem).
- **Meilleur connu de la littérature** (FJSP classique, E7) : `experiences_article1/meilleurs_connus.csv`, constitué
  le 6/10/2026 depuis FJSPLib (ScheduleOpt, commit 4993b4e du 9/08/2026 ; voir `externe/fjsplib/LISEZMOI.md`) ;
  identité des 134 instances vérifiée fichier par fichier ; source de chaque valeur dans le CSV.
  Utilisation : `statistiques.py --ref "FJSPLib meilleur connu|"`.
- Tous les tableaux sont produits par script depuis `banque_resultats/resultats.csv` ; aucun chiffre recopié.

## 5. Matériel
Relevé automatiquement à chaque commande (`experiences_article1/journaux/executions.jsonl`) : système,
processeur, versions de Python, numpy, torch, numba, ortools, scipy ; empreinte du code.

## 6. Constats préliminaires (6/10/2026, cloud, 10 instances Brandimarte — à confirmer par E6)
Faisceau **sans réseau** (moteur seul, toutes les actions) : −0,36 % (B = 5) et −0,50 % (B = 50) par rapport au
recuit, contre −1,00 % (5 × 4) et −0,98 % (50 × 5) avec le réseau. La recherche fait l'essentiel du gain ; le
réseau apporte environ 0,5 point et le faisceau sans réseau plafonne quand B augmente. À présenter tel quel.

## 7. Règles de rédaction (validées par Ghita le 6/10/2026, avec l'angle D5)
- **Thèse** : la recherche au moment de décider égale statistiquement un recuit réglé à budget d'évaluations
  comparable ; la politique apprise en divise le coût par 6 à 9 par rapport à la même recherche sans réseau.
- **Chaque chiffre avec son comparateur, jamais mélangés** :
  - « 6 à 9 fois moins de plannings » = faisceau guidé contre faisceau à règle manuscrite, à qualité égale, lu sur
    la courbe qualité / plannings (`resultats/qualite_budget.pdf`) dont tous les points viennent de la grille
    déclarée (E5, E6) ; jamais présenté comme un avantage sur le recuit ;
  - contre le recuit : à budget d'évaluations comparable (41 884 contre 50 000), écart statistiquement
    indistinguable ; tout avantage sur le recuit vient du **temps mur**, et seulement des mesures E10 ;
  - si E3 montre le recuit sous le faisceau guidé à petit budget, la seconde moitié de la thèse est nuancée.
- **Vocabulaire** : « statistiquement indistinguable du recuit » (jamais « égal ») ; décomposition par famille
  toujours visible, dont la faiblesse sur Hurink edata (+3,1 %).
- **Élagage** : ne pas écrire « ne change rien ». Écrire ce que mesure E6b : part des enfants examinés écartés
  par la borne, effet sur le C_max (instances qui diffèrent) et sur le nombre de plannings évalués. Les instances
  qui diffèrent ne sont pas commentées une à une : « écarts au niveau du bruit, dans les deux sens ». Pas
  d'inférence non mesurée (« les branches coupées auraient été écartées de toute façon ») : seulement l'argument
  de validité de la borne et les deux diagnostics E6b (élagués remplacés ; borne égale à l'incumbent).
  Définitions à écrire dans le papier : « incumbent » = meilleur planning complet connu AU MOMENT de la coupure
  (certificat, pas mesure a posteriori sur le meilleur final) ; un enfant est coupé si sa borne ≥ incumbent, donc
  aucun élagué n'a une borne inférieure : « borne = incumbent » (au mieux égalité) ou « borne > incumbent »
  (ne pouvait même pas égaler). **Phrase de mécanisme obligatoire** (sans elle « bornes sûres » et « qualité
  inchangée » paraissent redondantes, alors que leur coexistence est le résultat) : la borne garantit que les
  branches coupées ne peuvent pas battre l'incumbent ; l'effet de l'élagage passe donc par ailleurs : en libérant
  des places, il change quels autres enfants entrent dans le faisceau, et le score n'étant pas la vraie valeur, la
  trajectoire de recherche se déplace. (7/10/2026 : à même version du code, le C_max ne change sur AUCUNE des 127
  instances ; le mécanisme reste vrai mais n'a pas d'effet mesurable sur la qualité — phrase à réécrire.)
  (Écart politique / règle sur « borne = incumbent » : présent dans le pré-test sur 14 instances, absent sur les
  127 — 49–56 % contre 44–48 % ; phrase retirée le 7/10/2026.)
- **Thèse (validée le 7/10, à figer après E10)** : « à nombre de plannings complets évalués égal, la recherche
  guidée est significativement meilleure que recuit et tabou réglés à petit budget, statistiquement
  indistinguable vers 50 000, et le recuit passe devant au-delà [dans le domaine de budget exploré, jusqu'à E5b] ;
  la politique apprise divise par 6 à 9 le coût de la même recherche sans réseau ». « Domine » seulement là où
  le test par point de budget (E3t, Holm) le soutient ; légende de figure : inférence du réseau non comptée.
- **Élagage, diagnostics secondaires** : écart politique/règle sur « borne = incumbent » = une phrase + annexe
  (inversion edata visible) ; mécanisme : rien d'écrit avant le re-test E9, puis règle d'interprétation du journal
  (7/10 soir) appliquée telle quelle.
- **FJSP classique (E7/E8)** : rapporter tel quel. La politique seule ne transfère pas (glouton +99 %, maintenances
  inutiles) ; la recherche corrige ; 50×5 bat Song et al. 100 tirages (−1,4 %) mais pas le faisceau à règle. Note de
  tableau : 123 = 127 − 4 Kacem. Discussion : une phrase « élargir la distribution d'entraînement (facteur de
  seuil varié) ; question d'adaptation traitée en phase 2 » — sans expérience.
- **Garde-fous (9/10)** : « décider vite, de l'ordre de la seconde » seulement avec les chiffres d'E10 sur la machine
  de référence ; la phrase sur la phase 2 (replanification à chaque événement incompatible avec 10 min de CP-SAT par
  décision) est une MOTIVATION, pas une preuve (à établir empiriquement dans l'article 1b) ; nouveaux meilleurs
  connus : toujours avec source, méthode et date ; « optimum prouvé » seulement si meilleur connu = borne valide.
- **Style de la Méthode (9/10, demande de Ghita)** : expliquer comme à un lecteur non spécialiste — idée d'abord,
  paramètres avec un exemple chiffré (5 × 4 = 20 enfants par pas ; 50 × 5 = 250), étapes numérotées, rôle de chaque
  composant (le réseau filtre, la complétion classe), cas particuliers ; ce style vaut pour tout l'article.
- **Song et al. (9/10)** : jamais « nous battons Song » sans le budget. Écrire : « le faisceau 50 × 5 (≈ 36 700 plannings
  complétés) fait −1,4 % par rapport à Song et al. avec 100 tirages ; à 5 × 4 (≈ 2 700 plannings), différence non
  significative » ; préciser que Song est évalué avec son modèle publié 10 × 5, sur le FJSP classique, hors Kacem,
  et que les budgets diffèrent ; temps de Song mesurés en parallèle : non rapportables.
- **Optimum prouvé (9/10)** : expliquer la preuve : meilleur planning trouvé = borne inférieure valide ; bornes =
  CP-SAT régime A (modèle à segments, Proposition 1 : 8 instances) ou borne/optimum FJSPLib du FJSP classique
  (OptalCP, 11 instances), valable avec maintenance car retirer les maintenances d'un planning laisse un planning
  classique réalisable de même C_max.
- **Instances de réglage** : une ligne dans le papier (« les instances de réglage des métaheuristiques sont exclues
  de l'analyse »), sans en faire un argument, bien que l'exclusion favorise mécaniquement les méthodes non réglées.
- **E15** : en discussion. Le placement de maintenance a une valeur propre et il est couplé à la séquence ; le
  gain n'apparaît que sur les séquences construites par l'agent, pas en réappliquant un placement aux séquences du
  recuit (déjà co-optimisées). Variable explicative : maintenances qui retardent l'opération suivante.
- **Chiffres périmés à ne jamais reprendre** : « 40 % de plannings en moins » (variante sans doublons, remplacé par
  la courbe) ; temps « 5,8 s contre 21–24 s » de la phase 1 (mesurés en parallèle, remplacés par E10).

## Journal des modifications
- 13/10/2026 — article.tex : section Method réécrite en style pédagogique (vue d'ensemble, réseau, entraînement, moteur rapide et sa borne) ; détails vérifiés dans le code (fjsp_env.features, CandNet, imitation/entrainer.py, cand_ft_config.json, train_v3.py, moteur_rapide.borne_inf) ; compilation vérifiée sans erreur ; ancienne version dans article/archives/.
- 13/10/2026 — **E10 terminé** (12/10 21 h → 13/10 5 h 51, un processus ; 54 instances du sous-ensemble de temps
  pré-déclaré : Brandimarte, Kacem, Hurink vdata). Contrôle : C_max du faisceau en un processus identiques à la banque
  (54/54, 50 × 5). Temps moyens du faisceau guidé (réseau compris) : 1 × 4 0,26 s ; 5 × 4 0,90 s ; 10 × 4 1,76 s ;
  20 × 4 3,28 s ; 50 × 5 8,77 s ; faisceau à règle B = 5 / 50 / 200 : 1,22 / 12,4 / 49,5 s. Tests par point de temps
  (`resultats/tests_qualite_temps.md`, même règle d'appariement que E3t, Holm sur 12 tests) : faisceau
  significativement meilleur que le recuit ET le tabou à 1, 2, 5, 10, 20 et 40 s (ex. 1 s : −6,25 % vs recuit ;
  40 s : −0,60 % vs recuit, p Holm 0,003, avec le 50 × 5 à 8,8 s seulement). **Réserve majeure** : sur ce
  sous-ensemble, le faisceau domine AUSSI en plannings évalués jusqu'à 200 000 (recuit 200k −1,68 % contre
  faisceau 50 × 5 −2,74 %, écarts au recuit 50k) ; le sous-ensemble exclut Hurink edata et rdata, où le recuit
  passe devant à grand budget. Le résultat en temps ne peut donc pas être généralisé aux 127 instances sans mesure
  sur edata/rdata (proposition E10b, à décider avec Ghita). Débits mesurés : recuit ≈ 5 000 à 10 000 évaluations/s,
  faisceau 50 × 5 ≈ 4 700 complétions/s : l'unité « plannings évalués » est proche de l'unité temps à un facteur ≈ 1–2.
- 13/10/2026 — `budgets_e9b.json` écrit selon la règle du § 3 ter (temps moyens E10 arrondis) : 5 × 4 → 1 s,
  10 × 4 → 2 s, 50 × 5 → 9 s. Remarque : moyennes sur le sous-ensemble de temps (instances plus petites que la
  moyenne des 127) ; E9b reste lancé sur les 127 instances avec ces budgets, comme déclaré.
- 9/10/2026 — **E10s déclaré** (§ 3 quater) : Song et al. au même temps mur que le faisceau, par instance, sur un cœur ; E10 complété par le faisceau guidé en FJSP classique (5 × 4, 10 × 4, 50 × 5, Brandimarte + vdata) ; `lancer.py` : un dossier par commande. Essai du script (cloud, Mk01/Mk04) : lots de 20 en ≈ 1,3–3 s, dépassement de budget enregistré.
- 9/10/2026 — article.tex : sous-section « Decision-time beam search » réécrite de façon pédagogique (ancienne version dans article/archives/).
- 9/10/2026 (après-midi) — **E9 terminé** (classique : 127 instances de test, 31 OPTIMAL, 96 FEASIBLE ; 5 h 17). Aucune
  borne CP-SAT classique n'améliore la meilleure borne du régime A ; meilleure borne du régime A : FJSPLib (119),
  CP-SAT régime A (8). Classique : aucun C_max de la banque (CP-SAT compris) plus bas que FJSPLib → aucune
  revendication de nouveau meilleur connu en classique. Table `resultats/meilleurs_connus_article.md|csv` régénérée
  (régime A : 19 optimums prouvés, 108 ouvertes ; classique : 118 / 9).
- 9/10/2026 — **re-test pré-déclaré du mécanisme de l'élagage avec les bornes CP-SAT** (`taux_elagage_par_famille.md`
  § 3). Spearman(écart à la meilleure borne, taux d'élagage) : ensemble −0,24 (5 × 4, p 0,006) et −0,29 (50 × 5,
  p 0,0009) ; mais de signe opposé selon la famille : Hurink edata −0,48 (p 0,003), vdata +0,51 à +0,54 (p < 0,001),
  rdata ≈ 0, Brandimarte n.s. ; part « borne = incumbent » : aucune corrélation (≈ 0). **Transparence sur le
  sens** : la règle du 7/10 parlait de « corrélation positive » au sens de l'hypothèse (incumbent plus serré ⇒ plus
  de coupes), ce qui correspond à un Spearman(écart, taux) NÉGATIF ; l'ambiguïté d'écriture est signalée ici et
  la lecture retenue est celle de l'hypothèse. **Conclusion selon la règle** : corrélation globale faible
  (|ρ| < 0,3) et de signe contraire selon la famille ⇒ pas « nette » ⇒ « aucun mécanisme simple ne prédit le taux
  d'élagage » ; on rapporte les chiffres tels quels (faible tendance globale dans le sens attendu, inversée sur
  vdata), sans histoire. Seul le cas Kacem (incumbent à la borne) reste expliqué.
- 9/10/2026 — E10 : faisceau guidé 10 × 4 ajouté aux mesures de temps (nécessaire aux budgets appariés d'E9b ;
  aucun calcul E10 n'avait été fait). Durée réestimée : 11–12 h.
- 9/10/2026 — **E9b précisé avec Ghita avant tout calcul** (§ 3 ter) : scénarios A/B/C définis par le test (Wilcoxon,
  Holm) ; 1 fil = primaire, 8 fils = secondaire, séparés ; échecs = défaite de rang maximal, comptés ; budgets
  appariés = temps murs du faisceau mesurés par E10 (E9b après E10) ; analyse écrite avant les données
  (`outils/analyse_e9b.py`). Ajouts : colonne « Opt. prouvé atteint » dans `statistiques.py` (19 instances de test
  à optimum prouvé ; tableau principal : faisceau 50 × 5 9/19, 5 × 4 7/19, tabou 2/19, recuit 50k 3/19, recuit 200k
  7/19 — la référence n'est pas une ligne du tableau) ; table de provenance `outils/table_meilleurs_connus.py` →
  `resultats/meilleurs_connus_article.md|csv` (meilleur connu et borne par instance et régime, méthode / réglage /
  graine / date, statut optimum prouvé ou ouvert ; classique : comparaison à FJSPLib, aucun C_max plus bas que
  FJSPLib à ce jour ; régime A : 19 prouvés, 108 ouverts).
- 9/10/2026 — **synthèse E9, partie régime A (127 instances de test)** : CP-SAT 600 s (2 fils, démarrage à chaud
  depuis le meilleur planning de la banque, borne sup. = ce planning) : 16 OPTIMAL, 105 FEASIBLE, 6 UNKNOWN (grandes
  Hurink vdata la31–40 : ni planning ni borne). Meilleure borne inférieure : FJSPLib (FJSP classique, valable en
  régime A) sur 107 instances, CP-SAT régime A sur 20 (petites). Écart du meilleur planning connu à la meilleure
  borne : 7,8 % en moyenne (19 instances prouvées optimales, dont les 4 Kacem) ; faisceau 50 × 5 et recuit 50k :
  11,5 % ; recuit 200k : 9,8 % (majorants de l'écart à l'optimum). CP-SAT 600 s démarré à chaud améliore le
  meilleur planning de toutes les autres méthodes sur 78/121 instances (−0,47 % en moyenne, jusqu'à −4,5 %) ; contre
  le recuit 50k −2,99 % (116/5/0), le faisceau 50 × 5 −3,33 % (105/16/0). Comparaison NON équitable (départ = meilleur
  de toutes nos méthodes ; 600 s × 2 fils ; ne peut faire pire que son départ) : ne sera jamais présentée comme
  méthode concurrente ; sert aux bornes et aux meilleurs plannings connus. Partie FJSP classique : en cours.
  Conséquence pour le re-test du mécanisme de l'élagage : bornes CP-SAT peu serrées, apport attendu faible.
- 9/10/2026 — **E9b déclaré AVANT tout calcul (décision commune avec Ghita)** : CP-SAT SEUL comme méthode concurrente,
  voir § 3 ter. Essai préliminaire (cloud, Brandimarte + Kacem, 1 fil, 1 et 5 s, pour tester le script seulement,
  pas pour régler) : sans planning de départ, CP-SAT ne trouve souvent AUCUNE solution en 1–5 s avec ce modèle à
  segments (ex. Kacem2 à 5 s) ; d'où la règle « sans solution, jamais imputé ». Réserve à écrire : le modèle à
  segments est conçu pour une borne valide, pas pour trouver vite de bons plannings ; un modèle par intervalles
  optionnels pourrait faire mieux (limite de la comparaison, à dire).
- 9/10/2026 — E9, partie régime A : 133/134 instances (6 grandes Hurink vdata la31–40 : UNKNOWN, ni planning ni
  borne en 600 s). Bloqué 11 h sur Kacem1 (résolu en 1 s ailleurs ; veille désactivée chez Ghita) : processus fils
  figé, le groupe de processus attendait indéfiniment. `cpsat_article1.py` : chien de garde (aucun résultat pendant
  3 × temps + 600 s ⇒ processus détruits et relancés pour les instances restantes, 4 essais au plus, puis arrêt
  avec code 2) ; résultats inchangés (testé sur Kacem) ; ancienne version dans `archives_code_6oct/`.
- 8/10/2026 — **E5b + E3t (faits le 7/10, lus le 8/10)** : faisceau guidé 100 × 5 −0,15 % (83 019 plannings),
  200 × 4 −0,47 % (139 382) : la courbe descend encore, lentement, sans plafond net. Tests par point de budget
  (Holm, 14 tests) : recuit significativement devant à 100 000 (+0,79 % pour le faisceau, p 0,001) et 200 000
  (+1,01 %, p 0,002) ; tabou indistinguable à 100 000 et 200 000 (p 0,58 et 0,38) ; faisceau devant le recuit
  jusqu'à 10 000 et le tabou jusqu'à 20 000 ; indistinguables à 50 000. « Le recuit passe devant au-delà » est
  désormais mesuré sur les deux courbes ; le tabou, lui, n'est jamais significativement devant. Figure et grille
  E5 régénérées.
- 8/10/2026 — **décision (Ghita) sur E7/E8 : rapporter tel quel, sans masque de domaine.** Le contrôle de
  reproductibilité E8 (43 instances du calcul séquentiel interrompu retrouvées à l'identique) est conservé ici comme
  trace. Note du tableau classique : 123 = 127 de test − 4 Kacem (absents des instances publiées par Song et al. ;
  les 7 instances de réglage restent exclues) — écrite automatiquement par `statistiques.py` (md et tex).
  Discussion de l'article : UNE phrase de perspective, pas d'expérience — le remède structurel au défaut de
  transfert serait d'élargir la distribution d'entraînement (facteur de seuil varié), ce qui rejoint la question
  d'adaptation de la phase 2 (article 1b). Chantier non ouvert dans l'article 1.
- 8/10/2026 — **E7 et E8 terminés** (E8 : 130 instances, 10 h 09 avec 8 processus). Contrôle : les 43 instances
  du calcul séquentiel interrompu sont retrouvées à l'identique (glouton et 5 graines). Tableau `resultats/classique.md`
  (FJSP classique, s = 1000, 123 instances communes : Kacem absent chez Song).
  **Constat principal : la politique seule ne transfère pas au FJSP classique.** Glouton +99,4 % et 100 tirages
  +45,1 % au recuit 50k, avec 131 et 68 maintenances inutiles par instance (recuit et MWKR+EFT : 0) ; en régime A
  la même politique fait autant de maintenances que le recuit. Seuils × 1000 = hors de la distribution
  d'entraînement ; l'espace d'actions autorise la maintenance de toute machine libre. Le faisceau corrige (3,5 à
  4,4 maintenances, souvent sur machine inactive) : 5×4 +2,78 % (2 724 plannings), 50×5 +1,62 % (36 658) ; mais
  le faisceau à règle B = 50 fait +1,38 %, et 50×5 vs règle B = 50 : +0,24 %, 24/38/61, p = 0,0074 (règle meilleure).
  Song et al. (modèle publié 10×5) : glouton +8,49 %, 100 tirages × 5 graines +3,23 %. Apparié (123 instances) :
  faisceau 5×4 contre Song 100 tirages −0,33 % (72/8/43, p = 0,24, indistinguable) ; 50×5 contre Song 100 tirages
  −1,43 % (97/8/18, p = 2·10⁻¹¹) ; 5×4 contre Song glouton −4,94 % (p = 10⁻¹⁹).
  Décision à prendre avec Ghita (aucune correction faite) : rapporter tel quel, ou ajouter un masque de domaine
  déclaré a posteriori (pas de maintenance si elle ne peut jamais devenir nécessaire), présenté comme tel.
- 7/10/2026 (nuit) — E8 relancé en parallèle (8 processus, reprise activée) à 20 h 24 (heure locale). Débit mesuré :
  39 instances en 1 h 54, soit ≈ × 2 seulement par rapport au séquentiel (machine à 12 fils logiques, cœurs hybrides ;
  les gros Hurink la31–40 et vdata dominent). Fin estimée dans la nuit ; aucune autre campagne en même temps.
- 7/10/2026 (soir) — E8 (Song et al.) trop lent en séquentiel (≈ 5 min par instance, 1 fil ; ≈ 44/130 instances en
  3 h 30) et sans écriture au fil de l'eau. `externe/evaluer_song.py` : options `--processus` (instances en parallèle,
  graines fixées par instance) et `--reprendre` (écriture après chaque instance, reprise) ; ancienne version dans
  `externe/archives/`. Vérifié : Mk1, Mk2, Mk4 identiques (glouton et 5 graines) au calcul séquentiel en cours.
  Les temps de Song mesurés en parallèle ne sont pas rapportés (comme pour toutes les méthodes : temps = E10).
  Le calcul séquentiel interrompu sert de contrôle : ses C_max (journal E8.log) doivent être retrouvés.
- 7/10/2026 (soir, après relecture de Ghita) — **mécanisme de l'élagage : INDÉTERMINÉ, pas « non soutenu ».** La
  borne utilisée (moteur à la racine, FJSPLib) surestime l'écart à l'optimum de façon très inégale selon les
  instances : la corrélation ≈ −0,1 (et +0,5 sur vdata) ne falsifie ni ne soutient l'hypothèse. Re-test avec les
  bornes CP-SAT après E9 (`outils/elagage_par_famille.py`, § 3). **Règle d'interprétation fixée AVANT E9** : si la
  corrélation reste nulle ou négative, la conclusion écrite sera « aucun mécanisme simple ne prédit le taux
  d'élagage », sans chercher d'autre histoire ; seule une corrélation positive nette et significative (Holm) autorise
  une phrase mécaniste, et seulement dans le sens mesuré. Jusque-là : seul le cas Kacem est expliqué.
  **Écart politique / règle sur « borne = incumbent » = diagnostic secondaire de l'ablation** : une phrase dans le
  texte (« 61 % contre 51 % au réglage large, non significatif au petit, sens variable selon la famille ») et le
  tableau complet en annexe, inversion Hurink edata (66 % contre 82 %) comprise ; jamais présenté comme un résultat.
- 7/10/2026 (soir) — **élagage par famille** (`outils/elagage_par_famille.py` → `resultats/taux_elagage_par_famille.md|csv`,
  depuis `taux_elagage.csv`, seule la borne à la racine est recalculée).
  (a) Hétérogénéité : elle vient de Kacem seul (taux 24–61 %, 4 instances) ; Brandimarte coupe MOINS que la moyenne
  (2,5–3,9 %) ; Hurink 2,1–7,5 % (vdata le plus haut). Le pré-test (8,7–12,5 %) était gonflé par les 4 Kacem sur 14.
  Kacem : C_max = borne inférieure (optimum prouvé) ; une fois l'incumbent à la borne, tout enfant est coupé.
  (b) Écart politique / règle sur « borne = incumbent » : la phrase « disparu » du 7/10 était FAUSSE (l'écart du
  pré-test existait sur les mêmes 14 instances, même code ; il ne pouvait pas venir de la composition). Sur 127,
  apparié par instance, Holm sur 14 tests : 50×5 contre 50×0 : 61 % contre 51 %, 70/12/45, p Holm 0,032
  (significatif) ; 5×4 contre 5×0 : 58 % contre 54 %, p 0,41 (non significatif) ; par famille, aucun test
  significatif après Holm, sens variable (Hurink edata inversé à B = 5 : 66 % contre 82 %). Formulation : « au
  réglage large, une part plus grande des enfants coupés par la borne a une borne égale à l'incumbent avec la
  politique qu'avec la règle (61 % contre 51 %) ; l'écart n'est pas significatif au petit réglage et varie selon
  la famille ».
  (c) Mécanisme proposé (« incumbent plus serré ⇒ plus de coupes / plus de bornes égales ») NON soutenu par les
  données disponibles : Spearman(écart à la meilleure borne connue, taux d'élagage) ≈ −0,1 sur l'ensemble, et
  POSITIF dans Hurink vdata (+0,5) ; seule exception cohérente : Kacem (écart nul). Réserve : l'écart est mesuré
  à une borne faible (borne SUPÉRIEURE de l'écart à l'optimum) ; à refaire avec les bornes CP-SAT (E9) avant
  conclusion. En attendant, pas de phrase mécaniste générale dans l'article : seulement le cas Kacem.
  Article : tableau par famille en annexe ; texte : « 3 à 6 % en moyenne (2 à 8 % hors Kacem ; 24 à 61 % sur
  Kacem, où le faisceau atteint la borne inférieure) ».
- 7/10/2026 (après-midi) — **thèse par budget validée par Ghita, avec trois amendements.**
  (1) Courbe du faisceau guidé fermée à grand budget : étape **E5b** (100 × 5 et 200 × 4), ajoutée APRÈS avoir vu
  E3, explicitement comme sensibilité (ne change pas les réglages pré-déclarés 5 × 4 et 50 × 5). Question :
  plafonnement ou non du faisceau guidé. En attendant : « dans le domaine de budget exploré ».
  (2) Unité : axe de la figure = « Complete schedules evaluated per instance » ; légende de la figure et texte :
  le coût d'inférence du réseau n'est pas compté. La thèse n'est figée (et le résumé écrit) qu'après E10 : si le
  temps mur raconte la même histoire (domination à petit temps, croisement, dépassement), thèse dans les deux
  unités ; sinon, version « plannings évalués » présentée comme telle.
  (3) « Domine » = test : `tests_qualite_budget.py` (étape E3t). Appariement fixé le 7/10 après avoir vu la courbe,
  choisi conservateur pour le faisceau : à chaque budget b de la métaheuristique, faisceau de la grille au plus grand
  nombre moyen de plannings ≤ b ; Wilcoxon apparié par instance ; Holm sur tous les tests du graphique (recuit et
  tabou, 14 tests aujourd'hui, 14 après E5b). Résultat provisoire (avant E5b) : faisceau significativement
  meilleur que le recuit jusqu'à 10 000 (p Holm ≤ 2·10⁻⁵) et que le tabou jusqu'à 20 000 (0,0016) ; à 20 000 contre
  le recuit, différence −1,20 % [−2,08 ; −0,35] mais p Holm 0,23 ; à 50 000 indistinguable (0,23 recuit ; 0,58
  tabou) ; recuit significativement meilleur à 100 000 (0,002) et 200 000 (8·10⁻⁵), mais contre 100 × 4
  (70 821 plannings) faute de point plus grand → E5b.
  Cascade : chiffres historiques de la phase 1 marqués périmés dans les documents du projet (bilan, synthèse,
  plan phase 2) ; aucun brouillon de l'article ne les cite (vérifié). Fichier généré historique restant :
  `comparaisons/anticipation_eleve_faisceau5_k4.md` (RL:eleve, phase 1, hors article).
- 7/10/2026 (fin de matinée) — E5 (60 lignes recalculées) et E15 relancés. Banque ↔ E6b : 635/635 lignes identiques
  (C_max ET plannings évalués) : la banque du faisceau est désormais d'une seule version. Tableaux et figure
  régénérés (anciens dans `resultats/archives_avant_correction_7oct/`). Correctif de `statistiques.py` et
  `figure_qualite_budget.py` : « plannings évalués » et « temps/inst. » étaient moyennés sur TOUTES les lignes de la
  banque (131 instances, dont réglage et hors test), désormais moyenne par instance sur les seules instances
  analysées (anciens scripts dans `archives_code_6oct/`). Effet : 5×4 3 625 → 3 580 ; 50×5 41 884 → 41 326 ;
  règle B=5 5 810 → 5 856, B=50 61 660 → 62 100, B=200 246 441 → 248 089. Écarts au recuit quasi inchangés
  (5×4 +0,77 → +0,76 % ; 50×5 +0,03 → +0,05 %, p Holm 0,057). E15 inchangé à 0,01 point près (−1,64 %
  [−2,05 ; −1,25], 59/66/2).
- 7/10/2026 (matin) — correction (d) appliquée par Ghita : 60 lignes retirées (13 348 → 13 288 lignes), archivées
  dans `banque_resultats/archives/` (copie intégrale avant retrait + `faisceau_phase1_1oct2026.csv|jsonl`) ;
  aucun planning référencé manquant (vérifié). Il ne reste que des lignes du 6/10 pour le faisceau 5×4 et 50×5.
- 7/10/2026 — **E3 et E6b terminés ; défaut de banque découvert par E6b.**
  (a) E6b (127 instances, `resultats/taux_elagage.md`) : nouvelles colonnes présentes (nouvelle version bien
  utilisée). Taux d'élagage : politique 3,4 / 4,6 / 6,1 % (1×4 / 5×4 / 50×5), règle 6,2 / 6,4 % (5×0 / 50×0) ;
  élagués remplacés 74–83 % ; borne = incumbent 49–56 % (politique) et 44–48 % (règle). Les chiffres du pré-test
  (8,7–12,5 %, écart politique/règle 77–91 % contre 47–58 %) étaient dus aux 14 instances Brandimarte + Kacem : plus
  d'écart notable sur 127 ; la phrase prévue sur cet écart est retirée.
  (b) Comparaison E6b ↔ banque : C_max identiques sur 624/635 lignes ; les 11 différences portent toutes sur des
  lignes « RL:imit-ft » faisceau=5,k=4 et 50,k=5 datées du 1/10/2026 (30 benchmarks de la phase 1, dont 26 de
  test), que E5 n'avait pas recalculées (déjà présentes). Les lignes du 6/10 sont reproduites à l'identique ; les
  lignes anciennes des règles (30/9), du glouton (1/10), du recuit et du tabou (30/9, graines 0–2, Brandimarte)
  aussi (vérifié en relançant). Seul le faisceau de la phase 1 provient donc d'une version antérieure du code.
  (c) Conséquence : avec le code actuel, élagage ou non, le C_max du 5×4 est IDENTIQUE sur 127/127 instances ;
  les « 4 différences » attribuées à l'élagage venaient du mélange de versions, pas de l'élagage. Effet mesuré de
  l'élagage, même version : C_max inchangé partout ; plannings évalués 3 580 contre 4 025 (−11 %).
  (d) Correction prévue (validation de Ghita requise, banque modifiée) : `outils/retirer_faisceau_phase1.py`
  archive (copie intégrale + lignes retirées) puis retire les 60 lignes ; `lancer --etape E5` les recalcule ;
  puis E15 (utilise les plannings 5×4) et tous les tableaux et figures sont régénérés. Les lignes « RL:eleve »
  (1/10) ne sont dans aucun tableau de l'article et restent telles quelles.
  (e) E3 (courbe recuit et tabou, 2 000 à 200 000 évaluations) : à petit budget le faisceau guidé est nettement
  meilleur (5×4 : +0,77 % à 3 625 plannings ; recuit +5,4 % à 5 000, tabou +4,0 %) ; à 50 000 indistinguables ;
  au-delà le recuit passe devant (100 000 : −0,93 % ; 200 000 : −1,47 % ; faisceau 100×4 : −0,20 % à 70 715).
  Chiffres du faisceau provisoires jusqu'au recalcul (d). La thèse est à reformuler par budget (à valider).
- 6/10/2026 (soir) — **127 / 134, mise au clair avant E6b** : 134 instances sont CALCULÉES par toutes les campagnes
  (`lancer.py`, FAM = Brandimarte 10 + Hurink la01–la40 × 3 jeux 120 + Kacem 4) ; 127 sont ANALYSÉES (tous les
  tableaux, figures, tests et E6b). Les 7 retirées sont les instances du réglage Taguchi des métaheuristiques
  présentes dans la01–la40 : HurinkEdata13, HurinkEdata23, HurinkEdata33, HurinkRdata8, HurinkRdata18,
  HurinkRdata28, HurinkRdata38 (la 8e instance de réglage, HurinkEdata3, est hors la01–la40). Raison : une
  instance qui a servi à régler une méthode concurrente ne peut pas servir à la tester. Mise en œuvre :
  `INSTANCES_REGLAGE` (statistiques.py, figure_qualite_budget.py, e15_maintenance.py) et `REGLAGE_TAGUCHI`
  (outils/taux_elagage.py), mêmes 8 noms. Les 4 instances dont le C_max diffère avec et sans élagage (Mk05, Mk09,
  HurinkRdata36, HurinkRdata41) sont toutes de test : 4/127.
- 6/10/2026 (soir) — **diagnostic d'élagage (E6b uniquement)** : `anticipation.py` compte en plus (i) les enfants
  élagués dont la place dans le faisceau a été prise par un enfant moins bien classé, (ii) ceux dont la borne est
  égale au meilleur connu. Aucun effet sur la recherche (vérifié : C_max et compteurs identiques au calcul
  préliminaire). Le C_max de la banque reste celui de la recherche AVEC élagage ; le diagnostic n'écrit rien dans
  la banque. Le test demandé « la vraie valeur de l'enfant élagué l'aurait-elle fait entrer dans le faisceau
  (seuil d'admission du niveau) ? » est trivialement vrai par construction (les enfants sont examinés par score
  croissant et la borne n'est testée que tant que le faisceau n'est pas plein) ; il est remplacé par (i). Le vrai
  contrefactuel « sans élagage » est l'ablation E6 (banque) : 4/127 instances diffèrent.
  Préliminaire (Brandimarte + Kacem, 14 instances, `resultats/taux_elagage_diagnostic_preliminaire_brandimarte_kacem.md`) :
  ≈ 74 % des élagués (politique) sont remplacés par un enfant moins bien classé, 78–91 % ont une borne égale au
  meilleur connu. L'inférence « auraient été écartés de toute façon » est donc FAUSSE et abandonnée : l'élagage
  remodèle le faisceau ; sa neutralité sur le C_max (4/127, deux sens) est un constat, pas une conséquence.
- 6/10/2026 (soir) — `lancer --etape E3 E6b` lancé AVANT ces deux modifications et non interrompu. E3 n'utilise
  aucun fichier modifié (recuit et tabou). E6b démarre dans un nouveau processus après E3 et lit donc la nouvelle
  version d'`anticipation.py` et de `taux_elagage.py` ; mais l'empreinte de code notée dans `executions.jsonl` est
  celle du lancement (avant modification), pour E3 comme pour E6b. Preuve que E6b a tourné avec la nouvelle version :
  colonnes `elagues_remplaces` et `elagues_borne_egale` dans `resultats/taux_elagage.csv`.
- 6/10/2026 (soir) — définitions des compteurs écrites dans `taux_elagage.py` et au § 7 (incumbent au moment de la
  coupure ; colonne « borne > incumbent » ajoutée au tableau, simple complément, aucun calcul nouveau). Cascade
  127/134 vérifiée : figure qualité/budget (E3) lit la banque avec `INSTANCES_REGLAGE` exclues ; tableau par famille
  de `statistiques.py` sur la base analysée (`principal_provisoire.md` : edata 37, rdata 36) ; E10 porte sur le
  sous-ensemble de temps pré-déclaré Brandimarte + Kacem + Hurink vdata (54 instances), qui ne contient aucune
  instance de réglage (toutes edata/rdata), donc inclus dans les 127.
- 6/10/2026 : angle D5 validé ; règles de rédaction (§ 7) ; compteurs d'enfants examinés ajoutés à `anticipation.py` (sans effet sur les plannings) ; étape E6b (taux d'élagage).
- 6/10/2026 : version 1.
- 6/10/2026 : pilote pannes permises → NO-GO, consigné au § 1.
- 6/10/2026 (soir) : E15 lancée sans l'exclusion des 7 instances de réglage et arrêtée par une erreur d'affichage Windows (caractère « − ») APRÈS l'écriture de ses fichiers ; tableaux refaits sur 127 instances depuis `e15_details.csv` (`--resumer-seulement`), premier calcul conservé (`e15_premier_calcul_134_instances.md`). Correctifs : exclusion dans `e15_maintenance.py`, sorties UTF-8 dans `lancer.py` et les scripts. Aucun calcul refait, aucun chiffre changé hors exclusion.
- 6/10/2026 : `comparer_rl.py` parallélisé (`--processus`) ; résultats inchangés (vérifié) ; les temps par instance de l'agent seul deviennent, comme les autres, des temps de campagne parallèle, non rapportés.
- 6/10/2026 : confirmation de Ghita — aucun autre réglage du faisceau n'a été essayé ; réserve levée.
- 6/10/2026 : 7 instances de réglage Taguchi exclues du test (127 instances) — chevauchement repéré en préparant la rédaction.
- 6/10/2026 : table des meilleurs connus et bornes (FJSPLib) ; borne FJSPLib ajoutée au max des bornes.
- 6/10/2026 : règle de sélection du faisceau pré-déclarée (5 × 4 et 50 × 5 ; grille E5 = sensibilité seulement) ;
  graines et hasard de l'agent (100 tirages sans glouton × graines 0–4, symétrique de Song ; glouton et faisceau
  déterministes à réseau fixé) ; n effectif du Wilcoxon ; colonne « meilleur connu » conditionnelle ; précision
  sur les 109 placements de E15 ; 3 vs 5 graines. Protocole validé par Ghita.
- 6/10/2026 : pilote à 5 graines (R = u, β = 0 et 0,5) ; critère de tri du faisceau explicité (§ 3) ; E15 (§ 3 bis).
- 6/10/2026 : § 1 reformulé (la maintenance est le cœur de l'article ; le FJSP classique n'est qu'un contrôle).

### 13/10/2026 — Figure 1 (exemple illustratif de la section Problème)
- Instance : Table 1 de Bencheikh & Bettayeb (GOL'24, LNNS 1105, 2024 ; fichier litterature/Bencheikh2022.pdf, nom
  de fichier trompeur), 3 jobs × 2 machines ; T = lambda/mu = (10, 14) avec lambda = 0,7, mu = (0,07 ; 0,05) ; M = 2.
- Script : `python -m experiences_article1.figure_exemple` -> resultats/exemple_illustratif.{pdf,png,json}.
  Style commun de toutes les figures (palette, Gantt) : experiences_article1/style_figures.py, à réutiliser pour les
  Gantt de la section Résultats.
- Résultats (CP-SAT 1 fil, graine 0, OR-Tools 9.15 dans la VM Linux) : (a) FJSP sans usure C_max = 29 (OPTIMAL),
  seuil franchi sur les 2 machines ; (b) deux temps (ordres de (a), PM juste à temps, décalage à gauche) C_max = 35,
  4 PM ; (c) optimum conjoint C_max = 33 (OPTIMAL, borne 33), 3 PM.
- Contrôle croisé : 33 = valeur publiée par Bencheikh & Bettayeb (Fig. 1(c), lambda = 0,7, PMT = 2) avec leur MILP
  indexé sur le temps, alors que leur modèle déclenche la maintenance au seuil et le nôtre la laisse libre.
- Réserve : (b) dépend de l'optimum FJSP retenu en (a) (plusieurs optimums possibles) ; on le présente comme
  « un » plan en deux temps, pas comme le meilleur plan en deux temps.
- 13/10/2026 (article) : bencheikh2024gol et bencheikh2022jms ajoutés à references.bib et cités dans l'introduction et
  l'état de l'art (validé par Ghita) ; phrase du pilote retirée du résumé (le pilote P1 est abandonné, remplacé par
  la citation de bencheikh2024gol en section 3, à rédiger). Sauvegarde : article/archives/article_avant_bencheikh_2026-10-13.tex.
  Compilation vérifiée (pdflatex + bibtex, aucune référence indéfinie).
- 13/10/2026 (article) : exemple illustratif (figure_exemple.py) retiré de l'article par décision de Ghita ; script et
  résultats conservés (resultats/exemple_illustratif.*). Les citations Bencheikh (2022, 2024) iront dans l'introduction
  (importance de la planification conjointe). Section 3 révisée (style C&OR) dans article/revision_section3_2026-10-13.tex,
  en attente de validation ; notation : S_o début, C_o fin, N_k nombre de segments.
- 13/10/2026 : version de calcul OR-Tools = 9.15.6755 (venv du PC de calcul). À confirmer : cette version était-elle
  déjà installée lors des campagnes CP-SAT (E9, bornes) ? Sinon, le dire dans la section protocole.
- 13/10/2026 (article) : schéma de la preuve de la Proposition 1 (nombre de segments), exemple fictif purement
  illustratif (T_k = 10, M = 2, charges 4|3|8|2|7 -> 7|10|7). Script figure_preuve_segments.py ->
  resultats/schema_preuve_segments.{pdf,png} ; style commun style_figures.py.
- 13/10/2026 (article) : schéma du contre-exemple (facteur 2 de la Proposition 1) : trois opérations de durée 6,
  T = 10, aucune fusion possible, N = 3 = 2*ceil(18/10) - 1. Script figure_contre_exemple_segments.py ->
  resultats/schema_contre_exemple_segments.{pdf,png} (exemple fictif, illustratif).
- 13/10/2026 (article) : les deux schémas de la section 3.3 sont réunis côte à côte (décision de Ghita) :
  figure_segments.py -> resultats/schema_segments.{pdf,png} ; (a) fusion des segments, (b) aucun fusion possible.
- 14/10/2026 — **E9b et E10s terminés** (nuit du 13 au 14, machine au repos ; E9b 21 h 02 → 00 h 23, E10s → 02 h 41 ;
  OR-Tools 9.15.6755). Analyses pré-déclarées appliquées sans modification : resultats/e9b.md|csv, e10s_song_temps.md|csv.
  * E9b primaire (1 fil, budgets appariés 1 / 2 / 9 s) : scénario **A** aux trois budgets (p Holm ≤ 1,3e-22).
    CP-SAT sans départ ne trouve aucune solution sur 103, 90 et 54 instances sur 127 ; sur les instances résolues,
    C_max +174 %, +190 %, +145 % au-dessus du faisceau ; victoires de CP-SAT : 0, 0, 2. Secondaire (8 fils) : même sens
    (+127 % à +119 %, 102 à 53 échecs).
  * Contrôle hors analyse (grille, 1 fil, contre faisceau 50×5) : à 40 s, 32/127 instances toujours sans solution,
    écart médian +34 % sur les résolues, 12 instances où CP-SAT égale ou bat le faisceau. Neutralise la réserve sur
    les budgets (moyennes E10 sur un sous-ensemble plus petit) : même à ~4 fois le budget, la conclusion tient.
  * Règle de l'option « second modèle CP » (§ 3 ter) : écart TRÈS grand en A → limite dite en une phrase dans
    l'article (le modèle à segments est conçu pour des bornes valides, pas pour trouver vite des plannings) ; pas de
    contre-expérience requise par la règle.
  * E10s (FJSP classique, 50 instances Brandimarte + Hurink vdata, un cœur, même temps mur par instance) : scénario
    **A (faisceau meilleur)** pour 5×4, 10×4 et 50×5 : écart −2,75 %, −2,71 %, −3,11 % ; V/E/D 43/6/1, 43/6/1, 43/7/0 ;
    p Holm 3e-8. Médiane de 20 tirages pour Song (un seul lot) ; Song DÉPASSE son budget (médiane 4,6–6,8 s, max 65 s) :
    biais en faveur de Song, la conclusion est donc prudente.
- 14/10/2026 — **E10b déclaré** (§ 3 quinquies) avec Ghita, avant tout calcul ; implémenté : familles
  `HurinkEdataLaPair` / `HurinkRdataLaPair` (36 instances, vérifiées), étape `E10b` de `lancer.py`, option
  `--sous-ensemble` de `tests_qualite_temps.py` (défaut = E10, sortie vérifiée IDENTIQUE à l'ancienne). Lancement prévu
  la nuit du 14/10, machine au repos.
  Garde-fous ajoutés avant lancement : rapports de E10b écrits à part (`resultats_metaheuristiques/temps_mono_E10b/`,
  `comparaisons/anticipation_imit-ft-mono_*_E10b.md`, option `--suffixe` d'anticiper.py) pour ne pas écraser ceux de
  E10 ; les données vont dans la banque comme d'habitude (clé = instance, aucune collision avec E10).
- 14/10/2026 (article) : sections 4 (Decision process, brève) et 5 (Method) proposées dans
  article/revision_methode_2026-10-14.tex (notation O_{i,j}, p_{i,j,k}) ; trois schémas (figures_methode.py ->
  resultats/schema_methode_{ensemble,reseau,faisceau}) ; annexes : descripteurs (à compléter) et hyperparamètres
  (vérifiés dans le code). Correction : en mode « full », un lancement n'est proposé que s'il tient dans la marge
  d'usure, la maintenance est une action séparée (l'ancien texte était faux sur ce point).
- 14/10/2026 (article) : section MDP restructurée à la demande de Ghita (environnement, état, actions, transitions,
  récompense et objectif, agent et politique, complétude de l'espace d'actions = Proposition 2 avec preuve) ;
  schéma schema_methode_mdp.{pdf,png} (boucle agent–environnement, instants de décision). Ancienne proposition :
  article/archives/revision_methode_2026-10-14_v1.tex.
- 14/10/2026 (article) : section 4 réécrite dans le style demandé par Ghita (« Reinforcement learning formulation » :
  4.1 rappels — agent/environnement, tuple (S, A, P, R, γ), retour, V/Q, Bellman, familles d'algorithmes ; 4.2 MDP de
  notre problème, élément par élément, + politique, objectif et Proposition de complétude). Version précédente :
  article/archives/revision_methode_2026-10-14_v2.tex. Références classiques à vérifier avant ajout au .bib.
- 15/10/2026 — **E10b terminé** (nuit du 14/10, 16 h 57 → 19 h 50 heure du journal ; aucune erreur). Règle du
  § 3 quinquies appliquée sans modification : `resultats/tests_qualite_temps_E10b.md` (primaire, 36 instances).
  * Le faisceau n'est significativement meilleur à AUCUN budget sur E10b. Recuit : indistinguable à 1 et 2 s
    (p Holm = 1), recuit significativement MEILLEUR à 5, 10, 20 et 40 s (écart faisceau − recuit +2,10 %, +3,02 %,
    +2,98 %, +3,82 % ; p Holm ≤ 0,0028). Tabou : indistinguable à 1, 2 et 5 s ; tabou significativement meilleur à
    10, 20 et 40 s (+1,85 %, +2,12 %, +2,76 % ; p Holm ≤ 0,0011).
  * Temps moyens du faisceau sur E10b : 1×4 0,32 s, 5×4 1,12 s, 20×4 4,06 s, 50×5 10,29 s (plus longs qu'en E10 ;
    à 1 s c'est le 1×4 qui est apparié).
  * Conséquence (règle déclarée) : la phrase « en temps, le faisceau est meilleur de 1 à 40 s » ne vaut QUE pour le
    sous-ensemble E10 (Brandimarte, Kacem, vdata) ; sur edata/rdata, résultat rapporté tel quel (métaheuristiques
    meilleures à partir de 5 s pour le recuit, 10 s pour le tabou). Union 90 instances : descriptif seulement.
  * Contrôle descriptif (banque, budget en plannings, écart au recuit 50k, par famille ; hors analyse déclarée) :
    faisceau 50×5 : Brandimarte −0,84 %, Kacem −7,51 %, vdata −2,73 %, edata +3,17 %, rdata +1,02 % ; 5×4 : edata
    +4,24 %, rdata +2,00 %. L'hétérogénéité par famille existe aussi à budget égal en plannings : la moyenne +0,05 %
    du tableau principal cache un faisceau meilleur sur les instances très flexibles (vdata) et moins bon sur les
    peu flexibles (edata). Hypothèse À TESTER, pas un résultat : lien avec la flexibilité des instances
    d'entraînement générées.
  * Contrôle complémentaire (même jour, descriptif) : le faisceau SANS réseau (règle seule, 50×5 et 200×0) montre le
    MÊME profil par famille (edata +3,91 % / +3,07 %, rdata +1,10 % / +0,85 %, vdata −2,59 % / −2,74 %). Flexibilité
    moyenne (part des machines éligibles) : edata 0,15 ; rdata 0,26 ; Brandimarte 0,36 ; vdata 0,48 ; générateur
    d'entraînement ≈ 0,5–0,6 (k ~ U{1..m}). L'hypothèse « distribution d'entraînement » n'est donc PAS soutenue :
    la faiblesse sur instances peu flexibles vient du schéma de recherche (complétion MWKR + EFT), pas du réseau.
    Interprétation à présenter comme telle : à faible flexibilité le problème est surtout un problème de séquencement,
    que la complétion gloutonne estime mal, alors que la recherche locale des métaheuristiques le traite directement.
- 15/10/2026 — Tableau principal : ligne « Flexibilité » ajoutée (décision de Ghita : constat descriptif, pas
  d'expérience supplémentaire). Définition : part moyenne des machines éligibles par opération (fichiers .fjs),
  moyennée sur les instances analysées de chaque famille : Brandimarte 0,36 ; edata 0,15 ; rdata 0,26 ; vdata 0,48 ;
  Kacem 1,00 ; ensemble 0,33 (`resultats/principal_provisoire_flexibilite.json`). Régénéré par
  `python -m experiences_article1.statistiques --methodes experiences_article1/methodes_principal_sans_hybride.json
  --nom principal_provisoire` ; toutes les autres lignes vérifiées IDENTIQUES. Ancienne version du script :
  ../archives_code_6oct/statistiques_avant_flexibilite_2026-10-15.py. (Note : l'archive de tests_qualite_temps.py
  avant E10b n'a pas été écrite le 14/10, chemin erroné ; sans conséquence, la sortie E10 avait été vérifiée identique.)
- 15/10/2026 (article) : section Method réécrite de façon pédagogique (idée → définition → raison) avec équations
  (réseau, pertes d'imitation, PPO, auto-imitation, borne inférieure) et algorithme du faisceau (pseudo-code).
  Corrections vérifiées dans le code : (1) le rejeu d'un planning expert garde les séquences par machine, son C_max
  est ≤ celui de l'expert (et non « exactement égal ») — imitation/rejeu.py ; (2) l'auto-imitation compare aussi deux
  règles (PM-JIT, PM-JIT+), garde les 4 derniers tours en mémoire et apprend par entropie croisée — train_v3.py,
  sil_phase. Version précédente : article/archives/revision_methode_2026-10-15_v3.tex. Préambule : algorithm +
  algpseudocode à ajouter. Références à vérifier : schulman2016gae, oh2018sil.
- 15/10/2026 (article) : references.bib complété (11 entrées : garey1976, sutton2018, puterman1994, bellman1957,
  watkins1992, williams1992, mnih2015, konda2000, schulman2016gae, schulman2017ppo, oh2018sil), chacune vérifiée en
  ligne ; année d'OR-Tools / CP-SAT 9.15 = 2026 (notes de version, janvier 2026). Correction : deux commentaires du
  .bib contenaient « @ » et faisaient échouer deux entrées sous BibTeX. Test bibtex : 27 entrées, 0 erreur,
  0 avertissement. Sauvegarde : article/archives/references_avant_rl_2026-10-15.bib. Section 3 : \refverifier Garey
  remplacé par \citep{garey1976}.
- 15/10/2026 (article) : section 4 restructurée sur la base de la rédaction de Ghita : RL et ordonnancement présentés
  ensemble (chaque élément général suivi de « In our problem ») ; redondances supprimées (MDP, politique, retour, γ et
  politique optimale n'apparaissent plus qu'une fois). Version précédente : archives/revision_methode_2026-10-15_v4.tex.
- 15/10/2026 (article) : notation changée à la demande de Ghita : job j, i-ième opération O_{j,i} (n_j opérations,
  K_{j,i}, p_{j,i,k}, S_{j,i}, C_{j,i}, x_{j,i,k,s}, prochaine opération i_j, lancement (j,k), borne r_j, w_j).
  Appliquée aux sections 3, 4, 5 (fichiers de révision ; sauvegardes *_avant_notation_j_2026-10-15.tex) et au schéma
  du réseau (figures_methode.py, régénéré).
- 16/10/2026 (article) : figure de la preuve de la Proposition 2 (complétude de l'espace d'actions) : `figure_preuve_completude.py` -> `resultats/schema_preuve_completude.pdf|png`. Exemple fictif 2 jobs x 2 machines (aucune donnée expérimentale) ; C_max optimal = 15 vérifié dans le script par énumération des ordres sur chaque machine. Quatre panneaux : (a) planning optimal avec maintenance à usure nulle, maintenance finale et trou inutile ; (b) étape 1 ; (c) étape 2 ; (d) étape 3 (rejeu aux époques de décision).
- 16/10/2026 (article) : preuve de la Proposition 2 rédigée par un agent indépendant (demande de Ghita) -> article/brouillon_preuve_prop2_agent_2026-10-16.tex (non intégrée). Points soulevés : énoncé à restreindre aux instances faisables ; existence d'un optimum (temps continu) démontrée dans la preuve ; cas (a)/(b) non exclusifs ; conflits de notation (tau_m, S^*) à corriger.
- 16/10/2026 (article) : figure du modèle CP (section 3.2) : `figure_modele_cp.py` -> `resultats/schema_modele_cp.pdf|png`. Exemple fictif, une machine (T_k = 10, M_k = 2, N_k = 4) : segments, variables y_{k,s} et pi_{k,s}, segment vide, courbe d'usure c_k(t). Aucune donnée expérimentale.
- 20/10/2026 (article) : section 4, passage avantage / Bellman (forme déterministe Q et V) / erreur temporelle validé par Ghita -> article/textes_valides_section4_2026-10-20.tex (à intégrer dans article.tex).
- 21/10/2026 (article) : nouvelle figure du réseau de politique, couche par couche (demande de Ghita) : `figure_reseau_couches.py` -> `resultats/schema_reseau_couches.pdf|png` ; remplace schema_methode_reseau dans l'article (ancien script conservé). Architecture lue dans jssp_pm/fjsp_ppo.py (CandNet, h = 128). Nombre de paramètres calculé à partir des couches (torch absent de la machine) : phi_c 20 864, phi_g 19 072, psi 65 921, nu 49 537, total 155 394 (d dans theta ∈ R^d).
- 21/10/2026 (article) : schema_reseau_couches : ajout des cadres des cinq composants (i) encodeur d'actions, (ii) encodeur d'état, (iii) agrégation, (iv) tête de politique, (v) tête de valeur, alignés sur l'énumération du texte de la section 5.1.
- 21/10/2026 (article) : tableau des 33 + 19 features (section 5.1) -> article/tableau_features_2026-10-21.tex, rédigé ligne à ligne depuis fjsp_env.py (features, reset) et fjsp_env3.py. Points de détail relevés : marge d'une machine en maintenance prise égale à T_k dans f_{k'} (pm_head_fix) ; « fastest » = argmin (premier indice en cas d'égalité).
- 21/10/2026 (article) : tableau des features : notation sortie de la légende et placée dans un paragraphe d'annexe (section app:features) ; version précédente archives/tableau_features_2026-10-21_v1.tex.
- 21/10/2026 (article, constat important) : vérification des journaux d'entraînement pour justifier les trois étapes de la section 5.2.
  Validation (24 instances générées, politique gloutonne, C_max moyen ; référence de règle 175,75) :
  imitation seule (models/imitation/cand_log.json) : meilleur 176,75 (époque 3), instable 176,75–216,5 sur 20 époques ;
  imitation + PPO (cand_ft_log.json) : meilleur 165,21 à 51 200 décisions, puis 168,7–171,75 jusqu'à 301 056 ;
  auto-imitation (8 tours, départ du meilleur PPO) : 165,29–167,29, jamais sous 165,21.
  D'après train_v3.py (sil_phase : _best.pt écrit au départ, remplacé seulement si amélioration), le réseau retenu
  cand_ft_best.pt est donc le point PPO à 51 200 décisions : l'auto-imitation n'a rien apporté au réseau final.
  PPO sans imitation (models/v3/A_full_s{0,1,2}, PPO puis auto-imitation, lr 3e-4) : meilleurs 175,1 / 176,8 / 180,6
  (≈ niveau de la règle) — comparaison de développement, non contrôlée (taux d'apprentissage et budgets différents).
  Conséquence pour l'article : décrire l'entraînement retenu comme imitation + PPO ; l'auto-imitation ne peut pas être
  présentée comme une étape qui améliore le réseau.
- 21/10/2026 (article) : figure de la section 5.2 (trois étapes d'entraînement et sélection sur la validation) : `figure_entrainement.py` -> `resultats/schema_entrainement.pdf|png`. Schéma de méthode, aucun résultat ; theta_i = meilleur point de validation de l'étape i (train_v3.py : ppo_best rechargé en fin de PPO ; _best.pt en auto-imitation).
- 21/10/2026 (article) : paragraphe « Training instances » retiré de la section 5.2 et mis en attente pour Experimental setup -> article/a_deplacer_protocole.tex (décision de Ghita) ; la 5.2 garde une phrase de renvoi (« no benchmark instance is used for training or model selection »).
- 21/10/2026 (article) : schema_entrainement : détails de la validation (24 instances, politique gloutonne) retirés de la figure, renvoyés au protocole expérimental.
- 22/10/2026 (article) : figure de la section 5.3 en notation de l'article : `figure_faisceau.py` -> `resultats/schema_faisceau.pdf|png` (remplace schema_methode_faisceau, conservé). Exemple fictif B = K = 2 ; montre aussi les actions non développées (filtre du réseau).
- 22/10/2026 (article) : schema_faisceau refait avec B = 3, K = 2 (demande de Ghita) : arbre développement/évaluation + tableau de sélection (retenu, doublon, élagué, non examiné). Ancienne version : archives_code_6oct/figure_faisceau_B2K2_2026-10-22.py.
- 22/10/2026 (décision de Ghita) : E11–E12 (variance d'entraînement, réseaux de graines 1 et 2) NON réalisées. L'article
  utilise un seul réseau (`models/imitation/cand_ft_best.pt`, graine d'entraînement 0). Conséquences : la phrase sur
  les trois réseaux est retirée de la section Experimental setup ; la variabilité due à l'entraînement est citée comme
  limite dans la Discussion. Estimation du coût si un relecteur la demande : environ 9 h en séquentiel (2 réseaux).

## 27/10/2026 — Section Related work (rédaction)
- Section reformulée en entier : `article/related_work_2026-10-27.tex` (5 paragraphes continus + tableau `tab:literature`). Sources : fiches de `claude/revue_litterature.md` ; chiffres de Song et al. 2023 (tableau V) sourcés en commentaire.
- `article/references.bib` : les 16 entrées de l'état de l'art du 27/10 n'étaient pas dans la version locale (écrasée par l'ajout de Freddi2019) ; fusion des deux versions (45 entrées, aucun doublon) + ajout de `zhang2026dynamic` (CIE 218:112121, vérifiée sur la notice du dépôt BIT ; texte intégral non lu, PDF demandé à l'auteur).
