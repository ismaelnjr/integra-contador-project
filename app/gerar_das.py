"""Script para gerar DAS em lote para empresas do Simples Nacional"""

import logging
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

# Adiciona o diretório raiz do projeto ao PYTHONPATH
# Permite executar o script de qualquer local
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from integra_contador.api.auth import SerproAuthenticator
from integra_contador.api.pgdasd import PGDASDService
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


def solicitar_periodo() -> str:
    """
    Solicita período de apuração ao usuário.
    
    Returns:
        Período no formato AAAAMM
    """
    while True:
        periodo_input = input(
            "\nDigite o período de apuração (formato MM/AAAA ou AAAAMM, ex: 09/2025 ou 202509): "
        ).strip()
        
        periodo_normalizado = normalizar_periodo(periodo_input)
        
        if periodo_normalizado:
            # Validação básica
            ano = int(periodo_normalizado[:4])
            mes = int(periodo_normalizado[4:6])
            if 2000 <= ano <= 2100 and 1 <= mes <= 12:
                return periodo_normalizado
            else:
                print("Erro: Ano deve estar entre 2000-2100 e mês entre 01-12")
        else:
            print("Erro: Formato inválido. Use MM/AAAA (ex: 09/2025) ou AAAAMM (ex: 202509)")


def solicitar_data_consolidacao() -> Optional[str]:
    """
    Solicita data de consolidação opcional ao usuário.
    
    Returns:
        Data no formato AAAAMMDD ou None se não informada
    """
    resposta = input(
        "\nDeseja informar data de consolidação? (s/N): "
    ).strip().lower()
    
    if resposta not in ['s', 'sim', 'y', 'yes']:
        return None
    
    while True:
        data_input = input(
            "Digite a data de consolidação (formato DD/MM/AAAA ou AAAAMMDD, ex: 30/09/2025 ou 20250930): "
        ).strip()
        
        # Formato DD/MM/AAAA
        match_dd_mm_aaaa = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', data_input)
        if match_dd_mm_aaaa:
            dia = match_dd_mm_aaaa.group(1).zfill(2)
            mes = match_dd_mm_aaaa.group(2).zfill(2)
            ano = match_dd_mm_aaaa.group(3)
            data_normalizada = f"{ano}{mes}{dia}"
            
            # Validação básica
            if len(data_normalizada) == 8 and data_normalizada.isdigit():
                return data_normalizada
            else:
                print("Erro: Data inválida")
                continue
        
        # Formato AAAAMMDD
        match_aaaammdd = re.match(r'^(\d{4})(\d{2})(\d{2})$', data_input)
        if match_aaaammdd:
            return data_input
        
        print("Erro: Formato inválido. Use DD/MM/AAAA (ex: 30/09/2025) ou AAAAMMDD (ex: 20250930)")


def gerar_das_empresa(
    service: PGDASDService,
    empresa,
    periodo_apuracao: str,
    data_consolidacao: Optional[str],
    output_path: str
) -> Tuple[bool, str]:
    """
    Gera DAS para uma empresa específica.
    
    Args:
        service: Instância do serviço PGDASD
        empresa: Objeto Empresa ou dicionário com dados da empresa
        periodo_apuracao: Período de apuração no formato AAAAMM
        data_consolidacao: Data de consolidação opcional no formato AAAAMMDD
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
        
        # Gera DAS
        das_list = service.gerar_das(
            cnpj=cnpj,
            periodo_apuracao=periodo_apuracao,
            data_consolidacao=data_consolidacao
        )
        
        # Salva cada DAS gerado
        for idx, das in enumerate(das_list):
            # Nome do arquivo: DAS_{cnpj}_{periodo}_{indice}.pdf
            nome_arquivo = f"DAS_{das.cnpjCompleto}_{periodo_apuracao}"
            if len(das_list) > 1:
                nome_arquivo += f"_{idx + 1}"
            nome_arquivo += ".pdf"
            
            caminho_completo = Path(output_path) / nome_arquivo
            
            # Salva PDF
            with open(caminho_completo, "wb") as f:
                f.write(das.pdf)
            
            logger.info(
                f"DAS salvo: {caminho_completo} | "
                f"Documento: {das.detalhamento.numeroDocumento} | "
                f"Total: R$ {das.detalhamento.valores.total:.2f}"
            )
        
        return True, f"Sucesso - {len(das_list)} DAS gerado(s)"
        
    except ValueError as e:
        error_msg = f"Erro de validação: {str(e)}"
        logger.error(f"Empresa ID {id_empresa} - {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Erro ao gerar DAS: {str(e)}"
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
        service = PGDASDService(authenticator)
        repository = EmpresaRepository()
        
        # Carrega empresas
        empresas = repository.load_all()
        
        if not empresas:
            print("Nenhuma empresa encontrada no arquivo empresas.json")
            sys.exit(1)
        
        print(f"\n{len(empresas)} empresa(s) encontrada(s)")
        
        # Solicita período
        periodo_apuracao = solicitar_periodo()
        print(f"Período selecionado: {periodo_apuracao}")
        
        # Solicita data de consolidação (opcional)
        data_consolidacao = solicitar_data_consolidacao()
        if data_consolidacao:
            print(f"Data de consolidação: {data_consolidacao}")
        
        # Confirmação
        print(f"\nProcessando {len(empresas)} empresa(s) para o período {periodo_apuracao}...")
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
            sucesso, mensagem = gerar_das_empresa(
                service=service,
                empresa=empresa,
                periodo_apuracao=periodo_apuracao,
                data_consolidacao=data_consolidacao,
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

