#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

AGORA_PID_FILE="$DIR/.agora.pid"

echo "========================================================"
echo "📊 ESTADO DEL STACK DE ÁGORA & VRAM"
echo "========================================================"

# 1. Ollama Server Status & VRAM
echo "🔹 [OLLAMA SERVER - Puerto 11434]:"
if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "   • Estado: 🟢 EN LÍNEA (http://localhost:11434)"
    echo "   • Modelos en VRAM (GPU):"
    
    # Intentar con ollama ps
    PS_OUTPUT=$(ollama ps 2>/dev/null || true)
    if echo "$PS_OUTPUT" | grep -q "NAME"; then
        echo "$PS_OUTPUT" | sed 's/^/      /'
    else
        echo "      (Ningún modelo cargado en memoria GPU actualmente)"
    fi
else
    echo "   • Estado: 🔴 DETENIDO (Servidor Ollama apagado)"
fi

# 2. Agora Bot Daemon Status
echo ""
echo "🔹 [ÁGORA BOT SUPERVISOR]:"
AGORA_PID=$(pgrep -f "python.*main.py" | head -n 1 || true)
if [ -n "$AGORA_PID" ]; then
    echo "   • Estado: 🟢 EN EJECUCIÓN (PID: $AGORA_PID)"
    PS_INFO=$(ps -p "$AGORA_PID" -o %cpu,%mem,etime --no-headers 2>/dev/null || true)
    if [ -n "$PS_INFO" ]; then
        echo "   • Consumo (CPU/RAM/Tiempo): $PS_INFO"
    fi
elif [ -f "$AGORA_PID_FILE" ] && kill -0 "$(cat "$AGORA_PID_FILE")" 2>/dev/null; then
    echo "   • Estado: 🟢 EN EJECUCIÓN (PID: $(cat "$AGORA_PID_FILE"))"
else
    echo "   • Estado: 🔴 DETENIDO"
fi

# 3. Logs recientes
echo ""
echo "========================================================"
echo "📝 ÚLTIMOS LOGS:"
if [ -f "$DIR/logs/agora.log" ]; then
    echo "--- Ágora ($DIR/logs/agora.log) ---"
    tail -n 4 "$DIR/logs/agora.log"
fi
if [ -f "$DIR/logs/ollama.log" ]; then
    echo "--- Ollama ($DIR/logs/ollama.log) ---"
    tail -n 3 "$DIR/logs/ollama.log"
fi
echo "========================================================"
