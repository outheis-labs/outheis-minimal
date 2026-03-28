"""
Data agent (zeno).

Knowledge management across all vaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from anthropic import Anthropic

from outheis.agents.base import BaseAgent
from outheis.core.config import load_config
from outheis.core.index import SearchIndex, create_index
from outheis.core.message import Message
from outheis.core.vault import read_file, VaultFile

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

DATA_SYSTEM_PROMPT = """You are zeno, the Data agent in the outheis system.

Your responsibility: Knowledge management across the user's vault.

You have access to:
- Search results from the vault index
- Full content of relevant files when needed

Your tasks:
- Answer questions based on vault contents
- Find relevant notes and documents
- Summarize and synthesize information
- Identify connections between notes

Language:
- ALWAYS respond in the same language the user used in their query
- If unsure, use the default language: {language}
- Vault content may be in any language — translate/summarize as needed for your response

Style:
- Cite your sources (note titles, paths)
- Distinguish between what you found and what you infer
- Be concise but complete
- If information is incomplete, say so

You do NOT:
- Make up information that isn't in the vault
- Execute external actions
- Access calendar or email (that's Action agent's job)

Core principle: Be honest about what you know and don't know."""


# =============================================================================
# DATA AGENT
# =============================================================================

@dataclass
class DataAgent(BaseAgent):
    """
    Data agent handles vault search and knowledge retrieval.
    
    Uses LLM to interpret queries and synthesize results.
    """
    
    name: str = "data"
    _client: Anthropic | None = field(default=None, repr=False)
    _indices: dict[str, SearchIndex] = field(default_factory=dict, repr=False)
    
    def get_system_prompt(self) -> str:
        return DATA_SYSTEM_PROMPT
    
    @property
    def client(self) -> Anthropic:
        if self._client is None:
            self._client = Anthropic()
        return self._client
    
    def _get_indices(self) -> list[SearchIndex]:
        """Get or create search indices for all vaults."""
        config = load_config()
        vaults = config.user.all_vaults()
        
        indices = []
        for vault_path in vaults:
            if not vault_path.exists():
                continue
            
            key = str(vault_path)
            if key not in self._indices:
                self._indices[key] = create_index(vault_path)
                # Update index on first access
                self._indices[key].update()
            
            indices.append(self._indices[key])
        
        return indices
    
    def search(self, query: str, limit: int = 10) -> list[tuple[SearchIndex, any]]:
        """Search across all vaults."""
        results = []
        for index in self._get_indices():
            for entry in index.search(query, limit=limit):
                results.append((index, entry))
        
        # Sort by relevance (simple: just interleave for now)
        return results[:limit]
    
    def search_by_tag(self, tag: str) -> list[tuple[SearchIndex, any]]:
        """Find files by tag across all vaults."""
        results = []
        for index in self._get_indices():
            for entry in index.search_by_tag(tag):
                results.append((index, entry))
        return results
    
    def get_file_content(self, index: SearchIndex, path: str) -> VaultFile | None:
        """Load full file content."""
        full_path = index.vault_root / path
        if full_path.exists():
            return read_file(full_path)
        return None
    
    def get_system_prompt(self) -> str:
        """Get system prompt with language from config."""
        config = load_config()
        return DATA_SYSTEM_PROMPT.format(language=config.user.language)
    
    def _build_context(self, query: str) -> str:
        """Build context string from search results."""
        results = self.search(query, limit=5)
        
        if not results:
            return "No relevant documents found in the vault."
        
        context_parts = []
        for index, entry in results:
            # Load full content for top results
            vf = self.get_file_content(index, entry.path)
            if vf:
                # Truncate long content
                body = vf.body[:2000]
                if len(vf.body) > 2000:
                    body += "\n[... truncated ...]"
                
                context_parts.append(
                    f"=== {entry.title} ({entry.path}) ===\n"
                    f"Tags: {', '.join(entry.tags) if entry.tags else 'none'}\n\n"
                    f"{body}"
                )
        
        return "\n\n".join(context_parts)
    
    def handle(self, msg: Message) -> Message | None:
        """Handle an incoming message with LLM."""
        query = msg.payload.get("text", "") or msg.payload.get("query", "")
        
        # Determine response target: if from user, respond to transport; if from agent, respond to that agent
        response_to = "transport" if msg.from_user else (msg.from_agent or "relay")
        
        if not query:
            return self.respond(
                to=response_to,
                payload={"error": "Empty query"},
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
        
        # Build context from vault search
        context = self._build_context(query)
        
        # Prepare prompt
        user_content = f"""The user is asking about their vault contents.

VAULT SEARCH RESULTS:
{context}

USER QUERY:
{query}

Based on the vault contents above, answer the user's query. If the information isn't in the vault, say so clearly."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=self.get_system_prompt(),
                messages=[{"role": "user", "content": user_content}],
            )
            
            answer = response.content[0].text
            
            return self.respond(
                to=response_to,
                payload={
                    "answer": answer,
                    "sources": [entry.path for _, entry in self.search(query, limit=5)],
                },
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
            
        except Exception as e:
            return self.respond(
                to=response_to,
                payload={"error": str(e)},
                conversation_id=msg.conversation_id,
                reply_to=msg.id,
            )
    
    def handle_direct(self, query: str) -> str:
        """
        Direct query interface for Relay delegation.
        
        Returns the answer string directly, not a Message.
        """
        context = self._build_context(query)
        
        user_content = f"""The user is asking about their vault contents.

VAULT SEARCH RESULTS:
{context}

USER QUERY:
{query}

Based on the vault contents above, answer the user's query. If the information isn't in the vault, say so clearly."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=self.get_system_prompt(),
                messages=[{"role": "user", "content": user_content}],
            )
            return response.content[0].text
        except Exception as e:
            return f"Error searching vault: {e}"
    
    def rebuild_indices(self) -> dict[str, int]:
        """Rebuild all search indices."""
        results = {}
        for index in self._get_indices():
            count = index.rebuild()
            results[str(index.vault_root)] = count
        return results
    
    def get_stats(self) -> dict:
        """Get statistics about indexed content."""
        total_files = 0
        all_tags: dict[str, int] = {}
        
        for index in self._get_indices():
            total_files += len(index.entries)
            for tag, count in index.get_all_tags().items():
                all_tags[tag] = all_tags.get(tag, 0) + count
        
        return {
            "total_files": total_files,
            "vaults": len(self._get_indices()),
            "top_tags": sorted(all_tags.items(), key=lambda x: -x[1])[:10],
        }


# =============================================================================
# FACTORY
# =============================================================================

def create_data_agent() -> DataAgent:
    """Create a data agent instance."""
    return DataAgent()
