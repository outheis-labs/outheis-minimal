"""
Agenda agent (cato).

Personal secretary: filtering, prioritizing, learning user preferences.
"""

from __future__ import annotations

from dataclasses import dataclass

from outheis.agents.base import BaseAgent
from outheis.core.message import Message


# =============================================================================
# AGENDA AGENT
# =============================================================================

@dataclass
class AgendaAgent(BaseAgent):
    """
    Agenda agent handles filtering and prioritization.

    MVP: Not implemented.
    Production: User rules, daily management, conflict detection.
    """

    name: str = "agenda"

    def get_system_prompt(self) -> str:
        from outheis.agents.loader import load_rules
        return load_rules("agenda")

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message."""
        # TODO: Implement agenda operations
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "status": "not_implemented",
                "message": "Agenda agent not yet implemented",
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )


# =============================================================================
# FACTORY
# =============================================================================

def create_agenda_agent() -> AgendaAgent:
    """Create an agenda agent instance."""
    return AgendaAgent()
