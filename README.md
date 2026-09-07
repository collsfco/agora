# 🏛️ Ágora — Ecosistema Multi-Agente Distribuido & Orquestador de Homelab

> **Ágora**: *Plaza central de intercambio agéntico (Agent2Agent Protocol & MCP Hub)*

## 📜 Visión General del Nombre & Arquitectura

En la antigua Grecia, el **ágora** era la plaza pública central donde los ciudadanos intercambiaban información y los especialistas acudían a ofrecer sus servicios. 

En este repositorio, **Ágora** mapea de forma literal esa filosofía:
1. **Supervisores Principales (Los Ciudadanos)**: 
   - **Agente Principal de Francisco** (Telegram Ingress A).
   - **Agente Principal de Tu Esposa** (Telegram Ingress B).
   - Cada uno posee su propio contexto, su perfil, su bóveda de Obsidian aislada y sus permisos de seguridad.
2. **Sub-Agentes Especializados (Puestos del Ágora)**:
   - **Hunter Worker**: Cazador de empleos y vivienda conectado al servidor MCP de PulseHunter.
   - **SysAdmin Worker**: Diagnóstico e inspección de contenedores Docker del Homelab.
   - **English Coach Worker**: Tutor de voz en inglés con transcripción local en GPU mediante *Faster-Whisper*.
   - **Knowledge RAG Worker**: Búsqueda semántica en documentos y libros de la biblioteca.

---

## 🏛️ Descubrimiento & Protocolos: MCP + A2A (Agent2Agent)

Cada sub-agente acude a la "plaza pública" (el protocolo A2A) publicando su **Agent Card** (`/.well-known/agent-card.json`), donde declara de forma transparente qué herramientas (*tools*) ofrece y qué contrato de entrada/salida requiere.

- **MCP (Model Context Protocol)**: Resuelve la comunicación **Agente ↔ Herramientas Locales** (PulseHunter, Docker SDK, Obsidian Vault).
- **A2A (Agent2Agent Protocol)**: Resuelve la comunicación **Supervisor ↔ Worker Remoto** entre diferentes máquinas (Raspberry Pi 4, PC Desktop RX 7900 GRE y futuro Mini PC).

---

## 🏗️ Topología del Sistema

```
                         📱 Telegram (Francisco)         📱 Telegram (Tu Esposa)
                                     │                               │
                                     ▼                               ▼
                      ┌──────────────────────────────┬──────────────────────────────┐
                      │ 🏛️ Agente Principal (Francisco)│ 🏛️ Agente Principal (Esposa) │
                      │ • Contexto & Notas de Francisco│ • Contexto & Notas de Esposa  │
                      │ • Vault Obsidian: /Obsidian/F/ │ • Vault Obsidian: /Obsidian/E/│
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
                               │  • 🇬🇧 English Coach (Whisper STT)       │
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
   git clone https://github.com/tu-usuario/agora.git
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
   TELEGRAM_BOT_TOKEN_FRAN=tu_token_bot_1
   TELEGRAM_BOT_TOKEN_ESPOSA=tu_token_bot_2
   OBSIDIAN_VAULT_PATH_FRAN=/home/colls/Documents/ObsidianVault/Francisco
   OBSIDIAN_VAULT_PATH_ESPOSA=/home/colls/Documents/ObsidianVault/Esposa
   ```
4. Ejecutar el servicio:
   ```bash
   python main.py
   ```
