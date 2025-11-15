---
title: Implementation
---

# Implementation

*Concrete strategies and patterns. For developers and CS students.*

---

## Lock Management

Multiple agents may try to write to the message queue simultaneously. outheis uses a **priority-based lock manager** over a Unix domain socket.

### Priority Classes

| Priority | Agents | Rationale |
|----------|--------|-----------|
| HIGH (0) | transport | User is waiting |
| NORMAL (1) | relay, data, agenda, action | Standard operation |
| LOW (2) | pattern | Background work |

### Protocol

```
Client                    Lock Manager
   │                           │
   ├── connect ───────────────►│
   ├── "relay\n" ─────────────►│  (identify)
   │◄── "WAIT\n" ──────────────┤  (queued)
   │◄── "GRANTED\n" ───────────┤  (lock acquired)
   │    ... write to queue ... │
   ├── disconnect ────────────►│  (auto-release)
```

### Why Not flock?

`flock()` is FIFO — first come, first served. This means a background Pattern agent could block a user-facing Relay agent.

The socket-based manager implements priority scheduling: HIGH always preempts NORMAL, NORMAL always preempts LOW. Within a priority class, FIFO applies.

### Implementation

```python
class LockManager:
    def __init__(self, socket_path: Path):
        self.socket_path = socket_path
        self.queue: list[tuple[int, str, socket]] = []  # (priority, id, conn)
        self.current: socket | None = None
    
    def _grant_next(self):
        if self.current or not self.queue:
            return
        # Sort by priority, then arrival (stable sort)
        self.queue.sort(key=lambda x: x[0])
        _, _, conn = self.queue.pop(0)
        self.current = conn
        conn.send(b"GRANTED\n")
```

---

## Write-Ahead Logging

Appending to `messages.jsonl` can fail mid-write (crash, power loss). Write-ahead logging ensures recovery.

### Strategy

1. **Write intent** — save message to `.pending/{msg_id}.json`
2. **Commit** — append to `messages.jsonl` with flock
3. **Cleanup** — delete from `.pending/`

### Recovery

On dispatcher startup:

```python
def recover_pending(pending_dir: Path, queue_path: Path):
    # Load last N message IDs from queue
    existing_ids = set(last_n_ids(queue_path, n=100))
    
    for pending_file in pending_dir.glob("*.json"):
        msg = json.loads(pending_file.read_text())
        if msg["id"] not in existing_ids:
            append(queue_path, msg)  # Complete interrupted write
        pending_file.unlink()  # Clean up either way
```

### Why Check Existing IDs?

The crash might have occurred *after* the append but *before* the cleanup. Checking prevents duplicates.

---

## Schema Versioning

Data formats evolve. Every record carries a version number:

```json
{"v": 1, "id": "msg_abc", "role": "user", "content": "..."}
```

### Migration on Read

```python
def migrate_message(record: dict) -> Message:
    v = record.get("v", 1)
    if v == 1:
        return Message(**record)
    # Future: v2 migration
    raise ValueError(f"Unknown version: {v}")
```

Benefits:
- Old data remains readable
- No batch migrations required
- Version visible in every record

### Migration CLI

```bash
outheis migrate --scan    # Report versions found
outheis migrate --apply   # Upgrade to latest (future)
```

---

## Router Design

The dispatcher routes messages without LLM calls. Routing is deterministic.

### Algorithm

1. **Explicit mention** — `@zeno` → Data agent (highest priority)
2. **Keyword scoring** — count matches against agent keyword lists
3. **Threshold** — score must exceed threshold (default 0.3)
4. **Default** — Relay agent handles unrouted messages

### Keyword Configuration

```json
{
  "routing": {
    "threshold": 0.3,
    "data": ["vault", "search", "find", "note", "document"],
    "agenda": ["calendar", "schedule", "tomorrow", "meeting"],
    "action": ["send", "email", "execute", "run"]
  }
}
```

### Why Not LLM Routing?

- **Latency** — adds round-trip for every message
- **Cost** — API calls aren't free
- **Predictability** — users learn the routing rules

The keyword approach is fast, cheap, and transparent. Users can explicitly invoke agents when needed.

---

## Daemon Architecture

The dispatcher runs as a daemon with PID file management.

### Startup Sequence

```python
def start():
    if pid_file.exists():
        if process_alive(read_pid()):
            raise AlreadyRunning()
        pid_file.unlink()  # Stale PID
    
    write_pid(os.getpid())
    recover_pending()
    lock_manager.start()
    watcher.start()
    
    try:
        main_loop()
    finally:
        cleanup()
```

### File Watching

Two strategies:
- **watchdog** — native filesystem events (preferred)
- **polling** — fallback, checks every N seconds

```python
if WATCHDOG_AVAILABLE:
    watcher = WatchdogWatcher(queue_path, callback)
else:
    watcher = PollingWatcher(queue_path, callback, interval=1.0)
```

---

## Testing Strategy

### Unit Tests

Test components in isolation:

```python
def test_router_explicit_mention():
    router = Router(config)
    assert router.route("@zeno find my notes") == "data"

def test_queue_append_creates_pending():
    with tempdir() as d:
        append(d / "q.jsonl", msg, pending_dir=d / ".pending")
        assert (d / ".pending" / f"{msg['id']}.json").exists()
```

### Integration Tests

Require real LLM, run separately:

```python
@pytest.mark.integration
def test_relay_responds():
    # Requires ANTHROPIC_API_KEY
    response = relay.handle(Message(content="Hello"))
    assert response.content
```

### CI Configuration

```yaml
jobs:
  test:
    # Fast, no API key
    run: pytest -m "not integration"
  
  integration:
    # Slow, requires secret
    if: github.event_name == 'push'
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    run: pytest -m integration
```

---

## Future: Tag Extraction

Planned for Phase 3:

1. **Extract candidates** — YAKE or spaCy on vault content
2. **Vote** — tags gain weight through document co-occurrence
3. **Prune** — remove single-instance tags
4. **Re-evaluate** — periodic recalculation as vault changes

Result: bounded set of tags with genuine semantic relevance.

---

[← Back](../)
