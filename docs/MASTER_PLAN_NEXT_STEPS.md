# 📋 Plan Maestro de Implementación de Ágora: Memoria, MCPs y Homelab

> **DOCUMENTO AUTOCONTENIDO PARA LA SESIÓN DE MAÑANA**
> Este documento contiene el contexto arquitectónico completo, las decisiones técnicas acordadas y la guía detallada de implementación paso a paso para continuar el desarrollo sin perder ningún detalle de sesiones anteriores.

---

## 🏛️ 1. Contexto Arquitectónico y Reparto de Nodos

Ágora opera en una **arquitectura distribuida de 2 Nodos** para balancear el consumo de cómputo y la alta disponibilidad 24/7:



---

## 🎯 2. Objetivos de Implementación (Orden de Prioridad)

---

### 🧠 FASE 1: Evolución de la Memoria de Ágora (Engram FTS5 -> Grafo + Semántica)

#### 1.1 Por qué se hace:
* **Problema actual:**  busca solo palabras clave literales. Si preguntas por *"Ender 3"*, no encuentra una nota enlazada llamada  si esta no repite la palabra *"Ender"*. Tampoco resuelve sinónimos (*"presión neumáticos"* vs *"psi ruedas"*).
* **Solución acordada ("Tercera Vía"):** Extender nuestro propio  sin migrar a librerías externas para conservar el aislamiento multiusuario (, , ) y la velocidad extrema (<2ms).

#### 1.2 Tareas Técnicas a Ejecutar:
1. **Paso 1: Tabla de Grafo  en SQLite:**
   * Archivo a modificar: .
   * En , añadir la tabla de aristas:
     sql: Error: No DBURL given

Usage:
sql [-hnr] [--table-size] [--db-size] [-p pass-through] [-s string] dburl [sqlcommand]
sql [-hnr] [--table-size] [--db-size] [-p pass-through] [-s string] dburl < sql_command_file

See 'man sql' for the options
   * En , extraer enlaces al leer cada archivo Markdown usando expresiones regulares para capturar wikilinks.
2. **Paso 2: Expansión de Vecindario de 1er Grado en :**
   * Al buscar una nota coincidente, hacer un  con  para traer automáticamente el título y snippet de las notas enlazadas directamente, enriqueciendo el contexto que se pasa a Qwen 14B.
3. **Paso 3: Capa Semántica Ligera (FastEmbed / Model2Vec):**
   * Incorporar embeddings locales con  para calcular similitud vectorial sobre las notas.
   * Fusionar los resultados de FTS5 (léxico) y Vector (semántico) mediante **RRF (Reciprocal Rank Fusion)**.
4. **Paso 4: Curaduría Semanal de Enlaces (Workflow n8n + Telegram):**
   * Configurar un webhook/worker que detecte notas huérfanas o recientes.
   * El modelo sugiere conexiones y envía a Telegram botones interactivos:  .

---

### 🌐 FASE 2: Conexión de MCPs de Navegación en el PC

#### 2.1 Playwright MCP (Navegación e Interacción Web)
* **Objetivo:** Permitir al agente abrir navegadores reales en segundo plano, rellenar formularios, hacer clics y capturar pantallas de cualquier web.
* **Archivos a crear/modificar:**
  * Configurar  en local.
  * Crear  para exponer:
    * : Abre y lee la página renderizada en JS.
    * : Captura y envía la imagen resultante al chat de Telegram.
    * : Rellena campos y envía formularios.

#### 2.2 Firecrawl MCP (Web Scraping Limpio a Markdown)
* **Objetivo:** Cuando el usuario envíe una URL larga (artículo, blog, documentación técnica), Firecrawl extrae solo el contenido esencial en Markdown puro para que Qwen 14B lo resuma sin basura publicitaria ni código HTML innecesario.
* **Tool:**  -> .

---

### 🏠 FASE 3: Despliegue en la Raspberry Pi 4 (Homelab MCP & PulseHunter)

#### 3.1 Flujo de Compilación (Sin saturar la Pi):
* Compilar las imágenes en el PC potente con Docker Buildx para ARM64:
  
* En la Raspberry Pi, configurar  para usar  y .

#### 3.2 Herramientas del Homelab MCP en la Pi ():
* : Salud general de los 5 stacks, temperatura de CPU de la Pi y RAM libre.
* : Lista contenedores UP/DOWN en , , etc.
* : Lectura de logs en vivo de Traefik, CrowdSec, n8n, etc.
* : Reinicio seguro de contenedores.
* : Lista de IPs bloqueadas activamente por el firewall.

---

## 🔒 3. Reglas de Seguridad Innegociables

1. **Secretos y Credenciales:** NUNCA se guardan contraseñas o tokens en notas de Obsidian (), ya que los modelos LLM y los logs de auditoría ingieren ese texto. Todo secreto reside exclusivamente en **Vaultwarden**.
2. **Socket de Docker en la Pi:** Siempre montado con  (Solo Lectura) en el contenedor MCP para evitar riesgos de escalada de privilegios.
3. **Aislamiento Multi-usuario:** Cualquier nueva tabla o consulta en Engram DEBE incluir la cláusula .

---

## 📁 4. Archivos Clave del Repositorio Ágora

* [](file:///home/colls/github/agora/app/agents/supervisor.py): Definición de Tools del LLM y Router de ejecución.
* [](file:///home/colls/github/agora/app/tools/engram_fts5.py): Motor SQLite de búsqueda y base del nuevo Grafo de Enlaces.
* [](file:///home/colls/github/agora/app/tools/obsidian_io.py): Escritura y lectura de notas Markdown con YAML frontmatter.
* [](file:///home/colls/github/agora/app/tools/pulsehunter_client.py): Cliente HTTP no bloqueante para el backend de PulseHunter.
* [](file:///home/colls/github/agora/docs/MCP_INTEGRATION_GUIDE.md): Guía de arquitectura y contratos de herramientas.
* [](file:///home/colls/github/agora/docs/RASPBERRY_PI_DEPLOYMENT_GUIDE.md): Manual paso a paso para el despliegue en la Pi 4.
* [](file:///home/colls/github/agora/docs/ASYNC_TASKS_PATTERN_GUIDE.md): Patrón de tareas en segundo plano (<10ms + Push).
