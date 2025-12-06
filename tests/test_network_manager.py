"""
Tests for Network Manager
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.network.network_manager import (
    NetworkManager,
    NetworkType,
    NetworkConfig
)


class TestNetworkManager:
    """Tests for NetworkManager"""
    
    def test_initialization_with_defaults(self):
        """Test initialization with default configs"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        assert manager.current_network == NetworkType.TESTNET
        assert NetworkType.TESTNET in manager.network_configs
        assert NetworkType.MAINNET in manager.network_configs
    
    def test_get_current_network(self):
        """Test getting current network"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        assert manager.get_current_network() == NetworkType.TESTNET
    
    def test_get_network_config_testnet(self):
        """Test getting testnet configuration"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        config = manager.get_network_config(NetworkType.TESTNET)
        
        assert config.network_type == NetworkType.TESTNET
        assert config.network_id == "playergold-testnet"
        assert config.p2p_port == 18333
        assert config.api_port == 18080
        assert config.min_nodes == 2
        assert config.quorum_percentage == 0.66
    
    def test_get_network_config_mainnet(self):
        """Test getting mainnet configuration"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        config = manager.get_network_config(NetworkType.MAINNET)
        
        assert config.network_type == NetworkType.MAINNET
        assert config.network_id == "playergold-mainnet"
        assert config.p2p_port == 8333
        assert config.api_port == 8080
        assert config.min_nodes == 2
        assert config.quorum_percentage == 0.66
    
    def test_switch_network(self):
        """Test switching between networks"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        assert manager.current_network == NetworkType.TESTNET
        
        # Switch to mainnet
        result = manager.switch_network(NetworkType.MAINNET)
        
        assert result
        assert manager.current_network == NetworkType.MAINNET
        
        # Switch back to testnet
        result = manager.switch_network(NetworkType.TESTNET)
        
        assert result
        assert manager.current_network == NetworkType.TESTNET
    
    def test_is_testnet(self):
        """Test testnet check"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        assert manager.is_testnet()
        assert not manager.is_mainnet()
    
    def test_is_mainnet(self):
        """Test mainnet check"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        manager.switch_network(NetworkType.MAINNET)
        
        assert manager.is_mainnet()
        assert not manager.is_testnet()
    
    def test_get_network_info(self):
        """Test getting network information"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        info = manager.get_network_info()
        
        assert info['network_type'] == 'testnet'
        assert info['network_id'] == 'playergold-testnet'
        assert info['p2p_port'] == 18333
        assert info['api_port'] == 18080
        assert info['min_nodes'] == 2
        assert info['quorum_percentage'] == 0.66
        assert info['is_testnet']
        assert not info['is_mainnet']
    
    def test_validate_network_compatibility_same_network(self):
        """Test network compatibility validation with same network"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        assert manager.validate_network_compatibility("playergold-testnet")
    
    def test_validate_network_compatibility_different_network(self):
        """Test network compatibility validation with different network"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        assert not manager.validate_network_compatibility("playergold-mainnet")
    
    def test_get_data_directory_testnet(self):
        """Test getting data directory for testnet"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        assert manager.get_data_directory() == "./data/testnet"
    
    def test_get_data_directory_mainnet(self):
        """Test getting data directory for mainnet"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        manager.switch_network(NetworkType.MAINNET)
        
        assert manager.get_data_directory() == "./data/mainnet"
    
    def test_get_bootstrap_nodes(self):
        """Test getting bootstrap nodes"""
        manager = NetworkManager(config_path="nonexistent.yaml")
        
        nodes = manager.get_bootstrap_nodes()
        
        assert isinstance(nodes, list)
        assert len(nodes) > 0
        assert 'testnet.playergold.es:18333' in nodes
    
    def test_load_from_config_file(self):
        """Test loading configuration from file"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'network': {
                    'network_type': 'mainnet',
                    'min_nodes_for_consensus': 3,
                    'quorum_percentage': 0.75,
                    'testnet': {
                        'network_id': 'test-custom',
                        'p2p_port': 19000,
                        'api_port': 19001,
                        'bootstrap_nodes': ['custom-test.example.com:19000']
                    },
                    'mainnet': {
                        'network_id': 'main-custom',
                        'p2p_port': 9000,
                        'api_port': 9001,
                        'bootstrap_nodes': ['custom-main.example.com:9000']
                    }
                }
            }
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            manager = NetworkManager(config_path=config_path)
            
            # Should load mainnet as current
            assert manager.current_network == NetworkType.MAINNET
            
            # Check custom testnet config
            testnet_config = manager.get_network_config(NetworkType.TESTNET)
            assert testnet_config.network_id == 'test-custom'
            assert testnet_config.p2p_port == 19000
            assert testnet_config.min_nodes == 3
            assert testnet_config.quorum_percentage == 0.75
            
            # Check custom mainnet config
            mainnet_config = manager.get_network_config(NetworkType.MAINNET)
            assert mainnet_config.network_id == 'main-custom'
            assert mainnet_config.p2p_port == 9000
            
        finally:
            # Clean up temp file
            Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
