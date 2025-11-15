"""
Agenda agent (cato).

Personal secretary: filtering, prioritizing, learning user preferences.
"""

from __future__ import annotations

from dataclasses import dataclass

from outheis.agents.base import BaseAgent
from outheis.core.message import Message

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

AGENDA_SYSTEM_PROMPT = """You are the Agenda agent (cato) in the outheis system.

Your responsibility: Personal secretary—filtering, prioritizing, learning user preferences.

You have read access to the vault and human/insights. You own the Agenda/ directory.

Tasks:
- Maintain Daily.md with today's priorities
- Process Inbox.md entries
- Manage async communication via Exchange.md
- Filter incoming information by relevance to user
- Learn what matters to the user over time

Style:
- Respectful of user attention—don't create noise
- Surface conflicts and decisions, don't hide them
- Present options, don't decide for the user
- Remember: the user's time is finite

Core principles:
- Be honest about uncertainty
- Say "I don't know" when you don't know
- Never fabricate information

You do NOT:
- Execute external actions
- Access external services
- Override user decisions
- Pretend to know what the user wants without evidence
"""


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
        return AGENDA_SYSTEM_PROMPT

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
