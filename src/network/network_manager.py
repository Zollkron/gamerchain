#!/usr/bin/env python3
"""
Network Manager for PlayerGold

Manages network configurations for testnet and mainnet:
- Network-specific settings
- Bootstrap node configurations
- Network compatibility validation
- Network-aware IP validation (testnet allows private, mainnet public-only)
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import ipaddress

logger = logging.getLogger(__name__)


class NetworkType(Enum):
    """Network types supported by PlayerGold"""
    TESTNET = "testnet"
    MAINNET = "mainnet"


@dataclass
class NetworkConfig:
    """Configuration for a specific network"""
    network_id: str
    network_type: NetworkType
    p2p_port: int
    api_port: int
    bootstrap_nodes: List[str]
    genesis_pioneers_required: int = 2
    consensus_threshold: float = 0.66  # 66%
    block_interval: int = 10  # seconds
    initial_block_reward: int = 1024  # PRGLD
    halving_interval: int = 100000  # blocks
    faucet_enabled: bool = True
    reset_allowed: bool = False  # Only testnet allows reset


class NetworkManager:
    """
    Manages network configurations and provides network-specific functionality
    """
    
    def __init__(self):
        self.current_network = NetworkType.TESTNET
        self.networks = self._initialize_networks()
        
        # IP validation for network-aware filtering (testnet allows private, mainnet public-only)
        self.private_ipv4_ranges = [
            ipaddress.IPv4Network('10.0.0.0/8'),
            ipaddress.IPv4Network('172.16.0.0/12'),
            ipaddress.IPv4Network('192.168.0.0/16'),
            ipaddress.IPv4Network('127.0.0.0/8'),  # Loopback
            ipaddress.IPv4Network('169.254.0.0/16'),  # Link-local
        ]
        
        self.private_ipv6_ranges = [
            ipaddress.IPv6Network('fc00::/7'),  # Unique local
            ipaddress.IPv6Network('fe80::/10'),  # Link-local
            ipaddress.IPv6Network('::1/128'),   # Loopback
        ]
        
        logger.info(f"Network Manager initialized - Current network: {self.current_network.value}")
    
    def _initialize_networks(self) -> dict:
        """Initialize network configurations"""
        return {
            NetworkType.TESTNET: NetworkConfig(
                network_id="playergold-testnet-v1",
                network_type=NetworkType.TESTNET,
                p2p_port=18080,
                api_port=19080,
                bootstrap_nodes=[
                    # Add testnet bootstrap nodes here
                    # "testnet-node1.playergold.com:18080",
                    # "testnet-node2.playergold.com:18080",
                ],
                faucet_enabled=True,
                reset_allowed=True  # Testnet allows blockchain reset
            ),
            
            NetworkType.MAINNET: NetworkConfig(
                network_id="playergold-mainnet-v1",
                network_type=NetworkType.MAINNET,
                p2p_port=18081,
                api_port=19081,
                bootstrap_nodes=[
                    # Add mainnet bootstrap nodes here
                    # "mainnet-node1.playergold.com:18081",
                    # "mainnet-node2.playergold.com:18081",
                ],
                faucet_enabled=False,
                reset_allowed=False  # Mainnet never allows reset
            )
        }
    
    def set_current_network(self, network_type: NetworkType):
        """Set the current active network"""
        self.current_network = network_type
        logger.info(f"Switched to network: {network_type.value}")
    
    def get_current_network(self) -> NetworkType:
        """Get the current active network type"""
        return self.current_network
    
    def is_testnet(self) -> bool:
        """Check if current network is testnet"""
        return self.current_network == NetworkType.TESTNET
    
    def is_mainnet(self) -> bool:
        """Check if current network is mainnet"""
        return self.current_network == NetworkType.MAINNET
    
    def get_network_config(self, network_type: Optional[NetworkType] = None) -> NetworkConfig:
        """Get configuration for a specific network (or current network)"""
        network = network_type or self.current_network
        return self.networks[network]
    
    def validate_network_compatibility(self, peer_network_id: str) -> bool:
        """Validate if a peer's network is compatible with ours"""
        current_config = self.get_network_config()
        
        # Exact network ID match required
        compatible = peer_network_id == current_config.network_id
        
        if not compatible:
            logger.warning(
                f"Network incompatibility: peer={peer_network_id}, "
                f"local={current_config.network_id}"
            )
        
        return compatible
    
    def is_public_ip(self, ip_address: str) -> bool:
        """Check if an IP address is public (not private/local)"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check IPv4 private ranges
            if isinstance(ip, ipaddress.IPv4Address):
                for private_range in self.private_ipv4_ranges:
                    if ip in private_range:
                        return False
                return True
            
            # Check IPv6 private ranges
            elif isinstance(ip, ipaddress.IPv6Address):
                for private_range in self.private_ipv6_ranges:
                    if ip in private_range:
                        return False
                return True
            
            return False
            
        except ValueError:
            logger.error(f"Invalid IP address: {ip_address}")
            return False
    
    def validate_peer_ip(self, ip_address: str) -> dict:
        """Validate a peer's IP address for network connection"""
        result = {
            'is_valid': False,
            'is_public': False,
            'rejection_reason': None,
            'ip_info': {
                'address': ip_address,
                'type': None,
                'is_private': False,
                'is_loopback': False,
                'is_link_local': False
            }
        }
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Determine IP type
            if isinstance(ip, ipaddress.IPv4Address):
                result['ip_info']['type'] = 'IPv4'
            elif isinstance(ip, ipaddress.IPv6Address):
                result['ip_info']['type'] = 'IPv6'
            
            # Check IP properties
            result['ip_info']['is_private'] = ip.is_private
            result['ip_info']['is_loopback'] = ip.is_loopback
            result['ip_info']['is_link_local'] = ip.is_link_local
            
            # TESTNET EXCEPTION: Allow local IPs for testing
            if self.current_network == NetworkType.TESTNET:
                # In testnet, allow localhost and private IPs for local testing
                if ip.is_loopback or ip_address in ['127.0.0.1', '::1', 'localhost']:
                    result['is_valid'] = True
                    result['is_public'] = False  # Still mark as not public
                    logger.debug(f"Valid testnet local IP: {ip_address}")
                    return result
                elif ip.is_private:
                    # Allow private IPs in testnet for local network testing
                    result['is_valid'] = True
                    result['is_public'] = False
                    logger.debug(f"Valid testnet private IP: {ip_address}")
                    return result
            
            # Validate for public network (mainnet or strict mode)
            if ip.is_private:
                result['rejection_reason'] = f"Private IP address not allowed in {self.current_network.value}: {ip_address}"
            elif ip.is_loopback:
                result['rejection_reason'] = f"Loopback IP address not allowed in {self.current_network.value}: {ip_address}"
            elif ip.is_link_local:
                result['rejection_reason'] = f"Link-local IP address not allowed in {self.current_network.value}: {ip_address}"
            else:
                # IP is public
                result['is_valid'] = True
                result['is_public'] = True
                logger.debug(f"Valid public IP: {ip_address}")
            
        except ValueError:
            result['rejection_reason'] = f"Invalid IP address format: {ip_address}"
        
        return result
    
    def get_bootstrap_nodes(self, network_type: Optional[NetworkType] = None) -> List[str]:
        """Get bootstrap nodes for a specific network"""
        config = self.get_network_config(network_type)
        return config.bootstrap_nodes.copy()
    
    def add_bootstrap_node(self, node_address: str, network_type: Optional[NetworkType] = None):
        """Add a bootstrap node to a network"""
        config = self.get_network_config(network_type)
        
        if node_address not in config.bootstrap_nodes:
            config.bootstrap_nodes.append(node_address)
            logger.info(f"Added bootstrap node to {config.network_type.value}: {node_address}")
        else:
            logger.warning(f"Bootstrap node already exists: {node_address}")
    
    def remove_bootstrap_node(self, node_address: str, network_type: Optional[NetworkType] = None):
        """Remove a bootstrap node from a network"""
        config = self.get_network_config(network_type)
        
        if node_address in config.bootstrap_nodes:
            config.bootstrap_nodes.remove(node_address)
            logger.info(f"Removed bootstrap node from {config.network_type.value}: {node_address}")
        else:
            logger.warning(f"Bootstrap node not found: {node_address}")
    
    def can_reset_blockchain(self, network_type: Optional[NetworkType] = None) -> bool:
        """Check if blockchain reset is allowed for a network"""
        config = self.get_network_config(network_type)
        return config.reset_allowed
    
    def is_faucet_enabled(self, network_type: Optional[NetworkType] = None) -> bool:
        """Check if faucet is enabled for a network"""
        config = self.get_network_config(network_type)
        return config.faucet_enabled
    
    def get_network_info(self, network_type: Optional[NetworkType] = None) -> dict:
        """Get comprehensive network information"""
        config = self.get_network_config(network_type)
        
        return {
            'network_id': config.network_id,
            'network_type': config.network_type.value,
            'p2p_port': config.p2p_port,
            'api_port': config.api_port,
            'bootstrap_nodes': config.bootstrap_nodes,
            'genesis_pioneers_required': config.genesis_pioneers_required,
            'consensus_threshold': config.consensus_threshold,
            'block_interval': config.block_interval,
            'initial_block_reward': config.initial_block_reward,
            'halving_interval': config.halving_interval,
            'faucet_enabled': config.faucet_enabled,
            'reset_allowed': config.reset_allowed,
            'is_current': config.network_type == self.current_network
        }
    
    def get_all_networks_info(self) -> dict:
        """Get information about all configured networks"""
        return {
            network_type.value: self.get_network_info(network_type)
            for network_type in NetworkType
        }