"""Script para gerar relatórios de situação fiscal em lote para empresas"""

import logging
import sys
from pathlib import Path
from typing import Tuple

# Adiciona o diretório raiz do projeto ao PYTHONPATH
# Permite executar o script de qualquer local
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from integra_contador.api.auth import SerproAuthenticator
from integra_contador.api.sitfis import SITFISService
from integra_contador.settings import Settings
from app.repositories.empresa_repository import EmpresaRepository

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def gerar_relatorio_empresa(
    service: SITFISService,
    empresa,
    output_path: str
) -> Tuple[bool, str]:
    """
    Gera relatório de situação fiscal para uma empresa específica.
    
    Args:
        service: Instância do serviço SITFIS
        empresa: Objeto Empresa ou dicionário com dados da empresa
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
        
        # Gera relatório completo (solicita protocolo, aguarda e emite PDF)
        # Usa salvar_pdf=False para ter controle sobre o nome e local do arquivo
        protocolo, pdf_bytes = service.gerar_relatorio_completo(
            cnpj=cnpj,
            salvar_pdf=False
        )
        
        # Nome do arquivo: relatoriofiscal{cnpj}.pdf
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        nome_arquivo = f"relatoriofiscal{cnpj_clean}.pdf"
        caminho_completo = Path(output_path) / nome_arquivo
        
        # Salva PDF
        with open(caminho_completo, "wb") as f:
            f.write(pdf_bytes)
        
        logger.info(
            f"Relatório salvo: {caminho_completo} | "
            f"Protocolo: {protocolo} | "
            f"Tamanho: {len(pdf_bytes)} bytes"
        )
        
        return True, f"Sucesso - Protocolo: {protocolo}"
        
    except ValueError as e:
        error_msg = f"Erro de validação: {str(e)}"
        logger.error(f"Empresa ID {id_empresa} - {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Erro ao gerar relatório: {str(e)}"
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
        service = SITFISService(authenticator)
        repository = EmpresaRepository()
        
        # Carrega empresas
        empresas = repository.load_all()
        
        if not empresas:
            print("Nenhuma empresa encontrada no arquivo empresas.json")
            sys.exit(1)
        
        print(f"\n{len(empresas)} empresa(s) encontrada(s)")
        
        # Confirmação
        print(f"\nProcessando {len(empresas)} empresa(s) para gerar relatórios de situação fiscal...")
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
            sucesso, mensagem = gerar_relatorio_empresa(
                service=service,
                empresa=empresa,
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

