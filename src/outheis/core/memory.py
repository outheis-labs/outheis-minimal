"""
Memory system for persistent user knowledge.

Separates meta-knowledge (about the user, working style) from
vault content (documents, notes, projects).

Memory types:
- user: Personal information (family, preferences, background)
- feedback: How the agent should work (style, format, behavior)
- context: Current focus, active projects, recent topics

Memory is managed by the Pattern agent (rumi), which periodically
analyzes conversations and updates the persistent memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal
import json
import os

from outheis.core.config import get_human_dir


# =============================================================================
# TYPES
# =============================================================================

MemoryType = Literal["user", "feedback", "context"]


@dataclass
class MemoryEntry:
    """A single memory entry."""
    
    content: str
    type: MemoryType
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0  # 0-1, how certain we are
    source_count: int = 1    # how many times this was mentioned
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "type": self.type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confidence": self.confidence,
            "source_count": self.source_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(
            content=data["content"],
            type=data["type"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            confidence=data.get("confidence", 1.0),
            source_count=data.get("source_count", 1),
        )


# =============================================================================
# MEMORY STORE
# =============================================================================

@dataclass
class MemoryStore:
    """
    Persistent memory storage.
    
    Stores user knowledge, feedback, and context separately.
    Each type is a list of entries that can be queried and updated.
    """
    
    base_path: Path = field(default_factory=get_human_dir)
    _entries: dict[MemoryType, list[MemoryEntry]] = field(default_factory=dict)
    _loaded: bool = False
    
    @property
    def memory_path(self) -> Path:
        return self.base_path / "memory"
    
    def _ensure_dir(self) -> None:
        """Ensure memory directory exists."""
        self.memory_path.mkdir(parents=True, exist_ok=True)
    
    def _file_path(self, memory_type: MemoryType) -> Path:
        """Get file path for a memory type."""
        return self.memory_path / f"{memory_type}.json"
    
    def load(self) -> None:
        """Load all memory from disk."""
        self._ensure_dir()
        self._entries = {"user": [], "feedback": [], "context": []}
        
        for memory_type in ["user", "feedback", "context"]:
            path = self._file_path(memory_type)
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                    self._entries[memory_type] = [
                        MemoryEntry.from_dict(e) for e in data.get("entries", [])
                    ]
                except (json.JSONDecodeError, KeyError):
                    self._entries[memory_type] = []
        
        self._loaded = True
    
    def save(self, memory_type: MemoryType | None = None) -> None:
        """Save memory to disk."""
        self._ensure_dir()
        
        types_to_save = [memory_type] if memory_type else ["user", "feedback", "context"]
        
        for mt in types_to_save:
            path = self._file_path(mt)
            data = {
                "type": mt,
                "updated_at": datetime.now().isoformat(),
                "entries": [e.to_dict() for e in self._entries.get(mt, [])]
            }
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
    
    def _ensure_loaded(self) -> None:
        """Ensure memory is loaded."""
        if not self._loaded:
            self.load()
    
    def get(self, memory_type: MemoryType) -> list[MemoryEntry]:
        """Get all entries of a type."""
        self._ensure_loaded()
        return self._entries.get(memory_type, [])
    
    def get_all(self) -> dict[MemoryType, list[MemoryEntry]]:
        """Get all memory entries."""
        self._ensure_loaded()
        return self._entries.copy()
    
    def add(self, content: str, memory_type: MemoryType, confidence: float = 1.0) -> MemoryEntry:
        """Add a new memory entry."""
        self._ensure_loaded()
        
        entry = MemoryEntry(
            content=content,
            type=memory_type,
            confidence=confidence,
        )
        
        if memory_type not in self._entries:
            self._entries[memory_type] = []
        
        self._entries[memory_type].append(entry)
        self.save(memory_type)
        
        return entry
    
    def update(self, memory_type: MemoryType, index: int, content: str) -> MemoryEntry | None:
        """Update an existing memory entry."""
        self._ensure_loaded()
        
        entries = self._entries.get(memory_type, [])
        if 0 <= index < len(entries):
            entries[index].content = content
            entries[index].updated_at = datetime.now()
            entries[index].source_count += 1
            self.save(memory_type)
            return entries[index]
        
        return None
    
    def remove(self, memory_type: MemoryType, index: int) -> bool:
        """Remove a memory entry."""
        self._ensure_loaded()
        
        entries = self._entries.get(memory_type, [])
        if 0 <= index < len(entries):
            entries.pop(index)
            self.save(memory_type)
            return True
        
        return False
    
    def clear(self, memory_type: MemoryType) -> None:
        """Clear all entries of a type."""
        self._ensure_loaded()
        self._entries[memory_type] = []
        self.save(memory_type)
    
    def to_prompt_context(self) -> str:
        """
        Generate context string for agent prompts.
        
        Returns a formatted string summarizing all memory
        that agents can include in their system prompts.
        """
        self._ensure_loaded()
        
        sections = []
        
        # User info
        user_entries = self._entries.get("user", [])
        if user_entries:
            user_lines = [f"- {e.content}" for e in user_entries]
            sections.append(f"## About the user\n" + "\n".join(user_lines))
        
        # Feedback/preferences
        feedback_entries = self._entries.get("feedback", [])
        if feedback_entries:
            feedback_lines = [f"- {e.content}" for e in feedback_entries]
            sections.append(f"## Working preferences\n" + "\n".join(feedback_lines))
        
        # Current context
        context_entries = self._entries.get("context", [])
        if context_entries:
            context_lines = [f"- {e.content}" for e in context_entries]
            sections.append(f"## Current context\n" + "\n".join(context_lines))
        
        if not sections:
            return ""
        
        return "# Memory\n\n" + "\n\n".join(sections)


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    """Get the global memory store instance."""
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store


def get_memory_context() -> str:
    """Get formatted memory context for prompts."""
    return get_memory_store().to_prompt_context()
