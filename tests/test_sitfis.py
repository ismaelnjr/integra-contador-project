"""Caso de uso de teste para serviço SITFIS"""

import logging
import sys
from pathlib import Path

# Adiciona integra_contador ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from integra_contador.api.auth import SerproAuthenticator
from integra_contador.api.sitfis import SITFISService
from integra_contador.config.settings import Settings
from integra_contador.models.empresa import Empresa
from integra_contador.repositories.empresa_repository import EmpresaRepository

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Executa caso de uso de teste completo"""
    
    try:
        # Valida configurações
        logger.info("Validando configurações...")
        Settings.validate()
        logger.info("Configurações válidas ✓")
        
        # Inicializa componentes
        logger.info("Inicializando componentes...")
        authenticator = SerproAuthenticator()
        sitfis_service = SITFISService(authenticator)
        empresa_repo = EmpresaRepository()
        
        # Carrega empresas
        logger.info("Carregando empresas...")
        empresas = empresa_repo.load_all()
        
        if not empresas:
            logger.warning("Nenhuma empresa encontrada em empresas.json")
            return
        
        logger.info(f"Encontradas {len(empresas)} empresa(s)")
        
        # Processa cada empresa
        for empresa in empresas:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processando: {empresa.razao} (CNPJ: {empresa.cnpj})")
            logger.info(f"{'='*60}")
            
            try:
                # Verifica se já tem protocolo
                if empresa.has_protocolo():
                    logger.info(f"Usando protocolo existente: {empresa.protocoloRelatorio}")
                    protocolo = empresa.protocoloRelatorio
                else:
                    # Solicita novo protocolo
                    logger.info("Solicitando novo protocolo...")
                    protocolo, tempo_espera = sitfis_service.solicitar_relatorio(empresa.cnpj)
                    
                    # Atualiza protocolo no repositório
                    empresa_repo.update_protocolo(empresa.idempresas, protocolo)
                    logger.info(f"Protocolo salvo: {protocolo}")
                    
                    # Aguarda se necessário
                    if tempo_espera:
                        logger.info(f"Aguardando {tempo_espera}ms...")
                        import time
                        time.sleep(tempo_espera / 1000)
                
                # Emite relatório
                logger.info("Emitindo relatório...")
                pdf_bytes = sitfis_service.emitir_relatorio(empresa.cnpj, protocolo)
                
                # Salva PDF
                cnpj_clean = ''.join(filter(str.isdigit, empresa.cnpj))
                nome_arquivo = f"relatoriofiscal{cnpj_clean}.pdf"
                caminho_pdf = f"{Settings.PDF_OUTPUT_PATH}{nome_arquivo}"
                
                with open(caminho_pdf, "wb") as f:
                    f.write(pdf_bytes)
                
                logger.info(f"✓ PDF salvo em: {caminho_pdf}")
                logger.info(f"✓ Tamanho do arquivo: {len(pdf_bytes)} bytes")
                
                # Limpa protocolo após gerar PDF
                empresa_repo.clear_protocolo(empresa.idempresas)
                logger.info("✓ Protocolo limpo após geração do PDF")
                
                logger.info(f"✓ Processamento concluído para {empresa.razao}")
                
            except Exception as e:
                logger.error(f"✗ Erro ao processar {empresa.razao}: {e}")
                logger.exception("Detalhes do erro:")
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info("Processamento finalizado!")
        logger.info(f"{'='*60}")
        
    except ValueError as e:
        logger.error(f"Erro de configuração: {e}")
        logger.error("Verifique o arquivo .env e as variáveis de ambiente")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        logger.exception("Detalhes do erro:")
        sys.exit(1)


if __name__ == "__main__":
    main()

