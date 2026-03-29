"""
Pattern agent (rumi).

Reflection, insight extraction, learning, and knowledge generalization.
Manages persistent memory by analyzing conversations and extracting
relevant information about the user.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from outheis.agents.base import BaseAgent
from outheis.core.message import Message
from outheis.core.memory import get_memory_store, MemoryType
from outheis.core.queue import read_last_n
from outheis.core.config import get_messages_path, load_config

# =============================================================================
# EXTRACTION PROMPT (specialized for memory extraction task)
# =============================================================================

EXTRACTION_PROMPT = """Analyze the following conversation excerpts and extract NEW information
that should be remembered about the user.

Memory types:
- user: Personal facts (family, age, location, preferences, background) — PERMANENT
- feedback: How the user wants to be treated (communication style, format preferences) — PERMANENT
- context: Current projects, ongoing topics, recent focus areas — TEMPORARY (14 days default)

Language: {language}

CRITICAL RULES:
- Only extract information the user explicitly stated or clearly implied
- Don't repeat information already in memory
- Be concise—one fact per entry

WHAT TO EXTRACT:
- user: Facts about who they are (name, age, family, profession, location, interests)
- feedback: Explicit preferences about how you should work (length, tone, format, language)
- context: What they're currently working on (with decay_days for temporary relevance)

WHAT NOT TO EXTRACT:
- Temporary moods or emotional states (frustration, stress, bad day)
- One-time opinions that don't reflect stable preferences
- Vague or unclear statements
- Information already in memory

TEMPORAL AWARENESS:
- If user mentions being stressed/frustrated/tired, this is NOT a character trait
- Only extract behavioral patterns if they appear CONSISTENTLY across multiple conversations
- For context items, suggest appropriate decay_days (7-30 depending on nature)

Respond in JSON format:
{{
  "extractions": [
    {{"type": "user", "content": "User is 35 years old", "confidence": 0.9}},
    {{"type": "feedback", "content": "Prefers short, direct answers", "confidence": 0.8}},
    {{"type": "context", "content": "Working on Project Alpha mobile app", "confidence": 1.0, "decay_days": 30}}
  ],
  "reasoning": "Brief explanation of what you found"
}}

If nothing new to extract, respond:
{{
  "extractions": [],
  "reasoning": "No new memorable information in these conversations"
}}
"""


# =============================================================================
# PATTERN AGENT
# =============================================================================

@dataclass
class PatternAgent(BaseAgent):
    """
    Pattern agent handles reflection and learning.
    
    Analyzes conversations to extract and maintain persistent memory
    about the user.
    """

    name: str = "pattern"
    
    def get_system_prompt(self) -> str:
        from outheis.agents.loader import load_rules
        return load_rules("pattern")
    
    def get_extraction_prompt(self) -> str:
        """Get specialized prompt for memory extraction."""
        config = load_config()
        return EXTRACTION_PROMPT.format(language=config.user.language)

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message (direct query to pattern agent)."""
        query = msg.payload.get("text", "")
        
        if "analyze" in query.lower() or "memory" in query.lower():
            # Trigger memory analysis
            count = self.analyze_recent_conversations()
            return self.respond(
                to=msg.from_agent or "relay",
                payload={
                    "text": f"Analyzed recent conversations. Extracted {count} new memory entries.",
                },
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
        
        return self.respond(
            to=msg.from_agent or "relay",
            payload={
                "text": "Pattern agent is ready. Use 'analyze memory' to trigger analysis.",
            },
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )

    def analyze_recent_conversations(self, hours: int = 24) -> int:
        """
        Analyze recent conversations and extract memory.
        
        Returns number of new memory entries created.
        """
        # Get recent messages
        messages_path = get_messages_path()
        recent_messages = read_last_n(messages_path, 100)
        
        # Filter to user messages from the last N hours
        cutoff = datetime.now() - timedelta(hours=hours)
        user_messages = [
            m for m in recent_messages
            if m.from_user and datetime.fromtimestamp(m.timestamp) > cutoff
        ]
        
        if not user_messages:
            return 0
        
        # Build conversation context
        conversation_text = self._build_conversation_context(user_messages)
        
        # Get current memory to avoid duplicates
        store = get_memory_store()
        current_memory = store.to_prompt_context()
        
        # Call LLM to extract new information
        extractions = self._extract_with_llm(conversation_text, current_memory)
        
        # Store new memories
        count = 0
        for extraction in extractions:
            memory_type = extraction.get("type")
            content = extraction.get("content")
            confidence = extraction.get("confidence", 0.8)
            decay_days = extraction.get("decay_days")  # Optional
            
            if memory_type in ["user", "feedback", "context"] and content:
                store.add(
                    content,
                    memory_type,
                    confidence=confidence,
                    decay_days=decay_days,
                )
                count += 1
        
        # Also cleanup expired entries
        expired = store.cleanup_expired()
        if expired > 0:
            print(f"[Pattern] Cleaned up {expired} expired memory entries")
        
        return count
    
    def _build_conversation_context(self, messages: list[Message]) -> str:
        """Build a text context from messages for analysis."""
        lines = []
        for msg in messages[-20:]:  # Last 20 user messages
            text = msg.payload.get("text", "")
            if text:
                lines.append(f"User: {text}")
        
        return "\n".join(lines)
    
    def _extract_with_llm(self, conversation_text: str, current_memory: str) -> list[dict]:
        """Use LLM to extract memorable information."""
        import json
        
        user_prompt = f"""Current memory (don't repeat this):
{current_memory if current_memory else "(empty)"}

---

Recent conversation:
{conversation_text}

---

Extract any NEW information worth remembering. Respond in JSON only."""
        
        try:
            from outheis.core.llm import call_llm
            
            response = call_llm(
                model=self.model_alias,
                system=self.get_extraction_prompt(),
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=1000,
            )
            
            # Parse JSON response
            response_text = response.content[0].text.strip()
            
            # Handle markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            data = json.loads(response_text)
            return data.get("extractions", [])
            
        except Exception as e:
            print(f"Pattern agent extraction error: {e}")
            return []

    def run_scheduled(self) -> None:
        """
        Run scheduled reflection.

        Called at configured time (default 04:00).
        """
        print(f"[{datetime.now().isoformat()}] Pattern agent: starting scheduled analysis")
        count = self.analyze_recent_conversations(hours=24)
        print(f"[{datetime.now().isoformat()}] Pattern agent: extracted {count} new memories")
        
        # TODO: Also handle
        # - Tag harmonization
        # - Insight extraction
        # - Context cleanup (remove stale context entries)


# =============================================================================
# FACTORY
# =============================================================================

def create_pattern_agent(model_alias: str = "capable") -> PatternAgent:
    """Create a pattern agent instance."""
    return PatternAgent(model_alias=model_alias)
