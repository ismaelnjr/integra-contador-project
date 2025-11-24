"""Funções utilitárias para validação de dados da API"""

from typing import Dict, Any, List


def validar_ano_pa(ano: str) -> bool:
    """
    Valida formato do ano de apuração.
    
    Args:
        ano: Ano no formato AAAA
        
    Returns:
        True se válido
    """
    if not ano or len(ano) != 4:
        return False
    if not ano.isdigit():
        return False
    try:
        ano_int = int(ano)
        return 2000 <= ano_int <= 2100
    except ValueError:
        return False


def validar_mes_pa(mes: str) -> bool:
    """
    Valida formato do mês de apuração.
    
    Args:
        mes: Mês no formato MM (01-12)
        
    Returns:
        True se válido
    """
    if not mes or len(mes) not in [1, 2]:
        return False
    if not mes.isdigit():
        return False
    try:
        mes_int = int(mes)
        return 1 <= mes_int <= 12
    except ValueError:
        return False


def normalizar_mes_pa(mes: str) -> str:
    """
    Normaliza mês para formato MM (com zero à esquerda se necessário).
    
    Args:
        mes: Mês em formato 1-12 ou 01-12
        
    Returns:
        Mês no formato MM
        
    Raises:
        ValueError: Se o mês for inválido
    """
    mes_clean = mes.strip()
    if mes_clean.isdigit():
        mes_int = int(mes_clean)
        if 1 <= mes_int <= 12:
            return f"{mes_int:02d}"
    raise ValueError(f"Mês inválido: {mes}")


def construir_dados_guia_dctfweb(dados_guia: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói e valida dicionário de dados da guia DCTFWEB com formato mínimo.
    
    Args:
        dados_guia: Dicionário com dados da guia (deve conter anoPA e mesPA)
        
    Returns:
        Dicionário validado e normalizado com formato mínimo:
        {
            "categoria": "GERAL_MENSAL" (padrão),
            "anoPA": "2025",
            "mesPA": "10"
        }
        
    Raises:
        ValueError: Se anoPA ou mesPA forem inválidos ou ausentes
    """
    # Valida campos obrigatórios
    ano_pa = dados_guia.get('anoPA')
    mes_pa = dados_guia.get('mesPA')
    
    if not ano_pa:
        raise ValueError("Campo 'anoPA' é obrigatório. Informe o ano de apuração (ex: '2025')")
    
    if not mes_pa:
        raise ValueError("Campo 'mesPA' é obrigatório. Informe o mês de apuração (ex: '10' ou '01')")
    
    # Converte para string se necessário
    ano_pa = str(ano_pa).strip()
    mes_pa = str(mes_pa).strip()
    
    # Valida ano
    if not validar_ano_pa(ano_pa):
        raise ValueError(f"Ano de apuração inválido: {ano_pa}. Use formato AAAA (ex: 2025)")
    
    # Normaliza e valida mês
    mes_pa_normalizado = normalizar_mes_pa(mes_pa)
    if not validar_mes_pa(mes_pa_normalizado):
        raise ValueError(f"Mês de apuração inválido: {mes_pa}. Use formato MM (01-12)")
    
    # Constrói dicionário com formato mínimo
    dados_finais = {
        "categoria": dados_guia.get('categoria', 'GERAL_MENSAL'),
        "anoPA": ano_pa,
        "mesPA": mes_pa_normalizado
    }
    
    # Adiciona outros campos se fornecidos
    campos_extras = {k: v for k, v in dados_guia.items() 
                     if k not in ['categoria', 'anoPA', 'mesPA']}
    dados_finais.update(campos_extras)
    
    return dados_finais


def validar_periodo_apuracao(periodo: str) -> bool:
    """
    Valida formato do período de apuração (AAAAMM).
    
    Args:
        periodo: Período no formato AAAAMM
        
    Returns:
        True se válido
    """
    if not periodo or len(periodo) != 6:
        return False
    if not periodo.isdigit():
        return False
    try:
        ano = int(periodo[:4])
        mes = int(periodo[4:6])
        return 2000 <= ano <= 2100 and 1 <= mes <= 12
    except ValueError:
        return False


def validar_data_consolidacao(data: str) -> bool:
    """
    Valida formato da data de consolidação (AAAAMMDD).
    
    Args:
        data: Data no formato AAAAMMDD
        
    Returns:
        True se válido
    """
    if not data or len(data) != 8:
        return False
    if not data.isdigit():
        return False
    try:
        ano = int(data[:4])
        mes = int(data[4:6])
        dia = int(data[6:8])
        # Validação básica (não verifica se a data realmente existe)
        return 2000 <= ano <= 2100 and 1 <= mes <= 12 and 1 <= dia <= 31
    except ValueError:
        return False


def verificar_mensagem_sem_valor_devido(mensagens: List[Dict[str, Any]]) -> bool:
    """
    Verifica se há mensagem indicando que não há valor devido.
    
    Args:
        mensagens: Lista de mensagens da API
        
    Returns:
        True se encontrar mensagem indicando ausência de valor devido
    """
    if not mensagens:
        return False
    
    codigos_sem_valor = ['MSG_E0139', 'E0139']
    for msg in mensagens:
        if isinstance(msg, dict):
            codigo = msg.get('codigo', '')
            texto = msg.get('texto', '')
            # Verifica por código ou por texto contendo "não haver valor devido"
            if any(cod in str(codigo) for cod in codigos_sem_valor):
                return True
            if 'não haver valor devido' in texto.lower() or 'nao haver valor devido' in texto.lower():
                return True
    return False

