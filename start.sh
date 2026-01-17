#!/bin/bash
# Claude Telegram Daemon Launcher
# Choose between webhook mode (instant, needs ngrok) or polling mode (simple, no setup)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    echo "Claude Telegram Daemon"
    echo ""
    echo "Usage: ./start.sh [mode]"
    echo ""
    echo "Modes:"
    echo "  poll      Polling mode (simple, ~5 sec delay)"
    echo "  webhook   Webhook mode (instant, needs ngrok running)"
    echo ""
    echo "Examples:"
    echo "  ./start.sh poll"
    echo "  ./start.sh webhook"
    echo ""
    echo "For webhook mode, first run 'ngrok http 5000' in another terminal,"
    echo "then run './start.sh webhook <ngrok_url>'"
}

start_polling() {
    echo "Starting in POLLING mode..."
    echo "Messages will be checked every ~5 seconds."
    echo ""

    # Make sure webhook is disabled
    python3 set_webhook.py --delete 2>/dev/null

    ./telegram_daemon.sh
}

start_webhook() {
    local ngrok_url="$1"

    if [ -z "$ngrok_url" ]; then
        # Try to auto-detect ngrok URL
        ngrok_url=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)
    fi

    if [ -z "$ngrok_url" ]; then
        echo "ERROR: No ngrok URL provided and couldn't auto-detect."
        echo ""
        echo "Either:"
        echo "  1. Start ngrok first: ngrok http 5000"
        echo "  2. Provide URL: ./start.sh webhook https://xxxx.ngrok.io"
        exit 1
    fi

    echo "Starting in WEBHOOK mode..."
    echo "Ngrok URL: $ngrok_url"
    echo ""

    # Set the webhook
    python3 set_webhook.py "$ngrok_url"
    echo ""

    # Start the server
    python3 webhook_server.py
}

# Parse arguments
case "${1:-}" in
    poll|polling)
        start_polling
        ;;
    webhook|hook)
        start_webhook "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo "Choose a mode:"
        echo ""
        echo "  1) Polling (simple, ~5 sec delay)"
        echo "  2) Webhook (instant, needs ngrok)"
        echo ""
        read -p "Enter choice [1/2]: " choice
        case "$choice" in
            1) start_polling ;;
            2) start_webhook ;;
            *) echo "Invalid choice"; exit 1 ;;
        esac
        ;;
    *)
        echo "Unknown mode: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
