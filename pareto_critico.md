# Otimização Pareto Crítico - Documentação Técnica

## Visão Geral

A **Otimização Pareto Crítico** é uma estratégia que aplica apenas um subconjunto das movimentações de SKUs que representam a maior parte do ganho total, seguindo o princípio de Pareto (80/20). O objetivo é maximizar o benefício enquanto minimiza o número de movimentações físicas necessárias.

## Conceito

O princípio de Pareto aplicado ao slotting sugere que:
- **80% do ganho** pode ser obtido com apenas **20% das movimentações**
- Movimentações de alto impacto devem ser priorizadas
- Movimentações de baixo impacto podem ser evitadas para reduzir esforço operacional

## Fluxo Completo do Algoritmo

### Passo 1: Otimização Húngara Completa

**Objetivo:** Calcular a solução ótima sem restrições para identificar o potencial máximo de ganho.

**Algoritmo:**
```
1. Calcular matriz de custo C[i,j] para cada SKU i e posição j
   C[i,j] = distância(linha[j]) × importância[i] × log_amplification
   
2. Executar algoritmo Húngaro (Hungarian Algorithm)
   - Encontra assignment ótimo que minimiza custo total
   - Complexidade: O(n³)
   
3. Resultado: matriz_hungaro_completa
```

**Arquivo:** `slotting.py` - função `optimize_slotting()`

---

### Passo 2: Identificação de SKUs Inerciais

**Objetivo:** Identificar SKUs cujo ganho percentual de movimentação é inferior ao threshold configurado.

**Algoritmo:**
```
Para cada SKU i:
    custo_original = calculate_position_cost(posição_original[i], importância[i])
    custo_otimizado = calculate_position_cost(posição_hungaro[i], importância[i])
    
    ganho = custo_original - custo_otimizado
    ganho_percentual = (ganho / custo_original) × 100
    
    Se ganho_percentual < threshold_inércia:
        marcar SKU i como inercial
```

**Fórmula de Custo:**
```
custo = distância × importância × (1 + log(1 + importância/10))
```

**Parâmetro:** `gain_threshold_pct` (padrão: 5%)

**Arquivo:** `inertia.py` - função `identify_inertial_skus()`

---

### Passo 3: Otimização com Restrições de Inércia

**Objetivo:** Re-otimizar aplicando penalidade alta para SKUs inerciais, forçando-os a permanecer em suas posições originais.

**Algoritmo:**
```
1. Copiar matriz de custo original C
2. Para cada SKU inercial i:
       Para cada posição j ≠ posição_original[i]:
           C[i,j] += PENALIDADE_ALTA (ex: 1000)
           
3. Executar algoritmo Húngaro com matriz penalizada
4. Resultado: matriz_com_inércia
```

**Efeito:** SKUs inerciais ficam em suas posições originais, apenas SKUs com alto ganho são movimentados.

**Arquivo:** `optimize_inertia.py` - função `optimize_slotting_with_inertia()`

---

### Passo 4: Cálculo de Ganho por Movimentação

**Objetivo:** Calcular o ganho individual de cada movimentação da solução com inércia.

**Algoritmo:**
```
movimentações = []

Para cada SKU i:
    posição_original = encontrar_posição(SKU i, matriz_original)
    posição_otimizada = encontrar_posição(SKU i, matriz_com_inércia)
    
    Se posição_original ≠ posição_otimizada:
        linha_original = posição_original // 10
        linha_otimizada = posição_otimizada // 10
        
        custo_original = calculate_position_cost(linha_original, importância[i])
        custo_otimizado = calculate_position_cost(linha_otimizada, importância[i])
        
        ganho = custo_original - custo_otimizado
        
        movimentações.append({
            'sku': i,
            'de': posição_original,
            'para': posição_otimizada,
            'ganho': ganho
        })

Ordenar movimentações por ganho (decrescente)
```

**Arquivo:** `pareto_analysis.py` - função `calculate_movement_gains()`

---

### Passo 5: Identificação de Movimentações Críticas

**Objetivo:** Selecionar as N primeiras movimentações que acumulam X% do ganho total (princípio de Pareto).

**Algoritmo:**
```
ganho_total = soma(movimentação.ganho para todas movimentações)
ganho_alvo = ganho_total × (percentual_pareto / 100)

movimentações_críticas = []
ganho_acumulado = 0

Para cada movimentação em movimentações (ordenadas por ganho):
    Se ganho_acumulado < ganho_alvo:
        movimentações_críticas.append(movimentação)
        ganho_acumulado += movimentação.ganho
    Senão:
        break

Retornar movimentações_críticas
```

**Parâmetro:** `critical_gain_percentage` (padrão: 50%, configurável 40-80%)

**Exemplo:**
- 10 movimentações com ganho total = 1000
- Threshold Pareto = 80%
- Ganho alvo = 800
- Movimentações: [200, 150, 120, 100, 80, 70, 60, 50, 40, 30]
- **Selecionadas:** [200, 150, 120, 100, 80, 70, 60] = 880 ≥ 800
- **Resultado:** 7 movimentações (70% das movimentações, 88% do ganho)

**Arquivo:** `pareto_analysis.py` - função `identify_pareto_critical_movements()`

---

### Passo 6: Aplicação de Movimentações Críticas

**Objetivo:** Aplicar apenas as movimentações críticas selecionadas através de SWAPs sequenciais.

**Algoritmo:**
```
matriz_pareto = cópia(matriz_original)

Para cada movimentação em movimentações_críticas:
    sku = movimentação.sku
    posição_destino = movimentação.para
    
    # Encontrar posição atual do SKU na matriz
    posição_atual = encontrar_posição(sku, matriz_pareto)
    
    Se posição_atual ≠ posição_destino:
        # Fazer SWAP entre posição atual e destino
        temp = matriz_pareto[posição_destino]
        matriz_pareto[posição_destino] = matriz_pareto[posição_atual]
        matriz_pareto[posição_atual] = temp

Retornar matriz_pareto
```

**Importante:** 
- Os SWAPs são aplicados sequencialmente
- Cada SWAP troca dois SKUs de posição
- Não há duplicação ou perda de SKUs
- A ordem de aplicação dos SWAPs pode afetar o resultado final

**Arquivo:** `pareto_analysis.py` - função `apply_critical_movements_only()`

---

## Cálculo de Estatísticas

### Métricas Calculadas

```
custo_original = calculate_total_cost(matriz_original)
custo_inércia = calculate_total_cost(matriz_com_inércia)
custo_pareto = calculate_total_cost(matriz_pareto)

ganho_inércia = custo_original - custo_inércia
ganho_pareto = custo_original - custo_pareto

melhoria_inércia% = (ganho_inércia / custo_original) × 100
melhoria_pareto% = (ganho_pareto / custo_original) × 100

eficiência_pareto = (ganho_pareto / ganho_inércia) × 100
```

### Exemplo de Resultado

**Cenário:**
- Custo Original: 92.017
- Custo com Inércia: 73.693 (ganho: 18.324 = 19.9%)
- Threshold Pareto: 80%

**Resultado Esperado:**
- Movimentações Inércia: 10
- Movimentações Pareto: 6 (60% das movimentações)
- Ganho Pareto: ~14.659 (≈80% de 18.324)
- Melhoria Pareto: ~15.9% (80% de 19.9%)
- Eficiência: 80%

---

## Comparação de Soluções

| Solução | Movimentações | Ganho | Melhoria % | Eficiência |
|---------|---------------|-------|------------|------------|
| **Húngaro Completo** | 60 | 28.800 | 31.3% | 100% |
| **Com Inércia** | 10 | 18.324 | 19.9% | 63.6% |
| **Pareto 80%** | 6 | 14.659 | 15.9% | 50.9% |
| **Pareto 50%** | 3 | 9.162 | 10.0% | 31.8% |

**Análise:**
- Pareto 80% obtém 80% do ganho da solução com inércia usando apenas 60% das movimentações
- Trade-off entre ganho e esforço operacional
- Threshold configurável permite ajustar o equilíbrio

---

## Arquivos e Funções

### `slotting.py`
- `optimize_slotting()` - Otimização Húngara completa
- `optimize_slotting_pareto_critical()` - Orquestração completa do Pareto Crítico

### `inertia.py`
- `identify_inertial_skus()` - Identificação de SKUs inerciais por ganho%
- `apply_inertia_constraint()` - Aplicação de penalidade na matriz de custo

### `optimize_inertia.py`
- `optimize_slotting_with_inertia()` - Otimização com restrições de inércia

### `pareto_analysis.py`
- `calculate_movement_gains()` - Cálculo de ganho por movimentação
- `identify_pareto_critical_movements()` - Seleção de movimentações críticas
- `apply_critical_movements_only()` - Aplicação de SWAPs
- `get_pareto_critical_stats()` - Cálculo de estatísticas comparativas

### `funcao_custo.py`
- `calculate_position_cost()` - Cálculo de custo de uma posição
- `calculate_cost_matrix()` - Cálculo da matriz de custo completa
- `calculate_total_cost()` - Cálculo do custo total de uma solução

---

## Parâmetros Configuráveis

### Threshold de Inércia (`gain_threshold_pct`)
- **Padrão:** 5%
- **Faixa:** 0-50%
- **Significado:** SKUs com ganho < threshold% não são movimentados
- **Impacto:** Quanto maior, menos movimentações

### Percentual de Ganho Pareto (`critical_gain_percentage`)
- **Padrão:** 50%
- **Faixa:** 40-80%
- **Significado:** Percentual do ganho da solução com inércia a ser atingido
- **Impacto:** Quanto maior, mais movimentações críticas selecionadas

---

## Complexidade Computacional

| Operação | Complexidade | Observação |
|----------|--------------|------------|
| Algoritmo Húngaro | O(n³) | n = 100 (matriz 10×10) |
| Identificação Inercial | O(n) | Linear no número de SKUs |
| Cálculo de Ganhos | O(n²) | Busca de posições |
| Seleção Pareto | O(n log n) | Ordenação + acumulação |
| Aplicação SWAPs | O(k×n) | k = movimentações críticas |
| **Total** | **O(n³)** | Dominado pelo Húngaro |

Para matriz 10×10 (100 SKUs), o algoritmo executa em tempo aceitável (<1s).

---

## Vantagens e Limitações

### Vantagens
✅ Reduz número de movimentações físicas necessárias  
✅ Mantém maior parte do ganho (80% com 20-40% das movimentações)  
✅ Configurável via threshold Pareto  
✅ Respeita restrições de inércia  
✅ Baseado em princípio comprovado (Pareto)  

### Limitações
⚠️ Ganho menor que solução completa  
⚠️ Ordem de aplicação dos SWAPs pode afetar resultado  
⚠️ Não garante solução ótima para o subconjunto selecionado  
⚠️ Requer dois passos de otimização (Húngaro + Inércia)  

---

## Conclusão

A Otimização Pareto Crítico oferece um equilíbrio prático entre ganho de eficiência e esforço operacional, permitindo que gestores de armazém implementem melhorias significativas com um número reduzido de movimentações de SKUs.
