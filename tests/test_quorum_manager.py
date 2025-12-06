"""
Tests for Quorum Manager
"""

import pytest

from src.consensus.quorum_manager import (
    QuorumManager,
    QuorumStatus,
    QuorumResult
)


class TestQuorumManager:
    """Tests for QuorumManager"""
    
    def test_initialization(self):
        """Test quorum manager initialization"""
        manager = QuorumManager(quorum_percentage=0.66, min_nodes=2)
        
        assert manager.quorum_percentage == 0.66
        assert manager.min_nodes == 2
    
    def test_initialization_invalid_percentage(self):
        """Test initialization with invalid percentage"""
        with pytest.raises(ValueError):
            QuorumManager(quorum_percentage=0)
        
        with pytest.raises(ValueError):
            QuorumManager(quorum_percentage=1.5)
    
    def test_initialization_invalid_min_nodes(self):
        """Test initialization with invalid min nodes"""
        with pytest.raises(ValueError):
            QuorumManager(min_nodes=1)
    
    def test_calculate_required_nodes_2_nodes(self):
        """Test quorum calculation with 2 nodes"""
        manager = QuorumManager()
        
        # With 2 nodes, both are required (100%)
        required = manager.calculate_required_nodes(2)
        assert required == 2
    
    def test_calculate_required_nodes_3_nodes(self):
        """Test quorum calculation with 3 nodes"""
        manager = QuorumManager()
        
        # With 3 nodes, 2 are required (66.7%)
        required = manager.calculate_required_nodes(3)
        assert required == 2
    
    def test_calculate_required_nodes_10_nodes(self):
        """Test quorum calculation with 10 nodes"""
        manager = QuorumManager()
        
        # With 10 nodes, 7 are required (70%)
        required = manager.calculate_required_nodes(10)
        assert required == 7
    
    def test_calculate_required_nodes_100_nodes(self):
        """Test quorum calculation with 100 nodes"""
        manager = QuorumManager()
        
        # With 100 nodes, 66 are required (ceil(100*0.66)=66)
        required = manager.calculate_required_nodes(100)
        assert required == 66
    
    def test_calculate_required_nodes_1000_nodes(self):
        """Test quorum calculation with 1000 nodes"""
        manager = QuorumManager()
        
        # With 1000 nodes, 660 are required (ceil(1000*0.66)=660)
        required = manager.calculate_required_nodes(1000)
        assert required == 660
    
    def test_check_quorum_insufficient_nodes(self):
        """Test quorum check with insufficient total nodes"""
        manager = QuorumManager()
        
        active_nodes = {'node1'}
        all_nodes = {'node1'}
        
        result = manager.check_quorum(active_nodes, all_nodes)
        
        assert result.status == QuorumStatus.INSUFFICIENT_NODES
        assert not result.can_proceed
        assert result.total_nodes == 1
        assert result.active_nodes == 1
    
    def test_check_quorum_achieved_2_nodes(self):
        """Test quorum achieved with 2 nodes"""
        manager = QuorumManager()
        
        active_nodes = {'node1', 'node2'}
        all_nodes = {'node1', 'node2'}
        
        result = manager.check_quorum(active_nodes, all_nodes)
        
        assert result.status == QuorumStatus.ACHIEVED
        assert result.can_proceed
        assert result.total_nodes == 2
        assert result.active_nodes == 2
        assert result.required_nodes == 2
    
    def test_check_quorum_not_achieved_2_nodes(self):
        """Test quorum not achieved with 2 nodes (1 active)"""
        manager = QuorumManager()
        
        active_nodes = {'node1'}
        all_nodes = {'node1', 'node2'}
        
        result = manager.check_quorum(active_nodes, all_nodes)
        
        assert result.status == QuorumStatus.NOT_ACHIEVED
        assert not result.can_proceed
        assert result.total_nodes == 2
        assert result.active_nodes == 1
        assert result.required_nodes == 2
    
    def test_check_quorum_achieved_3_nodes(self):
        """Test quorum achieved with 3 nodes (2 active)"""
        manager = QuorumManager()
        
        active_nodes = {'node1', 'node2'}
        all_nodes = {'node1', 'node2', 'node3'}
        
        result = manager.check_quorum(active_nodes, all_nodes)
        
        assert result.status == QuorumStatus.ACHIEVED
        assert result.can_proceed
        assert result.total_nodes == 3
        assert result.active_nodes == 2
        assert result.required_nodes == 2
    
    def test_check_quorum_achieved_10_nodes(self):
        """Test quorum achieved with 10 nodes (7 active)"""
        manager = QuorumManager()
        
        active_nodes = {f'node{i}' for i in range(7)}
        all_nodes = {f'node{i}' for i in range(10)}
        
        result = manager.check_quorum(active_nodes, all_nodes)
        
        assert result.status == QuorumStatus.ACHIEVED
        assert result.can_proceed
        assert result.total_nodes == 10
        assert result.active_nodes == 7
        assert result.required_nodes == 7
    
    def test_check_quorum_not_achieved_10_nodes(self):
        """Test quorum not achieved with 10 nodes (6 active)"""
        manager = QuorumManager()
        
        active_nodes = {f'node{i}' for i in range(6)}
        all_nodes = {f'node{i}' for i in range(10)}
        
        result = manager.check_quorum(active_nodes, all_nodes)
        
        assert result.status == QuorumStatus.NOT_ACHIEVED
        assert not result.can_proceed
        assert result.total_nodes == 10
        assert result.active_nodes == 6
        assert result.required_nodes == 7
    
    def test_can_add_block_true(self):
        """Test can add block when quorum is achieved"""
        manager = QuorumManager()
        
        validating_nodes = {'node1', 'node2'}
        all_nodes = {'node1', 'node2', 'node3'}
        
        assert manager.can_add_block(validating_nodes, all_nodes)
    
    def test_can_add_block_false(self):
        """Test can add block when quorum is not achieved"""
        manager = QuorumManager()
        
        validating_nodes = {'node1'}
        all_nodes = {'node1', 'node2', 'node3'}
        
        assert not manager.can_add_block(validating_nodes, all_nodes)
    
    def test_get_quorum_info(self):
        """Test getting quorum information"""
        manager = QuorumManager()
        
        info = manager.get_quorum_info(10)
        
        assert info['total_nodes'] == 10
        assert info['required_nodes'] == 7
        assert info['quorum_percentage_target'] == 66.0
        assert info['actual_percentage'] == 70.0
        assert info['min_nodes'] == 2
        assert info['can_operate']
    
    def test_get_quorum_table(self):
        """Test generating quorum table"""
        manager = QuorumManager()
        
        table = manager.get_quorum_table(max_nodes=5)
        
        assert len(table) == 5
        assert table[0]['total_nodes'] == 1
        assert table[1]['total_nodes'] == 2
        assert table[2]['total_nodes'] == 3
        
        # Check specific values
        assert table[1]['required_nodes'] == 2  # 2 nodes need 2
        assert table[2]['required_nodes'] == 2  # 3 nodes need 2
        assert table[4]['required_nodes'] == 4  # 5 nodes need 4 (ceil(5*0.66)=4)
    
    def test_validate_consensus_achieved(self):
        """Test consensus validation when achieved"""
        manager = QuorumManager()
        
        votes = {
            'node1': True,
            'node2': True,
            'node3': False
        }
        all_nodes = {'node1', 'node2', 'node3'}
        
        consensus, message = manager.validate_consensus(votes, all_nodes)
        
        assert consensus
        assert '2/3' in message
    
    def test_validate_consensus_not_achieved(self):
        """Test consensus validation when not achieved"""
        manager = QuorumManager()
        
        votes = {
            'node1': True,
            'node2': False,
            'node3': False
        }
        all_nodes = {'node1', 'node2', 'node3'}
        
        consensus, message = manager.validate_consensus(votes, all_nodes)
        
        assert not consensus
    
    def test_get_missing_nodes_count_quorum_achieved(self):
        """Test getting missing nodes count when quorum achieved"""
        manager = QuorumManager()
        
        active_nodes = {'node1', 'node2'}
        all_nodes = {'node1', 'node2', 'node3'}
        
        missing = manager.get_missing_nodes_count(active_nodes, all_nodes)
        
        assert missing == 0
    
    def test_get_missing_nodes_count_quorum_not_achieved(self):
        """Test getting missing nodes count when quorum not achieved"""
        manager = QuorumManager()
        
        active_nodes = {'node1'}
        all_nodes = {'node1', 'node2', 'node3'}
        
        missing = manager.get_missing_nodes_count(active_nodes, all_nodes)
        
        assert missing == 1  # Need 1 more node (2 required, 1 active)
    
    def test_quorum_scaling(self):
        """Test that quorum scales correctly with network size"""
        manager = QuorumManager()
        
        # Test various network sizes
        test_cases = [
            (2, 2),      # 2 nodes -> 2 required (100%)
            (3, 2),      # 3 nodes -> 2 required (66.7%)
            (10, 7),     # 10 nodes -> 7 required (70%)
            (50, 33),    # 50 nodes -> 33 required (ceil(50*0.66)=33)
            (100, 66),   # 100 nodes -> 66 required (ceil(100*0.66)=66)
            (1000, 660), # 1000 nodes -> 660 required (ceil(1000*0.66)=660)
        ]
        
        for total, expected_required in test_cases:
            required = manager.calculate_required_nodes(total)
            assert required == expected_required, \
                f"Failed for {total} nodes: expected {expected_required}, got {required}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
