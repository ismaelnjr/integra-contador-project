"""Módulo de integração com API Serpro"""

from integra_contador.api.auth import SerproAuthenticator
from integra_contador.api.client import SerproAPIClient
from integra_contador.api.sitfis import SITFISService
from integra_contador.api.pgdasd import PGDASDService
from integra_contador.api.dctfweb import DCTFWEBService

__all__ = [
    'SerproAuthenticator',
    'SerproAPIClient',
    'SITFISService',
    'PGDASDService',
    'DCTFWEBService',
]

