#!/bin/bash
# Polling loop that only outputs when there's a message
# This runs on the bash side, minimizing Claude's token usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POLL_INTERVAL="${1:-5}"  # Default 5 seconds for responsiveness

while true; do
    result=$(python3 "$SCRIPT_DIR/poll_messages.py" 2>/dev/null)

    if [ -n "$result" ]; then
        # Got a message! Output it and exit so Claude can respond
        echo "$result"
        exit 0
    fi

    # No message, loop silently without bothering Claude
    # The Python script already waited POLL_INTERVAL seconds via long polling
done
