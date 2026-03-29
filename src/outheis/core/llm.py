"""
LLM client abstraction.

Provides a unified interface for different LLM providers:
- Anthropic (Claude)
- Ollama (local models)
- OpenAI (future)

Config is loaded once at startup. Call init_llm() from dispatcher.

Usage:
    from outheis.core.llm import call_llm
    
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

from typing import Any

from outheis.core.config import LLMConfig


# =============================================================================
# GLOBAL STATE (set once at startup)
# =============================================================================

_config: LLMConfig | None = None
_client: Any = None


def init_llm(config: LLMConfig) -> None:
    """
    Initialize LLM with config. Called once at dispatcher startup.
    """
    global _config, _client
    _config = config
    _client = None  # Will be created on first use


def get_llm_config() -> LLMConfig:
    """
    Get LLM config.
    
    Returns cached config, or loads from file if not initialized.
    """
    global _config
    if _config is None:
        from outheis.core.config import load_config
        _config = load_config().llm
    return _config


def get_client() -> Any:
    """
    Get LLM client. Creates on first use, then reuses.
    """
    global _client
    
    if _client is not None:
        return _client
    
    config = get_llm_config()
    
    if config.provider == "anthropic":
        import anthropic
        _client = anthropic.Anthropic()
    
    elif config.provider == "ollama":
        # Ollama uses OpenAI-compatible API
        import anthropic
        base_url = config.base_url or "http://localhost:11434/v1"
        _client = anthropic.Anthropic(
            base_url=base_url,
            api_key="ollama",  # Ollama doesn't need a real key
        )
    
    elif config.provider == "openai":
        raise NotImplementedError("OpenAI provider not yet implemented")
    
    else:
        raise ValueError(f"Unknown provider: {config.provider}")
    
    return _client


def resolve_model(model: str) -> str:
    """
    Resolve model alias to actual model name.
    
    Args:
        model: Model alias ("fast", "capable") or explicit model name
    
    Returns:
        Actual model name to use
    """
    config = get_llm_config()
    return config.get_model(model)


def call_llm(
    model: str,
    messages: list[dict[str, Any]],
    system: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 4096,
) -> Any:
    """
    Call LLM with messages.
    
    Args:
        model: Model alias ("fast", "capable") or explicit model name
        messages: List of message dicts with role/content
        system: System prompt (optional)
        tools: Tool definitions (optional)
        max_tokens: Maximum response tokens
    
    Returns:
        API response object
    """
    client = get_client()
    actual_model = resolve_model(model)
    
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
