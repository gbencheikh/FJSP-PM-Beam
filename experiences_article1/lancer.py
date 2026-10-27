"""Campagne d'expériences de l'article 1 (cas déterministe), étape par étape.

Toutes les commandes sont lancées depuis la racine du projet (dossier qui contient anticiper.py),
avec l'environnement Python du projet activé. Chaque étape :
  - reprend là où elle s'est arrêtée (les scripts sautent ce qui est déjà dans la banque) ;
  - écrit son journal dans experiences_article1/journaux/<étape>.log ;
  - ajoute une ligne dans experiences_article1/journaux/executions.jsonl (date, machine, empreinte du code,
    commande, durée, code de retour).

  python -m experiences_article1.lancer --liste                 # étapes, coût estimé
  python -m experiences_article1.lancer --etape E2 --processus 8
  python -m experiences_article1.lancer --etape E2 --essai       # affiche les commandes sans les lancer

Le protocole (instances, graines, budgets, statistiques) est figé dans experiences_article1/PROTOCOLE.md.
"""
import argparse, datetime, hashlib, json, os, platform, subprocess, sys, time

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
PY = sys.executable
FAM = ["Brandimarte", "HurinkLa", "Kacem"]                 # 10 + 120 + 4 = 134 instances CALCULÉES ; 127 analysées (7 de réglage Taguchi exclues, PROTOCOLE § 2)
TAGUCHI = "reglage_taguchi/parametres_retenus.json"
MODELE = "models/imitation/cand_ft_best.pt"               # meilleur réseau (graine d'entraînement 0)
GRAINES_MH = ["0", "1", "2", "3", "4"]
CLASSIQUE = "1000"                                         # facteur de seuil : FJSP classique (aucune maintenance utile)


def mh(methodes, evals=None, budget=None, graines=GRAINES_MH, fs="1", processus="{P}"):
    c = [PY, "-m", "metaheuristiques.comparer", "--familles", *FAM, "--graines", *graines,
         "--parametres", TAGUCHI, "--facteur-seuil", fs, "--processus", processus, "--methodes", *methodes]
    return c + (["--evaluations", str(evals)] if evals else ["--budget", str(budget)])


def faisceau(nom, modele, B, K, fs="1", extra=(), familles=FAM, processus="{P}"):
    m = ["--modele", modele] if modele else ["--sans-reseau"]
    return [PY, "anticiper.py", *m, "--nom", nom, "--largeur", str(B), "--k", str(K), "--familles", *familles,
            "--facteur-seuil", fs, "--processus", processus, *extra]


SA, TS, GA = "Recuit simulé", "Recherche tabou", "Algorithme génétique"
# Sous-ensemble pour les mesures de TEMPS (un seul processus, machine au repos) : 54 instances
SOUS_ENSEMBLE_TEMPS = ["Brandimarte", "Kacem", "HurinkVdataLa"]   # 10 + 4 + 40 vdata
# E10b (déclaré le 14/10/2026, PROTOCOLE § 3 quinquies) : une instance sur deux de Hurink edata / rdata, réglage exclu (36)
SOUS_ENSEMBLE_TEMPS_B = ["HurinkEdataLaPair", "HurinkRdataLaPair"]

ETAPES = {
    "E0": dict(titre="Contrôles : tests unitaires et informations machine", cout="5 min",
               cmds=[[PY, "-m", "pytest", "-q", "tests/test_moteur.py", "tests/test_anticipation.py", "tests/test_fjsp.py"]]),
    "E1": dict(titre="Règles de priorité (134 calculées, 127 analysées)", cout="5 min",
               cmds=[[PY, "-m", "regles_priorite.comparer", "--familles", *FAM, "--facteur-seuil", "1"]]),
    "E2": dict(titre="Métaheuristiques Taguchi, 50 000 évaluations, 5 graines (tableau principal)",
               cout="≈ 134 × 5 × (21 + 19 + 39) s ≈ 15 h CPU ; ≈ 2 h avec 8 processus",
               cmds=[mh([SA, TS, GA], evals=50000)]),
    "E3": dict(titre="Courbe qualité / budget en évaluations : recuit et tabou, 3 graines",
               cout="≈ 134 × 3 × 2 × 330 000 évaluations ≈ 30 h CPU ; ≈ 4 h avec 8 processus",
               cmds=[mh([SA, TS], evals=e, graines=["0", "1", "2"]) for e in (2000, 5000, 10000, 20000, 100000, 200000)]),
    "E4": dict(titre="Agent seul : glouton et 100 tirages × 5 graines (0–4), symétrique de Song et al.", cout="≈ 40 min",
               cmds=[[PY, "comparer_rl.py", "--processus", "{P}", "--modele", MODELE, "--nom", "imit-ft", "--familles", *FAM],
                     [PY, "comparer_rl.py", "--processus", "{P}", "--modele", MODELE, "--nom", "imit-ft", "--familles", *FAM,
                      "--echantillons", "100", "--graines", "0", "1", "2", "3", "4"]]),
    "E5": dict(titre="Agent + anticipation : grille B × K", cout="≈ 134 × (Σ temps des 11 réglages) ≈ 12 h CPU",
               cmds=[faisceau("imit-ft", MODELE, B, K) for B, K in
                     [(1, 2), (1, 4), (5, 2), (5, 4), (10, 4), (20, 2), (20, 4), (50, 2), (50, 4), (50, 5), (100, 4)]]),
    "E5b": dict(titre="Faisceau guidé à grand B (100 × 5, 200 × 4) : plafonnement ou non (ajout du 7/10, sensibilité seulement)",
                cout="≈ 134 × (80 + 125) s ≈ 8 h CPU ; ≈ 1 h avec 8 processus",
                cmds=[faisceau("imit-ft", MODELE, B, K) for B, K in [(100, 5), (200, 4)]]),
    "E3t": dict(titre="Tests appariés par point de budget de la courbe qualité / plannings (lit la banque)",
                cout="< 1 min",
                cmds=[[PY, "-m", "experiences_article1.tests_qualite_budget"]]),
    "E6": dict(titre="Ablations : faisceau sans réseau, réseau non entraîné, sans élagage, sans doublons",
               cout="≈ 6 h CPU",
               cmds=[[PY, "-m", "outils.reseau_aleatoire", "--ref", MODELE, "--graine", "0",
                      "--out", "models/aleatoire/cand_aleatoire_g0.pt"]]
                    + [faisceau("regle", None, B, 0) for B in (5, 20, 50, 100, 200)]
                    + [faisceau("aleatoire-g0", "models/aleatoire/cand_aleatoire_g0.pt", B, K) for B, K in [(5, 4), (50, 5)]]
                    + [faisceau("imit-ft", MODELE, 5, 4, extra=["--sans-elagage"]),
                       faisceau("imit-ft", MODELE, 5, 4, extra=["--sans-doublons"])]),
    "E6b": dict(titre="Taux d'élagage, de doublons et diagnostic des élagués, 127 instances (vérification de l'ablation ; ne touche pas la banque)",
                cout="≈ 30 min avec 8 processus",
                cmds=[[PY, "-m", "outils.taux_elagage", "--processus", "{P}"]]),
    "E7": dict(titre="FJSP classique (seuils infinis) : contrôle et terrain commun avec Song et al.",
               cout="≈ 8 h CPU (dont métaheuristiques 5 graines)",
               cmds=[[PY, "-m", "regles_priorite.comparer", "--familles", *FAM, "--facteur-seuil", CLASSIQUE],
                     mh([SA, TS], evals=50000, fs=CLASSIQUE),
                     [PY, "comparer_rl.py", "--processus", "{P}", "--modele", MODELE, "--nom", "imit-ft", "--familles", *FAM,
                      "--facteur-seuil", CLASSIQUE],
                     [PY, "comparer_rl.py", "--processus", "{P}", "--modele", MODELE, "--nom", "imit-ft", "--familles", *FAM,
                      "--facteur-seuil", CLASSIQUE, "--echantillons", "100", "--graines", "0", "1", "2", "3", "4"],
                     faisceau("imit-ft", MODELE, 5, 4, fs=CLASSIQUE), faisceau("imit-ft", MODELE, 50, 5, fs=CLASSIQUE),
                     faisceau("regle", None, 50, 0, fs=CLASSIQUE)]),
    "E8": dict(titre="Song et al. (2023), modèle publié 10×5, glouton + 100 tirages × 5 graines",
               cout="≈ 10–15 h en séquentiel ; mesuré le 7/10 : accélération ≈ × 2 seulement avec 8 processus sur cette machine (12 fils logiques, cœurs hybrides) → ≈ 6–8 h ; reprise possible (--reprendre) ; temps non rapportables", dossier="externe",
               cmds=[[PY, "evaluer_song.py", "--graines", "0", "1", "2", "3", "4", "--processus", "{P}", "--reprendre"]]),
    "E9": dict(titre="CP-SAT 600 s : régime A (borne valide) puis FJSP classique (relaxation)",
               cout="134 × 600 s × 2 ≈ 45 h mur si séquentiel ; ≈ 11 h avec 4 instances en parallèle × 2 fils",
               cmds=[[PY, "cpsat_article1.py", "--familles", *FAM, "--temps", "600", "--workers", "2",
                      "--instances-paralleles", "{P4}"],
                     [PY, "cpsat_article1.py", "--familles", *FAM, "--facteur-seuil", CLASSIQUE, "--temps", "600",
                      "--workers", "2", "--instances-paralleles", "{P4}"]]),
    "E9b": dict(titre="CP-SAT SEUL, sans démarrage à chaud — APRÈS E10 (budgets appariés dans budgets_e9b.json) ; 1 et 8 fils ; UN processus, machine au repos",
                cout="≈ 134 × (78 + 45) s ≈ 4 h 30 à 5 h mur ; reprise automatique (banque)",
                cmds=[[PY, "cpsat_sans_depart.py", "--familles", *FAM],
                      [PY, "-m", "outils.analyse_e9b"]]),
    "E10": dict(titre="Mesures de TEMPS sur un seul processus (machine au repos) : courbe qualité / temps",
                cout="≈ 11–12 h mur (recuit + tabou ≈ 7 h, faisceaux guidés ≈ 1 h, faisceaux à règle ≈ 3 h 30) : une nuit, machine au repos",
                cmds=[[PY, "-m", "metaheuristiques.comparer", "--familles", *SOUS_ENSEMBLE_TEMPS, "--graines", "0", "1", "2",
                       "--parametres", TAGUCHI, "--etiquette-params", "taguchi,mono", "--processus", "1",
                       "--methodes", SA, TS, "--budget", str(b),
                       "--sortie", "resultats_metaheuristiques/temps_mono"] for b in (1, 2, 5, 10, 20, 40)]
                     + [faisceau("imit-ft-mono", MODELE, B, K, familles=SOUS_ENSEMBLE_TEMPS, processus="1")
                        for B, K in [(1, 4), (5, 4), (10, 4), (20, 4), (50, 5)]]   # 10×4 ajouté le 9/10 (budgets appariés d'E9b)
                     + [faisceau("regle-mono", None, B, 0, familles=SOUS_ENSEMBLE_TEMPS, processus="1") for B in (5, 50, 200)]
                     # 9/10 : faisceau guidé en FJSP classique, budgets de temps de E10s (Song), sans Kacem (absent chez Song)
                     + [faisceau("imit-ft-mono", MODELE, B, K, fs=CLASSIQUE, familles=["Brandimarte", "HurinkVdataLa"],
                                 processus="1") for B, K in [(5, 4), (10, 4), (50, 5)]]),
    "E10s": dict(titre="Song et al. au MÊME temps mur que le faisceau (par instance), un cœur, FJSP classique — APRÈS E10",
                 cout="≈ 50 instances × 3 réglages × 3 graines × temps du faisceau ≈ 2 h ; machine au repos",
                 cmds=[[PY, "-m", "outils.budgets_song"],
                       [PY, "evaluer_song_temps.py", "--budgets", "budgets_song.csv", "--graines", "0", "1", "2"],
                       [PY, "-m", "outils.analyse_song_temps"]],
                 dossiers=[".", "externe", "."]),
    "E10b": dict(titre="Mesures de TEMPS sur Hurink edata / rdata (36 instances, une sur deux), un processus, machine au repos — même protocole que E10",
                 cout="≈ 36 × (2 × 3 × 78 s) ≈ 4 h 40 (recuit + tabou) + faisceaux guidés ≈ 1 h : ≈ 6 h, une nuit, machine au repos",
                 cmds=[[PY, "-m", "metaheuristiques.comparer", "--familles", *SOUS_ENSEMBLE_TEMPS_B, "--graines", "0", "1", "2",
                        "--parametres", TAGUCHI, "--etiquette-params", "taguchi,mono", "--processus", "1",
                        "--methodes", SA, TS, "--budget", str(b),
                        "--sortie", "resultats_metaheuristiques/temps_mono_E10b"] for b in (1, 2, 5, 10, 20, 40)]
                      + [faisceau("imit-ft-mono", MODELE, B, K, familles=SOUS_ENSEMBLE_TEMPS_B, processus="1",
                                  extra=("--suffixe", "_E10b"))
                         for B, K in [(1, 4), (5, 4), (10, 4), (20, 4), (50, 5)]]
                      + [[PY, "-m", "experiences_article1.tests_qualite_temps", "--sous-ensemble", "E10b"],
                         [PY, "-m", "experiences_article1.tests_qualite_temps", "--sous-ensemble", "union"]]),
    "E11": dict(titre="Deux graines d'entraînement supplémentaires (imitation puis PPO), mêmes plannings experts",
                cout="≈ 2 × (2 h imitation + 2 h PPO)",
                cmds=sum([[[PY, "-m", "imitation.entrainer", "--reseau", "candidats", "--epoques", "20", "--seed", g,
                            "--out", f"models/imitation/cand_g{g}"],
                           [PY, "train_v3.py", "--init", f"models/imitation/cand_g{g}_best.pt", "--lr", "1e-4",
                            "--ppo_steps", "300000", "--seed", g, "--out", f"models/imitation/cand_ft_g{g}"]]
                          for g in ("1", "2")], [])),
    "E12": dict(titre="Évaluation des graines d'entraînement 1 et 2 (glouton, meilleur de 100, faisceau 5×4 et 50×5)",
                cout="≈ 2 × 4 h CPU",
                cmds=sum([[[PY, "comparer_rl.py", "--processus", "{P}", "--modele", f"models/imitation/cand_ft_g{g}_best.pt", "--nom", f"imit-ft-g{g}",
                            "--familles", *FAM],
                           [PY, "comparer_rl.py", "--processus", "{P}", "--modele", f"models/imitation/cand_ft_g{g}_best.pt", "--nom", f"imit-ft-g{g}",
                            "--familles", *FAM, "--echantillons", "100", "--graines", "0", "1", "2", "3", "4"],
                           faisceau(f"imit-ft-g{g}", f"models/imitation/cand_ft_g{g}_best.pt", 5, 4),
                           faisceau(f"imit-ft-g{g}", f"models/imitation/cand_ft_g{g}_best.pt", 50, 5)] for g in ("1", "2")], [])),
    "E13": dict(titre="Sensibilité au facteur de seuil (0,7 et 1,5) : règles, recuit 50 000 × 3 graines, faisceau 5×4",
                cout="≈ 6 h CPU",
                cmds=sum([[[PY, "-m", "regles_priorite.comparer", "--familles", *FAM, "--facteur-seuil", fs],
                           mh([SA], evals=50000, graines=["0", "1", "2"], fs=fs),
                           faisceau("imit-ft", MODELE, 5, 4, fs=fs)] for fs in ("0.7", "1.5")], [])),
    "E14": dict(titre="Hybride (borne pratique) : recuit Taguchi 50 000 évaluations parti du planning de l'agent 5×4",
                cout="≈ 134 × 3 × 21 s ≈ 2,5 h CPU",
                cmds=[[PY, "hybride_rl_mh.py", "--nom", "imit-ft-faisceau5x4", "--depart-banque", "RL:imit-ft|faisceau=5,k=4",
                       "--methodes", SA, "--evaluations", "50000", "--graines", "0", "1", "2", "--parametres", TAGUCHI,
                       "--familles", *FAM, "--processus", "{P}"]]),
    "E15": dict(titre="Valeur de la décision de maintenance (ordre et affectation figés) — après E2 et E5",
                cout="≈ 134 × 2 sources × (100 tirages + 5 recuits de 20 000) ≈ 30 min",
                cmds=[[PY, "-m", "experiences_article1.e15_maintenance", "--familles", *FAM,
                       "--sources", "Recuit simulé|evals=50000,depart=heuristique,params=taguchi", "RL:imit-ft|faisceau=5,k=4"]]),
    "P1": dict(titre="Pilote pannes permises (déjà fait le 6/10 dans le cloud ; relance possible pour vérification)",
               cout="≈ 30 min",
               cmds=[[PY, "-m", "experiences_article1.pilote_regime_pannes", "--evaluations", "10000", "--betas", "0", "0.5", "2",
                      "--jeux", "A", "B"],
                     [PY, "-m", "experiences_article1.pilote_regime_pannes", "--evaluations", "10000", "--betas", "0", "0.5",
                      "--jeux", "A", "--rho", "1", "--graines", "0", "1", "2", "3", "4",
                      "--sortie", "experiences_article1/resultats/pilote_regime_pannes_rho1_5graines_pc.csv"]]),
}


def empreinte_code():
    h = hashlib.sha256()
    for d in ("jssp_pm", "metaheuristiques", "regles_priorite", "imitation", "outils"):
        for r, _, fs in sorted(os.walk(os.path.join(RACINE, d))):
            for f in sorted(fs):
                if f.endswith(".py"):
                    h.update(open(os.path.join(r, f), "rb").read())
    for f in ("anticiper.py", "comparer_rl.py", "cpsat_article1.py", "train_v3.py"):
        p = os.path.join(RACINE, f)
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:12]


def machine():
    info = dict(systeme=platform.platform(), processeur=platform.processor(), python=platform.python_version(),
                coeurs_logiques=os.cpu_count())
    for mod in ("numpy", "torch", "numba", "ortools", "scipy"):
        try:
            info[mod] = __import__(mod).__version__
        except Exception:
            info[mod] = None
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--etape", nargs="*", default=[])
    ap.add_argument("--liste", action="store_true")
    ap.add_argument("--essai", action="store_true", help="afficher les commandes sans les lancer")
    ap.add_argument("--processus", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    a = ap.parse_args()
    if a.liste or not a.etape:
        for k, e in ETAPES.items():
            print(f"{k:4s} {e['titre']}\n     coût estimé : {e['cout']} ; {len(e['cmds'])} commande(s)")
        return
    os.makedirs(os.path.join(ICI, "journaux"), exist_ok=True)
    emp, mach = empreinte_code(), machine()
    for k in a.etape:
        e = ETAPES[k]
        dossiers = e.get("dossiers", [e.get("dossier", ".")] * len(e["cmds"]))   # un dossier par commande (E10s)
        print(f"=== {k} : {e['titre']} (code {emp})", flush=True)
        for c, dos in zip(e["cmds"], dossiers):
            cwd = os.path.normpath(os.path.join(RACINE, dos))
            c = [x.replace("{P}", str(a.processus)).replace("{P4}", str(max(1, a.processus // 2))) for x in c]
            print("  $", " ".join(f'"{x}"' if " " in x else x for x in c), flush=True)
            if a.essai:
                continue
            t0 = time.time()
            with open(os.path.join(ICI, "journaux", f"{k}.log"), "a", encoding="utf-8", errors="replace") as log:
                log.write(f"\n### {datetime.datetime.now().isoformat(timespec='seconds')} {' '.join(c)}\n")
                log.flush()
                rc = subprocess.call(c, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                     env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            with open(os.path.join(ICI, "journaux", "executions.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(dict(etape=k, date=datetime.datetime.now().isoformat(timespec="seconds"),
                                        code=emp, machine=mach, commande=c, duree_s=round(time.time() - t0, 1),
                                        retour=rc), ensure_ascii=False) + "\n")
            print(f"    -> retour {rc}, {time.time() - t0:.0f} s", flush=True)
            if rc != 0:
                sys.exit(f"échec de l'étape {k} : voir experiences_article1/journaux/{k}.log")


if __name__ == "__main__":
    main()
