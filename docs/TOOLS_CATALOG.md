# 🛠️ Ágora Agent Tools & MCP Capability Catalog

Este documento recopila todas las herramientas (*Tools*), integraciones MCP y capacidades conectadas a los Agentes Principales en **Ágora**.

---

## 📋 Resumen de Herramientas Registradas

| Herramienta | Tipo | Destino / Origen | Descripción |
| :--- | :--- | :--- | :--- |
| `get_system_status` | Local System / Docker | Linux / Docker Engine | Obtiene métricas de CPU, RAM, uso de disco y estado de los contenedores Docker del Homelab. |
| `restart_docker_container` | Safe Action | Docker Engine | Reinicia un contenedor Docker. Si es un contenedor crítico (`traefik`, `postgres`, `homeassistant`), exige confirmación humana previa. |
| `get_pulsehunter_jobs` | MCP Client (REST) | PulseHunter API (`:8000`) | Busca y filtra ofertas de empleo tech por tecnología (`search`), país (`country`) y modalidad (`is_remote`). |
| `get_pulsehunter_housing` | MCP Client (REST) | PulseHunter API (`:8000`) | Consulta propiedades y pisos en alquiler en Irlanda (`county`, `max_price`, `min_bedrooms`). |
| `list_pulsehunter_alerts` | MCP Client (REST) | PulseHunter API (`:8000`) | Lista todas las alertas activas de empleo o vivienda configuradas en el scheduler. |
| `trigger_pulsehunter_alert` | MCP Client (REST) | PulseHunter API (`:8000`) | Fuerza la ejecución inmediata de una alerta de rastreo por su ID bajo demanda. |
| `delete_pulsehunter_alert` | MCP Client (REST) | PulseHunter API (`:8000`) | Elimina permanentemente una alerta de búsqueda de PulseHunter. |
| `create_pulsehunter_alert` | MCP Client (REST) | PulseHunter API (`:8000`) | Crea una alerta de rastreo recurrente automatizada para empleo en PulseHunter. |
| `get_weather` | External Metric API | wttr.in Structured API | Obtiene la temperatura real, sensación térmica, humedad, viento y estado del tiempo directo. |
| `search_web` | External Service | Internet (DuckDuckGo Search) | Permite al agente buscar información en tiempo real en la web (noticias, artículos, docs). |
| `search_user_memory` | Disposable Index | SQLite FTS5 / Obsidian | Busca notas, hechos y decisiones pasadas en la bóveda privada de Markdown del Principal activo. |
| `save_memory_fact` | Obsidian Local IO | Bóveda Obsidian (`.md`) | Guarda una nota estructurada en la carpeta de Obsidian del usuario e indexa el contenido en SQLite. |
| `send_message_to_peer_principal` | Multi-User Ingress | Telegram Bot Channel | Enruta un mensaje o recordatorio al otro Principal autorizado en el sistema de forma segura. |

---

## 🏛️ Arquitectura de Ejecución

```mermaid
graph TD
    User([👤 Usuario / Telegram / CLI]) --> LLM([🧠 Ollama LLM qwen2.5:14b])
    LLM --> Router{🛠️ Supervisor Dispatcher}
    
    Router -->|Homelab| T1[get_system_status / restart_docker]
    Router -->|PulseHunter| T2[jobs / housing / alerts: list, run, delete, create]
    Router -->|Clima e Internet| T3[get_weather / search_web]
    Router -->|Memoria| T4[search_user_memory / save_memory_fact]
    Router -->|Inter-Agente| T5[send_message_to_peer_principal]
    
    T1 --> Docker[Docker Host]
    T2 --> Pulse[PulseHunter Backend :8000]
    T3 --> Web[Live APIs]
    T4 --> Obs[Bóvedas Obsidian + SQLite FTS5]
    T5 --> Tel[Telegram API Ingress]
```
