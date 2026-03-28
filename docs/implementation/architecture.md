---
title: Architecture
---

# Architecture

*How the pieces fit together.*

## Overview

```
┌─────────────────────────────────────────┐
│              Dispatcher                  │
│            (Microkernel)                 │
│  ┌─────────┐ ┌─────────┐ ┌───────────┐  │
│  │ Watcher │ │  Lock   │ │ Scheduler │  │
│  │         │ │ Manager │ │           │  │
│  └─────────┘ └─────────┘ └───────────┘  │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    ▼             ▼             ▼             ▼
┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐
│  ou   │    │ zeno  │    │ cato  │    │ rumi  │
│ relay │    │ data  │    │agenda │    │pattern│
└───┬───┘    └───┬───┘    └───┬───┘    └───┬───┘
    │            │             │             │
    ▼            ▼             ▼             ▼
┌─────────┐  ┌───────┐   ┌────────┐   ┌────────┐
│   LLM   │  │ Vault │   │ Agenda │   │ Memory │
│ (Haiku) │  │       │   │  dir   │   │        │
└─────────┘  └───────┘   └────────┘   └────────┘
```

## Dispatcher

The dispatcher is the microkernel. It:
- **Watches** the message queue for changes
- **Manages locks** for shared resources
- **Schedules** periodic tasks (pattern analysis, index rebuild)
- **Recovers** pending operations on startup

The dispatcher contains no LLM calls. It's deterministic, testable, fast.

## Agents

Five agents, each with a name and role:

| Role | Name | When used | Reads | Writes |
|------|------|-----------|-------|--------|
| relay | ou | All messages — decides routing | Memory, Context | Messages |
| data | zeno | Vault search (via tool) | Vault, Memory | — |
| agenda | cato | Schedule queries (via tool) | Agenda/ | Agenda/ |
| action | hiro | External actions (future) | — | External |
| pattern | rumi | Scheduled (04:00) | Messages | Memory |

### Routing

Relay (ou) handles all user messages. It uses Haiku with tools:
- **search_vault** → delegates to Data agent (zeno)
- **check_agenda** → delegates to Agenda agent (cato)

No separate classification step. Relay decides intelligently based on the question and Memory.

Explicit mentions (@zeno, @cato) still work for direct delegation.

## Knowledge Stores

### Memory

Meta-knowledge about the user:

| Type | Purpose | Decay |
|------|---------|-------|
| `user` | Personal facts | Permanent |
| `feedback` | Working preferences | Permanent |
| `context` | Current focus | 14 days |

Stored in `~/.outheis/human/memory/`. See [Memory](memory.md) for details.

### Vault

The vault is a directory of Markdown files with YAML frontmatter:

```
vault/
├── Agenda/
│   ├── Daily.md      # Today's schedule
│   ├── Inbox.md      # Unprocessed items
│   └── Exchange.md   # External sync
├── projects/
│   └── *.md
└── notes/
    └── *.md
```

The Data agent maintains a search index.

## Message Queue

All communication flows through `messages.jsonl`:

```json
{"v":1,"id":"msg_abc","conversation_id":"conv_xyz","to":"dispatcher",...}
{"v":1,"id":"msg_def","conversation_id":"conv_xyz","to":"transport",...}
```

Append-only. Versioned. Recoverable.

## File Layout

```
~/.outheis/
├── .dispatcher.pid       # PID file
├── .dispatcher.sock      # Lock manager socket
└── human/
    ├── config.json       # Configuration
    ├── messages.jsonl    # Message queue
    ├── memory/           # Persistent memory
    │   ├── user.json
    │   ├── feedback.json
    │   └── context.json
    ├── .pending/         # Write-ahead log
    ├── vault/            # Primary vault
    └── rules/            # User-defined rules
```

## Scheduled Tasks

The dispatcher runs periodic tasks via built-in scheduler:

| Task | Time | Purpose |
|------|------|---------|
| `pattern` | 04:00 | Extract memories from conversations |
| `index_rebuild` | 04:30 | Rebuild vault search indices |
| `archive_rotation` | 05:00 | Archive old messages |

## Further Reading

- [Memory](memory.md) — How persistent memory works
- [Philosophy](../philosophy/) — Why this architecture
