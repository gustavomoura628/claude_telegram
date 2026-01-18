#!/usr/bin/env python3
"""
Long-polling script for Telegram messages.
Waits for messages and outputs them, then exits.
Designed to be called repeatedly from a waiting loop.
"""
import os
import sys
import json
import time
from datetime import datetime
import httpx


def format_time_delta(seconds):
    """Convert seconds to human-readable time delta string."""
    if seconds < 0:
        return "0s"

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_timestamp(timestamp):
    """Convert Unix timestamp to readable datetime string."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OFFSET_FILE = os.path.join(SCRIPT_DIR, ".telegram_offset")
LAST_MSG_TIME_FILE = os.path.join(SCRIPT_DIR, ".telegram_last_msg_time")
CREDS_FILE = os.path.join(SCRIPT_DIR, "credentials.txt")

def load_credentials():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        if os.path.exists(CREDS_FILE):
            with open(CREDS_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("BOT_TOKEN="):
                        bot_token = line.split("=", 1)[1]
                    elif line.startswith("CHAT_ID="):
                        chat_id = line.split("=", 1)[1]

    return bot_token, chat_id

def load_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            try:
                return int(f.read().strip())
            except:
                return None
    return None

def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))


def load_last_msg_time():
    if os.path.exists(LAST_MSG_TIME_FILE):
        with open(LAST_MSG_TIME_FILE) as f:
            try:
                return int(f.read().strip())
            except:
                return None
    return None


def save_last_msg_time(timestamp):
    with open(LAST_MSG_TIME_FILE, "w") as f:
        f.write(str(timestamp))

def main():
    bot_token, chat_id = load_credentials()

    if not bot_token:
        print("ERROR: No bot token configured", file=sys.stderr)
        sys.exit(1)

    offset = load_offset()
    last_msg_time = load_last_msg_time()

    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    params = {
        "timeout": 5,  # Poll for 5 seconds for faster response
        "allowed_updates": ["message"]
    }

    if offset is not None:
        params["offset"] = offset + 1

    try:
        # Use a longer timeout for the HTTP client than the Telegram timeout
        response = httpx.get(url, params=params, timeout=60)
    except httpx.TimeoutException:
        # No messages, just exit quietly
        sys.exit(0)

    if response.status_code != 200:
        print(f"ERROR: {response.text}", file=sys.stderr)
        sys.exit(1)

    data = response.json()

    if not data.get("ok"):
        print(f"ERROR: {data}", file=sys.stderr)
        sys.exit(1)

    updates = data.get("result", [])

    if not updates:
        # No messages
        sys.exit(0)

    messages = []
    max_update_id = offset

    for update in updates:
        update_id = update.get("update_id", 0)
        if max_update_id is None or update_id > max_update_id:
            max_update_id = update_id

        msg = update.get("message", {})

        # Only process messages from the configured chat
        msg_chat_id = str(msg.get("chat", {}).get("id", ""))
        if msg_chat_id != chat_id:
            continue

        text = msg.get("text", "")
        sender = msg.get("from", {}).get("first_name", "Unknown")
        msg_timestamp = msg.get("date", 0)

        if text:
            time_str = format_timestamp(msg_timestamp)
            # Calculate time since previous message
            if last_msg_time is not None:
                delta = msg_timestamp - last_msg_time
                delta_str = format_time_delta(delta)
                messages.append(f"[{sender}] ({time_str}, {delta_str} since last msg): {text}")
            else:
                messages.append(f"[{sender}] ({time_str}, first msg): {text}")
            last_msg_time = msg_timestamp

    # Save the new offset and last message time
    if max_update_id is not None:
        save_offset(max_update_id)
    if last_msg_time is not None:
        save_last_msg_time(last_msg_time)

    if messages:
        print("\n".join(messages))
        sys.exit(0)
    else:
        # Updates but no relevant messages
        sys.exit(0)

if __name__ == "__main__":
    main()
