import pandas as pd
import numpy as np
from scipy.optimize import linprog
from pathlib import Path

print("=== CALCULANDO O MODELO DEA (BCC - ORIENTAÇÃO A OUTPUT) ===")

PASTA_BASE = Path(r"C:\projeto_seguranca_pr")
PASTA_LIMPOS = PASTA_BASE / "dados_limpos"

# 1. Carregar a Base Master
df = pd.read_csv(PASTA_LIMPOS / "base_dea_aisp.csv")

# Nomes sedes para facilitar a leitura
sedes = {
    1: "Curitiba", 2: "RMC", 3: "Litoral", 4: "Ponta Grossa", 5: "Lapa/S.Mateus",
    6: "União da Vitória", 7: "Guarapuava", 8: "Laranjeiras do Sul", 9: "Pato Branco",
    10: "Fco. Beltrão", 11: "Cascavel", 12: "Foz do Iguaçu", 13: "Toledo",
    14: "Campo Mourão", 15: "Umuarama", 16: "Paranavaí", 17: "Maringá",
    18: "Apucarana", 19: "Arapongas", 20: "Londrina", 21: "Cornélio Procópio",
    22: "Telêmaco Borba", 23: "Jacarezinho"
}
df["sede_regional"] = df["cod_aisp"].map(sedes)

# 2. Preparar Inputs e Outputs
# Input: Gasto Per Capita
X = df[["gasto_policial_per_capita"]].values 

# Output: Inverso da Taxa MVI (multiplicado por 1000 para facilitar convergência matemática do solver)
df["seguranca_produzida"] = 1000 / df["taxa_mvi_100k"]
Y = df[["seguranca_produzida"]].values

n_dmus = len(df)
scores_eficiencia = []
benchmarks_list = []

# 3. Motor DEA - BCC Orientado a Output (Programação Linear)
for o in range(n_dmus):
    # Vetor de variáveis: [lambda_1, lambda_2, ..., lambda_23, phi]
    # Objetivo: Maximizar phi => Minimizar -phi
    c = np.zeros(n_dmus + 1)
    c[-1] = -1  # Coeficiente de phi
    
    # Restrições de Inequação (A_ub * x <= b_ub)
    A_ub = []
    b_ub = []
    
    # Restrição de Input: Sum(lambda * X) <= X_o
    for i in range(X.shape[1]):
        row = np.zeros(n_dmus + 1)
        row[:n_dmus] = X[:, i]
        row[-1] = 0
        A_ub.append(row)
        b_ub.append(X[o, i])
        
    # Restrição de Output: Sum(lambda * Y) >= phi * Y_o  =>  -Sum(lambda * Y) + phi * Y_o <= 0
    for r in range(Y.shape[1]):
        row = np.zeros(n_dmus + 1)
        row[:n_dmus] = -Y[:, r]
        row[-1] = Y[o, r]
        A_ub.append(row)
        b_ub.append(0)
        
    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)
    
    # Restrição de Equação para BCC (Retornos Variáveis): Sum(lambda) = 1
    A_eq = np.zeros((1, n_dmus + 1))
    A_eq[0, :n_dmus] = 1
    b_eq = np.array([1])
    
    # Limites das variáveis (lambdas >= 0, phi >= 1)
    bounds = [(0, None) for _ in range(n_dmus)] + [(1.0, None)]
    
    # Resolver PL
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    if res.success:
        phi = res.x[-1]
        eficiencia = 1 / phi  # Score DEA padrão
        lambdas = res.x[:n_dmus]
        
        # Identificar AISPs de referência (Benchmarks) para as ineficientes
        refs = []
        for j in range(n_dmus):
            if lambdas[j] > 0.001 and j != o:
                refs.append(str(df.loc[j, "cod_aisp"]))
        
        scores_eficiencia.append(eficiencia)
        benchmarks_list.append(", ".join(refs) if refs else "-")
    else:
        scores_eficiencia.append(np.nan)
        benchmarks_list.append("Erro")

df["score_dea"] = scores_eficiencia
df["score_percentual"] = df["score_dea"] * 100
df["benchmarks"] = benchmarks_list

# 4. Exportar e Exibir Resultados
df = df.sort_values(by="score_dea", ascending=False)
caminho_resultado = PASTA_LIMPOS / "resultado_dea_aisp.csv"
df.to_csv(caminho_resultado, index=False)

print("\n-> SUCESSO: Análise Envoltória de Dados (DEA) processada!")
print(f"-> Arquivo de resultados salvo em '{caminho_resultado.name}'.")

print("\n==========================================================================")
print("             RANKING DE EFICIÊNCIA DEA DAS AISPs (PARANÁ)")
print("==========================================================================")
print(f"{'AISP':<6} | {'Sede Regional':<20} | {'Taxa MVI':<10} | {'Score DEA':<10} | {'Benchmarks'}")
print("-" * 75)
for _, r in df.iterrows():
    taxa = f"{r['taxa_mvi_100k']:.2f}"
    score = f"{r['score_percentual']:.2f}%"
    bench = r['benchmarks']
    print(f"{r['cod_aisp']:<6} | {r['sede_regional']:<20} | {taxa:<10} | {score:<10} | {bench}")
print("==========================================================================")
print("* Nota: Taxa MVI expressa mortes por 100 mil habitantes.")
print("* Score 100% indica que a AISP está na fronteira máxima de eficiência.")