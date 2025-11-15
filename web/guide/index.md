---
title: Guide
# Guide

*Getting started with outheis.*

## Requirements

- Python 3.11+
- Anthropic API key (for now — local LLM support planned)

## Installation

```bash
git clone https://github.com/outheis-labs/outheis-minimal.git
cd outheis-minimal
pip install -e ".[dev,watch]"
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
    "vaults": ["~/notes"]
  }
}
```

## CLI Commands

### Daemon control

```bash
outheis start       # Start dispatcher (background)
outheis start -f    # Start in foreground
outheis stop        # Stop dispatcher
outheis status      # Show status, PID, uptime
```

The dispatcher runs as a background daemon. It watches the message queue, routes messages to agents, and schedules the Pattern agent (rumi) to run at a configured time (default: 04:00). No separate cron or launchd configuration needed — the scheduler is built into the dispatcher and works on all platforms.

### Messaging

```bash
outheis send "Hello"              # Single message
outheis send "@zeno find notes"   # Direct to Data agent
outheis chat                      # Interactive mode
```

### Maintenance

```bash
outheis pattern              # Run Pattern agent manually
outheis pattern --dry-run    # Preview without changes
outheis migrate --scan       # Check schema versions
```

## Agents

Address agents directly with `@name`:

| Mention | Agent | Use for |
|---------|-------|---------|
| @ou | Relay | General conversation |
| @zeno | Data | Search vault, find notes |
| @cato | Agenda | Schedule, calendar |
| @hiro | Action | External actions |
| @rumi | Pattern | Insight review |

Without explicit mention, routing is automatic based on keywords.

## Vault

Your vault is a directory of Markdown files:

```markdown
---
title: Project Alpha
tags: [active, client-work]
created: 2025-01-15
# Project Alpha

Status update...
```

The Data agent indexes and searches. Tags emerge over time through the Pattern agent's analysis.

### Recommended Structure

```
vault/
├── Agenda/
│   ├── Daily.md      # Today
│   ├── Inbox.md      # Capture
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
    "vaults": ["~/path/to/vault"]
  },
  "routing": {
    "threshold": 0.3,
    "data": ["search", "find", "vault"],
    "agenda": ["schedule", "tomorrow"],
    "action": ["send", "execute"]
  },
  "llm": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514"
  },
  "pattern_schedule": "04:00"
}
```

The `pattern_schedule` controls when the Pattern agent (rumi) runs its daily reflection. Format: `HH:MM` in local time.

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


