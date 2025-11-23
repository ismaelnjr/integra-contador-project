import json
import os


def carregar_empresas():
    """Carrega empresas do arquivo JSON"""
    arquivo_json = 'empresas.json'
    if os.path.exists(arquivo_json):
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_empresas(empresas):
    """Salva empresas no arquivo JSON"""
    arquivo_json = 'empresas.json'
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(empresas, f, indent=2, ensure_ascii=False)