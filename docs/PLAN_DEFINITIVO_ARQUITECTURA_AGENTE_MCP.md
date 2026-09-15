# 🛡️ Plan Definitivo de Arquitectura: Ágora, Blindaje MCP Anti-Alucinaciones & Control de Ejecución

> **Objetivo del Sistema:** Eliminar de raíz las alucinaciones en Ágora, no confiando en que el modelo local (Ollama sobre RX 7900 GRE o futuro Mini PC Ryzen 780M) "decida portarse bien", sino imponiendo **guardarraíles en código (Python + LangGraph)**, enrutamiento determinista previo, conjuntos mínimos de 1 a 4 herramientas por turno, evidencia obligatoria y tickets de confirmación firmados para acciones de riesgo.

---

## 🎯 El Principio Rector de la Arquitectura

> *"No es que la nueva arquitectura haga mágicamente infalibles a los modelos locales; **reduce las decisiones en las que el modelo puede equivocarse y bloquea en código los fallos que no son aceptables**."*

---

## 🏗️ Los 7 Pilares del Blindaje

### 1. El Grafo Manda: "Sin Evidencia no hay Respuesta"
- Para cualquier consulta que involucre datos vivos o privados (`requires_fresh_data = True`: homelab, domótica, taller, PulseHunter, clima, notas personales), **no existe una transición válida en el grafo hacia una respuesta final** a menos que la lista `evidence` contenga al menos un resultado exitoso de una herramienta de ese turno.
- Si la herramienta falla o no devuelve datos, el sistema responde obligatoriamente: *"No se ha podido verificar el estado actual en [fuente]"*. El modelo tiene prohibido inventar o usar memoria de contexto.

### 2. Enrutamiento Previo y Herramientas Mínimas (1–4 Tools)
- En lugar de pasar 19 herramientas de golpe, un **pre-router determinista en Python (por palabras clave)** clasifica el 85% de las consultas obvias sin coste de inferencia (0 ms, 0 tokens).
- Solo las peticiones complejas o ambiguas van a un Router LLM ligero con salida JSON estricta.
- El modelo ejecutor recibe únicamente las 1 a 4 herramientas de su dominio.

### 3. Modos de Ejecución: Sin "Thinking" y Temperatura 0.0 para Tools
- **Workers Ejecutores (Homelab, Workshop, Weather):** Corren con `temperature: 0.0`, `thinking: false` y esquemas Pydantic compactos. Su única misión es emitir el JSON de llamada a herramienta en menos de 1 segundo.
- **DeepSeek-R1 / Razonamiento pesado:** Queda restringido como planificador o asesor analítico de solo lectura; **jamás recibe herramientas de escritura ni acceso directo a infraestructura**.

### 4. Caché con TTL Inteligente e Invalidación
Para no saturar la Raspi ni el backend en conversaciones seguidas:
- **Métricas CPU/RAM/Temperatura:** TTL de `10–15 s`.
- **Lista de contenedores:** TTL de `15–30 s` (se invalida de inmediato tras reiniciar/desplegar).
- **Logs:** TTL de `0–5 s` (casi siempre en vivo).
- **Home Assistant (Luces/sensores):** TTL de `2–10 s`.
- **Taller (Spoolman / Homebox):** TTL de `5–15 min`.
- **Clima / Pronóstico:** TTL de `15–30 min`.
- **PulseHunter:** TTL de `15–60 min`.
- **Bypass forzado:** Si el usuario dice *"ahora mismo"*, *"actualiza"* o es el paso previo a una acción de escritura, se salta la caché.

### 5. `read_before_write` y Confirmación con Ticket Firmado (`action_id`)
- **Regla dura `read_before_write`:** No se puede proponer reiniciar un contenedor o borrar una alerta sin haber consultado su estado real inmediatamente antes en ese mismo turno.
- **Ticket serializado con expiración:**
  ```json
  {
    "action_id": "act_9918a2",
    "profile_id": "principal_a",
    "chat_id": 12345678,
    "tool": "restart_homelab_container",
    "arguments": { "container_name": "immich-server" },
    "args_hash": "e3b0c44...",
    "created_at": "2026-09-15T14:30:00+02:00",
    "expires_at": "2026-09-15T14:35:00+02:00"
  }
  ```
- El botón de Telegram envía únicamente el `action_id`. El backend valida el token, verifica la idempotencia (ejecución única) y ejecuta la acción en Docker sin reinterpretar texto con el LLM.

### 6. Presupuestos y Límites por Turno (*Turn Budgets*)
- Máximo de llamadas a herramientas por turno: **4 llamadas**.
- Máximo de reintentos por tool fallida: **1 reintento**.
- Timeout total por turno: **45 segundos**.
- Logs de contenedores: Máximo **100 líneas** / **12.000 caracteres**.
- Búsqueda web: Máximo **3 búsquedas** y **2 lecturas**.

### 7. Trazabilidad Estructurada (`JSONL`) desde el Día Uno
En `logs/agent_traces.jsonl` se guarda cada turno con:
- `trace_id`, `profile_id`, `domain`, `tools_visible`, `tool_calls`, `cache_hit`, `evidence_count`, `latency_ms` y `prompt_hash`.
- Enmascaramiento estricto de secretos, tokens, cookies y contraseñas.

---

## 🗂️ Nueva Estructura del Código en Ágora

```text
app/
├── agents/
│   ├── prompts/
│   │   ├── global/
│   │   │   ├── identity.md         # Rol de Ágora
│   │   │   ├── language.md         # Regla dinámica: idioma del usuario
│   │   │   ├── safety.md           # Reglas de seguridad y datos no confiables
│   │   │   └── grounding.md        # Política de evidencia obligatoria
│   │   ├── workers/
│   │   │   ├── router.md           # Clasificador de ambigüedad
│   │   │   ├── homelab.md          # HomelabOps (solo lectura Docker/Raspi)
│   │   │   ├── home_assistant.md   # Estado del hogar
│   │   │   ├── workshop.md         # Spoolman y Homebox
│   │   │   ├── pulsehunter.md      # Empleo y vivienda
│   │   │   └── weather_web.md      # Clima y búsqueda web
│   │   └── profiles/
│   │       ├── principal_a.md      # Francisco (DevOps, Homelab, 3D)
│   │       └── principal_b.md      # Perfil Secundario
│   │
│   ├── config/
│   │   ├── agents.yaml             # Modelos, temperaturas, budgets y thinking
│   │   ├── tool_registry.yaml      # Catálogo de tools: dominio, riesgo, TTL y profiles
│   │   └── routing_rules.yaml      # Palabras clave y dominios
│   │
│   ├── loader.py                   # Carga dinámica y modular de prompts .md
│   ├── router.py                   # Pre-router en Python (0ms) + fallback LLM
│   ├── graph.py                    # Grafo LangGraph con verificación de evidencia
│   └── state.py                    # AgoraState (TypedDict con evidence y pending_action)
│
├── policy/
│   ├── tool_policy.py              # Validación de allowlist y permisos por perfil
│   ├── confirmation.py             # Generador y validador de tickets action_id
│   └── profile_isolation.py        # Aislamiento estricto de bóvedas y memoria FTS5
│
├── mcp/
│   ├── registry.py                 # Despachador HTTP MCP
│   ├── cache.py                    # Gestor de caché en memoria con TTL
│   └── normalizer.py               # Envoltorio homogéneo NormalizedToolResult
│
├── logs/
│   ├── agent_traces.jsonl          # Trazabilidad completa por turno
│   └── action_audit.jsonl          # Auditoría de acciones ejecutadas por confirmación
│
└── evals/
    ├── cases/
    │   ├── happy_paths.json        # Casos estándar de consulta
    │   ├── failure_cases.json      # Timeouts, JSON corrupto, tools inventadas
    │   ├── security_cases.json     # Inyecciones en notas/logs, cruce Principal A/B
    │   └── confirmation_cases.json # Expiración de tickets, doble clic en Telegram
    └── run_evals.py                # Runner automatizado de benchmarking
```

---

## 🧩 Contratos de Datos y Tipos Clave

### Estado del Grafo (`state.py`)
```python
from typing import Any, Literal, TypedDict, Optional
from datetime import datetime

Domain = Literal["homelab", "home", "workshop", "pulsehunter", "knowledge", "weather_web", "general"]
Risk = Literal["none", "read", "write", "destructive"]

class Evidence(TypedDict):
    source: str
    tool: str
    observed_at: str
    cache_status: Literal["miss", "hit", "bypassed"]
    data: dict[str, Any]

class PendingAction(TypedDict):
    action_id: str
    tool: str
    arguments: dict[str, Any]
    summary: str
    profile_id: str
    chat_id: int
    expires_at: str

class AgoraState(TypedDict, total=False):
    profile_id: Literal["principal_a", "principal_b"]
    chat_id: int
    thread_id: str
    user_message: str
    response_language: Literal["es", "en"]
    domain: Domain
    risk: Risk
    requires_fresh_data: bool
    allowed_tools: list[str]
    evidence: list[Evidence]
    tool_call_count: int
    pending_action: Optional[PendingAction]
    final_answer: str
```

### Resultado MCP Normalizado (`normalizer.py`)
```python
from pydantic import BaseModel
from typing import Any, Literal, Optional
from datetime import datetime

class NormalizedToolResult(BaseModel):
    ok: bool
    source: str
    tool: str
    observed_at: datetime
    cache_status: Literal["miss", "hit", "bypassed"]
    data: dict[str, Any]
    warnings: list[str] = []
    error: Optional[str] = None
```

---

## ⚡ Preparado para el Futuro: Mini PC + GPU Heavy (Topología Dual)

Este diseño desacoplado encaja como un guante con tu futura topología de hardware:

```
┌──────────────────────────────────────────────────────────────────┐
│ MINI PC (Bmax Ryzen 7 8745HS / 780M / 32GB RAM) - 24/7 Always-On │
│ ➔ Telegram Ingress & CLI                                         │
│ ➔ Pre-router determinista (Python, 0 ms)                         │
│ ➔ Control Plane de LangGraph & SQLite Checkpoints                │
│ ➔ Workers de baja latencia con modelo 4B / 7B (clima, taller)   │
│ ➔ MCP Tool Gateway & Caché local                                 │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
             ¿Tarea compleja o modelo grande requerido?
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│ PC PRINCIPAL (AMD RX 7900 GRE 16GB VRAM) - Nodo "Heavy"          │
│ ➔ Modelo 14B / Qwen 2.5/3 para diagnósticos profundos de logs    │
│ ➔ Síntesis compleja de múltiples fuentes de infraestructura      │
│ ➔ Solo se enciende/despierta bajo demanda (WOL)                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📋 Plan de Ejecución Inmediato

### 🔹 Semana 1: Cimentación (Prompts, Config & Pre-Router)
- [ ] Crear estructura de directorios `prompts/` y extraer textos a Markdown en inglés con cláusula de idioma dinámico.
- [ ] Crear `config/tool_registry.yaml` y `config/routing_rules.yaml`.
- [ ] Implementar `state.py` con `AgoraState` y `loader.py` para componer prompts.
- [ ] Implementar `router.py` con pre-enrutamiento por palabras clave.

### 🔹 Semana 2: Gateway MCP, Borde Anti-Alucinaciones & Caché
- [ ] Implementar `mcp/cache.py` con TTL por dominio y clave canónica.
- [ ] Implementar `mcp/normalizer.py` asegurando `observed_at` en todas las herramientas.
- [ ] Crear borde condicional en LangGraph: si `requires_fresh_data=True` y `evidence` está vacía, impedir respuesta final y devolver aviso de no verificación.
- [ ] Limitar las tools visibles por turno a un máximo de 1 a 4.

### 🔹 Semana 3: Seguridad `action_id`, Logging JSONL & Evals
- [ ] Implementar `policy/confirmation.py` con generación de tickets `action_id` y flujo de botones en Telegram.
- [ ] Implementar `read_before_write` (obligar a leer estado antes de emitir ticket de reinicio/borrado).
- [ ] Activar logging estructurado en `logs/agent_traces.jsonl`.
- [ ] Crear suite de pruebas en `evals/` con casos felices y de fallo (timeouts, inyecciones, expiración).

