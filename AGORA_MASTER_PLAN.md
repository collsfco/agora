# 🏛️ Plan Maestro de Implementación: Ágora Agent Mesh

> **Guía de Ejecución Paso a Paso por Fases Micro-Atómicas**  
> *Cada tarea está diseñada para ser completada y verificada de forma independiente en pocos minutos.*

---

## 📊 Resumen del Estado de las Fases

| Fase | Descripción | Estado |
| :--- | :--- | :--- |
| **Fase 0** | Entorno Base, GPU (ROCm) & Validación de Ollama | ⏳ **Siguiente** |
| **Fase 1** | Estructura del Repositorio `agora`, Entorno Virtual & Contratos | ⬜ Pendiente |
| **Fase 2** | Capa de Memoria: Bóvedas de Obsidian (Principal_A / Principal_B) + Índice FTS5 | ⬜ Pendiente |
| **Fase 3** | Sub-Agentes Workers (Homelab Docker & PulseHunter MCP) | ⬜ Pendiente |
| **Fase 4** | Supervisores Principals (Principal_A & Principal_B) con LangGraph | ⬜ Pendiente |
| **Fase 5** | Interfaz Telegram Ingress (Multiusuario / Chat IDs) | ⬜ Pendiente |
| **Fase 6** | Automatización & Despliegue con Systemd (Arranque 24/7) | ⬜ Pendiente |

---

## 🚀 FASE 0: Entorno Base, GPU (ROCm) & Validación de Ollama

> **Objetivo**: Asegurar que la AMD RX 7900 GRE esté acelerando Ollama correctamente y que el modelo `qwen2.5` anuncie soporte para herramientas (*function calling*).

- [ ] **Tarea 0.1: Verificación de ROCm & Permisos de Usuario**
  - Comprobar que el usuario pertenezca a los grupos `render` y `video`.
  - Verificar que `rocm-smi` y `rocminfo` detecten la arquitectura `gfx1100`.
- [ ] **Tarea 0.2: Configuración del Servicio Ollama**
  - Asegurar que Ollama use exclusivamente la GPU dedicada 7900 GRE (`HIP_VISIBLE_DEVICES=0`).
  - Validar que el servidor responda en `http://localhost:11434`.
- [ ] **Tarea 0.3: Descarga y Verificación del Modelo Base**
  - Asegurar la descarga de `qwen2.5:7b-instruct`.
  - Verificar mediante `ollama show` que el modelo anuncie la capacidad `tools`.

---

## 📦 FASE 1: Estructura del Repositorio `agora`, Entorno Virtual & Contratos

> **Objetivo**: Dejar listo el entorno de desarrollo Python en `/home/colls/github/agora` y los contratos estrictos de datos.

- [ ] **Tarea 1.1: Creación del Entorno Virtual e Instalación de Dependencias**
  - Crear `.venv` dentro de `agora/`.
  - Instalar: `langgraph`, `langchain-ollama`, `langgraph-checkpoint-sqlite`, `python-telegram-bot`, `httpx`, `pydantic`, `docker`.
- [ ] **Tarea 1.2: Configuración de Variables de Entorno (`.env`)**
  - Crear `.env.example` y `.env` con las rutas a los Vaults de Obsidian, tokens y endpoints.
- [ ] **Tarea 1.3: Definición de Contratos de Herramientas (`tools_contracts.py`)**
  - Definir los esquemas Pydantic con límites de salida (*output budgeting*) para Docker, PulseHunter y Memoria.

---

## 📚 FASE 2: Capa de Memoria: Bóvedas de Obsidian + Índice FTS5

> **Objetivo**: Establecer las carpetas locales de Obsidian para Principal_A y su Principal_B, e implementar la búsqueda ultraligera por texto.

- [ ] **Tarea 2.1: Estructura de Bóvedas de Obsidian en Disco**
  - Crear `/home/colls/ObsidianVaults/Principal_A/` (`00_Perfil`, `01_Proyectos`, `02_Memoria`).
  - Crear `/home/colls/ObsidianVaults/Principal_B/` (`perfil.md`, `notas.md`).
- [ ] **Tarea 2.2: Módulo de Lectura/Escritura de Notas (`tools/obsidian_io.py`)**
  - Crear funciones deterministas para leer y hacer append en archivos Markdown según el usuario activo.
- [ ] **Tarea 2.3: Índice de Búsqueda Rápida FTS5 / Engram (`tools/engram_fts5.py`)**
  - Crear el motor SQLite FTS5 para indexar las notas Markdown y permitir búsquedas sub-milisegundo.

---

## 🛠️ FASE 3: Sub-Agentes Workers (Homelab & PulseHunter)

> **Objetivo**: Crear los trabajadores especializados con límites de seguridad (*Human-in-the-loop*).

- [ ] **Tarea 3.1: Worker Homelab (`workers/homelab/`)**
  - Implementar lectura de contenedores Docker (`docker ps` truncado), CPU, RAM y temperatura.
  - Implementar acción de reinicio protegida (requiere confirmación para contenedores fuera de la allowlist).
- [ ] **Tarea 3.2: Worker PulseHunter (`workers/hunter/`)**
  - Conectar el cliente al servidor MCP existente de PulseHunter.
  - Crear funciones para consultar vacantes pendientes (`get_pending_jobs`) y comparar contra el CV en Obsidian.
- [ ] **Tarea 3.3: Pruebas Aisladas de Workers por Consola**
  - Validar que cada worker ejecute sus tools y devuelva resúmenes compactos sin alucinaciones.

---

## 👑 FASE 4: Supervisores Principals (Principal_A & Principal_B) con LangGraph

> **Objetivo**: Construir los grafos de decisión de LangGraph que coordinan a los sub-agentes según el usuario.

- [ ] **Tarea 4.1: Plantilla Base de Agente Reusable (`AgentFactory`)**
  - Implementar la función universal para instanciar sub-agentes con `ChatOllama(temperature=0)`.
- [ ] **Tarea 4.2: Grafo Supervisor de Principal_A (`principals/principal_a/router.py`)**
  - Configurar el router con política de memoria técnica profunda (*deep memory*) y acceso completo a Homelab y PulseHunter.
- [ ] **Tarea 4.3: Grafo Supervisor de la Principal_B (`principals/principal_b/router.py`)**
  - Configurar el router con política de memoria ligera (*light memory*), tono conversacional y permisos de solo lectura.
- [ ] **Tarea 4.4: Persistencia de Sesión con Checkpoints SQLite**
  - Configurar `langgraph-checkpoint-sqlite` en `data/checkpoints.sqlite` para pausar y reanudar tareas.

---

## 📱 FASE 5: Interfaz Telegram Ingress (Multiusuario)

> **Objetivo**: Conectar los bots de Telegram para interactuar con los agentes desde el móvil con enrutado por usuario.

- [ ] **Tarea 5.1: Módulo de Enrutado por `chat_id` / Tokens Separados**
  - Configurar los handlers de `python-telegram-bot` para dirigir los mensajes de Principal_A a su grafo y los de su principal_b al suyo.
- [ ] **Tarea 5.2: Filtro de Preguntas Efímeras vs. Hechos Persistentes**
  - Integrar la lógica que responde preguntas triviales sin tocar la memoria de Obsidian.
- [ ] **Tarea 5.3: Botones Interactivos de Confirmación (*Human-in-the-Loop*)**
  - Añadir soporte para botones inline en Telegram ante acciones de reinicio de servicios.

---

## ⚙️ FASE 6: Automatización & Despliegue con Systemd (24/7)

> **Objetivo**: Asegurar que Ágora arranque solo con el PC y se recupere automáticamente ante cualquier fallo.

- [ ] **Tarea 6.1: Creación del Servicio Systemd (`agora.service`)**
  - Escribir `/etc/systemd/system/agora.service` con reinicio automático (`Restart=always`).
- [ ] **Tarea 6.2: Habilitación y Prueba de Arranque**
  - Activar el servicio (`systemctl enable --now agora`).
  - Validar logs en tiempo real con `journalctl -u agora -f`.
- [ ] **Tarea 6.3: Preparación del Perfil para Futuro Mini PC (`profiles/desktop.yaml`)**
  - Dejar listo el archivo declarativo para cuando se incorpore el segundo nodo por red (A2A + WoL).
