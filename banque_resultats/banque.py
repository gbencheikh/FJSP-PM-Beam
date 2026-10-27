"""Banque de résultats : chaque méthode n'est lancée qu'une fois par instance et par configuration.

Fichier principal : banque_resultats/resultats.csv — une ligne par exécution :
  instance, regime, facteur_seuil, methode, config, graine, cmax, maintenances, pannes, temps_s, date, solution
  - methode : nom de la règle / métaheuristique / agent RL (ex. « MWKR+EFT », « Recuit simulé », « RL:complet-s0 »)
  - config  : ce qui change le résultat en plus de la méthode (ex. « budget=5s,depart=heuristique »,
              « glouton ») ; vide pour les règles de priorité.
  - evaluations : nombre de plannings évalués par la méthode (vide pour les règles et le RL glouton).
  - solution : identifiant du planning complet dans banque_resultats/solutions.jsonl (vide si absent).
solutions.jsonl : une ligne JSON par exécution, {"id": ..., "planning": [[machine, début, fin, type, job], ...]},
  type 1 = opération, 2 = maintenance, 3 = réparation ; job = -1 pour une maintenance.

Avant de lancer une exécution, les scripts de comparaison consultent la banque : si la même
(instance, régime, facteur de seuil, méthode, config, graine) existe déjà, elle n'est pas relancée.
"""
import csv, datetime, json, os, re

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)))
FICHIER = os.path.join(DOSSIER, "resultats.csv")
SOLUTIONS = os.path.join(DOSSIER, "solutions.jsonl")
# Dépôt public : les plannings sont livrés compressés (solutions.jsonl.gz) ; décompression au premier import.
if not os.path.exists(SOLUTIONS) and os.path.exists(SOLUTIONS + ".gz"):
    import gzip, shutil
    with gzip.open(SOLUTIONS + ".gz", "rb") as _src, open(SOLUTIONS, "wb") as _dst:
        shutil.copyfileobj(_src, _dst)
COLONNES = ["instance", "regime", "facteur_seuil", "methode", "config", "graine", "cmax",
            "maintenances", "pannes", "temps_s", "date", "solution", "evaluations"]


def cle(instance, regime, facteur_seuil, methode, config="", graine=0):
    return (instance, regime, f"{float(facteur_seuil):g}", methode, config, str(int(graine)))


def _migrer():
    """Ajoute les colonnes manquantes à un ancien fichier (valeur vide)."""
    if not os.path.exists(FICHIER):
        return
    with open(FICHIER, newline="", encoding="utf-8") as f:
        lecteur = csv.DictReader(f)
        if lecteur.fieldnames == COLONNES:
            return
        lignes = list(lecteur)
    with open(FICHIER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        for r in lignes:
            w.writerow({c: r.get(c, "") or "" for c in COLONNES})


def charger():
    """Liste de dicts (toutes les exécutions enregistrées)."""
    _migrer()
    if not os.path.exists(FICHIER):
        return []
    with open(FICHIER, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cles_existantes():
    return {cle(r["instance"], r["regime"], r["facteur_seuil"], r["methode"], r["config"], r["graine"])
            for r in charger()}


def _nom_fichier(*parts):
    s = "__".join(str(p) for p in parts)
    return re.sub(r"[^A-Za-z0-9_.=+-]+", "-", s)


def ajouter(instance, regime, facteur_seuil, methode, config, graine, cmax, maintenances, pannes,
            temps_s, planning=None, evaluations=None):
    """Ajoute une exécution (et son planning si fourni). Écrit immédiatement sur disque."""
    ident = ""
    if planning is not None:
        ident = _nom_fichier(instance, regime, f"s{float(facteur_seuil):g}", methode, config, f"g{int(graine)}")
        with open(SOLUTIONS, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": ident, "planning": [[int(k), float(a), float(b), int(t), int(j)]
                                                          for k, a, b, t, j in planning]}) + "\n")
    _migrer()
    nouveau = not os.path.exists(FICHIER)
    with open(FICHIER, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nouveau:
            w.writerow(COLONNES)
        w.writerow([instance, regime, f"{float(facteur_seuil):g}", methode, config, int(graine),
                    f"{float(cmax):g}", int(maintenances), int(pannes), f"{float(temps_s):.3f}",
                    datetime.datetime.now().isoformat(timespec="seconds"), ident,
                    "" if evaluations is None else int(evaluations)])


def planning(ligne):
    """Recharge le planning d'une ligne de la banque (ou None)."""
    if not ligne.get("solution") or not os.path.exists(SOLUTIONS):
        return None
    with open(SOLUTIONS, encoding="utf-8") as f:
        for l in f:
            d = json.loads(l)
            if d["id"] == ligne["solution"]:
                return [tuple(x) for x in d["planning"]]
    return None


def supprimer(filtre):
    """Retire de la banque les lignes pour lesquelles filtre(ligne) est vrai (et leurs plannings)."""
    lignes = charger()
    garder = [r for r in lignes if not filtre(r)]
    ids = {r["solution"] for r in garder if r.get("solution")}
    if os.path.exists(SOLUTIONS):
        with open(SOLUTIONS, encoding="utf-8") as f:
            sols = [l for l in f if json.loads(l)["id"] in ids]
        with open(SOLUTIONS, "w", encoding="utf-8") as f:
            f.writelines(sols)
    with open(FICHIER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        w.writerows(garder)
    return len(lignes) - len(garder)
