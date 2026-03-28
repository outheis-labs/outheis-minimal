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
) -> None:
    """Start the outheis dispatcher daemon."""
    from outheis.core.config import init_directories
    from outheis.dispatcher.daemon import start_daemon

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
    from outheis.dispatcher.daemon import daemon_status
    from outheis.transport.cli import CLITransport

    # Check if daemon is running
    status = daemon_status()
    if not status["running"]:
        typer.echo("Dispatcher not running. Start it with: outheis start")
        raise typer.Exit(1)

    typer.echo("outheis CLI (type 'exit' to quit)")
    typer.echo("-" * 40)

    transport = CLITransport()

    while True:
        try:
            text = typer.prompt("\n>", default="", show_default=False)

            if not text.strip():
                continue

            if text.strip().lower() in ("exit", "quit", "q"):
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
        typer.echo("[dry-run] Would process session notes")
        typer.echo("[dry-run] Would extract insights")
        typer.echo("[dry-run] Would update tag weights")
        return

    agent.run_scheduled()

    typer.echo("Done.")


if __name__ == "__main__":
    app()
