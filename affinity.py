import numpy as np

def create_affinity_matrix_from_positions(positions, affinity_value=0.6, total_positions=100):
    """
    Cria matriz de afinidade baseada em posições selecionadas.
    
    Futuramente esta função será substituída por uma que lê dados reais de compras.
    
    Args:
        positions: Lista de tuplas (pos1, pos2, pos3) ou lista de índices lineares
                   Exemplo: [(5, 12, 23)] ou [5, 12, 23]
        affinity_value: Valor de afinidade entre os itens selecionados (padrão 0.6)
        total_positions: Total de posições na matriz (padrão 100 para 10x10)
    
    Returns:
        Matriz 100x100 simétrica com afinidades (0 para sem afinidade)
    """
    affinity_matrix = np.zeros((total_positions, total_positions))
    
    # Se positions é uma lista de índices
    if len(positions) > 0:
        # Criar afinidade entre todos os pares
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                pos_i = positions[i]
                pos_j = positions[j]
                
                # Matriz simétrica
                affinity_matrix[pos_i, pos_j] = affinity_value
                affinity_matrix[pos_j, pos_i] = affinity_value
    
    return affinity_matrix


def load_affinity_from_data(purchase_data):
    """
    Placeholder para função futura que carregará afinidades de dados reais.
    
    Args:
        purchase_data: DataFrame ou estrutura com histórico de compras
                      Colunas esperadas: ['order_id', 'sku_position', ...]
    
    Returns:
        Matriz 100x100 com afinidades calculadas de dados reais
    """
    # TODO: Implementar quando dados reais estiverem disponíveis
    # Exemplo de lógica:
    # 1. Agrupar por order_id
    # 2. Para cada pedido, encontrar pares de SKUs
    # 3. Calcular co-ocorrência: afinidade[i,j] = pedidos_com_ambos / pedidos_com_i_ou_j
    
    raise NotImplementedError("Função será implementada quando dados reais estiverem disponíveis")


def get_affinity_info(affinity_matrix, threshold=0.1):
    """
    Retorna informações sobre pares com afinidade na matriz.
    
    Args:
        affinity_matrix: Matriz 100x100 de afinidades
        threshold: Valor mínimo de afinidade para considerar (padrão 0.1)
    
    Returns:
        Lista de dicionários com informações dos pares
    """
    pairs = []
    
    for i in range(affinity_matrix.shape[0]):
        for j in range(i + 1, affinity_matrix.shape[1]):
            if affinity_matrix[i, j] >= threshold:
                pairs.append({
                    'pos1': i,
                    'pos2': j,
                    'affinity': affinity_matrix[i, j]
                })
    
    return pairs
