# Claude Code Telegram Daemon

Chat with Claude Code from your phone via Telegram - with **zero token cost while idle**.

## What Is This?

A daemon that lets you message Claude Code from Telegram. When you're not chatting, Claude isn't running at all (zero tokens). When a message arrives, it wakes up with full context, responds, and goes back to sleep.

**This isn't a dumbed-down chatbot.** When Claude wakes up, it has full Claude Code capabilities - read files, write files, run commands, use MCP tools. You can manage your computer from your phone.

## Two Modes

### Polling Mode (Simple)
```
┌─────────────────────────────────────────────────────┐
│  telegram_daemon.sh (bash loop)                     │
│                                                     │
│  while true:                                        │
│    poll Telegram every ~5 sec                       │
│    if message:                                      │
│      send "thinking..." instantly                   │
│      claude --continue --print                      │
│    back to polling                                  │
│  done                                               │
└─────────────────────────────────────────────────────┘
```
- No external dependencies
- ~5 second max delay between sending and receiving

### Webhook Mode (Instant)
```
┌──────────────────────────────────────────────────────┐
│  Telegram → ngrok → webhook_server.py                │
│                         │                            │
│                         ├─→ Instantly: "Thinking..." │
│                         └─→ claude --continue        │
└──────────────────────────────────────────────────────┘
```
- Instant message delivery
- Requires ngrok (or similar tunnel)

Both modes send an immediate "Claude is thinking..." message so you know your message was received.

## Prerequisites

- [Claude Code](https://claude.ai/code) installed and authenticated
- Python 3.7+
- `pip install -r requirements.txt`
- (For webhook mode) [ngrok](https://ngrok.com/) or similar tunnel

## Setup

### Step 1: Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name (e.g., "My Claude Bot")
4. Choose a username (must end in `bot`, e.g., `my_claude_bot`)
5. BotFather will give you a **Bot Token** - save this!

It looks like: `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Get Your Chat ID

Your bot needs to know which chat to read/write from. To find your chat ID:

1. **Send a message to your bot** on Telegram (just say "hi" or anything)
2. Open this URL in your browser (replace `YOUR_BOT_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Look for the `"chat":{"id":` field in the response:
   ```json
   {
     "ok": true,
     "result": [{
       "message": {
         "chat": {
           "id": 123456789,  ← This is your Chat ID
           "first_name": "Your Name",
           ...
         }
       }
     }]
   }
   ```

Your Chat ID is a number like `123456789`.

### Step 3: Create Credentials File

In the project directory, create `credentials.txt`:

```
BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CHAT_ID=123456789
```

Replace with your actual bot token and chat ID.

### Step 4: Configure Claude Code MCP

Add the Telegram MCP server to your Claude Code config. Edit `~/.claude.json` (or your Claude Code settings):

```json
{
  "mcpServers": {
    "telegram": {
      "command": "python3",
      "args": ["/full/path/to/this/repo/server.py"]
    }
  }
}
```

Replace `/full/path/to/this/repo/` with the actual path.

### Step 5: Initialize the Conversation

Before running the daemon, start an interactive Claude Code session in this directory:

```bash
cd /path/to/claude_telegram_mcp
claude
```

Have a brief conversation so Claude knows about the project and has context. Something like:

> "Hey, I've set up a Telegram daemon. You can send me messages via the telegram MCP tool. Let's test it - send me a hello!"

Once Claude successfully sends a Telegram message, exit the session. This creates the conversation context that `--continue` will use.

## Running

Use the launcher script:

```bash
./start.sh              # Interactive mode selector
./start.sh poll         # Polling mode (simple, ~5 sec delay)
./start.sh webhook      # Webhook mode (instant, auto-detects ngrok)
```

### Polling Mode
```bash
./start.sh poll
```
That's it! The daemon will poll for messages.

### Webhook Mode
```bash
# Terminal 1: Start ngrok
ngrok http 5000

# Terminal 2: Start the daemon
./start.sh webhook
```
The script auto-detects your ngrok URL. You can also specify it manually:
```bash
./start.sh webhook https://xxxx.ngrok.io
```

## Files

| File | Purpose |
|------|---------|
| `server.py` | MCP server with `send_message` and `get_messages` tools |
| `telegram_daemon.sh` | Polling mode daemon |
| `webhook_server.py` | Webhook mode server |
| `poll_messages.py` | Long-polls Telegram API (used by polling daemon) |
| `set_webhook.py` | Utility to set/remove Telegram webhook |
| `start.sh` | Launcher script to choose mode |
| `credentials.txt` | Your bot token and chat ID (don't commit!) |

## Security Notes

- **Don't commit `credentials.txt`** - it contains your bot token
- The daemon uses `--dangerously-skip-permissions` - Claude can do anything you can do
- Anyone with your bot token can send commands - keep it secret!

## How It Works

The magic is in combining three Claude Code features:

1. **MCP Tools**: Let Claude interact with external services (Telegram)
2. **`--continue`**: Preserves conversation context between invocations
3. **`--print`**: Non-interactive mode that auto-exits after responding

The daemon (polling or webhook) just waits for messages and pipes them to Claude. Claude does all the thinking.

## License

MIT - do whatever you want with it!
