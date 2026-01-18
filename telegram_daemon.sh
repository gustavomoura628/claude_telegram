#!/bin/bash
# Telegram Daemon for Claude Code
# Polls for messages and wakes up Claude only when needed
# Zero tokens while waiting - Claude isn't even running!

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POLL_SCRIPT="$SCRIPT_DIR/poll_messages.py"
CREDS_FILE="$SCRIPT_DIR/credentials.txt"

# Load credentials
if [ -f "$CREDS_FILE" ]; then
    BOT_TOKEN=$(grep "^BOT_TOKEN=" "$CREDS_FILE" | cut -d'=' -f2)
    CHAT_ID=$(grep "^CHAT_ID=" "$CREDS_FILE" | cut -d'=' -f2)
fi

send_thinking_message() {
    local delta="$1"
    local text
    if [ -n "$delta" ] && [ "$delta" != "first msg" ]; then
        text="Message received ($delta since last). Claude is thinking... 🧠"
    else
        text="Message received. Claude is thinking... 🧠"
    fi
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=$text" \
        -d "parse_mode=HTML" > /dev/null 2>&1
}

extract_time_delta() {
    # Extract the time delta from message format: [Name] (timestamp, DELTA since last msg): text
    # or [Name] (timestamp, first msg): text
    local msg="$1"
    if echo "$msg" | grep -q "first msg"; then
        echo "first msg"
    else
        # Extract between ", " and " since last msg"
        echo "$msg" | sed -n 's/.*(\([^,]*\), \([^)]*\) since last msg).*/\2/p' | head -1
    fi
}

echo "Starting Telegram daemon..."
echo "Claude Code will wake up when messages arrive."
echo "Press Ctrl+C to stop."
echo ""

cleanup() {
    echo ""
    echo "Shutting down daemon..."
    exit 0
}

trap cleanup SIGINT SIGTERM

while true; do
    # Poll for messages (this blocks for ~5 seconds if no message)
    message=$(python3 "$POLL_SCRIPT" 2>/dev/null)

    if [ -n "$message" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Message received: $message"
        echo "Sending thinking notification..."
        time_delta=$(extract_time_delta "$message")
        send_thinking_message "$time_delta"
        echo "Waking up Claude Code..."
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # Wake up Claude with the message as a prompt
        # Using --continue to preserve conversation context
        # --dangerously-skip-permissions for autonomous operation
        prompt="TELEGRAM MESSAGE ARRIVED:

$message

Please read this message, respond appropriately via the Telegram MCP tool (send_message), and then exit with /exit so I can go back to sleep and wait for the next message."

        echo "$prompt" | claude --continue --dangerously-skip-permissions --print

        echo ""
        echo "Claude finished. Returning to polling..."
        echo ""
    fi
done
