"""
Tests for P2P blockchain synchronization functionality.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from src.p2p.network import P2PNetwork, MessageType, P2PMessage
from src.p2p.synchronization import (
    BlockchainSynchronizer, SyncState, BlockHeader, PeerSyncInfo,
    SyncRequest, SyncResponse
)

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


class MockBlockchainManager:
    """Mock blockchain manager for testing"""
    
    def __init__(self):
        self.blocks = []
        self.latest_index = 0
        self.latest_hash = "genesis_hash"
        self.node_reputation = 1.0
    
    async def get_latest_block_index(self):
        return self.latest_index
    
    async def get_latest_block_hash(self):
        return self.latest_hash
    
    async def get_blocks_range(self, start_index, end_index):
        return [
            {
                'index': i,
                'hash': f'block_hash_{i}',
                'previous_hash': f'block_hash_{i-1}' if i > 0 else 'genesis_hash',
                'timestamp': time.time(),
                'merkle_root': f'merkle_{i}',
                'ai_validators': ['validator1', 'validator2']
            }
            for i in range(start_index, min(end_index + 1, len(self.blocks)))
        ]
    
    async def get_block_by_index(self, index):
        if 0 <= index < len(self.blocks):
            return self.blocks[index]
        return None
    
    async def add_block(self, block):
        self.blocks.append(block)
        self.latest_index = block['index']
        self.latest_hash = block['hash']
    
    async def replace_block(self, block):
        index = block['index']
        if 0 <= index < len(self.blocks):
            self.blocks[index] = block
    
    async def get_node_reputation(self, node_id):
        return self.node_reputation


class TestBlockchainSynchronizer:
    """Test blockchain synchronization functionality"""
    
    @pytest_asyncio.fixture
    async def sync_setup(self):
        """Create synchronizer setup for testing"""
        network = P2PNetwork("sync_test_node", listen_port=8020)
        blockchain = MockBlockchainManager()
        synchronizer = BlockchainSynchronizer(network, blockchain)
        
        yield network, blockchain, synchronizer
        
        await synchronizer.stop()
        if network.running:
            await network.stop()
    
    @pytest.mark.asyncio
    async def test_synchronizer_initialization(self, sync_setup):
        """Test synchronizer initialization"""
        network, blockchain, synchronizer = sync_setup
        
        assert synchronizer.network == network
        assert synchronizer.blockchain == blockchain
        assert synchronizer.sync_state == SyncState.SYNCED
        assert len(synchronizer.peer_sync_info) == 0
        assert not synchronizer.running
    
    @pytest.mark.asyncio
    async def test_peer_sync_info_creation(self):
        """Test peer sync info creation"""
        peer_info = PeerSyncInfo(
            peer_id="test_peer",
            latest_block_index=100,
            latest_block_hash="test_hash",
            reputation=0.8,
            last_sync=time.time(),
            sync_speed=10.0
        )
        
        assert peer_info.peer_id == "test_peer"
        assert peer_info.latest_block_index == 100
        assert peer_info.latest_block_hash == "test_hash"
        assert peer_info.reputation == 0.8
        assert peer_info.sync_speed == 10.0
        assert peer_info.is_reliable
    
    @pytest.mark.asyncio
    async def test_block_header_creation(self, sync_setup):
        """Test block header creation"""
        network, blockchain, synchronizer = sync_setup
        
        block_data = {
            'index': 5,
            'hash': 'test_hash',
            'previous_hash': 'prev_hash',
            'timestamp': time.time(),
            'merkle_root': 'merkle_root',
            'ai_validators': ['val1', 'val2', 'val3']
        }
        
        header = synchronizer._create_block_header(block_data)
        
        assert header.index == 5
        assert header.hash == 'test_hash'
        assert header.previous_hash == 'prev_hash'
        assert header.validator_count == 3
    
    @pytest.mark.asyncio
    async def test_sync_request_creation(self):
        """Test sync request creation"""
        request = SyncRequest(
            request_id="req_123",
            start_index=10,
            end_index=20,
            requester_id="requester",
            timestamp=time.time()
        )
        
        assert request.request_id == "req_123"
        assert request.start_index == 10
        assert request.end_index == 20
        assert request.requester_id == "requester"
    
    @pytest.mark.asyncio
    async def test_sync_response_creation(self):
        """Test sync response creation"""
        blocks = [{'index': 1, 'hash': 'hash1'}]
        headers = [BlockHeader(1, 'hash1', 'prev', time.time(), 'merkle', 2, 0.8)]
        
        response = SyncResponse(
            request_id="req_123",
            blocks=blocks,
            headers=headers,
            responder_id="responder",
            timestamp=time.time()
        )
        
        assert response.request_id == "req_123"
        assert len(response.blocks) == 1
        assert len(response.headers) == 1
        assert response.responder_id == "responder"
    
    @pytest.mark.asyncio
    async def test_peer_selection_for_sync(self, sync_setup):
        """Test peer selection for synchronization"""
        network, blockchain, synchronizer = sync_setup
        
        # Add some peer sync info
        synchronizer.peer_sync_info = {
            'peer1': PeerSyncInfo('peer1', 100, 'hash1', 0.9, time.time(), 5.0),
            'peer2': PeerSyncInfo('peer2', 95, 'hash2', 0.7, time.time(), 3.0),
            'peer3': PeerSyncInfo('peer3', 105, 'hash3', 0.3, time.time(), 8.0),  # Low reputation
        }
        
        selected_peers = synchronizer._select_sync_peers()
        
        # Should select peers with good reputation, sorted by reputation and block index
        assert len(selected_peers) == 2  # peer3 excluded due to low reputation
        assert selected_peers[0].peer_id == 'peer1'  # Highest reputation
        assert selected_peers[1].peer_id == 'peer2'
    
    @pytest.mark.asyncio
    async def test_block_validation(self, sync_setup):
        """Test block validation during sync"""
        network, blockchain, synchronizer = sync_setup
        
        # Valid block
        valid_block = {
            'index': 1,
            'hash': 'valid_hash',
            'previous_hash': 'genesis_hash',
            'timestamp': time.time()
        }
        
        header = BlockHeader(1, 'valid_hash', 'genesis_hash', time.time(), 'merkle', 2, 0.8)
        
        is_valid = await synchronizer._validate_synced_block(valid_block, header)
        assert is_valid
        
        # Invalid block (missing fields)
        invalid_block = {
            'index': 1,
            'hash': 'invalid_hash'
            # Missing required fields
        }
        
        is_valid = await synchronizer._validate_synced_block(invalid_block, None)
        assert not is_valid
    
    @pytest.mark.asyncio
    async def test_sync_status_update(self, sync_setup):
        """Test sync status updates"""
        network, blockchain, synchronizer = sync_setup
        
        # Initially synced
        assert synchronizer.sync_state == SyncState.SYNCED
        
        # Add peer with higher block index
        synchronizer.peer_sync_info['peer1'] = PeerSyncInfo(
            'peer1', 100, 'hash1', 0.8, time.time(), 5.0
        )
        
        # Mock blockchain to return lower index
        blockchain.latest_index = 50
        
        # Mock the network send method to avoid actual network calls
        network.send_message_to_peer = AsyncMock(return_value=False)
        
        await synchronizer._check_sync_status()
        
        # Should detect we're behind and start syncing
        assert synchronizer.sync_state in [SyncState.BEHIND, SyncState.SYNCING]
    
    @pytest.mark.asyncio
    async def test_conflict_resolution(self, sync_setup):
        """Test block conflict resolution"""
        network, blockchain, synchronizer = sync_setup
        
        # Add existing block
        existing_block = {
            'index': 5,
            'hash': 'existing_hash',
            'timestamp': time.time() - 100  # Older
        }
        blockchain.blocks = [existing_block]
        
        # New conflicting block from high-reputation peer
        new_block = {
            'index': 5,
            'hash': 'new_hash',
            'timestamp': time.time()  # Newer
        }
        
        # Add high-reputation peer
        synchronizer.peer_sync_info['peer1'] = PeerSyncInfo(
            'peer1', 10, 'hash1', 0.9, time.time(), 5.0
        )
        
        await synchronizer._handle_block_conflict(existing_block, new_block, 'peer1')
        
        # Should have resolved conflict (replaced block)
        assert synchronizer.stats['conflicts_resolved'] == 1
    
    @pytest.mark.asyncio
    async def test_partition_detection(self, sync_setup):
        """Test network partition detection"""
        network, blockchain, synchronizer = sync_setup
        
        # No connected peers
        network.connections = {}
        
        is_partitioned = await synchronizer._detect_partition()
        assert is_partitioned
        
        # Add connected peer but no recent sync info
        network.connections = {'peer1': Mock()}
        synchronizer.peer_sync_info = {
            'peer1': PeerSyncInfo('peer1', 10, 'hash1', 0.8, time.time() - 400, 5.0)  # Old sync
        }
        
        is_partitioned = await synchronizer._detect_partition()
        assert is_partitioned
        
        # Recent sync info
        synchronizer.peer_sync_info['peer1'].last_sync = time.time()
        
        is_partitioned = await synchronizer._detect_partition()
        assert not is_partitioned
    
    @pytest.mark.asyncio
    async def test_sync_statistics(self, sync_setup):
        """Test synchronization statistics"""
        network, blockchain, synchronizer = sync_setup
        
        # Initial stats
        stats = synchronizer.get_sync_status()
        assert stats['state'] == 'synced'
        assert stats['peer_count'] == 0
        assert stats['pending_requests'] == 0
        
        # Add some activity
        synchronizer.stats['sync_requests_sent'] = 5
        synchronizer.stats['blocks_synced'] = 100
        synchronizer.peer_sync_info['peer1'] = PeerSyncInfo(
            'peer1', 10, 'hash1', 0.8, time.time(), 5.0
        )
        
        stats = synchronizer.get_sync_status()
        assert stats['peer_count'] == 1
        assert stats['stats']['sync_requests_sent'] == 5
        assert stats['stats']['blocks_synced'] == 100


class TestSyncMessageHandling:
    """Test sync message handling"""
    
    @pytest_asyncio.fixture
    async def message_setup(self):
        """Setup for message handling tests"""
        network = P2PNetwork("msg_test_node", listen_port=8021)
        blockchain = MockBlockchainManager()
        synchronizer = BlockchainSynchronizer(network, blockchain)
        
        yield network, blockchain, synchronizer
        
        await synchronizer.stop()
        if network.running:
            await network.stop()
    
    @pytest.mark.asyncio
    async def test_status_request_handling(self, message_setup):
        """Test handling of status requests"""
        network, blockchain, synchronizer = message_setup
        
        # Mock network send method
        network.send_message_to_peer = AsyncMock(return_value=True)
        
        # Create status request message
        message = P2PMessage(
            message_type=MessageType.SYNC_REQUEST,
            sender_id="peer1",
            recipient_id=network.node_id,
            payload={'type': 'status_request'},
            timestamp=time.time(),
            signature=''
        )
        
        await synchronizer._handle_sync_request(message)
        
        # Should have sent status response
        network.send_message_to_peer.assert_called_once()
        call_args = network.send_message_to_peer.call_args
        assert call_args[0][0] == "peer1"  # peer_id
        response_message = call_args[0][1]  # message
        assert response_message.message_type == MessageType.SYNC_REQUEST
        assert response_message.payload['type'] == 'status_response'
    
    @pytest.mark.asyncio
    async def test_block_sync_request_handling(self, message_setup):
        """Test handling of block sync requests"""
        network, blockchain, synchronizer = message_setup
        
        # Add some blocks to blockchain
        blockchain.blocks = [
            {'index': 0, 'hash': 'genesis', 'previous_hash': '', 'timestamp': time.time()},
            {'index': 1, 'hash': 'hash1', 'previous_hash': 'genesis', 'timestamp': time.time()},
            {'index': 2, 'hash': 'hash2', 'previous_hash': 'hash1', 'timestamp': time.time()},
        ]
        
        # Mock network send method
        network.send_message_to_peer = AsyncMock(return_value=True)
        
        # Create block sync request
        message = P2PMessage(
            message_type=MessageType.SYNC_REQUEST,
            sender_id="peer1",
            recipient_id=network.node_id,
            payload={
                'request_id': 'req123',
                'start_index': 1,
                'end_index': 2,
                'requester_id': 'peer1',
                'timestamp': time.time()
            },
            timestamp=time.time(),
            signature=''
        )
        
        await synchronizer._handle_sync_request(message)
        
        # Should have sent sync response with blocks
        network.send_message_to_peer.assert_called_once()
        call_args = network.send_message_to_peer.call_args
        response_message = call_args[0][1]
        assert response_message.message_type == MessageType.SYNC_RESPONSE
        assert len(response_message.payload['blocks']) == 2
    
    @pytest.mark.asyncio
    async def test_sync_response_handling(self, message_setup):
        """Test handling of sync responses"""
        network, blockchain, synchronizer = message_setup
        
        # Add pending request
        request_id = 'req123'
        synchronizer.pending_requests[request_id] = SyncRequest(
            request_id=request_id,
            start_index=1,
            end_index=2,
            requester_id=network.node_id,
            timestamp=time.time()
        )
        
        # Create sync response
        blocks = [
            {'index': 1, 'hash': 'hash1', 'previous_hash': 'genesis', 'timestamp': time.time()},
            {'index': 2, 'hash': 'hash2', 'previous_hash': 'hash1', 'timestamp': time.time()},
        ]
        
        headers = [
            {'index': 1, 'hash': 'hash1', 'previous_hash': 'genesis', 'timestamp': time.time(), 
             'merkle_root': 'merkle1', 'validator_count': 2, 'reputation_score': 0.8},
            {'index': 2, 'hash': 'hash2', 'previous_hash': 'hash1', 'timestamp': time.time(),
             'merkle_root': 'merkle2', 'validator_count': 2, 'reputation_score': 0.8},
        ]
        
        message = P2PMessage(
            message_type=MessageType.SYNC_RESPONSE,
            sender_id="peer1",
            recipient_id=network.node_id,
            payload={
                'request_id': request_id,
                'blocks': blocks,
                'headers': headers,
                'responder_id': 'peer1',
                'timestamp': time.time()
            },
            timestamp=time.time(),
            signature=''
        )
        
        await synchronizer._handle_sync_response(message)
        
        # Should have processed blocks and removed pending request
        assert request_id not in synchronizer.pending_requests
        assert synchronizer.stats['blocks_synced'] == 2
        assert len(blockchain.blocks) == 2


if __name__ == "__main__":
    pytest.main([__file__])