"""Repositório para gerenciamento de empresas em JSON"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from integra_contador.models.empresa import Empresa
from integra_contador.config.settings import Settings

logger = logging.getLogger(__name__)


class EmpresaRepository:
    """Gerencia persistência de empresas em arquivo JSON"""
    
    def __init__(self, json_path: Optional[str] = None):
        """
        Inicializa o repositório.
        
        Args:
            json_path: Caminho do arquivo JSON. Se None, usa Settings.
        """
        self.json_path = json_path or Settings.EMPRESAS_JSON_PATH
    
    def load_all(self) -> List[Empresa]:
        """
        Carrega todas as empresas do arquivo JSON.
        
        Returns:
            Lista de empresas
            
        Raises:
            FileNotFoundError: Se o arquivo não existir
            ValueError: Se o JSON estiver inválido
        """
        if not os.path.exists(self.json_path):
            logger.warning(f"Arquivo {self.json_path} não encontrado. Retornando lista vazia.")
            return []
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            empresas = [Empresa.from_dict(item) for item in data]
            logger.info(f"Carregadas {len(empresas)} empresas de {self.json_path}")
            
            return empresas
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON: {e}")
            raise ValueError(f"Arquivo JSON inválido: {self.json_path}") from e
        except Exception as e:
            logger.error(f"Erro ao carregar empresas: {e}")
            raise
    
    def save(self, empresas: List[Empresa]) -> None:
        """
        Salva lista de empresas no arquivo JSON.
        
        Args:
            empresas: Lista de empresas a salvar
            
        Raises:
            Exception: Se não conseguir salvar
        """
        try:
            data = [empresa.to_dict() for empresa in empresas]
            
            # Garante que o diretório existe
            os.makedirs(os.path.dirname(self.json_path) or '.', exist_ok=True)
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Salvas {len(empresas)} empresas em {self.json_path}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar empresas: {e}")
            raise Exception(f"Falha ao salvar empresas: {str(e)}") from e
    
    def update_protocolo(self, empresa_id: int, protocolo: str) -> bool:
        """
        Atualiza protocolo de uma empresa específica.
        
        Args:
            empresa_id: ID da empresa
            protocolo: Novo protocolo
            
        Returns:
            True se atualizou com sucesso, False se empresa não encontrada
        """
        empresas = self.load_all()
        
        for empresa in empresas:
            if empresa.idempresas == empresa_id:
                empresa.protocoloRelatorio = protocolo
                self.save(empresas)
                logger.info(f"Protocolo atualizado para empresa {empresa_id}: {protocolo}")
                return True
        
        logger.warning(f"Empresa {empresa_id} não encontrada")
        return False
    
    def clear_protocolo(self, empresa_id: int) -> bool:
        """
        Limpa protocolo de uma empresa específica.
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            True se limpou com sucesso, False se empresa não encontrada
        """
        return self.update_protocolo(empresa_id, "")

