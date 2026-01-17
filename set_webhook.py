#!/usr/bin/env python3
"""
Set or remove the Telegram webhook URL
Usage:
  python set_webhook.py <ngrok_url>     # Set webhook
  python set_webhook.py --delete        # Remove webhook (go back to polling)
"""
import os
import sys
import httpx

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(SCRIPT_DIR, "credentials.txt")

def load_bot_token():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        if os.path.exists(CREDS_FILE):
            with open(CREDS_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("BOT_TOKEN="):
                        bot_token = line.split("=", 1)[1]
    return bot_token

def set_webhook(bot_token, url):
    """Set the webhook URL"""
    webhook_url = f"{url.rstrip('/')}/webhook"
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

    response = httpx.post(api_url, data={"url": webhook_url})
    result = response.json()

    if result.get("ok"):
        print(f"Webhook set successfully!")
        print(f"URL: {webhook_url}")
    else:
        print(f"Error: {result}")

def delete_webhook(bot_token):
    """Remove the webhook (go back to polling mode)"""
    api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"

    response = httpx.post(api_url)
    result = response.json()

    if result.get("ok"):
        print("Webhook deleted. Back to polling mode.")
    else:
        print(f"Error: {result}")

def get_webhook_info(bot_token):
    """Get current webhook info"""
    api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"

    response = httpx.get(api_url)
    result = response.json()

    if result.get("ok"):
        info = result.get("result", {})
        url = info.get("url", "")
        if url:
            print(f"Current webhook: {url}")
        else:
            print("No webhook set (polling mode)")
    else:
        print(f"Error: {result}")

if __name__ == "__main__":
    bot_token = load_bot_token()

    if not bot_token:
        print("Error: No bot token configured!")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Current status:")
        get_webhook_info(bot_token)
        print("")
        print("Usage:")
        print("  python set_webhook.py <ngrok_url>   # Set webhook")
        print("  python set_webhook.py --delete      # Remove webhook")
        sys.exit(0)

    arg = sys.argv[1]

    if arg == "--delete":
        delete_webhook(bot_token)
    else:
        set_webhook(bot_token, arg)
