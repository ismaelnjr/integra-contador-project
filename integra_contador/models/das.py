"""Modelos de dados para DAS (Documento de Arrecadação do Simples Nacional)"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class Valores:
    """Representa os valores do DAS"""
    
    principal: float
    multa: float
    juros: float
    total: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Valores':
        """
        Cria instância de Valores a partir de dicionário.
        
        Args:
            data: Dicionário com dados dos valores
            
        Returns:
            Instância de Valores
        """
        return cls(
            principal=float(data.get('principal', 0)),
            multa=float(data.get('multa', 0)),
            juros=float(data.get('juros', 0)),
            total=float(data.get('total', 0))
        )


@dataclass
class Composicao:
    """Representa a composição de um tributo no DAS"""
    
    periodoApuracao: str
    codigo: str
    denominacao: str
    valores: Valores
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Composicao':
        """
        Cria instância de Composicao a partir de dicionário.
        
        Args:
            data: Dicionário com dados da composição
            
        Returns:
            Instância de Composicao
        """
        return cls(
            periodoApuracao=data.get('periodoApuracao', ''),
            codigo=data.get('codigo', ''),
            denominacao=data.get('denominacao', ''),
            valores=Valores.from_dict(data.get('valores', {}))
        )


@dataclass
class DetalhamentoDas:
    """Representa o detalhamento do DAS"""
    
    periodoApuracao: str
    numeroDocumento: str
    dataVencimento: str
    dataLimiteAcolhimento: str
    valores: Valores
    observacao1: Optional[str] = None
    observacao2: Optional[str] = None
    observacao3: Optional[str] = None
    composicao: List[Composicao] = None
    
    def __post_init__(self):
        """Inicializa lista de composição se None"""
        if self.composicao is None:
            self.composicao = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetalhamentoDas':
        """
        Cria instância de DetalhamentoDas a partir de dicionário.
        
        Args:
            data: Dicionário com dados do detalhamento
            
        Returns:
            Instância de DetalhamentoDas
        """
        composicao_list = []
        if 'composicao' in data and isinstance(data['composicao'], list):
            composicao_list = [Composicao.from_dict(item) for item in data['composicao']]
        
        return cls(
            periodoApuracao=data.get('periodoApuracao', ''),
            numeroDocumento=data.get('numeroDocumento', ''),
            dataVencimento=data.get('dataVencimento', ''),
            dataLimiteAcolhimento=data.get('dataLimiteAcolhimento', ''),
            valores=Valores.from_dict(data.get('valores', {})),
            observacao1=data.get('observacao1'),
            observacao2=data.get('observacao2'),
            observacao3=data.get('observacao3'),
            composicao=composicao_list
        )


@dataclass
class Das:
    """Representa um DAS completo"""
    
    pdf: bytes
    cnpjCompleto: str
    detalhamento: DetalhamentoDas
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], pdf_bytes: bytes) -> 'Das':
        """
        Cria instância de Das a partir de dicionário e PDF.
        
        Args:
            data: Dicionário com dados do DAS
            pdf_bytes: PDF em bytes
            
        Returns:
            Instância de Das
        """
        return cls(
            pdf=pdf_bytes,
            cnpjCompleto=data.get('cnpjCompleto', ''),
            detalhamento=DetalhamentoDas.from_dict(data.get('detalhamento', {}))
        )

