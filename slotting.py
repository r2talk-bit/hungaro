import numpy as np
from scipy.optimize import linear_sum_assignment
from funcao_custo import calculate_cost_matrix, calculate_total_cost
from inertia import identify_inertial_skus, apply_inertia_constraint
from affinity_optimizer import post_optimize_affinity_swaps
from pareto_analysis import calculate_movement_gains, identify_pareto_critical_movements, apply_critical_movements_only, get_pareto_critical_stats


def optimize_slotting(matrix, importance_matrix=None, affinity_matrix=None, affinity_weight=0.0):
    """
    Otimiza a posição dos SKUs usando o algoritmo húngaro.
    
    O objetivo é minimizar o custo total, considerando:
    1. Frequência: itens de maior frequência mais próximos da entrada
    2. Afinidade: itens com afinidade ficam próximos entre si (se affinity_weight > 0)
    
    Args:
        matrix: Matriz 10x10 com classificações A, B, C
        importance_matrix: Matriz 10x10 com scores de frequência (1-100)
        affinity_matrix: Matriz 100x100 com afinidades entre SKUs (0-1), opcional
        affinity_weight: Peso da penalidade de afinidade (padrão 0.0 = desabilitado)
    
    Returns:
        Tupla (matriz_otimizada, importance_otimizada)
    """
    rows, cols = matrix.shape
    
    cost_matrix = calculate_cost_matrix(matrix, importance_matrix, affinity_matrix, affinity_weight)
    
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # Reorganizar matriz de classificação
    flat_matrix = matrix.flatten()
    optimized_flat = np.empty(flat_matrix.shape, dtype=flat_matrix.dtype)
    
    for original_pos, new_pos in zip(row_ind, col_ind):
        optimized_flat[new_pos] = flat_matrix[original_pos]
    
    optimized_matrix = optimized_flat.reshape(rows, cols)
    
    # Reorganizar matriz de importância da mesma forma
    optimized_importance = None
    if importance_matrix is not None:
        flat_importance = importance_matrix.flatten()
        optimized_importance_flat = np.empty(flat_importance.shape, dtype=flat_importance.dtype)
        
        for original_pos, new_pos in zip(row_ind, col_ind):
            optimized_importance_flat[new_pos] = flat_importance[original_pos]
        
        optimized_importance = optimized_importance_flat.reshape(rows, cols)
    
    return optimized_matrix, optimized_importance


def optimize_slotting_pareto(matrix, importance_matrix=None, affinity_matrix=None, 
                             affinity_weight=0.0, inertia_threshold=30):
    """
    Otimiza a posição dos SKUs usando o algoritmo húngaro com análise Pareto.
    Balanceia custo vs. movimentações, aplicando constraint de inércia.
    
    SKUs inerciais (baixa frequência) recebem penalidade alta para movimentação,
    sendo movidos apenas quando necessário para otimizar o layout geral.
    
    Args:
        matrix: Matriz 10x10 com classificações A, B, C
        importance_matrix: Matriz 10x10 com scores de frequência (1-100)
        affinity_matrix: Matriz 100x100 com afinidades entre SKUs (0-1), opcional
        affinity_weight: Peso da penalidade de afinidade (padrão 0.0 = desabilitado)
        inertia_threshold: Threshold para identificar SKUs inerciais (padrão 30)
    
    Returns:
        Tupla (matriz_pareto, importance_pareto, inertial_count)
    """
    rows, cols = matrix.shape
    
    # Identificar SKUs inerciais
    inertial_mask, inertial_count = identify_inertial_skus(importance_matrix, inertia_threshold)
    
    # Calcular matriz de custo base
    cost_matrix = calculate_cost_matrix(matrix, importance_matrix, affinity_matrix, affinity_weight)
    
    # Aplicar constraint de inércia
    cost_matrix_pareto = apply_inertia_constraint(cost_matrix, inertial_mask)
    
    # Otimizar com constraint
    row_ind, col_ind = linear_sum_assignment(cost_matrix_pareto)
    
    # Reorganizar matriz de classificação
    flat_matrix = matrix.flatten()
    optimized_flat = np.empty(flat_matrix.shape, dtype=flat_matrix.dtype)
    
    for original_pos, new_pos in zip(row_ind, col_ind):
        optimized_flat[new_pos] = flat_matrix[original_pos]
    
    optimized_matrix = optimized_flat.reshape(rows, cols)
    
    # Reorganizar matriz de importância da mesma forma
    optimized_importance = None
    if importance_matrix is not None:
        flat_importance = importance_matrix.flatten()
        optimized_importance_flat = np.empty(flat_importance.shape, dtype=flat_importance.dtype)
        
        for original_pos, new_pos in zip(row_ind, col_ind):
            optimized_importance_flat[new_pos] = flat_importance[original_pos]
        
        optimized_importance = optimized_importance_flat.reshape(rows, cols)
    
    return optimized_matrix, optimized_importance, inertial_count


def optimize_slotting_with_affinity_post(matrix, importance_matrix=None, affinity_matrix=None, 
                                         affinity_weight=1.0, max_cost_increase_pct=2.0):
    """
    Otimiza usando algoritmo húngaro + ajuste pós-otimização para afinidade.
    
    Esta abordagem resolve a limitação do algoritmo húngaro que não consegue
    otimizar relações entre pares de SKUs. Primeiro otimiza o custo base,
    depois ajusta localmente para aproximar SKUs com afinidade.
    
    Args:
        matrix: Matriz 10x10 com classificações A, B, C
        importance_matrix: Matriz 10x10 com scores de frequência (1-100)
        affinity_matrix: Matriz 100x100 com afinidades entre SKUs (0-1)
        affinity_weight: Peso da penalidade de afinidade
        max_cost_increase_pct: Aumento máximo permitido no custo (%)
    
    Returns:
        Tupla (matriz_otimizada, importance_otimizada, stats_affinity)
    """
    rows, cols = matrix.shape
    
    cost_matrix = calculate_cost_matrix(matrix, importance_matrix, affinity_matrix=None, affinity_weight=0.0)
    
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    flat_matrix = matrix.flatten()
    optimized_flat = np.empty(flat_matrix.shape, dtype=flat_matrix.dtype)
    
    for original_pos, new_pos in zip(row_ind, col_ind):
        optimized_flat[new_pos] = flat_matrix[original_pos]
    
    optimized_matrix = optimized_flat.reshape(rows, cols)
    
    optimized_importance = None
    if importance_matrix is not None:
        flat_importance = importance_matrix.flatten()
        optimized_importance_flat = np.empty(flat_importance.shape, dtype=flat_importance.dtype)
        
        for original_pos, new_pos in zip(row_ind, col_ind):
            optimized_importance_flat[new_pos] = flat_importance[original_pos]
        
        optimized_importance = optimized_importance_flat.reshape(rows, cols)
    
    if affinity_matrix is not None and affinity_weight > 0:
        optimized_matrix, optimized_importance, affinity_stats = post_optimize_affinity_swaps(
            optimized_matrix, optimized_importance, affinity_matrix, 
            affinity_weight, max_cost_increase_pct
        )
    else:
        affinity_stats = {'swaps': 0, 'improvement': 0}
    
    return optimized_matrix, optimized_importance, affinity_stats


def optimize_slotting_pareto_critical(matrix, importance_matrix=None, affinity_matrix=None, 
                                      affinity_weight=0.0, inertia_threshold=30, 
                                      critical_gain_percentage=50):
    """
    Otimização Pareto de segunda ordem: Inércia + Movimentações Críticas.
    
    Combina dois níveis de análise Pareto em sequência:
    1. Primeiro: Aplica Pareto com Inércia (constraint na matriz de custo)
    2. Segundo: Identifica movimentações críticas que representam X% do ganho da solução com inércia
    
    A matriz Pareto com Inércia serve como BASE para análise de movimentações críticas.
    
    Args:
        matrix: Matriz 10x10 com classificações A, B, C
        importance_matrix: Matriz 10x10 com scores de frequência (1-100)
        affinity_matrix: Matriz 100x100 com afinidades entre SKUs (0-1), opcional
        affinity_weight: Peso da penalidade de afinidade (padrão 0.0 = desabilitado)
        inertia_threshold: Threshold para identificar SKUs inerciais (padrão 30)
        critical_gain_percentage: Percentual do ganho a atingir (40-80, padrão 50)
    
    Returns:
        Tupla (matriz_critical, importance_critical, critical_stats)
    """
    rows, cols = matrix.shape
    
    # Passo 1: Otimização Húngara COMPLETA (para calcular ganhos)
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
        inertia_threshold  # Agora é gain_threshold_pct
    )
    
    # Passo 3: Otimização Pareto com Inércia (matriz base)
    cost_matrix_pareto = apply_inertia_constraint(cost_matrix, inertial_mask)
    
    row_ind, col_ind = linear_sum_assignment(cost_matrix_pareto)
    
    flat_matrix = matrix.flatten()
    pareto_inertia_flat = np.empty(flat_matrix.shape, dtype=flat_matrix.dtype)
    
    for original_pos, new_pos in zip(row_ind, col_ind):
        pareto_inertia_flat[new_pos] = flat_matrix[original_pos]
    
    pareto_inertia_matrix = pareto_inertia_flat.reshape(rows, cols)
    
    pareto_inertia_importance = None
    if importance_matrix is not None:
        flat_importance = importance_matrix.flatten()
        pareto_inertia_importance_flat = np.empty(flat_importance.shape, dtype=flat_importance.dtype)
        
        for original_pos, new_pos in zip(row_ind, col_ind):
            pareto_inertia_importance_flat[new_pos] = flat_importance[original_pos]
        
        pareto_inertia_importance = pareto_inertia_importance_flat.reshape(rows, cols)
    
    # Passo 3: Calcular ganho individual de cada movimentação da solução Pareto com Inércia
    movements = calculate_movement_gains(matrix, pareto_inertia_matrix, 
                                        importance_matrix, pareto_inertia_importance)
    
    # Passo 4: Identificar movimentações críticas (X% do ganho da solução com inércia)
    critical_movements, pareto_stats = identify_pareto_critical_movements(movements, critical_gain_percentage)
    
    # Passo 5: Aplicar apenas movimentações críticas (sem filtro adicional de inércia)
    # Executar novo Húngaro com penalidade para movimentações NÃO críticas
    critical_matrix, critical_importance, applied_movements, skipped_inertial = apply_critical_movements_only(
        matrix, importance_matrix, critical_movements, None
    )
    
    # Passo 6: Calcular estatísticas completas
    full_stats = get_pareto_critical_stats(
        matrix, pareto_inertia_matrix, critical_matrix,
        importance_matrix, pareto_inertia_importance, critical_importance,
        critical_movements, pareto_stats
    )
    
    full_stats['inertial_count'] = inertial_count
    full_stats['applied_movements'] = applied_movements
    full_stats['skipped_inertial'] = skipped_inertial
    full_stats['critical_movements'] = critical_movements
    full_stats['critical_gain_percentage'] = critical_gain_percentage
    
    return critical_matrix, critical_importance, full_stats


def get_optimization_stats(original_matrix, optimized_matrix, 
                          original_importance=None, optimized_importance=None):
    """
    Retorna estatísticas comparativas entre matriz original e otimizada.
    
    Args:
        original_matrix: Matriz original
        optimized_matrix: Matriz otimizada
        original_importance: Matriz de scores original
        optimized_importance: Matriz de scores otimizada
    
    Returns:
        Dicionário com estatísticas
    """
    original_cost = calculate_total_cost(original_matrix, original_importance)
    optimized_cost = calculate_total_cost(optimized_matrix, optimized_importance)
    improvement = ((original_cost - optimized_cost) / original_cost) * 100 if original_cost > 0 else 0
    
    stats = {
        'original_cost': original_cost,
        'optimized_cost': optimized_cost,
        'cost_reduction': original_cost - optimized_cost,
        'improvement_percentage': improvement
    }
    
    for row_idx in range(original_matrix.shape[0]):
        for classification in ['A', 'B', 'C']:
            original_count = np.sum(original_matrix[row_idx, :] == classification)
            optimized_count = np.sum(optimized_matrix[row_idx, :] == classification)
            
            stats[f'row_{row_idx}_{classification}_original'] = original_count
            stats[f'row_{row_idx}_{classification}_optimized'] = optimized_count
    
    return stats
