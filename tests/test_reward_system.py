"""
Tests for PlayerGold reward distribution system.
"""

import pytest
import time
from decimal import Decimal

from src.blockchain.reward_system import (
    RewardCalculator, StakeManager, StakeType,
    AIValidatorReward, StakerReward, RewardDistribution,
    calculate_proportional_rewards
)
from src.blockchain.transaction import TransactionType


class TestRewardCalculator:
    """Test cases for RewardCalculator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = RewardCalculator()
        
        self.sample_validators = [
            {
                'node_id': 'ai_node_1',
                'model_hash': 'hash1',
                'participation_score': 1.0,
                'validation_count': 10
            },
            {
                'node_id': 'ai_node_2',
                'model_hash': 'hash2',
                'participation_score': 0.95,
                'validation_count': 8
            },
            {
                'node_id': 'ai_node_3',
                'model_hash': 'hash3',
                'participation_score': 1.0,
                'validation_count': 12
            }
        ]
        
        self.sample_stakers = [
            {
                'address': 'staker1',
                'stake_amount': '1000.0',
                'stake_type': 'pool'
            },
            {
                'address': 'staker2',
                'stake_amount': '500.0',
                'stake_type': 'delegated',
                'delegated_node_id': 'ai_node_1'
            },
            {
                'address': 'staker3',
                'stake_amount': '2000.0',
                'stake_type': 'pool'
            }
        ]
    
    def test_reward_calculator_initialization(self):
        """Test reward calculator initialization."""
        assert self.calculator.ai_reward_percentage == Decimal('0.90')
        assert self.calculator.staker_reward_percentage == Decimal('0.10')
    
    def test_calculate_block_rewards(self):
        """Test complete block reward calculation."""
        total_reward = Decimal('100.0')
        
        distribution = self.calculator.calculate_block_rewards(
            block_index=1,
            total_reward=total_reward,
            ai_validators=self.sample_validators,
            stakers=self.sample_stakers
        )
        
        assert distribution.block_index == 1
        assert distribution.total_reward == total_reward
        assert distribution.ai_portion == Decimal('90.0')  # 90% of 100
        assert distribution.staker_portion == Decimal('10.0')  # 10% of 100
        
        # Check AI validator rewards
        assert len(distribution.ai_validator_rewards) == 3
        expected_ai_reward = Decimal('90.0') / 3  # Equal distribution
        for reward in distribution.ai_validator_rewards:
            assert reward.reward_amount == expected_ai_reward
        
        # Check staker rewards
        assert len(distribution.staker_rewards) == 3
        
        # Verify total staker rewards add up to staker portion
        total_staker_rewards = sum(r.reward_amount for r in distribution.staker_rewards)
        assert abs(total_staker_rewards - distribution.staker_portion) < Decimal('0.01')
    
    def test_ai_rewards_equal_distribution(self):
        """Test AI validator rewards are distributed equally."""
        validators = self.sample_validators
        total_ai_reward = Decimal('90.0')
        
        ai_rewards = self.calculator._calculate_ai_rewards(validators, total_ai_reward)
        
        assert len(ai_rewards) == 3
        expected_reward = total_ai_reward / 3
        
        for reward in ai_rewards:
            assert isinstance(reward, AIValidatorReward)
            assert reward.reward_amount == expected_reward
            assert reward.node_id in ['ai_node_1', 'ai_node_2', 'ai_node_3']
    
    def test_ai_rewards_empty_validators(self):
        """Test AI rewards with no validators."""
        ai_rewards = self.calculator._calculate_ai_rewards([], Decimal('90.0'))
        assert ai_rewards == []
    
    def test_staker_rewards_proportional(self):
        """Test staker rewards are proportional to stake amount."""
        stakers = self.sample_stakers
        total_staker_reward = Decimal('10.0')
        
        staker_rewards = self.calculator._calculate_staker_rewards(stakers, total_staker_reward)
        
        assert len(staker_rewards) == 3
        
        # Calculate expected proportions
        total_stake = Decimal('1000.0') + Decimal('500.0') + Decimal('2000.0')  # 3500
        
        expected_rewards = {
            'staker1': (Decimal('1000.0') / total_stake) * total_staker_reward,
            'staker2': (Decimal('500.0') / total_stake) * total_staker_reward,
            'staker3': (Decimal('2000.0') / total_stake) * total_staker_reward
        }
        
        for reward in staker_rewards:
            assert isinstance(reward, StakerReward)
            expected = expected_rewards[reward.staker_address]
            assert abs(reward.reward_amount - expected) < Decimal('0.01')
    
    def test_staker_rewards_empty_stakers(self):
        """Test staker rewards with no stakers."""
        staker_rewards = self.calculator._calculate_staker_rewards([], Decimal('10.0'))
        assert staker_rewards == []
    
    def test_staker_rewards_zero_total_stake(self):
        """Test staker rewards with zero total stake."""
        zero_stakers = [
            {'address': 'staker1', 'stake_amount': '0.0', 'stake_type': 'pool'}
        ]
        
        staker_rewards = self.calculator._calculate_staker_rewards(zero_stakers, Decimal('10.0'))
        assert staker_rewards == []
    
    def test_create_reward_transactions(self):
        """Test creation of reward transactions."""
        distribution = self.calculator.calculate_block_rewards(
            block_index=1,
            total_reward=Decimal('100.0'),
            ai_validators=self.sample_validators,
            stakers=self.sample_stakers
        )
        
        transactions = self.calculator.create_reward_transactions(distribution)
        
        # Should have transactions for all validators and stakers
        expected_count = len(self.sample_validators) + len(self.sample_stakers)
        assert len(transactions) == expected_count
        
        # Check transaction properties
        for tx in transactions:
            assert tx.from_address == "network"
            assert tx.fee == Decimal('0.0')
            assert tx.transaction_type == TransactionType.REWARD
            assert tx.amount > 0
    
    def test_reward_distribution_percentages(self):
        """Test that reward percentages are correctly applied."""
        total_reward = Decimal('1000.0')
        
        distribution = self.calculator.calculate_block_rewards(
            block_index=1,
            total_reward=total_reward,
            ai_validators=self.sample_validators,
            stakers=self.sample_stakers
        )
        
        # Verify percentages
        assert distribution.ai_portion == total_reward * Decimal('0.90')
        assert distribution.staker_portion == total_reward * Decimal('0.10')
        
        # Verify total adds up
        assert distribution.ai_portion + distribution.staker_portion == total_reward


class TestStakeManager:
    """Test cases for StakeManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.stake_manager = StakeManager()
    
    def test_add_stake_pool(self):
        """Test adding a pool stake."""
        success = self.stake_manager.add_stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            stake_type=StakeType.POOL
        )
        
        assert success is True
        assert "staker1" in self.stake_manager.stakes
        
        stake_info = self.stake_manager.get_staker_info("staker1")
        assert stake_info['stake_amount'] == Decimal('1000.0')
        assert stake_info['stake_type'] == 'pool'
        assert stake_info['delegated_node_id'] is None
    
    def test_add_stake_delegated(self):
        """Test adding a delegated stake."""
        success = self.stake_manager.add_stake(
            staker_address="staker2",
            amount=Decimal('500.0'),
            stake_type=StakeType.DELEGATED,
            delegated_node_id="ai_node_1"
        )
        
        assert success is True
        
        stake_info = self.stake_manager.get_staker_info("staker2")
        assert stake_info['stake_amount'] == Decimal('500.0')
        assert stake_info['stake_type'] == 'delegated'
        assert stake_info['delegated_node_id'] == "ai_node_1"
        
        # Check delegation tracking
        delegations = self.stake_manager.get_node_delegations("ai_node_1")
        assert len(delegations) == 1
        assert delegations[0]['address'] == "staker2"
    
    def test_add_invalid_stake(self):
        """Test adding invalid stake (zero or negative amount)."""
        success = self.stake_manager.add_stake(
            staker_address="staker3",
            amount=Decimal('0.0'),
            stake_type=StakeType.POOL
        )
        
        assert success is False
        assert "staker3" not in self.stake_manager.stakes
        
        success = self.stake_manager.add_stake(
            staker_address="staker4",
            amount=Decimal('-100.0'),
            stake_type=StakeType.POOL
        )
        
        assert success is False
        assert "staker4" not in self.stake_manager.stakes
    
    def test_remove_stake(self):
        """Test removing a stake."""
        # Add stake first
        self.stake_manager.add_stake(
            staker_address="staker1",
            amount=Decimal('1000.0'),
            stake_type=StakeType.DELEGATED,
            delegated_node_id="ai_node_1"
        )
        
        # Remove stake
        success = self.stake_manager.remove_stake("staker1")
        assert success is True
        assert "staker1" not in self.stake_manager.stakes
        
        # Check delegation was removed
        delegations = self.stake_manager.get_node_delegations("ai_node_1")
        assert len(delegations) == 0
    
    def test_remove_nonexistent_stake(self):
        """Test removing a stake that doesn't exist."""
        success = self.stake_manager.remove_stake("nonexistent")
        assert success is False
    
    def test_get_all_stakes(self):
        """Test getting all stakes."""
        # Add multiple stakes
        self.stake_manager.add_stake("staker1", Decimal('1000.0'), StakeType.POOL)
        self.stake_manager.add_stake("staker2", Decimal('500.0'), StakeType.DELEGATED, "ai_node_1")
        
        all_stakes = self.stake_manager.get_all_stakes()
        assert len(all_stakes) == 2
        
        addresses = [stake['address'] for stake in all_stakes]
        assert "staker1" in addresses
        assert "staker2" in addresses
    
    def test_get_node_delegations(self):
        """Test getting delegations for a specific node."""
        # Add delegated stakes
        self.stake_manager.add_stake("staker1", Decimal('1000.0'), StakeType.DELEGATED, "ai_node_1")
        self.stake_manager.add_stake("staker2", Decimal('500.0'), StakeType.DELEGATED, "ai_node_1")
        self.stake_manager.add_stake("staker3", Decimal('750.0'), StakeType.DELEGATED, "ai_node_2")
        
        # Check delegations for ai_node_1
        delegations_1 = self.stake_manager.get_node_delegations("ai_node_1")
        assert len(delegations_1) == 2
        
        addresses = [d['address'] for d in delegations_1]
        assert "staker1" in addresses
        assert "staker2" in addresses
        
        # Check delegations for ai_node_2
        delegations_2 = self.stake_manager.get_node_delegations("ai_node_2")
        assert len(delegations_2) == 1
        assert delegations_2[0]['address'] == "staker3"
        
        # Check delegations for non-existent node
        delegations_none = self.stake_manager.get_node_delegations("nonexistent")
        assert len(delegations_none) == 0
    
    def test_get_total_staked(self):
        """Test calculating total staked amount."""
        # Initially zero
        assert self.stake_manager.get_total_staked() == Decimal('0.0')
        
        # Add stakes
        self.stake_manager.add_stake("staker1", Decimal('1000.0'), StakeType.POOL)
        self.stake_manager.add_stake("staker2", Decimal('500.0'), StakeType.DELEGATED, "ai_node_1")
        self.stake_manager.add_stake("staker3", Decimal('750.0'), StakeType.POOL)
        
        total = self.stake_manager.get_total_staked()
        assert total == Decimal('2250.0')  # 1000 + 500 + 750
    
    def test_get_staker_info(self):
        """Test getting specific staker information."""
        # Add stake
        self.stake_manager.add_stake("staker1", Decimal('1000.0'), StakeType.POOL)
        
        # Get info
        info = self.stake_manager.get_staker_info("staker1")
        assert info is not None
        assert info['address'] == "staker1"
        assert info['stake_amount'] == Decimal('1000.0')
        
        # Get info for non-existent staker
        info_none = self.stake_manager.get_staker_info("nonexistent")
        assert info_none is None


class TestProportionalRewards:
    """Test cases for proportional reward calculation."""
    
    def test_calculate_proportional_rewards(self):
        """Test proportional reward calculation."""
        participants = [
            {'address': 'user1', 'amount': '1000.0'},
            {'address': 'user2', 'amount': '500.0'},
            {'address': 'user3', 'amount': '1500.0'}
        ]
        
        total_reward = Decimal('100.0')
        
        results = calculate_proportional_rewards(participants, total_reward, 'amount')
        
        assert len(results) == 3
        
        # Total amount: 3000, so proportions are 1/3, 1/6, 1/2
        expected_rewards = {
            'user1': Decimal('100.0') * (Decimal('1000.0') / Decimal('3000.0')),  # 33.33
            'user2': Decimal('100.0') * (Decimal('500.0') / Decimal('3000.0')),   # 16.67
            'user3': Decimal('100.0') * (Decimal('1500.0') / Decimal('3000.0'))   # 50.00
        }
        
        for result in results:
            address = result['address']
            expected = expected_rewards[address]
            assert abs(result['reward_amount'] - expected) < Decimal('0.01')
    
    def test_proportional_rewards_empty_list(self):
        """Test proportional rewards with empty participant list."""
        results = calculate_proportional_rewards([], Decimal('100.0'))
        assert results == []
    
    def test_proportional_rewards_zero_total_weight(self):
        """Test proportional rewards with zero total weight."""
        participants = [
            {'address': 'user1', 'amount': '0.0'},
            {'address': 'user2', 'amount': '0.0'}
        ]
        
        results = calculate_proportional_rewards(participants, Decimal('100.0'), 'amount')
        
        # Should return original participants without reward_amount
        assert len(results) == 2
        for result in results:
            assert 'reward_amount' not in result or result['reward_amount'] == 0
    
    def test_proportional_rewards_custom_weight_key(self):
        """Test proportional rewards with custom weight key."""
        participants = [
            {'address': 'user1', 'stake': '2000.0'},
            {'address': 'user2', 'stake': '1000.0'}
        ]
        
        results = calculate_proportional_rewards(participants, Decimal('90.0'), 'stake')
        
        # Total stake: 3000, so user1 gets 2/3, user2 gets 1/3
        user1_reward = Decimal('90.0') * (Decimal('2000.0') / Decimal('3000.0'))  # 60.0
        user2_reward = Decimal('90.0') * (Decimal('1000.0') / Decimal('3000.0'))  # 30.0
        
        for result in results:
            if result['address'] == 'user1':
                assert abs(result['reward_amount'] - user1_reward) < Decimal('0.01')
            elif result['address'] == 'user2':
                assert abs(result['reward_amount'] - user2_reward) < Decimal('0.01')