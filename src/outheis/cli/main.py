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
    """Initialize outheis directories and config."""
    from outheis.core.config import get_config_path, init_directories

    init_directories()
    typer.echo("Initialized outheis at ~/.outheis")
    typer.echo(f"Config: {get_config_path()}")


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
def signal() -> None:
    """Start Signal transport (requires dispatcher running)."""
    from outheis.core.config import load_config
    from outheis.dispatcher.daemon import daemon_status
    from outheis.transport.signal import SignalTransport

    # Check if daemon is running
    status = daemon_status()
    if not status["running"]:
        typer.echo("Dispatcher not running. Start it with: outheis start")
        raise typer.Exit(1)

    # Load config and validate
    config = load_config()
    
    if not config.signal.enabled:
        typer.echo("Signal not enabled. Add to config.json:")
        typer.echo('  "signal": { "enabled": true, "bot_phone": "+49..." }')
        raise typer.Exit(1)
    
    if not config.signal.bot_phone:
        typer.echo("signal.bot_phone not configured")
        raise typer.Exit(1)
    
    if not config.user.phone:
        typer.echo("user.phone not configured (needed for authorization)")
        raise typer.Exit(1)

    # Start transport
    try:
        transport = SignalTransport(config)
        transport.run()
    except Exception as e:
        typer.echo(f"Error: {e}")
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
    # outheis breathing circle: ○ → ◎ → ◦ → · → ◦ → ◎
    start = time.time()
    spinner = ['○', '◎', '◦', '·', '◦', '◎']
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
    typer.echo(f"User: {config.user.name}")
    typer.echo(f"Language: {config.user.language}")
    typer.echo(f"Timezone: {config.user.timezone}")
    typer.echo(f"Primary vault: {config.user.primary_vault()}")
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
