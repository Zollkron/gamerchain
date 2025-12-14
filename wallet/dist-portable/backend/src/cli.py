"""
PlayerGold Command Line Interface
Provides CLI commands for managing the PlayerGold application
"""

import click
import asyncio
from pathlib import Path

from config.config import get_config, reload_config
from src.utils.logging import setup_logging, get_logger
from src.main import PlayerGoldApp


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, config, debug):
    """PlayerGold - Distributed AI Nodes Architecture for Gaming Blockchain"""
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config
    ctx.obj['debug'] = debug


@cli.command()
@click.pass_context
def run(ctx):
    """Run the PlayerGold application"""
    config_file = ctx.obj.get('config_file')
    debug = ctx.obj.get('debug')
    
    if config_file:
        reload_config(config_file)
    
    config = get_config()
    if debug:
        config.debug = True
        config.logging.log_level = "DEBUG"
    
    # Setup logging
    setup_logging(
        log_level=config.logging.log_level,
        log_file=config.logging.log_file
    )
    
    logger = get_logger("cli")
    logger.info("Starting PlayerGold from CLI")
    
    app = PlayerGoldApp()
    asyncio.run(app.start())


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize a new PlayerGold project"""
    click.echo("Initializing PlayerGold project...")
    
    # Create necessary directories
    directories = [
        "data",
        "logs", 
        "models",
        "wallets"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        click.echo(f"Created directory: {directory}")
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        Path(".env").write_text(Path(".env.example").read_text())
        click.echo("Created .env file from template")
    
    click.echo("PlayerGold project initialized successfully!")
    click.echo("Run 'playergold run' to start the application")


@cli.command()
def config():
    """Show current configuration"""
    config = get_config()
    
    click.echo("PlayerGold Configuration:")
    click.echo(f"  Environment: {config.environment}")
    click.echo(f"  Debug: {config.debug}")
    click.echo(f"  P2P Port: {config.network.p2p_port}")
    click.echo(f"  API Port: {config.network.api_port}")
    click.echo(f"  Data Directory: {config.blockchain.data_dir}")
    click.echo(f"  Models Directory: {config.ai.models_dir}")
    click.echo(f"  Log Level: {config.logging.log_level}")


@cli.command()
def version():
    """Show PlayerGold version"""
    click.echo("PlayerGold v0.1.0")
    click.echo("Distributed AI Nodes Architecture for Gaming Blockchain")


@cli.command()
def status():
    """Show system status"""
    config = get_config()
    
    click.echo("PlayerGold System Status:")
    
    # Check directories
    directories = [
        config.blockchain.data_dir,
        config.ai.models_dir,
        config.wallet.wallet_dir
    ]
    
    for directory in directories:
        exists = Path(directory).exists()
        status = "✓" if exists else "✗"
        click.echo(f"  {status} Directory {directory}: {'exists' if exists else 'missing'}")
    
    # Check configuration
    click.echo(f"  ✓ Configuration loaded: {config.environment}")
    
    # TODO: Add more status checks in later tasks
    # - AI models status
    # - Network connectivity
    # - Blockchain sync status


if __name__ == '__main__':
    cli()