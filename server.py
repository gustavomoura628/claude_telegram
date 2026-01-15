#!/usr/bin/env python3
import os
import httpx
from mcp.server.fastmcp import FastMCP

# Load credentials from file or environment
def load_credentials():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        creds_path = os.path.join(os.path.dirname(__file__), "credentials.txt")
        if os.path.exists(creds_path):
            with open(creds_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("BOT_TOKEN="):
                        bot_token = line.split("=", 1)[1]
                    elif line.startswith("CHAT_ID="):
                        chat_id = line.split("=", 1)[1]

    return bot_token, chat_id

BOT_TOKEN, CHAT_ID = load_credentials()

# Track the last update_id to avoid processing duplicates
last_update_id = None

mcp = FastMCP("telegram")

@mcp.tool()
def send_message(message: str) -> str:
    """Send a message to the configured Telegram chat.

    Args:
        message: The message text to send (supports HTML formatting)
    """
    if not BOT_TOKEN or not CHAT_ID:
        return "Error: Telegram credentials not configured"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = httpx.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

    if response.status_code == 200:
        return "Message sent successfully!"
    else:
        return f"Error: {response.text}"


@mcp.tool()
def get_messages(mark_as_read: bool = True) -> str:
    """Get new messages from the Telegram chat.

    Args:
        mark_as_read: If True, marks messages as read so they won't be returned again.
                      Set to False to peek at messages without consuming them.

    Returns:
        A formatted string with new messages, or "No new messages" if none.
    """
    global last_update_id

    if not BOT_TOKEN:
        return "Error: Telegram credentials not configured"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    params = {"timeout": 0}
    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    response = httpx.get(url, params=params)

    if response.status_code != 200:
        return f"Error: {response.text}"

    data = response.json()

    if not data.get("ok"):
        return f"Error: {data}"

    updates = data.get("result", [])

    if not updates:
        return "No new messages"

    messages = []
    max_update_id = last_update_id

    for update in updates:
        update_id = update.get("update_id", 0)
        if max_update_id is None or update_id > max_update_id:
            max_update_id = update_id

        msg = update.get("message", {})

        # Only process messages from the configured chat
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if chat_id != CHAT_ID:
            continue

        text = msg.get("text", "")
        sender = msg.get("from", {}).get("first_name", "Unknown")

        if text:
            messages.append(f"[{sender}]: {text}")

    # Update the offset if marking as read
    if mark_as_read and max_update_id is not None:
        last_update_id = max_update_id

    if not messages:
        return "No new messages"

    return "\n".join(messages)


if __name__ == "__main__":
    mcp.run()
