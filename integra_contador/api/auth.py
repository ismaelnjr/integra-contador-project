"""Autenticação na API Serpro"""

import base64
import json
import logging
from typing import Dict, Optional
from requests_pkcs12 import post

from integra_contador.settings import Settings

logger = logging.getLogger(__name__)


class SerproAuthenticator:
    """Gerencia autenticação na API Serpro"""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Inicializa o autenticador.
        
        Args:
            settings: Instância de Settings. Se None, usa Settings padrão.
        """
        self.settings = settings or Settings
        self._token_cache: Optional[Dict[str, str]] = None
    
    def _encode_base64(self, credentials: str) -> str:
        """
        Codifica credenciais em base64.
        
        Args:
            credentials: String no formato "key:secret"
            
        Returns:
            String codificada em base64
        """
        return base64.b64encode(credentials.encode("utf8")).decode("utf8")
    
    def authenticate(self) -> Dict[str, str]:
        """
        Autentica na API Serpro e retorna tokens de acesso.
        
        Returns:
            Dicionário com 'access_token' e 'jwt_token'
            
        Raises:
            Exception: Se a autenticação falhar
        """
        if self._token_cache:
            logger.debug("Usando token em cache")
            return self._token_cache
        
        url = self.settings.AUTH_URL
        
        # Prepara credenciais
        credentials = f"{self.settings.CONSUMER_KEY}:{self.settings.CONSUMER_SECRET}"
        auth_header = f"Basic {self._encode_base64(credentials)}"
        
        headers = {
            "Authorization": auth_header,
            "role-type": "TERCEIROS",
            "content-type": "application/x-www-form-urlencoded"
        }
        
        body = {'grant_type': 'client_credentials'}
        
        try:
            logger.info("Autenticando na API Serpro...")
            response = post(
                url,
                data=body,
                headers=headers,
                verify=True,
                pkcs12_filename=self.settings.CERTIFICADO_PATH,
                pkcs12_password=self.settings.CERTIFICADO_SENHA
            )
            
            response.raise_for_status()
            
            result = json.loads(response.content.decode("utf-8"))
            tokens = {
                'access_token': result['access_token'],
                'jwt_token': result['jwt_token']
            }
            
            self._token_cache = tokens
            logger.info("Autenticação realizada com sucesso")
            
            return tokens
            
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            raise Exception(f"Falha na autenticação: {str(e)}") from e
    
    def clear_cache(self) -> None:
        """Limpa o cache de tokens, forçando nova autenticação."""
        self._token_cache = None
        logger.debug("Cache de tokens limpo")

