# 🛡️ Estándar de Herramientas y Servidores MCP: Arquitectura Ágora

> **Documento Normativo Canónico para el Desarrollo de Capabilities**  
> **Versión:** 2.0.0  
> **Ámbito:** Repositorios `agora`, `homelab`, `pulse-hunter`, `agora-contracts` y servicios satélite.

---

## 🎯 Objetivo y Filosofía de Fiabilidad
Maximizar la fiabilidad y previsibilidad en la selección y ejecución de capacidades, convirtiendo los fallos no aceptables en **propiedades estrictamente verificables por el sistema**:
1. **Sin afirmaciones sin evidencia:** Ningún LLM puede hacer afirmaciones sobre el estado vivo del sistema sin un `ToolResult` reciente.
2. **Sin herramientas no autorizadas:** El modelo solo ve herramientas permitidas para el perfil activo y la intención actual (1–5 tools por turno).
3. **Sin mutaciones directas:** El modelo no ejecuta escrituras ni borrados; emite propuestas de acción que el backend valida y somete a confirmación humana (*Human-in-the-Loop*).
4. **Sin mezcla entre perfiles:** El alcance de datos (`owner_id` / `profile_id`) es inyectado por el backend autenticado; nunca es elegido por el LLM.
5. **Sin entradas o salidas no controladas:** Todo cruce de frontera de confianza debe validar esquemas Pydantic estrictos con `extra="forbid"`.

---

## 🌳 1. Árbol de Decisión: ¿Cuándo Tool Local y cuándo Servidor MCP?

El agente de desarrollo o programador debe seguir este árbol de decisión técnico:

```text
¿Qué tipo de capacidad estás implementando?
│
├── 1. ¿Es lógica de control, regex, enrutamiento, validación o idioma?
│      └── ▶ FUNCIÓN PYTHON INTERNA (Control Plane de Ágora, NUNCA Tool para el LLM)
│
├── 2. ¿Es una consulta HTTP/BD local o remota simple, exclusiva de Ágora y sin clientes externos?
│      └── ▶ TOOL LOCAL PYTHON (app/tools/<domain>/read_tools.py)
│          Ejemplo: Integración actual con Pulse Hunter API, consultas a SQLite/Obsidian.
│
├── 3. ¿Accede a hardware, Docker o red de otra máquina (ej. Raspberry Pi / Mini PC)?
│      └── ▶ SERVIDOR MCP DEDICADO (Streamable HTTP autenticado o FastMCP remoto)
│          Ejemplo: homelab-mcp (contenedores, Home Assistant, Spoolman, Homebox).
│
├── 4. ¿Maneja credenciales ultra-sensibles o infraestructura crítica aislada?
│      └── ▶ SERVIDOR MCP AISLADO con tokens de servicio y red privada/Tailscale.
│
└── 5. ¿Es una acción que modifica, borra o altera el mundo exterior (reinicio, borrar alerta, enviar mensaje)?
       └── ▶ TOOL DE PROPUESTA TIPADA (*_propose_*) + Ticket en Backend
           (El LLM emite una propuesta estructurada; el backend gestiona la confirmación en Telegram).
```

---

## 📦 2. Paquete Compartido de Contratos: `agora-contracts`

Para evitar desincronizaciones de esquemas entre repositorios (`agora`, `homelab`, `pulse-hunter`), los contratos base se centralizan en la librería:
`/home/colls/github/agora-contracts/`

### A. Envoltorio Universal `ToolResult[T]`
```python
from datetime import datetime
from typing import Generic, Literal, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

class ToolError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    retryable: bool = False
    http_status: int | None = None
    suggested_next_tool: str | None = None
    retry_after_seconds: int | None = None

class ToolMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    tool: str
    observed_at: datetime
    cache_status: Literal["hit", "miss", "bypassed"] = "bypassed"
    request_id: str | None = None
    contract_version: str = "1.0.0"

class ToolResult(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    meta: ToolMeta
    data: T | None = None
    warnings: list[str] = Field(default_factory=list)
    error: ToolError | None = None
```

---

## ⚡ 3. Flujo Seguro de Mutaciones: `ActionProposal` ➔ `ActionTicket`

Las herramientas con efectos colaterales se dividen en clases de riesgo:
`risk: read | write | destructive | external | admin`

### Ciclo de Ejecución:
1. **Lectura previa:** Se consulta el estado actual con una herramienta de lectura (`read`).
2. **Propuesta del LLM:** El LLM llama a `*_propose_*` y devuelve un `ActionProposal` tipado (sin tokens de autorización ni `action_id`):
   ```python
   class ActionProposal(BaseModel):
       model_config = ConfigDict(extra="forbid")
       kind: Literal["action_proposal"] = "action_proposal"
       action: str
       summary: str
       arguments: dict[str, Any]
       impact: str
       requires_confirmation: bool = True
   ```
3. **Generación del Ticket en Backend:** El Gateway de Ágora valida la política y genera el `ActionTicket`:
   * `action_id`: UUID criptográfico.
   * `profile_id`: Perfil autenticado (`principal_a` o `principal_b`).
   * `arguments_hash`: Hash SHA-256 de los argumentos normalizados.
   * `expiry`: 5 minutos de validez.
   * `idempotency_key`: Bloqueo ante dobles pulsaciones.
4. **Confirmación en Telegram:** Se envía mensaje con botones `[ Confirmar ]` y `[ Cancelar ]`. El callback transmite **únicamente el `action_id`**.
5. **Ejecución Backend:** El backend invoca la acción directamente sobre la API/MCP usando los argumentos almacenados en el ticket. **El LLM no participa en la ejecución.**
6. **Verificación:** Una tool de lectura verifica el resultado y confirma al usuario.

---

## 🔍 4. Gestión Eficiente de Contexto: Revelación Progresiva (*Progressive Disclosure*)

Siguiendo las mejores prácticas de la industria (Anthropic / Cloudflare Code Mode):
* **No sobrecargar el contexto:** En vez de inyectar decenas de esquemas de herramientas en cada turno, el enrutador determinista filtra y entrega **únicamente entre 1 y 5 herramientas relevantes** al worker asignado.
* **Filtrado previo en el adaptador:** Si una consulta devuelve 50 contenedores o 100 ofertas de trabajo, el adaptador o servidor MCP procesa, filtra y compacta los datos antes de inyectarlos al contexto del modelo.
* **Redacción de Secretos y Auditoría:** Los logs y trazas deben anonimizar automáticamente tokens, contraseñas y campos sensibles (`authorization`, `cookie`, `password`).

---

## 📋 5. Plantilla Central del Manifiesto (`tool_registry.yaml`)

```yaml
tools:
  homelab_get_resource_overview:
    version: 1
    enabled: true
    adapter:
      type: mcp
      server: homelab_mcp
      tool: homelab_get_resource_overview
    domain: homelab
    capability: containers
    operation: get_overview
    risk: read
    profiles:
      - principal_a
      - principal_b
    visibility:
      workers:
        - homelab
      max_tools_per_turn_group: 3
    freshness:
      requires_live_evidence: true
      max_evidence_age_seconds: 15
      cache_ttl_seconds: 10
    limits:
      timeout_seconds: 5
      max_retries: 1
      max_output_chars: 12000
    contracts:
      input: "agora_contracts.homelab.ResourceOverviewInput"
      output: "agora_contracts.homelab.ResourceOverviewOutput"
    audit:
      classification: operational_read
      log_arguments: true
      redact_fields: []

  pulsehunter_search_jobs:
    version: 1
    enabled: true
    adapter:
      type: local
      handler: app.tools.pulsehunter.read_tools.search_jobs
    domain: pulsehunter
    capability: jobs
    operation: search
    risk: read
    profiles:
      - principal_a
    visibility:
      workers:
        - pulsehunter
      max_tools_per_turn_group: 3
    freshness:
      requires_live_evidence: true
      max_evidence_age_seconds: 1800
      cache_ttl_seconds: 900
    limits:
      timeout_seconds: 12
      max_retries: 1
      max_output_chars: 16000
    contracts:
      input: "agora_contracts.pulsehunter.JobSearchInput"
      output: "agora_contracts.pulsehunter.JobSearchOutput"
    audit:
      classification: private_read
      log_arguments: true
      redact_fields: []
```

---

## 🔮 6. Primitivas Futuras de MCP

Para futuras evoluciones hacia un ecosistema multi-nodo (Mini PC ↔ Torre GPU):
* **Tools:** Consultas dinámicas y propuestas de acciones (el núcleo actual).
* **Resources:** Documentación estática de lectura y catálogos de servicios (`homelab://runbooks/immich`, `pulsehunter://filters/profile`).
* **Prompts:** Plantillas de tareas predefinidas en la UI (ej. `/diagnose-homelab`), nunca como sustituto de controles de seguridad.
