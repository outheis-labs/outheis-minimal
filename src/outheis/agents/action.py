"""
Action agent (hiro).

Task execution and external integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from outheis.agents.base import BaseAgent
from outheis.core.message import Message


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

ACTION_SYSTEM_PROMPT = """You are the Action agent (hiro) in the outheis system.

Your responsibility: Task execution and external integrations.

You have network access and can execute code. You write to human/imports/.

Tasks:
- Import data from external services (calendar, email, tasks)
- Execute user-requested actions (send email, create event)
- Run scripts and tools
- Interact with external APIs

Style:
- Confirm before destructive actions
- Report results clearly
- Handle errors gracefully
- Log what you do

Core principles:
- Be honest about uncertainty
- Say "I don't know" when you don't know
- Never fabricate information

You do NOT:
- Make decisions about what to do (that's Agenda's job)
- Communicate directly with users
- Modify vault content (only imports/)
- Act without explicit request or rule
"""


# =============================================================================
# ACTION AGENT
# =============================================================================

@dataclass
class ActionAgent(BaseAgent):
    """
    Action agent handles external operations.
    
    MVP: Not implemented.
    Production: Calendar, email, task integrations.
    """
    
    name: str = "action"
    
    def get_system_prompt(self) -> str:
        return ACTION_SYSTEM_PROMPT
    
    def handle(self, msg: Message) -> Optional[Message]:
        """Handle an incoming message."""
        # TODO: Implement action execution
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "status": "not_implemented",
                "message": "Action agent not yet implemented",
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )


# =============================================================================
# FACTORY
# =============================================================================

def create_action_agent() -> ActionAgent:
    """Create an action agent instance."""
    return ActionAgent()
