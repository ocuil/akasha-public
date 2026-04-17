#!/usr/bin/env python3
"""
📊 Proyección de Costes: Con Akasha vs Sin Akasha

Genera gráficos de comparación de costes a escala (1-50 agentes)
con hipótesis realistas de crecimiento no lineal para infraestructura.

Uso:
    python3 generate_cost_charts.py

Genera:
    cost_projection_main.png     — Comparativa principal (3 escenarios)
    cost_projection_breakdown.png — Desglose por componente
    cost_projection_savings.png  — Ahorro acumulado anual
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ══════════════════════════════════════════════════════════════════
# MODELO DE COSTES
# ══════════════════════════════════════════════════════════════════

def cost_akasha(n_agents: int) -> dict:
    """
    Modelo de costes con Akasha.
    
    Infraestructura: escalonada — $45 base, upgrade a $90 tras 25 agentes
    (necesitas nodos más grandes o un 4to nodo).
    
    LLM: lineal — $562/agente/mes (contexto reducido de 4.5K → 1.3K tokens)
    Memoria: casi cero — $10 fijo (Nidra batch processing)
    """
    # Infra: escalonada (step function)
    if n_agents <= 25:
        infra = 45       # 3x t3.small
    elif n_agents <= 50:
        infra = 90       # 3x t3.medium o 4 nodos
    else:
        infra = 135      # 5 nodos
    
    llm_per_agent = 562      # Input reducido (1.3K tokens/interacción)
    memoria_per_agent = 1.25 # Nidra batch: ~$10/8 agentes
    
    return {
        "infra": infra,
        "llm": llm_per_agent * n_agents,
        "memoria": max(10, memoria_per_agent * n_agents),
        "total": infra + llm_per_agent * n_agents + max(10, memoria_per_agent * n_agents),
    }


def cost_traditional(n_agents: int) -> dict:
    """
    Modelo de costes sin Akasha (stack custom: Redis + PG + Qdrant + Queue).
    
    Los componentes NO escalan en bloque:
    - Redis: aguanta muchos agentes, escala tarde (~30 agentes)
    - PostgreSQL: escala por storage, no por agentes. Upgrade ~20 agentes
    - Qdrant/VectorDB: escala PRIMERO — es el bottleneck (RAM por índices)
    - Message Queue: escala tarde (~40 agentes)
    - App Server: escala pronto — 1 instancia por cada ~5 agentes
    
    LLM: lineal — $962/agente/mes (context stuffing 4.5K tokens)
    """
    # ── Vector DB (escalona primero: memoria intensiva) ──
    if n_agents <= 5:
        vector_db = 80       # Qdrant starter (2GB)
    elif n_agents <= 12:
        vector_db = 150      # Qdrant 4GB
    elif n_agents <= 25:
        vector_db = 280      # Qdrant 8GB o Pinecone Standard
    elif n_agents <= 40:
        vector_db = 450      # Cluster Qdrant 2 nodos
    else:
        vector_db = 700      # Cluster Qdrant 3+ nodos
    
    # ── Redis (escala tarde: eficiente en memoria) ──
    if n_agents <= 15:
        redis = 30           # 1 GB managed
    elif n_agents <= 35:
        redis = 60           # 2 GB managed
    else:
        redis = 100          # 4 GB o cluster
    
    # ── PostgreSQL (escala por storage, no conexiones) ──
    if n_agents <= 20:
        postgres = 40        # db.t3.small
    elif n_agents <= 40:
        postgres = 80        # db.t3.medium
    else:
        postgres = 150       # db.t3.large
    
    # ── Message Queue (escala tarde) ──
    if n_agents <= 20:
        queue = 25           # RabbitMQ small
    elif n_agents <= 40:
        queue = 50           # RabbitMQ medium
    else:
        queue = 90           # Cluster
    
    # ── App Server (escala ~linealmente, 1 per 5 agents) ──
    app_instances = max(1, (n_agents + 4) // 5)
    app_server = app_instances * 50  # $50 per instance
    
    # ── Monitoring (fijo hasta ~30 agentes) ──
    monitoring = 30 if n_agents <= 30 else 60
    
    infra_total = vector_db + redis + postgres + queue + app_server + monitoring
    
    llm_per_agent = 962  # Context stuffing (4.5K tokens/interacción)
    
    return {
        "infra": infra_total,
        "vector_db": vector_db,
        "redis": redis,
        "postgres": postgres,
        "queue": queue,
        "app_server": app_server,
        "monitoring": monitoring,
        "llm": llm_per_agent * n_agents,
        "memoria": 0,  # In-house, no extra cost
        "total": infra_total + llm_per_agent * n_agents,
    }


def cost_mem0(n_agents: int) -> dict:
    """
    Modelo de costes con Mem0 (SaaS + LLM-per-write).
    
    Infra: Mem0 managed + Qdrant embebido (menos infra propia)
    LLM agente: $962/agente (mismo context stuffing que tradicional)
    LLM memoria: $375/agente (2 LLM calls por escritura, 50K writes/mes)
    """
    # Infra reducida (Mem0 gestiona una parte)
    if n_agents <= 10:
        infra = 120
    elif n_agents <= 25:
        infra = 200
    elif n_agents <= 40:
        infra = 350
    else:
        infra = 500
    
    llm_per_agent = 962    # Context stuffing (igual que tradicional)
    mem_per_agent = 375    # 2 LLM calls × 50K writes/mes
    
    return {
        "infra": infra,
        "llm": llm_per_agent * n_agents,
        "memoria": mem_per_agent * n_agents,
        "total": infra + (llm_per_agent + mem_per_agent) * n_agents,
    }


# ══════════════════════════════════════════════════════════════════
# GRÁFICO 1: Comparativa Principal
# ══════════════════════════════════════════════════════════════════

def plot_main_comparison():
    agents = np.arange(1, 51)
    
    akasha_costs = [cost_akasha(n)["total"] for n in agents]
    trad_costs = [cost_traditional(n)["total"] for n in agents]
    mem0_costs = [cost_mem0(n)["total"] for n in agents]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#0D1117')
    ax.set_facecolor('#0D1117')
    
    # Líneas
    ax.plot(agents, mem0_costs, color='#E84393', linewidth=2.5, label='Con Mem0 (LLM + $375/ag en memoria)', zorder=3)
    ax.plot(agents, trad_costs, color='#FDCB6E', linewidth=2.5, label='Stack Tradicional (Redis+PG+Qdrant+Queue)', zorder=3)
    ax.plot(agents, akasha_costs, color='#00CEC9', linewidth=3, label='Con Akasha ($45 infra fija + LLM reducido)', zorder=4)
    
    # Área de ahorro
    ax.fill_between(agents, akasha_costs, trad_costs, alpha=0.08, color='#00CEC9')
    ax.fill_between(agents, trad_costs, mem0_costs, alpha=0.05, color='#E84393')
    
    # Anotaciones
    ax.annotate(f'Ahorro vs Tradicional\na 20 agentes: ${trad_costs[19] - akasha_costs[19]:,.0f}/mes',
                xy=(20, (akasha_costs[19] + trad_costs[19]) / 2),
                xytext=(28, akasha_costs[19] + 1500),
                fontsize=10, color='#00CEC9',
                arrowprops=dict(arrowstyle='->', color='#00CEC9', lw=1.5),
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#161B22', edgecolor='#00CEC9', alpha=0.9))
    
    ax.annotate(f'Ahorro vs Mem0\na 20 agentes: ${mem0_costs[19] - akasha_costs[19]:,.0f}/mes',
                xy=(20, (akasha_costs[19] + mem0_costs[19]) / 2),
                xytext=(30, mem0_costs[19] - 2000),
                fontsize=10, color='#E84393',
                arrowprops=dict(arrowstyle='->', color='#E84393', lw=1.5),
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#161B22', edgecolor='#E84393', alpha=0.9))
    
    # Marcas de escalonamiento infra tradicional
    for n, label in [(5, 'VectorDB\nupgrade'), (12, 'VectorDB\n+ AppServer'), (25, 'VectorDB\ncluster')]:
        ax.axvline(x=n, color='#FDCB6E', linestyle=':', alpha=0.3, linewidth=1)
        ax.text(n, trad_costs[n-1] + 800, label, fontsize=7, color='#FDCB6E', 
                ha='center', alpha=0.7, style='italic')
    
    # Marca de escalonamiento Akasha
    ax.axvline(x=25, color='#00CEC9', linestyle=':', alpha=0.3, linewidth=1)
    ax.text(26, akasha_costs[24] + 400, 'Akasha\nupgrade\n$45→$90', fontsize=7, 
            color='#00CEC9', ha='center', alpha=0.7, style='italic')
    
    # Estilo
    ax.set_xlabel('Número de Agentes', fontsize=13, color='white', labelpad=10)
    ax.set_ylabel('Coste Mensual Total ($)', fontsize=13, color='white', labelpad=10)
    ax.set_title('Proyección de Costes: Akasha vs Alternativas\n50K interacciones/agente/mes · GPT-4o (abril 2026)',
                 fontsize=16, color='white', fontweight='bold', pad=20)
    
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax.tick_params(colors='#8B949E', labelsize=10)
    ax.spines['bottom'].set_color('#30363D')
    ax.spines['left'].set_color('#30363D')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', color='#21262D', linestyle='-', linewidth=0.5)
    
    legend = ax.legend(loc='upper left', fontsize=11, framealpha=0.9,
                       facecolor='#161B22', edgecolor='#30363D', labelcolor='white')
    
    fig.tight_layout()
    fig.savefig('cost_projection_main.png', dpi=150, bbox_inches='tight',
                facecolor='#0D1117', edgecolor='none')
    print("✅ cost_projection_main.png generado")
    plt.close()


# ══════════════════════════════════════════════════════════════════
# GRÁFICO 2: Desglose por Componente (Stack Tradicional)
# ══════════════════════════════════════════════════════════════════

def plot_breakdown():
    agents = np.arange(1, 51)
    
    vector_db = [cost_traditional(n)["vector_db"] for n in agents]
    redis = [cost_traditional(n)["redis"] for n in agents]
    postgres = [cost_traditional(n)["postgres"] for n in agents]
    queue = [cost_traditional(n)["queue"] for n in agents]
    app_server = [cost_traditional(n)["app_server"] for n in agents]
    monitoring = [cost_traditional(n)["monitoring"] for n in agents]
    llm = [cost_traditional(n)["llm"] for n in agents]
    
    akasha_infra = [cost_akasha(n)["infra"] for n in agents]
    akasha_llm = [cost_akasha(n)["llm"] for n in agents]
    akasha_mem = [cost_akasha(n)["memoria"] for n in agents]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    fig.patch.set_facecolor('#0D1117')
    
    # ── Panel izquierdo: Stack Tradicional ──
    ax1.set_facecolor('#0D1117')
    
    colors_trad = ['#E84393', '#FDCB6E', '#00B894', '#6C5CE7', '#74B9FF', '#636E72']
    labels_trad = ['Vector DB', 'Redis', 'PostgreSQL', 'Queue', 'App Server', 'Monitoring']
    components = [vector_db, redis, postgres, queue, app_server, monitoring]
    
    bottom = np.zeros(len(agents), dtype=float)
    for comp, color, label in zip(components, colors_trad, labels_trad):
        ax1.bar(agents, comp, bottom=bottom, color=color, alpha=0.85, label=label, width=0.8)
        bottom = bottom + np.array(comp, dtype=float)
    
    # LLM encima
    ax1.bar(agents, llm, bottom=bottom, color='#FF6B6B', alpha=0.6, label='LLM Tokens', width=0.8)
    
    ax1.set_xlabel('Agentes', fontsize=12, color='white')
    ax1.set_ylabel('Coste Mensual ($)', fontsize=12, color='white')
    ax1.set_title('Stack Tradicional\n(Redis + PG + Qdrant + Queue + App)', fontsize=14, color='#FDCB6E', fontweight='bold')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax1.tick_params(colors='#8B949E')
    ax1.spines['bottom'].set_color('#30363D')
    ax1.spines['left'].set_color('#30363D')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.legend(fontsize=9, framealpha=0.9, facecolor='#161B22', edgecolor='#30363D', 
               labelcolor='white', loc='upper left')
    
    # Anotaciones de escalonamiento
    for n in [5, 12, 25, 40]:
        ax1.axvline(x=n, color='#FDCB6E', linestyle='--', alpha=0.3, linewidth=1)
    
    # ── Panel derecho: Akasha ──
    ax2.set_facecolor('#0D1117')
    
    ax2.bar(agents, akasha_infra, color='#00CEC9', alpha=0.9, label='Akasha Infra', width=0.8)
    bottom_ak = np.array(akasha_infra, dtype=float)
    ax2.bar(agents, akasha_mem, bottom=bottom_ak, color='#6C5CE7', alpha=0.7, label='Nidra (LLM batch)', width=0.8)
    bottom_ak = bottom_ak + np.array(akasha_mem, dtype=float)
    ax2.bar(agents, akasha_llm, bottom=bottom_ak, color='#00CEC9', alpha=0.4, label='LLM Tokens (reducido)', width=0.8)
    
    ax2.set_xlabel('Agentes', fontsize=12, color='white')
    ax2.set_title('Con Akasha\n(Infra fija $45 + LLM reducido 42%)', fontsize=14, color='#00CEC9', fontweight='bold')
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax2.tick_params(colors='#8B949E')
    ax2.spines['bottom'].set_color('#30363D')
    ax2.spines['left'].set_color('#30363D')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.legend(fontsize=9, framealpha=0.9, facecolor='#161B22', edgecolor='#30363D',
               labelcolor='white', loc='upper left')
    
    # Misma escala Y para comparación visual
    max_y = max(max(cost_traditional(n)["total"] for n in agents),
                max(cost_akasha(n)["total"] for n in agents))
    ax1.set_ylim(0, max_y * 1.05)
    ax2.set_ylim(0, max_y * 1.05)
    
    fig.suptitle('Desglose de Costes por Componente', fontsize=18, color='white', 
                 fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig('cost_projection_breakdown.png', dpi=150, bbox_inches='tight',
                facecolor='#0D1117', edgecolor='none')
    print("✅ cost_projection_breakdown.png generado")
    plt.close()


# ══════════════════════════════════════════════════════════════════
# GRÁFICO 3: Ahorro Acumulado Anual
# ══════════════════════════════════════════════════════════════════

def plot_savings():
    agents = np.arange(1, 51)
    
    savings_vs_trad = [(cost_traditional(n)["total"] - cost_akasha(n)["total"]) * 12 for n in agents]
    savings_vs_mem0 = [(cost_mem0(n)["total"] - cost_akasha(n)["total"]) * 12 for n in agents]
    
    # Desglose del ahorro
    savings_llm = [(cost_traditional(n)["llm"] - cost_akasha(n)["llm"]) * 12 for n in agents]
    savings_mem = [(cost_mem0(n)["memoria"] - cost_akasha(n)["memoria"]) * 12 for n in agents]
    savings_infra = [(cost_traditional(n)["infra"] - cost_akasha(n)["infra"]) * 12 for n in agents]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    fig.patch.set_facecolor('#0D1117')
    
    # ── Panel superior: Ahorro total ──
    ax1.set_facecolor('#0D1117')
    
    ax1.fill_between(agents, 0, savings_vs_mem0, alpha=0.15, color='#E84393')
    ax1.fill_between(agents, 0, savings_vs_trad, alpha=0.15, color='#00CEC9')
    ax1.plot(agents, savings_vs_mem0, color='#E84393', linewidth=2.5, label='Ahorro anual vs Mem0')
    ax1.plot(agents, savings_vs_trad, color='#00CEC9', linewidth=2.5, label='Ahorro anual vs Stack Tradicional')
    
    # Marcadores clave
    for n in [5, 10, 20, 50]:
        idx = n - 1
        ax1.plot(n, savings_vs_trad[idx], 'o', color='#00CEC9', markersize=8, zorder=5)
        ax1.annotate(f'${savings_vs_trad[idx]:,.0f}/año',
                    xy=(n, savings_vs_trad[idx]),
                    xytext=(n + 1.5, savings_vs_trad[idx] + savings_vs_trad[-1] * 0.04),
                    fontsize=9, color='#00CEC9',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#161B22', edgecolor='#00CEC9', alpha=0.8))
        
        ax1.plot(n, savings_vs_mem0[idx], 'o', color='#E84393', markersize=8, zorder=5)
        ax1.annotate(f'${savings_vs_mem0[idx]:,.0f}/año',
                    xy=(n, savings_vs_mem0[idx]),
                    xytext=(n + 1.5, savings_vs_mem0[idx] + savings_vs_trad[-1] * 0.04),
                    fontsize=9, color='#E84393',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#161B22', edgecolor='#E84393', alpha=0.8))
    
    ax1.set_xlabel('Número de Agentes', fontsize=12, color='white')
    ax1.set_ylabel('Ahorro Anual ($)', fontsize=12, color='white')
    ax1.set_title('Ahorro Anual Acumulado con Akasha', fontsize=16, color='white', fontweight='bold', pad=15)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax1.tick_params(colors='#8B949E')
    ax1.spines['bottom'].set_color('#30363D')
    ax1.spines['left'].set_color('#30363D')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(axis='y', color='#21262D', linestyle='-', linewidth=0.5)
    ax1.legend(fontsize=11, framealpha=0.9, facecolor='#161B22', edgecolor='#30363D', labelcolor='white')
    
    # ── Panel inferior: Composición del ahorro ──
    ax2.set_facecolor('#0D1117')
    
    ax2.bar(agents, savings_infra, color='#74B9FF', alpha=0.8, label='Ahorro en Infraestructura', width=0.8)
    bottom = np.array(savings_infra, dtype=float)
    ax2.bar(agents, savings_llm, bottom=bottom, color='#00CEC9', alpha=0.8, label='Ahorro en Tokens LLM', width=0.8)
    bottom = bottom + np.array(savings_llm, dtype=float)
    ax2.bar(agents, savings_mem, bottom=bottom, color='#E84393', alpha=0.8, label='Ahorro vs Mem0 (escrituras)', width=0.8)
    
    # Línea de % que es LLM+Memoria
    pct_llm_mem = [(savings_llm[i] + savings_mem[i]) / max(1, savings_llm[i] + savings_mem[i] + savings_infra[i]) * 100 
                   for i in range(len(agents))]
    ax2_twin = ax2.twinx()
    ax2_twin.plot(agents, pct_llm_mem, color='#FDCB6E', linewidth=2, linestyle='--', label='% ahorro de LLM+Memoria')
    ax2_twin.set_ylabel('% del ahorro total', fontsize=11, color='#FDCB6E')
    ax2_twin.tick_params(colors='#FDCB6E')
    ax2_twin.set_ylim(0, 100)
    ax2_twin.spines['right'].set_color('#FDCB6E')
    ax2_twin.spines['top'].set_visible(False)
    
    ax2.set_xlabel('Número de Agentes', fontsize=12, color='white')
    ax2.set_ylabel('Ahorro Anual ($)', fontsize=12, color='white')
    ax2.set_title('Composición del Ahorro: ¿De dónde viene?', fontsize=14, color='white', fontweight='bold', pad=15)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax2.tick_params(colors='#8B949E')
    ax2.spines['bottom'].set_color('#30363D')
    ax2.spines['left'].set_color('#30363D')
    ax2.spines['top'].set_visible(False)
    ax2.legend(fontsize=10, framealpha=0.9, facecolor='#161B22', edgecolor='#30363D', 
               labelcolor='white', loc='upper left')
    ax2_twin.legend(fontsize=10, framealpha=0.9, facecolor='#161B22', edgecolor='#FDCB6E',
                    labelcolor='#FDCB6E', loc='center left', bbox_to_anchor=(0, 0.7))
    
    fig.tight_layout()
    fig.savefig('cost_projection_savings.png', dpi=150, bbox_inches='tight',
                facecolor='#0D1117', edgecolor='none')
    print("✅ cost_projection_savings.png generado")
    plt.close()


# ══════════════════════════════════════════════════════════════════
# GRÁFICO 4: Coste por Agente (muestra la amortización)
# ══════════════════════════════════════════════════════════════════

def plot_per_agent():
    agents = np.arange(1, 51)
    
    akasha_per = [cost_akasha(n)["total"] / n for n in agents]
    trad_per = [cost_traditional(n)["total"] / n for n in agents]
    mem0_per = [cost_mem0(n)["total"] / n for n in agents]
    
    # Solo infra por agente (sin LLM)
    akasha_infra_per = [cost_akasha(n)["infra"] / n for n in agents]
    trad_infra_per = [cost_traditional(n)["infra"] / n for n in agents]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor('#0D1117')
    
    # ── Panel izquierdo: Coste total por agente ──
    ax1.set_facecolor('#0D1117')
    ax1.plot(agents, mem0_per, color='#E84393', linewidth=2.5, label='Mem0')
    ax1.plot(agents, trad_per, color='#FDCB6E', linewidth=2.5, label='Stack Tradicional')
    ax1.plot(agents, akasha_per, color='#00CEC9', linewidth=3, label='Akasha')
    
    # Líneas de convergencia
    ax1.axhline(y=962, color='#FDCB6E', linestyle=':', alpha=0.3)
    ax1.text(45, 962 + 30, 'Suelo LLM: $962/ag', fontsize=8, color='#FDCB6E', alpha=0.5)
    ax1.axhline(y=562, color='#00CEC9', linestyle=':', alpha=0.3)
    ax1.text(45, 562 + 30, 'Suelo LLM: $562/ag', fontsize=8, color='#00CEC9', alpha=0.5)
    
    ax1.set_xlabel('Número de Agentes', fontsize=12, color='white')
    ax1.set_ylabel('Coste Mensual por Agente ($)', fontsize=12, color='white')
    ax1.set_title('Coste Total por Agente\n(incluye infra + LLM)', fontsize=14, color='white', fontweight='bold')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax1.tick_params(colors='#8B949E')
    ax1.spines['bottom'].set_color('#30363D')
    ax1.spines['left'].set_color('#30363D')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(axis='y', color='#21262D', linewidth=0.5)
    ax1.legend(fontsize=11, framealpha=0.9, facecolor='#161B22', edgecolor='#30363D', labelcolor='white')
    
    # ── Panel derecho: Solo infra por agente ──
    ax2.set_facecolor('#0D1117')
    ax2.plot(agents, trad_infra_per, color='#FDCB6E', linewidth=2.5, label='Stack Tradicional (infra)')
    ax2.plot(agents, akasha_infra_per, color='#00CEC9', linewidth=3, label='Akasha (infra)')
    
    ax2.fill_between(agents, akasha_infra_per, trad_infra_per, alpha=0.1, color='#00CEC9')
    
    # Zona de convergencia
    ax2.axhspan(0, 15, alpha=0.05, color='#FDCB6E')
    ax2.text(40, 8, 'Zona de convergencia', fontsize=9, color='#FDCB6E', alpha=0.5, style='italic')
    
    ax2.set_xlabel('Número de Agentes', fontsize=12, color='white')
    ax2.set_ylabel('Coste Infra por Agente ($)', fontsize=12, color='white')
    ax2.set_title('Solo Infraestructura por Agente\n(sin LLM — muestra amortización)', fontsize=14, color='white', fontweight='bold')
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.0f}'))
    ax2.tick_params(colors='#8B949E')
    ax2.spines['bottom'].set_color('#30363D')
    ax2.spines['left'].set_color('#30363D')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.grid(axis='y', color='#21262D', linewidth=0.5)
    ax2.legend(fontsize=11, framealpha=0.9, facecolor='#161B22', edgecolor='#30363D', labelcolor='white')
    
    fig.tight_layout()
    fig.savefig('cost_projection_per_agent.png', dpi=150, bbox_inches='tight',
                facecolor='#0D1117', edgecolor='none')
    print("✅ cost_projection_per_agent.png generado")
    plt.close()


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("📊 Generando gráficos de proyección de costes...\n")
    
    plot_main_comparison()
    plot_breakdown()
    plot_savings()
    plot_per_agent()
    
    # Print table summary
    print("\n📋 Tabla resumen:\n")
    print(f"{'Agentes':>8} {'Akasha':>12} {'Tradicional':>14} {'Mem0':>12} {'Ahorro/Trad':>14} {'Ahorro/Mem0':>14}")
    print("-" * 78)
    for n in [1, 3, 5, 8, 10, 15, 20, 30, 50]:
        a = cost_akasha(n)["total"]
        t = cost_traditional(n)["total"]
        m = cost_mem0(n)["total"]
        print(f"{n:>8} ${a:>10,.0f} ${t:>12,.0f} ${m:>10,.0f} ${t-a:>12,.0f} ${m-a:>12,.0f}")
    
    print("\n✅ Todos los gráficos generados.")
