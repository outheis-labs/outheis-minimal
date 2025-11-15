# Implementation Status

Work-in-progress tracking. Completed items are removed.

---

## Open Tasks

### Phase 1: Data Agent

- [ ] Implement vault search in Data agent
- [ ] Build search index (`index.jsonl`)
- [ ] Relay delegates vault queries to Data

### Phase 2: Agenda & Action

- [ ] Agenda agent: Daily.md, Inbox.md, Exchange.md
- [ ] Action agent: External imports
- [ ] User rules (`human/rules/`)

### Phase 3: Pattern & Polish

- [ ] Pattern agent: Session note review, insight extraction
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
