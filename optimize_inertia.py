import numpy as np
from scipy.optimize import linear_sum_assignment
from funcao_custo import calculate_cost_matrix, calculate_total_cost
from inertia import identify_inertial_skus, apply_inertia_constraint


def optimize_slotting_with_inertia(matrix, importance_matrix=None, affinity_matrix=None, 
                                    affinity_weight=0.0, gain_threshold_pct=5):
    """
    Otimiza a posição dos SKUs usando o algoritmo húngaro com restrições de inércia.
    
    Processo em 2 etapas:
    1. Executa Húngaro completo para calcular ganho de cada movimentação
    2. Identifica SKUs com ganho < threshold% como inerciais
    3. Re-executa Húngaro com penalidade para SKUs inerciais
    
    Args:
        matrix: Matriz 10x10 com classificações A, B, C
        importance_matrix: Matriz 10x10 com scores de frequência (1-100)
        affinity_matrix: Matriz 100x100 com afinidades entre SKUs (0-1), opcional
        affinity_weight: Peso da penalidade de afinidade (padrão 0.0 = desabilitado)
        gain_threshold_pct: Threshold de ganho mínimo em % (padrão 5%)
    
    Returns:
        Tupla (matriz_otimizada_inertia, importance_otimizada_inertia, inertial_count)
    """
    rows, cols = matrix.shape
    
    # Passo 1: Otimização Húngara COMPLETA (sem restrições)
    cost_matrix = calculate_cost_matrix(matrix, importance_matrix, affinity_matrix, affinity_weight)
    row_ind_full, col_ind_full = linear_sum_assignment(cost_matrix)
    
    # Reorganizar matriz otimizada completa
    flat_matrix = matrix.flatten()
    hungarian_full_flat = np.empty(flat_matrix.shape, dtype=flat_matrix.dtype)
    
    for original_pos, new_pos in zip(row_ind_full, col_ind_full):
        hungarian_full_flat[new_pos] = flat_matrix[original_pos]
    
    hungarian_full_matrix = hungarian_full_flat.reshape(rows, cols)
    
    hungarian_full_importance = None
    if importance_matrix is not None:
        flat_importance = importance_matrix.flatten()
        hungarian_full_importance_flat = np.empty(flat_importance.shape, dtype=flat_importance.dtype)
        
        for original_pos, new_pos in zip(row_ind_full, col_ind_full):
            hungarian_full_importance_flat[new_pos] = flat_importance[original_pos]
        
        hungarian_full_importance = hungarian_full_importance_flat.reshape(rows, cols)
    
    # Passo 2: Identificar SKUs inerciais baseado no ganho percentual
    inertial_mask, inertial_count = identify_inertial_skus(
        matrix, hungarian_full_matrix,
        importance_matrix, hungarian_full_importance,
        gain_threshold_pct
    )
    
    # Passo 3: Re-otimizar COM restrição de inércia
    cost_matrix_inertia = apply_inertia_constraint(cost_matrix, inertial_mask)
    row_ind, col_ind = linear_sum_assignment(cost_matrix_inertia)
    
    # Reorganizar matriz com inércia
    optimized_flat = np.empty(flat_matrix.shape, dtype=flat_matrix.dtype)
    
    for original_pos, new_pos in zip(row_ind, col_ind):
        optimized_flat[new_pos] = flat_matrix[original_pos]
    
    optimized_matrix = optimized_flat.reshape(rows, cols)
    
    # Reorganizar matriz de importância
    optimized_importance = None
    if importance_matrix is not None:
        optimized_importance_flat = np.empty(flat_importance.shape, dtype=flat_importance.dtype)
        
        for original_pos, new_pos in zip(row_ind, col_ind):
            optimized_importance_flat[new_pos] = flat_importance[original_pos]
        
        optimized_importance = optimized_importance_flat.reshape(rows, cols)
    
    return optimized_matrix, optimized_importance, inertial_count
