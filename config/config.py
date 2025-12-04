"""
Centralized configuration management for PlayerGold
Handles environment variables, config files, and default settings
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class NetworkConfig(BaseSettings):
    """Network and P2P configuration"""
    p2p_port: int = Field(default=8333, description="P2P network port")
    api_port: int = Field(default=8080, description="API server port")
    max_peers: int = Field(default=50, description="Maximum number of peers")
    bootstrap_nodes: list = Field(default_factory=list, description="Bootstrap node addresses")
    network_id: str = Field(default="playergold-mainnet", description="Network identifier")


class AIConfig(BaseSettings):
    """AI nodes configuration"""
    models_dir: str = Field(default="./models", description="Directory for AI models")
    certified_models: Dict[str, str] = Field(
        default_factory=lambda: {
            "gemma-3-4b": "sha256:a1b2c3d4e5f6...",
            "mistral-3b": "sha256:f6e5d4c3b2a1...",
            "qwen-3-4b": "sha256:1a2b3c4d5e6f..."
        },
        description="Certified AI models with their SHA-256 hashes"
    )
    challenge_timeout: float = Field(default=0.1, description="Challenge timeout in seconds")
    min_validators: int = Field(default=3, description="Minimum validators for consensus")


class BlockchainConfig(BaseSettings):
    """Blockchain core configuration"""
    data_dir: str = Field(default="./data", description="Blockchain data directory")
    block_time: int = Field(default=10, description="Target block time in seconds")
    max_block_size: int = Field(default=1048576, description="Maximum block size in bytes")
    reward_distribution: Dict[str, float] = Field(
        default_factory=lambda: {"ai_nodes": 0.9, "stakers": 0.1},
        description="Reward distribution percentages"
    )
    fee_distribution: Dict[str, float] = Field(
        default_factory=lambda: {"liquidity": 0.2, "burn": 0.8},
        description="Fee distribution percentages"
    )


class WalletConfig(BaseSettings):
    """Wallet configuration"""
    wallet_dir: str = Field(default="./wallets", description="Wallet data directory")
    enable_2fa: bool = Field(default=True, description="Enable two-factor authentication")
    auto_backup: bool = Field(default=True, description="Enable automatic backups")
    backup_interval: int = Field(default=3600, description="Backup interval in seconds")


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_rotation: bool = Field(default=True, description="Enable log rotation")
    max_log_size: int = Field(default=10485760, description="Maximum log file size")


class PlayerGoldConfig(BaseSettings):
    """Main configuration class combining all settings"""
    
    # Environment
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Sub-configurations
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    blockchain: BlockchainConfig = Field(default_factory=BlockchainConfig)
    wallet: WalletConfig = Field(default_factory=WalletConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__"
    }


def load_config(config_file: Optional[str] = None) -> PlayerGoldConfig:
    """Load configuration from file and environment variables"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Start with default configuration
    config_data = {}
    
    # Load from YAML config file if provided
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config_data.update(file_config)
    
    # Create configuration instance (will also load from environment)
    config = PlayerGoldConfig(**config_data)
    
    # Create necessary directories
    Path(config.blockchain.data_dir).mkdir(parents=True, exist_ok=True)
    Path(config.wallet.wallet_dir).mkdir(parents=True, exist_ok=True)
    Path(config.ai.models_dir).mkdir(parents=True, exist_ok=True)
    
    return config


# Global configuration instance
_config: Optional[PlayerGoldConfig] = None


def get_config() -> PlayerGoldConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_file: Optional[str] = None) -> PlayerGoldConfig:
    """Reload configuration from file"""
    global _config
    _config = load_config(config_file)
    return _config