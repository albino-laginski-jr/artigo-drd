import html
import re
import unicodedata
from pathlib import Path
import pandas as pd

print("=== CONSOLIDAÇÃO ORÇAMENTÁRIA E DEMOGRÁFICA (CENSO 2022 x SEFA-PR) ===")

PASTA_BASE = Path(r"C:\projeto_seguranca_pr")
PASTA_BRUTOS = PASTA_BASE / "dados_brutos"
PASTA_LIMPOS = PASTA_BASE / "dados_limpos"
PASTA_LIMPOS.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# 1. PROCESSAR EXECUTADO ORÇAMENTÁRIO (SEFA-PR 2023)
# -------------------------------------------------------------
candidatos_orc = list(PASTA_BRUTOS.glob("*Consulta*Atualizada*Dezembro*2023*")) + \
                 list(PASTA_BRUTOS.glob("*Dezembro*2023*"))
candidatos_orc = [f for f in set(candidatos_orc) if f.is_file() and not f.name.endswith(".py")]

caminho_orc = candidatos_orc[0]
print(f"-> Arquivo orçamentário lido: {caminho_orc.name}")

# Leitura com fallback de separador (alguns arquivos do portal usam vírgula em vez de ponto-e-vírgula)
try:
    df_orc = pd.read_csv(caminho_orc, sep=";", encoding="latin1", low_memory=False)
    if len(df_orc.columns) < 5:
        df_orc = pd.read_csv(caminho_orc, sep=",", encoding="latin1", low_memory=False)
except Exception:
    df_orc = pd.read_csv(caminho_orc, sep=";", encoding="utf-8", low_memory=False)

df_orc.columns = df_orc.columns.str.strip()

# Deteção inteligente da coluna liquidada
col_liq = [c for c in df_orc.columns if "liquidado" in c.lower()]
if not col_liq:
    print("\nERRO: Nenhuma coluna de valor liquidado encontrada.")
    print("Colunas presentes:", df_orc.columns.tolist())
    exit()

# Tenta pegar a acumulada ("até"). Se não existir, pega a última coluna liquidada disponível.
col_at = [c for c in col_liq if "at" in c.lower() or "ano" in c.lower() or "acum" in c.lower()]
coluna_liquidado = col_at[0] if col_at else col_liq[-1]
print(f"-> Coluna de despesa identificada: '{coluna_liquidado}'")

def limpar_moeda(val):
    if pd.isna(val): return 0.0
    s = str(val).strip().replace(".", "").replace(",", ".")
    try: return float(s)
    except: return 0.0

df_orc["VALOR_LIQUIDADO"] = df_orc[coluna_liquidado].apply(limpar_moeda)

# Deteção inteligente das colunas de Função e Unidade
col_funcao = [c for c in df_orc.columns if "fun" in c.lower() and "descri" in c.lower()]
col_funcao = col_funcao[0] if col_funcao else [c for c in df_orc.columns if "fun" in c.lower()][0]

col_unidade = [c for c in df_orc.columns if "unidade" in c.lower() and "descri" in c.lower()]
col_unidade = col_unidade[0] if col_unidade else [c for c in df_orc.columns if "unidade" in c.lower()][0]

df_seg = df_orc[df_orc[col_funcao].astype(str).str.strip().str.upper() == "SEGURANÇA PÚBLICA"].copy()

unidades_policiais = [
    "POLÍCIA MILITAR", "POLÍCIA CÍVIL", "POLÍCIA CIENTÍFICA",
    "SECRETARIA DE ESTADO DA SEGURANÇA PÚBLICA - DG",
    "FUNDO ESP. DE SEGURANÇA PUB. DO PARANA", "FDO ESP SIST UNICO SEG PUBLICA"
]

despesa_policial_total = df_seg[df_seg[col_unidade].isin(unidades_policiais)]["VALOR_LIQUIDADO"].sum()
despesa_seguranca_ampla = df_seg["VALOR_LIQUIDADO"].sum()

print(f"Total Liquidado (Forças Policiais): R$ {despesa_policial_total:,.2f}")
print(f"Total Liquidado (Função 06 Geral): R$ {despesa_seguranca_ampla:,.2f}")

# -------------------------------------------------------------
# 2. CARREGAR POPULAÇÃO DO CENSO 2022 (IBGE-PR.csv)
# -------------------------------------------------------------
caminho_ibge = PASTA_BRUTOS / "IBGE-PR.csv"
print(f"-> Arquivo demográfico lido: {caminho_ibge.name}")

with open(caminho_ibge, 'r', encoding='latin1') as f:
    linhas = f.readlines()

linhas_processadas = [html.unescape(linha).strip() for linha in linhas[1:] if linha.strip()]
dados_ibge = []
cabecalho = linhas_processadas[0].split(',')

idx_municipio = next(i for i, c in enumerate(cabecalho) if "Munic" in c)
idx_populacao = next(i for i, c in enumerate(cabecalho) if "2022" in c and "Popula" in c)

for linha in linhas_processadas[1:]:
    colunas = linha.split(',')
    if len(colunas) > idx_populacao:
        nome_mun = colunas[idx_municipio].strip()
        pop_str = colunas[idx_populacao].strip()
        if pop_str.isdigit():
            dados_ibge.append({"municipio_raw": nome_mun, "populacao": int(pop_str)})

df_pop = pd.DataFrame(dados_ibge)

def normalizar_nome(texto):
    t = unicodedata.normalize('NFD', str(texto).upper().strip())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = re.sub(r"[^A-Z]", "", t)
    return t

df_pop["CHAVE"] = df_pop["municipio_raw"].apply(normalizar_nome)

# -------------------------------------------------------------
# 3. CRUZAMENTO COM A BASE DAS 23 AISPs
# -------------------------------------------------------------
df_rel = pd.read_csv(PASTA_BRUTOS / "relacao_municipios_aisp.csv")
df_rel["CHAVE"] = df_rel["municipio"].apply(normalizar_nome)

df_cruzado = pd.merge(df_rel, df_pop[["CHAVE", "populacao"]], on="CHAVE", how="left")

faltantes = df_cruzado[df_cruzado["populacao"].isna()]
for idx, row in faltantes.iterrows():
    chave_prefixo = row["CHAVE"][:6]
    match = df_pop[df_pop["CHAVE"].str.startswith(chave_prefixo)]
    if not match.empty:
        df_cruzado.loc[idx, "populacao"] = match.iloc[0]["populacao"]

pop_por_aisp = df_cruzado.groupby("cod_aisp")["populacao"].sum().reset_index()
pop_total_pr = pop_por_aisp["populacao"].sum()
print(f"-> População Total do Paraná apurada (Censo 2022): {pop_total_pr:,} habitantes.")

# -------------------------------------------------------------
# 4. ALOCAÇÃO DO RATEIO POPULACIONAL (ABORDAGEM 1)
# -------------------------------------------------------------
pop_por_aisp["peso_populacional"] = pop_por_aisp["populacao"] / pop_total_pr
pop_por_aisp["despesa_policial_liquidada"] = pop_por_aisp["peso_populacional"] * despesa_policial_total
pop_por_aisp["gasto_policial_per_capita"] = pop_por_aisp["despesa_policial_liquidada"] / pop_por_aisp["populacao"]

# -------------------------------------------------------------
# 5. GERAR BASE MASTER DEA (CRUZAMENTO COM MVI DA TAREFA 3)
# -------------------------------------------------------------
df_mvi = pd.read_csv(PASTA_BRUTOS / "mvi_por_aisp.csv")
df_master = pd.merge(pop_por_aisp, df_mvi, on="cod_aisp")
df_master["taxa_mvi_100k"] = (df_master["mvi_total"] / df_master["populacao"]) * 100000

# Gravar o arquivo oficial para o modelo DEA
caminho_master = PASTA_LIMPOS / "base_dea_aisp.csv"
df_master.to_csv(caminho_master, index=False)
print(f"\n-> SUCESSO EXTREMO: Base Master DEA gerada e gravada em '{caminho_master.name}'.")

print("\n--- AMOSTRA DA BASE CONSOLIDADA (5 PRIMEIRAS AISPs) ---")
colunas_exibir = ["cod_aisp", "populacao", "peso_populacional", "despesa_policial_liquidada", "mvi_total", "taxa_mvi_100k"]
amostra = df_master[colunas_exibir].head(5).copy()
amostra["despesa_policial_liquidada"] = amostra["despesa_policial_liquidada"].apply(lambda x: f"R$ {x:,.2f}")
amostra["taxa_mvi_100k"] = amostra["taxa_mvi_100k"].round(2)
amostra["peso_populacional"] = amostra["peso_populacional"].apply(lambda x: f"{x*100:.2f}%")
print(amostra.to_string(index=False))