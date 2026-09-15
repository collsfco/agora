# Guía de Patrón de Tareas Asíncronas (Non-Blocking Tasks) para Herramientas de Agente y MCP

Esta guía documenta el patrón estándar de diseño para implementar herramientas de Agente o endpoints de MCP que ejecutan operaciones pesadas (que tardan más de 3-5 segundos), evitando bloqueos en la interfaz del usuario o timeouts HTTP.

---

## 🏗️ Los 3 Pilares del Patrón

```
[Cliente (Telegram / Front)] ──(1. POST Request)──> [Servidor Backend (FastAPI)]
                                                          │
[Cliente (Telegram / Front)] <──(2. 202 Accepted)────────┘  (Lanza BackgroundTask)
                                                                  │
                                                          (3. Ejecuta Scraper / Procesamiento)
                                                                  │
[Telegram / Web User] <───────(4. Push Notification / Webhook)───┘
```

1. **Aceptación Instantánea (<10ms):** El endpoint o tool expuesta no espera a que termine el trabajo pesado. Responde inmediatamente con HTTP `202 Accepted` y un cuerpo indicando `"status": "started"`.
2. **Ejecución en Segundo Plano (Non-Blocking):** Se utiliza `BackgroundTasks` de FastAPI (o Celery/APScheduler para procesos multinodo) para ejecutar la función de scraping, generación de documentos o análisis sin congelar el hilo principal.
3. **Notificación Push / Evento Final:** Al concluir la tarea en background, el servicio backend emite una notificación directamente al chat de Telegram del usuario o dispara un Webhook.

---

## 💻 Ejemplo de Implementación

### 1. En el Backend / Servidor MCP (FastAPI)

```python
from fastapi import APIRouter, BackgroundTasks, status

router = APIRouter()

@router.post("/heavy-task/{task_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_heavy_task(
    task_id: int, 
    background_tasks: BackgroundTasks
):
    """Lanza un trabajo pesado en segundo plano sin bloquear al cliente."""
    
    # 1. Encolar la función pesada en segundo plano
    background_tasks.add_task(process_heavy_job, task_id)
    
    # 2. Responder al instante en <10ms
    return {
        "status": "started",
        "task_id": task_id,
        "message": f"Tarea {task_id} iniciada en segundo plano."
    }

async def process_heavy_job(task_id: int):
    # Proceso pesado (ej. scraping de 30s, generación de PDF, etc.)
    results = await run_scraping_or_processing(task_id)
    
    # Notificación activa al usuario cuando finaliza
    await notifier_service.send_telegram_message(
        f"✅ ¡La tarea {task_id} ha finalizado! Se generaron {len(results)} elementos."
    )
```

---

### 2. En el Cliente de Herramientas del Agente (`pulsehunter_client.py`)

```python
async def execute_heavy_task_tool(task_id: int) -> str:
    url = f"{API_BASE}/heavy-task/{task_id}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(url)
        if res.status_code in (200, 201, 202):
            return f"🚀 Tarea {task_id} iniciada con éxito en segundo plano. El sistema notificará automáticamente al finalizar."
        return f"❌ Error iniciando la tarea: {res.text}"
```

---

### 3. En la Definición del Agente (`supervisor.py`)

```python
{
    "type": function,
    "function": {
        "name": "trigger_heavy_task",
        "description": "Ejecuta de forma asíncrona (en segundo plano) una tarea pesada de procesamiento o scraping.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID de la tarea a ejecutar"}
            },
            "required": ["task_id"]
        }
    }
}
```

---

## 🎯 Cuándo utilizar este patrón

Usar obligatoriamente este patrón en cualquier herramienta que:
* Realice **Web Scraping** dinámico (Playwright, Selenium, JobSpy, Daft, etc.).
* Descargue o procese **vídeos, audios o modelos pesados** (OCR, Whisper, etc.).
* Genere **informes pesados / PDFs** de analítica.
* Consuma **APIs externas** sin garantía de respuesta rápida (<2s).
