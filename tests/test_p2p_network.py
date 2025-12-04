"""
Tests for P2P network functionality.
"""

import pytest
import pytest_asyncio
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock

from src.p2p.network import P2PNetwork, MessageType, P2PMessage, PeerInfo
from src.p2p.propagation import MessagePropagator, PropagationStrategy
from src.p2p.discovery import PeerDiscovery, DiscoveredPeer, DiscoveryMethod

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


class TestP2PNetwork:
    """Test P2P network functionality"""
    
    @pytest_asyncio.fixture
    async def network(self):
        """Create a test P2P network"""
        network = P2PNetwork("test_node_1", listen_port=8001)
        yield network
        if network.running:
            await network.stop()
    
    @pytest.mark.asyncio
    async def test_network_initialization(self, network):
        """Test network initialization"""
        assert network.node_id == "test_node_1"
        assert network.listen_port == 8001
        assert network.max_peers == 50
        assert not network.running
        assert len(network.peers) == 0
        assert len(network.connections) == 0
    
    @pytest.mark.asyncio
    async def test_tls_setup(self, network):
        """Test TLS configuration setup"""
        await network._setup_tls()
        
        assert network.ssl_context is not None
        assert network.certificate is not None
        assert network.private_key is not None
    
    @pytest.mark.asyncio
    async def test_message_handler_registration(self, network):
        """Test message handler registration"""
        handler = AsyncMock()
        
        network.register_message_handler(MessageType.TRANSACTION, handler)
        
        assert MessageType.TRANSACTION in network.message_handlers
        assert network.message_handlers[MessageType.TRANSACTION] == handler
    
    @pytest.mark.asyncio
    async def test_peer_info_creation(self):
        """Test peer info creation"""
        peer = PeerInfo(
            peer_id="test_peer",
            address="127.0.0.1",
            port=8002,
            public_key="test_key",
            reputation=1.0,
            is_ai_node=True,
            model_hash="test_hash"
        )
        
        assert peer.peer_id == "test_peer"
        assert peer.address == "127.0.0.1"
        assert peer.port == 8002
        assert peer.reputation == 1.0
        assert peer.is_ai_node
        assert peer.model_hash == "test_hash"
    
    @pytest.mark.asyncio
    async def test_p2p_message_creation(self):
        """Test P2P message creation"""
        message = P2PMessage(
            message_type=MessageType.TRANSACTION,
            sender_id="sender",
            recipient_id="recipient",
            payload={"data": "test"},
            timestamp=time.time(),
            signature="test_sig"
        )
        
        assert message.message_type == MessageType.TRANSACTION
        assert message.sender_id == "sender"
        assert message.recipient_id == "recipient"
        assert message.payload == {"data": "test"}
        assert message.signature == "test_sig"
    
    @pytest.mark.asyncio
    async def test_network_stats(self, network):
        """Test network statistics"""
        stats = network.get_network_stats()
        
        assert 'messages_sent' in stats
        assert 'messages_received' in stats
        assert 'bytes_sent' in stats
        assert 'bytes_received' in stats
        assert 'peer_count' in stats
        assert 'active_connections' in stats
        
        assert stats['peer_count'] == 0
        assert stats['active_connections'] == 0


class TestMessagePropagation:
    """Test message propagation functionality"""
    
    @pytest_asyncio.fixture
    async def network_and_propagator(self):
        """Create network and propagator for testing"""
        network = P2PNetwork("test_node", listen_port=8003)
        propagator = MessagePropagator(network)
        
        yield network, propagator
        
        await propagator.stop()
        if network.running:
            await network.stop()
    
    @pytest.mark.asyncio
    async def test_propagator_initialization(self, network_and_propagator):
        """Test propagator initialization"""
        network, propagator = network_and_propagator
        
        assert propagator.network == network
        assert propagator.config is not None
        assert len(propagator.seen_messages) == 0
        assert not propagator.running
    
    @pytest.mark.asyncio
    async def test_message_id_generation(self, network_and_propagator):
        """Test message ID generation"""
        network, propagator = network_and_propagator
        
        payload1 = {"data": "test1"}
        payload2 = {"data": "test2"}
        
        id1 = propagator._generate_message_id(MessageType.TRANSACTION, payload1)
        id2 = propagator._generate_message_id(MessageType.TRANSACTION, payload2)
        id3 = propagator._generate_message_id(MessageType.TRANSACTION, payload1)
        
        assert id1 != id2  # Different payloads should have different IDs
        assert id1 == id3  # Same payload should have same ID
        assert len(id1) == 16  # Should be 16 character hash
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, network_and_propagator):
        """Test duplicate message detection"""
        network, propagator = network_and_propagator
        
        message_id = "test_message_123"
        
        # Initially not a duplicate
        assert not propagator._is_duplicate(message_id)
        
        # Mark as seen
        propagator.seen_messages[message_id] = time.time()
        
        # Now should be detected as duplicate
        assert propagator._is_duplicate(message_id)
    
    @pytest.mark.asyncio
    async def test_propagation_stats(self, network_and_propagator):
        """Test propagation statistics"""
        network, propagator = network_and_propagator
        
        stats = propagator.get_propagation_stats()
        
        assert 'messages_propagated' in stats
        assert 'messages_deduplicated' in stats
        assert 'seen_messages_count' in stats
        assert 'pending_messages_count' in stats
        
        assert stats['messages_propagated'] == 0
        assert stats['messages_deduplicated'] == 0


class TestPeerDiscovery:
    """Test peer discovery functionality"""
    
    @pytest.fixture
    def discovery(self):
        """Create peer discovery instance"""
        return PeerDiscovery("test_node", 8004)
    
    def test_discovery_initialization(self, discovery):
        """Test discovery initialization"""
        assert discovery.node_id == "test_node"
        assert discovery.listen_port == 8004
        assert len(discovery.discovered_peers) == 0
        assert len(discovery.bootstrap_nodes) > 0  # Should have default bootstrap nodes
        assert not discovery.running
    
    @pytest.mark.asyncio
    async def test_manual_peer_addition(self, discovery):
        """Test manual peer addition"""
        discovery.add_manual_peer("127.0.0.1", 8005, "manual_peer")
        
        # Give it a moment to process
        await asyncio.sleep(0.1)
        
        assert len(discovery.discovered_peers) == 1
        peer = list(discovery.discovered_peers.values())[0]
        assert peer.node_id == "manual_peer"
        assert peer.address == "127.0.0.1"
        assert peer.port == 8005
        assert peer.discovery_method == "manual"
    
    def test_discovered_peer_creation(self):
        """Test discovered peer creation"""
        peer = DiscoveredPeer(
            node_id="test_peer",
            address="192.168.1.100",
            port=8006,
            discovery_method="mdns",
            capabilities=["ai_node", "validator"],
            timestamp=time.time()
        )
        
        assert peer.node_id == "test_peer"
        assert peer.address == "192.168.1.100"
        assert peer.port == 8006
        assert peer.discovery_method == "mdns"
        assert "ai_node" in peer.capabilities
        assert "validator" in peer.capabilities
        assert not peer.verified
    
    def test_discovery_stats(self, discovery):
        """Test discovery statistics"""
        stats = discovery.get_discovery_stats()
        
        assert 'peers_discovered' in stats
        assert 'bootstrap_attempts' in stats
        assert 'mdns_discoveries' in stats
        assert 'dht_discoveries' in stats
        assert 'total_discovered_peers' in stats
        assert 'ai_node_peers' in stats
        assert 'bootstrap_nodes' in stats
        
        assert stats['peers_discovered'] == 0
        assert stats['total_discovered_peers'] == 0
        assert stats['bootstrap_nodes'] > 0


class TestIntegration:
    """Integration tests for P2P components"""
    
    @pytest.mark.asyncio
    async def test_network_with_propagator(self):
        """Test network integration with propagator"""
        network = P2PNetwork("integration_test", listen_port=8007)
        propagator = MessagePropagator(network)
        
        try:
            # Setup TLS
            await network._setup_tls()
            
            # Start propagator
            await propagator.start()
            
            assert propagator.running
            
            # Test message propagation (without actual network)
            message_id = await propagator.propagate_transaction({
                "from": "addr1",
                "to": "addr2", 
                "amount": 100
            })
            
            assert message_id is not None
            assert len(message_id) == 16
            
        finally:
            await propagator.stop()
            if network.running:
                await network.stop()
    
    @pytest.mark.asyncio
    async def test_network_with_discovery(self):
        """Test network integration with discovery"""
        network = P2PNetwork("discovery_test", listen_port=8008)
        discovery = PeerDiscovery("discovery_test", 8008)
        
        try:
            # Add some manual peers
            discovery.add_manual_peer("127.0.0.1", 8009, "peer1")
            discovery.add_manual_peer("127.0.0.1", 8010, "peer2")
            
            # Give it time to process
            await asyncio.sleep(0.1)
            
            peers = discovery.get_discovered_peers()
            assert len(peers) == 2
            
            # Test getting AI node peers (none in this case)
            ai_peers = discovery.get_ai_node_peers()
            assert len(ai_peers) == 0
            
        finally:
            await discovery.stop()
            if network.running:
                await network.stop()


class TestErrorHandling:
    """Test error handling in P2P components"""
    
    @pytest.mark.asyncio
    async def test_network_start_failure(self):
        """Test network start failure handling"""
        # Try to start network on invalid port
        network = P2PNetwork("error_test", listen_port=-1)
        
        with pytest.raises(Exception):
            await network.start()
    
    @pytest.mark.asyncio
    async def test_propagator_with_invalid_network(self):
        """Test propagator with invalid network"""
        network = Mock()
        network.node_id = "mock_node"
        network.connections = {}
        network.peers = {}
        
        propagator = MessagePropagator(network)
        
        # Should handle gracefully
        message_id = await propagator.propagate_transaction({"test": "data"})
        assert message_id is not None
    
    def test_discovery_with_invalid_bootstrap(self):
        """Test discovery with invalid bootstrap nodes"""
        discovery = PeerDiscovery("error_test", 8011)
        
        # Clear bootstrap nodes and add invalid one
        from src.p2p.discovery import BootstrapNode
        discovery.bootstrap_nodes.clear()
        discovery.bootstrap_nodes.append(
            BootstrapNode("invalid.host", 9999, "invalid", "")
        )
        
        # Should not crash
        stats = discovery.get_discovery_stats()
        assert stats['bootstrap_nodes'] == 1


if __name__ == "__main__":
    pytest.main([__file__])