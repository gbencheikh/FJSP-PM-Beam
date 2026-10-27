# Pilote go/no-go — pannes permises avec seuils connus (6 octobre 2026)

Script : `experiences_article1/pilote_regime_pannes.py` (cloud, 2 cœurs). Données : `pilote_regime_pannes_rho6.csv`
(protocole, R = 6u), `pilote_regime_pannes_rho1.csv` et `_rho2.csv` (diagnostic, R = u et R = 2u).

## Dispositif
- 5 instances : Brandimarte Mk1, Mk4, Mk7, Mk10, Hurink vdata la01.
- Politique de maintenance « seuil de décision » θ : maintenance si c_k + p > θ·T_k ; θ ∈ {1 ; 1,25 ; 1,5 ; 2 ; ∞}.
  θ = 1 : prévention stricte ; θ > 1 : on laisse l'usure franchir T_k (panne : op arrêtée au seuil, réparation R_k,
  reprise, usure remise à 0) ; θ = ∞ : jamais de maintenance.
- Objectif J = C_max + β·u·N_pannes, β ∈ {0 ; 0,5 ; 2} (0 = diagnostic).
- Méthodes : MWKR + EFT (moteur rapide) et recuit simulé sur (ordre, machines) avec objectif J
  (10 000 évaluations pour R = 6u, 5 000 pour le diagnostic), départ = règle, 1 graine.
- Seuils « A » (protocole de l'article) et « B » (protocole « stress » : seuils plus bas, options plus longues que T_k gardées).

## Résultats (θ* = θ qui minimise J, recuit)
| Seuils | R | β = 0 | β = 0,5 | β = 2 |
|---|---|---|---|---|
| A | 6u | θ* = 1 sur 5/5 | θ* = 1 sur 5/5 | θ* = 1 sur 5/5 |
| B | 6u | θ* = 1 sur 4/5 (Mk1 : 1,5, « gain » 11,5 %) | θ* = 1 sur 4/5 (Mk1 : 1,5, 1,7 %) | θ* = 1 sur 4/5 (Mk1 : 1,5, 6,2 %) |
| A | 2u | θ* = 1 sur 4/5 (gain 1,2 %) | θ* = 1 sur 4/5 (gain 1,4 %) | θ* = 1 sur 5/5 |
| A | u | θ* > 1 sur 4/5 (gain 1,2 à 4,8 %) | θ* = 1 sur 5/5 | θ* = 1 sur 5/5 |

Bruit du recuit (1 graine) : à θ = 1, le même problème donne des J qui varient de 3 à 5 % d'un lancement à l'autre
(Mk4, R = u : 83 / 81 / 86) ; les gains du risque observés sont de cet ordre. Le cas Mk1 en seuils B ne bascule pas
avec β (θ* = 1,5 aux trois β) et la solution θ = 1,5 a MOINS de pannes (1) que celle à θ = 1 (2, pannes forcées par les
options plus longues que T_k) : ce n'est pas une prise de risque, c'est la variance du recuit (à θ = 1, J = 78 / 80,8 / 89,1).

## Verdict : NO-GO pour l'article 1
- Avec le protocole (R = 6u), la prévention stricte est optimale partout, même à β = 0 : personne n'a intérêt à
  courir le risque. Aucun basculement entre β = 0,5 et β = 2.
- Même en rendant la réparation aussi courte que la maintenance (R = u), le risque ne paie qu'à β = 0, et de
  quelques pour cent, au niveau du bruit. Dès β = 0,5, la prévention gagne partout.
- Explication : avec un seuil connu, une panne est une maintenance plus chère (R ≥ M), placée au pire endroit
  (au milieu d'une opération, jamais dans un temps mort), et pénalisée par β. Son seul avantage — consommer toute
  la vie restante — est faible. Prendre un risque n'a de valeur que quand le seuil est incertain : c'est le terrain
  de l'article 1b.
- Le régime « pannes permises » reste dans le code pour l'article 1b. Phrase possible dans l'article 1 (discussion) :
  avec information parfaite, la prévention domine la prise de risque, même quand la réparation n'est pas plus longue
  que la maintenance (pilote, 5 instances).

## Limites du pilote
5 instances, 1 graine, budgets courts, politique θ uniforme sur toutes les machines et tous les cycles (une décision
cycle par cycle pourrait trouver un peu plus). Ces limites ne changent pas le verdict : même l'effet maximal observé
reste au niveau du bruit et disparaît dès β = 0,5.

## Vérification à 5 graines (cas le plus favorable au risque : R = u)
Fichiers : `pilote_regime_pannes_rho1_5graines*.csv|txt` (β = 0) et `pilote_regime_pannes_rho1_beta05_5graines*` (β = 0,5).
Recuit 10 000 évaluations, graines 0–4 ; pour chaque instance, θ = 1 contre le meilleur θ > 1 (choisi a posteriori
parmi 4 : test de Mann-Whitney unilatéral, correction de Bonferroni × 4).

| Instance | β = 0 : écart du meilleur θ > 1 (p corrigée) | β = 0,5 : écart du meilleur θ > 1 |
|---|---|---|
| Mk1 | −0,39 % (0,85) | +0,54 % |
| Mk4 | −2,47 % (1) | +13,82 % |
| Mk7 | −4,13 % (0,11) | +13,24 % |
| Mk10 | −1,26 % (**0,012**) | +40,92 % |
| Hurink vdata la01 | −0,62 % (0,62) | +6,56 % |

Conclusion affinée : « jamais rentable » serait trop fort. La panne paie dans le seul cas limite R = M et β = 0,
et seulement sur une instance sur cinq de façon significative (Mk10, −1,3 %) : la panne n'y est qu'une
maintenance gratuite placée exactement au seuil, au milieu d'une opération, c'est-à-dire une préemption.
Dès qu'elle coûte quelque chose (β = 0,5), la prévention domine partout. Phrase pour l'article : « with perfect
information, prevention dominates risk-taking as soon as a breakdown costs anything beyond a maintenance;
the value of risk only appears under uncertainty ».
