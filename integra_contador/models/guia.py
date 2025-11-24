"""Modelos de dados para Guias DCTFWEB (Documento de Arrecadação)

Nota sobre nomenclatura:
Os atributos estão em camelCase (ex: cnpjCompleto) para manter
compatibilidade direta com a API Serpro que retorna dados neste formato.
Isso evita necessidade de mapeamento/conversão nos métodos from_dict/to_dict.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class GuiaDCTFWeb:
    """Representa uma guia de pagamento DCTFWEB completa"""
    
    pdf: bytes
    cnpjCompleto: Optional[str] = None
    detalhamento: Optional[Dict[str, Any]] = None
    dados: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], pdf_bytes: bytes) -> 'GuiaDCTFWeb':
        """
        Cria instância de GuiaDCTFWeb a partir de dicionário e PDF.
        
        Args:
            data: Dicionário com dados da guia
            pdf_bytes: PDF em bytes
            
        Returns:
            Instância de GuiaDCTFWeb
        """
        # Extrai detalhamento se existir
        detalhamento = data.get('detalhamento')
        
        # Remove campos que não são parte do detalhamento
        dados_guia = {k: v for k, v in data.items() if k not in ['pdf', 'detalhamento']}
        
        return cls(
            pdf=pdf_bytes,
            cnpjCompleto=data.get('cnpjCompleto'),
            detalhamento=detalhamento if isinstance(detalhamento, dict) else None,
            dados=dados_guia if dados_guia else None
        )

