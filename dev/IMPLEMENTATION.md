# Implementation Status

Work-in-progress tracking. Completed items are removed.

---

## Open Tasks

### Phase 1: Data Agent — ✓ COMPLETE

- [x] Implement vault search in Data agent
- [x] Build search index (`index.jsonl`)
- [x] Relay delegates vault queries to Data

### Phase 1.5: Memory System — ✓ COMPLETE

- [x] Memory store (`core/memory.py`)
- [x] Pattern agent memory extraction
- [x] Explicit `!` marker for immediate storage
- [x] Temporal decay for context entries
- [x] Memory in agent system prompts

### Phase 2: Agenda & Action

- [ ] Agenda agent: Daily.md, Inbox.md, Exchange.md
- [ ] Action agent: External imports
- [ ] User rules (`human/rules/`)

### Phase 3: Pattern & Polish

- [ ] Pattern agent: Bot-chat analysis for behavioral patterns
- [ ] **Dynamic tag extraction with voting**
  - Extract candidate tags from vault content (YAKE/spaCy, local, fast)
  - Voting mechanism: tags gain weight through co-occurrence across documents
  - Prune single-instance/low-relevance tags automatically
  - Periodically re-evaluate as vault content changes
  - Result: bounded set of high-semantic-overlap tags
  - Store in `tag-weights.jsonl`, expose via Data agent
- [ ] Tag harmonization
- [ ] Signal transport
- [ ] Web UI (localhost)
  - [ ] Memory view and edit interface

---

## Architecture Decisions

### Memory System

Persistent memory about the user, separate from vault content.

**Memory vs. Vault:**
- **Memory** = Meta-level (about the user, working preferences, current context)
- **Vault** = Work content (documents, notes, projects)

**Memory Types:**

| Type | Purpose | Decay | Examples |
|------|---------|-------|----------|
| `user` | Personal facts | Permanent | "User is 35 years old", "Children: Leo, Emma" |
| `feedback` | Working preferences | Permanent | "Prefers short answers", "Respond in German" |
| `context` | Current focus | 14 days default | "Working on Project Alpha", "Preparing for trip" |

**Storage:**
```
~/.outheis/human/memory/
├── user.json
├── feedback.json
└── context.json
```

**Explicit Marker `!`:**
User can prefix messages with `!` to immediately store in memory:
- `! ich bin 35 jahre alt` → user memory
- `! bitte kurze Antworten` → feedback memory
- `! arbeite an Project X` → context memory (with decay)

Classification is automatic based on keywords.

**Temporal Awareness:**
- `context` entries expire after `decay_days` (default: 14)
- Temporary moods/stress are NOT stored as character traits
- Pattern agent cleans up expired entries during scheduled runs

**Memory Entry Fields:**
```python
@dataclass
class MemoryEntry:
    content: str
    type: MemoryType        # user/feedback/context
    created_at: datetime
    updated_at: datetime
    confidence: float       # 0-1
    source_count: int       # reinforcement counter
    decay_days: int | None  # None = permanent
    is_explicit: bool       # True if "!" marker used
```

**Integration:**
- Relay agent includes memory context in system prompt
- Pattern agent extracts memories during scheduled analysis (04:00)
- CLI: `outheis memory` to view/edit

### Dispatcher Scheduler

The dispatcher includes a built-in scheduler for periodic tasks. This is more portable than relying on external schedulers (cron, launchd, systemd timers).

**Implementation:**
- Uses `select()` with timeout — no polling loop, no external dependencies
- Wakeup pipe for signal handling
- Timeout calculated from next scheduled task

**Scheduled tasks:**
- `pattern` (04:00): Run Pattern agent reflection, extract memories
- `index_rebuild` (04:30): Rebuild vault search indices  
- `archive_rotation` (05:00): Rotate old messages to archive

**Why not external scheduler?**
- Different on every platform (cron, launchd, Task Scheduler)
- Dispatcher already runs as daemon
- `select()` timeout adds zero overhead when idle

---

## Open Questions

1. **Local LLM support?**
   - Current: Anthropic API only
   - Future: Ollama via litellm?

2. **Signal transport implementation?**
   - signal-cli or signal-cli-rest-api?
   - Polling interval?

3. **Web UI Memory Editor?**
   - Direct JSON edit vs. structured form?
   - Conflict resolution if Pattern agent updates during edit?

---

## Completed

Moved to `docs/` — see implementation documentation there.

- ✓ Core modules (schema, message, queue, config)
- ✓ Dispatcher daemon with routing
- ✓ Dispatcher scheduler (select-based, no polling)
- ✓ Lock manager (socket + priority)
- ✓ Write-ahead logging
- ✓ CLI transport (init, start, stop, send, chat, status, pattern, migrate, memory)
- ✓ Relay agent with LLM + memory context
- ✓ Data agent with vault search
- ✓ Pattern agent with memory extraction
- ✓ Memory system (core/memory.py)
- ✓ Explicit `!` marker for memory
- ✓ Agent stubs (agenda, action)
- ✓ GitHub Actions CI
- ✓ Test fixtures (vault)
