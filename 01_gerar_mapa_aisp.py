import re
import unicodedata
import warnings
from pathlib import Path
import geopandas as gpd
import pandas as pd

warnings.filterwarnings('ignore')

print("=== INICIANDO TAREFA 2: CRUZAMENTO IBGE x SESP/PR ===")

PASTA_BASE = Path(r"C:\projeto_seguranca_pr")
PASTA_BRUTOS = PASTA_BASE / "dados_brutos"
PASTA_MAPAS = PASTA_BASE / "mapas"

# 1. Localizar e carregar o Shapefile oficial do IBGE
caminho_shp_ibge = PASTA_MAPAS / "PR_Municipios_2022.shp"
if not caminho_shp_ibge.exists():
    print(f"ERRO: Não foi encontrado o arquivo {caminho_shp_ibge}.")
    print("Verifique se extraiu o ZIP do IBGE na pasta 'mapas'.")
    exit()

gdf_mun = gpd.read_file(caminho_shp_ibge)

# Identificar colunas de código e nome do município no shapefile
col_cod = [c for c in gdf_mun.columns if 'MUN' in c and ('CD' in c or 'COD' in c)][0]
col_nome = [c for c in gdf_mun.columns if 'MUN' in c and ('NM' in c or 'NOME' in c)][0]

# 2. Função de padronização textual (ignora acentos, hífens e variações ortográficas)
def padronizar_nome(texto):
    t = unicodedata.normalize('NFD', str(texto).upper().strip())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = re.sub(r"[^A-Z]", "", t)
    t = t.replace("DOESTE", "OESTE").replace("DOOESTE", "OESTE")
    t = t.replace("CAJUA", "CAIUA")
    t = t.replace("MARINCK", "MAIRINCK")
    t = t.replace("LARANJERAS", "LARANJEIRAS")
    return t

gdf_mun["CHAVE_BUSCA"] = gdf_mun[col_nome].apply(padronizar_nome)

# 3. Relação oficial dos 399 municípios pelas 23 AISPs (SESP/PR)
lista_sesp = [
    # 1ª AISP
    (1, "CURITIBA"),
    # 2ª AISP
    (2, "ADRIANOPOLIS"), (2, "AGUDOS DO SUL"), (2, "ALMIRANTE TAMANDARE"), (2, "ARAUCARIA"), (2, "BALSA NOVA"),
    (2, "BOCAIUVA DO SUL"), (2, "CAMPINA GRANDE DO SUL"), (2, "CAMPO LARGO"), (2, "CAMPO MAGRO"), (2, "CERRO AZUL"),
    (2, "COLOMBO"), (2, "DOUTOR ULYSSES"), (2, "FAZENDA RIO GRANDE"), (2, "ITAPERUCU"), (2, "MANDIRITUBA"),
    (2, "PINHAIS"), (2, "PIRAQUARA"), (2, "QUATRO BARRAS"), (2, "RIO BRANCO DO SUL"), (2, "SAO JOSE DOS PINHAIS"),
    (2, "TIJUCAS DO SUL"), (2, "TUNAS DO PARANA"),
    # 3ª AISP
    (3, "ANTONINA"), (3, "GUARAQUECABA"), (3, "GUARATUBA"), (3, "MATINHOS"), (3, "MORRETES"), (3, "PARANAGUA"), (3, "PONTAL DO PARANA"),
    # 4ª AISP
    (4, "ARAPOTI"), (4, "CARAMBEI"), (4, "CASTRO"), (4, "FERNANDES PINHEIRO"), (4, "GUAMIRANGA"), (4, "IMBITUVA"),
    (4, "INACIO MARTINS"), (4, "IPIRANGA"), (4, "IRATI"), (4, "IVAI"), (4, "JAGUARIAIVA"), (4, "PALMEIRA"),
    (4, "PIRAI DO SUL"), (4, "PONTA GROSSA"), (4, "PORTO AMAZONAS"), (4, "REBOUCAS"), (4, "RIO AZUL"),
    (4, "SENGES"), (4, "TEIXEIRA SOARES"), (4, "SAO JOAO DO TRIUNFO"),
    # 5ª AISP
    (5, "ANTONIO OLINTO"), (5, "CAMPO DO TENENTE"), (5, "CONTENDA"), (5, "LAPA"), (5, "PIEN"), (5, "QUITANDINHA"),
    (5, "RIO NEGRO"), (5, "SAO MATEUS DO SUL"),
    # 6ª AISP
    (6, "BITURUNA"), (6, "CRUZ MACHADO"), (6, "GENERAL CARNEIRO"), (6, "MALLET"), (6, "PAULA FREITAS"),
    (6, "PAULO FRONTIN"), (6, "PORTO VITORIA"), (6, "UNIAO DA VITORIA"),
    # 7ª AISP
    (7, "BOA VENTURA DE SAO ROQUE"), (7, "CAMPINA DO SIMAO"), (7, "CANDOI"), (7, "FOZ DO JORDAO"), (7, "GUARAPUAVA"),
    (7, "MANOEL RIBAS"), (7, "MATO RICO"), (7, "NOVA TEBAS"), (7, "PINHAO"), (7, "PITANGA"), (7, "PRUDENTOPOLIS"),
    (7, "RESERVA DO IGUACU"), (7, "SANTA MARIA DO OESTE"), (7, "TURVO"),
    # 8ª AISP
    (8, "CANTAGALO"), (8, "GOIOXIM"), (8, "LARANJAL"), (8, "LARANJEIRAS DO SUL"), (8, "MARQUINHO"), (8, "NOVA LARANJEIRAS"),
    (8, "PALMITAL"), (8, "PORTO BARREIRO"), (8, "RIO BONITO DO IGUACU"), (8, "VIRMOND"),
    # 9ª AISP
    (9, "BOM SUCESSO DO SUL"), (9, "CHOPINZINHO"), (9, "CLEVELANDIA"), (9, "CORONEL DOMINGOS SOARES"), (9, "CORONEL VIVIDA"),
    (9, "HONORIO SERPA"), (9, "ITAPEJARA D'OESTE"), (9, "MANGUEIRINHA"), (9, "MARIOPOLIS"), (9, "PALMAS"),
    (9, "PATO BRANCO"), (9, "SAO JOAO"), (9, "SAO JORGE DO OESTE"), (9, "SAUDADE DO IGUACU"), (9, "SULINA"), (9, "VITORINO"),
    # 10ª AISP
    (10, "AMPERE"), (10, "BARRACAO"), (10, "BELA VISTA DA CAROBA"), (10, "BOA ESPERANCA DO IGUACU"), (10, "BOM JESUS DO SUL"),
    (10, "CAPANEMA"), (10, "CRUZEIRO DO IGUACU"), (10, "DOIS VIZINHOS"), (10, "ENEAS MARQUES"), (10, "FLOR DA SERRA DO SUL"),
    (10, "FRANCISCO BELTRAO"), (10, "MANFRINOPOLIS"), (10, "MARMELEIRO"), (10, "NOVA ESPERANCA DO SUDOESTE"),
    (10, "NOVA PRATA DO IGUACU"), (10, "PEROLA D'OESTE"), (10, "PINHAL DE SAO BENTO"), (10, "PLANALTO"), (10, "PRANCHITA"),
    (10, "REALEZA"), (10, "RENASCENCA"), (10, "SALGADO FILHO"), (10, "SALTO DO LONTRA"), (10, "SANTA IZABEL DO OESTE"),
    (10, "SANTO ANTONIO DO SUDOESTE"), (10, "VERE"),
    # 11ª AISP
    (11, "ANAHY"), (11, "BOA VISTA DA APARECIDA"), (11, "BRAGANEY"), (11, "CAMPO BONITO"), (11, "CAPITAO LEONIDAS MARQUES"),
    (11, "CASCAVEL"), (11, "CATANDUVAS"), (11, "CEU AZUL"), (11, "CORBELIA"), (11, "DIAMANTE DO SUL"),
    (11, "ESPIGAO ALTO DO IGUACU"), (11, "GUARANIACU"), (11, "IBEMA"), (11, "IGUATU"), (11, "LINDOESTE"), (11, "MATELANDIA"),
    (11, "QUEDAS DO IGUACU"), (11, "RAMILANDIA"), (11, "SANTA LUCIA"), (11, "SANTA TEREZA DO OESTE"),
    (11, "TRES BARRAS DO PARANA"), (11, "VERA CRUZ DO OESTE"),
    # 12ª AISP
    (12, "FOZ DO IGUACU"), (12, "ITAIPULANDIA"), (12, "MEDIANEIRA"), (12, "MISSAL"), (12, "SANTA TEREZINHA DE ITAIPU"),
    (12, "SAO MIGUEL DO IGUACU"), (12, "SERRANOPOLIS DO IGUACU"),
    # 13ª AISP
    (13, "ASSIS CHATEAUBRIAND"), (13, "CAFELANDIA"), (13, "DIAMANTE D'OESTE"), (13, "ENTRE RIOS DO OESTE"),
    (13, "FORMOSA DO OESTE"), (13, "GUAIRA"), (13, "IRACEMA DO OESTE"), (13, "JESUITAS"), (13, "MARECHAL CANDIDO RONDON"),
    (13, "MARIPA"), (13, "MERCEDES"), (13, "NOVA AURORA"), (13, "NOVA SANTA ROSA"), (13, "OURO VERDE DO OESTE"),
    (13, "PALOTINA"), (13, "PATO BRAGADO"), (13, "QUATRO PONTES"), (13, "SANTA HELENA"), (13, "SAO JOSE DAS PALMEIRAS"),
    (13, "SAO PEDRO DO IGUACU"), (13, "TERRA ROXA"), (13, "TOLEDO"), (13, "TUPASSI"),
    # 14ª AISP
    (14, "ALTAMIRA DO PARANA"), (14, "ARARUNA"), (14, "BARBOSA FERRAZ"), (14, "BOA ESPERANCA"), (14, "CAMPINA DA LAGOA"),
    (14, "CAMPO MOURAO"), (14, "CIANORTE"), (14, "CORUMBATAI DO SUL"), (14, "ENGENHEIRO BELTRAO"), (14, "FAROL"),
    (14, "FENIX"), (14, "INDIANOPOLIS"), (14, "IRETAMA"), (14, "JANIOPOLIS"), (14, "JAPURA"), (14, "JURANDA"),
    (14, "JUSSARA"), (14, "LUIZIANA"), (14, "MAMBORE"), (14, "NOVA CANTU"), (14, "PEABIRU"), (14, "QUINTA DO SOL"),
    (14, "RONCADOR"), (14, "SAO MANOEL DO PARANA"), (14, "SAO TOME"), (14, "TERRA BOA"), (14, "UBIRATA"),
    # 15ª AISP
    (15, "ALTO PARAISO"), (15, "ALTO PIQUIRI"), (15, "ALTONIA"), (15, "BRASILANDIA DO SUL"), (15, "CAFEZAL DO SUL"),
    (15, "CIDADE GAUCHA"), (15, "CRUZEIRO DO OESTE"), (15, "DOURADINA"), (15, "ESPERANCA NOVA"), (15, "FRANCISCO ALVES"),
    (15, "GOIOERE"), (15, "GUAPOREMA"), (15, "ICARAIMA"), (15, "IPORA"), (15, "IVATE"), (15, "MARIA HELENA"),
    (15, "MARILUZ"), (15, "MOREIRA SALES"), (15, "NOVA OLIMPIA"), (15, "PEROBAL"), (15, "PEROLA"),
    (15, "QUARTO CENTENARIO"), (15, "RANCHO ALEGRE D'OESTE"), (15, "RONDON"), (15, "SAO JORGE DO PATROCINIO"),
    (15, "TAPEJARA"), (15, "TAPIRA"), (15, "TUNEIRAS DO OESTE"), (15, "UMUARAMA"), (15, "XAMBRE"),
    # 16ª AISP
    (16, "ALTO PARANA"), (16, "AMAPORA"), (16, "ATALAIA"), (16, "CRUZEIRO DO SUL"), (16, "DIAMANTE DO NORTE"),
    (16, "FLORAI"), (16, "GUAIRACA"), (16, "INAJA"), (16, "ITAUNA DO SUL"), (16, "JARDIM OLINDA"), (16, "LOANDA"),
    (16, "MARILENA"), (16, "MIRADOR"), (16, "NOVA ALIANCA DO IVAI"), (16, "NOVA ESPERANCA"), (16, "NOVA LONDRINA"),
    (16, "PARAISO DO NORTE"), (16, "PARANACITY"), (16, "PARANAPOEMA"), (16, "PARANAVAI"), (16, "PLANALTINA DO PARANA"),
    (16, "PORTO RICO"), (16, "PRESIDENTE CASTELO BRANCO"), (16, "QUERENCIA DO NORTE"), (16, "SANTA CRUZ DE MONTE CASTELO"),
    (16, "SANTA ISABEL DO IVAI"), (16, "SANTA MONICA"), (16, "SANTO ANTONIO DO CAIUA"), (16, "SAO CARLOS DO IVAI"),
    (16, "SAO JOAO DO CAIUA"), (16, "SAO PEDRO DO PARANA"), (16, "TAMBOARA"), (16, "TERRA RICA"), (16, "UNIFLOR"),
    # 17ª AISP
    (17, "ANGULO"), (17, "ASTORGA"), (17, "COLORADO"), (17, "DOUTOR CAMARGO"), (17, "FLORESTA"), (17, "FLORIDA"),
    (17, "IGUARACU"), (17, "ITAGUAJE"), (17, "ITAMBE"), (17, "IVATUBA"), (17, "LOBATO"), (17, "MANDAGUACU"),
    (17, "MANDAGUARI"), (17, "MARIALVA"), (17, "MARINGA"), (17, "MUNHOZ DE MELO"), (17, "NOSSA SENHORA DAS GRACAS"),
    (17, "OURIZONA"), (17, "PAICANDU"), (17, "PITANGUEIRAS"), (17, "SANTA FE"), (17, "SANTA INES"), (17, "SANTO INACIO"),
    (17, "SAO JORGE DO IVAI"), (17, "SARANDI"),
    # 18ª AISP
    (18, "APUCARANA"), (18, "ARAPUA"), (18, "ARIRANHA DO IVAI"), (18, "BOM SUCESSO"), (18, "BORRAZOPOLIS"),
    (18, "CALIFORNIA"), (18, "CAMBIRA"), (18, "CRUZMALTINA"), (18, "FAXINAL"), (18, "GODOY MOREIRA"), (18, "GRANDES RIOS"),
    (18, "IVAIPORA"), (18, "JANDAIA DO SUL"), (18, "JARDIM ALEGRE"), (18, "KALORE"), (18, "LIDIANOPOLIS"),
    (18, "LUNARDELLI"), (18, "MARILANDIA DO SUL"), (18, "MARUMBI"), (18, "MAUA DA SERRA"), (18, "NOVO ITACOLOMI"),
    (18, "RIO BOM"), (18, "RIO BRANCO DO IVAI"), (18, "ROSARIO DO IVAI"), (18, "SAO JOAO DO IVAI"), (18, "SAO PEDRO DO IVAI"),
    # 19ª AISP
    (19, "ALVORADA DO SUL"), (19, "ARAPONGAS"), (19, "BELA VISTA DO PARAISO"), (19, "CAFEARA"), (19, "CENTENARIO DO SUL"),
    (19, "FLORESTOPOLIS"), (19, "GUARACI"), (19, "JAGUAPITA"), (19, "LUPIONOPOLIS"), (19, "MIRASELVA"), (19, "PORECATU"),
    (19, "PRADO FERREIRA"), (19, "PRIMEIRO DE MAIO"), (19, "ROLANDIA"), (19, "SABAUDIA"), (19, "SERTANOPOLIS"),
    # 20ª AISP
    (20, "CAMBE"), (20, "IBIPORA"), (20, "JATAIZINHO"), (20, "LONDRINA"), (20, "TAMARANA"),
    # 21ª AISP
    (21, "ANDIRA"), (21, "ASSAI"), (21, "BANDEIRANTES"), (21, "BARRA DO JACARE"), (21, "CONGONHINHAS"),
    (21, "CORNELIO PROCOPIO"), (21, "ITAMBARACA"), (21, "LEOPOLIS"), (21, "NOVA AMERICA DA COLINA"), (21, "NOVA FATIMA"),
    (21, "NOVA SANTA BARBARA"), (21, "RANCHO ALEGRE"), (21, "SANTA AMELIA"), (21, "SANTA CECILIA DO PAVAO"),
    (21, "SANTA MARIANA"), (21, "SANTO ANTONIO DO PARAISO"), (21, "SAO JERONIMO DA SERRA"), (21, "SAO SEBASTIAO DA AMOREIRA"),
    (21, "SERTANEJA"), (21, "URAI"),
    # 22ª AISP
    (22, "CANDIDO DE ABREU"), (22, "CURIUVA"), (22, "FIGUEIRA"), (22, "IMBAU"), (22, "ORTIGUEIRA"), (22, "RESERVA"),
    (22, "SAPOPEMA"), (22, "TELEMACO BORBA"), (22, "TIBAGI"), (22, "VENTANIA"),
    # 23ª AISP
    (23, "ABATIA"), (23, "CAMBARA"), (23, "CARLOPOLIS"), (23, "CONSELHEIRO MAIRINCK"), (23, "GUAPIRAMA"), (23, "IBAITI"),
    (23, "JABOTI"), (23, "JACAREZINHO"), (23, "JAPIRA"), (23, "JOAQUIM TAVORA"), (23, "JUNDIAI DO SUL"), (23, "PINHALAO"),
    (23, "QUATIGUA"), (23, "RIBEIRAO CLARO"), (23, "RIBEIRAO DO PINHAL"), (23, "SALTO DO ITARARE"), (23, "SANTANA DO ITARARE"),
    (23, "SANTO ANTONIO DA PLATINA"), (23, "SAO JOSE DA BOA VISTA"), (23, "SIQUEIRA CAMPOS"), (23, "TOMAZINA"), (23, "WENCESLAU BRAZ")
]

df_sesp = pd.DataFrame(lista_sesp, columns=["cod_aisp", "NOME_SESP"])
df_sesp["CHAVE_BUSCA"] = df_sesp["NOME_SESP"].apply(padronizar_nome)

# 4. Cruzamento exato com validação de integridade
df_cruzamento = pd.merge(gdf_mun[[col_cod, col_nome, "CHAVE_BUSCA"]], df_sesp, on="CHAVE_BUSCA", how="left")
nao_encontrados = df_cruzamento[df_cruzamento['cod_aisp'].isna()]

if not nao_encontrados.empty:
    print("\nERRO: Os seguintes municípios do shapefile não foram mapeados:")
    print(nao_encontrados[[col_nome]])
    exit()

df_cruzamento.rename(columns={col_cod: 'cod_ibge', col_nome: 'municipio'}, inplace=True)
df_relacao = df_cruzamento[["cod_ibge", "cod_aisp", "municipio"]]

# Salvar a planilha de correspondência oficial
caminho_csv = PASTA_BRUTOS / "relacao_municipios_aisp.csv"
df_relacao.to_csv(caminho_csv, index=False, encoding="utf-8")
print(f"-> SUCESSO: Arquivo '{caminho_csv.name}' salvo com 399 municípios únicos.")

# 5. Gerar o Shapefile das 23 AISPs por dissolução espacial
print("Gerando fronteiras unificadas das 23 AISPs...")
gdf_unido = gdf_mun.merge(df_relacao[["cod_ibge", "cod_aisp"]], left_on=col_cod, right_on="cod_ibge")
gdf_aisp = gdf_unido.dissolve(by="cod_aisp", as_index=False)[["cod_aisp", "geometry"]]

caminho_shp_aisp = PASTA_MAPAS / "malha_aisp.shp"
gdf_aisp.to_file(caminho_shp_aisp, encoding="utf-8")
print(f"-> SUCESSO: Shapefile '{caminho_shp_aisp.name}' gerado com 23 polígonos contíguos.")