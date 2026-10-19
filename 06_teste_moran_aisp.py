import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path

print("=== INICIANDO TESTE DE AUTOCORRELAÇÃO ESPACIAL (I DE MORAN) ===")

PASTA_BASE = Path(r"C:\projeto_seguranca_pr")
PASTA_LIMPOS = PASTA_BASE / "dados_limpos"

# 1. Localização Dinâmica dos Ficheiros
candidatos_shp = list(PASTA_BASE.rglob("malha_aisp.shp"))
candidatos_dea = list(PASTA_BASE.rglob("resultado_dea_aisp.csv"))

if not candidatos_shp:
    print("ERRO: 'malha_aisp.shp' não encontrado em nenhuma pasta de C:\\projeto_seguranca_pr")
    exit()
if not candidatos_dea:
    print("ERRO: 'resultado_dea_aisp.csv' não encontrado em nenhuma pasta de C:\\projeto_seguranca_pr")
    exit()

caminho_shp = candidatos_shp[0]
caminho_dea = candidatos_dea[0]
print(f"-> Shapefile encontrado em: {caminho_shp}")
print(f"-> Base DEA encontrada em: {caminho_dea}")

gdf = gpd.read_file(caminho_shp)
df_dea = pd.read_csv(caminho_dea)

gdf["cod_aisp"] = gdf["cod_aisp"].astype(int)
df_dea["cod_aisp"] = df_dea["cod_aisp"].astype(int)

# Mesclar e ordenar estritamente por cod_aisp
gdf = gdf.merge(df_dea, on="cod_aisp").sort_values("cod_aisp").reset_index(drop=True)
n = len(gdf)
print(f"-> Total de AISPs preparadas para análise espacial: {n}\n")

# 2. Construir Matriz de Vizinhança Espacial W (Contiguidade Queen)
W = np.zeros((n, n))
for i in range(n):
    geom_i = gdf.geometry.iloc[i]
    for j in range(n):
        if i != j:
            geom_j = gdf.geometry.iloc[j]
            # Vizinhos compartilham borda ou vértice
            if geom_i.touches(geom_j) or geom_i.intersects(geom_j):
                W[i, j] = 1.0

# Padronização pelas linhas (Row-standardization)
soma_linhas = W.sum(axis=1)
if (soma_linhas == 0).any():
    print("ALERTA: Detectada AISP sem vizinhos de contiguidade direta.")
W_std = np.divide(W, soma_linhas[:, np.newaxis], out=np.zeros_like(W), where=soma_linhas[:, np.newaxis] != 0)

# 3. Função para Cálculo do Moran Global (Permutação de Monte Carlo)
def calcular_moran_global(y, W_matrix, n_perm=999, seed=42):
    np.random.seed(seed)
    z = y - np.mean(y)
    s0 = np.sum(W_matrix)
    den = np.sum(z**2)
    num = np.sum(W_matrix * np.outer(z, z))
    
    I_obs = (len(y) / s0) * (num / den)
    EI = -1.0 / (len(y) - 1)
    
    sim_I = []
    for _ in range(n_perm):
        z_perm = np.random.permutation(z)
        num_p = np.sum(W_matrix * np.outer(z_perm, z_perm))
        sim_I.append((len(y) / s0) * (num_p / den))
    
    sim_I = np.array(sim_I)
    z_score = (I_obs - np.mean(sim_I)) / np.std(sim_I)
    p_valor = (np.sum(np.abs(sim_I - EI) >= np.abs(I_obs - EI)) + 1) / (n_perm + 1)
    
    return I_obs, EI, z_score, p_valor

# 4. Função para Cálculo do Moran Local (LISA)
def calcular_moran_local(y, W_matrix, n_perm=999, seed=42):
    np.random.seed(seed)
    n_obs = len(y)
    z = y - np.mean(y)
    m2 = np.sum(z**2) / n_obs
    lag_z = np.dot(W_matrix, z)
    
    Ii = (z / m2) * lag_z
    
    quadrantes = []
    for zi, lag_zi in zip(z, lag_z):
        if zi >= 0 and lag_zi >= 0:
            quadrantes.append("Alto-Alto")
        elif zi < 0 and lag_zi < 0:
            quadrantes.append("Baixo-Baixo")
        elif zi >= 0 and lag_zi < 0:
            quadrantes.append("Alto-Baixo")
        else:
            quadrantes.append("Baixo-Alto")
            
    p_locais = np.zeros(n_obs)
    for i in range(n_obs):
        z_outros = np.delete(z, i)
        w_i = np.delete(W_matrix[i, :], i)
        
        sim_Ii = []
        for _ in range(n_perm):
            perm = np.random.permutation(z_outros)
            sim_lag = np.sum(w_i * perm)
            sim_Ii.append((z[i] / m2) * sim_lag)
            
        sim_Ii = np.array(sim_Ii)
        p_locais[i] = (np.sum(np.abs(sim_Ii) >= np.abs(Ii[i])) + 1) / (n_perm + 1)
        
    return Ii, quadrantes, p_locais

# -------------------------------------------------------------
# 5. EXECUÇÃO DOS TESTES ESPACIAIS
# -------------------------------------------------------------
y_dea = gdf["score_dea"].values
I_dea, EI, z_dea, p_dea = calcular_moran_global(y_dea, W_std)

y_mvi = gdf["taxa_mvi_100k"].values
I_mvi, _, z_mvi, p_mvi = calcular_moran_global(y_mvi, W_std)

Ii_dea, quad_dea, p_lisa_dea = calcular_moran_local(y_dea, W_std)
gdf["I_local_dea"] = Ii_dea
gdf["quadrante_dea"] = quad_dea
gdf["p_valor_lisa"] = p_lisa_dea
gdf["significativo_5pct"] = gdf["p_valor_lisa"].apply(lambda p: "Sim" if p <= 0.05 else "Não")

colunas_salvar = [
    "cod_aisp", "sede_regional", "score_percentual", "taxa_mvi_100k",
    "I_local_dea", "quadrante_dea", "p_valor_lisa", "significativo_5pct"
]
caminho_out = PASTA_LIMPOS / "moran_aisp_resultados.csv"
gdf[colunas_salvar].to_csv(caminho_out, index=False)

print("==========================================================================")
print("             DIAGNÓSTICO DE AUTOCORRELAÇÃO ESPACIAL (MORAN GLOBAL)")
print("==========================================================================")
print(f"Expectativa Teórica sob H0 (E[I]): {EI:.4f}")
print("-" * 75)
print(f"Variável: Escore de Eficiência DEA")
print(f"  * I de Moran Observado : {I_dea:.4f}")
print(f"  * Escore Z (Pseudo-Z)  : {z_dea:.4f}")
print(f"  * Pseudo p-valor       : {p_dea:.4f} {'(Significativo a 5%)' if p_dea <= 0.05 else '(Não significativo)'}")
print("-" * 75)
print(f"Variável: Taxa de MVI (por 100k habitantes)")
print(f"  * I de Moran Observado : {I_mvi:.4f}")
print(f"  * Escore Z (Pseudo-Z)  : {z_mvi:.4f}")
print(f"  * Pseudo p-valor       : {p_mvi:.4f} {'(Significativo a 5%)' if p_mvi <= 0.05 else '(Não significativo)'}")
print("==========================================================================")

print("\n--- RESUMO DOS QUADRANTES LISA (EFICIÊNCIA DEA) ---")
print(gdf["quadrante_dea"].value_counts().to_string())

print("\n--- AISPs COM AGRUPAMENTO LOCAL SIGNIFICATIVO (p <= 0.10) ---")
sig_10 = gdf[gdf["p_valor_lisa"] <= 0.10][["cod_aisp", "sede_regional", "score_percentual", "quadrante_dea", "p_valor_lisa"]]
if not sig_10.empty:
    print(sig_10.to_string(index=False))
else:
    print("Nenhuma AISP apresentou significância local individual abaixo de 0.10.")