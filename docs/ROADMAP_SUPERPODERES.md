# 🚀 Ágora Superpoderes Roadmap (2026)

Este documento traza la evolución de capacidades, herramientas y especialización de subagentes para el ecosistema **Ágora**, ejecutándose en una **arquitectura híbrida**:
- **Cerebro Local Privado**: Aceleración hardware en **AMD Radeon RX 7900 GRE (16 GB VRAM ROCm)** con el modelo **`qwen2.5:14b-instruct`**.
- **Cerebro en la Nube (Google Gemini / Imagen 3)**: Fallback, generación visual y análisis de documentos gigantes mediante **Google AI Studio**.

---

## 🏛️ Fase 1: Upgrade del Cerebro Principal
- [x] Despliegue de Ollama con ROCm (`gfx1100`).
- [x] Descarga y activación de **`qwen2.5:14b-instruct`** (9.0 GB VRAM, 16k contexto nativo).
- [x] Ajuste de `.env` y validación de *Function Calling* complejo con 14B.

---

## ☁️ Fase 2: Integración Híbrida con Google Cloud & Gemini API (Plan Detallado)
- [ ] **Configuración de Google AI Studio**:
  - Obtención de API Key en [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) (incluida en el ecosistema Google One AI Premium).
  - Variable de entorno: `GEMINI_API_KEY=AIzaSy...` en `.env`.
- [ ] **Generación de Imágenes en la Nube (Google Imagen 3)**:
  - Tool `generate_image_gemini`: El usuario pide *"Genera una imagen fotorrealista de X"* -> El agente llama a Google Imagen 3 -> Descarga el PNG y lo envía por Telegram con `bot.send_photo()`.
- [ ] **Análisis de Documentos Gigantes & Visión Multimodal (Gemini 1.5 Flash / Pro)**:
  - Tool `analyze_large_document`: Capacidad para enviar PDFs de cientos de páginas, libros o transcripciones de vídeo aprovechando la ventana de contexto de 1 millón de tokens de Gemini.
- [ ] **Fallback Automático (Modo Alta Disponibilidad)**:
  - Si la máquina local está apagada o la GPU saturada en otras tareas (ej: gaming), el ingress de Telegram conmuta automáticamente al backend de Gemini en la nube.

---

## 🎨 Fase 3: Generación de Imágenes 100% Local (Opción Offline)
- [ ] **Despliegue de ComfyUI / SDXL / FLUX.1 en GPU AMD**:
  - Instalación de motor de difusión local con soporte ROCm en `http://localhost:8188`.
  - Tool `generate_image_local`: Generación privada y offline a 1024x1024 en ~2 segundos sin gastar cuota de API.

---

## ⚡ Fase 4: Superpoderes de Comunicación & Entrada Multimodal
- [ ] **Telegram Voice Notes (Whisper Local)**:
  - Integración de `faster-whisper` corriendo en GPU.
  - El usuario envía audios por Telegram -> El agente transcribe al instante y procesa la orden.
- [ ] **Alertas Proactivas Programadas (Cron Heartbeat)**:
  - Resumen matutino a las 08:30: El tiempo de hoy, estado de los servidores y vacantes nuevas de empleo detectadas durante la noche.

---

## 💼 Fase 5: Superpoderes de Carrera & PulseHunter MCP
- [ ] **CV Tailor & Match Score**:
  - Comparador vectorial / LLM entre tu CV en Markdown y ofertas encontradas.
  - Generación de consejos de entrevista y cartas de presentación personalizadas.
- [ ] **Market Salary Intelligence**:
  - Análisis agregado de rangos salariales por tecnología (PHP, React, Python, Go) en Irlanda, España y UE.
- [ ] **Housing Tracker Proactivo**:
  - Alerta inmediata en Telegram cuando aparezca un piso por debajo de 1800€ con 2 habitaciones en Dublín.

---

## 🖥️ Fase 6: Superpoderes de Homelab & Red Remota
- [ ] **Conexión Raspberry Pi (SSH / Docker Socket Remoto)**:
  - Conexión directa desde Ágora al stack del Homelab en la Raspberry Pi.
- [ ] **Container Logs & Diagnosis**:
  - Herramienta para leer los últimos logs de cualquier contenedor que falle (`docker logs --tail 50 <service>`) y diagnosticar la causa raíz.
- [ ] **Automated Backup & Sync Verification**:
  - Comprobación de estado de Rclone y sincronización de carpetas de Obsidian con Google Drive / NAS.

---

## 📅 Fase 7: Superpoderes de Productividad & Vida Diaria
- [ ] **Google Calendar & Tasks MCP**:
  - Crear, consultar y mover eventos de agenda mediante comandos de voz o texto en Telegram.
- [ ] **Currency & Finance Converter**:
  - Conversión de divisas en tiempo real y seguimiento de tipos de cambio.
- [ ] **Smart Obsidian Knowledge Graph**:
  - El agente relaciona automáticamente notas nuevas con conceptos existentes en la bóveda creando enlaces tipo `[[Nota]]`.

---

## 👥 Fase 8: Malla de Subagentes Especializados (LangGraph Swarm)
- [ ] **Supervisor Dispatcher (qwen2.5:14b)**: Enrutador central inteligente.
- [ ] **Hunter Subagent**: Especialista en scraping, análisis de empleo y vivienda.
- [ ] **Guardian Subagent**: Monitorización 24/7 y mantenimiento del Homelab.
- [ ] **Scholar Subagent**: Gestión del conocimiento, resúmenes web y Obsidian.
- [ ] **Personal Assistant**: Recordatorios, clima y mensajes inter-principales.
