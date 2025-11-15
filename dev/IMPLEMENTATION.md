# Coherence Review and Implementation Plan

## Architecture Overview

```
┌─────────────────────────────────────────┐
│              Dispatcher                  │
│            (Microkernel)                 │
│  - Routing (no LLM)                     │
│  - Agent lifecycle                      │
│  - Message queue management             │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌───────┐    ┌───────┐    ┌───────┐
│ relay │    │ data  │    │ ...   │
│ (ou)  │    │(zeno) │    │       │
└───┬───┘    └───┬───┘    └───────┘
    │            │
    ▼            ▼
┌─────────────────────────────────────────┐
│               LLM (CPU)                  │
│  - Anthropic API                        │
│  - Ollama (local)                       │
│  - ...                                  │
└─────────────────────────────────────────┘
```

| OS Concept | outheis Equivalent |
|------------|-------------------|
| Microkernel | Dispatcher |
| CPU | LLM (Anthropic, Ollama, ...) |
| Processes | Agents |
| IPC | messages.jsonl |

---

## 1. Document Coherence Analysis

### 1.1 Consistency Across Documents ✓

| Aspect | 03-architecture | 04-data-formats | 06-agent-prompts | Status |
|--------|-----------------|-----------------|------------------|--------|
| Agent names | ou, zeno, cato, hiro, rumi | — | ou, zeno, cato, hiro, rumi | ✓ Consistent |
| Agent roles | relay, data, agenda, action, pattern | — | relay, data, agenda, action, pattern | ✓ Consistent |
| Directory structure | `~/.outheis/human/` | `~/.outheis/human/` | `human/` | ✓ Consistent |
| Message queue | `messages.jsonl` | `messages.jsonl` | `messages.jsonl` | ✓ Consistent |
| Vault location | External + `human/vault/` | External + `human/vault/` | — | ✓ Consistent |
| Capability matrix | Table in §Access Control | — | Referenced | ✓ Consistent |

### 1.2 Resolved Cross-References

| From | To | Reference | Status |
|------|-----|-----------|--------|
| 04-data-formats | research-base | Temporalization of Order | ✓ Updated |
| 06-agent-prompts | research-base | Who Owns Experience? | ✓ Updated |
| 05-related-work | research-base | Temporalization of Order | ✓ Updated |

### 1.3 Issues Found and Resolved

**Issue 1: Related Work reference** ✓ Fixed
- Updated link to research-base

**Issue 2: Session notes schema** ✓ Fixed
- Added `session_notes.jsonl` schema to 04-data-formats

**Issue 3: Errors.jsonl** ✓ Fixed
- Clarified: errors go to messages.jsonl with `error: true` flag

---

## 2. Implementation Feasibility

### 2.1 Core Components

| Component | Complexity | Dependencies | MVP Priority |
|-----------|------------|--------------|--------------|
| Message queue (JSONL) | Low | None | P0 |
| Schema versioning | Low | Message queue | P0 |
| Dispatcher (keyword routing) | Low | Message queue | P0 |
| Transport (CLI) | Low | Message queue | P0 |
| Transport (Signal) | Medium | signal-cli, Message queue | P1 |
| Relay agent | Medium | LLM API | P0 |
| Data agent | Medium | Vault access, Index | P1 |
| Agenda agent | Medium | Data agent, Rules | P2 |
| Action agent | Medium | Network, Execution sandbox | P2 |
| Pattern agent | High | All agents, Generalization logic | P3 |
| Web UI | Medium | All components | P3 |

### 2.2 MVP Definition

**Phase 0: Infrastructure**
- Message queue with schema versioning
- Dispatcher with keyword routing
- CLI transport

**Phase 1: Single Agent**
- Relay agent only (handles everything)
- Basic vault read
- No learning, no insights

**Phase 2: Data Separation**
- Data agent for vault operations
- Index management
- Relay delegates to Data

**Phase 3: Full System**
- Agenda, Action, Pattern agents
- Learning model
- Signal transport
- Web UI

### 2.3 Technical Decisions

| Decision | Options | Recommendation | Rationale |
|----------|---------|----------------|-----------|
| Language | Python, Rust, Go | **Python** | LLM libraries, rapid prototyping |
| LLM client | Raw HTTP, anthropic SDK, litellm | **anthropic SDK** | Official, typed |
| Filewatch | inotify, polling | **watchdog** (Python) | Cross-platform |
| CLI | argparse, click, typer | **typer** | Modern, typed |
| Config | JSON, YAML, TOML | **JSON** | As specified |

### 2.4 Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM costs exceed budget | High | Medium | Strict keyword routing, caching |
| Signal transport complexity | Medium | High | CLI-first, Signal later |
| Pattern agent generalization | High | High | Start with explicit rules only |
| Concurrent file access | Medium | Low | fcntl locking as specified |

---

## 3. Required Fixes Before Implementation

### 3.1 Document Updates

```
[ ] 05-related-work.md: Update reference to research-base
[ ] 04-data-formats.md: Add session_notes schema
[ ] 04-data-formats.md: Clarify errors.jsonl (or remove from 03)
```

### 3.2 Missing Specifications

```
[ ] CLI interface specification (commands, flags)
[ ] Config file complete schema
[ ] Agent spawn/lifecycle details
[ ] Graceful shutdown procedure
```

---

## 4. Proposed src/ Structure

```
src/
├── outheis/
│   ├── __init__.py
│   ├── __main__.py              # Entry point: python -m outheis
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── schema.py            # Version constants, migration
│   │   ├── message.py           # Message dataclass, serialization
│   │   ├── queue.py             # Append, read, lock
│   │   └── config.py            # Load/save config.json
│   │
│   ├── dispatcher/
│   │   ├── __init__.py
│   │   ├── router.py            # Keyword scoring, routing logic
│   │   ├── watcher.py           # Filewatch on messages.jsonl
│   │   └── lifecycle.py         # Agent spawn, notify, shutdown
│   │
│   ├── transport/
│   │   ├── __init__.py
│   │   ├── cli.py               # CLI interface
│   │   ├── signal.py            # Signal transport (future)
│   │   └── api.py               # HTTP API (future)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # Base agent class
│   │   ├── relay.py             # Relay agent
│   │   ├── data.py              # Data agent
│   │   ├── agenda.py            # Agenda agent
│   │   ├── action.py            # Action agent
│   │   └── pattern.py           # Pattern agent
│   │
│   ├── vault/
│   │   ├── __init__.py
│   │   ├── reader.py            # Read markdown, parse frontmatter
│   │   ├── writer.py            # Write with atomic rename
│   │   ├── index.py             # Build/query index
│   │   └── tags.py              # Tag extraction, normalization
│   │
│   └── cli/
│       ├── __init__.py
│       ├── main.py              # Typer app
│       ├── start.py             # outheis start
│       ├── stop.py              # outheis stop
│       ├── status.py            # outheis status
│       ├── send.py              # outheis send "message"
│       └── migrate.py           # outheis migrate --scan/--apply
│
├── tests/
│   ├── __init__.py
│   ├── test_schema.py
│   ├── test_queue.py
│   ├── test_router.py
│   └── ...
│
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 5. Immediate Next Steps

1. **Fix document issues** (see §3.1)
2. **Create src/ skeleton** with core/ only
3. **Implement message queue** with versioning
4. **Implement CLI transport** (send/receive)
5. **Implement dispatcher** (keyword routing)
6. **Implement relay agent** (LLM call)
7. **Test end-to-end**: CLI → Dispatcher → Relay → Response

---

## 6. Open Questions for Decision

1. **Daemon vs. CLI-driven?**
   - Option A: `outheis start` runs daemon, `outheis send` talks to it
   - Option B: `outheis chat` is interactive, no daemon
   - Recommendation: A (matches architecture), but B as fallback

2. **Signal transport priority?**
   - Option A: MVP with Signal
   - Option B: CLI-only MVP, Signal in Phase 2
   - Recommendation: B (reduce complexity)

3. **Local LLM support in MVP?**
   - Option A: Anthropic API only
   - Option B: Anthropic + Ollama from start
   - Recommendation: A (simpler), B via litellm later

