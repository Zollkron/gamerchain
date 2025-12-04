"""
Tests for the reputation interface.
"""

import pytest
import tempfile
import shutil
from decimal import Decimal

from src.reputation.reputation_interface import ReputationInterface
from src.reputation.reputation_types import NodeBehaviorType, PenaltySeverity


class TestReputationInterface:
    """Test cases for ReputationInterface."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def reputation_interface(self, temp_dir):
        """Create a reputation interface instance for testing."""
        return ReputationInterface(data_dir=temp_dir)
    
    def test_user_reputation_display_new_user(self, reputation_interface):
        """Test reputation display for new user."""
        user_id = "new_user"
        
        display_data = reputation_interface.get_user_reputation_display(user_id)
        
        assert display_data['reputation_score'] == 50.0
        assert display_data['priority_level'] == 1
        assert display_data['priority_name'] == 'Standard'
        assert display_data['tokens_burned'] == '0.00'
        assert display_data['voluntary_burns'] == 0
        assert display_data['transaction_count'] == 0
        assert display_data['priority_multiplier'] == 1.0
        assert display_data['next_level_threshold'] == 75.0
        assert display_data['progress_to_next'] == 0.0
        assert not display_data['is_high_priority']
    
    def test_user_reputation_display_with_burns(self, reputation_interface):
        """Test reputation display after token burns."""
        user_id = "test_user"
        
        # Burn tokens to increase reputation
        burn_result = reputation_interface.burn_tokens_for_reputation(user_id, Decimal('10.0'))
        
        assert burn_result['reputation_score'] == 150.0  # 50 + 10*10
        assert burn_result['priority_level'] == 3  # Silver level
        assert burn_result['priority_name'] == 'Silver'
        assert burn_result['tokens_burned'] == '10.0'
        assert burn_result['voluntary_burns'] == 1
        assert burn_result['priority_multiplier'] == 2.0
        assert burn_result['next_level_threshold'] == 300.0
        
        # Check progress calculation
        # Current: 150, Previous threshold: 150, Next: 300
        # Progress should be 0.0 since we're exactly at the threshold
        assert burn_result['progress_to_next'] == 0.0
    
    def test_burn_tokens_validation(self, reputation_interface):
        """Test token burn validation."""
        user_id = "test_user"
        
        # Should raise error for negative amount
        with pytest.raises(ValueError, match="Burn amount must be positive"):
            reputation_interface.burn_tokens_for_reputation(user_id, Decimal('-5.0'))
        
        # Should raise error for zero amount
        with pytest.raises(ValueError, match="Burn amount must be positive"):
            reputation_interface.burn_tokens_for_reputation(user_id, Decimal('0.0'))
    
    def test_transaction_priority_info(self, reputation_interface):
        """Test transaction priority information."""
        user_id = "test_user"
        
        # Initial priority
        priority_info = reputation_interface.get_transaction_priority_info(user_id)
        assert priority_info['priority_level'] == 1
        assert priority_info['priority_name'] == 'Standard'
        assert priority_info['priority_multiplier'] == 1.0
        assert not priority_info['is_high_priority']
        assert 'estimated_processing_time' in priority_info
        assert 'queue_position_estimate' in priority_info
        
        # After burning tokens
        reputation_interface.burn_tokens_for_reputation(user_id, Decimal('50.0'))
        priority_info = reputation_interface.get_transaction_priority_info(user_id)
        
        assert priority_info['priority_level'] == 5  # Platinum level
        assert priority_info['priority_name'] == 'Platinum'
        assert priority_info['priority_multiplier'] == 5.0
        assert priority_info['is_high_priority']
    
    def test_node_reputation_summary(self, reputation_interface):
        """Test node reputation summary."""
        node_id = "test_node"
        
        # Non-existent node
        summary = reputation_interface.get_node_reputation_summary(node_id)
        assert summary is None
        
        # Register node and add some activity
        reputation_interface.node_engine.register_node(node_id)
        reputation_interface.node_engine.record_successful_validation(node_id)
        reputation_interface.node_engine.apply_penalty(
            node_id,
            NodeBehaviorType.NETWORK_DELAY,
            PenaltySeverity.LIGHT
        )
        
        summary = reputation_interface.get_node_reputation_summary(node_id)
        assert summary is not None
        assert summary['node_id'] == node_id
        assert summary['total_validations'] == 1
        assert summary['success_rate'] == 1.0
        assert summary['penalties_applied'] == 1
        assert summary['is_eligible']
        assert 'reputation_score' in summary
        assert 'participation_rate' in summary
        assert 'reliability_score' in summary
        assert 'last_activity' in summary
    
    def test_network_health(self, reputation_interface):
        """Test network health metrics."""
        # Add some nodes and users
        reputation_interface.node_engine.register_node("node_1")
        reputation_interface.node_engine.register_node("node_2")
        reputation_interface.node_engine.record_successful_validation("node_1")
        
        reputation_interface.user_engine.register_user("user_1")
        reputation_interface.burn_tokens_for_reputation("user_1", Decimal('15.0'))
        
        health = reputation_interface.get_network_health()
        
        assert 'nodes' in health
        assert 'users' in health
        
        # Check node metrics
        node_metrics = health['nodes']
        assert node_metrics['total_nodes'] == 2
        assert node_metrics['eligible_nodes'] == 2
        assert node_metrics['total_validations'] == 1
        
        # Check user metrics
        user_metrics = health['users']
        assert user_metrics['total_users'] == 1
        assert user_metrics['total_burns'] == '15.0'
    
    def test_top_performers(self, reputation_interface):
        """Test top performers listing."""
        # Add nodes with different performance
        nodes = ["node_1", "node_2", "node_3"]
        for i, node_id in enumerate(nodes):
            reputation_interface.node_engine.register_node(node_id)
            for _ in range(i + 1):  # Different validation counts
                reputation_interface.node_engine.record_successful_validation(node_id)
        
        # Add users with different burn amounts
        users = ["user_1", "user_2", "user_3"]
        burn_amounts = [Decimal('5.0'), Decimal('15.0'), Decimal('10.0')]
        for user_id, amount in zip(users, burn_amounts):
            reputation_interface.burn_tokens_for_reputation(user_id, amount)
        
        performers = reputation_interface.get_top_performers(limit=2)
        
        assert 'top_nodes' in performers
        assert 'top_users' in performers
        
        # Check top nodes (should be sorted by reputation)
        top_nodes = performers['top_nodes']
        assert len(top_nodes) == 2
        assert top_nodes[0]['node_id'] == 'node_3'  # Most validations
        assert top_nodes[1]['node_id'] == 'node_2'
        
        # Check top users (should be sorted by reputation)
        top_users = performers['top_users']
        assert len(top_users) == 2
        assert top_users[0]['user_id'] == 'user_2'  # Highest burn amount
        assert top_users[1]['user_id'] == 'user_3'
    
    def test_transaction_prioritization(self, reputation_interface):
        """Test transaction prioritization logic."""
        user_id = "test_user"
        
        # Initially should not be prioritized
        assert not reputation_interface.should_prioritize_transaction(user_id)
        
        # Burn enough tokens to reach high priority
        reputation_interface.burn_tokens_for_reputation(user_id, Decimal('10.0'))  # 150 reputation
        assert reputation_interface.should_prioritize_transaction(user_id)
    
    def test_fee_discount(self, reputation_interface):
        """Test fee discount calculation."""
        user_id = "test_user"
        
        # Initial discount (none)
        assert reputation_interface.get_transaction_fee_discount(user_id) == 1.0
        
        # Burn tokens to increase priority
        reputation_interface.burn_tokens_for_reputation(user_id, Decimal('2.5'))  # Level 2
        assert reputation_interface.get_transaction_fee_discount(user_id) == 0.95  # 5% discount
        
        reputation_interface.burn_tokens_for_reputation(user_id, Decimal('7.5'))  # Level 3
        assert reputation_interface.get_transaction_fee_discount(user_id) == 0.90  # 10% discount
        
        reputation_interface.burn_tokens_for_reputation(user_id, Decimal('15.0'))  # Level 4
        assert reputation_interface.get_transaction_fee_discount(user_id) == 0.85  # 15% discount
        
        reputation_interface.burn_tokens_for_reputation(user_id, Decimal('20.0'))  # Level 5
        assert reputation_interface.get_transaction_fee_discount(user_id) == 0.80  # 20% discount
    
    def test_transaction_recording(self, reputation_interface):
        """Test transaction recording."""
        user_id = "test_user"
        
        # Record some transactions
        for _ in range(3):
            reputation_interface.record_user_transaction(user_id)
        
        display_data = reputation_interface.get_user_reputation_display(user_id)
        assert display_data['transaction_count'] == 3
    
    def test_priority_level_progression(self, reputation_interface):
        """Test priority level progression with burns."""
        user_id = "test_user"
        
        # Test each level
        test_cases = [
            (Decimal('0.0'), 1, 'Standard'),
            (Decimal('2.5'), 2, 'Bronze'),     # 75 reputation
            (Decimal('10.0'), 3, 'Silver'),    # 150 reputation  
            (Decimal('25.0'), 4, 'Gold'),      # 300 reputation
            (Decimal('45.0'), 5, 'Platinum'),  # 500 reputation
        ]
        
        for burn_amount, expected_level, expected_name in test_cases:
            # Reset user
            reputation_interface.user_engine.user_scores.pop(user_id, None)
            
            if burn_amount > 0:
                reputation_interface.burn_tokens_for_reputation(user_id, burn_amount)
            
            display_data = reputation_interface.get_user_reputation_display(user_id)
            assert display_data['priority_level'] == expected_level
            assert display_data['priority_name'] == expected_name
    
    def test_progress_calculation(self, reputation_interface):
        """Test progress to next level calculation."""
        user_id = "test_user"
        
        # Burn tokens to get to middle of level 2 (between 75 and 150)
        reputation_interface.burn_tokens_for_reputation(user_id, Decimal('11.25'))  # 162.5 reputation
        
        display_data = reputation_interface.get_user_reputation_display(user_id)
        
        # Should be in level 3 (150-300 range)
        assert display_data['priority_level'] == 3
        
        # Progress from 150 to 300: (162.5 - 150) / (300 - 150) = 12.5 / 150 ≈ 0.083
        expected_progress = (162.5 - 150) / (300 - 150)
        assert abs(display_data['progress_to_next'] - expected_progress) < 0.001