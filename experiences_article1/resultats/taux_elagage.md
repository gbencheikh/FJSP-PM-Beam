# Taux d'élagage et de doublons du faisceau (127 instances)

Taux = écartés / enfants examinés pour entrer dans le faisceau, moyenne sur les instances.

Trois dernières colonnes : part des enfants élagués (tous réunis, toutes instances). « Incumbent » = meilleur planning complet connu AU MOMENT de la coupure. Remplacés : leur place est prise par un enfant moins bien classé. Borne = incumbent : la branche pouvait au mieux l'égaler ; borne > incumbent : elle ne pouvait même pas l'égaler (aucun élagué n'a une borne < incumbent, par la règle de coupure).

| Réglage | Enfants évalués / inst. | Examinés / inst. | Taux d'élagage | Instances avec ≥ 1 élagage | Taux de doublons | Instances avec ≥ 1 doublon | Élagués remplacés | Borne = incumbent | Borne > incumbent |
|---|---|---|---|---|---|---|---|---|---|
| politique 1x4 | 708 | 202 | 3.40 % | 127/127 | 0.00 % | 0/127 | 74.2 % | 48.7 % | 51.3 % |
| politique 5x4 | 3580 | 1088 | 4.59 % | 127/127 | 6.22 % | 127/127 | 76.0 % | 53.6 % | 46.4 % |
| politique 50x5 | 41326 | 11538 | 6.14 % | 127/127 | 11.66 % | 127/127 | 80.0 % | 55.5 % | 44.5 % |
| regle 5x0 | 5856 | 1043 | 6.23 % | 127/127 | 7.82 % | 126/127 | 81.5 % | 48.4 % | 51.6 % |
| regle 50x0 | 62100 | 12156 | 6.38 % | 127/127 | 19.11 % | 127/127 | 82.9 % | 44.1 % | 55.9 % |
