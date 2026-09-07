# 🏛️ Plan Maestro de Implementación: Ágora Agent Mesh

> **Guía de Ejecución Paso a Paso por Fases Micro-Atómicas**  
> *Cada tarea está diseñada para ser completada y verificada de forma independiente en pocos minutos.*

---

## 📊 Resumen del Estado de las Fases

| Fase | Descripción | Estado |
| :--- | :--- | :--- |
| **Fase 0** | Entorno Base, GPU (ROCm) & Validación de Ollama | ✅ **Completada** |
| **Fase 1** | Estructura del Repositorio `agora`, Entorno Virtual & Contratos | ✅ **Completada** |
| **Fase 2** | Capa de Memoria: Bóvedas de Obsidian (Principal A / B / Shared) + Motor FTS5 | ⏳ **EN PROCESO (Siguiente)** |
| **Fase 3** | Sub-Agentes Workers (Homelab Docker & PulseHunter MCP) | ⬜ Pendiente |
| **Fase 4** | Supervisores Principals (Principal A & B) con LangGraph | ⬜ Pendiente |
| **Fase 5** | Interfaz Telegram Ingress (Multiusuario & Mensajes Inter-Principal) | ⬜ Pendiente |
| **Fase 6** | Automatización & Despliegue con Systemd (Arranque 24/7) | ⬜ Pendiente |

---

## 🚀 FASE 0: Entorno Base, GPU (ROCm) & Validación de Ollama
> **Estado**: ✅ **COMPLETADA**

- [x] **Tarea 0.1: Verificación de ROCm & Permisos de Usuario**
  - Usuario verificado en grupos `render` y `video`.
- [x] **Tarea 0.2: Configuración del Servicio Ollama**
  - Servidor Ollama verificado y respondiendo en `http://localhost:11434`.
- [x] **Tarea 0.3: Descarga y Verificación del Modelo Base**
  - Modelo `qwen2.5:7b-instruct` verificado con capacidad nativa de `tools`.

---

## 📦 FASE 1: Estructura del Repositorio `agora`, Entorno Virtual & Contratos
> **Estado**: ✅ **COMPLETADA**

- [x] **Tarea 1.1: Creación del Entorno Virtual e Instalación de Dependencias**
  - `.venv` creado con `langgraph`, `langchain-ollama`, `langgraph-checkpoint-sqlite`, `python-telegram-bot`, `pydantic`.
- [x] **Tarea 1.2: Configuración de Variables de Entorno (`.env`)**
  - Creado `config.py` tipado y `.env.example` con soporte para Principal A y Principal B.
- [x] **Tarea 1.3: Definición de Contratos de Herramientas (`tools_contracts.py`)**
  - Modelos Pydantic con límites de tokens para Docker, PulseHunter y Memoria.
- [x] **Tarea 1.4: Repositorio Remoto en GitHub**
  - Repositorio conectado y sincronizado en `https://github.com/collsfco/agora.git`.

---

## 📚 FASE 2: Capa de Memoria: Bóvedas de Obsidian + Índice FTS5
> **Estado**: ⏳ **SIGUIENTE A EJECUTAR**

- [ ] **Tarea 2.1: Estructura de Bóvedas en Disco Local**
  - Crear `/home/colls/ObsidianVaults/PrincipalA/` (`00_Perfil`, `01_Informes_Mercado`, `02_Memoria`).
  - Crear `/home/colls/ObsidianVaults/PrincipalB/` (`00_Perfil`, `01_Notas`).
  - Crear `/home/colls/ObsidianVaults/Compartido/` (`manuales`, `vivienda_criterios`).
- [ ] **Tarea 2.2: Módulo de Lectura/Escritura con Inyección de Contexto (`tools/obsidian_io.py`)**
  - Funciones seguras para leer y escribir Markdown según el `principal_id` activo.
- [ ] **Tarea 2.3: Motor de Búsqueda Rápida SQLite FTS5 (`tools/engram_fts5.py`)**
  - Motor de indexación ultraligero con aislamiento estricto `WHERE principal_id IN (?, 'shared')`.
- [ ] **Tarea 2.4: Script CLI de Reindexación (`cli.py reindex`)**
  - Comando para reconstruir la base de datos de búsqueda en 1 segundo desde los archivos Markdown.

---

## 🛠️ FASE 3: Sub-Agentes Workers (Homelab & PulseHunter)
> **Estado**: ⬜ Pendiente

- [ ] **Tarea 3.1: Worker Homelab (`workers/homelab/`)**
  - Lectura de contenedores Docker (`docker ps` truncado), CPU, RAM y temperatura.
  - Acción de reinicio protegida (*Human-in-the-Loop*).
- [ ] **Tarea 3.2: Worker PulseHunter (`workers/hunter/`)**
  - Cliente MCP para consultar vacantes (`get_pending_jobs`) y comparar contra el CV en Obsidian.
- [ ] **Tarea 3.3: Pruebas de Workers Aislados por Consola**

---

## 👑 FASE 4: Supervisores Principals (Principal A & B) con LangGraph
> **Estado**: ⬜ Pendiente

- [ ] **Tarea 4.1: Fábrica Base de Agentes (`AgentFactory`)**
- [ ] **Tarea 4.2: Grafo Supervisor Principal A (`principals/principal_a/router.py`)**
  - Política Deep Memory y acceso completo a Homelab y PulseHunter.
- [ ] **Tarea 4.3: Grafo Supervisor Principal B (`principals/principal_b/router.py`)**
  - Política Light Memory y permisos acotados.
- [ ] **Tarea 4.4: Persistencia con SQLite Checkpoints (`data/checkpoints.sqlite`)**

---

## 📱 FASE 5: Interfaz Telegram Ingress (Multiusuario)
> **Estado**: ⬜ Pendiente

- [ ] **Tarea 5.1: Enrutado por `chat_id` / Bots Separados**
- [ ] **Tarea 5.2: Mensajería Inter-Principal (`send_message_to_principal`)**
- [ ] **Tarea 5.3: Filtro de Preguntas Efímeras vs. Hechos Persistentes**
- [ ] **Tarea 5.4: Botones Inline de Confirmación para Acciones Críticas**

---

## ⚙️ FASE 6: Automatización & Despliegue con Systemd (24/7)
> **Estado**: ⬜ Pendiente

- [ ] **Tarea 6.1: Creación del Servicio Systemd (`agora.service`)**
- [ ] **Tarea 6.2: Habilitación y Validación de Arranque Automático**
- [ ] **Tarea 6.3: Perfil Declarativo para Futuro Mini PC (`profiles/desktop.yaml` / `minipc.yaml`)**
