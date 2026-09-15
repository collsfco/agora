# Modelos Recomendados para Agora y MCP (AMD Radeon RX 7900 GRE - 16 GB VRAM)

Para erradicar por completo los problemas de razonamiento en tu agente conectado por MCP a tu Homelab, y considerando el limite fisico de los 16 GB de VRAM de tu AMD Radeon RX 7900 GRE, este documento resume las mejores opciones para ejecutar localmente en Ollama.

---

## Tabla Comparativa de Modelos

| Modelo | Ventaja Clave para tu MCP | Consumo de VRAM | Cuando elegirlo? |
| :--- | :--- | :--- | :--- |
| **deepseek-r1:14b** | Cero fallos de logica gracias al bloque de pensamiento tecnico (Chain of Thought). | ~9 GB (Muy holgado) | **Recomendado por defecto.** Razonamiento puro, analisis de materiales y stock sin alucinaciones. |
| **qwen2.5:14b-instruct** | Excelente balance de tool-calling rapido y seguimiento de instrucciones. | ~9 GB | Llamadas directas y respuestas rapidas. |
| **qwen2.5-coder:14b** | Especializado en codigo, scripting y configuracion de servidores. | ~9 GB | Automatizaciones intensivas y generacion de scripts. |

---

## Como Cambiar el Modelo Activo en Agora

1. **Descargar el modelo en Ollama:**
   ollama pull deepseek-r1:14b

2. **Editar la configuracion de Agora en .env:**
   OLLAMA_MODEL=deepseek-r1:14b

3. **Reiniciar el bot de Agora:**
   pkill -f 'agora/main.py'
   /home/colls/github/agora/.venv/bin/python /home/colls/github/agora/main.py &
