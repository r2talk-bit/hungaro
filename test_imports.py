#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar importações
"""

print("Testando importações...")

try:
    from slotting import optimize_slotting, optimize_slotting_pareto, optimize_slotting_with_affinity_post, optimize_slotting_pareto_critical, get_optimization_stats
    print("✅ slotting importado com sucesso")
    print(f"   - optimize_slotting: {optimize_slotting}")
    print(f"   - optimize_slotting_pareto: {optimize_slotting_pareto}")
    print(f"   - optimize_slotting_with_affinity_post: {optimize_slotting_with_affinity_post}")
    print(f"   - optimize_slotting_pareto_critical: {optimize_slotting_pareto_critical}")
    print(f"   - get_optimization_stats: {get_optimization_stats}")
except Exception as e:
    print(f"❌ Erro ao importar slotting: {e}")
    import traceback
    traceback.print_exc()

try:
    from optimize_inertia import optimize_slotting_with_inertia
    print("✅ optimize_inertia importado com sucesso")
    print(f"   - optimize_slotting_with_inertia: {optimize_slotting_with_inertia}")
except Exception as e:
    print(f"❌ Erro ao importar optimize_inertia: {e}")
    import traceback
    traceback.print_exc()

try:
    from funcao_custo import calculate_total_cost
    print("✅ funcao_custo importado com sucesso")
    print(f"   - calculate_total_cost: {calculate_total_cost}")
except Exception as e:
    print(f"❌ Erro ao importar funcao_custo: {e}")
    import traceback
    traceback.print_exc()

print("\nTodas as importações testadas!")
