---
title: Memory
---

# Memory

outheis remembers. Not everything — just what matters for working together well.

## Two stores

**Memory** holds meta-knowledge: who you are, how you work, what you're focused on.

**Vault** holds your content: documents, notes, projects.

Memory answers *who is this person?* Vault answers *what do they have?*

## Memory types

**user** — Personal facts. Your name, family, location, profession. Permanent until corrected.

**feedback** — Working preferences. Response style, language, format. Permanent until corrected.

**context** — Current focus. Active projects, upcoming events. Expires after 14 days by default.

## How memory forms

The Pattern agent runs nightly. It reads recent conversations, extracts what's worth remembering, discards what isn't.

Temporary moods don't become permanent traits. Stress on Tuesday doesn't define you on Wednesday.

For immediate storage, prefix with `!`:

```
! ich bin 35 jahre alt
! bitte kurze Antworten
! arbeite an Project Alpha
```

Classification is automatic.

## Rules

Rules are behavioral principles — how outheis should work with you.

There are two layers:

**System rules** define what agents can do. Architectural boundaries. Set by developers.

**User rules** define how agents should do it. Style, preferences. Emergent from interaction.

System rules live in code. User rules grow from memory.

When the Pattern agent sees consistent patterns — five requests for brevity, repeated corrections — it promotes them to rules. Rules shape all future interactions.

```
~/.outheis/human/rules/
├── common.md      # All agents
├── relay.md       # Conversation style
├── data.md        # Search behavior
└── ...
```

## Viewing

```bash
outheis memory          # View all memory
outheis memory --clear context   # Clear context entries
outheis rules           # View rules
outheis rules relay     # View relay rules only
```

## Coherent personality

outheis consists of five agents. You experience one assistant.

Memory and rules maintain this coherence. Common rules ensure consistent behavior. Agent-specific rules allow appropriate specialization. Over time, a stable personality emerges — not programmed, but grown.

Like an old friend who knows how you work.
