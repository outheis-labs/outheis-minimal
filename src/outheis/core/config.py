"""
Configuration management.

User config: ~/.outheis/human/config.json

Environment overrides:
  OUTHEIS_HUMAN_DIR — override human data directory
  OUTHEIS_VAULT — override vault path
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# =============================================================================
# PATHS
# =============================================================================

def get_outheis_dir() -> Path:
    """Get outheis system directory."""
    return Path(os.path.expanduser("~/.outheis"))


def get_human_dir() -> Path:
    """Get user data directory. Respects OUTHEIS_HUMAN_DIR env var."""
    override = os.environ.get("OUTHEIS_HUMAN_DIR")
    if override:
        return Path(os.path.expanduser(override))
    return get_outheis_dir() / "human"


def get_config_path() -> Path:
    """Get user config path."""
    return get_human_dir() / "config.json"


def get_messages_path() -> Path:
    """Get message queue path."""
    return get_human_dir() / "messages.jsonl"


def get_insights_path() -> Path:
    """Get insights path."""
    return get_human_dir() / "insights.jsonl"


def get_session_notes_path() -> Path:
    """Get session notes path."""
    return get_human_dir() / "session_notes.jsonl"


def get_rules_dir() -> Path:
    """Get user rules directory."""
    return get_human_dir() / "rules"


def get_archive_dir() -> Path:
    """Get archive directory."""
    return get_human_dir() / "archive"


# =============================================================================
# CONFIG DATACLASSES
# =============================================================================

@dataclass
class HumanConfig:
    """Human (administrator) configuration."""
    name: str = "Human"
    phone: list[str] = field(default_factory=list)  # One or more phone numbers
    language: str = "en"
    timezone: str = "Europe/Berlin"
    vault: list[str] = field(default_factory=lambda: ["~/Documents/Vault"])

    def primary_vault(self) -> Path:
        """Get primary vault path. Respects OUTHEIS_VAULT env var."""
        override = os.environ.get("OUTHEIS_VAULT")
        if override:
            return Path(os.path.expanduser(override))
        if not self.vault:
            return get_human_dir() / "vault"
        return Path(os.path.expanduser(self.vault[0]))

    def all_vaults(self) -> list[Path]:
        """Get all vault paths, expanded. Respects OUTHEIS_VAULT env var."""
        override = os.environ.get("OUTHEIS_VAULT")
        if override:
            return [Path(os.path.expanduser(override))]
        return [Path(os.path.expanduser(v)) for v in self.vault]


@dataclass
class AllowedContact:
    """An allowed Signal contact."""
    name: str
    phone: str


@dataclass
class SignalConfig:
    """Signal transport configuration."""
    enabled: bool = False
    bot_phone: str | None = None
    bot_name: str = "Ou"
    allowed: list[AllowedContact] = field(default_factory=list)  # Additional allowed contacts


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""
    api_key: str | None = None
    base_url: str | None = None


@dataclass
class ModelConfig:
    """Configuration for a single model alias."""
    provider: str  # "anthropic", "ollama", "openai"
    name: str  # e.g. "claude-sonnet-4-20250514", "llama3.2:3b"
    run_mode: str = "on-demand"  # "on-demand", "persistent"


@dataclass
class LLMConfig:
    """LLM providers and model aliases."""
    providers: dict[str, ProviderConfig] = field(default_factory=lambda: {
        "anthropic": ProviderConfig(),
    })
    models: dict[str, ModelConfig] = field(default_factory=lambda: {
        "fast": ModelConfig(provider="anthropic", name="claude-haiku-4-5"),
        "capable": ModelConfig(provider="anthropic", name="claude-sonnet-4-20250514"),
    })

    def get_model(self, alias: str) -> ModelConfig:
        """Get model config for alias. Raises KeyError if not found."""
        if alias in self.models:
            return self.models[alias]
        # Allow direct model name as fallback
        return ModelConfig(provider="anthropic", name=alias)
    
    def get_provider(self, name: str) -> ProviderConfig:
        """Get provider config. Returns empty config if not found."""
        return self.providers.get(name, ProviderConfig())


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    name: str  # Display name (e.g. "ou", "zeno")
    model: str = "capable"  # Model alias
    enabled: bool = True


@dataclass
class UpdatesConfig:
    """Memory migration and housekeeping settings."""
    auto_migrate: bool = True
    schedule: str = "04:00"


@dataclass
class Config:
    """Complete configuration."""
    human: HumanConfig = field(default_factory=HumanConfig)
    signal: SignalConfig = field(default_factory=SignalConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    agents: dict[str, AgentConfig] = field(default_factory=lambda: {
        "relay": AgentConfig(name="ou", model="fast"),
        "data": AgentConfig(name="zeno", model="capable"),
        "agenda": AgentConfig(name="cato", model="capable"),
        "action": AgentConfig(name="hiro", model="capable", enabled=False),
        "pattern": AgentConfig(name="rumi", model="capable"),
    })
    updates: UpdatesConfig = field(default_factory=UpdatesConfig)


# =============================================================================
# LOAD / SAVE
# =============================================================================

def _parse_providers(data: dict) -> dict[str, ProviderConfig]:
    """Parse providers from config data."""
    result = {}
    for name, cfg in data.items():
        if isinstance(cfg, dict):
            result[name] = ProviderConfig(
                api_key=cfg.get("api_key"),
                base_url=cfg.get("base_url"),
            )
        else:
            result[name] = ProviderConfig()
    return result


def _parse_models(data: dict) -> dict[str, ModelConfig]:
    """Parse models from config data."""
    result = {}
    for alias, cfg in data.items():
        if isinstance(cfg, dict):
            result[alias] = ModelConfig(
                provider=cfg.get("provider", "anthropic"),
                name=cfg.get("name", alias),
                run_mode=cfg.get("run_mode", "on-demand"),
            )
    return result


def _parse_agents(data: dict) -> dict[str, AgentConfig]:
    """Parse agents from config data."""
    result = {}
    for role, cfg in data.items():
        if isinstance(cfg, dict):
            result[role] = AgentConfig(
                name=cfg.get("name", role),
                model=cfg.get("model", "capable"),
                enabled=cfg.get("enabled", True),
            )
    return result


def load_config() -> Config:
    """Load configuration from file."""
    path = get_config_path()

    if not path.exists():
        return Config()

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # User
    human_data = data.get("human", {})
    # Handle phone as string or list
    phone_raw = human_data.get("phone", [])
    if isinstance(phone_raw, str):
        phone_list = [phone_raw] if phone_raw else []
    else:
        phone_list = phone_raw or []
    
    user = HumanConfig(
        name=human_data.get("name", "Human"),
        phone=phone_list,
        language=human_data.get("language", "en"),
        timezone=human_data.get("timezone", "Europe/Berlin"),
        vault=human_data.get("vault", ["~/Documents/Vault"]),
    )

    # Signal
    signal_data = data.get("signal", {})
    allowed_raw = signal_data.get("allowed", [])
    allowed = [
        AllowedContact(name=c.get("name", ""), phone=c.get("phone", ""))
        for c in allowed_raw if isinstance(c, dict)
    ]
    signal = SignalConfig(
        enabled=signal_data.get("enabled", False),
        bot_phone=signal_data.get("bot_phone"),
        bot_name=signal_data.get("bot_name", "Ou"),
        allowed=allowed,
    )

    # LLM
    llm_data = data.get("llm", {})
    llm = LLMConfig(
        providers=_parse_providers(llm_data.get("providers", {})),
        models=_parse_models(llm_data.get("models", {})),
    )
    # Use defaults if empty
    if not llm.providers:
        llm.providers = {"anthropic": ProviderConfig()}
    if not llm.models:
        llm.models = {
            "fast": ModelConfig(provider="anthropic", name="claude-haiku-4-5"),
            "capable": ModelConfig(provider="anthropic", name="claude-sonnet-4-20250514"),
        }

    # Agents
    agents = _parse_agents(data.get("agents", {}))
    # Use defaults if empty
    if not agents:
        agents = {
            "relay": AgentConfig(name="ou", model="fast"),
            "data": AgentConfig(name="zeno", model="capable"),
            "agenda": AgentConfig(name="cato", model="capable"),
            "action": AgentConfig(name="hiro", model="capable", enabled=False),
            "pattern": AgentConfig(name="rumi", model="capable"),
        }

    # Updates
    updates_data = data.get("updates", {})
    updates = UpdatesConfig(
        auto_migrate=updates_data.get("auto_migrate", True),
        schedule=updates_data.get("schedule", "04:00"),
    )

    return Config(
        user=user,
        signal=signal,
        llm=llm,
        agents=agents,
        updates=updates,
    )


def save_config(config: Config) -> None:
    """Save configuration to file."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "human": {
            "name": config.human.name,
            "language": config.human.language,
            "timezone": config.human.timezone,
            "vault": config.human.vault,
        },
        "llm": {
            "providers": {
                name: {
                    k: v for k, v in [
                        ("api_key", p.api_key),
                        ("base_url", p.base_url),
                    ] if v is not None
                }
                for name, p in config.llm.providers.items()
            },
            "models": {
                alias: {
                    "provider": m.provider,
                    "name": m.name,
                    "run_mode": m.run_mode,
                }
                for alias, m in config.llm.models.items()
            },
        },
        "agents": {
            role: {
                "name": a.name,
                "model": a.model,
                "enabled": a.enabled,
            }
            for role, a in config.agents.items()
        },
        "updates": {
            "auto_migrate": config.updates.auto_migrate,
            "schedule": config.updates.schedule,
        },
    }

    # User phone
    if config.human.phone:
        data["user"]["phone"] = config.human.phone

    # Signal config
    if config.signal.enabled or config.signal.bot_phone:
        data["signal"] = {
            "enabled": config.signal.enabled,
            "bot_name": config.signal.bot_name,
        }
        if config.signal.bot_phone:
            data["signal"]["bot_phone"] = config.signal.bot_phone

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_directories() -> None:
    """Create required directories if they don't exist."""
    dirs = [
        get_outheis_dir(),
        get_human_dir(),
        get_human_dir() / "vault",
        get_human_dir() / "rules",
        get_human_dir() / "archive",
        get_human_dir() / "cache",
        get_human_dir() / "imports",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Create default config if needed
    if not get_config_path().exists():
        save_config(Config())
