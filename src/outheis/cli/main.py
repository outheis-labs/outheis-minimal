"""
CLI application.

Entry point for outheis command-line interface.
"""

from __future__ import annotations

import typer

from outheis import __version__

app = typer.Typer(
    name="outheis",
    help="Multi-agent personal assistant",
    no_args_is_help=True,
)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
    ),
) -> None:
    """outheis — Multi-agent personal assistant."""
    if version:
        typer.echo(f"outheis {__version__}")
        raise typer.Exit()


@app.command()
def init() -> None:
    """Interactive setup wizard for outheis."""
    import os
    import shutil
    import subprocess
    
    from outheis.core.config import (
        Config,
        HumanConfig,
        SignalConfig,
        AllowedContact,
        LLMConfig,
        ProviderConfig,
        ModelConfig,
        AgentConfig,
        UpdatesConfig,
        get_config_path,
        get_human_dir,
        load_config,
        save_config,
        init_directories,
    )
    
    typer.echo("\n" + "=" * 50)
    typer.echo("Welcome to outheis!")
    typer.echo("=" * 50)
    typer.echo("\nThis wizard will guide you through the setup.")
    typer.echo("Press Enter to keep existing values shown in [brackets].\n")
    typer.echo("Configure via web instead: http://localhost:8080/setup")
    typer.echo("(Web interface coming in a future release)\n")
    
    # Load existing config or create new
    init_directories()
    try:
        config = load_config()
    except Exception:
        config = Config()
    
    # === HUMAN SECTION ===
    typer.echo("─" * 50)
    typer.echo("Human (Administrator)")
    typer.echo("─" * 50 + "\n")
    
    # Name
    default_name = config.human.name or "Human"
    name = typer.prompt("Your name", default=default_name)
    
    # Language
    default_lang = config.human.language or "en"
    language = typer.prompt("Language (en/de)", default=default_lang)
    
    # Timezone
    default_tz = config.human.timezone or "Europe/Berlin"
    timezone = typer.prompt("Timezone", default=default_tz)
    
    # Phone(s)
    default_phones = ", ".join(config.human.phone) if config.human.phone else ""
    phones_str = typer.prompt("Your phone number(s), comma-separated", default=default_phones or "")
    phones = [p.strip() for p in phones_str.split(",") if p.strip()]
    
    # Vault
    default_vault = config.human.vault[0] if config.human.vault else "~/Documents/Vault"
    vault_path = typer.prompt("Vault path", default=default_vault)
    
    # Update human config
    config.human = HumanConfig(
        name=name,
        phone=phones,
        language=language,
        timezone=timezone,
        vault=[vault_path],
    )
    
    # === LLM SECTION ===
    typer.echo("\n" + "─" * 50)
    typer.echo("LLM Configuration")
    typer.echo("─" * 50 + "\n")
    typer.echo("outheis uses Anthropic Claude by default.")
    typer.echo("You can switch to local models (Ollama) later.\n")
    
    # API Key
    existing_key = config.llm.providers.get("anthropic", ProviderConfig()).api_key
    if existing_key:
        masked = f"{existing_key[:10]}...{existing_key[-4:]}"
    else:
        masked = ""
    
    api_key_input = typer.prompt(
        "Anthropic API key",
        default=masked or "",
        hide_input=False,
    )
    
    # If user entered something new (not the masked version), use it
    if api_key_input and api_key_input != masked:
        api_key = api_key_input
    else:
        api_key = existing_key
    
    # Validate API key
    if api_key:
        typer.echo("Validating API key...", nl=False)
        if _validate_anthropic_key(api_key):
            typer.echo(" ✓")
        else:
            typer.echo(" ✗ invalid")
            if not typer.confirm("Continue anyway?"):
                raise typer.Exit(1)
    
    # Update LLM config
    config.llm.providers["anthropic"] = ProviderConfig(api_key=api_key)
    
    # === SIGNAL SECTION ===
    typer.echo("\n" + "─" * 50)
    typer.echo("Signal Messenger (optional)")
    typer.echo("─" * 50 + "\n")
    
    # Check if signal-cli is installed
    signal_cli_path = shutil.which("signal-cli")
    if signal_cli_path:
        typer.echo(f"✓ signal-cli found: {signal_cli_path}\n")
        
        default_enabled = "y" if config.signal.enabled else "n"
        enable_signal = typer.confirm("Enable Signal?", default=config.signal.enabled)
        
        if enable_signal:
            # Bot phone
            default_bot_phone = config.signal.bot_phone or ""
            bot_phone = typer.prompt("Bot phone number", default=default_bot_phone)
            
            # Check registration
            if bot_phone:
                typer.echo(f"Checking registration for {bot_phone}...", nl=False)
                registered = _check_signal_registration(bot_phone)
                
                if registered:
                    typer.echo(" ✓ registered")
                else:
                    typer.echo(" ✗ not registered")
                    if typer.confirm("Register now?"):
                        _register_signal(bot_phone)
            
            # Bot name
            default_bot_name = config.signal.bot_name or "Ou"
            bot_name = typer.prompt("Bot display name", default=default_bot_name)
            
            config.signal = SignalConfig(
                enabled=True,
                bot_phone=bot_phone,
                bot_name=bot_name,
                allowed=config.signal.allowed,  # Keep existing whitelist
            )
        else:
            config.signal.enabled = False
    else:
        typer.echo("ℹ signal-cli not found — skipping Signal setup")
        typer.echo("  Install: brew install signal-cli (macOS)")
        typer.echo("           or see https://github.com/AsamK/signal-cli\n")
    
    # === SAVE CONFIG ===
    save_config(config)
    typer.echo("\n" + "─" * 50)
    typer.echo("Setup complete!")
    typer.echo("─" * 50 + "\n")
    typer.echo(f"✓ Config saved to {get_config_path()}")
    
    # Create Agenda files if vault exists
    vault_expanded = os.path.expanduser(vault_path)
    agenda_dir = os.path.join(vault_expanded, "Agenda")
    
    if os.path.exists(vault_expanded):
        os.makedirs(agenda_dir, exist_ok=True)
        
        daily_path = os.path.join(agenda_dir, "Daily.md")
        if not os.path.exists(daily_path):
            with open(daily_path, "w") as f:
                f.write("# Daily\n\n## Today\n\n## Tomorrow\n")
            typer.echo(f"✓ Created {daily_path}")
        else:
            typer.echo(f"⏭ {daily_path} exists, skipping")
        
        inbox_path = os.path.join(agenda_dir, "Inbox.md")
        if not os.path.exists(inbox_path):
            with open(inbox_path, "w") as f:
                f.write("# Inbox\n\n")
            typer.echo(f"✓ Created {inbox_path}")
        else:
            typer.echo(f"⏭ {inbox_path} exists, skipping")
    else:
        typer.echo(f"⚠ Vault {vault_expanded} does not exist — create it manually")
    
    typer.echo(f"\nRun 'outheis start' to begin.\n")


def _validate_anthropic_key(api_key: str) -> bool:
    """Validate Anthropic API key with a minimal request."""
    if not api_key or not api_key.startswith("sk-ant-"):
        return False
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )
        return True
    except Exception:
        return False


def _check_signal_registration(phone: str) -> bool:
    """Check if a phone number is registered with signal-cli."""
    import subprocess
    try:
        result = subprocess.run(
            ["signal-cli", "-a", phone, "listAccounts"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return phone in result.stdout
    except Exception:
        return False


def _register_signal(phone: str) -> bool:
    """Register a phone number with signal-cli."""
    import subprocess
    
    typer.echo(f"\nRegistering {phone} with Signal...")
    typer.echo("Signal will send an SMS with a verification code.\n")
    
    use_voice = typer.confirm("Use voice call instead of SMS?", default=False)
    
    try:
        # Request verification
        cmd = ["signal-cli", "-a", phone, "register"]
        if use_voice:
            cmd.append("--voice")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            typer.echo(f"Error: {result.stderr}")
            return False
        
        # Get code from user
        code = typer.prompt("Enter verification code")
        
        # Verify
        result = subprocess.run(
            ["signal-cli", "-a", phone, "verify", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            typer.echo("✓ Registration successful!")
            return True
        else:
            typer.echo(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        typer.echo("Timeout — try again later")
        return False
    except Exception as e:
        typer.echo(f"Error: {e}")
        return False


@app.command()
def start(
    foreground: bool = typer.Option(
        False,
        "--foreground",
        "-f",
        help="Run in foreground (don't daemonize)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable debug output (routing, delegation)",
    ),
    human_dir: str = typer.Option(
        None,
        "--human",
        help="Override human data directory (default: ~/.outheis/human)",
    ),
    vault_path: str = typer.Option(
        None,
        "--vault",
        help="Override vault path",
    ),
) -> None:
    """Start the outheis dispatcher daemon."""
    import os
    from outheis.core.config import init_directories
    from outheis.dispatcher.daemon import start_daemon

    # Set environment overrides
    if human_dir:
        os.environ["OUTHEIS_HUMAN_DIR"] = human_dir
    if vault_path:
        os.environ["OUTHEIS_VAULT"] = vault_path
    if verbose:
        os.environ["OUTHEIS_VERBOSE"] = "1"

    init_directories()

    if foreground:
        typer.echo("Starting dispatcher in foreground (Ctrl+C to stop)...")

    success = start_daemon(foreground=foreground)
    if not success and not foreground:
        raise typer.Exit(1)


@app.command()
def stop() -> None:
    """Stop the outheis dispatcher daemon."""
    from outheis.dispatcher.daemon import stop_daemon

    success = stop_daemon()
    if not success:
        raise typer.Exit(1)


@app.command()
def send(
    message: str = typer.Argument(..., help="Message to send"),
    timeout: float = typer.Option(60.0, "--timeout", "-t", help="Response timeout in seconds"),
) -> None:
    """Send a message and wait for response."""
    import sys
    import time
    
    from outheis.dispatcher.daemon import daemon_status
    from outheis.transport.cli import CLITransport

    # Check if daemon is running
    status = daemon_status()
    if not status["running"]:
        typer.echo("Dispatcher not running. Start it with: outheis start")
        raise typer.Exit(1)

    transport = CLITransport()
    msg = transport.send(message)

    # Wait for response with progress indicator
    # Braille column animation: ⡀ → ⡄ → ⡆ → ⡇ → ⣇ → ⣧ → ⣷ → ⣿ → ⣾ → ⣼ → ⣸ → ⣰ → ⣠ → ⣀ → ⢀ → (space) → repeat
    start = time.time()
    spinner = ['⡀', '⡄', '⡆', '⡇', '⣇', '⣧', '⣷', '⣿', '⣾', '⣼', '⣸', '⣰', '⣠', '⣀', '⢀', ' ']
    spinner_idx = 0
    
    while time.time() - start < timeout:
        # Check for response
        response = transport.check_for_response(msg.id)
        if response:
            # Clear spinner line
            sys.stdout.write('\r' + ' ' * 40 + '\r')
            sys.stdout.flush()
            
            # Display response
            text = response.payload.get('text') or response.payload.get('answer', '')
            if response.payload.get('error'):
                typer.echo(f"[Error: {text}]")
            else:
                typer.echo(text)
            return
        
        # Show spinner with elapsed time
        elapsed = int(time.time() - start)
        sys.stdout.write(f'\r{spinner[spinner_idx]} Waiting for response... ({elapsed}s)')
        sys.stdout.flush()
        spinner_idx = (spinner_idx + 1) % len(spinner)
        time.sleep(0.3)
    
    # Timeout
    sys.stdout.write('\r' + ' ' * 40 + '\r')
    sys.stdout.flush()
    typer.echo("[no response within timeout]")


@app.command()
def chat() -> None:
    """Start interactive chat session (requires running dispatcher)."""
    import readline
    from outheis.dispatcher.daemon import daemon_status
    from outheis.transport.cli import CLITransport

    # Check if daemon is running
    status = daemon_status()
    if not status["running"]:
        typer.echo("Dispatcher not running. Start it with: outheis start")
        raise typer.Exit(1)

    # Configure readline for history
    readline.set_history_length(10)
    
    typer.echo("outheis CLI (type 'exit' to quit)")
    typer.echo("-" * 40)

    transport = CLITransport()

    while True:
        try:
            text = input("\n>: ").strip()

            if not text:
                continue

            if text.lower() in ("exit", "quit", "q"):
                break

            msg = transport.send(text)
            response = transport.wait_for_response(msg.id, timeout=30.0)

            if response:
                text = response.payload.get('text') or response.payload.get('answer', '')
                if response.payload.get('error'):
                    typer.echo(f"[Error: {text}]")
                else:
                    typer.echo(f"\n{text}")
            else:
                typer.echo("[no response]")

        except KeyboardInterrupt:
            typer.echo("\n[interrupted]")
            break
        except EOFError:
            break

    typer.echo("\nGoodbye.")


@app.command()
def status() -> None:
    """Show system status."""
    from outheis.core.config import (
        get_messages_path,
        load_config,
    )
    from outheis.core.queue import message_count, queue_size
    from outheis.dispatcher.daemon import daemon_status

    config = load_config()
    queue_path = get_messages_path()
    dstatus = daemon_status()

    typer.echo("outheis status")
    typer.echo("-" * 40)

    # Daemon status
    if dstatus["running"]:
        typer.echo(f"Dispatcher: running (PID {dstatus['pid']})")
    else:
        typer.echo("Dispatcher: stopped")

    typer.echo()
    typer.echo(f"User: {config.human.name}")
    typer.echo(f"Language: {config.human.language}")
    typer.echo(f"Timezone: {config.human.timezone}")
    typer.echo(f"Primary vault: {config.human.primary_vault()}")
    typer.echo()
    typer.echo(f"Messages: {message_count(queue_path)}")
    typer.echo(f"Queue size: {queue_size(queue_path)} bytes")


@app.command()
def migrate(
    scan: bool = typer.Option(False, "--scan", help="Scan for outdated records"),
    apply: bool = typer.Option(False, "--apply", help="Apply migrations"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
) -> None:
    """Scan for and apply schema migrations."""
    from outheis.core.config import get_insights_path, get_messages_path
    from outheis.core.schema import (
        INSIGHTS_VERSION,
        MESSAGES_VERSION,
        scan_file,
    )

    files_to_scan = [
        (get_messages_path(), "Message", MESSAGES_VERSION),
        (get_insights_path(), "Insight", INSIGHTS_VERSION),
    ]

    total_outdated = 0

    for path, record_type, current_version in files_to_scan:
        if not path.exists():
            continue

        report = scan_file(str(path), record_type, current_version)
        total_outdated += report.outdated

        if not quiet and report.outdated > 0:
            typer.echo(
                f"Found {report.outdated} {record_type}s at old version "
                f"(current: v{current_version})"
            )
            for v, count in sorted(report.versions_found.items()):
                if v < current_version:
                    typer.echo(f"  v{v}: {count} records")

    if scan and not apply:
        if total_outdated == 0:
            typer.echo("All records up to date.")
        else:
            typer.echo(f"\nTotal: {total_outdated} outdated records")
            typer.echo("Run 'outheis migrate --apply' to convert")
        return

    if apply:
        if total_outdated == 0:
            if not quiet:
                typer.echo("Nothing to migrate.")
            return

        # TODO: Implement actual migration
        typer.echo("Migration not yet implemented.")
        typer.echo("Records will be migrated on-the-fly when read.")


@app.command()
def pattern(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
) -> None:
    """Run Pattern agent reflection (normally scheduled at 04:00)."""
    from outheis.agents.pattern import create_pattern_agent

    typer.echo("Running Pattern agent...")

    agent = create_pattern_agent()

    if dry_run:
        typer.echo("[dry-run] Would analyze recent conversations")
        typer.echo("[dry-run] Would extract memories")
        return

    count = agent.analyze_recent_conversations()
    typer.echo(f"Extracted {count} new memory entries.")


@app.command()
def memory(
    show: bool = typer.Option(True, "--show", "-s", help="Show current memory"),
    add: str = typer.Option(None, "--add", "-a", help="Add memory entry (format: type:content)"),
    clear: str = typer.Option(None, "--clear", "-c", help="Clear memory type (user/feedback/context)"),
) -> None:
    """View and manage persistent memory."""
    from outheis.core.memory import get_memory_store
    
    store = get_memory_store()
    
    if add:
        # Parse "type:content" format
        if ":" not in add:
            typer.echo("Format: --add 'type:content' (type = user/feedback/context)")
            raise typer.Exit(1)
        
        memory_type, content = add.split(":", 1)
        memory_type = memory_type.strip().lower()
        content = content.strip()
        
        if memory_type not in ["user", "feedback", "context"]:
            typer.echo(f"Invalid type: {memory_type}. Use user/feedback/context.")
            raise typer.Exit(1)
        
        store.add(content, memory_type)
        typer.echo(f"Added to {memory_type}: {content}")
        return
    
    if clear:
        if clear not in ["user", "feedback", "context", "all"]:
            typer.echo("Use: --clear user/feedback/context/all")
            raise typer.Exit(1)
        
        if clear == "all":
            for mt in ["user", "feedback", "context"]:
                store.clear(mt)
            typer.echo("Cleared all memory.")
        else:
            store.clear(clear)
            typer.echo(f"Cleared {clear} memory.")
        return
    
    # Show memory
    typer.echo("Memory")
    typer.echo("-" * 40)
    
    for memory_type in ["user", "feedback", "context"]:
        entries = store.get(memory_type)
        typer.echo(f"\n[{memory_type}] ({len(entries)} entries)")
        for i, entry in enumerate(entries):
            # Build status indicators
            markers = []
            if entry.is_explicit:
                markers.append("!")
            if entry.confidence < 1.0:
                markers.append(f"{entry.confidence:.0%}")
            if entry.decay_days:
                from datetime import datetime, timedelta
                expiry = entry.updated_at + timedelta(days=entry.decay_days)
                days_left = (expiry - datetime.now()).days
                if days_left > 0:
                    markers.append(f"↓{days_left}d")
                else:
                    markers.append("expired")
            
            status = f" [{', '.join(markers)}]" if markers else ""
            typer.echo(f"  {i+1}. {entry.content}{status}")
    
    typer.echo()


@app.command()
def rules(
    agent: str = typer.Argument(None, help="Agent name (relay, data, agenda, action, pattern)"),
    user_only: bool = typer.Option(False, "--user", "-u", help="Show only user rules"),
    system_only: bool = typer.Option(False, "--system", "-s", help="Show only system rules"),
) -> None:
    """View rules for agents."""
    from outheis.agents.loader import (
        get_system_rules_dir,
        get_user_rules_dir,
        list_user_rules,
    )
    
    system_dir = get_system_rules_dir()
    user_dir = get_user_rules_dir()
    
    agents = ["common", "relay", "data", "agenda", "action", "pattern"]
    
    if agent:
        if agent not in agents:
            typer.echo(f"Unknown agent: {agent}. Use: {', '.join(agents)}")
            raise typer.Exit(1)
        agents = [agent]
    
    for ag in agents:
        typer.echo(f"\n{'='*40}")
        typer.echo(f"[{ag}]")
        typer.echo('='*40)
        
        # System rules
        if not user_only:
            system_file = system_dir / f"{ag}.md"
            if system_file.exists():
                typer.echo("\n## System Rules")
                content = system_file.read_text()
                # Show first 500 chars or summary
                if len(content) > 500:
                    typer.echo(content[:500] + "\n...")
                else:
                    typer.echo(content)
            else:
                typer.echo("\n## System Rules: (none)")
        
        # User rules
        if not system_only:
            user_file = user_dir / f"{ag}.md"
            if user_file.exists():
                typer.echo("\n## User Rules (emergent)")
                typer.echo(user_file.read_text())
            else:
                typer.echo("\n## User Rules: (none yet)")
    
    typer.echo()


if __name__ == "__main__":
    app()
