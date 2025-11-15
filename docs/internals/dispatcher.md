# Dispatcher

The dispatcher is the microkernel of outheis — the only persistent process.

## Architecture

```
┌─────────────────────────────────────────┐
│              Dispatcher                  │
│            (Microkernel)                 │
│  - Routing (no LLM)                     │
│  - Agent lifecycle                      │
│  - Lock management                      │
│  - Write-ahead recovery                 │
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
│  - Ollama (future)                      │
└─────────────────────────────────────────┘
```

| OS Concept | outheis Equivalent |
|------------|-------------------|
| Microkernel | Dispatcher |
| CPU | LLM |
| Processes | Agents |
| IPC | messages.jsonl |

## Startup Sequence

```python
def run(self):
    init_directories()
    write_pid()                          # ~/.outheis/.dispatcher.pid
    
    recovered = recover_pending()        # Write-ahead recovery
    
    lock_manager = LockManager()
    lock_manager.start()                 # ~/.outheis/.dispatcher.sock
    
    process_pending()                    # Handle existing messages
    
    watcher = QueueWatcher(on_message=process_pending)
    watcher.start()                      # inotify/kqueue
    
    while running:
        sleep(0.1)
    
    # Shutdown
    watcher.stop()
    lock_manager.stop()
    remove_pid()
```

## Routing

Messages addressed to `dispatcher` are routed based on content.

### Routing Logic

```python
def route(msg):
    text = msg.payload.get("text", "").lower()
    
    # 1. Explicit mention → immediate
    if "@ou" in text: return "relay"
    if "@zeno" in text: return "data"
    if "@cato" in text: return "agenda"
    if "@hiro" in text: return "action"
    if "@rumi" in text: return "pattern"
    
    # 2. Keyword scoring
    scores = {
        "data": score(text, config.routing.data),
        "agenda": score(text, config.routing.agenda),
        "action": score(text, config.routing.action),
    }
    
    best = max(scores, key=scores.get)
    
    if scores[best] >= config.routing.threshold:
        return best
    
    # 3. Fallback → Relay decides
    return "relay"
```

### Keyword Scoring

```python
def score(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    matches = sum(1 for kw in keywords if kw.lower() in text)
    return matches / len(keywords)
```

## File Watching

Uses `watchdog` library if available, falls back to polling.

```python
# With watchdog (recommended)
pip install watchdog

# Polling fallback
# Checks file size every second
```

Platform support:
- Linux: inotify
- macOS: kqueue/FSEvents
- Windows: ReadDirectoryChangesW

## Lock Manager

See [queue.md](queue.md) for details.

Starts Unix socket server on `~/.outheis/.dispatcher.sock`.

## Agent Lifecycle

Agents are loaded on-demand as Python modules.

```python
def get_agent(self, name: str):
    if name not in self._agents:
        if name == "relay":
            self._agents[name] = create_relay_agent()
        elif name == "data":
            self._agents[name] = create_data_agent()
        # ...
    return self._agents[name]
```

Future: Agents as separate processes with supervision.

## Process Management

**PID file:** `~/.outheis/.dispatcher.pid`

```python
# Write PID
def write_pid():
    get_pid_path().write_text(str(os.getpid()))

# Check if running
def read_pid() -> Optional[int]:
    path = get_pid_path()
    if not path.exists():
        return None
    try:
        pid = int(path.read_text().strip())
        os.kill(pid, 0)  # Check if alive
        return pid
    except (ValueError, OSError):
        path.unlink(missing_ok=True)
        return None
```

**Shutdown signals:** SIGTERM, SIGINT

```python
signal.signal(signal.SIGTERM, self._handle_shutdown)
signal.signal(signal.SIGINT, self._handle_shutdown)

def _handle_shutdown(self, signum, frame):
    self.running = False
```

## Daemonization

```bash
outheis start      # Fork to background
outheis start -f   # Run in foreground
```

Background mode:
1. Fork
2. `os.setsid()` — detach from terminal
3. Close stdin/stdout/stderr
4. Run dispatcher loop

Foreground mode (for debugging):
- No fork
- Output to terminal
- Ctrl+C to stop
