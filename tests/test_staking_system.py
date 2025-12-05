"""
Tests for the Staking System.
"""

import pytest
import time
from decimal import Decimal

from src.blockchain.staking_system import (
    StakingSystem, Stake, AINodeInfo, StakeStatus
)
from src.blockchain.transaction import TransactionType


class TestStake:
    """Tests for Stake dataclass."""
    
    def test_stake_creation(self):
        """Test creating a stake."""
        stake = Stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1",
            timestamp=time.time()
        )
        
        assert stake.staker_address == "staker1"
        assert stake.amount == Decimal('1000.0')
        assert stake.status == StakeStatus.ACTIVE
        assert stake.accumulated_rewards == Decimal('0.0')
    
    def test_stake_duration_calculation(self):
        """Test calculating stake duration."""
        start_time = time.time()
        stake = Stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1",
            timestamp=start_time
        )
        
        time.sleep(0.1)
        duration = stake.calculate_stake_duration()
        assert duration >= 0.1
    
    def test_stake_serialization(self):
        """Test stake to/from dict conversion."""
        stake = Stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1",
            timestamp=time.time()
        )
        
        stake_dict = stake.to_dict()
        restored_stake = Stake.from_dict(stake_dict)
        
        assert restored_stake.staker_address == stake.staker_address
        assert restored_stake.amount == stake.amount
        assert restored_stake.delegated_node_id == stake.delegated_node_id


class TestAINodeInfo:
    """Tests for AINodeInfo dataclass."""
    
    def test_node_info_creation(self):
        """Test creating AI node info."""
        node = AINodeInfo(
            node_id="node1",
            model_name="Gemma 3 4B",
            model_hash="abc123",
            reputation_score=0.95,
            total_validations=1000,
            uptime_percentage=99.5
        )
        
        assert node.node_id == "node1"
        assert node.is_active is True
        assert node.total_delegated == Decimal('0.0')
    
    def test_node_info_serialization(self):
        """Test node info to dict conversion."""
        node = AINodeInfo(
            node_id="node1",
            model_name="Gemma 3 4B",
            model_hash="abc123",
            reputation_score=0.95,
            total_validations=1000,
            uptime_percentage=99.5
        )
        
        node_dict = node.to_dict()
        assert node_dict['node_id'] == "node1"
        assert node_dict['model_name'] == "Gemma 3 4B"
        assert node_dict['is_active'] is True


class TestStakingSystem:
    """Tests for StakingSystem."""
    
    @pytest.fixture
    def staking_system(self):
        """Create a staking system for testing."""
        return StakingSystem(
            min_stake_amount=Decimal('100.0'),
            withdrawal_delay_seconds=10  # Short delay for testing
        )
    
    @pytest.fixture
    def sample_node(self):
        """Create a sample AI node."""
        return AINodeInfo(
            node_id="node1",
            model_name="Gemma 3 4B",
            model_hash="abc123",
            reputation_score=0.95,
            total_validations=1000,
            uptime_percentage=99.5
        )
    
    def test_register_ai_node(self, staking_system, sample_node):
        """Test registering an AI node."""
        success = staking_system.register_ai_node(sample_node)
        assert success is True
        
        # Try registering same node again
        success = staking_system.register_ai_node(sample_node)
        assert success is False
    
    def test_get_available_nodes(self, staking_system, sample_node):
        """Test getting available nodes."""
        staking_system.register_ai_node(sample_node)
        
        nodes = staking_system.get_available_nodes()
        assert len(nodes) == 1
        assert nodes[0].node_id == "node1"
        
        # Test with reputation filter
        nodes = staking_system.get_available_nodes(min_reputation=0.9)
        assert len(nodes) == 1
        
        nodes = staking_system.get_available_nodes(min_reputation=0.99)
        assert len(nodes) == 0
    
    def test_delegate_stake_success(self, staking_system, sample_node):
        """Test successful stake delegation."""
        staking_system.register_ai_node(sample_node)
        
        success, message = staking_system.delegate_stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1"
        )
        
        assert success is True
        assert "Successfully delegated" in message
        assert staking_system.total_staked == Decimal('1000.0')
        
        # Check node stats updated
        node = staking_system.ai_nodes["node1"]
        assert node.total_delegated == Decimal('1000.0')
        assert node.delegator_count == 1
    
    def test_delegate_stake_minimum_amount(self, staking_system, sample_node):
        """Test stake delegation with insufficient amount."""
        staking_system.register_ai_node(sample_node)
        
        success, message = staking_system.delegate_stake(
            staker_address="staker1",
            amount=Decimal('50.0'),  # Below minimum
            delegated_node_id="node1"
        )
        
        assert success is False
        assert "Minimum stake amount" in message
    
    def test_delegate_stake_invalid_node(self, staking_system):
        """Test stake delegation to non-existent node."""
        success, message = staking_system.delegate_stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="nonexistent"
        )
        
        assert success is False
        assert "not found" in message
    
    def test_delegate_stake_already_staking(self, staking_system, sample_node):
        """Test delegating when already have active stake."""
        staking_system.register_ai_node(sample_node)
        
        # First stake
        staking_system.delegate_stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1"
        )
        
        # Try to stake again
        success, message = staking_system.delegate_stake(
            staker_address="staker1",
            amount=Decimal('500.0'),
            delegated_node_id="node1"
        )
        
        assert success is False
        assert "Already have an active stake" in message
    
    def test_request_unstake(self, staking_system, sample_node):
        """Test requesting to unstake."""
        staking_system.register_ai_node(sample_node)
        staking_system.delegate_stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1"
        )
        
        success, message = staking_system.request_unstake("staker1")
        assert success is True
        assert "Withdrawal requested" in message
        
        stake = staking_system.stakes["staker1"]
        assert stake.status == StakeStatus.PENDING_WITHDRAWAL
        assert stake.withdrawal_request_time is not None
    
    def test_complete_unstake_before_delay(self, staking_system, sample_node):
        """Test completing unstake before delay period."""
        staking_system.register_ai_node(sample_node)
        staking_system.delegate_stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1"
        )
        staking_system.request_unstake("staker1")
        
        # Try to complete immediately
        success, message, amount = staking_system.complete_unstake("staker1")
        assert success is False
        assert "delay not met" in message
        assert amount is None
    
    def test_complete_unstake_after_delay(self, staking_system, sample_node):
        """Test completing unstake after delay period."""
        staking_system.register_ai_node(sample_node)
        staking_system.delegate_stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1"
        )
        staking_system.request_unstake("staker1")
        
        # Wait for delay
        time.sleep(11)  # withdrawal_delay_seconds is 10
        
        success, message, amount = staking_system.complete_unstake("staker1")
        assert success is True
        assert amount == Decimal('1000.0')
        assert staking_system.total_staked == Decimal('0.0')
        
        # Check node stats updated
        node = staking_system.ai_nodes["node1"]
        assert node.total_delegated == Decimal('0.0')
        assert node.delegator_count == 0
    
    def test_calculate_staking_rewards(self, staking_system, sample_node):
        """Test calculating staking rewards."""
        staking_system.register_ai_node(sample_node)
        
        # Create multiple stakes
        staking_system.delegate_stake("staker1", Decimal('1000.0'), "node1")
        staking_system.delegate_stake("staker2", Decimal('500.0'), "node1")
        
        # Calculate rewards (10% of block reward)
        staker_portion = Decimal('100.0')  # 10% of 1000 block reward
        rewards = staking_system.calculate_staking_rewards(staker_portion)
        
        assert len(rewards) == 2
        
        # Staker1 has 2/3 of total stake, should get 2/3 of rewards
        expected_reward1 = Decimal('66.666666666666666666666666667')
        assert abs(rewards["staker1"] - expected_reward1) < Decimal('0.01')
        
        # Staker2 has 1/3 of total stake, should get 1/3 of rewards
        expected_reward2 = Decimal('33.333333333333333333333333333')
        assert abs(rewards["staker2"] - expected_reward2) < Decimal('0.01')
        
        # Check accumulated rewards
        stake1 = staking_system.stakes["staker1"]
        assert stake1.accumulated_rewards > Decimal('0.0')
    
    def test_get_stake_info(self, staking_system, sample_node):
        """Test getting stake information."""
        staking_system.register_ai_node(sample_node)
        staking_system.delegate_stake("staker1", Decimal('1000.0'), "node1")
        
        info = staking_system.get_stake_info("staker1")
        assert info is not None
        assert info['stake']['staker_address'] == "staker1"
        assert info['node_info']['node_id'] == "node1"
        assert info['can_withdraw'] is False
    
    def test_get_node_delegations_info(self, staking_system, sample_node):
        """Test getting node delegation information."""
        staking_system.register_ai_node(sample_node)
        staking_system.delegate_stake("staker1", Decimal('1000.0'), "node1")
        staking_system.delegate_stake("staker2", Decimal('500.0'), "node1")
        
        info = staking_system.get_node_delegations_info("node1")
        assert info is not None
        assert len(info['delegators']) == 2
        assert info['delegator_count'] == 2
        assert Decimal(info['total_delegated']) == Decimal('1500.0')
    
    def test_get_staking_stats(self, staking_system, sample_node):
        """Test getting staking statistics."""
        staking_system.register_ai_node(sample_node)
        staking_system.delegate_stake("staker1", Decimal('1000.0'), "node1")
        
        stats = staking_system.get_staking_stats()
        assert Decimal(stats['total_staked']) == Decimal('1000.0')
        assert stats['active_stakes_count'] == 1
        assert stats['registered_nodes_count'] == 1
    
    def test_create_stake_transaction(self, staking_system):
        """Test creating a stake transaction."""
        tx = staking_system.create_stake_transaction(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            delegated_node_id="node1",
            nonce=0
        )
        
        assert tx.from_address == "staker1"
        assert tx.to_address == "stake:node1"
        assert tx.amount == Decimal('1000.0')
        assert tx.transaction_type == TransactionType.STAKE
    
    def test_create_unstake_transaction(self, staking_system, sample_node):
        """Test creating an unstake transaction."""
        staking_system.register_ai_node(sample_node)
        staking_system.delegate_stake("staker1", Decimal('1000.0'), "node1")
        
        tx = staking_system.create_unstake_transaction(
            staker_address="staker1",
            nonce=0
        )
        
        assert tx is not None
        assert tx.from_address == "stake:node1"
        assert tx.to_address == "staker1"
        assert tx.transaction_type == TransactionType.UNSTAKE
    
    def test_update_ai_node(self, staking_system, sample_node):
        """Test updating AI node information."""
        staking_system.register_ai_node(sample_node)
        
        success = staking_system.update_ai_node(
            "node1",
            reputation_score=0.98,
            total_validations=1500
        )
        
        assert success is True
        node = staking_system.ai_nodes["node1"]
        assert node.reputation_score == 0.98
        assert node.total_validations == 1500
    
    def test_multiple_stakers_same_node(self, staking_system, sample_node):
        """Test multiple stakers delegating to same node."""
        staking_system.register_ai_node(sample_node)
        
        # Multiple stakers
        staking_system.delegate_stake("staker1", Decimal('1000.0'), "node1")
        staking_system.delegate_stake("staker2", Decimal('2000.0'), "node1")
        staking_system.delegate_stake("staker3", Decimal('500.0'), "node1")
        
        assert staking_system.total_staked == Decimal('3500.0')
        
        node = staking_system.ai_nodes["node1"]
        assert node.total_delegated == Decimal('3500.0')
        assert node.delegator_count == 3
        
        # Calculate rewards
        rewards = staking_system.calculate_staking_rewards(Decimal('100.0'))
        assert len(rewards) == 3
        
        # Verify proportional distribution
        total_rewards = sum(rewards.values())
        assert abs(total_rewards - Decimal('100.0')) < Decimal('0.01')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
