#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

AGORA_PID_FILE="$DIR/.agora.pid"
OLLAMA_PID_FILE="$DIR/.ollama.pid"

echo "========================================================"
echo "🛑 DETENIENDO ÁGORA Y LIBERANDO VRAM DE OLLAMA"
echo "========================================================"

# 1. Detener Ágora Bot Daemon
if [ -f "$AGORA_PID_FILE" ]; then
    PID=$(cat "$AGORA_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "⏹️  Deteniendo Ágora Bot Daemon (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        sleep 0.5
    fi
    rm -f "$AGORA_PID_FILE"
fi
pkill -f "python.*main.py" 2>/dev/null || true
echo "✅ Ágora Bot detenido."

# 2. Descargar modelos de Ollama de la VRAM
if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "🧹 Descargando modelos de la VRAM (keep_alive: 0)..."
    python3 -c "
import urllib.request, json
try:
    req = urllib.request.urlopen('http://127.0.0.1:11434/api/ps')
    data = json.loads(req.read().decode())
    for m in data.get('models', []):
        name = m.get('name')
        if name:
            print(f'   ↳ Liberando modelo: {name}')
            post_data = json.dumps({'model': name, 'keep_alive': 0}).encode('utf-8')
            unload_req = urllib.request.Request('http://127.0.0.1:11434/api/generate', data=post_data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(unload_req)
except Exception:
    pass
" 2>/dev/null || true
fi

# 3. Detener Ollama Server
if [ -f "$OLLAMA_PID_FILE" ]; then
    PID=$(cat "$OLLAMA_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "⏹️  Deteniendo Ollama Server (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
    fi
    rm -f "$OLLAMA_PID_FILE"
fi

pkill -f "ollama serve" 2>/dev/null || true
pkill -f "ollama_llama_server" 2>/dev/null || true

sleep 1
echo "✅ Ollama detenido y VRAM liberada al 100%."
echo "========================================================"
