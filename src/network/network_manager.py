"""
Network Manager for PlayerGold
Manages testnet and mainnet configurations and switching
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class NetworkType(Enum):
    """Types of networks supported"""
    TESTNET = "testnet"
    MAINNET = "mainnet"


@dataclass
class NetworkConfig:
    """Configuration for a specific network"""
    network_type: NetworkType
    network_id: str
    p2p_port: int
    api_port: int
    bootstrap_nodes: List[str]
    min_nodes: int = 2
    quorum_percentage: float = 0.66


class NetworkManager:
    """
    Manages network configuration and switching between testnet and mainnet.
    
    Ensures proper network isolation and configuration management.
    """
    
    def __init__(self, config_path: str = "config/default.yaml"):
        self.config_path = config_path
        self.current_network: Optional[NetworkType] = None
        self.network_configs: dict[NetworkType, NetworkConfig] = {}
        
        self._load_network_configs()
        logger.info("Network Manager initialized")
    
    def _load_network_configs(self):
        """Load network configurations from config file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self._load_default_configs()
                return
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            network_config = config.get('network', {})
            
            # Load testnet config
            testnet_config = network_config.get('testnet', {})
            self.network_configs[NetworkType.TESTNET] = NetworkConfig(
                network_type=NetworkType.TESTNET,
                network_id=testnet_config.get('network_id', 'playergold-testnet'),
                p2p_port=testnet_config.get('p2p_port', 18333),
                api_port=testnet_config.get('api_port', 18080),
                bootstrap_nodes=testnet_config.get('bootstrap_nodes', ['testnet.playergold.es:18333']),
                min_nodes=network_config.get('min_nodes_for_consensus', 2),
                quorum_percentage=network_config.get('quorum_percentage', 0.66)
            )
            
            # Load mainnet config
            mainnet_config = network_config.get('mainnet', {})
            self.network_configs[NetworkType.MAINNET] = NetworkConfig(
                network_type=NetworkType.MAINNET,
                network_id=mainnet_config.get('network_id', 'playergold-mainnet'),
                p2p_port=mainnet_config.get('p2p_port', 8333),
                api_port=mainnet_config.get('api_port', 8080),
                bootstrap_nodes=mainnet_config.get('bootstrap_nodes', [
                    'seed1.playergold.es:8333',
                    'seed2.playergold.es:8333'
                ]),
                min_nodes=network_config.get('min_nodes_for_consensus', 2),
                quorum_percentage=network_config.get('quorum_percentage', 0.66)
            )
            
            # Set current network from config
            network_type_str = network_config.get('network_type', 'testnet')
            self.current_network = NetworkType(network_type_str)
            
            logger.info(f"Loaded network configs: testnet and mainnet")
            logger.info(f"Current network: {self.current_network.value}")
            
        except Exception as e:
            logger.error(f"Error loading network configs: {e}")
            self._load_default_configs()
    
    def _load_default_configs(self):
        """Load default network configurations"""
        self.network_configs[NetworkType.TESTNET] = NetworkConfig(
            network_type=NetworkType.TESTNET,
            network_id="playergold-testnet",
            p2p_port=18333,
            api_port=18080,
            bootstrap_nodes=['testnet.playergold.es:18333'],
            min_nodes=2,
            quorum_percentage=0.66
        )
        
        self.network_configs[NetworkType.MAINNET] = NetworkConfig(
            network_type=NetworkType.MAINNET,
            network_id="playergold-mainnet",
            p2p_port=8333,
            api_port=8080,
            bootstrap_nodes=[
                'seed1.playergold.es:8333',
                'seed2.playergold.es:8333'
            ],
            min_nodes=2,
            quorum_percentage=0.66
        )
        
        self.current_network = NetworkType.TESTNET
        logger.info("Loaded default network configurations")
    
    def get_current_network(self) -> NetworkType:
        """Get the currently active network"""
        return self.current_network
    
    def get_network_config(self, network_type: Optional[NetworkType] = None) -> NetworkConfig:
        """
        Get configuration for a specific network.
        
        Args:
            network_type: Network to get config for. If None, returns current network.
            
        Returns:
            NetworkConfig for the specified network
        """
        if network_type is None:
            network_type = self.current_network
        
        return self.network_configs[network_type]
    
    def switch_network(self, network_type: NetworkType) -> bool:
        """
        Switch to a different network.
        
        Args:
            network_type: Network to switch to
            
        Returns:
            bool: True if switch was successful
        """
        if network_type not in self.network_configs:
            logger.error(f"Network type {network_type} not configured")
            return False
        
        old_network = self.current_network
        self.current_network = network_type
        
        logger.info(f"Switched network from {old_network.value} to {network_type.value}")
        logger.warning("⚠️ Network switch requires node restart to take effect!")
        
        return True
    
    def is_testnet(self) -> bool:
        """Check if currently on testnet"""
        return self.current_network == NetworkType.TESTNET
    
    def is_mainnet(self) -> bool:
        """Check if currently on mainnet"""
        return self.current_network == NetworkType.MAINNET
    
    def get_network_info(self) -> dict:
        """Get information about current network"""
        config = self.get_network_config()
        
        return {
            'network_type': self.current_network.value,
            'network_id': config.network_id,
            'p2p_port': config.p2p_port,
            'api_port': config.api_port,
            'bootstrap_nodes': config.bootstrap_nodes,
            'min_nodes': config.min_nodes,
            'quorum_percentage': config.quorum_percentage,
            'is_testnet': self.is_testnet(),
            'is_mainnet': self.is_mainnet()
        }
    
    def validate_network_compatibility(self, peer_network_id: str) -> bool:
        """
        Validate that a peer is on the same network.
        
        Args:
            peer_network_id: Network ID from peer
            
        Returns:
            bool: True if peer is on same network
        """
        current_config = self.get_network_config()
        
        if peer_network_id != current_config.network_id:
            logger.warning(
                f"Network mismatch: local={current_config.network_id}, "
                f"peer={peer_network_id}"
            )
            return False
        
        return True
    
    def get_data_directory(self) -> str:
        """Get data directory for current network"""
        if self.is_testnet():
            return "./data/testnet"
        else:
            return "./data/mainnet"
    
    def get_bootstrap_nodes(self) -> List[str]:
        """Get bootstrap nodes for current network"""
        config = self.get_network_config()
        return config.bootstrap_nodes.copy()
