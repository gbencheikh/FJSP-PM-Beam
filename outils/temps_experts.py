"""Coût hors ligne des plannings experts (2e relecture, M13 ; 03/11/2026) : temps d'un expert (règle MWKR+EFT puis recuit
50 000 évaluations, imitation.experts.un_expert) mesuré sur un processus pour les 40 premières instances (20 base, 20 large),
puis extrapolé aux 2 000 instances (moyenne par classe de taille × 1 000). Paramètres du recuit : ceux de la génération
(Taguchi si --parametres est donné ; vérifier dans le journal de génération lesquels ont été utilisés).
  python -m outils.temps_experts --parametres reglage_taguchi/parametres_retenus.json
  -> experiences_article1/resultats/temps_experts.md
"""
import argparse, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from imitation.experts import un_expert, parametres_recuit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parametres", default=None)
    ap.add_argument("--nombre", type=int, default=40)
    a = ap.parse_args()
    params = parametres_recuit(a.parametres)
    T = {"base": [], "large": []}
    for i in range(a.nombre):
        t0 = time.perf_counter()
        r = un_expert((i, "A", 50000, params))
        T[r["dist"]].append(time.perf_counter() - t0)
    tot_h = sum(np.mean(v) * 1000 for v in T.values()) / 3600
    md = ["# Coût des 2 000 plannings experts (estimation, un processus)\n",
          *[f"- {d} : {len(v)} instances, {np.mean(v):.1f} s en moyenne (min {min(v):.1f}, max {max(v):.1f})" for d, v in T.items()],
          f"- Total estimé pour 1 000 base + 1 000 large : **{tot_h:.1f} h CPU** sur un processus."]
    open(os.path.join("experiences_article1", "resultats", "temps_experts.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
