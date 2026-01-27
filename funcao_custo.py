import numpy as np


def calculate_euclidean_distance(pos1_idx, pos2_idx, cols=10):
    """
    Calcula a distância euclidiana entre duas posições na matriz.
    
    Args:
        pos1_idx: Índice linear da posição 1 (0-99)
        pos2_idx: Índice linear da posição 2 (0-99)
        cols: Número de colunas da matriz (padrão 10)
    
    Returns:
        Distância euclidiana entre as posições
    """
    row1, col1 = pos1_idx // cols, pos1_idx % cols
    row2, col2 = pos2_idx // cols, pos2_idx % cols
    
    return np.sqrt((row1 - row2)**2 + (col1 - col2)**2)

def calculate_importance_factor(score):
    """
    Calcula o fator de amplificação logarítmica do score.
    
    Fórmula: log10(score + 1) + 1
    
    Isso dá peso progressivo a scores maiores sem criar descontinuidades.
    
    Args:
        score: Valor de frequência/importância do item (1-100)
    
    Returns:
        Fator de amplificação (sempre ≥ 1)
    
    Exemplos:
        score=10  → fator ≈ 2.04
        score=50  → fator ≈ 2.71
        score=100 → fator ≈ 3.00
    """
    return np.log10(score + 1) + 1


def calculate_position_cost(row, importance_score):
    """
    Calcula o custo de uma posição específica no armazém.
    
    Fórmula: Custo = distância × score × [log10(score + 1) + 1]
    
    O score já captura toda a informação de frequência.
    O fator logarítmico dá peso progressivo sem descontinuidades.
    
    Args:
        row: Número da linha (0-9)
        importance_score: Score de frequência do item (1-100)
    
    Returns:
        Custo da posição
    
    Exemplo:
        Item score=85, linha 5:
        - distância = 6
        - fator = log10(86) + 1 ≈ 2.93
        - custo = 6 × 85 × 2.93 ≈ 1,495
    """
    # Distância da entrada do armazém
    if row == 0:
        distance = 1
    else:
        distance = row + 1
    
    # Fator de amplificação logarítmica
    importance_factor = calculate_importance_factor(importance_score)
    
    # Custo final: distância × score × fator_log
    return distance * importance_score * importance_factor


def calculate_total_cost(matrix, importance_matrix=None):
    """
    Calcula o custo total de uma configuração de matriz.
    
    Args:
        matrix: Matriz 10x10 com classificações A, B, C (usado apenas para fallback)
        importance_matrix: Matriz 10x10 com scores de frequência (1-100)
    
    Returns:
        Custo total da configuração
    """
    rows, cols = matrix.shape
    total_cost = 0
    
    # Se não houver matriz de importância, usar valores padrão baseados na classe
    if importance_matrix is None:
        importance_matrix = np.zeros((rows, cols))
        for i in range(rows):
            for j in range(cols):
                if matrix[i, j] == 'A':
                    importance_matrix[i, j] = 85
                elif matrix[i, j] == 'B':
                    importance_matrix[i, j] = 60
                else:
                    importance_matrix[i, j] = 25
    
    for i in range(rows):
        for j in range(cols):
            importance_score = importance_matrix[i, j]
            cost = calculate_position_cost(i, importance_score)
            total_cost += cost
    
    return total_cost


def calculate_cost_matrix(matrix, importance_matrix=None, affinity_matrix=None, affinity_weight=0.0):
    """
    Calcula a matriz de custo para otimização de slotting.
    
    Esta matriz é usada pelo algoritmo húngaro para determinar
    a alocação ótima de SKUs nas posições do armazém.
    
    Cada elemento [i,j] representa o custo de alocar o item da posição i
    para a posição j, baseado no score de frequência e afinidade.
    
    Args:
        matrix: Matriz 10x10 com classificações A, B, C (usado apenas para fallback)
        importance_matrix: Matriz 10x10 com scores de frequência (1-100)
        affinity_matrix: Matriz 100x100 com afinidades entre SKUs (0-1), opcional
        affinity_weight: Peso da penalidade de afinidade (padrão 0.0 = desabilitado)
    
    Returns:
        Matriz de custo 100x100 para o algoritmo húngaro
    """
    rows, cols = matrix.shape
    total_positions = rows * cols
    
    # Se não houver matriz de importância, criar valores padrão
    if importance_matrix is None:
        importance_matrix = np.zeros((rows, cols))
        for i in range(rows):
            for j in range(cols):
                if matrix[i, j] == 'A':
                    importance_matrix[i, j] = 85
                elif matrix[i, j] == 'B':
                    importance_matrix[i, j] = 60
                else:
                    importance_matrix[i, j] = 25
    
    cost_matrix = np.zeros((total_positions, total_positions))
    
    # Custo base: distância × frequência
    for current_idx in range(total_positions):
        current_row = current_idx // cols
        current_col = current_idx % cols
        current_importance = importance_matrix[current_row, current_col]
        
        for target_idx in range(total_positions):
            target_row = target_idx // cols
            
            cost = calculate_position_cost(target_row, current_importance)
            cost_matrix[current_idx, target_idx] = cost
    
    # Adicionar penalidade de afinidade se fornecida
    if affinity_matrix is not None and affinity_weight > 0:
        # Pré-calcular todas as distâncias entre posições
        distance_matrix = np.zeros((total_positions, total_positions))
        for i in range(total_positions):
            for j in range(i + 1, total_positions):
                dist = calculate_euclidean_distance(i, j, cols)
                distance_matrix[i, j] = dist
                distance_matrix[j, i] = dist
        
        # Para cada SKU, adicionar penalidade baseada em afinidades
        for sku_i in range(total_positions):
            for sku_j in range(sku_i + 1, total_positions):
                if affinity_matrix[sku_i, sku_j] > 0:
                    # Penalidade para cada par de posições possíveis
                    for pos_i in range(total_positions):
                        for pos_j in range(total_positions):
                            if pos_i != pos_j:
                                # Penalidade = afinidade × distância × peso
                                penalty = affinity_matrix[sku_i, sku_j] * distance_matrix[pos_i, pos_j] * affinity_weight
                                
                                # Adicionar penalidade proporcional aos custos
                                cost_matrix[sku_i, pos_i] += penalty / 2
                                cost_matrix[sku_j, pos_j] += penalty / 2
    
    return cost_matrix
