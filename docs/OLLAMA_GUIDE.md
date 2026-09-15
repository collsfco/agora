# Guía Básica de Gestión de Modelos en Ollama

Esta guía te ayudará a gestionar los modelos de lenguaje que utilizas con tu agente **Agora** u otras herramientas en tu Home Lab, utilizando el servidor local de Ollama.

## 📋 1. Listar Modelos Instalados

Para ver qué modelos tienes actualmente descargados en tu sistema y cuánto espacio ocupan, abre una terminal y ejecuta:

```bash
ollama list
```

**Salida esperada:** Una tabla con el nombre del modelo, su ID, su tamaño (en GB) y la fecha de última modificación.

## ⬇️ 2. Descargar (Instalar) Nuevos Modelos

Si deseas probar un nuevo modelo recomendado (por ejemplo `deepseek-r1:14b`), utiliza el comando `pull`:

```bash
ollama pull <nombre-del-modelo>
```
*Ejemplo:* `ollama pull deepseek-r1:14b`

> **Nota:** La descarga de modelos grandes puede tardar dependiendo de tu conexión. Si se interrumpe por algún motivo, puedes volver a ejecutar el mismo comando y continuará desde donde se detuvo.

## 🗑️ 3. Borrar (Desinstalar) Modelos

Los modelos pesados ocupan mucho espacio en el disco duro. Si ya no utilizas un modelo, es recomendable eliminarlo para liberar espacio:

```bash
ollama rm <nombre-del-modelo>
```
*Ejemplo:* `ollama rm qwen2.5:14b-instruct`

## 📁 4. ¿Dónde se ubican los modelos físicamente?

Aunque **siempre debes usar el comando `ollama rm` para borrar modelos**, es útil saber dónde guarda Ollama los archivos en tu sistema Linux.

Los archivos binarios (los "blobs" y "manifests") de los modelos se almacenan de forma predeterminada en el directorio oculto de tu usuario:

```text
/home/tu_usuario/.ollama/models/
```
En tu caso específico, la ruta exacta es: `/home/colls/.ollama/models/`

> [!WARNING]
> Nunca borres las carpetas manualmente desde el explorador de archivos o con comandos `rm` de Linux en este directorio, ya que podrías corromper la base de datos interna de Ollama. Utiliza siempre el comando `ollama rm <modelo>`.

## 🔄 5. Cambiar el modelo en Agora

Una vez descargado un nuevo modelo, para que Agora empiece a utilizarlo debes:
1. Ir al archivo de configuración `/home/colls/github/agora/.env`.
2. Actualizar la variable correspondiente: `OLLAMA_MODEL=deepseek-r1:14b`
3. Reiniciar el agente para que tome los cambios.
