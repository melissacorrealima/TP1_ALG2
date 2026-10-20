
"""Gera figuras do relatório a partir do benchmark do GeoEntrega BH.

Uso: python graficos.py [caminho_para_csv]
Dependências: pandas, matplotlib
"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


ENTRADA = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path("resultados_benchmark.csv")
)

SAIDA = Path("graficos_relatorio")
SAIDA.mkdir(exist_ok=True)


# ============================================================
# CARREGAMENTO E VALIDAÇÃO DOS DADOS
# ============================================================

df = pd.read_csv(ENTRADA)

colunas = {
    "frota",
    "raio_km",
    "tempo_trie_ms",
    "tempo_exaustiva_ms",
    "tempo_construcao_ms",
    "total_candidatos",
    "correto",
}

faltantes = colunas - set(df.columns)

if faltantes:
    raise ValueError(
        f"Colunas ausentes no CSV: {sorted(faltantes)}"
    )

if not df["correto"].astype(str).str.lower().eq("true").all():
    print("AVISO: há consultas divergentes no benchmark.")


# ============================================================
# CONFIGURAÇÃO VISUAL DOS GRÁFICOS
# ============================================================

plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 130,
})


def salvar(nome):
    """Salva o gráfico em PNG e fecha a figura."""
    plt.tight_layout()

    caminho = SAIDA / nome

    plt.savefig(
        caminho,
        dpi=220,
        bbox_inches="tight",
    )

    plt.close()

    print("Gerado:", caminho)


# ============================================================
# GRÁFICO 1 — TEMPO DE CONSULTA POR TAMANHO DA FROTA
# ============================================================

g = df.groupby(
    "frota",
    as_index=False
)[
    ["tempo_trie_ms", "tempo_exaustiva_ms"]
].mean()

plt.figure(figsize=(8, 4.5))

plt.plot(
    g["frota"],
    g["tempo_trie_ms"],
    "o-",
    label="Trie compacta",
)

plt.plot(
    g["frota"],
    g["tempo_exaustiva_ms"],
    "s-",
    label="Busca exaustiva",
)

plt.xlabel("Quantidade de entregadores")
plt.ylabel("Tempo médio por consulta (ms)")
plt.title("Tempo de consulta por tamanho da frota")

plt.legend()
plt.grid(alpha=0.2)

salvar("01_tempo_por_frota.png")


# ============================================================
# GRÁFICO 2 — TEMPO DE CONSULTA POR RAIO
# ============================================================

g = df.groupby(
    "raio_km",
    as_index=False
)[
    ["tempo_trie_ms", "tempo_exaustiva_ms"]
].mean()

plt.figure(figsize=(8, 4.5))

plt.plot(
    g["raio_km"],
    g["tempo_trie_ms"],
    "o-",
    label="Trie compacta",
)

plt.plot(
    g["raio_km"],
    g["tempo_exaustiva_ms"],
    "s-",
    label="Busca exaustiva",
)

plt.xlabel("Raio da consulta (km)")
plt.ylabel("Tempo médio por consulta (ms)")
plt.title("Tempo de consulta por raio")

plt.xticks(sorted(df["raio_km"].unique()))

plt.legend()
plt.grid(alpha=0.2)

salvar("02_tempo_por_raio.png")


# ============================================================
# GRÁFICO 3 — PERCENTUAL DE CANDIDATOS RECUPERADOS
# ============================================================

# Mede a proporção da frota recuperada pelo índice.
# Não representa apenas os entregadores elegíveis.

df["percentual_candidatos"] = (
    100 * df["total_candidatos"] / df["frota"]
)

g = df.groupby(
    "raio_km",
    as_index=False
)["percentual_candidatos"].mean()

plt.figure(figsize=(8, 4.5))

plt.bar(
    g["raio_km"].astype(str),
    g["percentual_candidatos"],
)

plt.xlabel("Raio da consulta (km)")
plt.ylabel("Candidatos recuperados (% da frota)")
plt.ylim(0, 105)

plt.title("Seletividade do índice por raio")

salvar("03_percentual_candidatos.png")


# ============================================================
# GRÁFICO 4 — TEMPO DE CONSTRUÇÃO DA TRIE
# ============================================================

# A construção é medida uma vez por tamanho de frota.
# O mesmo valor aparece repetido nas linhas do CSV.

g = df.groupby(
    "frota",
    as_index=False
)["tempo_construcao_ms"].first()

plt.figure(figsize=(8, 4.5))

plt.plot(
    g["frota"],
    g["tempo_construcao_ms"],
    "o-",
)

plt.xlabel("Quantidade de entregadores")
plt.ylabel("Tempo de construção (ms)")
plt.title("Tempo de construção da Trie compacta")

plt.grid(alpha=0.2)

salvar("04_construcao_trie.png")


# ============================================================
# FINALIZAÇÃO
# ============================================================

print(
    f"Concluído: {len(df)} cenários lidos de {ENTRADA}"
)
