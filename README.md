# 🏛️ Ágora — Ecosistema Multi-Agente Distribuido & Orquestador de Homelab

> **Ágora**: *Plaza central de intercambio agéntico (Agent2Agent Protocol & MCP Hub)*

## 📜 Visión General del Nombre & Arquitectura

En la antigua Grecia, el **ágora** era la plaza pública central donde los ciudadanos interactuaban y los especialistas acudían a ofrecer sus servicios.

En este repositorio, **Ágora** mapea de forma modular esa filosofía:
1. **Supervisores Principales (Principals)**: 
   - **Principal A** (Perfil Primario con contexto técnico y canal Telegram A).
   - **Principal B** (Perfil Secundario con contexto independiente y canal Telegram B).
   - Cada principal posee su propio contexto, su bóveda de almacenamiento/Obsidian aislada y sus permisos de seguridad.
2. **Sub-Agentes Especializados (Puestos del Ágora / Workers)**:
   - **Hunter Worker**: Rastreador y evaluador de ofertas conectado al servidor MCP de PulseHunter.
   - **SysAdmin Worker**: Diagnóstico e inspección de contenedores Docker del Homelab.
   - **Knowledge RAG Worker**: Búsqueda semántica en documentos y biblioteca técnica.

---

## 🏛️ Descubrimiento & Protocolos: MCP + A2A (Agent2Agent)

Cada sub-agente acude a la "plaza pública" (el protocolo A2A) publicando su **Agent Card** (`/.well-known/agent-card.json`), donde declara de forma transparente qué herramientas (*tools*) ofrece y qué contrato de entrada/salida requiere.

- **MCP (Model Context Protocol)**: Resuelve la comunicación **Agente ↔ Herramientas Locales** (PulseHunter, Docker SDK, Obsidian Vault).
- **A2A (Agent2Agent Protocol)**: Resuelve la comunicación **Supervisor ↔ Worker Remoto** entre diferentes máquinas (Raspberry Pi 4, PC Desktop RX 7900 GRE y futuro Mini PC).

---

## 🏗️ Topología del Sistema

```
                         📱 Telegram (Principal A)       📱 Telegram (Principal B)
                                     │                               │
                                     ▼                               ▼
                      ┌──────────────────────────────┬──────────────────────────────┐
                      │ 🏛️ Supervisor: Principal A   │ 🏛️ Supervisor: Principal B   │
                      │ • Contexto de Usuario A      │ • Contexto de Usuario B      │
                      │ • Vault: /Obsidian/PrincipalA│ • Vault: /Obsidian/PrincipalB│
                      └──────────────┬───────────────┴──────────────┬───────────────┘
                                     │                              │
                                     └──────────────┬───────────────┘
                                                    │ (Agent Cards / A2A Protocol)
                                                    ▼
                               ┌──────────────────────────────────────────┐
                               │     PLAZA CENTRAL DE TRABAJADORES        │
                               │                                          │
                               │  • 🎯 Hunter Worker (PulseHunter MCP)    │
                               │  • 🖥️ SysAdmin Worker (Homelab Docker)   │
                               │  • 📚 Knowledge RAG Worker (ChromaDB)   │
                               └──────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

- **Language / Framework**: Python 3.11+, LangGraph, LangChain, FastAPI.
- **Inferencia LLM**: Ollama (`qwen2.5:7b-instruct` / `14b` en AMD RX 7900 GRE vía ROCm `gfx1100`).
- **Memoria Canónica**: Markdown en Obsidian + Git (con índice secundario FTS5/Engram).
- **Control Gateways**: n8n (para ejecuciones deterministas y Wake-on-LAN en Raspberry Pi 4).

---

## 🚀 Puesta en Marcha

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/collsfco/agora.git
   cd agora
   ```
2. Crear el entorno virtual e instalar dependencias:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install langgraph langchain-ollama langgraph-checkpoint-sqlite python-telegram-bot httpx pydantic
   ```
3. Configurar variables en `.env`:
   ```ini
   TELEGRAM_BOT_TOKEN_PRINCIPAL_A=tu_token_a
   TELEGRAM_BOT_TOKEN_PRINCIPAL_B=tu_token_b
   OBSIDIAN_VAULT_PRINCIPAL_A=/home/colls/ObsidianVaults/PrincipalA
   OBSIDIAN_VAULT_PRINCIPAL_B=/home/colls/ObsidianVaults/PrincipalB
   ```
4. Ejecutar el servicio:
   ```bash
   python main.py
   ```
