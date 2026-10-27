"""Réglage des paramètres des métaheuristiques par la méthode de Taguchi (tableau orthogonal L9).

  python -m reglage_taguchi.taguchi --processus 10                  # les 3 méthodes
  python -m reglage_taguchi.taguchi --methodes "Recuit simulé" --evaluations 20000

Principe
  1. Chaque méthode a 2 à 4 paramètres, chacun testé à 3 niveaux (tableau FACTEURS ci-dessous).
  2. Au lieu des 3^4 = 81 combinaisons, on n'en teste que 9, choisies par le tableau orthogonal L9 :
     chaque niveau de chaque paramètre apparaît 3 fois, et chaque paire de niveaux de deux paramètres
     apparaît exactement une fois.
  3. Chaque combinaison est lancée sur des instances DE RÉGLAGE (Hurink non utilisées pour les
     comparaisons finales) avec plusieurs graines, à budget égal en nombre d'évaluations.
  4. Réponse : y = C_max / C_max(MWKR+EFT) (makespan relatif à une règle de référence, pour que
     chaque instance pèse autant). Rapport signal/bruit « plus petit est meilleur » :
            S/N = -10 · log10( moyenne(y²) )        (plus grand = meilleur ET plus stable)
  5. Effet de chaque niveau = S/N moyen des 3 lignes qui l'utilisent. On retient, pour chaque
     paramètre, le niveau au S/N le plus élevé. ANOVA sur S/N : contribution (%) de chaque paramètre.
  6. Confirmation : la combinaison retenue (souvent absente des 9 lignes) et la combinaison par
     défaut sont relancées ; on compare leur S/N au S/N prédit.

Sorties (dossier reglage_taguchi/) :
  essais.csv                 toutes les exécutions (reprise automatique si interrompu)
  rapport.md                 tableaux L9, effets des niveaux, ANOVA, confirmation
  parametres_retenus.json    à passer à `python -m metaheuristiques.comparer --parametres ...`
"""
import argparse, csv, json, os, sys, time
import multiprocessing as mp
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jssp_pm.fjsp_env3 import run3
from metaheuristiques import genetique, tabou, recuit_simule
from metaheuristiques.codage import Budget, depuis_planning
from metaheuristiques.instances import PARAMS
from jssp_pm.fjsp_instance import load_fjs_v3
from regles_priorite.regles import ReglePriorite, environnement

DOSSIER = os.path.dirname(os.path.abspath(__file__))

# Tableau orthogonal L9 (3^4) : 9 essais, 4 colonnes, niveaux 0/1/2.
L9 = [(0, 0, 0, 0), (0, 1, 1, 1), (0, 2, 2, 2),
      (1, 0, 1, 2), (1, 1, 2, 0), (1, 2, 0, 1),
      (2, 0, 2, 1), (2, 1, 0, 2), (2, 2, 1, 0)]

# Paramètres et niveaux testés (le niveau du milieu = valeur par défaut actuelle).
FACTEURS = {
    "Algorithme génétique": (genetique, {
        "population": [30, 60, 100],
        "p_croisement": [0.6, 0.8, 0.95],
        "p_mutation": [0.05, 0.1, 0.2],
        "elite": [1, 2, 5]}),
    "Recherche tabou": (tabou, {
        "n_voisins": [20, 40, 80],
        "tenure": [6, 12, 24]}),
    "Recuit simulé": (recuit_simule, {
        "p0": [0.3, 0.5, 0.8],
        "ratio_fin": [1e-2, 1e-3, 1e-4]}),
}

# Instances de réglage : Hurink edata/rdata NON utilisées dans les comparaisons (1, 6, 11, …, 46).
INSTANCES_REGLAGE = [f"Instances/2b_Hurink_edata/HurinkEdata{i}.fjs" for i in (3, 13, 23, 33)] + \
                    [f"Instances/2c_Hurink_rdata/HurinkRdata{i}.fjs" for i in (8, 18, 28, 38)]


def combinaisons(nom):
    """Les 9 essais L9 d'une méthode : liste de dicts {paramètre: valeur}."""
    _, fact = FACTEURS[nom]
    noms = list(fact)
    return [{p: fact[p][ligne[c]] for c, p in enumerate(noms)} for ligne in L9]


def charger(fichiers):
    out = []
    for f in fichiers:
        if not os.path.exists(f):
            raise FileNotFoundError(f"{f} introuvable : lancez le script depuis le dossier du projet")
        out.append(load_fjs_v3(f, "A", **PARAMS["A"]))
    return out


def reference(inst):
    """C_max de la règle MWKR+EFT (sert à normaliser) et point de départ commun des méthodes."""
    _, sim = run3(environnement(), ReglePriorite("MWKR", "EFT"), inst)
    return sim.last_completion, depuis_planning(inst, sim.segments)


def une_execution(args):
    nom, essai, params, inst, graine, evaluations, ref, depart = args
    module, _ = FACTEURS[nom]
    rng = np.random.default_rng(1000 + graine)
    t0 = time.time()
    cmax, _, info = module.resoudre(inst, Budget(evaluations=evaluations), rng, depart=depart, **params)
    return dict(methode=nom, essai=essai, params=json.dumps(params), instance=inst.name, graine=graine,
                cmax=float(cmax), y=float(cmax) / ref, temps_s=round(time.time() - t0, 2))


def sn(ys):
    ys = np.asarray(ys, float)
    return -10 * np.log10(np.mean(ys ** 2))


def analyser(nom, lignes, md):
    _, fact = FACTEURS[nom]
    noms = list(fact)
    combis = combinaisons(nom)
    sn_essai = [sn([l["y"] for l in lignes if l["essai"] == str(e)]) for e in range(9)]
    moy_essai = [np.mean([l["y"] for l in lignes if l["essai"] == str(e)]) for e in range(9)]
    moyenne = float(np.mean(sn_essai))
    md.append(f"\n## {nom}\n")
    md.append("### Les 9 essais du tableau L9\n")
    md.append("| Essai | " + " | ".join(noms) + " | C_max relatif moyen | S/N (dB) |")
    md.append("|" + "---|" * (len(noms) + 3))
    for e, c in enumerate(combis):
        md.append(f"| {e + 1} | " + " | ".join(f"{c[p]:g}" for p in noms)
                  + f" | {moy_essai[e]:.4f} | {sn_essai[e]:.3f} |")
    # effets des niveaux + ANOVA sur S/N
    effets, ss, retenu = {}, {}, {}
    for c, p in enumerate(noms):
        niv = [np.mean([sn_essai[e] for e in range(9) if L9[e][c] == n]) for n in range(3)]
        effets[p] = niv
        ss[p] = 3 * sum((v - moyenne) ** 2 for v in niv)
        retenu[p] = fact[p][int(np.argmax(niv))]
    ss_total = sum((v - moyenne) ** 2 for v in sn_essai)
    md.append("\n### Effet de chaque niveau (S/N moyen, dB) et contribution\n")
    md.append("| Paramètre | Niveau 1 | Niveau 2 | Niveau 3 | Écart max. | Contribution (ANOVA) | Niveau retenu |")
    md.append("|---|---|---|---|---|---|---|")
    for p in sorted(noms, key=lambda p: -ss[p]):
        v = effets[p]
        md.append(f"| {p} | {fact[p][0]:g} : {v[0]:.3f} | {fact[p][1]:g} : {v[1]:.3f} | "
                  f"{fact[p][2]:g} : {v[2]:.3f} | {max(v) - min(v):.3f} | "
                  f"{100 * ss[p] / ss_total if ss_total > 0 else 0:.1f} % | **{retenu[p]:g}** |")
    if len(noms) < 4:
        md.append(f"\nPart non expliquée par les paramètres (interactions + bruit) : "
                  f"{max(0.0, 100 * (1 - sum(ss.values()) / ss_total)) if ss_total > 0 else 0:.1f} %.")
    predit = moyenne + sum(max(effets[p]) - moyenne for p in noms)
    return retenu, predit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--methodes", nargs="+", default=list(FACTEURS))
    ap.add_argument("--evaluations", type=int, default=50000)
    ap.add_argument("--graines", nargs="+", type=int, default=[0, 1])
    ap.add_argument("--instances", nargs="+", default=INSTANCES_REGLAGE)
    ap.add_argument("--processus", type=int, default=2)
    a = ap.parse_args()
    fichier = os.path.join(DOSSIER, "essais.csv")
    insts = charger(a.instances)
    refs = {i.name: reference(i) for i in insts}
    colonnes = ["methode", "essai", "params", "instance", "graine", "cmax", "y", "temps_s", "evaluations"]
    deja = []
    if os.path.exists(fichier):
        with open(fichier, newline="", encoding="utf-8") as f:
            deja = list(csv.DictReader(f))
    fait = {(l["methode"], l["essai"], l["instance"], l["graine"], l["evaluations"]) for l in deja}

    def taches(nom, essais):
        return [(nom, e, params, i, g, a.evaluations, refs[i.name][0], refs[i.name][1])
                for e, params in essais for i in insts for g in a.graines
                if (nom, str(e), i.name, str(g), str(a.evaluations)) not in fait]

    def lancer(t):
        if not t:
            return
        nouveau = not os.path.exists(fichier)
        ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
        with ctx.Pool(a.processus) as pool, open(fichier, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=colonnes)
            if nouveau:
                w.writeheader()
            for k, r in enumerate(pool.imap_unordered(une_execution, t), 1):
                r["evaluations"] = a.evaluations
                w.writerow(r)
                f.flush()
                if k % 10 == 0 or k == len(t):
                    print(f"  {k}/{len(t)}", flush=True)

    # 1) les 9 essais L9 de chaque méthode
    for nom in a.methodes:
        t = taches(nom, list(enumerate(combinaisons(nom))))
        print(f"{nom} : {len(t)} exécutions à lancer", flush=True)
        lancer(t)

    def lire():
        with open(fichier, newline="", encoding="utf-8") as f:
            return [dict(l, y=float(l["y"])) for l in csv.DictReader(f)
                    if l["evaluations"] == str(a.evaluations) and l["instance"] in refs
                    and int(l["graine"]) in a.graines]

    md = ["# Réglage des métaheuristiques par la méthode de Taguchi\n",
          f"Tableau orthogonal L9 ; {len(insts)} instances de réglage "
          f"({', '.join(i.name for i in insts)}) ; graines {a.graines} ; "
          f"{a.evaluations} évaluations par exécution ; départ MWKR+EFT.",
          "Réponse : C_max relatif à MWKR+EFT (plus petit = meilleur). "
          "S/N = −10·log10(moyenne des y²), plus grand = meilleur et plus stable."]
    retenus, confirm = {}, []
    lignes = lire()
    for nom in a.methodes:
        retenu, predit = analyser(nom, [l for l in lignes if l["methode"] == nom], md)
        retenus[nom] = retenu
        _, fact = FACTEURS[nom]
        defaut = {p: v[1] for p, v in fact.items()}
        confirm.append((nom, retenu, defaut, predit))

    # 2) confirmation : combinaison retenue (essai 100) et combinaison par défaut (essai 101)
    for nom, retenu, defaut, _ in confirm:
        lancer(taches(nom, [(100, retenu), (101, defaut)]))
    lignes = lire()
    md.append("\n## Confirmation\n")
    md.append("| Méthode | Paramètres retenus | S/N prédit | S/N obtenu (retenus) | S/N par défaut | "
              "C_max relatif retenus | C_max relatif défaut | Décision |")
    md.append("|---|---|---|---|---|---|---|---|")
    final = {}
    for nom, retenu, defaut, predit in confirm:
        yr = [l["y"] for l in lignes if l["methode"] == nom and l["essai"] == "100"]
        yd = [l["y"] for l in lignes if l["methode"] == nom and l["essai"] == "101"]
        garde = sn(yr) >= sn(yd)
        final[nom] = retenu if garde else defaut
        md.append(f"| {nom} | {', '.join(f'{k}={v:g}' for k, v in retenu.items())} | {predit:.3f} | "
                  f"{sn(yr):.3f} | {sn(yd):.3f} | {np.mean(yr):.4f} | {np.mean(yd):.4f} | "
                  f"{'retenus' if garde else 'défaut conservé'} |")
    md.append("\nSi le S/N obtenu est proche du S/N prédit, l'hypothèse de Taguchi (peu d'interactions "
              "entre paramètres) est raisonnable. Si les paramètres retenus ne battent pas les valeurs "
              "par défaut, les valeurs par défaut sont conservées dans parametres_retenus.json.")
    open(os.path.join(DOSSIER, "rapport.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    with open(os.path.join(DOSSIER, "parametres_retenus.json"), "w", encoding="utf-8") as f:
        json.dump(final, f, indent=1, ensure_ascii=False)
    print("\n".join(md))


if __name__ == "__main__":
    main()
