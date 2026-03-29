"""
Base classes for tasks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskSchedule(Enum):
    """When a task should run."""
    ONCE = "once"           # Run once, then delete
    IMMEDIATE = "immediate" # Run now, then delete
    HOURLY = "hourly"
    DAILY = "daily"         # Run once per day at specified time
    TWICE_DAILY = "twice_daily"  # Run at two specified times
    WEEKLY = "weekly"
    CUSTOM = "custom"       # Cron-like schedule


@dataclass
class TaskResult:
    """Result of a task execution."""
    success: bool
    data: Any = None
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Task(ABC):
    """
    Base class for executable tasks.
    
    Tasks are created by the user (via Relay) and executed by Action Agent.
    """
    
    id: str
    name: str
    schedule: TaskSchedule
    enabled: bool = True
    
    # Schedule details
    times: list[str] = field(default_factory=list)  # ["08:00", "18:00"]
    days: list[int] = field(default_factory=list)   # [0, 2, 4] = Mon, Wed, Fri
    
    # Execution tracking
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    
    # Target agent for output (usually "agenda")
    target_agent: str = "agenda"
    
    @abstractmethod
    def execute(self) -> TaskResult:
        """Execute the task and return result."""
        pass
    
    @abstractmethod
    def format_for_agenda(self, result: TaskResult) -> str:
        """Format the result for insertion into Agenda."""
        pass
    
    def to_dict(self) -> dict:
        """Serialize task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.__class__.__name__,
            "schedule": self.schedule.value,
            "enabled": self.enabled,
            "times": self.times,
            "days": self.days,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "target_agent": self.target_agent,
        }
