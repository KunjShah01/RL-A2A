"""Simple CLI for RL-A2A

Provides a few convenience commands for local development and starting the server.
"""
import asyncio
import click

from ..utils.logger import setup_logging

logger = setup_logging()


@click.group()
def cli():
    """RL-A2A command line interface"""
    pass


@cli.command()
@click.option("--host", default=None, help="Server host override")
@click.option("--port", default=None, type=int, help="Server port override")
def start(host, port):
    """Start the RL-A2A server (wrapper around main)"""
    # Import here to avoid heavy imports at module load
    try:
        from ... import main as _main_mod
    except Exception:
        click.echo("Unable to import main module. Run from project root.")
        raise

    # allow overriding via options by setting env or args — here we just call main
    click.echo("Starting RL-A2A server...")
    try:
        asyncio.run(_main_mod.main())
    except Exception as e:
        logger.error("Failed to start server: %s", e, exc_info=True)
        raise


@cli.command()
def version():
    """Print version info"""
    try:
        from ..utils.config import Config

        click.echo(f"{Config.SYSTEM_NAME} v{Config.VERSION}")
    except Exception:
        click.echo("rl-a2a (unknown version)")


if __name__ == "__main__":
    cli()
