"""
LLM client abstraction.

Provides a unified interface for different LLM providers:
- Anthropic (Claude)
- Ollama (local models)
- OpenAI (future)

Usage:
    from outheis.core.llm import get_client, call_llm
    
    # Simple call
    response = call_llm(
        model="fast",  # or "capable", or explicit model name
        messages=[{"role": "user", "content": "Hello"}],
    )
    
    # With tools
    response = call_llm(
        model="capable",
        system="You are helpful.",
        messages=[...],
        tools=[...],
    )
"""

from __future__ import annotations

import os
from typing import Any

from outheis.core.config import load_config, LLMConfig


def get_client(config: LLMConfig | None = None):
    """
    Get LLM client based on config.
    
    Returns appropriate client for the configured provider.
    """
    if config is None:
        config = load_config().llm
    
    if config.provider == "anthropic":
        import anthropic
        return anthropic.Anthropic()
    
    elif config.provider == "ollama":
        # Ollama uses OpenAI-compatible API
        import anthropic
        base_url = config.base_url or "http://localhost:11434/v1"
        return anthropic.Anthropic(
            base_url=base_url,
            api_key="ollama",  # Ollama doesn't need a real key
        )
    
    elif config.provider == "openai":
        raise NotImplementedError("OpenAI provider not yet implemented")
    
    else:
        raise ValueError(f"Unknown provider: {config.provider}")


def resolve_model(model: str, config: LLMConfig | None = None) -> str:
    """
    Resolve model alias to actual model name.
    
    Args:
        model: Model alias ("fast", "capable") or explicit model name
        config: LLM configuration (loaded from file if not provided)
    
    Returns:
        Actual model name to use
    """
    if config is None:
        config = load_config().llm
    
    return config.get_model(model)


def call_llm(
    model: str,
    messages: list[dict[str, Any]],
    system: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 4096,
    config: LLMConfig | None = None,
) -> Any:
    """
    Call LLM with messages.
    
    Args:
        model: Model alias ("fast", "capable") or explicit model name
        messages: List of message dicts with role/content
        system: System prompt (optional)
        tools: Tool definitions (optional)
        max_tokens: Maximum response tokens
        config: LLM configuration (loaded from file if not provided)
    
    Returns:
        API response object
    """
    if config is None:
        config = load_config().llm
    
    client = get_client(config)
    actual_model = resolve_model(model, config)
    
    kwargs: dict[str, Any] = {
        "model": actual_model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    
    if system:
        kwargs["system"] = system
    
    if tools:
        kwargs["tools"] = tools
    
    return client.messages.create(**kwargs)
