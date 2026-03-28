"""
Action agent (hiro).

Task execution and external integrations.
"""

from __future__ import annotations

from dataclasses import dataclass

from outheis.agents.base import BaseAgent
from outheis.core.message import Message


# =============================================================================
# ACTION AGENT
# =============================================================================

@dataclass
class ActionAgent(BaseAgent):
    """
    Action agent handles external operations.

    Phase 3: Calendar, email, task integrations.
    """

    name: str = "action"

    def get_system_prompt(self) -> str:
        from outheis.agents.loader import load_rules
        return load_rules("action")

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message."""
        # Phase 3: Implement action execution
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "status": "not_implemented",
                "message": "Action agent is planned for Phase 3",
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
