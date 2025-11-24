"""Serviço PGDASD - Geração de DAS do Simples Nacional"""

import base64
import json
import logging
from typing import Dict, Any, Optional, List

from integra_contador.api.client import SerproAPIClient
from integra_contador.api.auth import SerproAuthenticator
from integra_contador.api.validators import (
    validar_periodo_apuracao,
    validar_data_consolidacao,
    verificar_mensagem_sem_valor_devido
)
from integra_contador.settings import Settings
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
            Lista de objetos Das gerados (pode ser vazia se não houver valor devido)
            
        Raises:
            ValueError: Se período ou data forem inválidos, ou se não houver valor devido
            Exception: Se a geração falhar
        """
        # Normaliza CNPJ (remove formatação)
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        
        # Validações
        if not validar_periodo_apuracao(periodo_apuracao):
            raise ValueError(f"Período de apuração inválido: {periodo_apuracao}. Use formato AAAAMM (ex: 202509)")
        
        if data_consolidacao and not validar_data_consolidacao(data_consolidacao):
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
            
            # Verifica mensagens primeiro
            mensagens = resultado.get('mensagens', [])
            if mensagens:
                for msg in mensagens:
                    if isinstance(msg, dict) and msg.get('codigo'):
                        codigo = msg.get('codigo', '')
                        texto = msg.get('texto', '')
                        logger.warning(f"Mensagem da API: {codigo} - {texto}")
                
                # Verifica se há mensagem indicando ausência de valor devido
                if verificar_mensagem_sem_valor_devido(mensagens):
                    logger.info(f"Não há valor devido para CNPJ {cnpj_clean}, período {periodo_apuracao}")
                    raise ValueError(
                        f"Não foi gerado DAS por não haver valor devido para o período {periodo_apuracao}. "
                        f"O valor já pode ter sido recolhido anteriormente."
                    )
            
            # Parseia dados aninhados
            dados_str = resultado.get('dados', None)
            
            # Trata casos onde dados pode ser None, string vazia, ou lista vazia
            if dados_str is None:
                logger.warning("Campo 'dados' não encontrado na resposta")
                raise ValueError("Resposta da API não contém dados válidos")
            
            # Se for string, tenta parsear
            if isinstance(dados_str, str):
                dados_str = dados_str.strip()
                if not dados_str or dados_str == 'null' or dados_str == '[]' or dados_str == '{}':
                    logger.warning("Campo 'dados' está vazio na resposta")
                    raise ValueError("Não há dados de DAS na resposta da API")
                try:
                    dados = json.loads(dados_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao parsear JSON de dados: {e}")
                    raise ValueError(f"Resposta da API contém dados inválidos: {str(e)}")
            else:
                dados = dados_str
            
            # Verifica se dados está vazio após parsear
            if not dados or (isinstance(dados, list) and len(dados) == 0):
                logger.warning("Nenhum dado de DAS encontrado na resposta")
                raise ValueError("Não há dados de DAS na resposta da API")
            
            # A resposta pode ser uma lista de DAS ou um único objeto
            if not isinstance(dados, list):
                dados = [dados]
            
            # Processa cada DAS retornado
            das_list = []
            for das_data in dados:
                # Verifica se é um objeto válido (não None, não vazio)
                if not das_data or (isinstance(das_data, dict) and not das_data):
                    logger.warning("Dados de DAS inválidos ou vazios")
                    continue
                
                pdf_base64 = das_data.get('pdf') if isinstance(das_data, dict) else None
                
                if not pdf_base64:
                    logger.warning("PDF não encontrado na resposta para um dos DAS")
                    continue
                
                try:
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
                except Exception as e:
                    logger.error(f"Erro ao processar DAS: {e}")
                    continue
            
            if not das_list:
                raise ValueError("Nenhum DAS válido foi gerado na resposta da API")
            
            return das_list
            
        except ValueError:
            # Re-lança ValueError sem modificar
            raise
        except Exception as e:
            logger.error(f"Erro ao gerar DAS: {e}")
            raise

