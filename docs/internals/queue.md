# Queue & Locking

## Message Queue

Central communication channel: `~/.outheis/human/messages.jsonl`

Append-only JSONL. All agents read from and write to this queue.

### Message Format

```json
{
  "v": 1,
  "id": "msg_1731672000_a1b2c3",
  "conversation_id": "conv_1731672000_x1y2z3",
  "timestamp": "2025-11-15T10:00:00Z",
  "from": {"agent": "relay"},
  "to": "transport",
  "type": "response",
  "payload": {"text": "Hello!"},
  "reply_to": "msg_1731671999_d4e5f6"
}
```

## Locking

### Socket Lock (messages.jsonl)

For the message queue, a Unix socket lock manager handles prioritized access.

**Socket:** `~/.outheis/.dispatcher.sock`

**Priority classes:**

| Priority | Level | Requester |
|----------|-------|-----------|
| HIGH | 0 | transport |
| NORMAL | 1 | relay, data, agenda, action |
| LOW | 2 | pattern |

Within each class: FIFO ordering.

**Protocol:**

```python
from outheis.dispatcher.lock import LockClient

# Request lock, wait until granted
with LockClient("relay") as lock:
    append(queue_path, message)
```

Wire protocol:

```json
→ {"cmd": "request", "requester": "relay"}
← {"status": "granted"}

→ {"cmd": "release"}
← {"status": "released"}
```

If client disconnects, lock is automatically released.

### flock (other files)

For files without priority requirements, standard `flock` is used:

| File | Writers |
|------|---------|
| `session_notes.jsonl` | All agents |
| `config.json` | CLI, Web UI |
| Vault files (.md) | Data agent |

`flock` is blocking — writers wait until lock is available. Lock is automatically released if process dies.

```python
import fcntl

with open(path, "a") as f:
    fcntl.flock(f, fcntl.LOCK_EX)  # Blocks until acquired
    f.write(data)
    # Lock released on close
```

## Write-Ahead Logging

All queue writes use write-ahead for crash safety.

**Directory:** `~/.outheis/human/.pending/`

**Write sequence:**

```
1. Write message to .pending/{msg_id}.json
2. flock + append to messages.jsonl
3. Delete from .pending/
```

**If process dies:** Message survives in `.pending/`

**Recovery (Dispatcher startup):**

```python
from outheis.core.queue import recover_pending

recovered = recover_pending(queue_path)
# Scans .pending/, checks for duplicates, appends missing
```

Recovery steps:
1. Scan `.pending/` for `.json` files
2. Read last 100 message IDs from queue
3. For each pending file:
   - Skip if ID already in queue (duplicate)
   - Append to queue
   - Delete pending file

### Implementation

```python
# core/queue.py

def append(path: Path, msg: Message) -> None:
    # 1. Write-ahead
    pending_path = write_pending(msg)
    
    try:
        # 2. Append with lock
        line = write_message(msg.to_dict())
        
        with open(path, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(line + "\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        
        # 3. Cleanup
        delete_pending(pending_path)
    except Exception:
        # Keep pending for recovery
        raise
```

## Schema Versioning

Every JSONL record has a `"v": int` field.

**Current versions:**
- Messages: v1
- Insights: v1
- Session Notes: v1

**Migration:** Records are migrated on read. Old versions are transparently upgraded.

```python
from outheis.core.schema import read_message

# Automatically migrates v0 → v1
msg = read_message(line)
```

**CLI:**

```bash
outheis migrate --scan   # Show outdated records
outheis migrate --apply  # Apply migrations
```
