# Claude Code Telegram Daemon

Chat with Claude Code from your phone via Telegram - with **zero token cost while idle**.

## What Is This?

A daemon that lets you message Claude Code from Telegram. When you're not chatting, Claude isn't running at all (zero tokens). When a message arrives, it wakes up with full context, responds, and goes back to sleep.

```
┌─────────────────────────────────────────────────────┐
│  telegram_daemon.sh (always running, tiny process)  │
│                                                     │
│  while true:                                        │
│    poll Telegram      ← sleeps here, zero tokens   │
│    if message:                                      │
│      claude --continue --print                     │
│      ↑ wakes up, full context, does its thing      │
│    back to sleep                                    │
│  done                                               │
└─────────────────────────────────────────────────────┘
```

**This isn't a dumbed-down chatbot.** When Claude wakes up, it has full Claude Code capabilities - read files, write files, run commands, use MCP tools. You can manage your computer from your phone.

## Prerequisites

- [Claude Code](https://claude.ai/code) installed and authenticated
- Python 3.7+
- `httpx` Python package (`pip install httpx`)

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

Add the Telegram MCP server to your Claude Code config. Edit `~/.claude/claude_desktop_config.json` (or your Claude Code settings):

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

## Running the Daemon

```bash
./telegram_daemon.sh
```

That's it! The daemon will poll for messages. When you send something via Telegram:
1. The daemon detects it
2. Launches `claude --continue --print --dangerously-skip-permissions`
3. Claude wakes up, sees your message, responds
4. Claude auto-exits, daemon goes back to polling

### Keeping It Running

The daemon stops if your computer sleeps or you close the terminal. Options:

- **Prevent sleep**: Use `caffeinate` (macOS) or disable sleep in settings
- **Run in tmux/screen**: `tmux new -s telegram-claude` then run the daemon
- **Run on a server**: Deploy to a VPS or Raspberry Pi that stays on

## Files

| File | Purpose |
|------|---------|
| `server.py` | MCP server with `send_message` and `get_messages` tools |
| `poll_messages.py` | Long-polls Telegram API for new messages |
| `telegram_daemon.sh` | Main daemon loop - polls and wakes Claude |
| `credentials.txt` | Your bot token and chat ID (don't commit this!) |

## Security Notes

- **Don't commit `credentials.txt`** - it contains your bot token
- The daemon uses `--dangerously-skip-permissions` - Claude can do anything you can do
- Anyone with your bot token can send commands - keep it secret!

## How It Works

The magic is in combining three Claude Code features:

1. **MCP Tools**: Let Claude interact with external services (Telegram)
2. **`--continue`**: Preserves conversation context between invocations
3. **`--print`**: Non-interactive mode that auto-exits after responding

The daemon is just a bash script that polls Telegram and pipes messages to Claude. Claude does all the thinking.

## License

MIT - do whatever you want with it!
