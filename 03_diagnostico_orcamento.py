import pandas as pd
from pathlib import Path

caminho_csv = Path(r"C:\projeto_seguranca_pr\dados_brutos\01_Despesas_Jan_2023.csv")

print("=== DETALHAMENTO DAS UNIDADES DE SEGURANÇA PÚBLICA ===")

try:
    df = pd.read_csv(caminho_csv, sep=';', encoding='latin1', low_memory=False)
except Exception:
    df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8', low_memory=False)

df.columns = df.columns.str.strip()

# Filtrar Segurança Pública pela coluna textual
df_seg = df[df['Descrição Função'].astype(str).str.strip() == 'SEGURANÇA PÚBLICA'].copy()

# 1. Unidades Orçamentárias e Siglas
print(f"Total de registros de Segurança Pública: {len(df_seg)}")
print("\n--- UNIDADES ORÇAMENTÁRIAS PRESENTES ---")
unidades = df_seg[['Unidade', 'Descrição Unidade', 'Sigla']].drop_duplicates().sort_values('Unidade')
print(unidades.to_string(index=False))

# 2. Subfunções
print("\n--- SUBFUNÇÕES ---")
subfuncoes = df_seg[['Sub Função', 'Descrição Sub Função']].drop_duplicates()
print(subfuncoes.to_string(index=False))

# 3. Principais Projetos/Atividades (Ações Orçamentárias)
print("\n--- AMOSTRA DE PROJETOS E ATIVIDADES ---")
acoes = df_seg[['Projeto Atividade', 'Descrição Projeto Atividade']].drop_duplicates()
print(acoes.head(15).to_string(index=False))