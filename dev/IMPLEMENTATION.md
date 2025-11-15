# Implementation Status

Work-in-progress tracking. Completed items are removed.

---

## Open Tasks

### Phase 1: Data Agent — ✓ COMPLETE

- [x] Implement vault search in Data agent
- [x] Build search index (`index.jsonl`)
- [x] Relay delegates vault queries to Data

### Phase 2: Agenda & Action

- [ ] Agenda agent: Daily.md, Inbox.md, Exchange.md
- [ ] Action agent: External imports
- [ ] User rules (`human/rules/`)

### Phase 3: Pattern & Polish

- [ ] Pattern agent: Session note review, insight extraction
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

---

## Architecture Decisions

### Dispatcher Scheduler

The dispatcher includes a built-in scheduler for periodic tasks. This is more portable than relying on external schedulers (cron, launchd, systemd timers).

**Implementation:**
- Uses `select()` with timeout — no polling loop, no external dependencies
- Wakeup pipe for signal handling
- Timeout calculated from next scheduled task

**Scheduled tasks:**
- `pattern` (04:00): Run Pattern agent reflection
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

---

## Completed

Moved to `docs/` — see implementation documentation there.

- ✓ Core modules (schema, message, queue, config)
- ✓ Dispatcher daemon with routing
- ✓ Dispatcher scheduler (select-based, no polling)
- ✓ Lock manager (socket + priority)
- ✓ Write-ahead logging
- ✓ CLI transport (init, start, stop, send, chat, status, pattern, migrate)
- ✓ Relay agent with LLM
- ✓ Agent stubs (data, agenda, action, pattern)
- ✓ GitHub Actions CI
- ✓ Test fixtures (vault)
