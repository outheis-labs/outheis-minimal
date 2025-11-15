"""
Dispatcher routing logic.

Routes messages to agents based on:
1. Explicit mention (@agent)
2. Keyword scoring
3. Fallback to Relay
"""

from __future__ import annotations

import re

from outheis.core.config import RoutingConfig
from outheis.core.message import AgentId, Message

# =============================================================================
# ROUTING
# =============================================================================

# Explicit mention patterns
MENTION_PATTERNS = {
    "relay": re.compile(r"@ou\b", re.IGNORECASE),
    "data": re.compile(r"@zeno\b", re.IGNORECASE),
    "agenda": re.compile(r"@cato\b", re.IGNORECASE),
    "action": re.compile(r"@hiro\b", re.IGNORECASE),
    "pattern": re.compile(r"@rumi\b", re.IGNORECASE),
}


def route(msg: Message, config: RoutingConfig) -> AgentId | None:
    """
    Determine which agent should handle a message.

    Returns None if Relay should decide (fallback).
    """
    text = msg.payload.get("text", "").lower()

    # 1. Check explicit mentions
    for agent, pattern in MENTION_PATTERNS.items():
        if pattern.search(text):
            return agent

    # 2. Keyword scoring
    scores = {
        "data": score_keywords(text, config.data),
        "agenda": score_keywords(text, config.agenda),
        "action": score_keywords(text, config.action),
    }

    best = max(scores, key=scores.get)

    if scores[best] >= config.threshold:
        return best

    # 3. Fallback: Relay decides
    return None


def score_keywords(text: str, keywords: list[str]) -> float:
    """
    Score text against keyword list.

    Simple implementation: count matches, normalize by keyword count.
    """
    if not keywords:
        return 0.0

    matches = sum(1 for kw in keywords if kw.lower() in text)
    return matches / len(keywords)


# =============================================================================
# DISPATCH TARGET
# =============================================================================

def get_dispatch_target(msg: Message, config: RoutingConfig) -> str:
    """
    Get the final dispatch target for a message.

    Returns agent ID or "relay" as fallback.
    """
    # Messages already addressed to a specific agent
    if msg.to not in ("dispatcher", "transport"):
        return msg.to

    # Route based on content
    target = route(msg, config)
    return target or "relay"
