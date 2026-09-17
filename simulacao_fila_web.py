"""
Simulação de Eventos Discretos - Fila de Requisicoes em um Servidor Web (M/M/1)
Compara dois cenarios: baixa carga (rho=0.5) e alta carga (rho=0.9)
"""

import simpy
import numpy as np
from scipy import stats
import json
import csv

# ---------------------------------------------------------------
# Parametros dos cenarios
# ---------------------------------------------------------------
SCENARIOS = {
    "A_baixa_carga": {"lambda_": 5.0, "mu": 10.0},
    "B_alta_carga":  {"lambda_": 9.0, "mu": 10.0},
}

SIM_TIME = 20000.0     # tempo simulado por replicacao (segundos)
WARMUP = 2000.0        # periodo de warm-up descartado
N_REPLICATIONS = 30    # replicacoes independentes por cenario
CONFIDENCE = 0.95


class MM1Server:
    """Servidor web modelado como fila M/M/1."""

    def __init__(self, env, mu):
        self.env = env
        self.server = simpy.Resource(env, capacity=1)
        self.mu = mu
        # registros (apenas pos-warmup)
        self.wait_times = []      # Wq: tempo esperando na fila
        self.sojourn_times = []   # W : tempo total no sistema
        # amostragem de L(t)/Lq(t) por integracao no tempo
        self.area_L = 0.0
        self.area_Lq = 0.0
        self.last_event_time = 0.0
        self.n_in_system = 0
        self.n_in_queue = 0

    def _update_areas(self):
        now = self.env.now
        if now > WARMUP:
            dt = now - max(self.last_event_time, WARMUP)
            if dt > 0:
                self.area_L += self.n_in_system * dt
                self.area_Lq += self.n_in_queue * dt
        self.last_event_time = now

    def request(self):
        arrival = self.env.now
        self._update_areas()
        self.n_in_system += 1
        self.n_in_queue += 1
        with self.server.request() as req:
            yield req
            self._update_areas()
            self.n_in_queue -= 1
            wait = self.env.now - arrival
            service_time = np.random.exponential(1.0 / self.mu)
            yield self.env.timeout(service_time)
            self._update_areas()
            self.n_in_system -= 1
            sojourn = self.env.now - arrival
            if arrival >= WARMUP:
                self.wait_times.append(wait)
                self.sojourn_times.append(sojourn)


def arrivals(env, server, lambda_):
    while True:
        yield env.timeout(np.random.exponential(1.0 / lambda_))
        env.process(server.request())


def get_seed(scenario_idx, replication_idx):
    """Semente deterministica (NAO usar hash() de string: e' aleatorizado a
    cada execucao do processo Python por seguranca (PYTHONHASHSEED), o que
    tornaria os resultados irreprodutiveis entre execucoes)."""
    return scenario_idx * 100000 + replication_idx * 1000


def run_one_replication(lambda_, mu, seed):
    np.random.seed(seed)
    env = simpy.Environment()
    server = MM1Server(env, mu)
    env.process(arrivals(env, server, lambda_))
    env.run(until=SIM_TIME)
    server._update_areas()

    obs_time = SIM_TIME - WARMUP
    L_hat = server.area_L / obs_time
    Lq_hat = server.area_Lq / obs_time
    W_hat = np.mean(server.sojourn_times)
    Wq_hat = np.mean(server.wait_times)
    rho_hat = lambda_ * np.mean(np.random.exponential(1.0 / mu, size=1))  # placeholder nao usado
    return {
        "L": L_hat, "Lq": Lq_hat, "W": W_hat, "Wq": Wq_hat,
        "wait_sample": server.wait_times, "sojourn_sample": server.sojourn_times,
    }


def confidence_interval(data, confidence=CONFIDENCE):
    data = np.array(data)
    n = len(data)
    mean = data.mean()
    sem = stats.sem(data)
    h = sem * stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return mean, data.std(ddof=1), (mean - h, mean + h)


def theoretical_mm1(lambda_, mu):
    rho = lambda_ / mu
    L = rho / (1 - rho)
    Lq = rho ** 2 / (1 - rho)
    W = 1.0 / (mu - lambda_)
    Wq = rho / (mu - lambda_)
    return {"rho": rho, "L": L, "Lq": Lq, "W": W, "Wq": Wq}


def main():
    results = {}
    raw_samples = {}
    csv_rows = []  # dados de entrada/saida por replicacao, para dados_entrada_saida.csv

    for scenario_idx, (name, params) in enumerate(SCENARIOS.items()):
        lambda_, mu = params["lambda_"], params["mu"]
        reps = {"L": [], "Lq": [], "W": [], "Wq": []}
        all_wait, all_sojourn = [], []

        for i in range(N_REPLICATIONS):
            seed = get_seed(scenario_idx, i)
            r = run_one_replication(lambda_, mu, seed=seed)
            for k in ["L", "Lq", "W", "Wq"]:
                reps[k].append(r[k])
            all_wait.extend(r["wait_sample"])
            all_sojourn.extend(r["sojourn_sample"])
            csv_rows.append({
                "cenario": name, "replicacao": i + 1, "seed": seed,
                "lambda": lambda_, "mu": mu,
                "tempo_simulado_s": SIM_TIME, "warmup_s": WARMUP,
                "n_requisicoes_pos_warmup": len(r["wait_sample"]),
                "L": round(r["L"], 6), "Lq": round(r["Lq"], 6),
                "W_s": round(r["W"], 6), "Wq_s": round(r["Wq"], 6),
            })

        theo = theoretical_mm1(lambda_, mu)
        summary = {"lambda": lambda_, "mu": mu, "theoretical": theo, "empirical": {}}
        for k in ["L", "Lq", "W", "Wq"]:
            mean, std, ci = confidence_interval(reps[k])
            summary["empirical"][k] = {
                "mean": mean, "std": std, "ci95": ci,
                "theoretical": theo[k],
                "erro_pct": 100 * abs(mean - theo[k]) / theo[k],
            }
        results[name] = summary
        raw_samples[name] = {"wait": all_wait, "sojourn": all_sojourn, "mu": mu, "lambda": lambda_}

        print(f"\n=== Cenario {name} (lambda={lambda_}, mu={mu}, rho={theo['rho']:.2f}) ===")
        for k in ["L", "Lq", "W", "Wq"]:
            e = summary["empirical"][k]
            print(f"  {k:3s}: simulado={e['mean']:.4f} (dp={e['std']:.4f}, IC95%=[{e['ci95'][0]:.4f},{e['ci95'][1]:.4f}])"
                  f"  teorico={e['theoretical']:.4f}  erro={e['erro_pct']:.2f}%")

    # salva resultados numericos para consulta
    with open("resultados.json", "w") as f:
        json.dump(
            {k: {kk: vv for kk, vv in v.items() if kk != "empirical"} | {
                "empirical": {mk: {sk: sv for sk, sv in mv.items()} for mk, mv in v["empirical"].items()}
            } for k, v in results.items()},
            f, indent=2, default=str
        )

    np.save("raw_samples.npy", raw_samples, allow_pickle=True)

    # dados de entrada/saida por replicacao, em formato legivel (item 5.4 do edital)
    with open("dados_entrada_saida.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    print("\nResultados salvos em resultados.json, raw_samples.npy e dados_entrada_saida.csv")
    return results, raw_samples


if __name__ == "__main__":
    main()