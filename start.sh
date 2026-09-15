#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$DIR/logs"

echo "========================================================"
echo "🧠  INICIANDO ÁGORA (Ollama + Bot Supervisor)"
echo "========================================================"

# 1. Verificar/Iniciar Ollama
OLLAMA_PID_FILE="$DIR/.ollama.pid"
if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "⚡ Ollama ya está activo y respondiendo en http://localhost:11434"
else
    echo "⚡ Iniciando Ollama server en segundo plano..."
    setsid nohup ollama serve > "$DIR/logs/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    echo $OLLAMA_PID > "$OLLAMA_PID_FILE"
    disown $OLLAMA_PID 2>/dev/null || true
    echo "   ↳ Ollama lanzado (PID: $OLLAMA_PID). Esperando inicialización..."
    
    for i in {1..20}; do
        if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
fi

# 2. Verificar/Iniciar Ágora Daemon
AGORA_PID_FILE="$DIR/.agora.pid"
if [ -f "$AGORA_PID_FILE" ] && kill -0 "$(cat "$AGORA_PID_FILE")" 2>/dev/null; then
    echo "🤖 Ágora Daemon ya está corriendo (PID: $(cat "$AGORA_PID_FILE"))"
else
    echo "🤖 Iniciando Ágora Daemon (.venv/bin/python main.py)..."
    if [ ! -f "$DIR/.venv/bin/python" ]; then
        echo "❌ Error: No se encontró $DIR/.venv/bin/python. Crea el venv primero."
        exit 1
    fi
    cd "$DIR"
    setsid nohup "$DIR/.venv/bin/python" "$DIR/main.py" > "$DIR/logs/agora.log" 2>&1 &
    AGORA_PID=$!
    echo $AGORA_PID > "$AGORA_PID_FILE"
    disown $AGORA_PID 2>/dev/null || true
    echo "   ↳ Ágora lanzado en segundo plano (PID: $AGORA_PID)"
fi

sleep 2

echo ""
echo "========================================================"
echo "✨ ESTADO DEL STACK DE ÁGORA"
echo "========================================================"
echo "⚡ Ollama API:     http://localhost:11434"
if [ -f "$AGORA_PID_FILE" ] && kill -0 "$(cat "$AGORA_PID_FILE")" 2>/dev/null; then
    echo "🟢 Ágora Bot:      Corriendo (PID: $(cat "$AGORA_PID_FILE"))"
else
    echo "🟡 Ágora Bot:      Iniciándose (revisa $DIR/logs/agora.log)"
fi

echo ""
echo "📦 Modelos activos en VRAM:"
if command -v ollama >/dev/null 2>&1; then
    ollama ps 2>/dev/null || echo "   (Ningún modelo cargado en VRAM aún)"
fi

echo "========================================================"
echo "💡 Usa './status.sh' para ver VRAM y logs, './stop.sh' para detener y liberar GPU."
echo "========================================================"
