---
title: outheis
---

# οὐθείς

A multi-agent AI assistant built on proven operating system principles.

---

## What is outheis?

outheis is an AI assistant architecture that coordinates multiple specialized agents. Instead of one monolithic AI handling everything, different agents handle different tasks: data, actions, communication, scheduling, pattern recognition.

The challenge: how do these agents work together without stepping on each other?

## The Approach

We didn't invent new solutions. We borrowed from decades of operating system research.

Operating systems solve the same fundamental problem: independent processes that must communicate, share resources, and recover from failures. Systems like DragonFlyBSD, Erlang, OpenBSD, and Plan 9 have elegant, battle-tested answers.

outheis applies these patterns to AI agents.

## Core Principles

| Principle | Meaning |
|-----------|---------|
| **Message Passing** | Agents talk through messages, not shared memory |
| **Ownership** | Each agent is responsible for one domain |
| **Append-Only Log** | Every message is recorded, nothing is deleted |
| **Supervision** | If an agent fails, it restarts cleanly |
| **Secure by Default** | No implicit capabilities, all access declared |

## Learn More

- [Why OS Principles Apply to Agent Systems](concept/01-why-os-principles.md)
- [Survey of Relevant Systems](concept/02-systems-survey.md)

---

*outheis is open source under AGPL-3.0.*
