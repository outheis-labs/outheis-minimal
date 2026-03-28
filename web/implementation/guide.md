---
title: Guide
---

# Guide

*Getting started with outheis.*

## Requirements

- Python 3.11+
- Anthropic API key

## Installation

```bash
git clone https://github.com/outheis-labs/outheis-minimal.git
cd outheis-minimal
pip install -e ".[dev]"
```

## Setup

```bash
# Initialize configuration
outheis init

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

Edit `~/.outheis/human/config.json`:

```json
{
  "user": {
    "name": "your-name",
    "language": "en",
    "timezone": "Europe/Berlin",
    "vault": ["~/Documents/Vault"]
  }
}
```

## CLI Commands

### Daemon Control

```bash
outheis start       # Start dispatcher (background)
outheis start -f    # Start in foreground
outheis start -fv   # Foreground + verbose (shows tool calls)
outheis stop        # Stop dispatcher
outheis status      # Show status, PID, uptime
```

### Messaging

```bash
outheis send "Hello"              # Single message
outheis send "@zeno find notes"   # Direct to Data agent
outheis chat                      # Interactive mode (with history)
```

### Memory

```bash
outheis memory              # Show all memories
outheis memory --type user  # Show only user facts
```

### Rules

```bash
outheis rules         # Show all rules (system + user)
outheis rules relay   # Show relay agent rules
```

## Talking to outheis

Just talk naturally. Relay decides when to use tools:

| You say | What happens |
|---------|--------------|
| "hi" | Direct response |
| "was steht heute an?" | Uses check_agenda tool → Agenda agent |
| "wo wohne ich?" | Uses search_vault tool → Data agent |
| "! ich bin 54" | Saves to Memory (explicit marker) |

### Explicit Agent Mentions

Use `@name` for direct delegation:

| Mention | Agent | Use for |
|---------|-------|---------|
| @zeno | Data | Search vault explicitly |
| @cato | Agenda | Schedule queries |
| @hiro | Action | External actions (future) |

## Vault

Your vault is a directory of Markdown files:

```markdown
---
title: Project Alpha
tags: [active, client-work]
created: 2025-01-15
---
# Project Alpha

Status update...
```

### Recommended Structure

```
vault/
├── Agenda/
│   ├── Daily.md      # Today's schedule
│   ├── Inbox.md      # Unprocessed items
│   └── Exchange.md   # External sync
├── projects/
├── notes/
└── references/
```

## Configuration

`~/.outheis/human/config.json`:

```json
{
  "user": {
    "name": "string",
    "language": "en|de|...",
    "timezone": "Region/City",
    "vault": ["~/path/to/vault"]
  },
  "llm": {
    "provider": "anthropic"
  }
}
```

## Troubleshooting

### "Dispatcher not running"

```bash
outheis status   # Check if running
outheis start    # Start it
```

### Stale PID file

```bash
rm ~/.outheis/.dispatcher.pid
outheis start
```

### No API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Or add to ~/.bashrc / ~/.zshrc
```

### macOS: Daemon won't start in background

Use foreground mode:

```bash
outheis start -f &
```
