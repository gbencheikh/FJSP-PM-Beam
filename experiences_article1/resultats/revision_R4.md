# R4 — maintenance longue (mu = 3), réseau non réentraîné

127 instances de test ; référence : recuit Taguchi 50k (moyenne de 3 graines), même banque mu = 3.

| B × K | Filtre | Écart réseau | Écart filtre | Différence | IC 95 % | V/E/D (réseau) | p Holm |
|---|---|---|---|---|---|---|---|
| 5x4 | regle | +0.86 % | +1.33 % | -0.47 | [-0.84 ; -0.13] | 65/18/44 | 0.09 |
| 5x4 | borne | +0.86 % | +1.27 % | -0.41 | [-0.89 ; +0.03] | 76/12/39 | 0.1 |
| 50x5 | regle | -0.09 % | +0.18 % | -0.27 | [-0.56 ; +0.00] | 64/22/41 | 0.1 |
| 50x5 | borne | -0.09 % | +0.20 % | -0.29 | [-0.59 ; -0.00] | 67/19/41 | 0.1 |

Meilleur filtre à 5x4 : borne ; réseau significativement meilleur : non.

Meilleur filtre à 50x5 : regle ; réseau significativement meilleur : non.

**Verdict R4** : le verdict de R1 tient.

Équivalence ±1 % (faisceau guidé 50×5 contre recuit) : écart -0.09 %, IC 90 % [-0.87 ; +0.66] → oui.

Maintenances moyennes par instance (moyenne des graines) :
- Faisceau:filtre-borne [faisceau=5,k=4,filtre=borne] : 13.8
- Faisceau:filtre-borne [faisceau=50,k=5,filtre=borne] : 13.5
- Faisceau:filtre-regle [faisceau=5,k=4,filtre=regle] : 14.1
- Faisceau:filtre-regle [faisceau=50,k=5,filtre=regle] : 13.6
- RL:imit-ft [faisceau=5,k=4] : 13.3
- RL:imit-ft [faisceau=50,k=5] : 13.0
- Recuit simulé [evals=50000,depart=heuristique,params=taguchi] : 12.3
