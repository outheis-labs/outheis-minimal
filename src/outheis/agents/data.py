"""
Data agent (zeno).

Knowledge management across all vaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from outheis.agents.base import BaseAgent
from outheis.core.config import load_config
from outheis.core.index import SearchIndex, create_index
from outheis.core.message import Message
from outheis.core.vault import read_file, VaultFile


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
    _indices: dict[str, SearchIndex] = field(default_factory=dict, repr=False)
    
    def get_system_prompt(self) -> str:
        from outheis.agents.loader import load_rules
        from outheis.core.memory import get_memory_context
        
        config = load_config()
        rules = load_rules("data")
        memory_context = get_memory_context()
        
        prompt_parts = [rules]
        
        if memory_context:
            prompt_parts.append(memory_context)
        
        prompt_parts.append(f"\nDefault language: {config.human.language}")
        
        return "\n\n".join(prompt_parts)
    
    def _get_indices(self) -> list[SearchIndex]:
        """Get or create search indices for all vaults."""
        config = load_config()
        vaults = config.human.all_vaults()
        
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
    
    def find_by_path(self, pattern: str) -> list[tuple[SearchIndex, any]]:
        """Find files by path pattern across all vaults."""
        results = []
        for index in self._get_indices():
            for entry in index.find_by_path(pattern):
                results.append((index, entry))
        return results
    
    def list_path(self, path: str = "") -> list[dict]:
        """List contents of a path across all vaults."""
        results = []
        for index in self._get_indices():
            info = index.list_path(path)
            if info.get("exists"):
                info["vault"] = str(index.vault_root)
                results.append(info)
        return results
    
    def get_file_content(self, index: SearchIndex, path: str) -> VaultFile | None:
        """Load full file content."""
        full_path = index.vault_root / path
        if full_path.exists():
            return read_file(full_path)
        return None
    
    def _build_context(self, query: str) -> tuple[str, list[str]]:
        """
        Build context string from search results.
        
        Returns (context_text, list_of_source_paths)
        """
        # Check if query is asking about a specific path/directory
        path_keywords = ["verzeichnis", "ordner", "folder", "directory", "datei", "file", "pfad", "path"]
        is_path_query = any(kw in query.lower() for kw in path_keywords)
        
        results = []
        sources = []
        
        # If asking about paths, also do path-based search
        if is_path_query:
            # Extract potential path names from query
            words = query.split()
            for word in words:
                if len(word) > 2 and word not in path_keywords:
                    # Try listing this as a path
                    path_results = self.list_path(word)
                    for pr in path_results:
                        if pr.get("is_dir"):
                            results.append(f"Directory '{word}' exists in vault:\n  Subdirs: {pr.get('dirs', [])}\n  Files: {pr.get('files', [])}")
                    
                    # Try finding files with this in path
                    for index, entry in self.find_by_path(word):
                        if entry.path not in sources:
                            sources.append(entry.path)
        
        # Regular content search
        search_results = self.search(query, limit=5)
        
        if not search_results and not results:
            return "No relevant documents found in the vault.", []
        
        context_parts = list(results)  # Start with path results
        
        for index, entry in search_results:
            if entry.path in sources:
                continue
            sources.append(entry.path)
            
            # Load full content for top results
            vf = self.get_file_content(index, entry.path)
            if vf:
                # Truncate long content
                body = vf.body[:2000]
                if len(vf.body) > 2000:
                    body += "\n[... truncated ...]"
                
                context_parts.append(
                    f"=== {entry.title} ===\n"
                    f"Source: {entry.path}\n"
                    f"Tags: {', '.join(entry.tags) if entry.tags else 'none'}\n\n"
                    f"{body}"
                )
        
        return "\n\n".join(context_parts), sources
    
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
        context, sources = self._build_context(query)
        
        # Prepare prompt
        user_content = f"""The user is asking about their vault contents.

VAULT SEARCH RESULTS:
{context}

SOURCES FOUND:
{chr(10).join(f'- {s}' for s in sources) if sources else '(none)'}

USER QUERY:
{query}

Instructions:
1. Answer based on the vault contents above
2. ALWAYS mention the source file path when citing information (e.g., "In Projects/MyProject.md...")
3. If asked about a specific file or directory, confirm whether it exists
4. If the information isn't in the vault, say so clearly
5. Match the language of the user's query"""

        try:
            from outheis.core.llm import call_llm
            
            response = call_llm(
                model=self.model_alias,
                system=self.get_system_prompt(),
                messages=[{"role": "user", "content": user_content}],
                max_tokens=1024,
            )
            
            answer = response.content[0].text
            
            return self.respond(
                to=response_to,
                payload={
                    "answer": answer,
                    "sources": sources,
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
        context, sources = self._build_context(query)
        
        user_content = f"""The user wants to search their vault (notes, documents, files).

VAULT SEARCH RESULTS:
{context}

SOURCES FOUND:
{chr(10).join(f'- {s}' for s in sources) if sources else '(none)'}

USER QUERY:
{query}

Instructions:
1. Answer based on the vault search results above
2. ALWAYS mention the source file path when citing information (e.g., "In Projects/MyProject.md...")
3. If asked about a specific file or directory, confirm whether it exists
4. If nothing relevant was found, say so clearly
5. Match the language of the user's query"""

        try:
            from outheis.core.llm import call_llm
            
            response = call_llm(
                model=self.model_alias,
                system=self.get_system_prompt(),
                messages=[{"role": "user", "content": user_content}],
                max_tokens=1024,
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

def create_data_agent(model_alias: str = "capable") -> DataAgent:
    """Create a data agent instance."""
    return DataAgent(model_alias=model_alias)
