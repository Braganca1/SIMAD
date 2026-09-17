# Fila de Requisições em um Servidor Web — Simulação M/M/1

Trabalho de Simulação e Análise de Desempenho (SIMAD) — Instituto Militar de Engenharia (IME), 2026.

Modelagem e simulação de eventos discretos de um servidor web como uma fila M/M/1,
comparando o comportamento do sistema sob baixa carga (ρ = 0,5) e alta carga (ρ = 0,9),
com validação estatística contra o modelo analítico de Teoria das Filas.

## Resultados principais

| Métrica | Baixa carga (ρ=0,5) | Alta carga (ρ=0,9) | Erro vs. teórico |
|---|---|---|---|
| Tempo médio de espera na fila (Wq) | 0,10 s | 0,89 s | < 1,1% |
| Tempo médio no sistema (W) | 0,20 s | 0,99 s | < 0,9% |

Ao aumentar a utilização do servidor de 50% para 90% (+80% de carga), o tempo de
espera cresceu ~9x — evidenciando o comportamento assintótico característico de
sistemas de filas próximos da saturação.

## Estrutura do repositório

```
.
├── simulacao_fila_web.py       # Simulador (SimPy) — gera todos os dados
├── graficos.py                 # Gera os gráficos comparativos a partir dos dados
├── resultados.json             # Métricas agregadas (gerado pelo simulador)
├── raw_samples.npy             # Amostras brutas por requisição (gerado pelo simulador)
├── dados_entrada_saida.csv     # Dados de entrada/saída por replicação (30 por cenário)
├── cdf_comparativo.png         # CDF empírica vs. teórica do tempo no sistema
├── metricas_comparativo.png    # Comparação simulado vs. teórico (L, Lq, W, Wq)
├── relatorio_fila_web.tex      # Relatório completo (LaTeX)
└── relatorio_fila_web.pdf      # Relatório compilado
```

## Como rodar

```bash
pip install simpy numpy scipy matplotlib

python3 simulacao_fila_web.py   # gera resultados.json, raw_samples.npy, dados_entrada_saida.csv
python3 graficos.py             # gera cdf_comparativo.png e metricas_comparativo.png
```

Os resultados são **deterministicamente reprodutíveis**: as sementes aleatórias são
geradas a partir de índices fixos (cenário, replicação), não de `hash()` de string —
rodando o script quantas vezes for, os números batem exatamente com os do relatório.

## Metodologia

- **Modelo**: fila M/M/1 (Kendall) — chegadas Poisson (λ), atendimento exponencial (μ), 1 servidor.
- **Simulação**: eventos discretos via [SimPy](https://simpy.readthedocs.io/), código próprio.
- **Validação**: comparação direta com as fórmulas fechadas de Teoria das Filas (Kleinrock, 1975).
- **Estatística**: 30 replicações independentes por cenário, 20.000s simulados cada,
  2.000s de warm-up descartados, médias com IC 95%.

## Relatório completo

Ver [`relatorio_fila_web.pdf`](./relatorio_fila_web.pdf) para a análise completa,
incluindo descrição do sistema, modelagem matemática, validação, metodologia
experimental e discussão crítica dos resultados.

## Autores

- Cap Eryan José Portes
- Ten Arthur Bragança Siqueira de Souza
- Luan Siviero Passos

Trabalho orientado pela Major Gabriela Moutinho de Souza Dias, disciplina de
Simulação e Análise de Desempenho, IME (2026).