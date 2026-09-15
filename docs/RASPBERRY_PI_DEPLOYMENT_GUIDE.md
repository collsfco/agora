# 🍓 Guía de Despliegue en Raspberry Pi 4 (ARM64): Servidores MCP y Homelab

Esta guía contiene la especificación completa de los **Servidores MCP para la Raspberry Pi 4**, el **catálogo exacto de herramientas (Tools)** que debe implementar cada uno, y todos los métodos para **compilar en tu PC potente y transferir imágenes a la Raspberry Pi (con y sin Docker Hub)**.

---

## 🏗️ 1. Arquitectura de Distribución

```
┌─────────────────────────────────────────────────────────┐
│               NODO 1: PC DEL AGENTE (POTENTE)           │
│             (Ágora + AMD RX 7900 GRE + Cómputo)         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🧠 Ágora Bot (Supervisor / Telegram)                   │
│  ⚡ Ollama (Qwen 2.5 14B en GPU AMD)                    │
│                                                         │
│  🌐 MCPs Pesados Locales en el PC:                      │
│     • Playwright MCP (Navegación Chromium / Capturas)   │
│     • Firecrawl MCP (Scraping de webs a Markdown)       │
│     • Generación de Imágenes (ComfyUI / Gemini API)     │
└────────────────────────────┬────────────────────────────┘
                             │
                             │ (Peticiones HTTP Red Local / VPN)
                             ▼
┌─────────────────────────────────────────────────────────┐
│              NODO 2: RASPBERRY PI 4 (24/7)              │
│               (Captura de Datos y Homelab)              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🐳 5 Stacks Docker:                                    │
│     • 01-infrastructure (Traefik, CrowdSec, Portainer)  │
│     • 02-automation (Home Assistant, Zigbee2MQTT)       │
│     • 03-workshop (Homebox, Spoolman)                   │
│     • 04-utilities (Homepage, n8n, Uptime Kuma)         │
│     • 05-media (qBittorrent, CUPS)                      │
│                                                         │
│  🔌 Servidores MCP en la Pi:                            │
│     • Homelab MCP (:8001) -> Control Docker y Salud     │
│     • PulseHunter MCP (:8000) -> Alertas y Scrapers     │
│     • Home Assistant MCP (:8123) -> Domótica e IoT      │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ 2. Catálogo Detallado de Tools por cada MCP de la Raspberry Pi

Cada MCP desplegado en la Raspberry Pi 4 expone un conjunto específico de herramientas atómicas:

### A. 🛡️ Homelab Manager MCP (`http://192.168.1.X:8001`)
*Acceso al socket de Docker (`/var/run/docker.sock:ro`) y métricas del sistema.*

| Herramienta (Tool) | Parámetros | Descripción / Acción |
| :--- | :--- | :--- |
| `get_homelab_overview` | *Ninguno* | Devuelve el resumen de salud de los 5 stacks: total de contenedores, cuántos están UP, cuántos caídos, uso total de RAM y temperatura de la CPU de la Pi. |
| `list_stack_containers` | `stack_name` (opcional: `01-infrastructure`, `02-automation`, `all`) | Lista detallada de contenedores del stack indicado con su estado (`running`, `exited`, `restarting`), puertos e imagen. |
| `get_container_logs` | `container_name: str`, `tail: int = 50` | Extrae las últimas N líneas de logs de un contenedor específico (útil para diagnosticar fallos en Traefik, CrowdSec, n8n, etc.). |
| `restart_homelab_service` | `container_name: str` | Reinicia de forma segura un contenedor específico que se haya quedado congelado. |
| `get_crowdsec_status` | *Ninguno* | Consulta a CrowdSec la lista de IPs baneadas activamente y alertas de intrusión detectadas en Traefik. |
| `get_storage_usage` | *Ninguno* | Muestra el espacio libre y ocupado en los discos/SSD montados en la Raspberry Pi. |

---

### B. 🎯 PulseHunter MCP (`http://192.168.1.X:8000`)
*Scrapers continuos en background de empleo y vivienda.*

| Herramienta (Tool) | Parámetros | Descripción / Acción |
| :--- | :--- | :--- |
| `fetch_pulsehunter_jobs` | `search: str`, `country: str`, `is_remote: bool`, `limit: int` | Busca ofertas de trabajo tecnológicas indexadas en la base de datos de PulseHunter. |
| `fetch_pulsehunter_housing` | `county: str`, `max_price: float`, `min_bedrooms: int`, `listing_type: str` | Consulta viviendas en alquiler o venta (Daft / MyHome) guardadas por los scrapers. |
| `list_pulsehunter_alerts` | `alert_type: str` (`job` o `housing`) | Lista todas las alertas periódicas activas configuradas. |
| `trigger_pulsehunter_alert` | `alert_id: int` | Dispara la ejecución inmediata asíncrona de un scraper (devuelve `202 Accepted` de inmediato). |
| `create_pulsehunter_alert` | `name: str`, `role: str`, `country: str`, `interval_min: int` | Programa una nueva alerta recurrente de empleo o vivienda. |
| `delete_pulsehunter_alert` | `alert_id: int` | Elimina una alerta de rastreo de la base de datos. |

---

### C. 🌿 Home Assistant MCP (`http://192.168.1.X:8123`)
*Conector nativo con la API de Home Assistant (Stack `02-automation`).*

| Herramienta (Tool) | Parámetros | Descripción / Acción |
| :--- | :--- | :--- |
| `get_entity_state` | `entity_id: str` (ej: `sensor.temperatura_salon`) | Lee el estado actual, valor o atributo de cualquier sensor o dispositivo. |
| `list_entities_by_domain` | `domain: str` (`light`, `switch`, `climate`, `sensor`) | Devuelve todos los dispositivos disponibles de un tipo en la casa. |
| `call_ha_service` | `domain: str`, `service: str`, `entity_id: str`, `data: dict` | Ejecuta una acción física (ej: encender/apagar luces, cambiar temperatura, disparar una escena). |

---

## ⚡ 3. Métodos para Compilar en tu PC y Transferir a la Raspberry Pi

Para evitar compilar en la Raspberry Pi 4 (lo cual tardaría 20-30 min), compilamos la imagen ARM64 en tu PC potente en 30 segundos y la pasamos a la Pi.

### Método A: Transferencia 100% Local por SSH (Sin Docker Hub ni Internet) — *Recomendado para Privacidad*

Este método no requiere ninguna cuenta ni subir imágenes a internet. Se hace en 1 línea por la red local:

```bash
# 1. En tu PC potente: Compilar para ARM64 y guardarla en tu Docker local
docker buildx build --platform linux/arm64 -t pulsehunter:local --load .

# 2. Enviar directamente la imagen por SSH al Docker de la Raspberry Pi:
docker save pulsehunter:local | ssh pi@192.168.1.X "docker load"
```

*Alternativa con archivo `.tar.gz`:*
```bash
# Guardar archivo comprimido en tu PC:
docker save pulsehunter:local | gzip > pulsehunter-arm64.tar.gz

# Copiar por SCP a la Pi:
scp pulsehunter-arm64.tar.gz pi@192.168.1.X:/home/pi/

# Cargar en la Pi:
ssh pi@192.168.1.X "docker load < /home/pi/pulsehunter-arm64.tar.gz"
```

---

### Método B: Vía Registro en la Nube (GitHub Container Registry / GHCR)

1. **Iniciar sesión en GHCR desde tu PC:**
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u collsfco --password-stdin
   ```
2. **Compilar para ARM64 y subir en un solo paso:**
   ```bash
   docker buildx build --platform linux/arm64 -t ghcr.io/collsfco/pulsehunter-backend:latest --push .
   ```
3. **En la Pi:**
   ```bash
   docker compose pull
   ```

---

## 📦 4. Despliegue en la Raspberry Pi 4 (`docker-compose.yml`)

En tu Raspberry Pi 4, añade el servicio dentro de tu estructura de stacks:

```yaml
services:
  pulsehunter:
    image: pulsehunter:local   # <-- Si usas el Método Local A (o ghcr.io/... si usas Método B)
    container_name: pulsehunter
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - DATABASE_URL=sqlite+aiosqlite:////data/pulsehunter.db
    volumes:
      - ./data:/data

  homelab-mcp:
    image: homelab-mcp:local
    container_name: homelab-mcp
    restart: unless-stopped
    ports:
      - "8001:8001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro  # Solo lectura para seguridad
```

### Arrancar en la Pi:
```bash
docker compose up -d
```
