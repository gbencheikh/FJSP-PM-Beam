# Réglage des paramètres des métaheuristiques (méthode de Taguchi)

## Pourquoi
Les paramètres de l'algorithme génétique, de la recherche tabou et du recuit simulé avaient été
fixés « à la main ». Un relecteur peut objecter qu'une méthode a été désavantagée. La méthode de
Taguchi permet de les régler de façon systématique, avec peu d'essais.

## Ce que fait le script
1. Chaque paramètre est testé à 3 niveaux (le niveau du milieu = valeur actuelle).
2. Le tableau orthogonal L9 choisit 9 combinaisons seulement (au lieu de 81 pour 4 paramètres),
   de sorte que chaque niveau de chaque paramètre soit testé autant de fois.
3. Les essais tournent sur 8 instances Hurink **qui ne servent pas** aux comparaisons finales
   (edata 3, 13, 23, 33 et rdata 8, 18, 28, 38) : on ne règle pas sur les instances de test.
4. Mesure : C_max divisé par celui de la règle MWKR+EFT ; score S/N « plus petit est meilleur »
   (plus il est grand, meilleur et plus stable est le réglage).
5. Pour chaque paramètre, on garde le niveau au meilleur S/N ; une ANOVA donne l'influence (%)
   de chaque paramètre.
6. Confirmation : la combinaison retenue est relancée et comparée aux valeurs par défaut.
   Si elle ne fait pas mieux, les valeurs par défaut sont gardées.

## Lancer (Windows, depuis le dossier du projet, environnement activé)
```
python -m reglage_taguchi.taguchi --processus 10
```
Durée indicative : 3 méthodes × (9 + 2) combinaisons × 8 instances × 2 graines = 528 exécutions
de 50 000 évaluations. Si le script est interrompu, relancez la même commande : il reprend.

Puis, pour comparer avec les paramètres réglés (enregistré dans la banque sous une configuration
distincte `...,params=taguchi`, les anciens résultats restent) :
```
python -m metaheuristiques.comparer --evaluations 50000 --parametres reglage_taguchi/parametres_retenus.json --processus 10
```

## Fichiers produits
- `essais.csv` : chaque exécution (méthode, essai, paramètres, instance, graine, C_max…)
- `rapport.md` : tableaux L9, effet des niveaux, ANOVA, confirmation — prêt pour l'article
- `parametres_retenus.json` : paramètres finaux par méthode
