# 🏛️ Ágora — Ecosistema Multi-Agente Distribuido & Orquestador de Homelab

> **Ágora**: *Plaza central de intercambio agéntico (Agent2Agent Protocol & MCP Hub)*

---

## 📚 Documentación y Libro Maestro del Sistema

Para entender, replicar, operar y extender todo el ecosistema de forma autónoma sin depender de ninguna IA, consulta los manuales en la carpeta [`docs/`](docs/):

* 📖 **[El Gran Libro de Ágora (Manual Maestro)](docs/LIBRO_MAESTRO_AGORA.md)**: Vista de pájaro, mapa mental del ecosistema, replicación paso a paso en una máquina limpia y cheatsheet de comandos diarios.
* ⚡ **[Manual Completo de Ollama Autónomo](docs/MANUAL_OLLAMA_AUTONOMO.md)**: Arquitectura demonio-cliente, puertos, variables de entorno, gestión de modelos en disco/VRAM, GPU AMD Radeon y servicios systemd.
* 🤖 **[Arquitectura del Motor de Agentes y el LLM](docs/ARQUITECTURA_AGENTES_Y_LLM.md)**: Cómo el código Python se comunica con el LLM, el ciclo ReAct, llamadas a herramientas con esquemas JSON y gestión de memoria de contexto.
* 🧩 **[Guía de Creación de Agentes y Subagentes](docs/GUIA_CREACION_AGENTES_Y_SUBAGENTES.md)**: Fábrica de agentes de LangGraph, tutorial práctico para crear nuevos subagentes especializados y buenas prácticas de prompts.
* 📱 **[Pasarela de Entrada (Telegram) y Multiusuario](docs/TELEGRAM_Y_MULTIUSUARIO.md)**: Configuración de Telegram Bot API, BotFather, seguridad por ID numérico, perfiles Principal A/B y consola CLI interactiva.
* 🔌 **[MCP y Servicios Externos](docs/MCP_Y_SERVICIOS_EXTERNOS.md)**: Protocolo MCP, FastMCP en Raspberry Pi, integración con Homebox, Spoolman, Home Assistant y Docker.
* 🎯 **[Guía de Modelos Recomendados](docs/MODELS_RECOMMENDATION.md)**: Comparativa de rendimiento de modelos locales para la GPU AMD Radeon RX 7900 GRE (16 GB).

---

## 📜 Visión General del Nombre & Arquitectura

En la antigua Grecia, el **ágora** era la plaza pública central donde los ciudadanos interactuaban y los especialistas acudían a ofrecer sus servicios.

En este repositorio, **Ágora** mapea de forma modular esa filosofía:
1. **Supervisores Principales (Principals)**: 
   - **Principal A** (Perfil Primario con contexto técnico y canal Telegram A).
   - **Principal B** (Perfil Secundario con contexto independiente y canal Telegram B).
   - Cada principal posee su propio contexto, su bóveda de almacenamiento/Obsidian aislada y sus permisos de seguridad.
2. **Sub-Agentes Especializados (Puestos del Ágora / Workers)**:
   - **Taller & Inventario Worker**: Inventario de piezas en Homebox y bobinas de filamento 3D en Spoolman.
   - **Domótica & Home Assistant Worker**: Sensores de temperatura, clima y control de luces.
   - **Hunter Worker**: Rastreador y evaluador de ofertas conectado a PulseHunter.
   - **SysAdmin Worker**: Diagnóstico e inspección de contenedores Docker del Homelab.
   - **Knowledge RAG Worker**: Búsqueda semántica en documentos y biblioteca técnica.

---

## 🏗️ Topología del Sistema

```text
                         📱 Telegram (Principal A)       📱 Telegram (Principal B)
                                     │                               │
                                     ▼                               ▼
                      ┌─────────────────────────────────────────────────────┐
                      │    🔀 Telegram Ingress (app/api/telegram_ingress.py) │
                      └──────────────────────┬──────────────────────────────┘
                                             │
                                             ▼
                      ┌─────────────────────────────────────────────────────┐
                      │    👑 Ágora Supervisor (app/agents/supervisor.py)    │
                      │         (Motor ReAct / LangGraph Orchestrator)      │
                      └──────┬───────────────────────┬──────────────────────┘
                             │                       │
           (Inferencia Local HTTP)             (MCP Protocol HTTP/SSE)
                             │                       │
                             ▼                       ▼
              ┌─────────────────────────────┐ ┌─────────────────────────────┐
              │  ⚡ Ollama Daemon (:11434)  │ │  🔌 Homelab-MCP (:8001)     │
              │  🎮 AMD Radeon RX 7900 GRE  │ │  🍓 Raspberry Pi 4 (Docker) │
              │  (Qwen 2.5 14B Instruct)    │ │  (Homebox, Spoolman, HA)    │
              └─────────────────────────────┘ └─────────────────────────────┘
```

---

## ⚡ Comandos Rápidos del Día a Día

```bash
# Iniciar todo el stack (Ollama + Bot Supervisor)
./start.sh

# Ver estado en tiempo real, consumo de VRAM y logs
./status.sh

# Detener todo y liberar la VRAM de la GPU al 100%
./stop.sh

# Probar Ágora directamente en consola (sin Telegram)
.venv/bin/python main.py cli principal_a
```
