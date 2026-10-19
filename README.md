# artigo-drd
UNIVERSIDADE TECNOLÓGICA FEDERAL DO PARANÁ (UTFPR)
ALBINO LAGINSKI JUNIOR

Eficiência e Transbordamento Espacial na Segurança Pública do Paraná
Este repositório contém os dados suplementares e os códigos-fonte utilizados no artigo acadêmico "Eficiência e Transbordamento Espacial na Segurança Pública no Estado do Paraná", 
submetido à revista Desenvolvimento Regional em debate (DRd).

Sobre o Projeto
O estudo avalia a eficiência técnica das 23 Áreas Integradas de Segurança Pública (AISPs) do Paraná na contenção da violência letal (Mortes Violentas Intencionais - MVI), 
controlando o viés de sede orçamentária por meio de rateio demográfico (Censo 2022). O projeto integra métodos de programação linear e econometria espacial para testar a hipótese
de transbordamento territorial (efeito contágio inter-regional).

Metodologia Computacional
O pipeline analítico foi integralmente roteirizado em Python para garantir a total reprodutibilidade da pesquisa. A modelagem divide-se em duas frentes algorítmicas:
Otimização DEA-BCC: Cálculo da fronteira de eficiência empírica com orientação a output utilizando programação linear exata.
Análise Exploratória de Dados Espaciais (AEDE): Inferência topológica com cálculo do Índice Global de Moran e Indicadores Locais de Associação Espacial (LISA), validados por simulação
condicional de Monte Carlo (999 permutações).

Dependências e Bibliotecas
Para executar os scripts contidos neste repositório, é necessário ter o Python 3.12+ instalado, juntamente com as seguintes bibliotecas:
`numpy` - Para manipulação de arrays e operações matemáticas estruturais.
`pulp` - Para a modelagem e resolução do problema de programação linear (DEA).
`geopandas` - Para o tratamento topológico e manipulação das malhas vetoriais (shapefiles).
`libpysal` - Para a extração e estruturação da matriz de pesos espaciais (Contiguidade Queen).
`esda` - Para a execução dos algoritmos do Índice de Moran e tipologia LISA.
Você pode instalar todas as dependências utilizando o `pip`:
```bash
pip install numpy pulp geopandas libpysal esda
```
Como Utilizar
Faça o clone deste repositório.
Certifique-se de que a malha vetorial (`.shp`) e a base de dados estão no mesmo diretório dos scripts.
Execute o script de otimização (DEA) para gerar os escores de eficiência.
Execute o script espacial para gerar as matrizes de vizinhança e rodar a simulação de Monte Carlo.

Componentes

1. Scripts de Código Python:

00_preparar_ambiente.py
01_gerar_mapa_aisp.py
02_consolidar_mvi.py
03_diagnostico_orcamento.py
04_consolidar_orcamento_populacao.py
05_calcular_dea.py
06_teste_moran_aisp.py
07_gerar_mapas_artigo.py
08_gerar_graficos_extras.py

2.Bases de Dados

base_dea_aisp.csv
Consulta_Detalhada_Atualizada_Dezembro_2023.csv
Despesas_Jan_2023.csv
IBGE-PR.csv
moran_aisp_resultados.csv
Mortes Violentas Intencionais_Tabela.csv
mvi_por_aisp.csv
relacao_municipios_aisp.csv
resultado_dea_aisp.csv

3.Malha Vetorial

malha_aisp_parana.shp (geometria principal)
malha_aisp_parana.shx (índice da geometria)
malha_aisp_parana.dbf (banco de dados dos atributos)
malha_aisp_parana.prj (sistema de coordenadas - SIRGAS 2000)
malha_aisp_parana.cpg (codificação de caracteres)

4. Arquivo de Orientação

README.md
---------------------------------------------------------------------------------------------------
