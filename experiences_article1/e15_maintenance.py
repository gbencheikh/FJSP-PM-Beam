"""E15 — Valeur de la décision de maintenance en régime A (seuils connus, aucune panne).

Question : à ordre des opérations et affectation des machines FIGÉS, combien vaut le seul placement
des maintenances, et par quel mécanisme ?

Pour chaque instance et chaque planning source (un planning de la banque : recuit Taguchi, agent 5×4…) :
  1. on extrait la séquence de chaque machine et l'affectation (les maintenances sont retirées) ;
  2. on re-place les maintenances selon plusieurs politiques, et on recalcule le planning semi-actif
     (chaque opération commence dès que sa machine et son job sont libres ; une maintenance placée dans
     l'intervalle qui précède une opération commence dès la fin de l'opération précédente) ;
  3. on mesure C_max, nombre de maintenances, part des maintenances « dans un temps mort » (la maintenance
     ne retarde pas l'opération suivante de la machine : le job de cette opération n'est prêt qu'après la fin
     de la maintenance) et usure moyenne au moment de la maintenance (c / T).

Politiques (une maintenance n'a de sens que si l'usure est > 0 ; une maintenance OBLIGATOIRE est toujours
ajoutée si l'opération suivante ne tient pas dans la marge, de sorte que tout planning reste faisable) :
  - « au plus tard » (juste à temps) : uniquement les maintenances obligatoires (nombre minimal, dates au plus tard) ;
  - « au plus tôt » : même nombre minimal, positions au plus tôt (remplissage des cycles depuis la fin) ;
  - « systématique » : une maintenance avant chaque opération dès que l'usure est > 0 ;
  - « source » : positions de maintenance du planning source (celles choisies par le recuit ou l'agent) ;
  - « aléatoire » (politique nulle) : chaque position facultative reçoit une maintenance avec probabilité 1/2,
    100 tirages (graines 0–99) ; on rapporte la moyenne et le meilleur des 100 ;
  - « recuit sur le placement seul » : recuit simulé sur le vecteur binaire des positions facultatives
    (voisin = basculer une position), objectif C_max, 20 000 évaluations, 5 graines (0–4), départ « au plus tard ».
    Borne pratique de E15 : sépare le gain du placement de celui de l'ordonnancement.

Unité statistique : l'instance (protocole, § 4). Référence des écarts : « au plus tard » sur la même séquence.
Mécanisme : pour chaque instance, corrélation de Spearman entre une variable explicative et le C_max, sur
tous les placements évalués (tirages aléatoires + politiques) : (i) part des maintenances dans un temps mort
(variable prévue), (ii) nombre de maintenances qui retardent l'opération suivante, (iii) nombre total de
maintenances ; on rapporte la médiane des corrélations et la part des instances où elle est de signe attendu et
significative (p < 0,05) ; figure groupée en C_max normalisé (C_max / C_max au plus tard).

  python -m experiences_article1.e15_maintenance --familles Brandimarte HurinkLa Kacem \
         --sources "Recuit simulé|evals=50000,depart=heuristique,params=taguchi" "RL:imit-ft|faisceau=5,k=4"
"""
import argparse, csv, json, math, os, sys, time
from collections import defaultdict

import numpy as np
try:                                   # console Windows (cp1252) : ne pas planter sur « − », « ≤ »…
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, RACINE)
from metaheuristiques.instances import charger_instances      # noqa: E402
from banque_resultats import banque                           # noqa: E402

try:
    from numba import njit
except ImportError:                                           # repli sans numba (plus lent)
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]

PROC, PM = 1, 2
N_ALEA, N_EVAL_SA, GRAINES_SA = 100, 20000, (0, 1, 2, 3, 4)


@njit(cache=True)
def decoder(mseq, mdeb, mnb, MS, op_job, op_pos, P, T, M, x, nj):
    """Planning semi-actif. x[i] = 1 : maintenance facultative avant l'op mseq[i] (si usure > 0).
    Retourne (C_max, nb de maintenances, nb dans un temps mort, somme des c/T au moment des maintenances)."""
    m = mnb.shape[0]
    ptr = np.zeros(m, np.int64)
    mfree = np.zeros(m)
    wear = np.zeros(m)
    jready = np.zeros(nj)
    jnext = np.zeros(nj, np.int64)
    npm, nidle, swear = 0, 0, 0.0
    total = mseq.shape[0]
    fait = 0
    while fait < total:
        progres = False
        for k in range(m):
            while ptr[k] < mnb[k]:
                i = mdeb[k] + ptr[k]
                o = mseq[i]
                j = op_job[o]
                if op_pos[o] != jnext[j]:
                    break
                p = P[o, k]
                t = mfree[k]
                if wear[k] > 1e-9 and (x[i] == 1 or wear[k] + p > T[k] + 1e-9):
                    fin_pm = t + M[k]
                    npm += 1
                    swear += wear[k] / T[k]
                    if jready[j] >= fin_pm - 1e-9:
                        nidle += 1
                    t = fin_pm
                    wear[k] = 0.0
                debut = t if t > jready[j] else jready[j]
                mfree[k] = debut + p
                jready[j] = debut + p
                wear[k] += p
                jnext[j] += 1
                ptr[k] += 1
                fait += 1
                progres = True
        if not progres:
            return -1.0, 0, 0, 0.0                     # séquence incohérente (ne doit pas arriver)
    cmax = 0.0
    for j in range(nj):
        if jready[j] > cmax:
            cmax = jready[j]
    return cmax, npm, nidle, swear


@njit(cache=True)
def recuit_placement(mseq, mdeb, mnb, MS, op_job, op_pos, P, T, M, x0, libres, nj, n_eval, graine,
                     p0=0.05, ratio_fin=1e-3):
    np.random.seed(graine)
    x = x0.copy()
    c = decoder(mseq, mdeb, mnb, MS, op_job, op_pos, P, T, M, x, nj)[0]
    best, bx = c, x.copy()
    if libres.shape[0] == 0:
        return best, bx
    somme, nb = 0.0, 0
    for _ in range(30):
        i = libres[np.random.randint(libres.shape[0])]
        x[i] = 1 - x[i]
        d = decoder(mseq, mdeb, mnb, MS, op_job, op_pos, P, T, M, x, nj)[0] - c
        x[i] = 1 - x[i]
        if d > 0:
            somme += d
            nb += 1
    T0 = (somme / nb if nb > 0 else 1.0) / -np.log(p0)
    for it in range(n_eval):
        i = libres[np.random.randint(libres.shape[0])]
        x[i] = 1 - x[i]
        c2 = decoder(mseq, mdeb, mnb, MS, op_job, op_pos, P, T, M, x, nj)[0]
        d = c2 - c
        temp = T0 * ratio_fin ** (it / n_eval)
        if d <= 0 or np.random.random() < np.exp(-d / max(temp, 1e-12)):
            c = c2
            if c < best:
                best, bx = c, x.copy()
        else:
            x[i] = 1 - x[i]
    return best, bx


class Sequence:
    """Séquences machines et affectation extraites d'un planning (maintenances retirées)."""

    def __init__(self, inst, plan):
        self.inst = inst
        n_ops, m = inst.P.shape
        self.op_job = np.zeros(n_ops, np.int64)
        self.op_pos = np.zeros(n_ops, np.int64)
        for j, ops in enumerate(inst.job_ops):
            for q, o in enumerate(ops):
                self.op_job[o], self.op_pos[o] = j, q
        par_job = defaultdict(list)
        for k, a, b, typ, j in plan:
            if int(typ) == PROC:
                par_job[int(j)].append((float(a), int(k)))
        self.MS = np.zeros(n_ops, np.int64)
        par_machine = defaultdict(list)
        for j, lst in par_job.items():
            lst.sort()
            assert len(lst) == len(inst.job_ops[j]), "planning avec opérations coupées (panne) : hors régime A"
            for (a, k), o in zip(lst, inst.job_ops[j]):
                self.MS[o] = k
                par_machine[k].append((a, o))
        seqs = [[o for a, o in sorted(par_machine[k])] for k in range(m)]
        self.mnb = np.array([len(s) for s in seqs], np.int64)
        self.mdeb = np.concatenate([[0], np.cumsum(self.mnb)[:-1]]).astype(np.int64)
        self.mseq = np.array([o for s in seqs for o in s], np.int64)
        self.libres = np.array([self.mdeb[k] + q for k in range(m) for q in range(1, self.mnb[k])], np.int64)
        self.P = np.asarray(inst.P, np.float64)
        self.T = np.asarray(inst.T, np.float64)
        self.M = np.asarray(inst.M, np.float64)
        # positions de maintenance du planning source : maintenance entre deux opérations consécutives de k
        self.x_source = np.zeros(len(self.mseq), np.int64)
        pms = defaultdict(list)
        for k, a, b, typ, j in plan:
            if int(typ) == PM:
                pms[int(k)].append(float(a))
        debut = {o: a for j, lst in par_job.items() for (a, k), o in zip(sorted(lst), inst.job_ops[j])}
        for k in range(m):
            for q in range(1, self.mnb[k]):
                o_prec, o = self.mseq[self.mdeb[k] + q - 1], self.mseq[self.mdeb[k] + q]
                fin_prec = debut[o_prec] + self.P[o_prec, k]
                if any(fin_prec - 1e-6 <= t <= debut[o] + 1e-6 for t in pms[k]):
                    self.x_source[self.mdeb[k] + q] = 1

    def evaluer(self, x):
        c, npm, nidle, sw = decoder(self.mseq, self.mdeb, self.mnb, self.MS, self.op_job, self.op_pos,
                                    self.P, self.T, self.M, x, self.inst.n)
        return dict(cmax=float(c), maintenances=int(npm), dans_temps_mort=int(nidle),
                    retardantes=int(npm - nidle),
                    part_temps_mort=(nidle / npm) if npm else float("nan"),
                    usure_moyenne=(sw / npm) if npm else float("nan"))

    def x_au_plus_tot(self):
        """Nombre minimal de maintenances, positions au plus tôt : cycles remplis depuis la fin."""
        x = np.zeros(len(self.mseq), np.int64)
        for k in range(len(self.mnb)):
            charge = 0.0
            for q in range(self.mnb[k] - 1, -1, -1):
                o = self.mseq[self.mdeb[k] + q]
                p = self.P[o, k]
                if charge + p > self.T[k] + 1e-9:
                    x[self.mdeb[k] + q + 1] = 1          # maintenance juste avant l'op q+1
                    charge = 0.0
                charge += p
        return x

    def x_systematique(self):
        x = np.zeros(len(self.mseq), np.int64)
        x[self.libres] = 1
        return x


def spearman(a, b):
    from scipy.stats import spearmanr
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b))
    if ok.sum() < 5 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return float("nan"), float("nan")
    r = spearmanr(a[ok], b[ok])
    return float(r.correlation), float(r.pvalue)


def plan_source(nom, methode, config, graine=0):
    for r in banque.charger():
        if (r["instance"] == nom and r["regime"] == "A" and abs(float(r["facteur_seuil"]) - 1.0) < 1e-9
                and r["methode"] == methode and r["config"] == config and int(r["graine"]) == graine
                and r["solution"]):
            p = banque.planning(r)
            if p:
                return p, float(r["cmax"])
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familles", nargs="+", default=["Brandimarte", "HurinkLa", "Kacem"])
    ap.add_argument("--sources", nargs="+", default=["Recuit simulé|evals=50000,depart=heuristique,params=taguchi",
                                                    "RL:imit-ft|faisceau=5,k=4"])
    ap.add_argument("--n-alea", type=int, default=N_ALEA)
    ap.add_argument("--evaluations", type=int, default=N_EVAL_SA)
    ap.add_argument("--graines-recuit", type=int, nargs="+", default=list(GRAINES_SA))
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats", "e15"))
    ap.add_argument("--resumer-seulement", action="store_true",
                    help="refaire seulement les tableaux à partir de <sortie>_details.csv (sans recalcul)")
    ap.add_argument("--inclure-reglage", action="store_true",
                    help="garder les instances du réglage Taguchi (exclues par défaut, protocole § 2)")
    a = ap.parse_args()
    if a.resumer_seulement:
        num = ("cmax", "maintenances", "dans_temps_mort", "retardantes", "part_temps_mort", "usure_moyenne")
        lignes = [{k: (float(v) if k in num and v != "" else (float("nan") if k in num else v)) for k, v in r.items()}
                  for r in csv.DictReader(open(a.sortie + "_details.csv", encoding="utf-8"))]
        resumer(lignes, [], a)
        return
    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    instances = charger_instances(a.familles, regime="A", facteur_seuil=1.0)
    lignes, controles = [], []
    for src in a.sources:
        meth, cfg = src.split("|", 1)
        for inst in instances:
            plan, c_banque = plan_source(inst.name, meth, cfg)
            if plan is None:
                continue
            t0 = time.time()
            s = Sequence(inst, plan)
            base = dict(instance=inst.name, source=src)
            pol = {"au plus tard": np.zeros(len(s.mseq), np.int64), "au plus tôt": s.x_au_plus_tot(),
                   "systématique": s.x_systematique(), "source": s.x_source}
            for nom, x in pol.items():
                lignes.append(dict(base, politique=nom, tirage="", **s.evaluer(x)))
            rsrc = lignes[-1]
            controles.append(dict(instance=inst.name, source=src, cmax_banque=c_banque, cmax_redecode=rsrc["cmax"]))
            for g in range(a.n_alea):
                rng = np.random.default_rng(g)
                x = np.zeros(len(s.mseq), np.int64)
                x[s.libres] = rng.random(len(s.libres)) < 0.5
                lignes.append(dict(base, politique="aléatoire", tirage=g, **s.evaluer(x)))
            for g in a.graines_recuit:
                c, bx = recuit_placement(s.mseq, s.mdeb, s.mnb, s.MS, s.op_job, s.op_pos, s.P, s.T, s.M,
                                         np.zeros(len(s.mseq), np.int64), s.libres, inst.n, a.evaluations, g)
                lignes.append(dict(base, politique="recuit placement", tirage=g, **s.evaluer(bx)))
            print(f"{src} {inst.name} : au plus tard {lignes[-a.n_alea - len(a.graines_recuit) - 4]['cmax']:g}, "
                  f"source {rsrc['cmax']:g} (banque {c_banque:g}), recuit placement "
                  f"{min(l['cmax'] for l in lignes[-len(a.graines_recuit):]):g} ({time.time() - t0:.1f} s)", flush=True)

    with open(a.sortie + "_details.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0])); w.writeheader(); w.writerows(lignes)
    resumer(lignes, controles, a)


def resumer(lignes, controles, a):
    from experiences_article1.statistiques import bootstrap_ic, wilcoxon, holm, INSTANCES_REGLAGE
    exclues = sorted({l["instance"] for l in lignes if l["instance"] in INSTANCES_REGLAGE}) \
        if not getattr(a, "inclure_reglage", False) else []
    lignes = [l for l in lignes if l["instance"] not in exclues]
    md = ["# E15 — valeur de la décision de maintenance (ordre et affectation figés)\n",
          f"Politiques : au plus tard (référence), au plus tôt, systématique, source, aléatoire ({a.n_alea} tirages, "
          f"p = 1/2), recuit sur le placement seul ({a.evaluations} évaluations, graines {a.graines_recuit}). "
          "Unité : l'instance ; écart = C_max / C_max(au plus tard) − 1 ; IC bootstrap 95 % ; Wilcoxon apparié, Holm.\n"]
    if exclues:
        md.append(f"Instances exclues (réglage Taguchi) : {', '.join(exclues)}.\n")
    ok = [c for c in controles if c["cmax_redecode"] > c["cmax_banque"] + 1e-6]
    if controles:
        md.append(f"Contrôle du redécodage semi-actif : {len(controles) - len(ok)}/{len(controles)} plannings source "
                  f"retrouvés avec un C_max ≤ celui de la banque" + (f" ; écarts : {ok[:5]}" if ok else "") + ".\n")
    else:
        md.append("Contrôle du redécodage : voir le premier calcul (journaux/E15.log) ; tableaux refaits depuis le CSV.\n")
    for src in a.sources:
        L = [l for l in lignes if l["source"] == src]
        noms = sorted({l["instance"] for l in L})
        if not noms:
            continue
        ref = {n: next(l["cmax"] for l in L if l["instance"] == n and l["politique"] == "au plus tard") for n in noms}
        def agg(pol, f):
            return np.array([f([l for l in L if l["instance"] == n and l["politique"] == pol]) for n in noms])
        moy = lambda g: np.mean([l["cmax"] for l in g])
        meil = lambda g: np.min([l["cmax"] for l in g])
        cols = [("Au plus tôt", "au plus tôt", moy), ("Systématique", "systématique", moy),
                ("Source", "source", moy), ("Aléatoire (moyenne)", "aléatoire", moy),
                ("Aléatoire (meilleur des tirages)", "aléatoire", meil),
                ("Recuit placement (moyenne des graines)", "recuit placement", moy),
                ("Recuit placement (meilleure graine)", "recuit placement", meil)]
        r = np.array([ref[n] for n in noms])
        res, ps = [], []
        for lab, pol, f in cols:
            v = agg(pol, f)
            gap = 100 * (v / r - 1)
            ic = bootstrap_ic(gap)
            p = wilcoxon(v, r)
            ps.append(p)
            npm = agg(pol, lambda g: np.mean([l["maintenances"] for l in g]))
            part = agg(pol, lambda g: np.nanmean([l["part_temps_mort"] for l in g]))
            us = agg(pol, lambda g: np.nanmean([l["usure_moyenne"] for l in g]))
            d = v - r
            res.append((lab, gap.mean(), ic, np.median(gap), (d < -1e-9).sum(), (abs(d) <= 1e-9).sum(), (d > 1e-9).sum(),
                        npm.mean(), np.nanmean(part), np.nanmean(us)))
        ref_npm = agg("au plus tard", lambda g: g[0]["maintenances"]).mean()
        ref_part = np.nanmean(agg("au plus tard", lambda g: g[0]["part_temps_mort"]))
        ref_us = np.nanmean(agg("au plus tard", lambda g: g[0]["usure_moyenne"]))
        md += [f"\n## Source : {src} ({len(noms)} instances)\n",
               "| Politique | Écart moyen | IC 95 % | Médiane | V/E/D | p (Holm) | Maint./inst. | Part dans un temps mort | Usure c/T |",
               "|---|---|---|---|---|---|---|---|---|",
               f"| Au plus tard (référence) | 0 | | | | | {ref_npm:.1f} | {100 * ref_part:.0f} % | {ref_us:.2f} |"]
        for row, ph in zip(res, holm(ps)):
            lab, g, ic, med, V, E, D, npm, part, us = row
            md.append(f"| {lab} | {g:+.2f} % | [{ic[0]:+.2f} ; {ic[1]:+.2f}] | {med:+.2f} % | {V}/{E}/{D} | {ph:.2g} | "
                      f"{npm:.1f} | {100 * part:.0f} % | {us:.2f} |")
        # mécanisme
        npl = a.n_alea + 4 + len(a.graines_recuit)
        xs, ys, xr = [], [], []
        for var, signe, lab in (("part_temps_mort", -1, "part des maintenances dans un temps mort"),
                                ("retardantes", +1, "nombre de maintenances qui retardent l'opération suivante"),
                                ("maintenances", +1, "nombre total de maintenances")):
            rhos, sig = [], 0
            for n in noms:
                g = [l for l in L if l["instance"] == n]
                rho, p = spearman([l[var] for l in g], [l["cmax"] for l in g])
                if not math.isnan(rho):
                    rhos.append(rho)
                    sig += int(np.sign(rho) == signe and p < 0.05)
            md.append(f"\nMécanisme — Spearman({lab}, C_max) par instance, {npl} placements : médiane "
                      f"{np.median(rhos):+.2f} ; de signe attendu ({'négatif' if signe < 0 else 'positif'}) et significatif "
                      f"(p < 0,05) sur {sig}/{len(rhos)} instances." if rhos else f"\nMécanisme ({lab}) : non calculable.")
        for n in noms:
            g = [l for l in L if l["instance"] == n]
            xs += [l["part_temps_mort"] for l in g]
            xr += [l["retardantes"] for l in g]
            ys += [l["cmax"] / ref[n] for l in g]
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, axs = plt.subplots(1, 2, figsize=(8, 3.4), sharey=True)
            axs[0].scatter(xs, ys, s=4, alpha=0.25)
            axs[0].set_xlabel("Share of maintenances placed in idle time")
            axs[1].scatter(xr, ys, s=4, alpha=0.25)
            axs[1].set_xlabel("Maintenances delaying the next operation")
            axs[0].set_ylabel("C_max / C_max (latest placement)")
            fig.tight_layout()
            nomfig = a.sortie + "_mecanisme_" + ("recuit" if "Recuit" in src else "agent")
            fig.savefig(nomfig + ".png", dpi=200); fig.savefig(nomfig + ".pdf")
        except ImportError:
            pass
    open(a.sortie + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
