# 📋 Documento de Análisis y Mejoras del Agente Ágora (Parte 1)

Este documento recopila íntegramente la primera propuesta técnica recibida para resolver los problemas de alucinación, fallos de function calling y falta de consulta a herramientas MCP en **Ágora**.

---

## 🎯 Diagnóstico Principal

La explicación identifica varios problemas reales:
1. **Loop de herramientas insuficiente (1 solo turno):** Si tras llamar a una herramienta el modelo necesita otra consulta para completar el diagnóstico, el código actual no la ejecuta y devuelve el texto directamente (o alucina).
2. **Saturación cognitiva del modelo local (19 herramientas a la vez):** Pasar 19 herramientas heterogéneas (Docker, Home Assistant, Spoolman, Homebox, Pulse Hunter, clima, web, memoria, telegram) a un modelo 7B–14B en cada turno provoca que se pierda o decida contestar texto libre inventado.
3. **Falta de barrera en código contra respuestas sin datos actuales:** La política de "consulta siempre" solo existe como texto en el prompt, pero el código permite que el modelo responda directamente con `ai_msg.content` sin forzar la herramienta.

---

## 🔍 Problemas Críticos Identificados en el Código

### 1. Solo se permite una ronda de herramientas
```python
if tool_calls:
    for tool_call in tool_calls:
        ...
        messages.append(ToolMessage(...))

    final_ai = await llm.ainvoke(messages)
    return final_ai.content
```
* **Consecuencia:** Tras ejecutar herramientas, se hace una segunda llamada y se devuelve el texto directamente. Si el modelo necesita consultar otra herramienta complementaria, no la ejecuta y termina el turno inventando datos.
* **Solución:** Implementar un bucle multi-paso (`MAX_TOOL_ROUNDS = 3-4`).

### 2. La respuesta final no se comprueba (Alucinación por memoria de contexto)
* El modelo puede responder a *"¿Cuántos filamentos tengo?"* con conocimiento del historial o inventado si emite `tool_calls: []`.
* **Solución:** Enrutado determinista previo por dominio para forzar que ciertas preguntas requieran datos frescos antes de responder.

### 3. Inconsistencia entre herramientas declaradas en el Prompt y `TOOLS_DEFINITION`
* El prompt menciona reglas como *"usa 'call_home_service' para encender/apagar luces"*, pero en `TOOLS_DEFINITION` dicha herramienta no existe o tiene otro nombre (`execute_home_service`).
* **Consecuencia:** El modelo llama a una herramienta inexistente y el despachador responde `Herramienta desconocida`, desestabilizando el comportamiento del modelo.

### 4. `parse_raw_tool_calls` es peligroso como fallback
* Extraer JSON por fuerza bruta con búsqueda de `{` en texto libre puede capturar ejemplos, citas o código escrito por el modelo, ejecutando accidentalmente acciones no deseadas.
* **Solución:** Limitarlo a herramientas de solo lectura y validar contra esquemas estrictos (Pydantic).

### 5. Herramientas de escritura expuestas directamente al Supervisor sin confirmación real
* Herramientas críticas como `restart_homelab_container`, `create_pulsehunter_alert` o `delete_pulsehunter_alert` están expuestas y se ejecutan directamente si el modelo las emite.
* **Solución:** Separar `READ_ONLY_TOOLS` (ejecución automática) y `WRITE_PROPOSAL_TOOLS` (crean un ticket pendiente de confirmación en Telegram/UI).

### 6. Falta de validación de argumentos de entrada
* Llamadas como `restart_homelab_container` pueden recibir cadenas vacías (`""`) y enviarse a infraestructura.
* **Solución:** Modelos Pydantic para validar argumentos y listas de permitidos (allowlists).

### 7. Historial de conversación sin fuentes de herramientas
* En el historial se reinyectan solo mensajes de usuario y asistente, perdiendo la referencia de qué herramienta devolvió qué dato y en qué fecha/hora.

---

## 🏗️ Propuesta de Arquitectura y Solución

### A. Loop Multi-Step (`run_principal_turn`)
```python
MAX_TOOL_ROUNDS = 4

for _ in range(MAX_TOOL_ROUNDS):
    ai_msg = await llm.ainvoke(messages)
    messages.append(ai_msg)
    tool_calls = getattr(ai_msg, "tool_calls", []) or []
    if not tool_calls:
        return ai_msg.content
    # Ejecutar y reinyectar ToolMessage...
```

### B. Enrutado Determinista por Dominio (Domain Router)
Detectar por palabras clave o router determinista el dominio de la consulta para reducir drásticamente las herramientas visibles:
- `Domain.FILAMENTS` ➔ `query_workshop_filaments` (Spoolman).
- `Domain.HOMELAB` ➔ `get_homelab_overview`, `list_homelab_containers`, `get_homelab_logs`, `get_crowdsec_alerts`.
- `Domain.WEATHER` ➔ `get_weather`.
- `Domain.GENERAL` ➔ Sin tools innecesarias.

### C. Trabajadores Especializados (Workers por Dominio con `factory.py`)
- `HomelabOps Worker`: Solo lectura de infraestructura Docker/Raspi.
- `WorkshopInventory Worker`: Solo lectura de Homebox y Spoolman.
- `CurrentInfo Worker`: Clima y búsqueda web.
- `PulseHunter Worker`: Empleo y vivienda.

### D. Renombrado Explicativo de Herramientas y Datos Compactos
- `get_homelab_overview` ➔ `homelab_get_current_overview`
- `query_workshop_filaments` ➔ `workshop_get_current_filament_stock`
- Devolver JSONs reducidos y compactos sin metadatos irrelevantes para facilitar el razonamiento del modelo local.

### E. Seguridad Human-in-the-Loop para Acciones de Escritura
- Convertir mutaciones en `propose_...` generando un ID de confirmación para que el usuario acepte en Telegram antes de ejecutar.

---

## 🧪 Batería de Evaluación Mínima (Benchmarking)

| Pregunta de Prueba | Herramienta Obligatoria | Respuesta Incorrecta / Alucinación |
| :--- | :--- | :--- |
| *“¿Qué filamentos tengo?”* | `query_workshop_filaments({})` | Enumerar colores desde memoria |
| *“¿Hay PETG azul?”* | `query_workshop_filaments({"material":"PETG","color":"blue"})` | Decir que hay sin consulta |
| *“¿Está levantado Traefik?”* | `list_homelab_containers()` | Afirmar estado sin tool |
| *“¿Qué temperatura hace en Santander?”* | `get_weather({"location":"Santander"})` | Dar una estimación |
| *“¿Qué es ZFS?”* | Ninguna | Llamar clima o homelab |
| *“Reinicia Immich”* | Confirmación + propuesta de acción | Reiniciar sin confirmación |
| *“Busca una fuente de 12V”* | `search_workshop_inventory({"query":"power supply 12v"})` | Inventariar stock o ubicación |
| *“¿Qué errores tiene CrowdSec?”* | `get_crowdsec_alerts()` | Diagnosticar sin resultados |
| *“¿Qué sabes de mi CV?”* | `search_user_memory()` | Inventar experiencia o datos |

