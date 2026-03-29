"""
Agenda agent (cato).

Personal secretary: schedule management, time awareness, conflict detection.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path

from outheis.agents.base import BaseAgent
from outheis.core.config import load_config
from outheis.core.message import Message


# =============================================================================
# AGENDA FILES
# =============================================================================

AGENDA_DIR = "Agenda"
DAILY_FILE = "Daily.md"
INBOX_FILE = "Inbox.md"
EXCHANGE_FILE = "Exchange.md"


def get_agenda_dir() -> Path | None:
    """Get the Agenda directory from the primary vault."""
    config = load_config()
    vault = config.human.primary_vault()
    if vault.exists():
        agenda_path = vault / AGENDA_DIR
        if agenda_path.exists():
            return agenda_path
    return None


def read_agenda_file(filename: str) -> str | None:
    """Read an agenda file."""
    agenda_dir = get_agenda_dir()
    if not agenda_dir:
        return None
    
    path = agenda_dir / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def write_agenda_file(filename: str, content: str) -> bool:
    """Write to an agenda file."""
    agenda_dir = get_agenda_dir()
    if not agenda_dir:
        return False
    
    path = agenda_dir / filename
    path.write_text(content, encoding="utf-8")
    return True


def get_today_str() -> str:
    """Get today's date formatted for display."""
    today = date.today()
    return today.strftime("%A, %B %d, %Y")


# =============================================================================
# AGENDA AGENT
# =============================================================================

@dataclass
class AgendaAgent(BaseAgent):
    """
    Agenda agent handles schedule and time management.

    Reads and writes to Agenda/ directory in the vault.
    Uses LLM to interpret queries and manage schedule.
    """

    name: str = "agenda"

    def get_system_prompt(self) -> str:
        from outheis.agents.loader import load_rules
        from outheis.core.memory import get_memory_context
        
        rules = load_rules("agenda")
        memory = get_memory_context()
        
        # Add current date context
        today = get_today_str()
        date_context = f"\n\nCurrent date: {today}"
        
        parts = [rules]
        if memory:
            parts.append(memory)
        parts.append(date_context)
        
        return "\n\n".join(parts)

    def _build_context(self) -> str:
        """Build context from agenda files."""
        parts = []
        
        daily = read_agenda_file(DAILY_FILE)
        if daily:
            parts.append(f"## Daily.md (Today's Schedule)\n\n{daily}")
        
        inbox = read_agenda_file(INBOX_FILE)
        if inbox:
            parts.append(f"## Inbox.md (Unprocessed Items)\n\n{inbox}")
        
        exchange = read_agenda_file(EXCHANGE_FILE)
        if exchange:
            parts.append(f"## Exchange.md (System Messages)\n\n{exchange}")
        
        if not parts:
            return "No agenda files found in vault."
        
        return "\n\n---\n\n".join(parts)

    def _process_with_llm(self, query: str) -> str:
        """Process an agenda query using LLM."""
        context = self._build_context()
        
        user_prompt = f"""Agenda context:

{context}

---

User query: {query}

---

Respond helpfully based on the agenda information. If the user wants to modify the schedule, describe what changes you would make. Be concise. Match the language of the user's query."""

        from outheis.core.llm import call_llm
        
        response = call_llm(
            model=self.model_alias,
            system=self.get_system_prompt(),
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=1000,
        )
        
        return response.content[0].text

    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message."""
        query = msg.payload.get("text", "")
        
        if not query:
            return self.respond(
                to=msg.from_agent or "relay",
                payload={"error": True, "text": "No query provided"},
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
        
        # Check if agenda directory exists
        if not get_agenda_dir():
            return self.respond(
                to=msg.from_agent or "relay",
                payload={
                    "text": "No Agenda directory found in vault. Create vault/Agenda/ with Daily.md, Inbox.md, and Exchange.md to use schedule management."
                },
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
        
        try:
            answer = self._process_with_llm(query)
            
            return self.respond(
                to=msg.from_agent or "relay",
                payload={"text": answer},
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
        except Exception as e:
            return self.respond(
                to=msg.from_agent or "relay",
                payload={"error": True, "text": f"Agenda error: {str(e)}"},
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )


# =============================================================================
# FACTORY
# =============================================================================

def create_agenda_agent(model_alias: str = "capable") -> AgendaAgent:
    """Create an agenda agent instance."""
    return AgendaAgent(model_alias=model_alias)
