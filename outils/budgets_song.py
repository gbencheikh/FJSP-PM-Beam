"""Budgets de temps de E10s : temps mur du faisceau guidé MESURÉ PAR E10 sur chaque instance du FJSP classique
(méthode « RL:imit-ft-mono », un processus, machine au repos), pour 5×4, 10×4 et 50×5. Écrit externe/budgets_song.csv.

  python -m outils.budgets_song
"""
import csv, os, sys
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from banque_resultats import banque     # noqa: E402

REGLAGES = {"5x4": "faisceau=5,k=4", "10x4": "faisceau=10,k=4", "50x5": "faisceau=50,k=5"}
SORTIE = os.path.join(RACINE, "externe", "budgets_song.csv")


def main():
    lignes = []
    for r in banque.charger():
        if r["methode"] == "RL:imit-ft-mono" and float(r["facteur_seuil"]) == 1000 and r["regime"] == "A":
            for nom, cfg in REGLAGES.items():
                if r["config"] == cfg:
                    lignes.append(dict(instance=r["instance"], reglage=nom, budget_s=float(r["temps_s"])))
    if not lignes:
        sys.exit("aucune mesure E10 du faisceau en FJSP classique dans la banque : lancer E10 d'abord")
    with open(SORTIE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["instance", "reglage", "budget_s"]); w.writeheader(); w.writerows(lignes)
    print(f"{len(lignes)} budgets -> {SORTIE}")


if __name__ == "__main__":
    main()
