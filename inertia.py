import numpy as np
from funcao_custo import calculate_position_cost


def identify_inertial_skus(original_matrix, optimized_matrix, 
                           original_importance, optimized_importance, 
                           gain_threshold_pct=5):
    """
    Identifica SKUs inerciais baseado no ganho percentual da movimentação.
    SKUs com ganho < threshold% são considerados inerciais e não devem ser movidos.
    
    Args:
        original_matrix: Matriz original 10x10
        optimized_matrix: Matriz otimizada (Húngara completa) 10x10
        original_importance: Scores originais
        optimized_importance: Scores otimizados
        gain_threshold_pct: Threshold de ganho mínimo em % (padrão 5%)
    
    Returns:
        Tupla (inertial_mask, count) onde:
        - inertial_mask: Matriz booleana 10x10 indicando SKUs inerciais
        - count: Número total de SKUs inerciais
    """
    rows, cols = original_matrix.shape
    flat_original = original_matrix.flatten()
    flat_optimized = optimized_matrix.flatten()
    flat_original_importance = original_importance.flatten()
    flat_optimized_importance = optimized_importance.flatten()
    
    inertial_flat = np.zeros(len(flat_original), dtype=bool)
    
    # Para cada SKU, calcular ganho percentual da movimentação
    for orig_pos in range(len(flat_original)):
        # Encontrar onde este SKU foi parar na matriz otimizada
        for opt_pos in range(len(flat_optimized)):
            if (flat_original[orig_pos] == flat_optimized[opt_pos] and 
                flat_original_importance[orig_pos] == flat_optimized_importance[opt_pos]):
                
                # Calcular custos
                orig_row = orig_pos // cols
                opt_row = opt_pos // cols
                importance_score = flat_original_importance[orig_pos]
                
                original_cost = calculate_position_cost(orig_row, importance_score)
                optimized_cost = calculate_position_cost(opt_row, importance_score)
                
                # Calcular ganho e ganho percentual
                gain = original_cost - optimized_cost
                gain_pct = (gain / original_cost * 100) if original_cost > 0 else 0
                
                # Se ganho < threshold%, marcar como inercial
                if gain_pct < gain_threshold_pct:
                    inertial_flat[orig_pos] = True
                
                break
    
    inertial_mask = inertial_flat.reshape(rows, cols)
    count = np.sum(inertial_mask)
    return inertial_mask, count


def apply_inertia_constraint(cost_matrix, inertial_mask, penalty_factor=1000):
    """
    Aplica penalidade na matriz de custo para SKUs inerciais.
    Aumenta drasticamente o custo de mover SKUs inerciais.
    
    Args:
        cost_matrix: Matriz de custo 100x100
        inertial_mask: Matriz booleana 10x10 indicando SKUs inerciais
        penalty_factor: Fator de penalidade para movimentação
    
    Returns:
        Matriz de custo ajustada
    """
    flat_inertial = inertial_mask.flatten()
    adjusted_cost = cost_matrix.copy()
    
    for sku_idx in range(len(flat_inertial)):
        if flat_inertial[sku_idx]:
            for pos_idx in range(cost_matrix.shape[1]):
                if pos_idx != sku_idx:
                    adjusted_cost[sku_idx, pos_idx] += penalty_factor
    
    return adjusted_cost
