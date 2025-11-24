"""Configurações centralizadas do sistema"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


class Settings:
    """Gerencia configurações da aplicação via variáveis de ambiente"""
    
    # URLs da API
    AUTH_URL: str = os.getenv(
        'AUTH_URL',
        'https://autenticacao.sapi.serpro.gov.br/authenticate'
    )
    API_BASE_URL: str = os.getenv(
        'API_BASE_URL',
        'https://gateway.apiserpro.serpro.gov.br/integra-contador/v1'
    )
    
    # Credenciais de autenticação
    CONSUMER_KEY: str = os.getenv('CONSUMER_KEY', '')
    CONSUMER_SECRET: str = os.getenv('CONSUMER_SECRET', '')
    
    # Certificado digital
    CERTIFICADO_PATH: str = os.getenv('CERTIFICADO_PATH', '')
    CERTIFICADO_SENHA: str = os.getenv('CERTIFICADO_SENHA', '')
    
    # CNPJs
    CONTRATANTE_CNPJ: str = os.getenv('CONTRATANTE_CNPJ', '')
    AUTOR_PEDIDO_CNPJ: str = os.getenv('AUTOR_PEDIDO_CNPJ', '')
    
    # Paths
    EMPRESAS_JSON_PATH: str = os.getenv(
        'EMPRESAS_JSON_PATH',
        str(Path(__file__).parent.parent / 'empresas.json')
    )
    PDF_OUTPUT_PATH: str = os.getenv(
        'PDF_OUTPUT_PATH',
        'C:\\integracontador\\'
    )
    
    @classmethod
    def validate(cls) -> None:
        """
        Valida se todas as configurações obrigatórias estão presentes.
        
        Raises:
            ValueError: Se alguma configuração obrigatória estiver faltando.
        """
        required = {
            'CONSUMER_KEY': cls.CONSUMER_KEY,
            'CONSUMER_SECRET': cls.CONSUMER_SECRET,
            'CERTIFICADO_PATH': cls.CERTIFICADO_PATH,
            'CERTIFICADO_SENHA': cls.CERTIFICADO_SENHA,
            'CONTRATANTE_CNPJ': cls.CONTRATANTE_CNPJ,
            'AUTOR_PEDIDO_CNPJ': cls.AUTOR_PEDIDO_CNPJ,
        }
        
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(
                f'Configurações obrigatórias faltando: {", ".join(missing)}. '
                'Configure-as no arquivo .env ou como variáveis de ambiente.'
            )
        
        # Valida se o certificado existe
        if not os.path.exists(cls.CERTIFICADO_PATH):
            raise FileNotFoundError(
                f'Certificado não encontrado: {cls.CERTIFICADO_PATH}'
            )
        
        # Cria diretório de saída se não existir
        os.makedirs(cls.PDF_OUTPUT_PATH, exist_ok=True)

