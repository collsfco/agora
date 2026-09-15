# 🔌 Guía de Integración MCP en Ágora: Enfoques de Conexión y Roadmap

En **Ágora**, la integración con servidores de contexto y herramientas externas (como PulseHunter, Homelab, Playwright o Firecrawl) se realiza mediante un modelo híbrido estructurado según la potencia de cómputo de cada nodo.

---

## 🏛️ Comparativa de Enfoques

| Dimensión | Enfoque 1: Contrato Selectivo (Implementado en Ágora) | Enfoque 2: Descubrimiento Automático MCP |
| :--- | :--- | :--- |
| **Cómo opera** | Ágora define esquemas Pydantic y funciones cliente explícitas en `app/tools/`. | Ágora consulta `tools/list` al servidor MCP al arrancar y auto-registra todo. |
| **Control de Permisos** | **Granular y Total**: Tú eliges exactamente qué herramientas ve el bot en Telegram. | **Expone todo**: Expone automáticamente todas las herramientas registradas en el servidor. |
| **Consumo de Contexto (Tokens)** | **Mínimo y Rápido**: El System Prompt solo lleva las herramientas necesarias. | **Variable**: Si el MCP tiene 30 herramientas, el prompt inicial crece considerablemente. |
| **Mantenimiento** | Requiere mapear la función en `supervisor.py`. | Añadir `@mcp.tool()` en el servidor basta para que el agente la aprenda sola. |
| **Recomendado para** | Producción, agentes locales en GPU y control estricto de seguridad. | Prototipado rápido y conexión de MCPs de terceros (Filesystem, Brave, PostgreSQL). |

---

## 🗺️ Roadmap de Servidores MCP Planificados

Las herramientas del agente están distribuidas estratégicamente entre el **PC con GPU** (alto rendimiento) y el **Servidor Raspberry Pi 4** (24/7 y control físico):

### 💻 NODO 1: PC Principal (GPU AMD RX 7900 GRE + Cómputo Pesado)
* **Playwright MCP:** Navegación web interactiva, rellenado de formularios, renderizado de Javascript y capturas de pantalla de sitios web desde Telegram.
* **Firecrawl MCP:** Conversión limpia de páginas web y artículos completos a Markdown impecable para análisis por el LLM.
* **Multimodalidad / Generación de Imágenes (ComfyUI / Google Gemini API):** Generación de imágenes y análisis visual (OCR).

### 🏠 NODO 2: Raspberry Pi 4 (Servidor Homelab 24/7)
* **PulseHunter MCP:** Servidor de scrapers de empleo y alquileres en segundo plano.
* **Homelab MCP (Docker Manager):** Control y monitorización de contenedores de los 5 stacks (`01-infrastructure`, `02-automation`, etc.) vía socket de Docker.
* **Home Assistant MCP:** Control de sensores IoT, luces y domótica en la red local.

> 📖 **Despliegue en la Pi:** Para consultar la guía detallada de empaquetado Docker Buildx y despliegue sin sobrecargas en la Raspberry Pi 4, consulta la [Guía de Despliegue en Raspberry Pi 4](file:///home/colls/github/agora/docs/RASPBERRY_PI_DEPLOYMENT_GUIDE.md).

---

## 📦 Enfoque 1: Contrato Selectivo (Paso a Paso)

Para exponer una función de un MCP o API externa en Ágora:

1. **Crear la función cliente** en `app/tools/<modulo>_client.py`:
   ```python
   async def mi_funcion_tool(param: str) -> Dict[str, Any]:
       # Llamada HTTP / Socket al backend
       ...
   ```
2. **Declarar el esquema de la Tool** en `app/agents/supervisor.py`:
   ```python
   {
       "type": "function",
       "function": {
           "name": "mi_funcion_tool",
           "description": "Descripción clara en lenguaje natural",
           "parameters": { ... }
       }
   }
   ```
3. **Mapear la ejecución** en `execute_tool_call()` dentro de `supervisor.py`.

---

## 🌐 Enfoque 2: Descubrimiento Automático MCP (Para Futuros Servidores)

Para conectar servidores MCP externos de forma dinámica mediante `mcp-sdk`:
1. El servidor corre en un subproceso STDIO o endpoint SSE (`http://localhost:8000/sse`).
2. Ágora ejecuta el handshake inicial:
   ```python
   async with stdio_client(server_params) as (read, write):
       async with ClientSession(read, write) as session:
           await session.initialize()
           tools = await session.list_tools()
   ```
3. Las herramientas se convierten en objetos `BaseTool` de LangChain / LangGraph y se inyectan dinámicamente al LLM (`qwen2.5:14b`).
