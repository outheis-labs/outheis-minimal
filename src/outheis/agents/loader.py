"""
Rules loader.

Loads and combines system rules and user rules for agents.

System Rules: src/outheis/agents/rules/*.md (developer-defined)
User Rules: ~/.outheis/human/rules/*.md (emergent from interaction)
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from outheis.core.config import get_human_dir


# =============================================================================
# PATHS
# =============================================================================

def get_system_rules_dir() -> Path:
    """Get system rules directory (in package)."""
    return Path(__file__).parent / "rules"


def get_user_rules_dir() -> Path:
    """Get user rules directory."""
    return get_human_dir() / "rules"


# =============================================================================
# LOADING
# =============================================================================

def _load_markdown(path: Path) -> str:
    """Load markdown file, return empty string if not found."""
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


@lru_cache(maxsize=16)
def _load_system_rule(name: str) -> str:
    """Load a system rule file (cached)."""
    path = get_system_rules_dir() / f"{name}.md"
    return _load_markdown(path)


def _load_user_rule(name: str) -> str:
    """Load a user rule file (not cached — may change)."""
    path = get_user_rules_dir() / f"{name}.md"
    return _load_markdown(path)


def load_rules(agent_name: str) -> str:
    """
    Load combined rules for an agent.
    
    Combines:
    1. System common rules
    2. System agent-specific rules
    3. User common rules
    4. User agent-specific rules
    
    Returns formatted string for system prompt.
    """
    parts = []
    
    # System rules (from package)
    system_common = _load_system_rule("common")
    system_agent = _load_system_rule(agent_name)
    
    if system_common:
        parts.append(system_common)
    if system_agent:
        parts.append(system_agent)
    
    # User rules (from ~/.outheis/human/rules/)
    user_common = _load_user_rule("common")
    user_agent = _load_user_rule(agent_name)
    
    if user_common or user_agent:
        parts.append("\n# User Preferences\n")
        if user_common:
            parts.append(user_common)
        if user_agent:
            parts.append(user_agent)
    
    return "\n\n".join(parts)


def get_full_system_prompt(agent_name: str, memory_context: str = "") -> str:
    """
    Get complete system prompt for an agent.
    
    Combines:
    - Rules (system + user)
    - Memory context
    """
    rules = load_rules(agent_name)
    
    if memory_context:
        return f"{rules}\n\n{memory_context}"
    
    return rules


# =============================================================================
# USER RULES MANAGEMENT
# =============================================================================

def ensure_user_rules_dir() -> Path:
    """Ensure user rules directory exists."""
    path = get_user_rules_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_user_rule(agent_name: str, content: str) -> Path:
    """
    Write or update a user rule file.
    
    Used by Pattern agent to persist emergent rules.
    """
    ensure_user_rules_dir()
    path = get_user_rules_dir() / f"{agent_name}.md"
    path.write_text(content, encoding="utf-8")
    return path


def append_user_rule(agent_name: str, rule: str) -> None:
    """
    Append a rule to a user rule file.
    
    Creates file if it doesn't exist.
    """
    ensure_user_rules_dir()
    path = get_user_rules_dir() / f"{agent_name}.md"
    
    existing = _load_markdown(path)
    
    if existing:
        # Check if rule already exists
        if rule.strip() in existing:
            return
        new_content = f"{existing}\n- {rule.strip()}"
    else:
        new_content = f"# User Rules for {agent_name}\n\n- {rule.strip()}"
    
    path.write_text(new_content, encoding="utf-8")


def list_user_rules() -> dict[str, list[str]]:
    """
    List all user rules by agent.
    
    Returns dict mapping agent name to list of rules.
    """
    rules_dir = get_user_rules_dir()
    if not rules_dir.exists():
        return {}
    
    result = {}
    for path in rules_dir.glob("*.md"):
        agent_name = path.stem
        content = _load_markdown(path)
        
        # Extract rule lines (starting with -)
        rules = [
            line.strip()[1:].strip() 
            for line in content.split("\n") 
            if line.strip().startswith("-")
        ]
        
        if rules:
            result[agent_name] = rules
    
    return result
