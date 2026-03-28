---
title: Design
---

# Design

*Technical foundations — the conceptual architecture before code.*

These documents capture the design rationale, not the implementation. They explain *why* outheis works the way it does, drawing from operating system research and distributed systems theory.

## Documents

### [Why OS Principles](01-why-os-principles)

The core insight: multi-agent AI systems face the same challenges that operating systems solved decades ago. Message passing, ownership semantics, fault isolation — these aren't arbitrary choices but proven solutions.

### [Systems Survey](02-systems-survey)

A technical survey of operating systems and their applicable concepts:

- **DragonFlyBSD** — LWKT, per-CPU queues, ownership semantics
- **Erlang/OTP** — Actor model, supervision trees, "let it crash"
- **seL4** — Capability-based access control
- **Plan 9** — Everything as filesystem
- **OpenBSD** — Privilege separation, pledge/unveil

Each section maps OS concepts to agent system equivalents.

### [Architecture](03-architecture)

The complete architecture specification:

- System structure and directory semantics
- Agent roles, ownership model, capabilities
- Message protocol and schema
- Dispatcher design
- Vault structure and tag semantics
- Configuration format

### [Data Formats](04-data-formats)

Detailed specification of all data formats:

- Message schema (TypeScript interface)
- Configuration structure
- Memory storage format
- Vault conventions
- Logging format

### [Related Work](05-related-work)

Survey of existing multi-agent frameworks and how outheis differs:

- AutoGPT, BabyAGI, CrewAI
- LangChain, LangGraph
- Academic approaches
- Why most frameworks fail under complexity

### [Agent Prompts](06-agent-prompts)

System prompt specifications for each agent:

- Common principles
- Role-specific instructions
- Capability boundaries
- Response formatting

---

These documents were developed through iterative discussion before implementation. They represent the *design* — the implementation may diverge as we learn.
