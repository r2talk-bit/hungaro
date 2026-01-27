import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import importlib
import sys
import time

# Importar módulos primeiro
import slotting
import funcao_custo
import affinity
import inertia
import affinity_optimizer
import pareto_analysis
import optimize_inertia

# Forçar reload de módulos para evitar cache
importlib.reload(slotting)
importlib.reload(funcao_custo)
importlib.reload(affinity)
importlib.reload(inertia)
importlib.reload(affinity_optimizer)
importlib.reload(pareto_analysis)
importlib.reload(optimize_inertia)

# Importar funções específicas após reload
from slotting import optimize_slotting, optimize_slotting_pareto, optimize_slotting_with_affinity_post, optimize_slotting_pareto_critical, get_optimization_stats
from optimize_inertia import optimize_slotting_with_inertia
from funcao_custo import calculate_total_cost
from affinity import create_affinity_matrix_from_positions, get_affinity_info

st.set_page_config(page_title="Warehouse Matrix", layout="wide")

st.title("🏭 Matriz de Armazém - Otimização de Slotting")
st.markdown("Cada célula representa uma localização no armazém com classificação ABC de frequência de pedidos")

def generate_importance_matrix(classification_matrix):
    """
    Gera matriz de importância baseada na classificação ABC.
    A: 70-100, B: 50-69, C: 1-49
    """
    importance = np.zeros(classification_matrix.shape, dtype=int)
    for i in range(classification_matrix.shape[0]):
        for j in range(classification_matrix.shape[1]):
            if classification_matrix[i, j] == 'A':
                importance[i, j] = np.random.randint(70, 101)
            elif classification_matrix[i, j] == 'B':
                importance[i, j] = np.random.randint(50, 70)
            else:  # C
                importance[i, j] = np.random.randint(1, 50)
    return importance

if 'matrix' not in st.session_state:
    st.session_state.matrix = np.random.choice(['A', 'B', 'C'], size=(10, 10))
    st.session_state.importance_matrix = generate_importance_matrix(st.session_state.matrix)

if 'importance_matrix' not in st.session_state:
    st.session_state.importance_matrix = generate_importance_matrix(st.session_state.matrix)

if 'optimized_matrix' not in st.session_state:
    st.session_state.optimized_matrix = None

if 'optimized_importance' not in st.session_state:
    st.session_state.optimized_importance = None

if 'show_optimized' not in st.session_state:
    st.session_state.show_optimized = False

if 'affinity_weight' not in st.session_state:
    st.session_state.affinity_weight = 0.0

if 'selected_positions' not in st.session_state:
    st.session_state.selected_positions = []

if 'affinity_matrix' not in st.session_state:
    st.session_state.affinity_matrix = None

if 'pareto_matrix' not in st.session_state:
    st.session_state.pareto_matrix = None

if 'pareto_importance' not in st.session_state:
    st.session_state.pareto_importance = None

if 'inertial_count' not in st.session_state:
    st.session_state.inertial_count = 0

if 'gain_threshold_pct' not in st.session_state:
    st.session_state.gain_threshold_pct = 5

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'original'

if 'affinity_post_matrix' not in st.session_state:
    st.session_state.affinity_post_matrix = None

if 'affinity_post_importance' not in st.session_state:
    st.session_state.affinity_post_importance = None

if 'affinity_post_stats' not in st.session_state:
    st.session_state.affinity_post_stats = None

if 'max_cost_increase_pct' not in st.session_state:
    st.session_state.max_cost_increase_pct = 2.0

if 'pareto_critical_matrix' not in st.session_state:
    st.session_state.pareto_critical_matrix = None

if 'pareto_critical_importance' not in st.session_state:
    st.session_state.pareto_critical_importance = None

if 'pareto_critical_stats' not in st.session_state:
    st.session_state.pareto_critical_stats = None

if 'critical_gain_percentage' not in st.session_state:
    st.session_state.critical_gain_percentage = 50

if 'pareto_animation_active' not in st.session_state:
    st.session_state.pareto_animation_active = False

if 'pareto_animation_step' not in st.session_state:
    st.session_state.pareto_animation_step = 0

if 'pareto_animation_matrix' not in st.session_state:
    st.session_state.pareto_animation_matrix = None

if 'pareto_animation_importance' not in st.session_state:
    st.session_state.pareto_animation_importance = None

if 'pareto_swap_positions' not in st.session_state:
    st.session_state.pareto_swap_positions = []

if 'inertia_matrix' not in st.session_state:
    st.session_state.inertia_matrix = None

if 'inertia_importance' not in st.session_state:
    st.session_state.inertia_importance = None

if 'inertia_count' not in st.session_state:
    st.session_state.inertia_count = 0

col1, col2 = st.columns([2, 3])

with col1:
    if st.session_state.view_mode == 'optimized' and st.session_state.optimized_matrix is not None:
        st.subheader("Matriz Ótima - Algoritmo Húngaro")
        display_matrix = st.session_state.optimized_matrix
        display_importance = st.session_state.optimized_importance
    elif st.session_state.view_mode == 'inertia' and st.session_state.inertia_matrix is not None:
        st.subheader("Matriz Otimizada com Inércia")
        display_matrix = st.session_state.inertia_matrix
        display_importance = st.session_state.inertia_importance
    elif st.session_state.view_mode == 'pareto_animation' and st.session_state.pareto_animation_active:
        # Modo de animação de SWAPs
        critical_movements = st.session_state.pareto_critical_stats.get('critical_movements', [])
        total_swaps = len(critical_movements)
        current_step = st.session_state.pareto_animation_step
        
        if current_step < total_swaps:
            movement = critical_movements[current_step]
            
            # Aplicar SWAP atual
            orig_pos = movement['original_position']
            opt_pos = movement['optimized_position']
            
            # Encontrar posição atual do SKU
            flat_matrix = st.session_state.pareto_animation_matrix.flatten().copy()
            flat_importance = st.session_state.pareto_animation_importance.flatten().copy()
            flat_original = st.session_state.matrix.flatten()
            flat_original_importance = st.session_state.importance_matrix.flatten()
            
            sku_to_move = flat_original[orig_pos]
            importance_to_move = flat_original_importance[orig_pos]
            
            current_pos = None
            for pos in range(len(flat_matrix)):
                if (flat_matrix[pos] == sku_to_move and 
                    flat_importance[pos] == importance_to_move):
                    current_pos = pos
                    break
            
            # Se SKU já está na posição destino, pular para próximo SWAP
            if current_pos == opt_pos:
                st.session_state.pareto_animation_step += 1
                st.rerun()
            
            # Calcular linha atual e linha destino
            current_row = current_pos // 10 if current_pos is not None else movement['original_row']
            opt_row = opt_pos // 10
            
            st.subheader(f"🎬 Animação Pareto - SWAP {current_step + 1}/{total_swaps}")
            st.info(f"**Movimentação:** SKU {movement['sku_classification']}{movement['importance_score']} | "
                   f"Linha {current_row} → Linha {opt_row} | "
                   f"Ganho: {movement['gain']:.2f}")
            
            if current_pos is not None and current_pos != opt_pos:
                # Armazenar posições sendo trocadas para destaque visual
                st.session_state.pareto_swap_positions = [current_pos, opt_pos]
                
                # Fazer SWAP
                temp_sku = flat_matrix[opt_pos]
                temp_importance = flat_importance[opt_pos]
                
                flat_matrix[opt_pos] = flat_matrix[current_pos]
                flat_importance[opt_pos] = flat_importance[current_pos]
                
                flat_matrix[current_pos] = temp_sku
                flat_importance[current_pos] = temp_importance
                
                st.session_state.pareto_animation_matrix = flat_matrix.reshape(10, 10)
                st.session_state.pareto_animation_importance = flat_importance.reshape(10, 10)
            else:
                st.session_state.pareto_swap_positions = []
            
            display_matrix = st.session_state.pareto_animation_matrix
            display_importance = st.session_state.pareto_animation_importance
        else:
            # Animação completa
            st.session_state.pareto_animation_active = False
            st.session_state.pareto_swap_positions = []
            st.session_state.view_mode = 'pareto_critical'
            st.success("✅ Animação completa!")
            display_matrix = st.session_state.pareto_critical_matrix
            display_importance = st.session_state.pareto_critical_importance
    elif st.session_state.view_mode == 'pareto_critical' and st.session_state.pareto_critical_matrix is not None:
        st.subheader(f"Matriz Pareto Crítica ({st.session_state.critical_gain_percentage}% do Ganho)")
        display_matrix = st.session_state.pareto_critical_matrix
        display_importance = st.session_state.pareto_critical_importance
    elif st.session_state.view_mode == 'affinity_post' and st.session_state.affinity_post_matrix is not None:
        st.subheader("Matriz Otimizada + Ajuste de Afinidade")
        display_matrix = st.session_state.affinity_post_matrix
        display_importance = st.session_state.affinity_post_importance
    elif st.session_state.view_mode == 'pareto' and st.session_state.pareto_matrix is not None:
        st.subheader("Matriz Pareto - Com Inércia")
        display_matrix = st.session_state.pareto_matrix
        display_importance = st.session_state.pareto_importance
    elif st.session_state.view_mode == 'optimized' and st.session_state.optimized_matrix is not None:
        st.subheader("Matriz Ótima - Algoritmo Húngaro")
        display_matrix = st.session_state.optimized_matrix
        display_importance = st.session_state.optimized_importance
    else:
        st.subheader("Matriz Original do Armazém")
        display_matrix = st.session_state.matrix
        display_importance = st.session_state.importance_matrix
    
    # Legenda de destaques
    if st.session_state.view_mode != 'original':
        legend_cols = st.columns(3)
        with legend_cols[0]:
            st.markdown("🟢 **Verde**: SKU movimentado")
        with legend_cols[1]:
            if st.session_state.view_mode == 'pareto' and st.session_state.pareto_matrix is not None:
                st.markdown("🔵 **Azul**: SKU não movido (inercial)")
        with legend_cols[2]:
            if st.session_state.selected_positions:
                st.markdown("🟣 **Roxo**: SKU com afinidade")
    
    matrix_html = "<style>"
    matrix_html += """
    .warehouse-table {
        border-collapse: collapse;
        margin: 3px 0;
        font-size: 11px;
        font-family: 'Courier New', monospace;
    }
    .warehouse-table td {
        width: 38px;
        height: 38px;
        text-align: center;
        vertical-align: middle;
        border: 1px solid #333;
        background-color: #f5f5f5;
        cursor: pointer;
        transition: transform 0.2s;
        padding: 1px;
    }
    .warehouse-table td:hover {
        transform: scale(1.05);
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
    }
    .cell-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0px;
    }
    .circle {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 21px;
        height: 21px;
        border-radius: 50%;
        font-weight: bold;
        font-size: 10px;
    }
    .position-number {
        font-size: 7px;
        color: #666;
        font-weight: normal;
    }
    .circle-A {
        background-color: #ff6b6b;
        color: white;
    }
    .circle-B {
        background-color: #ffd93d;
        color: #333;
    }
    .circle-C {
        background-color: #6bcf7f;
        color: white;
    }
    .row-header, .col-header {
        background-color: #e0e0e0;
        font-weight: bold;
        color: #333;
    }
    .affinity-highlight {
        border: 4px solid #ff00ff !important;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.6) !important;
        background-color: #ffe6ff !important;
    }
    .affinity-highlight:hover {
        box-shadow: 0 0 20px rgba(255, 0, 255, 0.8) !important;
    }
    .unchanged-position {
        border: 4px solid #4169E1 !important;
        box-shadow: 0 0 15px rgba(65, 105, 225, 0.6) !important;
        background-color: #E6F0FF !important;
    }
    .unchanged-position:hover {
        box-shadow: 0 0 20px rgba(65, 105, 225, 0.8) !important;
    }
    .moved-position {
        border: 4px solid #00C853 !important;
        box-shadow: 0 0 15px rgba(0, 200, 83, 0.6) !important;
        background-color: #E8F5E9 !important;
    }
    .moved-position:hover {
        box-shadow: 0 0 20px rgba(0, 200, 83, 0.8) !important;
    }
    .swap-highlight {
        border: 4px solid #FF5722 !important;
        box-shadow: 0 0 20px rgba(255, 87, 34, 0.8) !important;
        background-color: #FFE0B2 !important;
        animation: pulse 0.5s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    </style>
    """
    
    matrix_html += "<table class='warehouse-table'>"
    
    matrix_html += "<tr><td class='row-header'></td>"
    for j in range(10):
        matrix_html += f"<td class='col-header'>{j}</td>"
    matrix_html += "</tr>"
    
    # Criar mapeamento de posições com afinidade para matriz otimizada
    affinity_positions_in_display = set()
    unchanged_positions = set()
    moved_positions = set()
    
    # Identificar SKUs que foram movimentados em relação à matriz original
    if st.session_state.view_mode != 'original':
        flat_original = st.session_state.matrix.flatten()
        flat_original_importance = st.session_state.importance_matrix.flatten()
        flat_display = display_matrix.flatten()
        flat_display_importance = display_importance.flatten()
        
        for pos in range(len(flat_original)):
            # Verificar se o SKU na posição atual é diferente do original
            if (flat_original[pos] != flat_display[pos] or 
                flat_original_importance[pos] != flat_display_importance[pos]):
                moved_positions.add(pos)
    
    if st.session_state.selected_positions:
        if st.session_state.view_mode == 'affinity_post' and st.session_state.affinity_post_matrix is not None:
            # Encontrar onde os SKUs das posições originais estão na matriz affinity_post
            flat_original = st.session_state.matrix.flatten()
            flat_affinity_post = st.session_state.affinity_post_matrix.flatten()
            
            for orig_pos in st.session_state.selected_positions:
                # Encontrar onde o SKU da posição original está na affinity_post
                for aff_pos in range(len(flat_affinity_post)):
                    if (flat_original[orig_pos] == flat_affinity_post[aff_pos] and 
                        st.session_state.importance_matrix.flatten()[orig_pos] == 
                        st.session_state.affinity_post_importance.flatten()[aff_pos]):
                        # Verificar se é a mesma combinação única
                        affinity_positions_in_display.add(aff_pos)
                        break
        elif st.session_state.view_mode == 'optimized' and st.session_state.optimized_matrix is not None:
            # Encontrar onde os SKUs das posições originais estão na matriz otimizada
            flat_original = st.session_state.matrix.flatten()
            flat_optimized = st.session_state.optimized_matrix.flatten()
            
            for orig_pos in st.session_state.selected_positions:
                # Encontrar onde o SKU da posição original está na otimizada
                for opt_pos in range(len(flat_optimized)):
                    if (flat_original[orig_pos] == flat_optimized[opt_pos] and 
                        st.session_state.importance_matrix.flatten()[orig_pos] == 
                        st.session_state.optimized_importance.flatten()[opt_pos]):
                        # Verificar se é a mesma combinação única
                        affinity_positions_in_display.add(opt_pos)
                        break
        elif st.session_state.view_mode == 'pareto' and st.session_state.pareto_matrix is not None:
            # Encontrar onde os SKUs das posições originais estão na matriz pareto
            flat_original = st.session_state.matrix.flatten()
            flat_pareto = st.session_state.pareto_matrix.flatten()
            
            for orig_pos in st.session_state.selected_positions:
                # Encontrar onde o SKU da posição original está na pareto
                for pareto_pos in range(len(flat_pareto)):
                    if (flat_original[orig_pos] == flat_pareto[pareto_pos] and 
                        st.session_state.importance_matrix.flatten()[orig_pos] == 
                        st.session_state.pareto_importance.flatten()[pareto_pos]):
                        # Verificar se é a mesma combinação única
                        affinity_positions_in_display.add(pareto_pos)
                        break
        else:
            # Matriz original - usar posições diretas
            affinity_positions_in_display = set(st.session_state.selected_positions)
    
    # Identificar células que não foram movidas na visualização Pareto
    if st.session_state.view_mode == 'pareto' and st.session_state.pareto_matrix is not None:
        flat_original = st.session_state.matrix.flatten()
        flat_pareto = st.session_state.pareto_matrix.flatten()
        flat_original_importance = st.session_state.importance_matrix.flatten()
        flat_pareto_importance = st.session_state.pareto_importance.flatten()
        
        for pos in range(len(flat_original)):
            # Verificar se o SKU permaneceu na mesma posição
            if (flat_original[pos] == flat_pareto[pos] and 
                flat_original_importance[pos] == flat_pareto_importance[pos]):
                unchanged_positions.add(pos)
    
    for i in range(10):
        matrix_html += f"<tr><td class='row-header'>{i}</td>"
        for j in range(10):
            classification = display_matrix[i][j]
            importance = display_importance[i][j]
            position = i * 10 + j
            
            # Adicionar classe de highlight (prioridade: swap > afinidade > unchanged > moved)
            highlight_class = ""
            if st.session_state.view_mode == 'pareto_animation' and position in st.session_state.pareto_swap_positions:
                highlight_class = " swap-highlight"
            elif position in affinity_positions_in_display:
                highlight_class = " affinity-highlight"
            elif position in unchanged_positions:
                highlight_class = " unchanged-position"
            elif position in moved_positions:
                highlight_class = " moved-position"
            
            matrix_html += f"<td class='{highlight_class}'><div class='cell-content'><div class='circle circle-{classification}'>{classification}<br><span style='font-size:6px'>{importance}</span></div></div></td>"
        matrix_html += "</tr>"
    
    matrix_html += "</table>"
    
    components.html(matrix_html, height=480, scrolling=False)
    
    # Botão manual para avançar animação Pareto
    if st.session_state.view_mode == 'pareto_animation' and st.session_state.pareto_animation_active:
        critical_movements = st.session_state.pareto_critical_stats.get('critical_movements', [])
        if st.session_state.pareto_animation_step < len(critical_movements):
            # Mostrar botão para avançar manualmente
            col_a, col_b = st.columns([3, 1])
            with col_b:
                if st.button("⏭️ Próximo SWAP", key=f"next_swap_{st.session_state.pareto_animation_step}"):
                    st.session_state.pareto_animation_step += 1
                    st.rerun()

with col2:
    # Criar 4 sub-colunas: Otimização, Estatísticas, Comparação e Visualizar/Ações
    subcol1, subcol2, subcol3, subcol4 = st.columns([1, 1, 1.2, 1])
    
    with subcol1:
        st.subheader("Otimização")
        
        # Configuração de Inércia
        with st.expander("⚙️ Configurar Inércia", expanded=False):
            st.markdown("**Ganho Mínimo para Movimentação (%)**")
            gain_threshold_pct = st.slider(
                "Ganho Mínimo",
                min_value=0,
                max_value=50,
                value=st.session_state.gain_threshold_pct,
                step=1,
                help="SKUs com ganho < threshold% são considerados inerciais e não serão movimentados",
                label_visibility="collapsed"
            )
            st.session_state.gain_threshold_pct = gain_threshold_pct
            st.caption(f"SKUs com ganho < {gain_threshold_pct}% não serão movimentados")
        
        # Configuração de Movimentações Críticas
        with st.expander("⚙️ Movimentações Críticas", expanded=False):
            st.markdown("**Percentual do Ganho Alvo (%)**")
            critical_gain_pct = st.slider(
                "Ganho Alvo",
                min_value=40,
                max_value=80,
                value=st.session_state.critical_gain_percentage,
                step=5,
                help="Percentual do ganho da solução Pareto com Inércia a ser atingido",
                label_visibility="collapsed"
            )
            st.session_state.critical_gain_percentage = critical_gain_pct
            st.caption(f"Aplicar movimentações que somam {critical_gain_pct}% do ganho da solução com inércia")
        
        if st.button("🎯 Otimizar Húngaro (Completo)", use_container_width=True, type="primary"):
            with st.spinner("Otimizando posições..."):
                st.session_state.optimized_matrix, st.session_state.optimized_importance = optimize_slotting(
                    st.session_state.matrix, 
                    st.session_state.importance_matrix,
                    None,  # sem affinity_matrix
                    0.0    # sem affinity_weight
                )
                st.session_state.view_mode = 'optimized'
            st.rerun()
        
        if st.button("🔒 Otimizar com Inércia", use_container_width=True, type="secondary"):
            with st.spinner("Otimizando com restrições de inércia..."):
                st.session_state.inertia_matrix, st.session_state.inertia_importance, st.session_state.inertia_count = optimize_slotting_with_inertia(
                    st.session_state.matrix, 
                    st.session_state.importance_matrix,
                    None,  # sem affinity_matrix
                    0.0,   # sem affinity_weight
                    st.session_state.gain_threshold_pct
                )
                st.session_state.view_mode = 'inertia'
            st.rerun()
        
        if st.button("📊 Otimizar Pareto Crítico", use_container_width=True, type="secondary"):
            with st.spinner("Analisando movimentações críticas..."):
                st.session_state.pareto_critical_matrix, st.session_state.pareto_critical_importance, st.session_state.pareto_critical_stats = optimize_slotting_pareto_critical(
                    st.session_state.matrix, 
                    st.session_state.importance_matrix,
                    st.session_state.affinity_matrix,
                    st.session_state.affinity_weight,
                    st.session_state.gain_threshold_pct,
                    st.session_state.critical_gain_percentage
                )
                st.session_state.view_mode = 'pareto_critical'
            st.rerun()
    
    with subcol2:
        st.markdown("#### Estatísticas")
        total_cells = 100
        count_A = np.sum(display_matrix == 'A')
        count_B = np.sum(display_matrix == 'B')
        count_C = np.sum(display_matrix == 'C')
        current_cost = calculate_total_cost(display_matrix, display_importance)
        
        st.markdown(f"**A:** {count_A} | **B:** {count_B} | **C:** {count_C}")
        st.markdown(f"**Custo:** {current_cost:.0f}")
    
    with subcol3:
        st.markdown("#### Comparação")
        
        if st.session_state.optimized_matrix is not None and st.session_state.view_mode == 'optimized':
            stats = get_optimization_stats(
                st.session_state.matrix, 
                st.session_state.optimized_matrix,
                st.session_state.importance_matrix,
                st.session_state.optimized_importance
            )
            
            st.metric("Custo Original", f"{stats['original_cost']:.0f}")
            st.metric("Custo Otimizado", f"{stats['optimized_cost']:.0f}", 
                     delta=f"{-stats['cost_reduction']:.0f}")
            
            st.success(f"✅ Melhoria: {stats['improvement_percentage']:.1f}%")
            st.info("🎯 Solução ótima completa")
        
        elif st.session_state.inertia_matrix is not None and st.session_state.view_mode == 'inertia':
            stats = get_optimization_stats(
                st.session_state.matrix, 
                st.session_state.inertia_matrix,
                st.session_state.importance_matrix,
                st.session_state.inertia_importance
            )
            
            st.metric("Custo Original", f"{stats['original_cost']:.0f}")
            st.metric("Custo Otimizado", f"{stats['optimized_cost']:.0f}", 
                     delta=f"{-stats['cost_reduction']:.0f}")
            
            st.success(f"✅ Melhoria: {stats['improvement_percentage']:.1f}%")
            st.info(f"🔒 SKUs Inerciais: {st.session_state.inertia_count}")
        
        elif st.session_state.pareto_critical_matrix is not None and st.session_state.view_mode == 'pareto_critical':
            stats_pc = st.session_state.pareto_critical_stats
            
            st.metric("Custo Original", f"{stats_pc['original_cost']:.0f}")
            st.metric("Custo Otimizado", f"{stats_pc['pareto_critical_cost']:.0f}", 
                     delta=f"{-stats_pc['pareto_critical_gain']:.0f}")
            
            st.success(f"✅ Melhoria: {stats_pc['pareto_critical_improvement_pct']:.1f}%")
            
            st.info(f"📊 Movimentações: {stats_pc['applied_movements']}/{stats_pc['total_possible_movements']} ({stats_pc['critical_movements_pct']:.1f}%)")
            st.caption(f"Eficiência: {stats_pc['efficiency_ratio']:.1f}% | Alvo: {stats_pc['target_percentage']}%")
            
            if stats_pc.get('inertial_count', 0) > 0:
                st.info(f"🔒 SKUs Inerciais: {stats_pc['inertial_count']}")
            
            if stats_pc.get('skipped_inertial', 0) > 0:
                st.caption(f"⚠️ {stats_pc['skipped_inertial']} movimentações inerciais evitadas")
        else:
            st.caption("Execute uma otimização para ver a comparação")
    
    with subcol4:
        st.markdown("#### Visualizar")
        
        if st.session_state.optimized_matrix is not None or st.session_state.inertia_matrix is not None or st.session_state.pareto_critical_matrix is not None:
            if st.button("📊 Original", use_container_width=True):
                st.session_state.view_mode = 'original'
                st.rerun()
            if st.button("🎯 Húngaro", use_container_width=True):
                st.session_state.view_mode = 'optimized'
                st.rerun()
            if st.button("🔒 Inércia", use_container_width=True):
                st.session_state.view_mode = 'inertia'
                st.rerun()
            if st.button("✨ Pareto", use_container_width=True):
                if st.session_state.pareto_critical_stats is not None:
                    # Iniciar animação de SWAPs
                    st.session_state.pareto_animation_active = True
                    st.session_state.pareto_animation_step = 0
                    st.session_state.pareto_animation_matrix = st.session_state.matrix.copy()
                    st.session_state.pareto_animation_importance = st.session_state.importance_matrix.copy()
                    st.session_state.view_mode = 'pareto_animation'
                else:
                    st.session_state.view_mode = 'pareto_critical'
                st.rerun()
            
            if st.button("🔄 Resetar", use_container_width=True):
                st.session_state.optimized_matrix = None
                st.session_state.optimized_importance = None
                st.session_state.inertia_matrix = None
                st.session_state.inertia_importance = None
                st.session_state.inertia_count = 0
                st.session_state.pareto_critical_matrix = None
                st.session_state.pareto_critical_importance = None
                st.session_state.pareto_critical_stats = None
                st.session_state.view_mode = 'original'
                st.success("✅ Resetado!")
                st.rerun()
        
        st.markdown("**Ações**")
        if st.button("🔄 Gerar Nova Matriz", use_container_width=True):
            st.session_state.matrix = np.random.choice(['A', 'B', 'C'], size=(10, 10))
            st.session_state.importance_matrix = generate_importance_matrix(st.session_state.matrix)
            st.session_state.optimized_matrix = None
            st.session_state.optimized_importance = None
            st.session_state.inertia_matrix = None
            st.session_state.inertia_importance = None
            st.session_state.inertia_count = 0
            st.session_state.pareto_critical_matrix = None
            st.session_state.pareto_critical_importance = None
            st.session_state.pareto_critical_stats = None
            st.session_state.view_mode = 'original'
            st.rerun()
        
        st.markdown("**Distribuição**")
        prob_A = st.slider("A (%)", 0, 100, 33)
        prob_B = st.slider("B (%)", 0, 100, 33)
        prob_C = 100 - prob_A - prob_B
        st.caption(f"C: {prob_C}%")
        
        if st.button("Aplicar", use_container_width=True):
            probs = [prob_A/100, prob_B/100, prob_C/100]
            st.session_state.matrix = np.random.choice(['A', 'B', 'C'], size=(10, 10), p=probs)
            st.session_state.importance_matrix = generate_importance_matrix(st.session_state.matrix)
            st.session_state.optimized_matrix = None
            st.session_state.optimized_importance = None
            st.session_state.inertia_matrix = None
            st.session_state.inertia_importance = None
            st.session_state.inertia_count = 0
            st.session_state.optimized_importance = None
            st.session_state.pareto_critical_matrix = None
            st.session_state.pareto_critical_importance = None
            st.session_state.pareto_critical_stats = None
            st.session_state.view_mode = 'original'
            st.rerun()

