# CLI Reference

## Installation

```bash
pip install -e .
```

## Commands

### outheis init

Initialize outheis directories and default config.

```bash
outheis init
```

Creates:
- `~/.outheis/`
- `~/.outheis/human/`
- `~/.outheis/human/config.json`

### outheis start

Start the dispatcher daemon.

```bash
outheis start           # Background (daemonize)
outheis start -f        # Foreground (for debugging)
```

The dispatcher:
- Watches `messages.jsonl` for new messages
- Routes messages to agents
- Manages lock server on `~/.outheis/.dispatcher.sock`
- Recovers pending messages from `.pending/`

PID written to `~/.outheis/.dispatcher.pid`.

### outheis stop

Stop the dispatcher daemon.

```bash
outheis stop
```

Sends SIGTERM, waits for clean shutdown.

### outheis status

Show system status.

```bash
outheis status
```

Output:
```
outheis status
----------------------------------------
Dispatcher: running (PID 12345)

User: default
Language: en
Timezone: UTC
Primary vault: ~/.outheis/human/vault

Messages: 42
Queue size: 8192 bytes
```

### outheis send

Send a message and wait for response.

```bash
outheis send "What's on my agenda today?"
outheis send -t 60 "Complex question..."   # 60s timeout
```

Requires running dispatcher.

### outheis chat

Interactive chat session.

```bash
outheis chat
```

Type messages, receive responses. Exit with `exit`, `quit`, or Ctrl+C.

Requires running dispatcher.

### outheis pattern

Run Pattern agent manually (normally scheduled at 04:00).

```bash
outheis pattern            # Run reflection
outheis pattern --dry-run  # Show what would be done
```

Processes session notes, extracts insights, updates tag weights.

### outheis migrate

Schema migration for JSONL files.

```bash
outheis migrate --scan     # Show outdated records
outheis migrate --apply    # Apply migrations
outheis migrate -q         # Quiet mode
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key for LLM calls |
| `HOME` | Home directory (for `~/.outheis/`) |
