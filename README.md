# οὐθείς (outheis)

A multi-agent AI assistant built on proven operating system principles.

The concept is conceived for both personal assistant (1:1) and domain expert mode (many:1).

## The Problem

Current AI agent frameworks often reinvent solutions that operating systems solved decades ago: coordinating independent processes, managing communication, handling failures gracefully. Most do this poorly, leading to brittle architectures.

## The Insight

An operating system coordinates processes that must communicate without corrupting shared state, access resources without conflict, and fail gracefully. A multi-agent AI system has the same requirements.

Instead of reinventing, outheis applies proven concepts from OS research—message passing, ownership semantics, supervision—to agent coordination.

## Principles

- **Message Passing**: Agents communicate via messages, not shared state
- **Ownership**: Each agent owns its domain exclusively
- **Append-Only Log**: The message queue is immutable and auditable
- **Supervision**: Failed agents can be restarted without losing system state
- **Specialization**: Each agent does one thing well

## Documentation

**[→ outheis-labs.github.io/outheis-minimal](https://outheis-labs.github.io/outheis-minimal/)**

Design documents in [design/](design/):

- [Why OS Principles Apply](design/01-why-os-principles.md)
- [Systems Survey](design/02-systems-survey.md)
- [Architecture](design/03-architecture.md)
- [Data Formats](design/04-data-formats.md)
- [Related Work](design/05-related-work.md)
- [Agent Prompts](design/06-agent-prompts.md)

## Status

Prototype working. Conceptual makeover. New implementation ongoing.

## License

AGPL-3.0

## Acknowledgments

outheis draws inspiration from:

- [DragonFlyBSD](https://www.dragonflybsd.org/) — message passing architecture, LWKT, ownership semantics
- [Erlang/OTP](https://www.erlang.org/) — actor model, supervision trees, "let it crash" philosophy
- [OpenBSD](https://www.openbsd.org/) — pledge/unveil security model, privilege separation
- [seL4](https://sel4.systems/) — capability-based access control
- [Plan 9](https://9p.io/plan9/) — uniform resource interfaces
- [Apple Grand Central Dispatch](https://apple.github.io/swift-corelibs-libdispatch/) — priority-aware scheduling
- Event Sourcing pattern from the Domain-Driven Design community
