"""
Base agent class.

All agents inherit from this base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from outheis.core.config import get_messages_path, get_human_dir, load_config
from outheis.core.message import Message, create_agent_message, AgentId
from outheis.core.queue import append, read_conversation


# =============================================================================
# BASE AGENT
# =============================================================================

@dataclass
class BaseAgent(ABC):
    """
    Base class for all agents.
    
    Provides common functionality for message handling,
    queue access, and response creation.
    """
    
    name: AgentId
    queue_path: Path = field(default_factory=get_messages_path)
    
    @abstractmethod
    def handle(self, msg: Message) -> Optional[Message]:
        """
        Handle an incoming message.
        
        Returns a response message, or None if no response needed.
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    def respond(
        self,
        to: str,
        payload: dict,
        conversation_id: str,
        reply_to: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> Message:
        """Create and queue a response message."""
        msg = create_agent_message(
            from_agent=self.name,
            to=to,
            type="response",
            payload=payload,
            conversation_id=conversation_id,
            reply_to=reply_to,
            intent=intent,
        )
        append(self.queue_path, msg)
        return msg
    
    def request(
        self,
        to: str,
        payload: dict,
        conversation_id: str,
        intent: Optional[str] = None,
    ) -> Message:
        """Create and queue a request to another agent."""
        msg = create_agent_message(
            from_agent=self.name,
            to=to,
            type="request",
            payload=payload,
            conversation_id=conversation_id,
            intent=intent,
        )
        append(self.queue_path, msg)
        return msg
    
    def get_conversation_context(
        self,
        conversation_id: str,
        max_messages: int = 10,
    ) -> list[Message]:
        """Get recent messages in a conversation for context."""
        messages = read_conversation(self.queue_path, conversation_id)
        return messages[-max_messages:]
    
    def log_session_note(
        self,
        problem: str,
        solution: str,
        session_id: str,
        context: Optional[dict] = None,
    ) -> None:
        """
        Log a session note for Pattern agent to review.
        
        Used when user helps solve a problem.
        """
        from outheis.core.schema import write_session_note
        from outheis.core.config import get_session_notes_path
        import time
        import json
        
        note = {
            "id": f"note_{int(time.time())}",
            "session_id": session_id,
            "agent": self.name,
            "problem": problem,
            "solution": solution,
            "context": context or {},
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "reviewed": False,
        }
        
        path = get_session_notes_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "a", encoding="utf-8") as f:
            f.write(write_session_note(note) + "\n")
