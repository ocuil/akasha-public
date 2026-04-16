# Guía de Integración de Agentes con Akasha

## Para el integrador que quiere sacar el máximo provecho

---

## ¿Qué es Akasha? (En 30 segundos)

Akasha es la **capa de memoria persistente** entre tus agentes. No es un framework, no es un orquestador, no reemplaza a LangGraph ni CrewAI. Es la infraestructura que les da a tus agentes algo que hoy no tienen: **memoria compartida que persiste entre sesiones y se coordina entre agentes**.

```
Sin Akasha:                          Con Akasha:

Agente A ──→ LLM                     Agente A ──→ LLM
Agente B ──→ LLM                              ↕
Agente C ──→ LLM                     ┌─── AKASHA ───┐
                                     │  Memoria      │
(Cada uno olvida todo al            │  compartida   │
 cerrar sesión. Ninguno              │  persistente  │
 sabe qué hace el otro.)            └───────────────┘
                                              ↕
                                     Agente B ──→ LLM
                                              ↕
                                     Agente C ──→ LLM
```

**Akasha NO:**
- ❌ Ejecuta tus agentes
- ❌ Gestiona el LLM
- ❌ Orquesta el flujo de trabajo
- ❌ Decide qué agente actúa cuándo

**Akasha SÍ:**
- ✅ Almacena cualquier dato vía REST/gRPC/MCP en <1ms
- ✅ Organiza la memoria en 4 capas cognitivas
- ✅ Permite que los agentes dejen "señales" (pheromones) para otros
- ✅ Consolida conocimiento automáticamente (Nidra)
- ✅ Replica los datos en 3 nodos para alta disponibilidad
- ✅ Provee un dashboard para visualizar todo en tiempo real

---

## El Contrato: Qué Hace Akasha vs Qué Debe Hacer Tu Agente

Este es el punto más importante del documento. La magia ocurre cuando **el agente está programado para interactuar con Akasha de forma inteligente**.

```
┌────────────────────────────────────┬────────────────────────────────────┐
│         AKASHA SE ENCARGA DE        │       TU AGENTE SE ENCARGA DE      │
├────────────────────────────────────┼────────────────────────────────────┤
│                                    │                                    │
│  • Persistir datos con baja        │  • LEER antes de actuar            │
│    latencia (<1ms)                 │    "¿Qué sé ya de este contexto?" │
│                                    │                                    │
│  • Organizar en capas de memoria   │  • ESCRIBIR después de actuar      │
│    (working, episodic, semantic,   │    "¿Qué aprendí que otros deben  │
│    procedural)                     │    saber?"                         │
│                                    │                                    │
│  • Replicar datos entre nodos      │  • SEÑALIZAR cuando hay algo       │
│  • Resolver conflictos (CRDT)      │    importante (depositar           │
│  • Expirar datos con TTL           │    pheromones)                     │
│  • Consolidar con Nidra            │                                    │
│  • Audit trail inmutable           │  • SENSAR señales de otros         │
│                                    │    agentes (leer pheromones)       │
│  • Dashboard de observabilidad     │                                    │
│  • Cifrado en reposo               │  • Elegir la CAPA correcta        │
│  • Autenticación y API keys        │    para cada dato                  │
│                                    │                                    │
└────────────────────────────────────┴────────────────────────────────────┘
```

---

## Las 5 Reglas del Agente Akasha-Ready

### Regla 1: LEE ANTES DE ACTUAR

El agente debe **consultar la memoria compartida antes de tomar cualquier decisión**. Esto es lo que transforma un agente amnésico en uno contextual.

```python
# ❌ MAL — El agente actúa sin contexto
def handle_ticket(ticket):
    response = llm.chat(f"Resuelve este ticket: {ticket.description}")
    return response

# ✅ BIEN — El agente consulta primero
def handle_ticket(ticket):
    # 1. ¿Qué sé de este cliente?
    client_profile = akasha.get(f"memory/semantic/clients/{ticket.client_id}/profile")
    
    # 2. ¿Ha tenido tickets similares?
    past_tickets = akasha.query(f"memory/episodic/support/{ticket.client_id}/*")
    
    # 3. ¿Hay alguna señal de alerta sobre este cliente?
    pheromones = akasha.sense_pheromones()
    client_warnings = [p for p in pheromones if ticket.client_id in p.trail]
    
    # 4. ¿Existe un procedimiento para este tipo de problema?
    runbook = akasha.get(f"memory/procedural/runbooks/{ticket.category}")
    
    # 5. Ahora sí — actuar con contexto completo
    context = build_context(client_profile, past_tickets, client_warnings, runbook)
    response = llm.chat(f"""
        Contexto del cliente: {context}
        Ticket actual: {ticket.description}
        Resuelve con el contexto disponible.
    """)
    return response
```

**¿Qué poner en el prompt del agente?**

```
Eres un agente de soporte L1. Antes de responder a cualquier ticket:
1. Consulta el perfil del cliente en Akasha (semantic/clients/{id}/profile)
2. Busca tickets anteriores similares (episodic/support/{id}/*)
3. Verifica si hay alertas activas (pheromones con signal WARNING)
4. Lee el runbook correspondiente (procedural/runbooks/{categoría})

Si encuentras una resolución anterior para un problema similar, 
úsala como punto de partida. No investigues desde cero.
```

---

### Regla 2: ESCRIBE DESPUÉS DE ACTUAR

Cada acción del agente que produzca conocimiento útil debe **escribirse en Akasha** para que otros agentes (o el mismo agente en el futuro) puedan beneficiarse.

```python
# Después de resolver un ticket
def save_resolution(ticket, resolution):
    # Episódico — lo que pasó (tiene TTL, se consolidará)
    akasha.put(f"memory/episodic/support/{ticket.client_id}/{ticket.id}", {
        "description": ticket.description,
        "category": ticket.category,
        "resolution": resolution.text,
        "time_to_resolve_min": resolution.duration,
        "root_cause": resolution.root_cause,
        "resolved_by": "support-l1",
        "timestamp": now(),
    }, ttl_seconds=86400 * 30)  # 30 días

    # Semántico — si aprendí algo permanente sobre el cliente
    if resolution.learned_preference:
        profile = akasha.get(f"memory/semantic/clients/{ticket.client_id}/profile") or {}
        profile["known_issues"] = profile.get("known_issues", []) + [resolution.root_cause]
        akasha.put(f"memory/semantic/clients/{ticket.client_id}/profile", profile)
```

**Pregunta clave para decidir dónde escribir:**

| Pregunta | Capa | Ejemplo |
|----------|------|---------|
| ¿Es temporal, de esta tarea? | **Working** (TTL: segundos/minutos) | Estado intermedio de un análisis |
| ¿Es algo que pasó? Un evento | **Episodic** (TTL: horas/días) | "Cliente X abrió ticket Y" |
| ¿Es un hecho permanente? | **Semantic** (sin TTL) | "Cliente X prefiere email formal" |
| ¿Es un procedimiento aprendido? | **Procedural** (sin TTL) | "Para resolver timeout, hacer A→B→C" |

---

### Regla 3: SEÑALIZA LO IMPORTANTE

Los pheromones son el sistema nervioso del ecosistema de agentes. Cuando un agente detecta algo relevante para otros, **deposita una señal**.

```python
# Agente de Triage detecta un cliente enterprise en riesgo
akasha.deposit_pheromone(
    trail=f"alerts/clients/{client_id}",
    signal_type="warning",
    emitter="triage-agent",
    intensity=0.9,            # 0.0 a 1.0 — cuán importante es
    half_life_secs=3600,      # La señal dura ~1 hora
    payload={
        "reason": "P1 ticket + renewal in 63 days + declining sentiment",
        "ticket_id": "TK-4521",
        "arr": 180000,
        "recommended_action": "Escalate to human CSM"
    }
)
```

**Cuándo depositar pheromones:**

| Situación | signal_type | intensity | half_life |
|-----------|-------------|-----------|-----------|
| Descubrí información útil | `discovery` | 0.5-0.7 | 30 min |
| Completé algo exitosamente | `success` | 0.6-0.8 | 1 hora |
| Algo falló, evitar este camino | `failure` | 0.7-0.9 | 2 horas |
| ⚠️ Hay un riesgo o urgencia | `warning` | 0.8-1.0 | 1-4 horas |
| Confirmo la señal de otro agente | `reinforcement` | 0.5-0.7 | 1 hora |

---

### Regla 4: SENSA ANTES DE PLANIFICAR

Si tu agente toma decisiones o planifica acciones, debe **sensar los pheromones activos primero**.

```python
def plan_next_action(agent):
    # ¿Hay señales que deba considerar?
    trails = akasha.sense_pheromones()
    
    warnings = [t for t in trails if t.signal_type == "warning" and t.current_intensity > 0.3]
    discoveries = [t for t in trails if t.signal_type == "discovery"]
    failures = [t for t in trails if t.signal_type == "failure"]
    
    if warnings:
        # Hay algo urgente — ajustar prioridades
        return prioritize_urgent(warnings)
    
    if failures:
        # Alguien ya falló en este camino — evitarlo
        return avoid_failed_paths(failures)
    
    if discoveries:
        # Hay información nueva disponible — incorporarla
        return incorporate_discoveries(discoveries)
    
    return default_plan()
```

**En el prompt del agente:**

```
Antes de planificar tu próxima acción, consulta las señales activas 
en Akasha (pheromones). Si hay señales de tipo WARNING con intensidad 
> 0.5, ajusta tu plan para abordar esas urgencias primero. Si hay 
señales FAILURE, evita repetir las acciones que fallaron.
```

---

### Regla 5: USA PATHS CONSISTENTES

La potencia de Akasha depende de que los agentes **sean consistentes en cómo nombran sus datos**. Un path es como una dirección postal — si cada agente usa formatos diferentes, nadie encontrará nada.

**Convención recomendada:**

```
memory/{capa}/{dominio}/{entidad}/{detalle}

Ejemplos:
  memory/working/analysis/report-42/progress     ← tarea en curso
  memory/episodic/support/acme-corp/TK-4521      ← evento específico
  memory/semantic/clients/acme-corp/profile       ← conocimiento permanente
  memory/procedural/runbooks/api-timeout          ← procedimiento aprendido
  _pheromones/alerts/clients/acme-corp            ← señal de coordinación
```

**Anti-patrones a evitar:**

```
❌ memory/datos/cosas/12345          ← Paths genéricos sin significado
❌ a/b/c                             ← Demasiado corto, no descriptivo
❌ MEMORY/SEMANTIC/Clients/AcmeCorp  ← Inconsistencia en mayúsculas
❌ memory/semantic/todo               ← Un solo record con "todo"
```

---

## Patrones de Prompt para Agentes Akasha-Ready

### Patrón 1 — System Prompt Base

```
=== INSTRUCCIONES DE MEMORIA ===

Tienes acceso a Akasha, un sistema de memoria compartida. DEBES usarlo así:

ANTES de cada acción:
- Lee datos relevantes de Akasha usando los paths de memoria
- Verifica si hay señales (pheromones) que afecten tu decisión
- Busca procedimientos conocidos para este tipo de tarea

DESPUÉS de cada acción:
- Escribe lo que aprendiste o hiciste en la capa apropiada
- Si descubriste algo importante para otros agentes, deposita un pheromone
- Si completaste una tarea, actualiza tu working memory

CAPAS DE MEMORIA:
- working/   → Estado temporal de tu tarea actual (TTL: 60s)
- episodic/  → Lo que pasó: eventos, interacciones (TTL: 1-24h)
- semantic/  → Hechos permanentes: perfiles, preferencias (sin TTL)
- procedural/→ Procedimientos aprendidos: "para X, hacer Y" (sin TTL)

NUNCA actúes sin consultar primero la memoria disponible.
SIEMPRE registra el resultado de tus acciones.
```

### Patrón 2 — Agente con MCP (Claude, Gemini, Cursor)

Si el agente usa Akasha como MCP tool, las instrucciones son más naturales:

```
Tienes acceso a la herramienta "akasha" para persistir y consultar 
memoria compartida con otros agentes.

Cuando el usuario te pide algo:
1. Usa akasha_read para ver si hay contexto previo relevante
2. Realiza tu tarea normalmente
3. Usa akasha_write para guardar lo que aprendiste
4. Si el resultado es relevante para otros agentes, usa akasha_pheromone

Paths de memoria que debes usar:
- memory/semantic/projects/{nombre}/ — conocimiento del proyecto
- memory/episodic/conversations/{fecha}/ — lo que discutimos
- memory/procedural/how-to/{tarea}/ — procedimientos que funcionan
```

### Patrón 3 — Agente Programático (Python/Node)

```python
class AkashaAwareAgent:
    """Base para cualquier agente que use Akasha."""
    
    def __init__(self, agent_name: str, akasha_url: str, api_key: str):
        self.name = agent_name
        self.client = AkashaClient(akasha_url, api_key)
    
    async def act(self, task):
        # Fase 1: Recuerda
        context = await self.recall(task)
        
        # Fase 2: Piensa (tu lógica + LLM)
        result = await self.think(task, context)
        
        # Fase 3: Memoriza
        await self.memorize(task, result)
        
        # Fase 4: Señaliza (si aplica)
        await self.signal(task, result)
        
        return result
    
    async def recall(self, task):
        """Lee todo lo relevante de Akasha antes de actuar."""
        context = {}
        
        # Conocimiento semántico del dominio
        domain_knowledge = await self.client.query(
            f"memory/semantic/{task.domain}/**"
        )
        context["knowledge"] = domain_knowledge
        
        # Episodios anteriores similares
        history = await self.client.query(
            f"memory/episodic/{task.domain}/{task.entity}/*"
        )
        context["history"] = history
        
        # Procedimientos conocidos
        procedure = await self.client.get(
            f"memory/procedural/{task.type}"
        )
        context["procedure"] = procedure
        
        # Señales activas
        pheromones = await self.client.sense_pheromones()
        context["signals"] = [
            p for p in pheromones 
            if p.current_intensity > 0.3
        ]
        
        return context
    
    async def memorize(self, task, result):
        """Escribe lo aprendido en la capa correcta."""
        # Siempre escribir el episodio
        await self.client.put(
            f"memory/episodic/{task.domain}/{task.entity}/{task.id}",
            {
                "agent": self.name,
                "action": task.type,
                "input": task.summary,
                "result": result.summary,
                "success": result.success,
                "timestamp": datetime.utcnow().isoformat(),
            },
            ttl_seconds=86400  # 24 horas, Nidra consolidará
        )
        
        # Si aprendí algo permanente → semántico
        if result.learned_facts:
            for fact in result.learned_facts:
                await self.client.put(
                    f"memory/semantic/{fact.domain}/{fact.key}",
                    fact.value
                )
    
    async def signal(self, task, result):
        """Deposita pheromone si el resultado es relevante para otros."""
        if result.is_urgent:
            await self.client.deposit_pheromone(
                trail=f"alerts/{task.domain}/{task.entity}",
                signal_type="warning",
                emitter=self.name,
                intensity=0.9,
                half_life_secs=3600,
                payload={"reason": result.urgency_reason}
            )
        elif result.success and result.is_novel:
            await self.client.deposit_pheromone(
                trail=f"discoveries/{task.domain}",
                signal_type="discovery",
                emitter=self.name,
                intensity=0.6,
                half_life_secs=1800,
                payload={"finding": result.summary}
            )
```

---

## Checklist de Integración

### Para el desarrollador que conecta su primer agente:

```
PRE-REQUISITOS
  □ Akasha desplegado y accesible (docker-compose up)
  □ API key generada para este agente (Dashboard > Admin > API Keys)
  □ SDK instalado (pip install akasha-sdk o npm install @akasha/client)

CONFIGURACIÓN DEL AGENTE
  □ El agente lee de Akasha ANTES de decidir (Regla 1)
  □ El agente escribe en Akasha DESPUÉS de actuar (Regla 2)
  □ Los paths siguen la convención memory/{capa}/{dominio}/{entidad}/{detalle}
  □ Los TTL son apropiados para cada capa
  □ El system prompt incluye instrucciones de memoria

COORDINACIÓN MULTI-AGENTE
  □ El agente deposita pheromones cuando detecta algo relevante
  □ El agente sensa pheromones antes de planificar
  □ Los signal_type son consistentes (discovery, success, failure, warning)
  □ La intensidad refleja la importancia real (0.0 a 1.0)

VALIDACIÓN
  □ Abrir Dashboard → Explorer → verificar que los paths se crean
  □ Simular una secuencia: Agente A escribe → Agente B lee → correcto
  □ Verificar que Nidra consolida (Dashboard > Cluster > Nidra Status)
  □ Testear desconexión: el agente funciona si Akasha no responde?
```

---

## Ejemplo Completo: Dos Agentes Coordinados

### Escenario: Agente de Investigación + Agente de Escritura

```python
# === AGENTE 1: Investigador ===

async def research_agent(topic: str):
    """Investiga un tema y comparte hallazgos via Akasha."""
    
    # 1. ¿Ya tengo investigaciones previas sobre esto?
    existing = await akasha.query(f"memory/semantic/research/{topic}/**")
    if existing:
        print(f"Ya tengo {len(existing)} datos previos sobre {topic}")
    
    # 2. Investigar (simulado — en realidad llamaría a un LLM + herramientas)
    findings = await do_research(topic, existing_knowledge=existing)
    
    # 3. Guardar hallazgos en Akasha
    for finding in findings:
        await akasha.put(
            f"memory/episodic/research/{topic}/{finding.id}",
            {
                "title": finding.title,
                "content": finding.content,
                "sources": finding.sources,
                "confidence": finding.confidence,
                "researcher": "research-agent",
                "timestamp": datetime.utcnow().isoformat(),
            },
            ttl_seconds=86400 * 7  # 7 días
        )
    
    # 4. Señalizar que hay material disponible
    await akasha.deposit_pheromone(
        trail=f"content/research/{topic}",
        signal_type="discovery",
        emitter="research-agent",
        intensity=0.8,
        half_life_secs=7200,  # 2 horas
        payload={
            "topic": topic,
            "findings_count": len(findings),
            "ready_for_writing": True,
        }
    )
    
    print(f"✅ Investigación sobre '{topic}' completada. "
          f"{len(findings)} hallazgos guardados en Akasha.")


# === AGENTE 2: Escritor ===

async def writer_agent():
    """Detecta investigaciones listas y genera contenido."""
    
    # 1. ¿Hay señales de investigaciones completadas?
    trails = await akasha.sense_pheromones()
    research_signals = [
        t for t in trails 
        if t.signal_type == "discovery" 
        and "research/" in t.trail
        and t.current_intensity > 0.3
    ]
    
    if not research_signals:
        print("No hay investigaciones listas. Esperando...")
        return
    
    for signal in research_signals:
        topic = signal.payload["topic"]
        
        # 2. Leer toda la investigación disponible
        research_data = await akasha.query(
            f"memory/episodic/research/{topic}/*"
        )
        
        # 3. ¿Hay guías de estilo en memoria procedural?
        style_guide = await akasha.get(
            "memory/procedural/writing/style-guide"
        )
        
        # 4. Generar el artículo
        article = await generate_article(
            topic=topic,
            research=research_data,
            style=style_guide,
        )
        
        # 5. Guardar el artículo
        await akasha.put(
            f"memory/semantic/articles/{topic}",
            {
                "title": article.title,
                "content": article.content,
                "based_on": [r.path for r in research_data],
                "author": "writer-agent",
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        
        # 6. Señalizar que el artículo está listo
        await akasha.deposit_pheromone(
            trail=f"content/articles/{topic}",
            signal_type="success",
            emitter="writer-agent",
            intensity=0.7,
            half_life_secs=3600,
            payload={"article_path": f"memory/semantic/articles/{topic}"}
        )
        
        print(f"✅ Artículo sobre '{topic}' generado y guardado.")
```

**Lo que pasa aquí:**
1. El Investigador no conoce al Escritor. No se comunican directamente.
2. El Investigador deposita una feromona "discovery" con `ready_for_writing: True`
3. El Escritor sensa esa feromona y sabe que hay material disponible
4. El Escritor lee la investigación de Akasha, no del Investigador
5. **Coordinación sin acoplamiento** — pueden correr en procesos, máquinas o incluso frameworks diferentes

---

## Errores Comunes y Cómo Evitarlos

| Error | Por qué falla | Solución |
|-------|--------------|----------|
| Agente que solo escribe, nunca lee | Akasha se llena de datos que nadie usa. No hay valor. | Cada escritura debe estar motivada por una lectura futura. Pregúntate: "¿Quién leerá esto?" |
| Agente que lee todo en cada ciclo | `query("**")` es caro y devuelve ruido | Usa paths específicos. `query("memory/semantic/clients/acme/*")`, no `query("**/acme/**")` |
| Todo en memoria semántica | No hay diferencia entre "lo que pasó hoy" y "lo que siempre es verdad" | Episódico para eventos, Semántico para hechos. Nidra promoverá automáticamente lo importante |
| Pheromones con intensity=1.0 siempre | Si todo es urgente, nada lo es | Usa intensidad proporcional. 0.3-0.5 para info, 0.6-0.8 para importante, 0.9+ solo para emergencias |
| No manejar el caso "Akasha no responde" | El agente se cuelga si Akasha está momentáneamente caído | Siempre usar try/catch. El agente debe funcionar (con menos contexto) sin Akasha |
| Paths inconsistentes entre agentes | Agente A escribe en `clients/acme`, Agente B busca en `customer/acme-corp` | Documentar y acordar el schema de paths ANTES de implementar |

---

## Resumen: El Agente Ideal

```
┌──────────────────────────────────────────────────────────────────────┐
│                    EL AGENTE AKASHA-READY                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. RECUERDA   → Lee contexto de Akasha antes de actuar             │
│  2. ACTÚA      → Ejecuta su lógica con contexto completo            │
│  3. APRENDE    → Escribe lo que descubrió en la capa correcta       │
│  4. SEÑALIZA   → Deposita pheromones si otros deben saber           │
│  5. SENSA      → Lee señales de otros antes de planificar           │
│  6. DEGRADA    → Funciona (con menos contexto) si Akasha no responde│
│                                                                      │
│  Su prompt incluye instrucciones de memoria.                         │
│  Sus paths son consistentes y descriptivos.                          │
│  Sus TTL reflejan la naturaleza del dato.                            │
│  Sus pheromones reflejan la importancia real.                        │
│                                                                      │
│  → El resultado: un agente que NO necesita hablar con los demás,    │
│    pero que puede beneficiarse de TODO lo que los demás saben.      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

> **Para el integrador:** Akasha es como la pizarra del equipo. Tú pones las reglas de qué escribir y cómo leerlo. Akasha se encarga de que esté siempre disponible, replicada, segura y consolidada. Cuanto mejor sea la disciplina de tus agentes con la memoria, más valor extraerán del sistema.
