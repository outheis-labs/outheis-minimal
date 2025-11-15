---
title: outheis
---

# οὐθείς

*Nobody — and everybody who refuses to be captured.*

---

## The Name

When Odysseus escapes the Cyclops, he calls himself οὐθείς — *nobody*. It's a trick, but also a truth: by not being pinned to a name, he remains free.

outheis carries this idea into how we work with AI. Your conversations, your notes, your patterns of thought — they shouldn't be captured, profiled, monetized. They should serve *you*.

---

## What is outheis?

A personal AI assistant that runs on your terms.

Five agents, each with a role:

| Agent | Name | Role |
|-------|------|------|
| **Relay** | ou | Conversation partner, first contact |
| **Data** | zeno | Searches your vault, finds connections |
| **Agenda** | cato | Manages time, tasks, exchanges |
| **Action** | hiro | Executes external actions |
| **Pattern** | rumi | Observes, extracts insights over time |

They coordinate through messages. Your knowledge stays in a local vault — Markdown files you control. Nothing leaves without your intent.

---

## Why OS Principles?

The agents need to work together without conflict. This is a solved problem — operating systems have coordinated independent processes for decades.

outheis borrows from DragonFlyBSD, Erlang, OpenBSD, Plan 9:

| Principle | Meaning |
|-----------|---------|
| **Message Passing** | Agents communicate through messages, not shared state |
| **Ownership** | Each agent is responsible for one domain |
| **Append-Only Log** | Every message recorded, nothing silently lost |
| **Supervision** | Failures are contained and recovered |
| **Declared Capabilities** | No implicit access, everything explicit |

The technical foundation serves a larger purpose: *sovereignty over your own cognitive infrastructure*.

---

## The Vault

Your knowledge lives in Markdown files with YAML frontmatter. Plain text, portable, version-controllable.

```
vault/
├── Agenda/
│   ├── Daily.md
│   └── Inbox.md
├── projects/
│   └── current-work.md
└── notes/
    └── ideas.md
```

The Data agent indexes and searches. The Pattern agent observes what matters to you over time. Tags emerge through use — not assigned, but earned through co-occurrence.

---

## Learn More

- [Why OS Principles Apply](concept/01-why-os-principles.md)
- [Systems Survey](concept/02-systems-survey.md)
- [Architecture](concept/03-architecture.md)

---

*outheis is open source under AGPL-3.0.*
