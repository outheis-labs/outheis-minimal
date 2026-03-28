"""
Relay agent (ou).

The communication interface. Routes messages, composes responses,
formats output for each channel.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from outheis.agents.base import BaseAgent
from outheis.core.message import Message

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
        from outheis.agents.loader import load_rules
        from outheis.core.config import load_config
        from outheis.core.memory import get_memory_context
        
        config = load_config()
        rules = load_rules("relay")
        memory_context = get_memory_context()
        
        # Combine rules with memory and language setting
        prompt_parts = [rules]
        
        if memory_context:
            prompt_parts.append(memory_context)
        
        prompt_parts.append(f"\nDefault language: {config.user.language}")
        
        return "\n\n".join(prompt_parts)

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
