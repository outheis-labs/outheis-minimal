"""
Message queue — append-only JSONL file with locking.

The queue is the central communication channel. All agents
read from and write to this queue.
"""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
from typing import Iterator, Optional

from outheis.core.schema import read_message, write_message
from outheis.core.message import Message


# =============================================================================
# QUEUE OPERATIONS
# =============================================================================

def append(path: Path, msg: Message) -> None:
    """
    Append a message to the queue.
    
    Uses exclusive file locking to prevent concurrent write corruption.
    """
    line = write_message(msg.to_dict())
    
    with open(path, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(line + "\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def read_all(path: Path) -> list[Message]:
    """
    Read all messages from the queue.
    
    Handles version migration transparently.
    """
    if not path.exists():
        return []
    
    messages = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = read_message(line)
                messages.append(Message.from_dict(d))
            except Exception:
                # Skip malformed lines, log in production
                continue
    
    return messages


def read_from(path: Path, after_id: Optional[str] = None) -> Iterator[Message]:
    """
    Read messages from the queue, optionally after a given ID.
    
    Yields messages one by one for memory efficiency.
    """
    if not path.exists():
        return
    
    found_marker = after_id is None
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = read_message(line)
                msg = Message.from_dict(d)
                
                if not found_marker:
                    if msg.id == after_id:
                        found_marker = True
                    continue
                
                yield msg
            except Exception:
                continue


def read_last_n(path: Path, n: int) -> list[Message]:
    """
    Read the last N messages from the queue.
    
    Simple implementation: reads all, returns last N.
    For large queues, a more efficient implementation would
    read from the end of the file.
    """
    all_messages = read_all(path)
    return all_messages[-n:] if len(all_messages) > n else all_messages


def read_conversation(path: Path, conversation_id: str) -> list[Message]:
    """Read all messages belonging to a conversation."""
    return [
        msg for msg in read_all(path)
        if msg.conversation_id == conversation_id
    ]


# =============================================================================
# QUEUE MANAGEMENT
# =============================================================================

def ensure_queue(path: Path) -> None:
    """Ensure queue file exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()


def queue_size(path: Path) -> int:
    """Get queue file size in bytes."""
    if not path.exists():
        return 0
    return path.stat().st_size


def message_count(path: Path) -> int:
    """Count messages in queue."""
    if not path.exists():
        return 0
    
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count
