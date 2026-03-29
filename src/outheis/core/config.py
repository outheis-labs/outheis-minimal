"""
Configuration management.

User config: ~/.outheis/human/config.json
System config: ~/.outheis/config.json (future)

Environment overrides:
  OUTHEIS_HUMAN_DIR — override human data directory
  OUTHEIS_VAULT — override vault path
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

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
# CONFIG DATACLASS
# =============================================================================

@dataclass
class UserConfig:
    """User configuration."""
    name: str = "User"
    language: str = "en"
    timezone: str = "UTC"
    vault: list[str] = field(default_factory=lambda: ["~/Documents/Vault"])

    # User's phone (for single-user mode authorization)
    phone: str | None = None

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
class SignalConfig:
    """Signal transport configuration."""
    enabled: bool = False
    bot_phone: str | None = None  # Bot's registered Signal number


@dataclass
class RoutingConfig:
    """Dispatcher routing configuration."""
    threshold: float = 0.3
    data: list[str] = field(default_factory=lambda: ["vault", "search", "find", "note"])
    agenda: list[str] = field(default_factory=lambda: ["appointment", "calendar", "tomorrow", "schedule"])
    action: list[str] = field(default_factory=lambda: ["send", "email", "open", "execute"])


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    model: str = "capable"
    run_mode: str = "on-demand"  # "daemon", "on-demand", "scheduled"
    enabled: bool = True


@dataclass
class Config:
    """Complete configuration."""
    user: UserConfig = field(default_factory=UserConfig)
    signal: SignalConfig = field(default_factory=SignalConfig)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    agents: dict[str, AgentConfig] = field(default_factory=dict)

    # System settings
    auto_migrate: bool = True
    migrate_schedule: str = "04:00"


# =============================================================================
# LOAD / SAVE
# =============================================================================

def load_config() -> Config:
    """Load configuration from file."""
    path = get_config_path()

    if not path.exists():
        return Config()

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    user = UserConfig(**data.get("user", {})) if "user" in data else UserConfig()
    signal = SignalConfig(**data.get("signal", {})) if "signal" in data else SignalConfig()
    routing = RoutingConfig(**data.get("routing", {})) if "routing" in data else RoutingConfig()

    agents = {}
    for name, cfg in data.get("agents", {}).items():
        agents[name] = AgentConfig(**cfg)

    return Config(
        user=user,
        signal=signal,
        routing=routing,
        agents=agents,
        auto_migrate=data.get("auto_migrate", True),
        migrate_schedule=data.get("migrate_schedule", "04:00"),
    )


def save_config(config: Config) -> None:
    """Save configuration to file."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "user": {
            "name": config.user.name,
            "language": config.user.language,
            "timezone": config.user.timezone,
            "vault": config.user.vault,
        },
        "routing": {
            "threshold": config.routing.threshold,
            "data": config.routing.data,
            "agenda": config.routing.agenda,
            "action": config.routing.action,
        },
        "agents": {
            name: {
                "model": cfg.model,
                "run_mode": cfg.run_mode,
                "enabled": cfg.enabled,
            }
            for name, cfg in config.agents.items()
        },
        "auto_migrate": config.auto_migrate,
        "migrate_schedule": config.migrate_schedule,
    }

    # User phone
    if config.user.phone:
        data["user"]["phone"] = config.user.phone

    # Signal config
    if config.signal.enabled or config.signal.bot_phone:
        data["signal"] = {
            "enabled": config.signal.enabled,
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
