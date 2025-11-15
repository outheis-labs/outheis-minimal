"""
Dispatcher daemon.

The central process that watches the message queue,
routes messages to agents, and manages agent lifecycle.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from outheis.core.config import (
    load_config,
    get_messages_path,
    get_human_dir,
    init_directories,
    Config,
)
from outheis.core.queue import read_from, append
from outheis.core.message import Message
from outheis.dispatcher.router import get_dispatch_target
from outheis.dispatcher.watcher import QueueWatcher
from outheis.dispatcher.lifecycle import LifecycleManager
from outheis.agents import (
    create_relay_agent,
    create_data_agent,
    create_agenda_agent,
    create_action_agent,
    create_pattern_agent,
)


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


def read_pid() -> Optional[int]:
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
    and manages responses.
    """
    
    config: Config = field(default_factory=load_config)
    queue_path: Path = field(default_factory=get_messages_path)
    last_processed_id: Optional[str] = None
    running: bool = False
    
    # Agents (loaded on demand)
    _agents: dict = field(default_factory=dict)
    
    def __post_init__(self):
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        self.running = False
    
    def get_agent(self, name: str):
        """Get or create an agent instance."""
        if name not in self._agents:
            if name == "relay":
                self._agents[name] = create_relay_agent()
            elif name == "data":
                self._agents[name] = create_data_agent()
            elif name == "agenda":
                self._agents[name] = create_agenda_agent()
            elif name == "action":
                self._agents[name] = create_action_agent()
            elif name == "pattern":
                self._agents[name] = create_pattern_agent()
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
        init_directories()
        write_pid()
        self.running = True
        
        print(f"Dispatcher started (PID {os.getpid()})")
        print(f"Watching: {self.queue_path}")
        
        # Process any existing messages
        self.process_pending()
        
        # Set up file watcher
        watcher = QueueWatcher(
            queue_path=self.queue_path,
            on_message=self._on_queue_change,
        )
        watcher.start()
        
        try:
            while self.running:
                time.sleep(0.1)
        finally:
            watcher.stop()
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
            sys.stdin = open(os.devnull, 'r')
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')
            
            # Run dispatcher
            dispatcher = Dispatcher()
            dispatcher.run()
            sys.exit(0)


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
