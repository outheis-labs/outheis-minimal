"""
Action agent (hiro).

Dynamic task scheduler and executor.
Like an intelligent cron that runs tasks at specified times.
"""

from __future__ import annotations

from dataclasses import dataclass

from outheis.agents.base import BaseAgent
from outheis.agents.tasks import Task, TaskResult, get_registry
from outheis.core.message import Message


# =============================================================================
# ACTION AGENT
# =============================================================================

@dataclass
class ActionAgent(BaseAgent):
    """
    Action agent — task execution and scheduling.
    
    Responsibilities:
    - Execute scheduled tasks (news, data fetching, etc.)
    - Run immediate one-off tasks
    - Coordinate with other agents (e.g., Agenda for output)
    
    Tasks can be:
    - Recurring: "2x daily", "every Monday at 9:00"
    - One-time: "tomorrow at 14:00"
    - Immediate: "now"
    """

    name: str = "action"

    def get_system_prompt(self) -> str:
        from outheis.agents.loader import load_rules
        return load_rules("action")

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message."""
        payload = msg.payload or {}
        action = payload.get("action")
        
        if action == "run_task":
            return self._run_task(msg, payload.get("task_id"))
        elif action == "run_due_tasks":
            return self._run_due_tasks(msg)
        elif action == "add_task":
            return self._add_task(msg, payload)
        elif action == "list_tasks":
            return self._list_tasks(msg)
        else:
            return self.respond(
                to=msg.from_agent or "relay",
                payload={
                    "status": "error",
                    "message": f"Unknown action: {action}",
                },
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
    
    def _run_task(self, msg: Message, task_id: str | None) -> Message | None:
        """Run a specific task by ID."""
        if not task_id:
            return self._error_response(msg, "task_id required")
        
        registry = get_registry()
        task = registry.get(task_id)
        
        if not task:
            return self._error_response(msg, f"Task not found: {task_id}")
        
        result = self._execute_task(task)
        registry.mark_completed(task)
        
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "status": "success" if result.success else "error",
                "task_id": task_id,
                "result": result.data if result.success else result.error,
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )
    
    def _run_due_tasks(self, msg: Message) -> Message | None:
        """Run all tasks that are due."""
        registry = get_registry()
        due_tasks = registry.get_due_tasks()
        
        results = []
        for task in due_tasks:
            result = self._execute_task(task)
            registry.mark_completed(task)
            results.append({
                "task_id": task.id,
                "name": task.name,
                "success": result.success,
            })
        
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "status": "success",
                "tasks_run": len(results),
                "results": results,
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )
    
    def _execute_task(self, task: Task) -> TaskResult:
        """Execute a task and send output to target agent."""
        # Run the task
        result = task.execute()
        
        # If successful and has target agent, send formatted output
        if result.success and task.target_agent:
            formatted = task.format_for_agenda(result)
            self._send_to_agent(task.target_agent, {
                "action": "insert",
                "content": formatted,
                "source": f"task:{task.id}",
            })
        
        return result
    
    def _send_to_agent(self, agent: str, payload: dict) -> None:
        """Send a message to another agent via the queue."""
        from outheis.core.queue import append
        from outheis.core.config import get_messages_path
        
        msg = self.respond(
            to=agent,
            payload=payload,
        )
        if msg:
            append(get_messages_path(), msg)
    
    def _add_task(self, msg: Message, payload: dict) -> Message | None:
        """Add a new task to the registry."""
        task_type = payload.get("task_type")
        
        if task_type == "news_headlines":
            from outheis.agents.tasks.news import create_sz_task
            task = create_sz_task(
                task_id=payload.get("task_id", "sz_headlines"),
                times=payload.get("times", ["08:00", "18:00"]),
            )
            registry = get_registry()
            registry.add(task)
            
            return self.respond(
                to=msg.from_agent or "relay",
                payload={
                    "status": "success",
                    "message": f"Task '{task.name}' added",
                    "task": task.to_dict(),
                },
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
        else:
            return self._error_response(msg, f"Unknown task type: {task_type}")
    
    def _list_tasks(self, msg: Message) -> Message | None:
        """List all registered tasks."""
        registry = get_registry()
        tasks = [task.to_dict() for task in registry.tasks.values()]
        
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "status": "success",
                "tasks": tasks,
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )
    
    def _error_response(self, msg: Message, error: str) -> Message:
        """Create an error response."""
        return self.respond(
            to=msg.from_agent or "relay",
            payload={"status": "error", "message": error},
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )


# =============================================================================
# FACTORY
# =============================================================================

def create_action_agent(model_alias: str = "capable") -> ActionAgent:
    """Create an action agent instance."""
    return ActionAgent(model_alias=model_alias)

