from pathlib import Path

diretorio_base = Path(r"C:\projeto_seguranca_pr")

pastas = [
    diretorio_base / "dados_brutos",
    diretorio_base / "mapas",
    diretorio_base / "dados_limpos",
    diretorio_base / "resultados_visuais"
]

for pasta in pastas:
    pasta.mkdir(parents=True, exist_ok=True)

print("Estrutura de diretórios criada com sucesso.")