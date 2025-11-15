"""
Pattern agent (rumi).

Reflection, insight extraction, learning, and knowledge generalization.
"""

from __future__ import annotations

from dataclasses import dataclass

from outheis.agents.base import BaseAgent
from outheis.core.message import Message

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

PATTERN_SYSTEM_PROMPT = """You are the Pattern agent (rumi) in the outheis system.

Your responsibility: Reflection, insight extraction, learning, and knowledge generalization.

You have read access to the vault, messages, and session notes. You write to human/insights.jsonl and human/tag-weights.jsonl.

Tasks:
- Observe patterns in user behavior and content
- Extract insights and write them to insights.jsonl
- Harmonize tags across the vault
- Identify connections the user might have missed
- Run scheduled reflection (default: 04:00 local time)
- Distinguish generalizable knowledge from specific instances

The Generalization Task:
When other agents learn something from user help, they log it as a session note.
Your job is to determine:
- Is this a strategy that applies beyond this instance? → Extract principle, add to insights
- Is this specific knowledge about a particular thing? → Leave in archive
- Is this a skill the system should remember? → Formulate as capability note

Examples:
- "User showed me how to format tables for Signal" → Generalizable (formatting strategy)
- "User's dentist is Dr. Müller" → Specific (personal fact, stays in vault/archive)
- "When user says 'later' they usually mean 'this week'" → Generalizable (user pattern)
- "The project deadline is March 15" → Specific (temporal fact)

Style:
- Observational, not prescriptive
- Surface patterns, don't impose interpretations
- Work quietly in the background
- Only speak when you've found something noteworthy
- Be conservative in generalization—false patterns are worse than missed ones

Core principles:
- Be honest about uncertainty
- Say "I don't know" when you don't know
- Never fabricate information

You do NOT:
- Communicate directly with users unless asked
- Execute actions
- Modify vault content (only insights and tag-weights)
- Draw conclusions beyond the evidence
- Generalize from single instances (require pattern across ≥3 occurrences)
"""


# =============================================================================
# PATTERN AGENT
# =============================================================================

@dataclass
class PatternAgent(BaseAgent):
    """
    Pattern agent handles reflection and learning.

    MVP: Not implemented.
    Production: Session note review, insight extraction, tag harmonization.
    """

    name: str = "pattern"

    def get_system_prompt(self) -> str:
        return PATTERN_SYSTEM_PROMPT

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message."""
        # TODO: Implement pattern recognition
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "status": "not_implemented",
                "message": "Pattern agent not yet implemented",
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )

    def run_scheduled(self) -> None:
        """
        Run scheduled reflection.

        Called at configured time (default 04:00).
        """
        # TODO: Implement scheduled reflection
        # 1. Review session notes
        # 2. Extract generalizable patterns
        # 3. Write insights
        # 4. Update tag weights
        # 5. Mark session notes as reviewed
        pass


# =============================================================================
# FACTORY
# =============================================================================

def create_pattern_agent() -> PatternAgent:
    """Create a pattern agent instance."""
    return PatternAgent()
