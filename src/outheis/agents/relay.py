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

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message."""
        import os
        import sys
        
        verbose = os.environ.get("OUTHEIS_VERBOSE")
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

        # Check for explicit agent mentions (@zeno, @cato)
        text_lower = text.lower()
        if "@zeno" in text_lower:
            if verbose:
                print("[explicit @zeno → data]", file=sys.stderr)
            response_text = self._handle_with_data_agent(text, msg)
        elif "@cato" in text_lower:
            if verbose:
                print("[explicit @cato → agenda]", file=sys.stderr)
            response_text = self._handle_with_agenda_agent(text, msg)
        else:
            # Let Relay handle with tools - it decides when to delegate
            context = self.get_conversation_context(msg.conversation_id)
            response_text = self._generate_response(text, context, msg)

        return self.respond(
            to="transport",
            payload={"text": response_text},
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )

    def _handle_with_agenda_agent(self, text: str, msg: Message) -> str:
        """Delegate to Agenda agent and format response."""
        from outheis.core.message import generate_id
        
        try:
            agenda_msg = Message(
                id=generate_id(),
                to="agenda",
                type="request",
                payload={"text": text},
                conversation_id=msg.conversation_id,
                from_agent="relay",
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
        """Generate a response using LLM with tools."""
        try:
            return self._call_llm_with_tools(text, context)
        except Exception as e:
            return f"Ein Fehler ist aufgetreten: {e}"

    def _call_llm_with_tools(self, text: str, context: list[Message]) -> str:
        """Call LLM API with tool support for vault/agenda access."""
        import os
        import sys
        
        verbose = os.environ.get("OUTHEIS_VERBOSE")
        
        # Define tools
        tools = [
            {
                "name": "search_vault",
                "description": "Search the user's vault (notes, documents, files) for personal information. USE THIS when asked about personal facts you don't know from Memory: where they live, contacts, family details, projects, health info, or anything personal that might be in their notes.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What to search for"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "check_agenda",
                "description": "Check the user's schedule/calendar. Use for questions about appointments, availability, what's happening today/tomorrow/this week.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The schedule question"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        # Build messages
        messages = []
        for msg in context[-5:]:
            if msg.from_user:
                messages.append({"role": "user", "content": msg.payload.get("text", "")})
            elif msg.from_agent == "relay":
                messages.append({"role": "assistant", "content": msg.payload.get("text", "")})
        messages.append({"role": "user", "content": text})
        
        # First call - may use tools
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=self.get_system_prompt(),
            messages=messages,
            tools=tools,
        )
        
        # Check if tool use is needed
        if response.stop_reason == "tool_use":
            # Process tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        print(f"[tool: {block.name}({block.input})]", file=sys.stderr)
                    
                    if block.name == "search_vault":
                        result = self.data_agent.handle_direct(block.input["query"])
                    elif block.name == "check_agenda":
                        # Create a minimal message for agenda
                        from outheis.core.message import generate_id
                        agenda_msg = Message(
                            id=generate_id(),
                            to="agenda",
                            type="request",
                            payload={"text": block.input["query"]},
                            conversation_id="tool_call",
                            from_agent="relay",
                        )
                        agenda_response = self.agenda_agent.handle(agenda_msg)
                        result = agenda_response.payload.get("text", "") if agenda_response else "Keine Termine gefunden."
                    else:
                        result = "Tool not found"
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            
            # Second call with tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            final_response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=self.get_system_prompt(),
                messages=messages,
                tools=tools,
            )
            
            # Extract text from response
            for block in final_response.content:
                if hasattr(block, "text"):
                    return block.text
            return "Ich konnte keine Antwort formulieren."
        
        # No tool use - return direct response
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return "Ich konnte keine Antwort formulieren."


# =============================================================================
# FACTORY
# =============================================================================

def create_relay_agent() -> RelayAgent:
    """Create a relay agent instance."""
    return RelayAgent()
