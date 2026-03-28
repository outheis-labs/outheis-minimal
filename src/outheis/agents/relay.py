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
# ROUTING
# =============================================================================

ROUTING_PROMPT = """You are a routing classifier for a personal AI assistant.

The user has sent a message. Classify where it should be handled:

- "data" — Questions about the user's personal information stored in their vault (notes, documents, contacts, addresses, health info, projects, family, anything the user has written down)
- "agenda" — Questions about schedule, calendar, appointments, what's happening today/tomorrow, availability
- "relay" — General conversation, questions you can answer directly, chitchat, requests that don't need personal data

Respond with exactly one word: data, agenda, or relay

Examples:
- "wo wohne ich?" → data
- "what's my doctor's phone number?" → data  
- "erzähl mir was über meine projekte" → data
- "was steht heute an?" → agenda
- "bin ich morgen frei?" → agenda
- "wie geht es dir?" → relay
- "erkläre mir was über Python" → relay
- "was ist die hauptstadt von frankreich?" → relay"""


def classify_query(client, text: str) -> str:
    """Use Haiku to classify where a query should be routed."""
    response = client.messages.create(
        model="claude-haiku-4-5-20250514",
        max_tokens=10,
        system=ROUTING_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    
    classification = response.content[0].text.strip().lower()
    
    # Validate response
    if classification in ("data", "agenda", "relay"):
        return classification
    
    # Default to relay if unclear
    return "relay"


# =============================================================================
# RELAY AGENT
# =============================================================================

@dataclass
class RelayAgent(BaseAgent):
    """
    Relay agent handles all user communication.

    Uses LLM to classify queries and delegate to appropriate agent:
    - Data agent (zeno) for vault/personal data queries
    - Agenda agent (cato) for schedule queries
    - Handles general conversation directly
    """

    name: str = "relay"
    _client: any = field(default=None, repr=False)
    _data_agent: any = field(default=None, repr=False)
    _agenda_agent: any = field(default=None, repr=False)

    @property
    def client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    def get_system_prompt(self) -> str:
        from outheis.agents.loader import load_rules
        from outheis.core.config import load_config
        from outheis.core.memory import get_memory_context
        
        config = load_config()
        rules = load_rules("relay")
        memory_context = get_memory_context()
        
        # Combine rules with user context
        prompt_parts = [rules]
        
        # Add user identity
        if config.user.name:
            prompt_parts.append(f"# User\n\nThe user's name is {config.user.name}.")
        
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

    @property
    def agenda_agent(self):
        """Lazy load Agenda agent for delegation."""
        if self._agenda_agent is None:
            from outheis.agents.agenda import create_agenda_agent
            self._agenda_agent = create_agenda_agent()
        return self._agenda_agent

    def _route_query(self, text: str) -> str:
        """Determine where to route a query using LLM classification."""
        text_lower = text.lower()
        
        # Explicit agent mentions override classification
        if "@zeno" in text_lower:
            return "data"
        if "@cato" in text_lower:
            return "agenda"
        
        # Use Haiku to classify
        try:
            return classify_query(self.client, text)
        except Exception:
            # On error, default to relay
            return "relay"

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message."""
        text = msg.payload.get("text", "")

        if not text:
            return None

        # Check for explicit memory marker "!"
        from outheis.core.memory import handle_explicit_memory
        was_memory, memory_response = handle_explicit_memory(text)
        
        if was_memory:
            return self.respond(
                to="transport",
                payload={"text": memory_response},
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )

        # Route query using LLM classification
        route = self._route_query(text)
        
        if route == "agenda":
            response_text = self._handle_with_agenda_agent(text, msg)
        elif route == "data":
            response_text = self._handle_with_data_agent(text, msg)
        else:
            # Handle directly
            context = self.get_conversation_context(msg.conversation_id)
            response_text = self._generate_response(text, context, msg)

        return self.respond(
            to="transport",
            payload={"text": response_text},
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )

    def _handle_with_data_agent(self, text: str, msg: Message) -> str:
        """Delegate to Data agent and format response."""
        try:
            answer = self.data_agent.handle_direct(text)
            return answer
        except Exception as e:
            return f"I tried to search your vault but encountered an error: {e}"

    def _handle_with_agenda_agent(self, text: str, msg: Message) -> str:
        """Delegate to Agenda agent and format response."""
        try:
            agenda_msg = Message(
                to="agenda",
                type="query",
                payload={"text": text},
                conversation_id=msg.conversation_id,
            )
            response = self.agenda_agent.handle(agenda_msg)
            if response:
                return response.payload.get("text", "No response from agenda agent.")
            return "No response from agenda agent."
        except Exception as e:
            return f"I tried to check your schedule but encountered an error: {e}"

    def _generate_response(
        self,
        text: str,
        context: list[Message],
        original_msg: Message,
    ) -> str:
        """Generate a response using LLM."""
        try:
            return self._call_llm(text, context)
        except Exception as e:
            return f"I encountered an error: {e}"

    def _call_llm(self, text: str, context: list[Message]) -> str:
        """Call LLM API for conversation."""
        # Build messages for API
        messages = []

        # Add context from conversation
        for msg in context[-5:]:
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

        # Use Sonnet for conversation (better quality)
        response = self.client.messages.create(
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
