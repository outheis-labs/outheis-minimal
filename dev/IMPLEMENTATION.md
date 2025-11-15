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
- [ ] **Housekeeping tasks** (Pattern agent, scheduled)
  - File rotation: messages.jsonl, session_notes.jsonl → archive/
  - Index maintenance: rebuild/optimize search index
  - Trigger schema migrations if pending
  - Cleanup: .pending/, stale locks, orphaned files
  - Configurable retention policies
- [x] **Scheduler in dispatcher** (no cron/launchd needed)
  - Dispatcher wakes Pattern agent at configured time
  - Platform-independent, runs wherever dispatcher runs
  - Default: 04:00 local time, configurable via `pattern_schedule`
- [ ] Tag harmonization
- [ ] Signal transport
- [ ] Web UI (localhost)

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
- ✓ Lock manager (socket + priority)
- ✓ Write-ahead logging
- ✓ CLI transport (init, start, stop, send, chat, status, pattern, migrate)
- ✓ Relay agent with LLM
- ✓ Agent stubs (data, agenda, action, pattern)
- ✓ GitHub Actions CI
- ✓ Test fixtures (vault)
