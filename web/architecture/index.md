---
title: Architecture
# Architecture

*How the pieces fit together.*

## Overview

```
┌─────────────────────────────────────────┐
│              Dispatcher                  │
│            (Microkernel)                 │
│  ┌─────────┐ ┌─────────┐ ┌───────────┐  │
│  │ Router  │ │  Lock   │ │ Lifecycle │  │
│  │         │ │ Manager │ │  Manager  │  │
│  └─────────┘ └─────────┘ └───────────┘  │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌───────┐    ┌───────┐    ┌───────┐
│  ou   │    │ zeno  │    │ rumi  │
│ relay │    │ data  │    │pattern│
└───┬───┘    └───┬───┘    └───────┘
    │            │
    ▼            ▼
┌─────────────────────────────────────────┐
│                  LLM                     │
│         (Anthropic API / local)          │
└─────────────────────────────────────────┘
```

## Dispatcher

The dispatcher is the microkernel. It:
- **Routes** messages to the appropriate agent
- **Manages locks** for shared resources
- **Supervises** agent lifecycle
- **Recovers** pending operations on startup

The dispatcher contains no LLM calls. It's deterministic, testable, fast.

## Agents

Five agents, each with a name and role:

| Role | Name | Trigger |
|------|------|---------|
| relay | ou | Default — handles conversation |
| data | zeno | "search", "find", "vault", @zeno |
| agenda | cato | "schedule", "tomorrow", @cato |
| action | hiro | "send", "execute", @hiro |
| pattern | rumi | Scheduled, background |

Agents are stateless between invocations. All persistent state lives in the vault or message queue.

## Vault

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
    ├── session_notes.jsonl
    ├── tag-weights.jsonl
    ├── .pending/         # Write-ahead log
    ├── vault/            # Primary vault
    └── rules/            # User-defined rules
```

## Further Reading

- [Data Formats](../design/04-data-formats.md)
- [Agent Prompts](../design/06-agent-prompts.md)


