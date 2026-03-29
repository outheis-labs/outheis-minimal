"""
Search index for vault content.

Maintains a JSONL index of vault files for fast search.
Index is rebuilt on demand or when files change.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from outheis.core.vault import VaultFile, iter_vault_files


# =============================================================================
# INDEX ENTRY
# =============================================================================

@dataclass
class IndexEntry:
    """A single entry in the search index."""
    path: str  # Relative to vault root
    title: str
    tags: list[str]
    content_hash: str  # MD5 of content for change detection
    indexed_at: str  # ISO timestamp
    
    # Searchable text (title + tags + first N chars of body)
    searchable: str = ""
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "title": self.title,
            "tags": self.tags,
            "content_hash": self.content_hash,
            "indexed_at": self.indexed_at,
            "searchable": self.searchable,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> IndexEntry:
        return cls(
            path=data["path"],
            title=data["title"],
            tags=data.get("tags", []),
            content_hash=data["content_hash"],
            indexed_at=data["indexed_at"],
            searchable=data.get("searchable", ""),
        )
    
    @classmethod
    def from_vault_file(cls, vf: VaultFile, vault_root: Path) -> IndexEntry:
        """Create index entry from vault file."""
        content_hash = hashlib.md5(vf.content.encode()).hexdigest()
        
        try:
            rel_path = str(vf.path.relative_to(vault_root))
        except ValueError:
            rel_path = str(vf.path)
        
        # Build searchable text: path + title + tags + first 500 chars of body
        body_preview = vf.body[:500].replace("\n", " ").strip()
        searchable = f"{rel_path} {vf.title} {' '.join(vf.tags)} {body_preview}".lower()
        
        return cls(
            path=rel_path,
            title=vf.title,
            tags=vf.tags,
            content_hash=content_hash,
            indexed_at=datetime.now(timezone.utc).isoformat(),
            searchable=searchable,
        )


# =============================================================================
# SEARCH INDEX
# =============================================================================

@dataclass
class SearchIndex:
    """
    In-memory search index backed by JSONL file.
    
    Supports incremental updates: only reindex changed files.
    """
    vault_root: Path
    index_path: Path
    entries: dict[str, IndexEntry] = field(default_factory=dict)  # path -> entry
    
    def load(self) -> None:
        """Load index from disk."""
        self.entries.clear()
        
        if not self.index_path.exists():
            return
        
        with open(self.index_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entry = IndexEntry.from_dict(data)
                    self.entries[entry.path] = entry
                except (json.JSONDecodeError, KeyError):
                    continue
    
    def save(self) -> None:
        """Save index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.index_path, "w", encoding="utf-8") as f:
            for entry in self.entries.values():
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
    
    def rebuild(self) -> int:
        """
        Full rebuild of index from vault.
        
        Returns number of files indexed.
        """
        self.entries.clear()
        
        for vf in iter_vault_files(self.vault_root):
            entry = IndexEntry.from_vault_file(vf, self.vault_root)
            self.entries[entry.path] = entry
        
        self.save()
        return len(self.entries)
    
    def update(self) -> tuple[int, int, int]:
        """
        Incremental update: only reindex changed files.
        
        Returns (added, updated, removed) counts.
        """
        added = 0
        updated = 0
        removed = 0
        
        # Get current files
        current_files: dict[str, VaultFile] = {}
        for vf in iter_vault_files(self.vault_root):
            try:
                rel_path = str(vf.path.relative_to(self.vault_root))
            except ValueError:
                rel_path = str(vf.path)
            current_files[rel_path] = vf
        
        # Remove entries for deleted files
        for path in list(self.entries.keys()):
            if path not in current_files:
                del self.entries[path]
                removed += 1
        
        # Add/update entries
        for path, vf in current_files.items():
            content_hash = hashlib.md5(vf.content.encode()).hexdigest()
            
            existing = self.entries.get(path)
            if existing is None:
                # New file
                self.entries[path] = IndexEntry.from_vault_file(vf, self.vault_root)
                added += 1
            elif existing.content_hash != content_hash:
                # Changed file
                self.entries[path] = IndexEntry.from_vault_file(vf, self.vault_root)
                updated += 1
        
        self.save()
        return added, updated, removed
    
    def search(self, query: str, limit: int = 10) -> list[IndexEntry]:
        """
        Search index for matching entries.
        
        Simple substring matching on searchable text.
        Returns entries sorted by relevance (number of query term matches).
        """
        query_terms = query.lower().split()
        if not query_terms:
            return []
        
        results: list[tuple[int, IndexEntry]] = []
        
        for entry in self.entries.values():
            # Count matching terms
            score = sum(1 for term in query_terms if term in entry.searchable)
            if score > 0:
                results.append((score, entry))
        
        # Sort by score descending
        results.sort(key=lambda x: -x[0])
        
        return [entry for _, entry in results[:limit]]
    
    def search_by_tag(self, tag: str) -> list[IndexEntry]:
        """Find all entries with a specific tag."""
        tag_lower = tag.lower()
        return [
            entry for entry in self.entries.values()
            if any(t.lower() == tag_lower for t in entry.tags)
        ]
    
    def get_all_tags(self) -> dict[str, int]:
        """Get all tags with their counts."""
        tag_counts: dict[str, int] = {}
        for entry in self.entries.values():
            for tag in entry.tags:
                tag_lower = tag.lower()
                tag_counts[tag_lower] = tag_counts.get(tag_lower, 0) + 1
        return tag_counts
    
    def list_path(self, path: str = "") -> dict:
        """
        List contents of a path in the vault.
        
        Returns:
            {
                "exists": bool,
                "is_dir": bool,
                "files": [str],      # If directory
                "dirs": [str],       # If directory  
                "content": str,      # If file
            }
        """
        target = self.vault_root / path if path else self.vault_root
        
        if not target.exists():
            return {"exists": False}
        
        if target.is_file():
            return {
                "exists": True,
                "is_dir": False,
                "path": str(target.relative_to(self.vault_root)),
            }
        
        # It's a directory
        files = []
        dirs = []
        
        for item in sorted(target.iterdir()):
            if item.name.startswith("."):
                continue
            rel = str(item.relative_to(self.vault_root))
            if item.is_dir():
                dirs.append(rel)
            else:
                files.append(rel)
        
        return {
            "exists": True,
            "is_dir": True,
            "path": path or "/",
            "dirs": dirs,
            "files": files,
        }
    
    def find_by_path(self, pattern: str) -> list[IndexEntry]:
        """Find entries where path contains pattern."""
        pattern_lower = pattern.lower()
        return [
            entry for entry in self.entries.values()
            if pattern_lower in entry.path.lower()
        ]


# =============================================================================
# FACTORY
# =============================================================================

def create_index(vault_root: Path, index_path: Path | None = None) -> SearchIndex:
    """Create a search index for a vault."""
    if index_path is None:
        index_path = vault_root / ".index.jsonl"
    
    index = SearchIndex(vault_root=vault_root, index_path=index_path)
    index.load()
    return index
