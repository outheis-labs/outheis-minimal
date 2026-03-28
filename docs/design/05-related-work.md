# Related Work

This document surveys existing research on applying operating system principles to AI agent architectures.

---

## The Emerging Field

The application of OS concepts to AI agent systems is a nascent but growing research area. Recent work recognizes that agent architectures face challenges operating systems solved decades ago.

As one recent paper observes: "Today's agent architectures resemble the pre-OS era of computing—a chaos of duplicated solutions lacking fundamental abstractions for resource management, isolation, and coordination."

---

## Key Publications

### AIOS: LLM Agent Operating System

**Source**: arXiv 2403.16971, COLM 2025

The most directly relevant work. AIOS proposes an OS kernel for LLM-based agents with:

- Scheduler for dispatching agent requests
- Context manager with snapshot/restoration (analogous to process context switching)
- Memory manager for runtime operations
- Storage manager for persistence
- Access control for agent permissions

Key insight: LLMs are treated as cores, analogous to CPU cores, with a unified interface for diverse LLM endpoints.

**Difference from outheis**: AIOS focuses on multi-tenant agent serving with performance optimization. outheis focuses on personal assistant with privacy guarantees and plaintext data architecture.

### Agent Operating Systems (Agent-OS)

**Source**: Preprints.org, 2025

Proposes a layered architecture:

1. Kernel plane
2. Resource & Service plane
3. Agent Runtime plane
4. Orchestration & Workflow plane
5. User & Application plane

Emphasizes real-time guarantees and security primitives for autonomous systems.

**Difference from outheis**: Agent-OS targets enterprise/SmartTech scenarios with formal verification. outheis targets personal use with simplicity and transparency.

### Multi-Agent Memory from a Computer Architecture Perspective

**Source**: arXiv 2603.10062, 2026

Frames multi-agent memory as a computer architecture problem:

- Distinguishes shared vs. distributed memory paradigms
- Proposes three-layer hierarchy: I/O, cache, memory
- Identifies cache sharing and memory consistency as critical gaps

Key insight: "Agent performance is an end-to-end data movement problem."

**Relevance to outheis**: Validates our index-based access strategy and the distinction between hot (messages.jsonl) and cold (archive/) storage.

### Integrating AI into Operating Systems: A Survey

**Source**: arXiv 2407.14567, 2025

Comprehensive survey covering two directions:

1. **AI for OS**: ML/LLM techniques to enhance OS (scheduling, memory, security)
2. **OS for AI**: OS architecture innovations to support AI workloads

Identifies three paradigms:
- Kernel-level AI integration
- Agent-mediated workflows
- LLM-as-OS abstraction

**Relevance to outheis**: Confirms the validity of applying OS principles to agent design; provides vocabulary and framing.

### Modeling an Operating System Based on Agents

**Source**: Springer HAIS 2012

Early work proposing OS modeling with multi-agent paradigms, considering interaction-based computing and cloud computing.

**Relevance to outheis**: Shows this is not an entirely new idea, but predates the LLM era.

### The Orchestration of Multi-Agent Systems

**Source**: arXiv 2601.13671, 2026

Technical blueprint for enterprise multi-agent systems:

- Model Context Protocol (MCP) for tool access
- Agent-to-Agent (A2A) protocol for peer coordination
- Governance frameworks and observability

**Difference from outheis**: Focuses on enterprise orchestration with complex protocols. outheis uses simple message passing with append-only queue.

---

## Conceptual Parallels

| OS Concept | AIOS | Agent-OS | outheis |
|------------|------|----------|---------|
| Kernel | LLM kernel with modules | Layered planes | Dispatcher (no LLM) |
| Scheduling | FIFO, Round Robin | Real-time guarantees | Priority + keywords |
| Memory | K-LRU eviction | Three-layer hierarchy | Index + lazy load |
| IPC | System calls | Protocols (MCP, A2A) | Message queue (JSONL) |
| Access Control | Privilege groups | Security primitives | Capabilities (pledge/unveil) |
| Context Switch | Logits-based snapshot | Not specified | Conversation archival |

---

## What Distinguishes outheis

### 1. Privacy-First Architecture

Most related work assumes multi-tenant cloud deployment. outheis targets two modes: Personal Assistant (single-user, local-first) and Domain Expert Assistant (specialized knowledge service). Both prioritize privacy:

- User data only in `human/` and `vault/`
- Removing `human/` erases all user traces
- No telemetry, no cloud dependency (optional)

### 2. Plaintext Data Philosophy

Related work typically uses databases or specialized storage. outheis uses:

- Markdown files with tags (prospective information architecture)
- JSONL for structured data (messages, index, imports)
- Human-readable, tool-agnostic formats

This draws from Unix philosophy rather than database tradition.

### 3. Simplicity Over Performance

AIOS optimizes for throughput (2.1x faster execution). outheis optimizes for:

- Understandability (static dispatcher, no LLM in routing)
- Auditability (append-only log)
- Deployment flexibility (cloud minimal to local maximal)

### 4. Personal Agency

The Agenda agent concept—enabling user agency through intelligent filtering—is not present in enterprise-focused related work.

---

## Theoretical Foundations

The related work draws primarily from:

- **Distributed systems**: Message passing, consensus, fault tolerance
- **Operating systems**: Scheduling, memory hierarchy, access control
- **Software architecture**: Microservices, event sourcing

outheis additionally draws from:

- **Information science**: Prospective vs. retrospective architecture
- **Unix philosophy**: Plaintext, small tools, composability
- **Erlang/OTP**: Actor model, supervision, let-it-crash

---

## Open Research Questions

The literature identifies several open problems relevant to outheis:

1. **Memory consistency** in multi-agent systems
2. **Cache sharing** protocols across agents
3. **Context management** for long-running conversations
4. **Tag harmonization** via LLM (addressed in our theoretical work)

---

## References

1. Mei, K., Li, Z., et al. (2024). AIOS: LLM Agent Operating System. arXiv:2403.16971. COLM 2025.

2. Agent Operating Systems (Agent-OS): A Foundational Specification. Preprints.org, 2025.

3. Multi-Agent Memory from a Computer Architecture Perspective. arXiv:2603.10062, 2026.

4. Integrating Artificial Intelligence into Operating Systems: A Survey. arXiv:2407.14567, 2025.

5. Cámara, J.P., et al. (2012). Modeling an Operating System Based on Agents. HAIS 2012, Springer.

6. The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption. arXiv:2601.13671, 2026.

7. Ge, Y., et al. (2023). LLM as OS, Agents as Apps: Envisioning AIOS, Agents and the AIOS-Agent Ecosystem.

---

## Conclusion

The application of OS principles to AI agent architecture is an active research area. Existing work focuses primarily on performance optimization for enterprise multi-agent systems. outheis contributes a complementary perspective: privacy-first personal assistant architecture with plaintext data philosophy and emphasis on user agency.

The theoretical foundation linking prospective information architecture to agent design (see: [Temporalization of Order](https://github.com/outheis-labs/research-base/blob/main/temporalization-of-order/temporalization-of-order.md)) appears to be novel and not addressed in current literature.
