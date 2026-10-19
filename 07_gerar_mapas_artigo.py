import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

print("=== GERANDO MAPAS TEMÁTICOS E TABELA PARA O MANUSCRITO ===")

PASTA_BASE = Path(r"C:\projeto_seguranca_pr")
PASTA_LIMPOS = PASTA_BASE / "dados_limpos"
PASTA_MAPAS = PASTA_BASE / "mapas"
PASTA_MAPAS.mkdir(exist_ok=True)

# ---------------------------------------------------------
# 1. LOCALIZAÇÃO DOS FICHEIROS
# ---------------------------------------------------------
caminho_shp = list(PASTA_BASE.rglob("malha_aisp.shp"))[0]
caminho_moran = PASTA_LIMPOS / "moran_aisp_resultados.csv"
caminho_dea_master = PASTA_LIMPOS / "base_dea_aisp.csv"
caminho_dea_resultados = PASTA_LIMPOS / "resultado_dea_aisp.csv"

# ---------------------------------------------------------
# 2. GERAR A TABELA FORMAL PARA O ARTIGO (CSV PARA EXCEL/WORD)
# ---------------------------------------------------------
df_master = pd.read_csv(caminho_dea_master)
df_moran = pd.read_csv(caminho_moran)
df_dea_res = pd.read_csv(caminho_dea_resultados)

# Cruzar as bases para ter tudo na mesma tabela
tabela_artigo = df_master[["cod_aisp", "populacao"]].merge(df_moran, on="cod_aisp")
tabela_artigo = tabela_artigo.merge(df_dea_res[["cod_aisp", "benchmarks"]], on="cod_aisp")

# Ordenar pelo Score DEA (do maior para o menor)
tabela_artigo = tabela_artigo.sort_values(by="score_percentual", ascending=False)

# Formatar colunas para o padrão acadêmico do Brasil (ponto milhar, vírgula decimal)
tabela_artigo["populacao"] = tabela_artigo["populacao"].apply(lambda x: f"{x:,}".replace(",", "."))
tabela_artigo["score_percentual"] = tabela_artigo["score_percentual"].apply(lambda x: f"{x:.2f}%".replace(".", ","))
tabela_artigo["taxa_mvi_100k"] = tabela_artigo["taxa_mvi_100k"].apply(lambda x: f"{x:.2f}".replace(".", ","))
tabela_artigo["p_valor_lisa"] = tabela_artigo["p_valor_lisa"].apply(lambda x: f"{x:.3f}".replace(".", ","))

# Renomear colunas para o formato da Tabela Final
tabela_artigo = tabela_artigo.rename(columns={
    "cod_aisp": "AISP",
    "sede_regional": "Sede Regional",
    "populacao": "População (2022)",
    "taxa_mvi_100k": "Taxa MVI (por 100 mil hab.)",
    "score_percentual": "Escore DEA-BCC",
    "benchmarks": "Benchmarks",
    "quadrante_dea": "Quadrante LISA",
    "p_valor_lisa": "Valor-p (LISA)"
})

colunas_finais = [
    "AISP", "Sede Regional", "População (2022)", "Taxa MVI (por 100 mil hab.)", 
    "Escore DEA-BCC", "Benchmarks", "Quadrante LISA", "Valor-p (LISA)"
]
tabela_artigo = tabela_artigo[colunas_finais]

# Salvar como CSV formatado
caminho_tabela_csv = PASTA_BASE / "Tabela_Resultados_Manuscrito.csv"
tabela_artigo.to_csv(caminho_tabela_csv, index=False, sep=";", encoding="utf-8-sig")

print(f"-> SUCESSO: Tabela do manuscrito gerada em '{caminho_tabela_csv.name}' (Abra no Excel).")

# ---------------------------------------------------------
# 3. GERAR MAPAS CARTOGRÁFICOS EM ALTA RESOLUÇÃO
# ---------------------------------------------------------
gdf = gpd.read_file(caminho_shp)
gdf["cod_aisp"] = gdf["cod_aisp"].astype(int)
df_moran["cod_aisp"] = df_moran["cod_aisp"].astype(int)
gdf_mapa = gdf.merge(df_moran, on="cod_aisp")

# Configurar figura com 2 painéis
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9), dpi=300)

# MAPA A: Escore de Eficiência DEA
gdf_mapa.plot(
    column="score_percentual",
    cmap="RdYlGn",
    linewidth=0.7,
    edgecolor="black",
    legend=True,
    legend_kwds={"label": "Eficiência DEA-BCC (%)", "orientation": "horizontal", "shrink": 0.7, "pad": 0.05},
    ax=ax1
)
ax1.set_title("A. Eficiência Técnica das 23 AISPs (DEA-BCC)", fontsize=14, fontweight="bold")
ax1.set_axis_off()

for _, row in gdf_mapa.iterrows():
    c = row.geometry.centroid
    ax1.annotate(str(row["cod_aisp"]), xy=(c.x, c.y), horizontalalignment="center", fontsize=8, fontweight="bold")

# MAPA B: Quadrantes LISA
cores_lisa = {
    "Alto-Alto": "#d7191c",      # Vermelho
    "Baixo-Baixo": "#2b83ba",    # Azul
    "Alto-Baixo": "#fdae61",     # Laranja
    "Baixo-Alto": "#abdda4"      # Verde claro
}
gdf_mapa["cor_quad"] = gdf_mapa["quadrante_dea"].map(cores_lisa)

gdf_mapa.plot(
    color=gdf_mapa["cor_quad"],
    linewidth=0.7,
    edgecolor="black",
    ax=ax2
)
ax2.set_title("B. Tipologia Espacial LISA (Quadrantes de Eficiência)", fontsize=14, fontweight="bold")
ax2.set_axis_off()

for _, row in gdf_mapa.iterrows():
    c = row.geometry.centroid
    ax2.annotate(str(row["cod_aisp"]), xy=(c.x, c.y), horizontalalignment="center", fontsize=8, fontweight="bold")

# Legenda do Mapa B
legend_elements = [
    Patch(facecolor="#d7191c", edgecolor="black", label="Alto-Alto (Alta ef. com vizinhos de Alta ef.)"),
    Patch(facecolor="#2b83ba", edgecolor="black", label="Baixo-Baixo (Baixa ef. com vizinhos de Baixa ef.)"),
    Patch(facecolor="#fdae61", edgecolor="black", label="Alto-Baixo (Alta ef. com vizinhos de Baixa ef.)"),
    Patch(facecolor="#abdda4", edgecolor="black", label="Baixo-Alto (Baixa ef. com vizinhos de Alta ef.)")
]
ax2.legend(handles=legend_elements, loc="lower left", fontsize=10, frameon=True)

plt.tight_layout()
caminho_fig = PASTA_MAPAS / "figura_mapas_dea_lisa.png"
plt.savefig(caminho_fig, bbox_inches="tight")

print(f"-> SUCESSO: Figura cartográfica de alta resolução salva em '{caminho_fig}'.")
print("Processo concluído! Os anexos para o seu artigo estão prontos.")