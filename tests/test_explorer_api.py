"""
Tests for Block Explorer API
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from src.api.explorer_api import ExplorerAPI
from src.blockchain.block import Block
from src.blockchain.transaction import Transaction, TransactionType
from decimal import Decimal


class MockBlockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
    
    def get_balance(self, address):
        return Decimal('100.0')
    
    def get_total_supply(self):
        return Decimal('1000000.0')
    
    def get_circulating_supply(self):
        return Decimal('900000.0')


class MockP2PNetwork:
    def __init__(self):
        self.peers = ['node1', 'node2', 'node3']
    
    def get_active_peers(self):
        return self.peers
    
    def get_peer_info(self, peer_id):
        return {
            'model_name': 'Gemma 3 4B',
            'model_hash': 'abc123'
        }


class MockReputationManager:
    def get_reputation(self, node_id):
        return {
            'score': 85.5,
            'total_validations': 150,
            'last_validation': time.time()
        }


@pytest.fixture
def mock_blockchain():
    blockchain = MockBlockchain()
    
    # Create some test blocks
    for i in range(5):
        block = Block(
            index=i,
            previous_hash='0' * 64 if i == 0 else f'hash{i-1}',
            timestamp=time.time() - (5 - i) * 60,
            transactions=[],
            merkle_root='merkle' + str(i)
        )
        block.hash = f'hash{i}'
        block.ai_validators = ['node1', 'node2']
        blockchain.chain.append(block)
    
    return blockchain


@pytest.fixture
def mock_p2p():
    return MockP2PNetwork()


@pytest.fixture
def mock_reputation():
    return MockReputationManager()


@pytest.fixture
def explorer_api(mock_blockchain, mock_p2p, mock_reputation):
    api = ExplorerAPI(mock_blockchain, mock_p2p, mock_reputation)
    return api


def test_calculate_network_metrics(explorer_api):
    """Test network metrics calculation"""
    metrics = explorer_api.calculate_network_metrics()
    
    assert 'tps' in metrics
    assert 'latency' in metrics
    assert 'active_nodes' in metrics
    assert 'block_height' in metrics
    assert 'total_supply' in metrics
    assert 'circulating_supply' in metrics
    assert 'timestamp' in metrics
    
    assert metrics['active_nodes'] == 3
    assert metrics['block_height'] == 5
    assert metrics['total_supply'] == Decimal('1000000.0')


def test_get_recent_blocks(explorer_api):
    """Test getting recent blocks"""
    blocks = explorer_api.get_recent_blocks(limit=3)
    
    assert len(blocks) == 3
    assert blocks[0]['index'] == 4  # Most recent first
    assert blocks[1]['index'] == 3
    assert blocks[2]['index'] == 2
    
    # Check block structure
    assert 'hash' in blocks[0]
    assert 'previous_hash' in blocks[0]
    assert 'timestamp' in blocks[0]
    assert 'transactions' in blocks[0]
    assert 'ai_validators' in blocks[0]


def test_find_block_by_hash(explorer_api):
    """Test finding block by hash"""
    block = explorer_api.find_block_by_hash('hash2')
    
    assert block is not None
    assert block.index == 2
    assert block.hash == 'hash2'
    
    # Test non-existent block
    block = explorer_api.find_block_by_hash('nonexistent')
    assert block is None


def test_get_address_details(explorer_api):
    """Test getting address details"""
    address = 'test_address_123'
    details = explorer_api.get_address_details(address)
    
    assert 'address' in details
    assert 'balance' in details
    assert 'transaction_count' in details
    assert 'reputation' in details
    
    assert details['address'] == address
    assert details['balance'] == 100.0


def test_get_node_distribution_stats(explorer_api):
    """Test getting node distribution statistics"""
    stats = explorer_api.get_node_distribution_stats()
    
    assert 'models' in stats
    assert 'nodes' in stats
    assert 'total_nodes' in stats
    
    assert stats['total_nodes'] == 3
    assert len(stats['nodes']) == 3
    
    # Check node details
    node = stats['nodes'][0]
    assert 'node_id' in node
    assert 'model_name' in node
    assert 'reputation_score' in node
    assert 'total_validations' in node


def test_serialize_block(explorer_api, mock_blockchain):
    """Test block serialization"""
    block = mock_blockchain.chain[0]
    serialized = explorer_api.serialize_block(block)
    
    assert serialized['index'] == block.index
    assert serialized['hash'] == block.hash
    assert serialized['previous_hash'] == block.previous_hash
    assert serialized['timestamp'] == block.timestamp
    assert isinstance(serialized['transactions'], list)
    assert isinstance(serialized['ai_validators'], list)


def test_serialize_transaction(explorer_api):
    """Test transaction serialization"""
    tx = Transaction(
        from_address='addr1',
        to_address='addr2',
        amount=Decimal('50.0'),
        fee=Decimal('0.1')
    )
    tx.timestamp = time.time()
    tx.transaction_type = TransactionType.TRANSFER
    
    serialized = explorer_api.serialize_transaction(tx, 'confirmed')
    
    assert serialized['from_address'] == 'addr1'
    assert serialized['to_address'] == 'addr2'
    assert serialized['amount'] == 50.0
    assert serialized['fee'] == 0.1
    assert serialized['status'] == 'confirmed'
    assert 'hash' in serialized


def test_calculate_tps(explorer_api, mock_blockchain):
    """Test TPS calculation"""
    # Add transactions to recent blocks
    now = time.time()
    for i in range(3):
        block = Block(
            index=len(mock_blockchain.chain),
            previous_hash='prev',
            timestamp=now - (i * 10),
            transactions=[
                Transaction('addr1', 'addr2', Decimal('10'), Decimal('0.1'))
                for _ in range(5)
            ],
            merkle_root='merkle'
        )
        block.hash = f'recent_hash{i}'
        mock_blockchain.chain.append(block)
    
    tps = explorer_api.calculate_tps()
    assert tps > 0  # Should have some TPS from recent transactions


def test_record_block_latency(explorer_api):
    """Test recording block latency"""
    explorer_api.record_block_latency(50)
    explorer_api.record_block_latency(60)
    explorer_api.record_block_latency(55)
    
    assert len(explorer_api.latency_samples) == 3
    
    latency = explorer_api.calculate_average_latency()
    assert latency == 55  # Average of 50, 60, 55


def test_perform_search_block(explorer_api):
    """Test search for block"""
    result = explorer_api.perform_search('hash2')
    
    assert result['type'] == 'block'
    assert result['data']['index'] == 2


def test_perform_search_not_found(explorer_api):
    """Test search with no results"""
    result = explorer_api.perform_search('nonexistent_hash')
    
    assert result['type'] == 'not_found'
    assert result['data'] is None


def test_get_tps_history(explorer_api):
    """Test getting TPS history"""
    # Add some metrics to history
    now = time.time()
    for i in range(10):
        explorer_api.metrics_history.append({
            'timestamp': now - (i * 300),  # Every 5 minutes
            'tps': 100 + i
        })
    
    history = explorer_api.get_tps_history(hours=1)
    assert len(history) > 0
    assert all('tps' in m for m in history)


def test_get_latency_history(explorer_api):
    """Test getting latency history"""
    # Add some metrics to history
    now = time.time()
    for i in range(10):
        explorer_api.metrics_history.append({
            'timestamp': now - (i * 300),
            'latency': 50 + i
        })
    
    history = explorer_api.get_latency_history(hours=1)
    assert len(history) > 0
    assert all('latency' in m for m in history)


def test_api_routes_exist(explorer_api):
    """Test that all required API routes are registered"""
    routes = [rule.rule for rule in explorer_api.app.url_map.iter_rules()]
    
    assert '/api/network/metrics' in routes
    assert '/api/blocks/recent' in routes
    assert '/api/transactions/recent' in routes
    assert '/api/nodes/distribution' in routes
    assert '/api/search' in routes
    assert '/api/stats/tps' in routes
    assert '/api/stats/latency' in routes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
