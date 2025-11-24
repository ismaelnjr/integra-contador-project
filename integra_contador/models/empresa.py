"""Modelo de dados Empresa"""

import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Empresa:
    """
    Representa uma empresa no sistema.
    
    Nota sobre nomenclatura:
    Os atributos estão em camelCase (ex: protocoloRelatorio) para manter
    compatibilidade direta com:
    - A API Serpro que retorna dados neste formato
    - O arquivo empresas.json que usa este formato
    - Evita necessidade de mapeamento/conversão nos métodos from_dict/to_dict
    """
    
    idempresas: int
    cnpj: str
    razao: str
    protocoloRelatorio: str = ""  # camelCase para compatibilidade com API/JSON
    
    def __post_init__(self):
        """Valida CNPJ após inicialização"""
        self.cnpj = self._normalize_cnpj(self.cnpj)
        if not self.validate_cnpj():
            raise ValueError(f"CNPJ inválido: {self.cnpj}")
    
    @staticmethod
    def _normalize_cnpj(cnpj: str) -> str:
        """
        Remove formatação do CNPJ (pontos, barras, hífens).
        
        Args:
            cnpj: CNPJ com ou sem formatação
            
        Returns:
            CNPJ apenas com números
        """
        return re.sub(r'[^\d]', '', cnpj)
    
    def validate_cnpj(self) -> bool:
        """
        Valida formato básico do CNPJ (14 dígitos).
        
        Returns:
            True se o CNPJ tem formato válido
        """
        cnpj_clean = self._normalize_cnpj(self.cnpj)
        return len(cnpj_clean) == 14 and cnpj_clean.isdigit()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte empresa para dicionário.
        
        Returns:
            Dicionário com dados da empresa
        """
        return {
            'idempresas': self.idempresas,
            'cnpj': self.cnpj,
            'razao': self.razao,
            'protocoloRelatorio': self.protocoloRelatorio
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Empresa':
        """
        Cria instância de Empresa a partir de dicionário.
        
        Args:
            data: Dicionário com dados da empresa
            
        Returns:
            Instância de Empresa
        """
        return cls(
            idempresas=data.get('idempresas', 0),
            cnpj=data.get('cnpj', ''),
            razao=data.get('razao', ''),
            protocoloRelatorio=data.get('protocoloRelatorio', '')
        )
    
    def has_protocolo(self) -> bool:
        """
        Verifica se empresa possui protocolo.
        
        Returns:
            True se protocolo não está vazio
        """
        return bool(self.protocoloRelatorio and self.protocoloRelatorio.strip())

