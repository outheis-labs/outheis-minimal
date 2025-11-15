"""
Data agent (zeno).

Knowledge management across all vaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from outheis.agents.base import BaseAgent
from outheis.core.message import Message


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

DATA_SYSTEM_PROMPT = """You are the Data agent (zeno) in the outheis system.

Your responsibility: Knowledge management across all vaults.

You have read and write access to the vault. You maintain the search index.

Tasks:
- Search for information in the vault
- Create, update, and organize notes
- Maintain tag consistency
- Answer questions based on vault contents
- Aggregate information across multiple notes

Style:
- Cite your sources (note titles, paths)
- Distinguish between what you found and what you infer
- Acknowledge when information is incomplete or outdated

Core principles:
- Be honest about uncertainty
- Say "I don't know" when you don't know
- Never fabricate information

You do NOT:
- Communicate directly with users (go through Relay)
- Execute external actions
- Access imported data (calendar, email) without going through Action
- Make up information that isn't in the vault
"""


# =============================================================================
# DATA AGENT
# =============================================================================

@dataclass
class DataAgent(BaseAgent):
    """
    Data agent handles vault operations.
    
    MVP: Basic search and read.
    Production: Full index, write operations, tag management.
    """
    
    name: str = "data"
    
    def get_system_prompt(self) -> str:
        return DATA_SYSTEM_PROMPT
    
    def handle(self, msg: Message) -> Optional[Message]:
        """Handle an incoming message."""
        # TODO: Implement vault search and operations
        intent = msg.intent or "unknown"
        
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "status": "not_implemented",
                "message": f"Data agent received intent: {intent}",
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )


# =============================================================================
# FACTORY
# =============================================================================

def create_data_agent() -> DataAgent:
    """Create a data agent instance."""
    return DataAgent()
