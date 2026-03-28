# Design

*Technical foundations — the conceptual architecture before code.*

These documents capture the design rationale, not the implementation. They explain *why* outheis works the way it does, drawing from operating system research and distributed systems theory.

## Documents

### [Why OS Principles](01-why-os-principles.md)

The core insight: multi-agent AI systems face the same challenges that operating systems solved decades ago. Message passing, ownership semantics, fault isolation — these aren't arbitrary choices but proven solutions.

### [Systems Survey](02-systems-survey.md)

A technical survey of operating systems and their applicable concepts:

- **DragonFlyBSD** — LWKT, per-CPU queues, ownership semantics
- **Erlang/OTP** — Actor model, supervision trees, "let it crash"
- **seL4** — Capability-based access control
- **Plan 9** — Everything as filesystem
- **OpenBSD** — Privilege separation, pledge/unveil

### [Architecture](03-architecture.md)

The complete architecture specification: system structure, agent roles, ownership model, message protocol, dispatcher design, vault structure, configuration format.

### [Data Formats](04-data-formats.md)

Detailed specification of all data formats: message schema, configuration structure, memory storage, vault conventions, logging format.

### [Related Work](05-related-work.md)

Survey of existing multi-agent frameworks and how outheis differs.

### [Agent Prompts](06-agent-prompts.md)

System prompt specifications for each agent: common principles, role-specific instructions, capability boundaries.
