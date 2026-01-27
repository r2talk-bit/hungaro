import numpy as np
from funcao_custo import calculate_position_cost


def calculate_movement_gains(original_matrix, optimized_matrix, 
                             original_importance, optimized_importance):
    """
    Calcula o ganho individual de cada movimentação após otimização húngara.
    
    Args:
        original_matrix: Matriz original 10x10
        optimized_matrix: Matriz otimizada 10x10
        original_importance: Scores originais
        optimized_importance: Scores otimizados
    
    Returns:
        Lista de dicionários com informações de cada movimentação
    """
    rows, cols = original_matrix.shape
    flat_original = original_matrix.flatten()
    flat_optimized = optimized_matrix.flatten()
    flat_original_importance = original_importance.flatten()
    flat_optimized_importance = optimized_importance.flatten()
    
    movements = []
    
    for orig_pos in range(len(flat_original)):
        for opt_pos in range(len(flat_optimized)):
            if (flat_original[orig_pos] == flat_optimized[opt_pos] and 
                flat_original_importance[orig_pos] == flat_optimized_importance[opt_pos]):
                
                if orig_pos != opt_pos:
                    orig_row = orig_pos // cols
                    opt_row = opt_pos // cols
                    
                    importance_score = flat_original_importance[orig_pos]
                    
                    original_cost = calculate_position_cost(orig_row, importance_score)
                    optimized_cost = calculate_position_cost(opt_row, importance_score)
                    
                    gain = original_cost - optimized_cost
                    
                    movements.append({
                        'sku_classification': flat_original[orig_pos],
                        'importance_score': importance_score,
                        'original_position': orig_pos,
                        'optimized_position': opt_pos,
                        'original_row': orig_row,
                        'optimized_row': opt_row,
                        'original_cost': original_cost,
                        'optimized_cost': optimized_cost,
                        'gain': gain,
                        'gain_percentage': (gain / original_cost * 100) if original_cost > 0 else 0
                    })
                break
    
    movements.sort(key=lambda x: x['gain'], reverse=True)
    
    return movements


def identify_pareto_critical_movements(movements, target_percentage=50):
    """
    Identifica movimentações que representam X% do ganho total (Pareto configurável).
    
    Args:
        movements: Lista de movimentações ordenadas por ganho
        target_percentage: Percentual do ganho a atingir (40-80, padrão 50)
    
    Returns:
        Tupla (movimentações_críticas, estatísticas)
    """
    if not movements:
        return [], {'total_movements': 0, 'critical_movements': 0, 'total_gain': 0, 'critical_gain': 0, 'target_percentage': target_percentage}
    
    total_gain = sum(m['gain'] for m in movements)
    target_gain = total_gain * (target_percentage / 100)
    
    critical_movements = []
    accumulated_gain = 0
    
    for movement in movements:
        if accumulated_gain < target_gain:
            critical_movements.append(movement)
            accumulated_gain += movement['gain']
        else:
            break
    
    stats = {
        'total_movements': len(movements),
        'critical_movements': len(critical_movements),
        'critical_percentage': (len(critical_movements) / len(movements) * 100) if movements else 0,
        'total_gain': total_gain,
        'critical_gain': accumulated_gain,
        'critical_gain_percentage': (accumulated_gain / total_gain * 100) if total_gain > 0 else 0,
        'target_percentage': target_percentage
    }
    
    return critical_movements, stats


def apply_critical_movements_only(original_matrix, original_importance, 
                                   critical_movements, inertial_mask=None):
    """
    Aplica apenas as movimentações críticas identificadas pela análise Pareto.
    
    Estratégia: Aplicar movimentações críticas com swap correto para evitar duplicação.
    Para cada movimentação crítica, fazer swap entre origem e destino.
    
    Args:
        original_matrix: Matriz original 10x10
        original_importance: Scores originais
        critical_movements: Lista de movimentações críticas
        inertial_mask: Máscara de SKUs inerciais (não utilizado)
    
    Returns:
        Tupla (matriz_pareto, importance_pareto, applied_movements, skipped_inertial)
    """
    rows, cols = original_matrix.shape
    
    # Começar com a matriz original
    flat_pareto = original_matrix.flatten().copy()
    flat_pareto_importance = original_importance.flatten().copy()
    
    # Aplicar movimentações críticas com swap
    for movement in critical_movements:
        orig_pos = movement['original_position']
        opt_pos = movement['optimized_position']
        
        # Encontrar onde está o SKU que queremos mover na matriz atual
        sku_to_move = original_matrix.flatten()[orig_pos]
        importance_to_move = original_importance.flatten()[orig_pos]
        
        # Encontrar a posição atual desse SKU na matriz pareto
        current_pos = None
        for pos in range(len(flat_pareto)):
            if (flat_pareto[pos] == sku_to_move and 
                flat_pareto_importance[pos] == importance_to_move):
                current_pos = pos
                break
        
        if current_pos is not None and current_pos != opt_pos:
            # Fazer swap entre posição atual e posição destino
            temp_sku = flat_pareto[opt_pos]
            temp_importance = flat_pareto_importance[opt_pos]
            
            flat_pareto[opt_pos] = flat_pareto[current_pos]
            flat_pareto_importance[opt_pos] = flat_pareto_importance[current_pos]
            
            flat_pareto[current_pos] = temp_sku
            flat_pareto_importance[current_pos] = temp_importance
    
    pareto_matrix = flat_pareto.reshape(rows, cols)
    pareto_importance = flat_pareto_importance.reshape(rows, cols)
    
    applied_movements = len(critical_movements)
    skipped_inertial = 0
    
    return pareto_matrix, pareto_importance, applied_movements, skipped_inertial


def get_pareto_critical_stats(original_matrix, optimized_matrix, pareto_critical_matrix,
                               original_importance, optimized_importance, pareto_critical_importance,
                               critical_movements, pareto_stats):
    """
    Retorna estatísticas comparativas entre as três matrizes.
    
    Args:
        original_matrix: Matriz original
        optimized_matrix: Matriz otimizada (base para cálculo de movimentações)
        pareto_critical_matrix: Matriz Pareto com movimentações críticas
        original_importance: Scores originais
        optimized_importance: Scores otimizados
        pareto_critical_importance: Scores Pareto críticas
        critical_movements: Lista de movimentações críticas
        pareto_stats: Estatísticas da análise Pareto
    
    Returns:
        Dicionário com estatísticas completas
    """
    from funcao_custo import calculate_total_cost
    
    original_cost = calculate_total_cost(original_matrix, original_importance)
    optimized_cost = calculate_total_cost(optimized_matrix, optimized_importance)
    pareto_critical_cost = calculate_total_cost(pareto_critical_matrix, pareto_critical_importance)
    
    optimized_gain = original_cost - optimized_cost
    pareto_critical_gain = original_cost - pareto_critical_cost
    
    stats = {
        'original_cost': original_cost,
        'optimized_cost': optimized_cost,
        'pareto_critical_cost': pareto_critical_cost,
        'optimized_gain': optimized_gain,
        'pareto_critical_gain': pareto_critical_gain,
        'optimized_improvement_pct': (optimized_gain / original_cost * 100) if original_cost > 0 else 0,
        'pareto_critical_improvement_pct': (pareto_critical_gain / original_cost * 100) if original_cost > 0 else 0,
        'efficiency_ratio': (pareto_critical_gain / optimized_gain * 100) if optimized_gain > 0 else 0,
        'total_possible_movements': pareto_stats['total_movements'],
        'critical_movements_count': pareto_stats['critical_movements'],
        'critical_movements_pct': pareto_stats['critical_percentage'],
        'movements_avoided': pareto_stats['total_movements'] - pareto_stats['critical_movements'],
        'movements_avoided_pct': 100 - pareto_stats['critical_percentage'],
        'target_percentage': pareto_stats.get('target_percentage', 50)
    }
    
    return stats
