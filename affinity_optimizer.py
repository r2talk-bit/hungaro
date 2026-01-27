import numpy as np
from funcao_custo import calculate_euclidean_distance, calculate_total_cost


def find_sku_position(matrix, importance_matrix, original_sku_idx):
    """
    Encontra a posição atual de um SKU na matriz otimizada.
    
    Args:
        matrix: Matriz atual (otimizada)
        importance_matrix: Matriz de importância atual
        original_sku_idx: Índice linear do SKU na matriz original (0-99)
    
    Returns:
        Índice linear da posição atual do SKU
    """
    flat_matrix = matrix.flatten()
    flat_importance = importance_matrix.flatten()
    
    for pos in range(len(flat_matrix)):
        if pos == original_sku_idx:
            return pos
    
    return original_sku_idx


def get_neighbors(position, rows=10, cols=10, radius=2):
    """
    Retorna posições vizinhas dentro de um raio.
    
    Args:
        position: Índice linear da posição (0-99)
        rows: Número de linhas da matriz
        cols: Número de colunas da matriz
        radius: Raio de busca
    
    Returns:
        Lista de índices lineares dos vizinhos
    """
    row = position // cols
    col = position % cols
    
    neighbors = []
    for r in range(max(0, row - radius), min(rows, row + radius + 1)):
        for c in range(max(0, col - radius), min(cols, col + radius + 1)):
            neighbor_pos = r * cols + c
            if neighbor_pos != position:
                neighbors.append(neighbor_pos)
    
    return neighbors


def swap_positions(matrix, importance_matrix, pos1, pos2):
    """
    Troca dois SKUs de posição.
    
    Args:
        matrix: Matriz de classificação
        importance_matrix: Matriz de importância
        pos1: Índice linear da posição 1
        pos2: Índice linear da posição 2
    
    Returns:
        Tupla (nova_matriz, nova_importance)
    """
    rows, cols = matrix.shape
    
    new_matrix = matrix.copy()
    new_importance = importance_matrix.copy()
    
    flat_matrix = new_matrix.flatten()
    flat_importance = new_importance.flatten()
    
    flat_matrix[pos1], flat_matrix[pos2] = flat_matrix[pos2], flat_matrix[pos1]
    flat_importance[pos1], flat_importance[pos2] = flat_importance[pos2], flat_importance[pos1]
    
    new_matrix = flat_matrix.reshape(rows, cols)
    new_importance = flat_importance.reshape(rows, cols)
    
    return new_matrix, new_importance


def calculate_affinity_penalty(matrix, importance_matrix, affinity_matrix, affinity_weight=1.0):
    """
    Calcula a penalidade total de afinidade baseada nas distâncias atuais.
    
    Args:
        matrix: Matriz de classificação atual
        importance_matrix: Matriz de importância atual
        affinity_matrix: Matriz 100x100 de afinidades
        affinity_weight: Peso da penalidade
    
    Returns:
        Penalidade total de afinidade
    """
    if affinity_matrix is None:
        return 0.0
    
    total_penalty = 0.0
    total_positions = matrix.size
    
    for sku_i in range(total_positions):
        for sku_j in range(sku_i + 1, total_positions):
            if affinity_matrix[sku_i, sku_j] > 0:
                pos_i = find_sku_position(matrix, importance_matrix, sku_i)
                pos_j = find_sku_position(matrix, importance_matrix, sku_j)
                
                distance = calculate_euclidean_distance(pos_i, pos_j)
                penalty = affinity_matrix[sku_i, sku_j] * distance * affinity_weight
                total_penalty += penalty
    
    return total_penalty


def calculate_combined_score(matrix, importance_matrix, affinity_matrix, affinity_weight=1.0):
    """
    Calcula score combinado: custo operacional + penalidade de afinidade.
    
    Args:
        matrix: Matriz de classificação
        importance_matrix: Matriz de importância
        affinity_matrix: Matriz de afinidades
        affinity_weight: Peso da penalidade de afinidade
    
    Returns:
        Score total combinado
    """
    operational_cost = calculate_total_cost(matrix, importance_matrix)
    affinity_penalty = calculate_affinity_penalty(matrix, importance_matrix, affinity_matrix, affinity_weight)
    
    return operational_cost + affinity_penalty


def post_optimize_affinity_swaps(optimized_matrix, importance_matrix, affinity_matrix, 
                                  affinity_weight=1.0, max_cost_increase_pct=2.0, 
                                  max_iterations=100):
    """
    Realiza trocas locais para aproximar SKUs com afinidade após otimização húngara.
    
    Args:
        optimized_matrix: Matriz otimizada pelo algoritmo húngaro
        importance_matrix: Matriz de importância correspondente
        affinity_matrix: Matriz 100x100 de afinidades entre SKUs
        affinity_weight: Peso da penalidade de afinidade
        max_cost_increase_pct: Aumento máximo permitido no custo (%)
        max_iterations: Número máximo de iterações
    
    Returns:
        Tupla (matriz_ajustada, importance_ajustada, stats)
    """
    if affinity_matrix is None:
        return optimized_matrix, importance_matrix, {'swaps': 0, 'improvement': 0}
    
    current_matrix = optimized_matrix.copy()
    current_importance = importance_matrix.copy()
    
    initial_cost = calculate_total_cost(current_matrix, current_importance)
    initial_affinity_penalty = calculate_affinity_penalty(current_matrix, current_importance, 
                                                           affinity_matrix, affinity_weight)
    initial_score = initial_cost + initial_affinity_penalty
    
    max_allowed_cost = initial_cost * (1 + max_cost_increase_pct / 100)
    
    total_swaps = 0
    iteration = 0
    improved = True
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        affinity_pairs = []
        for i in range(affinity_matrix.shape[0]):
            for j in range(i + 1, affinity_matrix.shape[1]):
                if affinity_matrix[i, j] > 0.1:
                    affinity_pairs.append({
                        'sku_i': i,
                        'sku_j': j,
                        'affinity': affinity_matrix[i, j]
                    })
        
        affinity_pairs.sort(key=lambda x: x['affinity'], reverse=True)
        
        for pair in affinity_pairs:
            sku_i = pair['sku_i']
            sku_j = pair['sku_j']
            
            pos_i = find_sku_position(current_matrix, current_importance, sku_i)
            pos_j = find_sku_position(current_matrix, current_importance, sku_j)
            
            current_distance = calculate_euclidean_distance(pos_i, pos_j)
            
            neighbors_i = get_neighbors(pos_i, radius=2)
            neighbors_j = get_neighbors(pos_j, radius=2)
            
            best_swap = None
            best_score = calculate_combined_score(current_matrix, current_importance, 
                                                   affinity_matrix, affinity_weight)
            
            for neighbor in neighbors_i:
                new_matrix, new_importance = swap_positions(
                    current_matrix, current_importance, pos_j, neighbor
                )
                
                new_cost = calculate_total_cost(new_matrix, new_importance)
                
                if new_cost <= max_allowed_cost:
                    new_score = calculate_combined_score(new_matrix, new_importance, 
                                                         affinity_matrix, affinity_weight)
                    new_distance = calculate_euclidean_distance(pos_i, neighbor)
                    
                    if new_score < best_score and new_distance < current_distance:
                        best_score = new_score
                        best_swap = (pos_j, neighbor)
            
            for neighbor in neighbors_j:
                new_matrix, new_importance = swap_positions(
                    current_matrix, current_importance, pos_i, neighbor
                )
                
                new_cost = calculate_total_cost(new_matrix, new_importance)
                
                if new_cost <= max_allowed_cost:
                    new_score = calculate_combined_score(new_matrix, new_importance, 
                                                         affinity_matrix, affinity_weight)
                    new_distance = calculate_euclidean_distance(neighbor, pos_j)
                    
                    if new_score < best_score and new_distance < current_distance:
                        best_score = new_score
                        best_swap = (pos_i, neighbor)
            
            if best_swap:
                current_matrix, current_importance = swap_positions(
                    current_matrix, current_importance, best_swap[0], best_swap[1]
                )
                total_swaps += 1
                improved = True
                break
    
    final_cost = calculate_total_cost(current_matrix, current_importance)
    final_affinity_penalty = calculate_affinity_penalty(current_matrix, current_importance, 
                                                         affinity_matrix, affinity_weight)
    final_score = final_cost + final_affinity_penalty
    
    stats = {
        'swaps': total_swaps,
        'iterations': iteration,
        'initial_cost': initial_cost,
        'final_cost': final_cost,
        'cost_increase': final_cost - initial_cost,
        'cost_increase_pct': ((final_cost - initial_cost) / initial_cost * 100) if initial_cost > 0 else 0,
        'initial_affinity_penalty': initial_affinity_penalty,
        'final_affinity_penalty': final_affinity_penalty,
        'affinity_improvement': initial_affinity_penalty - final_affinity_penalty,
        'affinity_improvement_pct': ((initial_affinity_penalty - final_affinity_penalty) / initial_affinity_penalty * 100) if initial_affinity_penalty > 0 else 0,
        'initial_score': initial_score,
        'final_score': final_score,
        'total_improvement': initial_score - final_score
    }
    
    return current_matrix, current_importance, stats
