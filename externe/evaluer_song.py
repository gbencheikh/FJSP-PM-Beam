"""Évaluation du modèle publié de Song et al. (IEEE TII 19(2):1600–1610, 2023, DOI 10.1109/TII.2022.3189725)
sur les instances publiques, SANS modifier leur code (dépôt songwenas12/fjsp-drl, commit dans
fjsp-drl/COMMIT_SOURCE.txt, licence Apache-2.0).

Différences avec leur test.py, toutes sans effet attendu sur les plannings :
  - une ligne de next_time corrigée pour les versions récentes de PyTorch (voir _next_time_corrige) ;
  - gym remplacé par un module minimal (leur code n'en utilise que la classe de base et l'enregistrement) ;
  - CPU, sans pynvml ni sortie Excel ; résultats en CSV ;
  - environnement créé directement (FJSPEnv) au lieu de gym.make ;
  - noms d'instances convertis vers ceux du projet (correspondance_instances_song.csv).
Modes : glouton (DRL-G, déterministe, 1 exécution, temps = moyenne de 10 comme dans leur protocole)
et échantillonnage (DRL-S, 100 solutions, meilleure gardée) pour plusieurs graines.

  cd externe
  python evaluer_song.py --graines 0 1 2 3 4                     # -> resultats_song.csv
"""
import argparse, copy, csv, json, os, random, sys, time

import numpy as np
import torch

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.join(ICI, "fjsp-drl")
sys.path.insert(0, DEPOT)
# Leur environnement hérite de gym.Env et s'enregistre auprès de gym, sans utiliser d'autre fonction de gym.
# Un module minimal remplace gym (les anciennes versions de gym ne s'installent plus avec les outils récents).
import types                                       # noqa: E402
if "gym" not in sys.modules:
    _gym = types.ModuleType("gym"); _gym.Env = object
    _envs = types.ModuleType("gym.envs"); _reg = types.ModuleType("gym.envs.registration")
    _reg.register = lambda **kw: None
    _gym.envs, _envs.registration = _envs, _reg
    sys.modules.update({"gym": _gym, "gym.envs": _envs, "gym.envs.registration": _reg})
import PPO_model                                   # noqa: E402
from env.fjsp_env import FJSPEnv                   # noqa: E402
from env.load_data import nums_detec               # noqa: E402


def _next_time_corrige(self, flag_trans_2_next_time):
    """Copie de FJSPEnv.next_time (env/fjsp_env.py, l. 323–360) avec UNE ligne corrigée.

    Leur ligne `aa = machines_batch.transpose(1, 2); aa[d, 0] = 1` applique un masque (lot, machines)
    à un tenseur (lot, 4, machines) : refusé par les versions récentes de PyTorch (IndexError).
    Intention évidente (commentaire et suite du code) : les machines qui viennent de finir redeviennent
    libres, soit machines_batch[:, :, 0][d] = 1. La fidélité est contrôlée par la reproduction des
    moyennes publiées (tableau V : mk, DRL 10×5 glouton 201,00).
    """
    flag_need_trans = (flag_trans_2_next_time == 0) & (~self.done_batch)
    a = self.machines_batch[:, :, 1]
    b = torch.where(a > self.time[:, None], a, torch.max(self.feat_opes_batch[:, 4, :]) + 1.0)
    c = torch.min(b, dim=1)[0]
    d = torch.where((a == c[:, None]) & (self.machines_batch[:, :, 0] == 0) & flag_need_trans[:, None], True, False)
    e = torch.where(flag_need_trans, c, self.time)
    self.time = e
    etat = self.machines_batch[:, :, 0]
    etat[d] = 1                                          # <- seule ligne modifiée
    self.machines_batch[:, :, 0] = etat
    utiliz = self.machines_batch[:, :, 2]
    cur_time = self.time[:, None].expand_as(utiliz)
    utiliz = torch.minimum(utiliz, cur_time)
    utiliz = utiliz.div(self.time[:, None] + 1e-5)
    self.feat_mas_batch[:, 2, :] = utiliz
    jobs = torch.where(d, self.machines_batch[:, :, 3].double(), -1.0).float()
    jobs_index = np.argwhere(jobs.cpu() >= 0).to(self.device)
    job_idxes = jobs[jobs_index[0], jobs_index[1]].long()
    batch_idxes = jobs_index[0]
    self.mask_job_procing_batch[batch_idxes, job_idxes] = False
    self.mask_ma_procing_batch[d] = False
    self.mask_job_finish_batch = torch.where(self.ope_step_batch == self.end_ope_biases_batch + 1,
                                             True, self.mask_job_finish_batch)


def graine(s):
    torch.manual_seed(s); np.random.seed(s); random.seed(s)


def resoudre(env, model, echantillon):
    state, dones = env.state, env.done_batch
    memories = PPO_model.Memory()
    t0 = time.perf_counter()
    while not dones.all():
        with torch.no_grad():
            actions = model.policy_old.act(state, memories, dones, flag_sample=echantillon, flag_train=False)
        state, _, dones = env.step(actions)
    dt = time.perf_counter() - t0
    assert env.validate_gantt()[0], "planning invalide"
    return float(torch.min(env.makespan_batch)), dt


_CTX = {}


def _preparer(modele, threads, sans_correctif):
    """Charge le modèle une fois par processus (appelé aussi dans chaque processus fils)."""
    if not sans_correctif:
        FJSPEnv.next_time = _next_time_corrige
    torch.set_default_tensor_type("torch.FloatTensor")
    torch.set_num_threads(threads)
    cfg = json.load(open(os.path.join(DEPOT, "config.json")))
    env_p, model_p, train_p = cfg["env_paras"], cfg["model_paras"], cfg["train_paras"]
    env_p["device"] = model_p["device"] = torch.device("cpu")
    model_p["actor_in_dim"] = model_p["out_size_ma"] * 2 + model_p["out_size_ope"] * 2
    model_p["critic_in_dim"] = model_p["out_size_ma"] + model_p["out_size_ope"]
    model = PPO_model.PPO(model_p, train_p)
    etat = torch.load(modele, map_location="cpu")
    model.policy.load_state_dict(etat); model.policy_old.load_state_dict(etat)
    _CTX.update(model=model, env_p=env_p)


def evaluer_instance(r, graines, n_ech, rep_glouton):
    """Glouton (temps = moyenne de rep_glouton exécutions) puis n_ech échantillons pour chaque graine."""
    model, env_p = _CTX["model"], _CTX["env_p"]
    f = os.path.join(DEPOT, "data_test", "Public", r["instance_song"] + ".fjs")
    nj, nm, _ = nums_detec(open(f).readlines())
    p = dict(env_p, num_jobs=nj, num_mas=nm)
    env = FJSPEnv([f], dict(p, batch_size=1), data_source="file")
    lignes, temps = [], []
    for _ in range(rep_glouton):
        c, dt = resoudre(env, model, False); temps.append(dt); env.reset()
    lignes.append(dict(instance=r["instance_projet"], instance_song=r["instance_song"], mode="glouton",
                       graine="", cmax=c, temps_s=float(np.mean(temps))))
    env = FJSPEnv([f] * n_ech, dict(p, batch_size=n_ech), data_source="file")
    for g in graines:
        graine(g); env.reset()
        c, dt = resoudre(env, model, True)
        lignes.append(dict(instance=r["instance_projet"], instance_song=r["instance_song"],
                           mode=f"echantillons={n_ech}", graine=g, cmax=c, temps_s=dt))
    return lignes


def _tache(args):
    return evaluer_instance(*args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modele", default=os.path.join(DEPOT, "model", "save_10_5.pt"))
    ap.add_argument("--graines", nargs="*", type=int, default=[0, 1, 2, 3, 4])
    ap.add_argument("--n-echantillons", type=int, default=100)
    ap.add_argument("--repetitions-glouton", type=int, default=10)
    ap.add_argument("--threads", type=int, default=1, help="fils PyTorch (temps rapportés : préciser la valeur)")
    ap.add_argument("--processus", type=int, default=1,
                    help="instances en parallèle (C_max identiques : graines fixées par instance) ; temps NON rapportables si > 1")
    ap.add_argument("--sortie", default=os.path.join(ICI, "resultats_song.csv"))
    ap.add_argument("--reprendre", action="store_true",
                    help="ne pas refaire les instances déjà présentes dans --sortie (écriture au fil de l'eau)")
    ap.add_argument("--sans-correctif", action="store_true",
                    help="garder leur next_time d'origine (ne fonctionne qu'avec d'anciennes versions de PyTorch)")
    ap.add_argument("--instances", nargs="*", default=None, help="sous-ensemble (noms du projet), pour tester")
    a = ap.parse_args()
    _preparer(a.modele, a.threads, a.sans_correctif)
    corr = [r for r in csv.DictReader(open(os.path.join(ICI, "correspondance_instances_song.csv")))
            if r["instance_song"]]
    corr.append({"instance_projet": "BrandimarteMk6", "instance_song": "Mk06"})   # en-tête 15 machines chez Song, 10 chez nous ; données identiques
    if a.instances:
        corr = [r for r in corr if r["instance_projet"] in a.instances]
    champs = ["instance", "instance_song", "mode", "graine", "cmax", "temps_s"]
    deja = set()
    if a.reprendre and os.path.exists(a.sortie):
        deja = {r["instance"] for r in csv.DictReader(open(a.sortie, encoding="utf-8"))}
    else:
        with open(a.sortie, "w", newline="", encoding="utf-8") as fo:
            csv.DictWriter(fo, fieldnames=champs).writeheader()
    corr = [r for r in corr if r["instance_projet"] not in deja]
    print(f"{len(corr)} instances à faire ({len(deja)} déjà dans {a.sortie}) ; {a.processus} processus", flush=True)
    taches = [(r, a.graines, a.n_echantillons, a.repetitions_glouton) for r in corr]
    if a.processus > 1:
        import multiprocessing as mp
        ctx = mp.get_context("spawn" if os.name == "nt" else "fork")
        pool = ctx.Pool(a.processus, initializer=_preparer, initargs=(a.modele, a.threads, a.sans_correctif))
        resultats = pool.imap_unordered(_tache, taches)
    else:
        pool, resultats = None, map(_tache, taches)
    for lignes in resultats:
        with open(a.sortie, "a", newline="", encoding="utf-8") as fo:     # écrit au fil de l'eau
            csv.DictWriter(fo, fieldnames=champs).writerows(lignes)
        print(lignes[0]["instance"], [l["cmax"] for l in lignes], flush=True)
    if pool:
        pool.close(); pool.join()
    print("->", a.sortie)


if __name__ == "__main__":
    main()
