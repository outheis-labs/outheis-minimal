# Configuration

Config file: `~/.outheis/human/config.json`

## Default Configuration

```json
{
  "user": {
    "name": "default",
    "language": "en",
    "timezone": "UTC",
    "vaults": []
  },
  "routing": {
    "threshold": 0.3,
    "data": ["vault", "search", "find", "note", "remember"],
    "agenda": ["calendar", "schedule", "appointment", "meeting", "tomorrow", "today"],
    "action": ["send", "email", "execute", "run", "import"]
  },
  "agents": {
    "relay": {"model": "claude-sonnet-4-20250514", "enabled": true},
    "data": {"model": "claude-sonnet-4-20250514", "enabled": true},
    "agenda": {"model": "claude-sonnet-4-20250514", "enabled": true},
    "action": {"model": "claude-sonnet-4-20250514", "enabled": true},
    "pattern": {"model": "claude-sonnet-4-20250514", "enabled": true}
  }
}
```

## Sections

### user

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | User display name |
| `language` | string | ISO language code (en, de, ...) |
| `timezone` | string | IANA timezone (Europe/Berlin, UTC, ...) |
| `vaults` | string[] | Paths to external vaults |

Primary vault is always `~/.outheis/human/vault/`. Additional vaults are read-only.

### routing

Keyword-based routing configuration. Messages are scored against keyword lists.

| Field | Type | Description |
|-------|------|-------------|
| `threshold` | float | Minimum score to route (0.0-1.0) |
| `data` | string[] | Keywords for Data agent |
| `agenda` | string[] | Keywords for Agenda agent |
| `action` | string[] | Keywords for Action agent |

If no agent scores above threshold, message goes to Relay.

### agents

Per-agent configuration.

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model identifier |
| `enabled` | bool | Whether agent is active |

## File Paths

| Path | Description |
|------|-------------|
| `~/.outheis/` | System directory |
| `~/.outheis/.dispatcher.pid` | Dispatcher PID file |
| `~/.outheis/.dispatcher.sock` | Lock manager socket |
| `~/.outheis/human/` | User data directory |
| `~/.outheis/human/config.json` | Configuration |
| `~/.outheis/human/messages.jsonl` | Message queue |
| `~/.outheis/human/insights.jsonl` | Extracted insights |
| `~/.outheis/human/session_notes.jsonl` | Session learning notes |
| `~/.outheis/human/tag-weights.jsonl` | Tag relevance weights |
| `~/.outheis/human/.pending/` | Write-ahead directory |
| `~/.outheis/human/vault/` | Primary vault |
| `~/.outheis/human/rules/` | User-defined rules |
