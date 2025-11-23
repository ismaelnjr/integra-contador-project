"""Serviço SITFIS - Relatório de Situação Fiscal"""

import base64
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple

from integra_contador.api.client import SerproAPIClient
from integra_contador.api.auth import SerproAuthenticator
from integra_contador.config.settings import Settings

logger = logging.getLogger(__name__)


class SITFISService(SerproAPIClient):
    """Serviço para geração de relatórios de situação fiscal (SITFIS)"""
    
    # IDs do sistema e serviços conforme documentação
    ID_SISTEMA = "SITFIS"
    ID_SERVICO_SOLICITAR = "SOLICITARPROTOCOLO91"
    ID_SERVICO_EMITIR = "RELATORIOSITFIS92"
    VERSAO_SISTEMA = "2.0"
    
    # Endpoints
    ENDPOINT_APOIAR = "/Apoiar"
    ENDPOINT_EMITIR = "/Emitir"
    
    def __init__(
        self,
        authenticator: SerproAuthenticator,
        settings: Optional[Settings] = None
    ):
        """
        Inicializa o serviço SITFIS.
        
        Args:
            authenticator: Instância do autenticador
            settings: Instância de Settings. Se None, usa Settings padrão.
        """
        super().__init__(authenticator, settings)
        self.settings = settings or Settings
    
    def _build_pedido_base(self, cnpj_contribuinte: str) -> Dict[str, Any]:
        """
        Constrói estrutura base de pedido.
        
        Args:
            cnpj_contribuinte: CNPJ do contribuinte
            
        Returns:
            Dicionário com estrutura de pedido
        """
        return {
            "contratante": {
                "numero": self.settings.CONTRATANTE_CNPJ,
                "tipo": 2
            },
            "autorPedidoDados": {
                "numero": self.settings.AUTOR_PEDIDO_CNPJ,
                "tipo": 2
            },
            "contribuinte": {
                "numero": cnpj_contribuinte,
                "tipo": 2
            },
            "pedidoDados": {
                "idSistema": self.ID_SISTEMA,
                "versaoSistema": self.VERSAO_SISTEMA
            }
        }
    
    def solicitar_relatorio(self, cnpj: str) -> Tuple[str, Optional[int]]:
        """
        Solicita protocolo para geração de relatório de situação fiscal.
        
        Args:
            cnpj: CNPJ do contribuinte (com ou sem formatação)
            
        Returns:
            Tupla com (protocolo, tempo_espera_ms)
            - protocolo: Protocolo obtido
            - tempo_espera_ms: Tempo de espera em milissegundos (None se status 304)
            
        Raises:
            Exception: Se a solicitação falhar
        """
        # Normaliza CNPJ (remove formatação)
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        
        logger.info(f"Solicitando relatório SITFIS para CNPJ: {cnpj_clean}")
        
        # Constrói payload
        pedido = self._build_pedido_base(cnpj_clean)
        pedido["pedidoDados"]["idServico"] = self.ID_SERVICO_SOLICITAR
        pedido["pedidoDados"]["dados"] = ""
        
        url = f"{self.settings.API_BASE_URL}{self.ENDPOINT_APOIAR}"
        
        try:
            status_code, response_body, response_headers = self._make_request(
                url, method='POST', data=pedido
            )
            
            # Status 304: Não modificado (usa protocolo do cache/ETag)
            if status_code == 304:
                logger.info("Status 304 - Relatório não modificado, extraindo protocolo do ETag")
                protocolo = self._extract_protocolo_from_etag(response_headers)
                
                if protocolo:
                    logger.info(f"Protocolo extraído do ETag: {protocolo}")
                    return protocolo, None
                else:
                    raise Exception("Protocolo não encontrado no header ETag")
            
            # Status 200: Nova solicitação
            elif status_code == 200:
                logger.info("Status 200 - Nova solicitação processada")
                resultado = self._parse_response(response_body)
                
                # Parseia dados aninhados
                dados_str = resultado.get('dados', '{}')
                dados = json.loads(dados_str) if isinstance(dados_str, str) else dados_str
                
                protocolo = dados.get('protocoloRelatorio')
                tempo_espera = dados.get('tempoEspera')
                
                if not protocolo:
                    raise Exception("Protocolo não encontrado na resposta")
                
                logger.info(f"Protocolo obtido: {protocolo}, Tempo de espera: {tempo_espera}ms")
                
                return protocolo, tempo_espera
            
            else:
                error_msg = f"Status HTTP inesperado: {status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Erro ao solicitar relatório: {e}")
            raise
    
    def emitir_relatorio(self, cnpj: str, protocolo: str) -> bytes:
        """
        Emite relatório de situação fiscal em PDF.
        
        Args:
            cnpj: CNPJ do contribuinte (com ou sem formatação)
            protocolo: Protocolo obtido na solicitação
            
        Returns:
            Conteúdo do PDF em bytes
            
        Raises:
            Exception: Se a emissão falhar
        """
        # Normaliza CNPJ
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        
        logger.info(f"Emitindo relatório SITFIS para CNPJ: {cnpj_clean}, Protocolo: {protocolo}")
        
        # Constrói payload
        pedido = self._build_pedido_base(cnpj_clean)
        pedido["pedidoDados"]["idServico"] = self.ID_SERVICO_EMITIR
        pedido["pedidoDados"]["dados"] = json.dumps({
            "protocoloRelatorio": protocolo
        })
        
        url = f"{self.settings.API_BASE_URL}{self.ENDPOINT_EMITIR}"
        
        try:
            status_code, response_body, _ = self._make_request(
                url, method='POST', data=pedido
            )
            
            if status_code != 200:
                error_msg = f"Status HTTP inesperado ao emitir: {status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            resultado = self._parse_response(response_body)
            
            # Parseia dados aninhados
            dados_str = resultado.get('dados', '{}')
            dados = json.loads(dados_str) if isinstance(dados_str, str) else dados_str
            
            pdf_base64 = dados.get('pdf')
            
            if not pdf_base64:
                raise Exception("PDF não encontrado na resposta")
            
            # Decodifica base64 para bytes
            pdf_bytes = base64.b64decode(pdf_base64)
            logger.info(f"PDF gerado com sucesso ({len(pdf_bytes)} bytes)")
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Erro ao emitir relatório: {e}")
            raise
    
    def gerar_relatorio_completo(
        self,
        cnpj: str,
        salvar_pdf: bool = True,
        nome_arquivo: Optional[str] = None
    ) -> Tuple[str, bytes]:
        """
        Executa fluxo completo: solicitar e emitir relatório.
        
        Args:
            cnpj: CNPJ do contribuinte
            salvar_pdf: Se True, salva PDF no diretório configurado
            nome_arquivo: Nome do arquivo PDF (se None, usa CNPJ)
            
        Returns:
            Tupla com (protocolo, pdf_bytes)
        """
        # Solicita protocolo
        protocolo, tempo_espera = self.solicitar_relatorio(cnpj)
        
        # Aguarda tempo necessário se fornecido
        if tempo_espera:
            logger.info(f"Aguardando {tempo_espera}ms antes de emitir...")
            time.sleep(tempo_espera / 1000)
        
        # Emite relatório
        pdf_bytes = self.emitir_relatorio(cnpj, protocolo)
        
        # Salva PDF se solicitado
        if salvar_pdf:
            if not nome_arquivo:
                cnpj_clean = ''.join(filter(str.isdigit, cnpj))
                nome_arquivo = f"relatoriofiscal{cnpj_clean}.pdf"
            
            caminho_completo = f"{self.settings.PDF_OUTPUT_PATH}{nome_arquivo}"
            
            with open(caminho_completo, "wb") as f:
                f.write(pdf_bytes)
            
            logger.info(f"PDF salvo em: {caminho_completo}")
        
        return protocolo, pdf_bytes

