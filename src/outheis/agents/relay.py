"""
Relay agent (ou).

The communication interface. Routes messages, composes responses,
formats output for each channel.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from outheis.agents.base import BaseAgent
from outheis.core.message import Message

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

RELAY_SYSTEM_PROMPT = """You are ou, the Relay agent in the outheis system.

Your responsibility: All communication between users and the system.

You are the only agent that speaks directly to users. Other agents speak through you.

{memory_context}

Tasks:
- Receive user messages from any channel (Signal, CLI, API)
- Handle general conversation directly
- Delegate vault/note queries to the Data agent (zeno)
- Compose responses from agent outputs
- Adapt formatting to the channel

Language:
- ALWAYS respond in the same language the user used in their message
- If unsure, use the default language: {language}
- Match the user's register (formal if formal, casual if casual)

Style:
- Be brief—especially on mobile channels
- Don't explain the system unless asked
- Don't announce what you're doing ("Let me check..."—just check)
- Use memory naturally—don't announce "I remember that..."

Core principles:
- Be honest about uncertainty
- Say "I don't know" when you don't know
- Be concise
- Never fabricate information

When to delegate to Data agent:
- Questions about vault contents, notes, documents
- "Find", "search", "what do I have about..."
- Requests for information that might be in the user's notes

You handle directly:
- General conversation
- Questions about the system
- Simple tasks that don't need vault access

When the user shares personal information (family, preferences, facts about themselves),
acknowledge it naturally. The Pattern agent will decide what to persist.
"""

# Keywords that suggest vault queries
VAULT_KEYWORDS = [
    "vault", "note", "notes", "document", "find", "search",
    "what do i have", "my files", "my notes", "look up",
    "in my", "did i write", "where is", "show me",
]


# =============================================================================
# RELAY AGENT
# =============================================================================

@dataclass
class RelayAgent(BaseAgent):
    """
    Relay agent handles all user communication.

    Delegates vault queries to Data agent.
    Handles general conversation directly.
    """

    name: str = "relay"
    _data_agent: any = field(default=None, repr=False)

    def get_system_prompt(self) -> str:
        from outheis.core.config import load_config
        from outheis.core.memory import get_memory_context
        
        config = load_config()
        memory_context = get_memory_context()
        
        return RELAY_SYSTEM_PROMPT.format(
            language=config.user.language,
            memory_context=memory_context,
        )

    @property
    def data_agent(self):
        """Lazy load Data agent for delegation."""
        if self._data_agent is None:
            from outheis.agents.data import create_data_agent
            self._data_agent = create_data_agent()
        return self._data_agent

    def _should_delegate_to_data(self, text: str) -> bool:
        """Check if query should go to Data agent."""
        text_lower = text.lower()
        
        # Explicit mention
        if "@zeno" in text_lower:
            return True
        
        # Keyword matching
        for keyword in VAULT_KEYWORDS:
            if keyword in text_lower:
                return True
        
        return False

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message."""
        # Get user text
        text = msg.payload.get("text", "")

        if not text:
            return None

        # Check for explicit memory marker "!"
        from outheis.core.memory import handle_explicit_memory
        was_memory, memory_response = handle_explicit_memory(text)
        
        if was_memory:
            # Acknowledge memory storage
            return self.respond(
                to="transport",
                payload={"text": memory_response},
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )

        # Check for delegation
        if self._should_delegate_to_data(text):
            response_text = self._handle_with_data_agent(text, msg)
        else:
            # Handle directly
            context = self.get_conversation_context(msg.conversation_id)
            response_text = self._generate_response(text, context, msg)

        # Send response to transport
        return self.respond(
            to="transport",
            payload={"text": response_text},
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )

    def _handle_with_data_agent(self, text: str, msg: Message) -> str:
        """Delegate to Data agent and format response."""
        try:
            # Get answer from Data agent
            answer = self.data_agent.handle_direct(text)
            return answer
        except Exception as e:
            return f"I tried to search your vault but encountered an error: {e}"

    def _generate_response(
        self,
        text: str,
        context: list[Message],
        original_msg: Message,
    ) -> str:
        """
        Generate a response using LLM.

        MVP: Uses anthropic SDK directly.
        """
        try:
            return self._call_llm(text, context)
        except Exception as e:
            return f"I encountered an error: {e}"

    def _call_llm(self, text: str, context: list[Message]) -> str:
        """Call LLM API."""
        try:
            import anthropic
        except ImportError:
            return "[anthropic SDK not installed. Run: pip install anthropic]"

        # Build messages for API
        messages = []

        # Add context from conversation
        for msg in context[-5:]:  # Last 5 messages
            if msg.from_user:
                messages.append({
                    "role": "user",
                    "content": msg.payload.get("text", ""),
                })
            elif msg.from_agent == "relay":
                messages.append({
                    "role": "assistant",
                    "content": msg.payload.get("text", ""),
                })

        # Add current message
        messages.append({
            "role": "user",
            "content": text,
        })

        # Call API
        client = anthropic.Anthropic()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=self.get_system_prompt(),
            messages=messages,
        )

        return response.content[0].text


# =============================================================================
# FACTORY
# =============================================================================

def create_relay_agent() -> RelayAgent:
    """Create a relay agent instance."""
    return RelayAgent()
