"""Script para gerar guias DCTFWEB em lote para empresas"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Adiciona o diretório raiz do projeto ao PYTHONPATH
# Permite executar o script de qualquer local
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from integra_contador.api.auth import SerproAuthenticator
from integra_contador.api.dctfweb import DCTFWEBService
from integra_contador.settings import Settings
from app.repositories.empresa_repository import EmpresaRepository

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalizar_periodo(periodo_input: str) -> Optional[str]:
    """
    Normaliza período de entrada para formato AAAAMM.
    
    Aceita formatos:
    - MM/AAAA (ex: 09/2025)
    - AAAAMM (ex: 202509)
    
    Args:
        periodo_input: Período em qualquer formato aceito
        
    Returns:
        Período no formato AAAAMM ou None se inválido
    """
    periodo_input = periodo_input.strip()
    
    # Formato MM/AAAA
    match_mm_aaaa = re.match(r'^(\d{1,2})/(\d{4})$', periodo_input)
    if match_mm_aaaa:
        mes = match_mm_aaaa.group(1).zfill(2)
        ano = match_mm_aaaa.group(2)
        return f"{ano}{mes}"
    
    # Formato AAAAMM
    match_aaaamm = re.match(r'^(\d{4})(\d{2})$', periodo_input)
    if match_aaaamm:
        return periodo_input
    
    return None


def solicitar_ano_pa() -> Optional[str]:
    """
    Solicita ano de apuração ao usuário.
    
    Returns:
        Ano no formato AAAA ou None se não informado
    """
    while True:
        ano_input = input(
            "\nDigite o ano de apuração (formato AAAA, ex: 2025): "
        ).strip()
        
        if not ano_input:
            return None
        
        if len(ano_input) == 4 and ano_input.isdigit():
            ano_int = int(ano_input)
            if 2000 <= ano_int <= 2100:
                return ano_input
            else:
                print("Erro: Ano deve estar entre 2000-2100")
        else:
            print("Erro: Formato inválido. Use formato AAAA (ex: 2025)")


def solicitar_mes_pa() -> Optional[str]:
    """
    Solicita mês de apuração ao usuário.
    
    Returns:
        Mês no formato MM ou None se não informado
    """
    while True:
        mes_input = input(
            "Digite o mês de apuração (formato MM, ex: 10 ou 01): "
        ).strip()
        
        if not mes_input:
            return None
        
        if mes_input.isdigit():
            mes_int = int(mes_input)
            if 1 <= mes_int <= 12:
                return f"{mes_int:02d}"
            else:
                print("Erro: Mês deve estar entre 01-12")
        else:
            print("Erro: Formato inválido. Use formato MM (ex: 10 ou 01)")


def solicitar_dados_guia() -> Dict[str, Any]:
    """
    Solicita dados para gerar a guia.
    
    Returns:
        Dicionário com dados da guia (anoPA e mesPA são obrigatórios)
    """
    dados_guia = {}
    
    # Solicita ano de apuração (obrigatório)
    ano_pa = solicitar_ano_pa()
    if ano_pa:
        dados_guia['anoPA'] = ano_pa
    
    # Solicita mês de apuração (obrigatório)
    mes_pa = solicitar_mes_pa()
    if mes_pa:
        dados_guia['mesPA'] = mes_pa
    
    # Pergunta sobre categoria (opcional)
    resposta_categoria = input(
        "\nDeseja informar categoria? (padrão: GERAL_MENSAL) (s/N): "
    ).strip().lower()
    
    if resposta_categoria in ['s', 'sim', 'y', 'yes']:
        categoria = input("Digite a categoria: ").strip()
        if categoria:
            dados_guia['categoria'] = categoria
    
    # Pergunta se deseja informar dados adicionais via JSON
    resposta = input(
        "\nDeseja informar dados adicionais da guia em formato JSON? (s/N): "
    ).strip().lower()
    
    if resposta in ['s', 'sim', 'y', 'yes']:
        print("\nDigite os dados adicionais em formato JSON (ex: {\"campo1\": \"valor1\", \"campo2\": \"valor2\"})")
        print("Ou pressione Enter para pular:")
        json_input = input().strip()
        
        if json_input:
            try:
                dados_adicionais = json.loads(json_input)
                dados_guia.update(dados_adicionais)
            except json.JSONDecodeError as e:
                print(f"Erro ao parsear JSON: {e}")
                print("Continuando sem dados adicionais...")
    
    return dados_guia


def gerar_guia_empresa(
    service: DCTFWEBService,
    empresa,
    dados_guia: Dict[str, Any],
    output_path: str
) -> Tuple[bool, str]:
    """
    Gera guia DCTFWEB para uma empresa específica.
    
    Args:
        service: Instância do serviço DCTFWEB
        empresa: Objeto Empresa ou dicionário com dados da empresa
        dados_guia: Dicionário com dados necessários para gerar a guia
        output_path: Caminho para salvar os PDFs
        
    Returns:
        Tupla (sucesso: bool, mensagem: str)
    """
    # Suporta tanto objeto Empresa quanto dicionário
    if hasattr(empresa, 'cnpj'):
        # É um objeto Empresa
        cnpj = empresa.cnpj
        razao = empresa.razao
        id_empresa = empresa.idempresas
    else:
        # É um dicionário
        cnpj = empresa.get('cnpj', '')
        razao = empresa.get('razao', 'N/A')
        id_empresa = empresa.get('idempresas', 'N/A')
    
    try:
        logger.info(f"Processando empresa ID {id_empresa} - {razao} (CNPJ: {cnpj})")
        
        # Gera guia
        guia = service.gerar_guia(
            cnpj=cnpj,
            dados_guia=dados_guia
        )
        
        # Nome do arquivo: GUIA_DCTFWEB_{cnpj}_{anoPA}_{mesPA}.pdf
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        ano_pa = dados_guia.get('anoPA', '')
        mes_pa = dados_guia.get('mesPA', '')
        nome_arquivo = f"GUIA_DCTFWEB_{cnpj_clean}"
        if ano_pa and mes_pa:
            nome_arquivo += f"_{ano_pa}{mes_pa}"
        nome_arquivo += ".pdf"
        
        caminho_completo = Path(output_path) / nome_arquivo
        
        # Salva PDF
        with open(caminho_completo, "wb") as f:
            f.write(guia.pdf)
        
        logger.info(
            f"Guia salva: {caminho_completo} | "
            f"CNPJ: {guia.cnpjCompleto or cnpj_clean} | "
            f"PDF: {len(guia.pdf)} bytes"
        )
        
        return True, f"Sucesso - Guia gerada"
        
    except ValueError as e:
        error_msg = f"Erro de validação: {str(e)}"
        logger.error(f"Empresa ID {id_empresa} - {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Erro ao gerar guia: {str(e)}"
        logger.error(f"Empresa ID {id_empresa} - {error_msg}")
        return False, error_msg


def main():
    """Função principal"""
    try:
        # Valida configurações
        Settings.validate()
        logger.info("Configurações validadas com sucesso")
        
        # Inicializa componentes
        authenticator = SerproAuthenticator()
        service = DCTFWEBService(authenticator)
        repository = EmpresaRepository()
        
        # Carrega empresas
        empresas = repository.load_all()
        
        if not empresas:
            print("Nenhuma empresa encontrada no arquivo empresas.json")
            sys.exit(1)
        
        print(f"\n{len(empresas)} empresa(s) encontrada(s)")
        
        # Solicita dados da guia
        dados_guia = solicitar_dados_guia()
        
        # Valida se anoPA e mesPA foram informados
        if not dados_guia.get('anoPA') or not dados_guia.get('mesPA'):
            print("\nErro: Ano e mês de apuração são obrigatórios!")
            sys.exit(1)
        
        print(f"\nDados da guia: {json.dumps(dados_guia, indent=2, ensure_ascii=False)}")
        
        # Confirmação
        print(f"\nProcessando {len(empresas)} empresa(s)...")
        confirmacao = input("Deseja continuar? (S/n): ").strip().lower()
        if confirmacao in ['n', 'nao', 'no', 'não']:
            print("Operação cancelada pelo usuário")
            sys.exit(0)
        
        # Processa empresas
        sucessos = 0
        falhas = 0
        resultados = []
        
        output_path = Settings.PDF_OUTPUT_PATH
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*80)
        print("INICIANDO PROCESSAMENTO")
        print("="*80)
        
        for empresa in empresas:
            sucesso, mensagem = gerar_guia_empresa(
                service=service,
                empresa=empresa,
                dados_guia=dados_guia,
                output_path=output_path
            )
            
            # Extrai dados da empresa (suporta objeto ou dicionário)
            if hasattr(empresa, 'razao'):
                empresa_nome = empresa.razao
                empresa_cnpj = empresa.cnpj
            else:
                empresa_nome = empresa.get('razao', 'N/A')
                empresa_cnpj = empresa.get('cnpj', 'N/A')
            
            resultados.append({
                'empresa': empresa_nome,
                'cnpj': empresa_cnpj,
                'sucesso': sucesso,
                'mensagem': mensagem
            })
            
            if sucesso:
                sucessos += 1
            else:
                falhas += 1
        
        # Resumo final
        print("\n" + "="*80)
        print("RESUMO DO PROCESSAMENTO")
        print("="*80)
        print(f"Total de empresas: {len(empresas)}")
        print(f"Sucessos: {sucessos}")
        print(f"Falhas: {falhas}")
        print(f"\nPDFs salvos em: {output_path}")
        
        if falhas > 0:
            print("\nEmpresas com falha:")
            for resultado in resultados:
                if not resultado['sucesso']:
                    print(f"  - {resultado['empresa']} ({resultado['cnpj']}): {resultado['mensagem']}")
        
        print("\n" + "="*80)
        
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        print(f"\nErro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

