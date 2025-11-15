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
    from outheis.core.config import init_directories, get_config_path
    
    init_directories()
    typer.echo(f"Initialized outheis at ~/.outheis")
    typer.echo(f"Config: {get_config_path()}")


@app.command()
def send(
    message: str = typer.Argument(..., help="Message to send"),
) -> None:
    """Send a message and wait for response."""
    from outheis.core.config import init_directories
    from outheis.transport.cli import CLITransport
    from outheis.agents.relay import create_relay_agent
    from outheis.core.queue import read_last_n
    from outheis.core.config import get_messages_path
    
    init_directories()
    
    transport = CLITransport()
    msg = transport.send(message)
    
    typer.echo(f"Sent: {msg.id[:8]}...")
    
    # For MVP: handle directly with relay agent
    relay = create_relay_agent()
    response = relay.handle(msg)
    
    if response:
        typer.echo(f"\n{response.payload.get('text', '')}")
    else:
        typer.echo("[no response]")


@app.command()
def chat() -> None:
    """Start interactive chat session."""
    from outheis.core.config import init_directories
    from outheis.transport.cli import CLITransport
    from outheis.agents.relay import create_relay_agent
    
    init_directories()
    
    typer.echo("outheis CLI (type 'exit' to quit)")
    typer.echo("-" * 40)
    
    transport = CLITransport()
    relay = create_relay_agent()
    
    while True:
        try:
            text = typer.prompt("\n>", default="", show_default=False)
            
            if not text.strip():
                continue
            
            if text.strip().lower() in ("exit", "quit", "q"):
                break
            
            msg = transport.send(text)
            response = relay.handle(msg)
            
            if response:
                typer.echo(f"\n{response.payload.get('text', '')}")
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
        load_config,
        get_messages_path,
        get_human_dir,
    )
    from outheis.core.queue import message_count, queue_size
    
    config = load_config()
    queue_path = get_messages_path()
    
    typer.echo("outheis status")
    typer.echo("-" * 40)
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
    from outheis.core.config import get_messages_path, get_insights_path
    from outheis.core.schema import (
        scan_file,
        MESSAGES_VERSION,
        INSIGHTS_VERSION,
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


if __name__ == "__main__":
    app()
