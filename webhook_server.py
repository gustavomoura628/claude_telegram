#!/usr/bin/env python3
"""
Telegram Webhook Server for Claude Code
Instant message delivery - no polling delay!
"""
import os
import sys
import json
import subprocess
import threading
import time
from datetime import datetime
import httpx
from flask import Flask, request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(SCRIPT_DIR, "credentials.txt")
OFFSET_FILE = os.path.join(SCRIPT_DIR, ".telegram_offset")
LAST_MSG_TIME_FILE = os.path.join(SCRIPT_DIR, ".telegram_last_msg_time")


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

app = Flask(__name__)

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

BOT_TOKEN, CHAT_ID = load_credentials()

def send_telegram_message(text):
    """Send a message via Telegram Bot API"""
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: No credentials configured")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    httpx.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

def save_offset(offset):
    """Save the last processed update_id"""
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))

def wake_claude(message_text, sender, time_info):
    """Wake up Claude Code to handle the message"""
    prompt = f"""TELEGRAM MESSAGE ARRIVED:

[{sender}] ({time_info}): {message_text}

Please read this message, respond appropriately via the Telegram MCP tool (send_message), and then exit with /exit so I can go back to sleep and wait for the next message."""

    # Run Claude in a subprocess
    subprocess.run(
        ["claude", "--continue", "--dangerously-skip-permissions", "--print"],
        input=prompt,
        text=True,
        cwd=SCRIPT_DIR
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates"""
    data = request.get_json()

    if not data:
        return "OK", 200

    # Extract message info
    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "")
    sender = message.get("from", {}).get("first_name", "Unknown")
    update_id = data.get("update_id", 0)
    msg_timestamp = message.get("date", 0)

    # Only process messages from the configured chat
    if chat_id != CHAT_ID:
        return "OK", 200

    if not text:
        return "OK", 200

    # Calculate time info
    time_str = format_timestamp(msg_timestamp)
    last_msg_time = load_last_msg_time()
    if last_msg_time is not None:
        delta = msg_timestamp - last_msg_time
        delta_str = format_time_delta(delta)
        time_info = f"{time_str}, {delta_str} since last msg"
    else:
        time_info = f"{time_str}, first msg"

    # Save offset and last message time
    save_offset(update_id)
    save_last_msg_time(msg_timestamp)

    print(f"[{sender}] ({time_info}): {text}")

    # Immediately acknowledge with time delta
    if last_msg_time is not None:
        thinking_msg = f"Message received ({delta_str} since last). Claude is thinking... 🧠"
    else:
        thinking_msg = "Message received. Claude is thinking... 🧠"
    send_telegram_message(thinking_msg)

    # Wake up Claude in a separate thread so we can return 200 quickly
    thread = threading.Thread(target=wake_claude, args=(text, sender, time_info))
    thread.start()

    return "OK", 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return "OK", 200

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: No bot token configured!")
        sys.exit(1)

    print("Starting Telegram Webhook Server...")
    print("Waiting for messages...")
    print("")
    print("Don't forget to:")
    print("1. Start ngrok: ngrok http 5000")
    print("2. Set webhook: python set_webhook.py <ngrok_url>")
    print("")

    app.run(host="0.0.0.0", port=5000, debug=False)
