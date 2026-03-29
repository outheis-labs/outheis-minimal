"""
LLM client abstraction.

Supports multiple providers per config:
- Anthropic (Claude)
- Ollama (local models)
- OpenAI (future)

Config is loaded once at startup. Call init_llm() from dispatcher.
"""

from __future__ import annotations

from typing import Any

from outheis.core.config import LLMConfig, ModelConfig, ProviderConfig


# =============================================================================
# GLOBAL STATE (set once at startup)
# =============================================================================

_config: LLMConfig | None = None
_clients: dict[str, Any] = {}  # provider_name -> client


def init_llm(config: LLMConfig) -> None:
    """
    Initialize LLM with config. Called once at dispatcher startup.
    """
    global _config, _clients
    _config = config
    _clients = {}  # Reset clients


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


def get_client(provider_name: str) -> Any:
    """
    Get LLM client for a provider. Creates on first use, then reuses.
    """
    global _clients
    
    if provider_name in _clients:
        return _clients[provider_name]
    
    config = get_llm_config()
    provider = config.get_provider(provider_name)
    
    if provider_name == "anthropic":
        import anthropic
        kwargs = {}
        if provider.api_key:
            kwargs["api_key"] = provider.api_key
        if provider.base_url:
            kwargs["base_url"] = provider.base_url
        _clients[provider_name] = anthropic.Anthropic(**kwargs)
    
    elif provider_name == "ollama":
        import anthropic
        base_url = provider.base_url or "http://localhost:11434/v1"
        _clients[provider_name] = anthropic.Anthropic(
            base_url=base_url,
            api_key="ollama",  # Ollama doesn't need a real key
        )
    
    elif provider_name == "openai":
        try:
            import openai
            kwargs = {}
            if provider.api_key:
                kwargs["api_key"] = provider.api_key
            if provider.base_url:
                kwargs["base_url"] = provider.base_url
            _clients[provider_name] = openai.OpenAI(**kwargs)
        except ImportError:
            raise ImportError("openai package not installed")
    
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return _clients[provider_name]


def resolve_model(alias: str) -> ModelConfig:
    """
    Resolve model alias to ModelConfig.
    
    Args:
        alias: Model alias ("fast", "capable") or explicit model name
    
    Returns:
        ModelConfig with provider, name, run_mode
    """
    config = get_llm_config()
    return config.get_model(alias)


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
    model_config = resolve_model(model)
    client = get_client(model_config.provider)
    
    kwargs: dict[str, Any] = {
        "model": model_config.name,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    
    if system:
        kwargs["system"] = system
    
    if tools:
        kwargs["tools"] = tools
    
    return client.messages.create(**kwargs)
