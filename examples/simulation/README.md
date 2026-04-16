# 🚀 Simulación Multi-Agente para Akasha

3 agentes autónomos que trabajan en equipo a través de Akasha, generando actividad real en las 4 capas de memoria + pheromones. Ideal para demos, desarrollo de dashboards, y pruebas de carga.

---

## Requisitos

```bash
pip install requests
```

Akasha debe estar corriendo (el cluster de `akasha-pro/docker-compose.yml`).

---

## Lanzar

```bash
# Desde la carpeta simulacion/
cd /Users/ikairos/lab/akasha/simulacion

# Opción 1: Los 3 agentes en paralelo (recomendado)
python3 run_simulation.py

# Opción 2: Contra un server remoto
python3 run_simulation.py https://mi-server:7777

# Opción 3: Un agente individual (para debug)
python3 agent_scout.py
python3 agent_analyst.py
python3 agent_coordinator.py
```

## Parar

```
Ctrl+C
```

Los 3 procesos se detienen limpiamente.

---

## Los Agentes

| Agente | Script | Ciclo | Qué hace |
|--------|--------|-------|----------|
| 🔍 **Scout** | `agent_scout.py` | 5-15s | Descubre incidentes y oportunidades, escribe en `episodic/`, deposita pheromones |
| 🧠 **Analyst** | `agent_analyst.py` | 10-25s | Sensa pheromones, lee episodic, genera insights en `semantic/`, crea runbooks en `procedural/` |
| 📋 **Coordinator** | `agent_coordinator.py` | 15-35s | Lee todo, genera status reports en `working/` (TTL 2min), refuerza pheromones importantes |

## Flujo de datos

```
Scout ──escribe──→ episodic/{dominio}/{id}     ──leído por──→ Analyst
Scout ──deposita─→ pheromones (discovery/warning) ──sensado por→ Analyst

Analyst ─escribe→ semantic/{dominio}/insights/  ──leído por──→ Coordinator
Analyst ─escribe→ procedural/runbooks/{tipo}    ──leído por──→ Coordinator

Coordinator ───→ working/coordinator/status/    (TTL 2 min, snapshots)
Coordinator ───→ semantic/system/latest-status  (estado actual)
Coordinator ───→ pheromones (reinforcement)     ──sensado por→ todos
```

## Paths creados en Akasha

| Path | Capa | TTL | Contenido |
|------|------|-----|-----------|
| `memory/episodic/{dominio}/{id}` | Episodic | 1h | Incidentes y oportunidades descubiertas |
| `memory/semantic/{dominio}/scan-stats` | Semantic | ∞ | Contadores de escaneos por dominio |
| `memory/semantic/{dominio}/insights/{id}` | Semantic | ∞ | Análisis e insights generados |
| `memory/semantic/system/latest-status` | Semantic | ∞ | Último estado del sistema |
| `memory/procedural/runbooks/{tipo}` | Procedural | ∞ | Procedimientos aprendidos |
| `memory/working/coordinator/status/{id}` | Working | 2min | Snapshots de estado (efímeros) |

## Dominios simulados

`infrastructure` · `security` · `performance` · `customer-feedback` · `market-intel`
