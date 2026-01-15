#!/bin/bash
# Telegram Daemon for Claude Code
# Polls for messages and wakes up Claude only when needed
# Zero tokens while waiting - Claude isn't even running!

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POLL_SCRIPT="$SCRIPT_DIR/poll_messages.py"

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
