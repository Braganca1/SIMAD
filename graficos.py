import numpy as np
import matplotlib.pyplot as plt

raw = np.load("raw_samples.npy", allow_pickle=True).item()

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for ax, (name, label, color) in zip(
    axes,
    [("A_baixa_carga", "Cenario A - Baixa carga (rho=0.5)", "tab:blue"),
     ("B_alta_carga", "Cenario B - Alta carga (rho=0.9)", "tab:red")],
):
    sojourn = np.array(raw[name]["sojourn"])
    lam, mu = raw[name]["lambda"], raw[name]["mu"]

    # CDF empirica
    x_emp = np.sort(sojourn)
    y_emp = np.arange(1, len(x_emp) + 1) / len(x_emp)

    # CDF teorica: W ~ Exponencial(mu - lambda)
    rate = mu - lam
    x_theo = np.linspace(0, np.quantile(sojourn, 0.999), 300)
    y_theo = 1 - np.exp(-rate * x_theo)

    ax.plot(x_emp, y_emp, color=color, lw=1.5, label="Simulado (empirico)")
    ax.plot(x_theo, y_theo, "k--", lw=1.5, label="Teorico M/M/1")
    ax.set_xlim(0, np.quantile(sojourn, 0.995))
    ax.set_xlabel("Tempo no sistema W (s)")
    ax.set_ylabel("F(W) - Probabilidade acumulada")
    ax.set_title(label)
    ax.legend()
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("cdf_comparativo.png", dpi=150)
print("Grafico CDF salvo.")

# ---- grafico de barras comparando metricas entre cenarios ----
import json
with open("resultados.json") as f:
    results = json.load(f)

metrics = ["Wq", "W", "Lq", "L"]
labels = {"Wq": "Espera na fila (s)", "W": "Tempo no sistema (s)",
          "Lq": "Nº médio na fila", "L": "Nº médio no sistema"}

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
for ax, m in zip(axes, metrics):
    sim_vals = [results[s]["empirical"][m]["mean"] for s in ["A_baixa_carga", "B_alta_carga"]]
    theo_vals = [results[s]["empirical"][m]["theoretical"] for s in ["A_baixa_carga", "B_alta_carga"]]
    ci_errs = [
        (results[s]["empirical"][m]["mean"] - results[s]["empirical"][m]["ci95"][0])
        for s in ["A_baixa_carga", "B_alta_carga"]
    ]
    x = np.arange(2)
    w = 0.35
    ax.bar(x - w / 2, sim_vals, w, yerr=ci_errs, capsize=4, label="Simulado", color="tab:blue")
    ax.bar(x + w / 2, theo_vals, w, label="Teorico", color="tab:gray")
    ax.set_xticks(x)
    ax.set_xticklabels(["Baixa\ncarga", "Alta\ncarga"])
    ax.set_title(labels[m])
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("metricas_comparativo.png", dpi=150)
print("Grafico de metricas salvo.")