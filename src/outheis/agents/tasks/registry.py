"""
Task registry — stores and manages scheduled tasks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from outheis.agents.tasks.base import Task, TaskSchedule


@dataclass
class TaskRegistry:
    """
    Registry for scheduled tasks.
    
    Tasks are stored in ~/.outheis/human/tasks.json
    """
    
    tasks: dict[str, "Task"] = field(default_factory=dict)
    _path: Path | None = None
    
    def __post_init__(self):
        from outheis.core.config import get_human_dir
        self._path = get_human_dir() / "tasks.json"
    
    def add(self, task: "Task") -> None:
        """Add a task to the registry."""
        self.tasks[task.id] = task
        self._calculate_next_run(task)
        self.save()
    
    def remove(self, task_id: str) -> bool:
        """Remove a task from the registry."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save()
            return True
        return False
    
    def get(self, task_id: str) -> "Task | None":
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_due_tasks(self) -> list["Task"]:
        """Get all tasks that are due to run."""
        now = datetime.now()
        due = []
        for task in self.tasks.values():
            if task.enabled and task.next_run and task.next_run <= now:
                due.append(task)
        return due
    
    def mark_completed(self, task: "Task") -> None:
        """Mark a task as completed and calculate next run."""
        from outheis.agents.tasks.base import TaskSchedule
        
        task.last_run = datetime.now()
        task.run_count += 1
        
        # Remove one-time tasks
        if task.schedule in (TaskSchedule.ONCE, TaskSchedule.IMMEDIATE):
            self.remove(task.id)
        else:
            self._calculate_next_run(task)
            self.save()
    
    def _calculate_next_run(self, task: "Task") -> None:
        """Calculate the next run time for a task."""
        from outheis.agents.tasks.base import TaskSchedule
        
        now = datetime.now()
        
        if task.schedule == TaskSchedule.IMMEDIATE:
            task.next_run = now
        
        elif task.schedule == TaskSchedule.ONCE:
            if task.times:
                # Parse time like "14:30"
                h, m = map(int, task.times[0].split(":"))
                next_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
                task.next_run = next_time
            else:
                task.next_run = now
        
        elif task.schedule == TaskSchedule.DAILY:
            if task.times:
                h, m = map(int, task.times[0].split(":"))
                next_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
                task.next_run = next_time
        
        elif task.schedule == TaskSchedule.TWICE_DAILY:
            if len(task.times) >= 2:
                candidates = []
                for time_str in task.times[:2]:
                    h, m = map(int, time_str.split(":"))
                    t = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    if t <= now:
                        t += timedelta(days=1)
                    candidates.append(t)
                task.next_run = min(candidates)
        
        elif task.schedule == TaskSchedule.HOURLY:
            task.next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    def save(self) -> None:
        """Save registry to disk."""
        if not self._path:
            return
        
        data = {
            task_id: task.to_dict()
            for task_id, task in self.tasks.items()
        }
        
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, default=str))
    
    def load(self) -> None:
        """Load registry from disk."""
        if not self._path or not self._path.exists():
            return
        
        try:
            data = json.loads(self._path.read_text())
            # TODO: Deserialize tasks based on type
            # For now, we'll handle this when we have concrete task types
        except Exception:
            pass


# Singleton registry
_registry: TaskRegistry | None = None


def get_registry() -> TaskRegistry:
    """Get the global task registry."""
    global _registry
    if _registry is None:
        _registry = TaskRegistry()
        _registry.load()
    return _registry
