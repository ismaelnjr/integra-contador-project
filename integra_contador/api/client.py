"""Cliente HTTP base para API Serpro"""

import json
import logging
import re
from io import BytesIO
from typing import Dict, Any, Optional, Tuple
import pycurl

from integra_contador.api.auth import SerproAuthenticator
from integra_contador.settings import Settings

logger = logging.getLogger(__name__)


class SerproAPIClient:
    """Cliente HTTP base para comunicação com API Serpro"""
    
    def __init__(
        self,
        authenticator: SerproAuthenticator,
        settings: Optional[Settings] = None
    ):
        """
        Inicializa o cliente API.
        
        Args:
            authenticator: Instância do autenticador
            settings: Instância de Settings. Se None, usa Settings padrão.
        """
        self.authenticator = authenticator
        self.settings = settings or Settings
        self._tokens: Optional[Dict[str, str]] = None
    
    def _get_tokens(self) -> Dict[str, str]:
        """
        Obtém tokens de autenticação.
        
        Returns:
            Dicionário com tokens
        """
        if not self._tokens:
            self._tokens = self.authenticator.authenticate()
        return self._tokens
    
    def _get_headers(self) -> list:
        """
        Prepara headers HTTP para requisições.
        
        Returns:
            Lista de headers no formato pycurl
        """
        tokens = self._get_tokens()
        return [
            f'jwt_token:{tokens["jwt_token"]}',
            f'Authorization: Bearer {tokens["access_token"]}',
            'Content-Type: application/json',
            'accept: text/plain'
        ]
    
    def _make_request(
        self,
        url: str,
        method: str = 'POST',
        data: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, bytes, str]:
        """
        Realiza requisição HTTP para a API.
        
        Args:
            url: URL completa do endpoint
            method: Método HTTP (POST, GET, etc.)
            data: Dados a serem enviados (será convertido para JSON)
            
        Returns:
            Tupla com (status_code, response_body, response_headers)
            
        Raises:
            Exception: Se a requisição falhar
        """
        buffer = BytesIO()
        header_buffer = BytesIO()
        
        curl = pycurl.Curl()
        
        try:
            curl.setopt(curl.URL, url)
            curl.setopt(curl.HTTPHEADER, self._get_headers())
            curl.setopt(curl.HEADERFUNCTION, header_buffer.write)
            curl.setopt(curl.WRITEDATA, buffer)
            
            if method.upper() == 'POST' and data:
                post_data = json.dumps(data)
                curl.setopt(curl.POSTFIELDS, post_data)
            
            logger.debug(f"Enviando requisição {method} para {url}")
            curl.perform()
            
            status_code = curl.getinfo(curl.RESPONSE_CODE)
            response_body = buffer.getvalue()
            response_headers = header_buffer.getvalue().decode('utf-8')
            
            logger.debug(f"Resposta recebida: status {status_code}")
            
            return status_code, response_body, response_headers
            
        except Exception as e:
            logger.error(f"Erro na requisição HTTP: {e}")
            raise Exception(f"Falha na requisição: {str(e)}") from e
            
        finally:
            curl.close()
    
    def _parse_response(self, response_body: bytes) -> Dict[str, Any]:
        """
        Parseia resposta JSON da API.
        
        Args:
            response_body: Corpo da resposta em bytes
            
        Returns:
            Dicionário com dados parseados
        """
        try:
            return json.loads(response_body.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON: {e}")
            raise ValueError(f"Resposta inválida da API: {str(e)}") from e
    
    def _extract_protocolo_from_etag(self, headers: str) -> Optional[str]:
        """
        Extrai protocolo do header ETag quando status é 304.
        
        Args:
            headers: Headers HTTP como string
            
        Returns:
            Protocolo extraído ou None se não encontrado
        """
        match = re.search(r'etag:\s*"protocoloRelatorio:([^\s"]+)', headers.lower())
        if match:
            return match.group(1)
        return None

