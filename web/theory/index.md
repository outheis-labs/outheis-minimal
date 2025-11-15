---
title: Theory
# Theory

*OS principles applied to agent coordination.*

## The Coordination Problem

Multiple agents working together face the same challenges as multiple processes in an operating system:

- **Concurrency** — agents may act simultaneously
- **Shared resources** — the vault, the message queue, external APIs
- **Failures** — network errors, API limits, bugs
- **Recovery** — the system must not lose state

Operating systems have solved these problems over decades. outheis applies their solutions.

## Message Passing

Agents communicate exclusively through messages. No shared memory, no direct calls.

This comes from Erlang/OTP and microkernel design. Benefits:
- Agents can fail independently
- State changes are explicit and logged
- Testing and debugging are straightforward

Every message is appended to `messages.jsonl`. The log is immutable — a complete audit trail.

## Ownership

Each agent owns a specific domain:

| Agent | Domain |
|-------|--------|
| Relay | User conversation |
| Data | Vault content, search index |
| Agenda | Time-bound items, scheduling |
| Action | External system interaction |
| Pattern | Cross-session insight extraction |

Ownership means responsibility: the Data agent maintains the search index, the Agenda agent manages the calendar view. No overlapping authority.

## Supervision

When an agent fails, it doesn't bring down the system. The dispatcher:

1. Detects the failure
2. Logs it
3. Restarts the agent with clean state
4. Resumes from the message queue

This is Erlang's "let it crash" philosophy. Failures are expected; recovery is designed in.

## Capabilities

Agents declare what they can access. No implicit permissions.

```json
{
  "agent": "action",
  "capabilities": ["vault:read", "http:external"]
}
```

If an agent tries to access something undeclared, the dispatcher blocks it. This makes the security model auditable.

## Append-Only Log

The message queue is append-only. Nothing is deleted or modified in place.

Benefits:
- **Recovery** — replay from any point
- **Debugging** — complete history available
- **Trust** — no silent mutations

This draws from database write-ahead logging and event sourcing.

## Further Reading

- [Systems Survey](../design/02-systems-survey.md) — DragonFlyBSD, Erlang, OpenBSD, Plan 9
- [Why OS Principles Apply](../design/01-why-os-principles.md)


