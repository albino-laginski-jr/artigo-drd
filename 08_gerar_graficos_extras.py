import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

print("=== GERANDO GRÁFICOS COMPLEMENTARES PARA O MANUSCRITO ===")

PASTA_BASE = Path(r"C:\projeto_seguranca_pr")
PASTA_LIMPOS = PASTA_BASE / "dados_limpos"
PASTA_MAPAS = PASTA_BASE / "mapas"
PASTA_MAPAS.mkdir(exist_ok=True)

# 1. Carregar Base de Moran, DEA e Malha
caminho_shp = list(PASTA_BASE.rglob("malha_aisp.shp"))[0]
df_moran = pd.read_csv(PASTA_LIMPOS / "moran_aisp_resultados.csv")

gdf = gpd.read_file(caminho_shp)
gdf["cod_aisp"] = gdf["cod_aisp"].astype(int)
df_moran["cod_aisp"] = df_moran["cod_aisp"].astype(int)
gdf = gdf.merge(df_moran, on="cod_aisp").sort_values("cod_aisp").reset_index(drop=True)

# 2. Reconstruir W e recriar as variáveis do Scatterplot
n = len(gdf)
W = np.zeros((n, n))
for i in range(n):
    geom_i = gdf.geometry.iloc[i]
    for j in range(n):
        if i != j:
            geom_j = gdf.geometry.iloc[j]
            if geom_i.touches(geom_j) or geom_i.intersects(geom_j):
                W[i, j] = 1.0

soma_linhas = W.sum(axis=1)
W_std = np.divide(W, soma_linhas[:, np.newaxis], out=np.zeros_like(W), where=soma_linhas[:, np.newaxis] != 0)

y_dea = gdf["score_percentual"].values
z = y_dea - np.mean(y_dea)  # Desvio em relação à média (eixo X)
wz = np.dot(W_std, z)       # Defasagem Espacial (eixo Y)

# Calcular inclinação da reta (que é matematicamente igual ao I de Moran Global)
m, b = np.polyfit(z, wz, 1)

# -------------------------------------------------------------
# GRÁFICO 1: DIAGRAMA DE DISPERSÃO DE MORAN
# -------------------------------------------------------------
plt.figure(figsize=(9, 9), dpi=300)
plt.axhline(0, color='black', lw=1.2, ls='--')
plt.axvline(0, color='black', lw=1.2, ls='--')

cores_lisa = {
    "Alto-Alto": "#d7191c", "Baixo-Baixo": "#2b83ba",
    "Alto-Baixo": "#fdae61", "Baixo-Alto": "#abdda4"
}

# Plotar os pontos
for q, color in cores_lisa.items():
    mascara = gdf["quadrante_dea"] == q
    plt.scatter(z[mascara], wz[mascara], c=color, label=q, s=80, edgecolors='black', alpha=0.9, zorder=3)

# Adicionar os números das AISPs ao lado dos pontos
for i in range(n):
    plt.text(z[i] + 1.2, wz[i] + 0.3, str(gdf["cod_aisp"].iloc[i]), fontsize=8, color="dimgrey", fontweight='bold', zorder=4)

# Plotar a Reta de Regressão do I de Moran
x_vals = np.array([min(z)-5, max(z)+5])
y_vals = b + m * x_vals
plt.plot(x_vals, y_vals, color='gray', lw=2.5, zorder=2, label=f"Reta Global (I = {m:.4f}; p = 0.60)")

# Formatação
plt.title("Diagrama de Dispersão de Moran - Eficiência Técnica das AISPs", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("Eficiência Técnica DEA - Desvio em relação à média ($z$)", fontsize=11)
plt.ylabel("Eficiência dos Vizinhos - Defasagem Espacial ($W_z$)", fontsize=11)
plt.xlim(min(z)-8, max(z)+8)
plt.ylim(min(wz)-8, max(wz)+8)
plt.legend(loc="upper left", frameon=True, fontsize=10)
plt.grid(True, linestyle=':', alpha=0.6, zorder=1)

caminho_scatter = PASTA_MAPAS / "grafico_moran_scatterplot.png"
plt.savefig(caminho_scatter, bbox_inches="tight")
plt.close()

print(f"-> SUCESSO: Diagrama de Dispersão salvo em '{caminho_scatter.name}'.")

# -------------------------------------------------------------
# GRÁFICO 2: FRONTEIRA EMPÍRICA DEA (Gráfico de Pontos)
# -------------------------------------------------------------
df_master = pd.read_csv(PASTA_LIMPOS / "base_dea_aisp.csv")
df_master = df_master.merge(df_moran[["cod_aisp", "score_percentual"]], on="cod_aisp")

plt.figure(figsize=(10, 6), dpi=300)

# Eixo X = População da AISP; Eixo Y = Taxa MVI; Bolha = Cor pela eficiência
sc = plt.scatter(
    df_master["populacao"] / 1000,  # X em milhares
    df_master["taxa_mvi_100k"],     # Y
    c=df_master["score_percentual"], 
    cmap="RdYlGn",
    s=df_master["score_percentual"] * 3, # Tamanho da bolha aumenta com a eficiência
    edgecolors='black', 
    alpha=0.9
)

# Adicionar os números das AISPs nas bolhas
for i, r in df_master.iterrows():
    plt.text((r["populacao"]/1000) + 15, r["taxa_mvi_100k"] + 0.5, str(int(r["cod_aisp"])), fontsize=8, fontweight='bold')

plt.title("Desempenho das AISPs: Dimensão Demográfica vs. Taxa de Criminalidade Letal", fontsize=13, fontweight='bold', pad=15)
plt.xlabel("População da AISP (em milhares de habitantes)", fontsize=11)
plt.ylabel("Taxa de Mortes Violentas Intencionais (por 100 mil hab.)", fontsize=11)
plt.grid(True, linestyle=':', alpha=0.6)

# Barra de cor lateral (Escala de Eficiência)
cbar = plt.colorbar(sc)
cbar.set_label("Escore de Eficiência DEA-BCC (%)", rotation=270, labelpad=15)

caminho_bolhas = PASTA_MAPAS / "grafico_eficiencia_demografia.png"
plt.savefig(caminho_bolhas, bbox_inches="tight")
plt.close()

print(f"-> SUCESSO: Gráfico de Eficiência x Demografia salvo em '{caminho_bolhas.name}'.")
print("\nProcesso concluído! Os dois gráficos complementares foram adicionados à pasta 'mapas'.")