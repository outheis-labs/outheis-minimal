"""
Dispatcher daemon.

The central process that watches the message queue,
routes messages to agents, and manages agent lifecycle.

Includes built-in scheduler for periodic tasks (Pattern agent, housekeeping).
Uses select() with timeout — no polling loop, no external dependencies.
"""

from __future__ import annotations

import os
import select
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from outheis.agents import (
    create_action_agent,
    create_agenda_agent,
    create_data_agent,
    create_pattern_agent,
    create_relay_agent,
)
from outheis.core.config import (
    Config,
    get_messages_path,
    init_directories,
    load_config,
)
from outheis.core.message import Message
from outheis.core.queue import append, get_last_id, get_unanswered_requests, read_from
from outheis.dispatcher.router import get_dispatch_target
from outheis.dispatcher.watcher import QueueWatcher


# =============================================================================
# SCHEDULER
# =============================================================================

@dataclass
class ScheduledTask:
    """A task scheduled to run at specific times."""
    name: str
    run: Callable[[], None]
    hour: int  # 0-23
    minute: int = 0
    last_run: datetime | None = None
    
    def next_run(self, now: datetime) -> datetime:
        """Calculate next run time."""
        today_run = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        if now >= today_run:
            # Already passed today, schedule for tomorrow
            return today_run + timedelta(days=1)
        return today_run
    
    def seconds_until_next(self, now: datetime) -> float:
        """Seconds until next scheduled run."""
        return (self.next_run(now) - now).total_seconds()
    
    def should_run(self, now: datetime) -> bool:
        """Check if task should run now."""
        if self.last_run is None:
            # Never run — check if we're at the scheduled time
            return (now.hour == self.hour and now.minute == self.minute)
        # Already ran today?
        if self.last_run.date() == now.date():
            return False
        # Is it time?
        return (now.hour == self.hour and now.minute >= self.minute)


@dataclass
class Scheduler:
    """
    Built-in scheduler for periodic tasks.
    
    No external dependencies. Integrates with select() timeout.
    """
    tasks: list[ScheduledTask] = field(default_factory=list)
    
    def add(self, name: str, run: Callable[[], None], hour: int, minute: int = 0) -> None:
        """Add a scheduled task."""
        self.tasks.append(ScheduledTask(name=name, run=run, hour=hour, minute=minute))
    
    def seconds_until_next(self) -> float:
        """Seconds until next task needs to run."""
        if not self.tasks:
            return 3600.0  # No tasks, check again in an hour
        
        now = datetime.now()
        return min(task.seconds_until_next(now) for task in self.tasks)
    
    def run_due(self) -> list[str]:
        """Run all due tasks. Returns names of tasks run."""
        now = datetime.now()
        ran = []
        for task in self.tasks:
            if task.should_run(now):
                try:
                    task.run()
                    task.last_run = now
                    ran.append(task.name)
                except Exception as e:
                    # Log but don't crash
                    print(f"Scheduled task {task.name} failed: {e}")
        return ran


# =============================================================================
# PID FILE
# =============================================================================

def get_pid_path() -> Path:
    """Get path to PID file."""
    from outheis.core.config import get_outheis_dir
    return get_outheis_dir() / ".dispatcher.pid"


def write_pid() -> None:
    """Write current PID to file."""
    get_pid_path().write_text(str(os.getpid()))


def read_pid() -> int | None:
    """Read PID from file, or None if not running."""
    path = get_pid_path()
    if not path.exists():
        return None
    try:
        pid = int(path.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError):
        # Invalid PID or process not running
        path.unlink(missing_ok=True)
        return None


def remove_pid() -> None:
    """Remove PID file."""
    get_pid_path().unlink(missing_ok=True)


# =============================================================================
# DISPATCHER
# =============================================================================

@dataclass
class Dispatcher:
    """
    The dispatcher daemon.

    Watches the message queue, routes messages to agents,
    manages responses, and runs scheduled tasks.
    
    Uses select() with timeout for efficient waiting:
    - Wakes on file changes (inotify/kqueue via watcher)
    - Wakes on scheduled task deadline
    - No busy polling
    """

    config: Config = field(default_factory=load_config)
    queue_path: Path = field(default_factory=get_messages_path)
    last_processed_id: str | None = None
    running: bool = False
    scheduler: Scheduler = field(default_factory=Scheduler)

    # Agents (loaded on demand)
    _agents: dict = field(default_factory=dict)
    
    # Pipe for wakeup signal
    _wakeup_read: int | None = None
    _wakeup_write: int | None = None

    def __post_init__(self):
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        # Create wakeup pipe
        self._wakeup_read, self._wakeup_write = os.pipe()
        os.set_blocking(self._wakeup_read, False)
        os.set_blocking(self._wakeup_write, False)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        self.running = False
        # Wake up select()
        if self._wakeup_write:
            try:
                os.write(self._wakeup_write, b'x')
            except OSError:
                pass

    def _setup_scheduled_tasks(self) -> None:
        """Configure scheduled tasks."""
        # Pattern agent: default 04:00
        # TODO: Read from config
        self.scheduler.add(
            name="pattern",
            run=self._run_pattern_agent,
            hour=4,
            minute=0,
        )
        
        # Index rebuild: 04:30
        self.scheduler.add(
            name="index_rebuild",
            run=self._run_index_rebuild,
            hour=4,
            minute=30,
        )
        
        # Archive rotation: 05:00
        self.scheduler.add(
            name="archive_rotation",
            run=self._run_archive_rotation,
            hour=5,
            minute=0,
        )

    def _run_pattern_agent(self) -> None:
        """Run Pattern agent scheduled reflection."""
        agent = self.get_agent("pattern")
        if agent:
            agent.run_scheduled()

    def _run_index_rebuild(self) -> None:
        """Rebuild vault search indices."""
        agent = self.get_agent("data")
        if agent and hasattr(agent, 'rebuild_indices'):
            agent.rebuild_indices()

    def _run_archive_rotation(self) -> None:
        """Rotate old messages to archive."""
        # TODO: Implement archive rotation
        pass

    def get_agent(self, name: str):
        """Get or create an agent instance."""
        if name not in self._agents:
            # Get agent-specific config
            agent_config = self.config.agents.get(name)
            model_alias = agent_config.model if agent_config else "capable"
            
            # Check if agent is enabled
            if agent_config and not agent_config.enabled:
                return None
            
            if name == "relay":
                self._agents[name] = create_relay_agent(model_alias=model_alias)
            elif name == "data":
                self._agents[name] = create_data_agent(model_alias=model_alias)
            elif name == "agenda":
                self._agents[name] = create_agenda_agent(model_alias=model_alias)
            elif name == "action":
                self._agents[name] = create_action_agent(model_alias=model_alias)
            elif name == "pattern":
                self._agents[name] = create_pattern_agent(model_alias=model_alias)
            else:
                return None
        return self._agents[name]

    def process_message(self, msg: Message) -> None:
        """Process a single message."""
        # Skip messages not addressed to dispatcher
        if msg.to != "dispatcher":
            return

        # Route to appropriate agent
        target = get_dispatch_target(msg, self.config.routing)

        # Get agent and handle
        agent = self.get_agent(target)
        if agent:
            try:
                agent.handle(msg)
            except Exception as e:
                # Log error, send error response
                self._handle_agent_error(msg, target, e)

    def _handle_agent_error(self, msg: Message, agent: str, error: Exception) -> None:
        """Handle agent processing error."""
        from outheis.core.message import create_agent_message

        error_msg = create_agent_message(
            from_agent="relay",
            to="transport",
            type="response",
            payload={
                "text": f"Error processing request: {error}",
                "error": True,
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )
        append(self.queue_path, error_msg)

    def process_pending(self) -> int:
        """Process all pending messages. Returns count processed."""
        count = 0
        for msg in read_from(self.queue_path, after_id=self.last_processed_id):
            self.process_message(msg)
            self.last_processed_id = msg.id
            count += 1
        return count

    def run(self) -> None:
        """Run the dispatcher daemon."""
        from outheis.core.queue import recover_pending
        from outheis.core.llm import init_llm
        from outheis.dispatcher.lock import LockManager

        init_directories()
        write_pid()
        self.running = True
        
        # Initialize LLM with config (once, at startup)
        init_llm(self.config.llm)
        
        # Set up scheduled tasks
        self._setup_scheduled_tasks()

        print(f"Dispatcher started (PID {os.getpid()})")
        print(f"Watching: {self.queue_path}")
        print(f"Scheduled tasks: {[t.name for t in self.scheduler.tasks]}")

        # Recover any pending messages from crashed processes
        recovered = recover_pending(self.queue_path)
        if recovered:
            print(f"Recovered {recovered} pending message(s)")

        # Process any unanswered requests (crashed before response)
        unanswered = get_unanswered_requests(self.queue_path)
        if unanswered:
            print(f"Processing {len(unanswered)} unanswered request(s)...")
            for msg in unanswered:
                self.process_message(msg)

        # Start from last message for new ones
        self.last_processed_id = get_last_id(self.queue_path)

        # Start lock manager
        lock_manager = LockManager()
        lock_manager.start()
        print(f"Lock manager listening on: {lock_manager.socket_path}")

        # Set up file watcher
        watcher = QueueWatcher(
            queue_path=self.queue_path,
            on_message=self._on_queue_change,
        )
        watcher.start()

        try:
            while self.running:
                # Calculate timeout until next scheduled task
                timeout = min(self.scheduler.seconds_until_next(), 60.0)
                
                # Wait for wakeup signal or timeout
                ready, _, _ = select.select([self._wakeup_read], [], [], timeout)
                
                if ready:
                    # Drain wakeup pipe
                    try:
                        os.read(self._wakeup_read, 1024)
                    except OSError:
                        pass
                
                # Run any due scheduled tasks
                ran = self.scheduler.run_due()
                if ran:
                    print(f"Ran scheduled tasks: {ran}")
                    
        finally:
            watcher.stop()
            lock_manager.stop()
            
            # Close wakeup pipe
            if self._wakeup_read:
                os.close(self._wakeup_read)
            if self._wakeup_write:
                os.close(self._wakeup_write)
                
            remove_pid()
            print("Dispatcher stopped")

    def _on_queue_change(self) -> None:
        """Called when queue file changes."""
        self.process_pending()


# =============================================================================
# DAEMON CONTROL
# =============================================================================

def start_daemon(foreground: bool = False) -> bool:
    """
    Start the dispatcher daemon.

    Args:
        foreground: If True, run in foreground (blocking).
                   If False, fork to background.

    Returns:
        True if started successfully.
    """
    # Check if already running
    existing_pid = read_pid()
    if existing_pid:
        print(f"Dispatcher already running (PID {existing_pid})")
        return False

    # Validate API keys BEFORE forking
    print("Validating API keys...")
    errors = _validate_api_keys()
    if errors:
        for err in errors:
            print(f"  ✗ {err}")
        print("\nDispatcher cannot start. Fix configuration and try again.")
        return False
    print("  ✓ API keys valid")

    if foreground:
        # Run in foreground
        dispatcher = Dispatcher()
        dispatcher.run()
        return True
    else:
        # Fork to background
        pid = os.fork()
        if pid > 0:
            # Parent process
            time.sleep(0.5)  # Wait for child to start
            child_pid = read_pid()
            if child_pid:
                print(f"Dispatcher started (PID {child_pid})")
                return True
            else:
                print("Failed to start dispatcher")
                return False
        else:
            # Child process
            # Detach from terminal
            os.setsid()

            # Close standard file descriptors
            sys.stdin.close()
            sys.stdout.close()
            sys.stderr.close()

            # Redirect to /dev/null
            sys.stdin = open(os.devnull)
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')

            # Run dispatcher (validation already done)
            dispatcher = Dispatcher()
            dispatcher.run()
            sys.exit(0)


def _validate_api_keys() -> list[str]:
    """
    Validate API keys for all enabled agents.
    
    Returns list of errors, empty if all valid.
    """
    import os as _os
    errors = []
    
    # Check Anthropic API key (used by relay, data, pattern)
    api_key = _os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        errors.append("ANTHROPIC_API_KEY not set")
    elif not api_key.startswith("sk-ant-"):
        errors.append("ANTHROPIC_API_KEY has invalid format")
    else:
        # Quick validation: try a minimal API call
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            # Minimal request to validate key
            client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
        except anthropic.AuthenticationError:
            errors.append("ANTHROPIC_API_KEY is invalid")
        except anthropic.APIError as e:
            # Rate limit or other API error is OK - key is valid
            if "authentication" in str(e).lower():
                errors.append(f"ANTHROPIC_API_KEY error: {e}")
        except Exception as e:
            errors.append(f"API key validation failed: {e}")
    
    return errors


def stop_daemon() -> bool:
    """
    Stop the dispatcher daemon.

    Returns:
        True if stopped successfully.
    """
    pid = read_pid()
    if not pid:
        print("Dispatcher not running")
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        # Wait for process to exit
        for _ in range(50):  # 5 seconds max
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except OSError:
                # Process exited
                remove_pid()
                print("Dispatcher stopped")
                return True

        # Force kill
        os.kill(pid, signal.SIGKILL)
        remove_pid()
        print("Dispatcher killed")
        return True
    except OSError as e:
        print(f"Error stopping dispatcher: {e}")
        remove_pid()
        return False


def daemon_status() -> dict:
    """
    Get daemon status.

    Returns:
        Dict with status information.
    """
    pid = read_pid()
    return {
        "running": pid is not None,
        "pid": pid,
    }
