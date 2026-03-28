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
│  │ Router  │ │  Lock   │ │ Scheduler │  │
│  │         │ │ Manager │ │           │  │
│  └─────────┘ └─────────┘ └───────────┘  │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌───────┐    ┌───────┐    ┌───────┐
│  ou   │    │ zeno  │    │ rumi  │
│ relay │    │ data  │    │pattern│
└───┬───┘    └───┬───┘    └───┬───┘
    │            │             │
    ▼            ▼             ▼
┌─────────┐  ┌───────┐   ┌────────┐
│   LLM   │  │ Vault │   │ Memory │
└─────────┘  └───────┘   └────────┘
```

## Dispatcher

The dispatcher is the microkernel. It:
- **Routes** messages to the appropriate agent
- **Manages locks** for shared resources
- **Schedules** periodic tasks (pattern analysis, index rebuild)
- **Recovers** pending operations on startup

The dispatcher contains no LLM calls. It's deterministic, testable, fast.

## Agents

Five agents, each with a name and role:

| Role | Name | Trigger | Reads | Writes |
|------|------|---------|-------|--------|
| relay | ou | Default — conversation | Memory | Messages |
| data | zeno | "search", "find", @zeno | Vault, Memory | — |
| agenda | cato | "schedule", @cato | Vault | Vault |
| action | hiro | "send", "execute", @hiro | — | External |
| pattern | rumi | Scheduled (04:00) | Messages | Memory |

Agents are stateless between invocations. All persistent state lives in Memory, Vault, or the message queue.

## Knowledge Stores

### Memory

Meta-knowledge about the user:

| Type | Purpose | Decay |
|------|---------|-------|
| `user` | Personal facts | Permanent |
| `feedback` | Working preferences | Permanent |
| `context` | Current focus | 14 days |

See [Memory](../memory/) for details.

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

The Data agent maintains a search index. Tags emerge through co-occurrence analysis by the Pattern agent.

## Message Queue

All communication flows through `messages.jsonl`:

```json
{"v":1,"id":"msg_abc","ts":"...","role":"user","content":"..."}
{"v":1,"id":"msg_def","ts":"...","role":"assistant","agent":"relay","content":"..."}
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
    ├── insights.jsonl    # Extracted patterns
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

- [Memory](../memory/) — How persistent memory works
- [Philosophy](../philosophy/) — Why this architecture
