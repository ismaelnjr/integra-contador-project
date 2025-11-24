"""Serviço DCTFWEB - Geração de Guias de Pagamento"""

import base64
import json
import logging
from typing import Dict, Any, Optional, List

from integra_contador.api.client import SerproAPIClient
from integra_contador.api.auth import SerproAuthenticator
from integra_contador.api.validators import construir_dados_guia_dctfweb
from integra_contador.settings import Settings
from integra_contador.models.guia import GuiaDCTFWeb

logger = logging.getLogger(__name__)


class DCTFWEBService(SerproAPIClient):
    """Serviço para geração de guias de pagamento (Documento de Arrecadação) da DCTFWEB"""
    
    # IDs do sistema e serviços conforme documentação
    ID_SISTEMA = "DCTFWEB"
    ID_SERVICO = "GERARGUIA31"
    VERSAO_SISTEMA = "1.0"
    
    # Endpoint
    ENDPOINT_EMITIR = "/Emitir"
    
    def __init__(
        self,
        authenticator: SerproAuthenticator,
        settings: Optional[Settings] = None
    ):
        """
        Inicializa o serviço DCTFWEB.
        
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
    
    def gerar_guia(
        self,
        cnpj: str,
        dados_guia: Dict[str, Any]
    ) -> GuiaDCTFWeb:
        """
        Gera guia de pagamento para uma empresa.
        
        Args:
            cnpj: CNPJ do contribuinte (com ou sem formatação)
            dados_guia: Dicionário com dados necessários para gerar a guia.
                        Deve conter no mínimo:
                        - anoPA: Ano de apuração (formato AAAA, ex: "2025")
                        - mesPA: Mês de apuração (formato MM, ex: "10")
                        - categoria: (opcional, padrão: "GERAL_MENSAL")
            
        Returns:
            Objeto GuiaDCTFWeb com dados da guia e PDF
            
        Raises:
            ValueError: Se parâmetros forem inválidos
            Exception: Se a geração falhar
        """
        # Normaliza CNPJ (remove formatação)
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj_clean) != 14:
            raise ValueError(f"CNPJ inválido: {cnpj}. Deve conter 14 dígitos")
        
        # Valida e constrói dados da guia
        dados_validados = construir_dados_guia_dctfweb(dados_guia)
        
        logger.info(
            f"Gerando guia DCTFWEB para CNPJ: {cnpj_clean}, "
            f"Ano: {dados_validados['anoPA']}, Mês: {dados_validados['mesPA']}, "
            f"Categoria: {dados_validados['categoria']}"
        )
        
        # Constrói pedido completo
        pedido = self._build_pedido_base(cnpj_clean)
        pedido["pedidoDados"]["idServico"] = self.ID_SERVICO
        pedido["pedidoDados"]["dados"] = json.dumps(dados_validados)
        
        url = f"{self.settings.API_BASE_URL}{self.ENDPOINT_EMITIR}"
        
        try:
            status_code, response_body, _ = self._make_request(
                url, method='POST', data=pedido
            )
            
            if status_code != 200:
                error_msg = f"Status HTTP inesperado ao gerar guia: {status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            resultado = self._parse_response(response_body)
            
            # Verifica mensagens
            mensagens = resultado.get('mensagens', [])
            if mensagens:
                for msg in mensagens:
                    if isinstance(msg, dict) and msg.get('codigo'):
                        codigo = msg.get('codigo', '')
                        texto = msg.get('texto', '')
                        logger.info(f"Mensagem da API: {codigo} - {texto}")
            
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
                    raise ValueError("Não há dados de guia na resposta da API")
                try:
                    dados = json.loads(dados_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao parsear JSON de dados: {e}")
                    raise ValueError(f"Resposta da API contém dados inválidos: {str(e)}")
            else:
                dados = dados_str
            
            # Verifica se dados está vazio após parsear
            if not dados or (isinstance(dados, dict) and not dados):
                logger.warning("Nenhum dado de guia encontrado na resposta")
                raise ValueError("Não há dados de guia na resposta da API")
            
            # Extrai PDF base64
            pdf_base64 = dados.get('PDFByteArrayBase64') if isinstance(dados, dict) else None
            
            if not pdf_base64:
                logger.warning("PDF não encontrado na resposta")
                raise ValueError("PDF não encontrado na resposta da API")
            
            try:
                # Decodifica base64 para bytes
                pdf_bytes = base64.b64decode(pdf_base64)
                
                # Cria objeto GuiaDCTFWeb
                guia_obj = GuiaDCTFWeb.from_dict(dados, pdf_bytes)
                
                logger.info(
                    f"Guia gerada com sucesso - "
                    f"CNPJ: {guia_obj.cnpjCompleto if hasattr(guia_obj, 'cnpjCompleto') else cnpj_clean}, "
                    f"PDF: {len(pdf_bytes)} bytes"
                )
                
                return guia_obj
                
            except Exception as e:
                logger.error(f"Erro ao processar guia: {e}")
                raise
            
        except ValueError:
            # Re-lança ValueError sem modificar
            raise
        except Exception as e:
            logger.error(f"Erro ao gerar guia: {e}")
            raise

