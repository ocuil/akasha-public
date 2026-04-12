# Akasha — Memoria Persistente para Agentes de IA

> *"¿Y si tus agentes de IA pudieran recordar, aprender y coordinarse — sin que tú cablearas cada conexión?"*

---

## El Problema

Toda organización que despliega agentes de IA en 2026 choca con el mismo muro:

**Los agentes son individualmente inteligentes pero colectivamente amnésicos.** Un planificador agenda tareas. Un investigador recupera documentos. Un programador escribe código. Un monitor vigila producción. Cada uno es brillante en aislamiento — pero ninguno recuerda lo que los otros aprendieron.

### Tres Promesas Rotas de los Sistemas Multi-Agente

#### 1. Los Agentes Lo Olvidan Todo
Cuando el Agente A descubre que "el cliente prefiere resúmenes de menos de 200 palabras", ese conocimiento muere con la sesión. La próxima vez que el Agente B atiende al mismo cliente, empieza desde cero. **No hay aprendizaje compartido.**

#### 2. La Coordinación Requiere Cableado Manual
Si el Agente A necesita pasar contexto al Agente B, construyes un pipeline. Si el Agente C necesita saber lo que aprendió el Agente A, construyes otro. Para N agentes, necesitas N² conexiones. **Esto no escala.**

#### 3. La Infraestructura No Fue Diseñada Para Esto
Las bases de datos almacenan datos. Las bases vectoriales almacenan embeddings. Ninguna almacena *conocimiento* — la comprensión estructurada y en evolución que los agentes construyen con el tiempo.

---

## La Solución: Akasha

Akasha es un **sistema de memoria persistente** para agentes de IA. Se sitúa detrás de tus agentes — no los reemplaza, sino que **les da un espacio compartido para almacenar conocimiento, recordar experiencias y coordinarse sin cableado explícito.**

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Agente A│  │ Agente B│  │ Agente C│
│Planific.│  │ Coder   │  │ Monitor │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┼────────────┘
                  │
          ┌───────▼───────┐
          │    AKASHA     │
          │               │
          │  Working ─────│── Qué están haciendo ahora
          │  Episódica ───│── Qué ocurrió (historial)
          │  Semántica ───│── Qué han aprendido
          │  Procedural ──│── Cómo hacer las cosas
          │               │
          │  Feromonas ───│── Señales de coordinación
          │               │
          └───────────────┘
```

Cualquier agente puede **escribir** lo que aprende. Cualquier agente puede **leer** lo que otros saben. Sin pipelines. Sin colas de mensajes. Sin orquestador decidiendo quién habla con quién.

---

## Principios de Diseño

### Cuatro Capas de Memoria (Inspiradas en Ciencia Cognitiva)

| Capa | Propósito | Vida Útil | Analogía |
|------|-----------|-----------|----------|
| **Working** | Bloc de notas de la tarea actual | Minutos | Tu escritorio |
| **Episódica** | Eventos, resultados, decisiones | Horas → Días | Tu diario |
| **Semántica** | Hechos, patrones, insights | Días → Permanente | Tu base de conocimiento |
| **Procedural** | Workflows probados, playbooks | Permanente | Tu memoria muscular |

### Nidra — Consolidación Automática de Memoria

Nombrado por *Yoga Nidra* (sueño yóguico), Nidra es un proceso en segundo plano que organiza la memoria — como tu cerebro consolida experiencias durante el sueño.

> [!IMPORTANT]
> **Cómo funciona Nidra realmente (realidad de implementación):**
> - **Modo por defecto (basado en reglas, sin LLM):** Cuenta registros por tema, identifica áreas de alta actividad, crea registros resumen en la capa semántica. **Los registros originales se marcan como consolidados — NUNCA se eliminan.**
> - **Modo LLM (Enterprise, opt-in):** Solo si el operador lo configura explícitamente. Los prompts son deterministas y auditables.
> - **Evaporación de feromonas:** Solo afecta a señales de feromonas (hints de coordinación). Nunca toca registros, nunca borra datos.
>
> Nidra NO es compresión con pérdida. Es aditiva — crea nuevo conocimiento sin destruir fuentes.

### Estigmergia — Coordinación Sin Comunicación

Inspirada en cómo las colonias de hormigas se coordinan mediante señales ambientales:

- Los agentes emiten **señales de feromonas** (metadata ligera con intensidad y vida media)
- Otros agentes detectan estas señales y responden en consecuencia
- Las señales decaen naturalmente — las pistas antiguas se desvanecen, las actuales permanecen fuertes

> [!IMPORTANT]
> **Qué son realmente las feromonas (realidad de implementación):**
> - Las feromonas son **hints de coordinación**, no colas de mensajes. Señalizán "descubrimiento", "éxito", "alerta", "reclamación" sobre un tema.
> - NO son para entrega garantizada de tareas. Para eso, usa registros normales sin TTL.
> - Piensa en ellas como un "tablón de estado del equipo" — no como una "cola de tickets de trabajo".
> - Akasha ofrece ambos modelos: registros durables para datos, feromonas efímeras para coordinación.

---

## Lo Que Akasha NO Es

Para evitar malentendidos, seamos explícitos:

| Akasha es... | Akasha NO es... |
|-------------|-----------------|
| Un almacén de memoria persistente | Una cola de mensajes (usa Kafka/RabbitMQ para entrega garantizada) |
| Una capa de coordinación vía estigmergia | Un orquestador de tareas (usa LangGraph/Temporal para DAGs) |
| Un sistema key-value con paths y queries glob | Una base de datos vectorial (usa Qdrant/Pinecone para búsqueda semántica) |
| Zero-LLM por defecto — operaciones sub-ms | Dependiente de LLM como Mem0 (que llama a LLMs en cada escritura) |
| Infraestructura — funciona con cualquier framework | Un framework — no reemplaza LangGraph, CrewAI, etc. |

---

## Lo Que Existe Hoy (v1.1.2)

Akasha es software en producción funcionando hoy — no un roadmap.

### Capacidades Principales

| Capacidad | Estado | Significado |
|-----------|--------|-------------|
| **Memoria Key-Value Persistente** | ✅ Producción | Cualquier agente lee/escribe via REST, gRPC o MCP |
| **Cuatro Capas de Memoria** | ✅ Producción | Working, Episódica, Semántica, Procedural — cada una con retención apropiada |
| **Rastros de Feromonas** | ✅ Producción | Coordinación vía señales ambientales, no mensajería directa |
| **Consolidación de Memoria (Nidra)** | ✅ Producción | Extracción automática de patrones — originales siempre preservados |
| **Concurrencia Optimista (CAS)** | ✅ Producción | Escrituras multi-agente seguras sin locks |
| **Cluster HA de 3 Nodos** | ✅ Producción | Replicación CRDT, operaciones sin downtime |
| **MCP Server** | ✅ Producción | Integración nativa con Claude, Gemini, Cursor y cualquier cliente MCP |
| **Auto-TLS** | ✅ Producción | Cifrado por defecto, zero configuración |
| **Dashboard** | ✅ Producción | Visibilidad en tiempo real del estado de memoria y salud del cluster |
| **Cifrado en Reposo (BYOK)** | ✅ Producción | AES-256-GCM con Bring Your Own Key |
| **Audit Trail Inmutable** | ✅ Producción | Todos los eventos de seguridad, append-only, no eliminables |
| **Sync Backpressure** | ✅ Producción | Anti-entropía rate-limited, zero pérdida de datos bajo carga |
| **Informes de Diagnóstico** | ✅ Producción | Health scoring (0-100) con topología, seguridad y rendimiento |

### Distribución

| Canal | Enlace |
|-------|--------|
| **Docker Hub** | `docker pull alejandrosl/akasha` |
| **Python SDK** | `pip install akasha-client` |
| **Node.js SDK** | `npm install akasha-memory` |
| **MCP Server** | [github.com/ocuil/akasha-public/mcp-server](https://github.com/ocuil/akasha-public/tree/main/mcp-server) |
| **GitHub** | [github.com/ocuil/akasha-public](https://github.com/ocuil/akasha-public) |

### Perfil de Rendimiento

| Métrica | Valor | Contexto |
|---------|-------|----------|
| Latencia de lectura (P50) | **1.2 ms** | Sin LLM en la ruta de lectura |
| Latencia de escritura (P50) | **1.5 ms** | Sin LLM en la ruta de escritura |
| Throughput | **2.237 ops/seg** | Carga multi-agente concurrente |
| Binario | **25 MB** | Un solo ejecutable, sin JVM, sin runtime |
| Imagen Docker | **46 MB** | Más pequeña que un hello-world de Node.js |
| Memoria | **~50 MB** | Para 100K registros |
| QA Suite | **41/41 pasando** | Unitarios + integración + cluster E2E |

---

## Casos de Uso Concretos

### Caso 1: Contexto Persistente Entre Sesiones

**Sin Akasha:**
```
Lunes:   Claude analiza 500 documentos → genera conclusiones
Martes:  Claude NO recuerda NADA del lunes
         ¿Inyectar 10M tokens? → 15-40€ por conversación, 30s latencia
```

**Con Akasha:**
```
Lunes:   Claude guarda hallazgos → memory/semantic/research/api-design
Martes:  Claude lee 200 tokens → tiene todo el contexto → 0,001€, instantáneo
```

### Caso 2: Conocimiento Compartido Multi-Agente

**Sin Akasha:**
```
Agente A: "El cliente prefiere email" → muere con la sesión
Agente B: Contacta al cliente por Slack → cliente frustrado
```

**Con Akasha:**
```
Agente A: escribe memory/semantic/clientes/acme/preferencias → {"canal": "email"}
Agente B: lo lee antes de actuar → usa email → cliente satisfecho
```

### Caso 3: Coordinación entre Agentes (Estigmergia)

**Sin Akasha:**
```
Agente A inicia tarea → nadie lo sabe
Agente B inicia LA MISMA tarea → computación desperdiciada
```

**Con Akasha:**
```
Agente A: emite feromona("tasks/enrichment", signal=CLAIM) → "Estoy en ello"
Agente B: detecta la feromona → "Ya está cubierto, haré otra cosa"
```

---

## Posición Competitiva

| | **Akasha** | **Mem0** | **Zep (Graphiti)** | **Custom (Redis + VectorDB)** |
|--|---|---|---|---|
| **Latencia escritura** | **<1 ms** (0 LLM) | ~1.400 ms (2 LLM) | ~200 ms | Variable |
| **Latencia lectura** | **<1 ms** | ~200-500 ms | ~200 ms | Variable |
| **Dependencia LLM** | **Ninguna** (opcional) | **Crítica** | **Crítica** | Ninguna |
| **Multi-agente** | ✅ Nativo | ❌ Single-user | ❌ Single-user | DIY |
| **Coordinación** | ✅ Estigmergia | ❌ | ❌ | ❌ |
| **Clustering (HA)** | ✅ CRDT 3+ nodos | ❌ | ❌ | DIY |
| **Self-hosted** | ✅ Binario único | ❌ Cloud + Qdrant | ❌ Neo4j | DIY |
| **MCP Server** | ✅ Nativo | ❌ | ❌ | ❌ |

**Insight clave:** Mem0 pregunta *"¿qué hechos debo recordar sobre este usuario?"* (personalización single-user). Akasha pregunta *"¿cómo debería una comunidad de agentes compartir y construir conocimiento?"* (coordinación multi-agente). Resuelven problemas diferentes.

---

## Arquitectura

- **Motor:** Rust (binario único, zero dependencias)
- **Almacenamiento:** RocksDB (WAL, LSM, compresión LZ4, cifrado AES-256-GCM opcional)
- **APIs:** REST (HTTPS :7777) + gRPC (:50051) + MCP (stdio/SSE) + WebSocket + SSE
- **Clustering:** SWIM gossip + replicación delta CRDT + consenso GossipRaft
- **Auth:** JWT + API Keys, Argon2id, RBAC, aislamiento por namespace
- **Dashboard:** SPA React embebida (rust-embed, sin servidor separado)

---

## Hoja de Ruta

### Fase 1: Adopción (Ahora → Q3 2026)
*Que sea trivialmente fácil de probar*

- ✅ MCP Server para Claude/Gemini/Cursor
- ✅ SDKs Python y Node.js
- ✅ Deploy Docker de un solo comando
- ◻️ Ejemplo de integración con LangGraph
- ◻️ Ejemplo de integración con CrewAI
- ◻️ Integración con Google ADK

### Fase 2: Inteligencia (Q3 → Q4 2026)
*La capa de memoria empieza a pensar*

- ◻️ Consolidación potenciada por LLM (Nidra + modelos de lenguaje)
- ◻️ Extracción automática de entidades y grafos de conocimiento
- ◻️ Consultas temporales de memoria ("¿qué cambió la semana pasada?")

### Fase 3: Ecosistema (2027)
*Akasha se convierte en estándar*

- ◻️ Oferta cloud gestionada
- ◻️ Esquemas de memoria pre-construidos para agentes
- ◻️ SDKs para Go, Java, Rust

---

## El Nombre

**Akasha** (आकाश) es un término sánscrito para la sustancia fundamental del cosmos — el "espacio" en el que todo existe y a través del cual viaja toda la información.

En la cosmología védica, los Registros Akáshicos son la memoria universal — un campo donde cada pensamiento, acción y experiencia queda inscrito. No es propiedad de ningún individuo, pero accesible para todos.

Eso es lo que estamos construyendo: **el campo de memoria compartida para agentes inteligentes.**

---

*Construido con 🦀 Rust para rendimiento · Diseñado con biología para inteligencia · Distribuido con intención para escalar*

*Un binario. Zero dependencias. Memoria persistente.*
