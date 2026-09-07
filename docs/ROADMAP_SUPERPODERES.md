# 🚀 Ágora Superpoderes Roadmap (2026)

Este documento traza la evolución de capacidades, herramientas y especialización de subagentes para el ecosistema **Ágora**, ejecutándose localmente con aceleración hardware en **AMD Radeon RX 7900 GRE (16 GB VRAM ROCm)** sobre el modelo **`qwen2.5:14b-instruct`**, con capacidad de arquitectura híbrida (Fallback & Servicios en la nube vía Gemini / Imagen 3).

---

## 🏛️ Fase 1: Upgrade del Cerebro Principal
- [x] Despliegue de Ollama con ROCm (`gfx1100`).
- [ ] Descarga y activación de **`qwen2.5:14b-instruct`** (9.0 GB VRAM, 16k contexto nativo).
- [ ] Ajuste de `.env` y validación de *Function Calling* complejo con 14B.

---

## 🎨 Fase 2: Superpoderes Visuales & Generación de Imágenes (Nuevo)
- [ ] **Generación de Imágenes Híbrida**:
  - **Opción Nube (Google Imagen 3 / Gemini API)**: Uso de API Key de Google AI Studio / Google Cloud para generar imágenes ultra fotorrealistas con Imagen 3.
  - **Opción Local (ComfyUI / SDXL / FLUX.1 en GPU RX 7900 GRE)**: Generación 100% offline, gratuita y privada en local.
  - **Entrega en Telegram**: Envío directo de la foto renderizada vía `bot.send_photo()`.
- [ ] **Visión / OCR Multimodal**:
  - Enviar capturas de pantalla, facturas o diagramas por Telegram para análisis visual con Gemini 1.5 Flash / Qwen-VL.

---

## ⚡ Fase 3: Superpoderes de Comunicación & Entrada Multimodal
- [ ] **Telegram Voice Notes (Whisper Local)**:
  - Integración de `faster-whisper` corriendo en GPU.
  - El usuario envía audios por Telegram -> El agente transcribe al instante y procesa la orden.
- [ ] **Alertas Proactivas Programadas (Cron Heartbeat)**:
  - Resumen matutino a las 08:30: El tiempo de hoy, estado de los servidores y vacantes nuevas de empleo detectadas durante la noche.

---

## 💼 Fase 4: Superpoderes de Carrera & PulseHunter MCP
- [ ] **CV Tailor & Match Score**:
  - Comparador vectorial / LLM entre tu CV en Markdown y ofertas encontradas.
  - Generación de consejos de entrevista y cartas de presentación personalizadas.
- [ ] **Market Salary Intelligence**:
  - Análisis agregado de rangos salariales por tecnología (PHP, React, Python, Go) en Irlanda, España y UE.
- [ ] **Housing Tracker Proactivo**:
  - Alerta inmediata en Telegram cuando aparezca un piso por debajo de 1800€ con 2 habitaciones en Dublín.

---

## 🖥️ Fase 5: Superpoderes de Homelab & Red Remota
- [ ] **Conexión Raspberry Pi (SSH / Docker Socket Remoto)**:
  - Conexión directa desde Ágora al stack del Homelab en la Raspberry Pi.
- [ ] **Container Logs & Diagnosis**:
  - Herramienta para leer los últimos logs de cualquier contenedor que falle (`docker logs --tail 50 <service>`) y diagnosticar la causa raíz.
- [ ] **Automated Backup & Sync Verification**:
  - Comprobación de estado de Rclone y sincronización de carpetas de Obsidian con Google Drive / NAS.

---

## 📅 Fase 6: Superpoderes de Productividad & Vida Diaria
- [ ] **Google Calendar & Tasks MCP**:
  - Crear, consultar y mover eventos de agenda mediante comandos de voz o texto en Telegram.
- [ ] **Currency & Finance Converter**:
  - Conversión de divisas en tiempo real y seguimiento de tipos de cambio.
- [ ] **Smart Obsidian Knowledge Graph**:
  - El agente relaciona automáticamente notas nuevas con conceptos existentes en la bóveda creando enlaces tipo `[[Nota]]`.

---

## 👥 Fase 7: Malla de Subagentes Especializados (LangGraph Swarm)
- [ ] **Supervisor Dispatcher (qwen2.5:14b)**: Enrutador central inteligente.
- [ ] **Hunter Subagent**: Especialista en scraping, análisis de empleo y vivienda.
- [ ] **Guardian Subagent**: Monitorización 24/7 y mantenimiento del Homelab.
- [ ] **Scholar Subagent**: Gestión del conocimiento, resúmenes web y Obsidian.
- [ ] **Personal Assistant**: Recordatorios, clima y mensajes inter-principales.
