#!/bin/bash

# Launch Scheduler UI - Starts the server and opens the interface in browser

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_PID_FILE="/tmp/scheduler-server.pid"

echo "🚀 Telegram-Notion Scheduler UI Launcher"
echo "=========================================="
echo ""

# Function to cleanup on exit
cleanup() {
    if [ -f "$SERVER_PID_FILE" ]; then
        PID=$(cat "$SERVER_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo ""
            echo "🛑 Fermando il server..."
            kill $PID 2>/dev/null || true
            rm -f "$SERVER_PID_FILE"
        fi
    fi
}

trap cleanup EXIT

# Check if server is already running
if [ -f "$SERVER_PID_FILE" ]; then
    OLD_PID=$(cat "$SERVER_PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "⚠️  Server già in esecuzione (PID: $OLD_PID)"
        echo ""
        echo "Premo Ctrl+C per fermare il server e l'UI"
        echo ""
    fi
fi

# Start the server
echo "📍 Avviando il server su http://localhost:5555"
echo ""

cd "$SCRIPT_DIR"
source venv/bin/activate

# Start server in background
python3 scheduler-server.py &
SERVER_PID=$!
echo $SERVER_PID > "$SERVER_PID_FILE"

# Wait for server to start
echo "⏳ Aspettando il server..."
sleep 2

# Open the UI in browser
echo "🌐 Aprendo l'interfaccia nel browser..."
open "file://$SCRIPT_DIR/scheduler-launcher.html"

echo ""
echo "✅ Server avviato con successo!"
echo ""
echo "📱 L'interfaccia si è aperta nel browser predefinito"
echo "🔗 URL: file://$SCRIPT_DIR/scheduler-launcher.html"
echo ""
echo "💡 Premi Ctrl+C per fermare il server"
echo ""

# Keep the script running
wait $SERVER_PID
