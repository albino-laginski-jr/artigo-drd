import pandas as pd
from pathlib import Path
import unicodedata
import re

print("=== CONSOLIDANDO DADOS OFICIAIS DE MVI (TRIÉNIO 2022-2024) ===")

PASTA_BASE = Path(r"C:\projeto_seguranca_pr")
PASTA_BRUTOS = PASTA_BASE / "dados_brutos"

# 1. Localizar a tabela de MVI
candidatos = [
    PASTA_BRUTOS / "Mortes Violentas Intencionais_Tabela.csv",
    PASTA_BASE / "Mortes Violentas Intencionais_Tabela.csv"
]
caminho_mvi = next((p for p in candidatos if p.exists()), None)

if not caminho_mvi:
    print("ERRO: Ficheiro 'Mortes Violentas Intencionais_Tabela.csv' não encontrado.")
    exit()

# 2. Carregar a relação oficial gerada na Tarefa 2
caminho_rel = PASTA_BRUTOS / "relacao_municipios_aisp.csv"
df_rel = pd.read_csv(caminho_rel)

def normalizar(texto):
    t = unicodedata.normalize('NFD', str(texto).upper().strip())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = re.sub(r"[^A-Z]", "", t)
    return t

df_rel['CHAVE'] = df_rel['municipio'].apply(normalizar)

# 3. Ler o ficheiro oficial da SESP (codificação UTF-16 e separador TAB)
df_raw = pd.read_csv(caminho_mvi, sep='\t', encoding='utf-16', header=[0, 1, 2])

def limpar_numero(val):
    if pd.isna(val): return 0
    s = str(val).strip().replace('.', '')
    return int(s) if s.isdigit() else 0

df_muns = pd.DataFrame()
df_muns['municipio_raw'] = df_raw.iloc[1:, 0].values
df_muns['CHAVE'] = df_muns['municipio_raw'].apply(normalizar)

# Extrair Homicídio Doloso, Latrocínio e Lesão Corporal Seguidas de Morte para 2022, 2023 e 2024
for y in ['2022', '2023', '2024']:
    col_hom = ('Mortes Violentas Intencionais', 'Vítimas de Homicídio Doloso', y)
    col_lat = ('Mortes Violentas Intencionais', 'Vítimas de Roubo com Resultado de Morte (Latrocínio)', y)
    col_les = ('Mortes Violentas Intencionais', 'Vítimas de Lesão Corporal com Resultado de Morte', y)
    
    hom = df_raw.iloc[1:][col_hom].apply(limpar_numero).values
    lat = df_raw.iloc[1:][col_lat].apply(limpar_numero).values
    les = df_raw.iloc[1:][col_les].apply(limpar_numero).values
    
    df_muns[f'mvi_{y}'] = hom + lat + les

# Cruzar com a AISP
df_consolidado = pd.merge(df_muns, df_rel[['CHAVE', 'cod_aisp']], on='CHAVE', how='left')

# Calcular total do triénio e média anual
df_consolidado['mvi_trienio'] = df_consolidado['mvi_2022'] + df_consolidado['mvi_2023'] + df_consolidado['mvi_2024']
df_consolidado['mvi_media'] = df_consolidado['mvi_trienio'] / 3.0

# Agregar por AISP
df_aisp = df_consolidado.groupby('cod_aisp')['mvi_media'].sum().round(2).reset_index()
df_aisp.rename(columns={'mvi_media': 'mvi_total'}, inplace=True)

# Gravar ficheiro definitivo
caminho_saida = PASTA_BRUTOS / "mvi_por_aisp.csv"
df_aisp.to_csv(caminho_saida, index=False)
print(f"-> SUCESSO: '{caminho_saida.name}' gravado com a média trienal das 23 AISPs.")