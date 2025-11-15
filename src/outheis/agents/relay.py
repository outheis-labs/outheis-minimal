"""
Relay agent (ou).

The communication interface. Routes messages, composes responses,
formats output for each channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from outheis.agents.base import BaseAgent
from outheis.core.message import Message


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

RELAY_SYSTEM_PROMPT = """You are the Relay agent (ou) in the outheis system.

Your responsibility: All communication between users and the system.

You are the only agent that speaks directly to users. Other agents speak through you.

Tasks:
- Receive user messages from any channel (Signal, CLI, API)
- Route requests to appropriate agents or handle simple ones yourself
- Compose responses from agent outputs
- Adapt formatting to the channel (emoji for Signal, ANSI for CLI, JSON for API)

Style:
- Match the user's register (formal if they're formal, casual if they're casual)
- Be brief—especially on mobile channels
- Don't explain the system unless asked
- Don't announce what you're doing ("Let me check..."—just check)

Core principles:
- Be honest about uncertainty
- Say "I don't know" when you don't know
- Be concise
- Never fabricate information

You do NOT:
- Access the vault directly
- Execute external actions
- Make decisions about priorities
- Learn user patterns (that's Pattern's job)
"""


# =============================================================================
# RELAY AGENT
# =============================================================================

@dataclass
class RelayAgent(BaseAgent):
    """
    Relay agent handles all user communication.
    
    For MVP: handles everything directly via LLM.
    For production: delegates to specialized agents.
    """
    
    name: str = "relay"
    
    def get_system_prompt(self) -> str:
        return RELAY_SYSTEM_PROMPT
    
    def handle(self, msg: Message) -> Optional[Message]:
        """Handle an incoming message."""
        # Get user text
        text = msg.payload.get("text", "")
        
        if not text:
            return None
        
        # Get conversation context
        context = self.get_conversation_context(msg.conversation_id)
        
        # Generate response via LLM
        response_text = self._generate_response(text, context, msg)
        
        # Send response to transport
        return self.respond(
            to="transport",
            payload={"text": response_text},
            conversation_id=msg.conversation_id,
            reply_to=msg.id,
        )
    
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
