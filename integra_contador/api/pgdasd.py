"""Serviço PGDASD - Geração de DAS do Simples Nacional"""

import base64
import json
import logging
import re
from typing import Dict, Any, Optional, List

from integra_contador.api.client import SerproAPIClient
from integra_contador.api.auth import SerproAuthenticator
from integra_contador.config.settings import Settings
from integra_contador.models.das import Das

logger = logging.getLogger(__name__)


class PGDASDService(SerproAPIClient):
    """Serviço para geração de DAS (Documento de Arrecadação do Simples Nacional)"""
    
    # IDs do sistema e serviços conforme documentação
    ID_SISTEMA = "PGDASD"
    ID_SERVICO = "GERARDAS12"
    VERSAO_SISTEMA = "1.0"
    
    # Endpoint
    ENDPOINT_EMITIR = "/Emitir"
    
    def __init__(
        self,
        authenticator: SerproAuthenticator,
        settings: Optional[Settings] = None
    ):
        """
        Inicializa o serviço PGDASD.
        
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
    
    def _validar_periodo_apuracao(self, periodo: str) -> bool:
        """
        Valida formato do período de apuração (AAAAMM).
        
        Args:
            periodo: Período no formato AAAAMM
            
        Returns:
            True se válido
        """
        if not periodo or len(periodo) != 6:
            return False
        if not periodo.isdigit():
            return False
        ano = int(periodo[:4])
        mes = int(periodo[4:6])
        return 2000 <= ano <= 2100 and 1 <= mes <= 12
    
    def _validar_data_consolidacao(self, data: str) -> bool:
        """
        Valida formato da data de consolidação (AAAAMMDD).
        
        Args:
            data: Data no formato AAAAMMDD
            
        Returns:
            True se válido
        """
        if not data or len(data) != 8:
            return False
        if not data.isdigit():
            return False
        try:
            ano = int(data[:4])
            mes = int(data[4:6])
            dia = int(data[6:8])
            # Validação básica (não verifica se a data realmente existe)
            return 2000 <= ano <= 2100 and 1 <= mes <= 12 and 1 <= dia <= 31
        except ValueError:
            return False
    
    def gerar_das(
        self,
        cnpj: str,
        periodo_apuracao: str,
        data_consolidacao: Optional[str] = None
    ) -> List[Das]:
        """
        Gera DAS para uma empresa do Simples Nacional.
        
        Args:
            cnpj: CNPJ do contribuinte (com ou sem formatação)
            periodo_apuracao: Período de apuração no formato AAAAMM (ex: "202509")
            data_consolidacao: Data de consolidação no formato AAAAMMDD (opcional)
            
        Returns:
            Lista de objetos Das gerados
            
        Raises:
            ValueError: Se período ou data forem inválidos
            Exception: Se a geração falhar
        """
        # Normaliza CNPJ (remove formatação)
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        
        # Validações
        if not self._validar_periodo_apuracao(periodo_apuracao):
            raise ValueError(f"Período de apuração inválido: {periodo_apuracao}. Use formato AAAAMM (ex: 202509)")
        
        if data_consolidacao and not self._validar_data_consolidacao(data_consolidacao):
            raise ValueError(f"Data de consolidação inválida: {data_consolidacao}. Use formato AAAAMMDD (ex: 20250930)")
        
        logger.info(f"Gerando DAS para CNPJ: {cnpj_clean}, Período: {periodo_apuracao}")
        
        # Constrói payload de dados
        dados_payload = {
            "periodoApuracao": periodo_apuracao
        }
        
        if data_consolidacao:
            dados_payload["dataConsolidacao"] = data_consolidacao
        
        # Constrói pedido completo
        pedido = self._build_pedido_base(cnpj_clean)
        pedido["pedidoDados"]["idServico"] = self.ID_SERVICO
        pedido["pedidoDados"]["dados"] = json.dumps(dados_payload)
        
        url = f"{self.settings.API_BASE_URL}{self.ENDPOINT_EMITIR}"
        
        try:
            status_code, response_body, _ = self._make_request(
                url, method='POST', data=pedido
            )
            
            if status_code != 200:
                error_msg = f"Status HTTP inesperado ao gerar DAS: {status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            resultado = self._parse_response(response_body)
            
            # Verifica se há mensagens de erro
            mensagens = resultado.get('mensagens', [])
            if mensagens:
                for msg in mensagens:
                    if isinstance(msg, dict) and msg.get('codigo'):
                        logger.warning(f"Mensagem da API: {msg.get('texto', '')}")
            
            # Parseia dados aninhados
            dados_str = resultado.get('dados', '[]')
            if isinstance(dados_str, str):
                dados = json.loads(dados_str)
            else:
                dados = dados_str
            
            # A resposta pode ser uma lista de DAS ou um único objeto
            if not isinstance(dados, list):
                dados = [dados]
            
            # Processa cada DAS retornado
            das_list = []
            for das_data in dados:
                pdf_base64 = das_data.get('pdf')
                
                if not pdf_base64:
                    logger.warning("PDF não encontrado na resposta para um dos DAS")
                    continue
                
                # Decodifica base64 para bytes
                pdf_bytes = base64.b64decode(pdf_base64)
                
                # Cria objeto Das
                das_obj = Das.from_dict(das_data, pdf_bytes)
                das_list.append(das_obj)
                
                logger.info(
                    f"DAS gerado com sucesso - "
                    f"CNPJ: {das_obj.cnpjCompleto}, "
                    f"Período: {das_obj.detalhamento.periodoApuracao}, "
                    f"Documento: {das_obj.detalhamento.numeroDocumento}, "
                    f"Total: R$ {das_obj.detalhamento.valores.total:.2f}, "
                    f"PDF: {len(pdf_bytes)} bytes"
                )
            
            if not das_list:
                raise Exception("Nenhum DAS foi gerado na resposta da API")
            
            return das_list
            
        except Exception as e:
            logger.error(f"Erro ao gerar DAS: {e}")
            raise

