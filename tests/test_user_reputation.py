"""
Tests for the user reputation engine.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from decimal import Decimal

from src.reputation.user_reputation import UserReputationEngine
from src.reputation.reputation_types import ReputationConfig


class TestUserReputationEngine:
    """Test cases for UserReputationEngine."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def reputation_engine(self, temp_dir):
        """Create a user reputation engine instance for testing."""
        return UserReputationEngine(data_dir=temp_dir)
    
    def test_register_user(self, reputation_engine):
        """Test user registration."""
        user_id = "test_user_1"
        
        # Register new user
        score = reputation_engine.register_user(user_id)
        
        assert score.user_id == user_id
        assert score.current_score == ReputationConfig.INITIAL_USER_REPUTATION
        assert score.tokens_burned == Decimal('0')
        assert score.voluntary_burns == 0
        assert score.transaction_count == 0
        assert score.priority_level == 1
        
        # Registering same user should return existing score
        score2 = reputation_engine.register_user(user_id)
        assert score2 is score
    
    def test_voluntary_burn(self, reputation_engine):
        """Test recording voluntary token burns."""
        user_id = "test_user_1"
        reputation_engine.register_user(user_id)
        
        initial_score = reputation_engine.get_user_reputation(user_id).current_score
        burn_amount = Decimal('10.5')
        
        # Record voluntary burn
        reputation_engine.record_voluntary_burn(user_id, burn_amount)
        
        score = reputation_engine.get_user_reputation(user_id)
        assert score.tokens_burned == burn_amount
        assert score.voluntary_burns == 1
        
        expected_increase = float(burn_amount) * ReputationConfig.BURN_REPUTATION_MULTIPLIER
        expected_score = initial_score + expected_increase
        assert score.current_score == expected_score
        
        # Record multiple burns
        for i in range(3):
            reputation_engine.record_voluntary_burn(user_id, Decimal('5.0'))
        
        score = reputation_engine.get_user_reputation(user_id)
        assert score.tokens_burned == burn_amount + Decimal('15.0')  # 10.5 + 3*5.0
        assert score.voluntary_burns == 4
    
    def test_transaction_recording(self, reputation_engine):
        """Test recording user transactions."""
        user_id = "test_user_1"
        reputation_engine.register_user(user_id)
        
        # Record transactions
        for i in range(5):
            reputation_engine.record_transaction(user_id)
        
        score = reputation_engine.get_user_reputation(user_id)
        assert score.transaction_count == 5
    
    def test_priority_calculation(self, reputation_engine):
        """Test priority level calculation."""
        user_id = "test_user_1"
        reputation_engine.register_user(user_id)
        
        # Initial priority should be 1
        assert reputation_engine.get_transaction_priority(user_id) == 1
        assert reputation_engine.get_priority_multiplier(user_id) == 1.0
        
        # Burn tokens to increase reputation and priority
        reputation_engine.record_voluntary_burn(user_id, Decimal('10.0'))  # +100 reputation
        
        score = reputation_engine.get_user_reputation(user_id)
        assert score.priority_level == 3  # Should be level 3 now (150+ reputation)
        assert reputation_engine.get_transaction_priority(user_id) == 3
        assert reputation_engine.get_priority_multiplier(user_id) == 2.0
        
        # Burn more to reach highest priority
        reputation_engine.record_voluntary_burn(user_id, Decimal('50.0'))  # +500 reputation
        
        score = reputation_engine.get_user_reputation(user_id)
        assert score.priority_level == 5  # Should be max level (500+ reputation)
        assert reputation_engine.get_transaction_priority(user_id) == 5
        assert reputation_engine.get_priority_multiplier(user_id) == 5.0
    
    def test_high_priority_user(self, reputation_engine):
        """Test high priority user detection."""
        user_id = "test_user_1"
        reputation_engine.register_user(user_id)
        
        # Initially not high priority
        assert not reputation_engine.is_high_priority_user(user_id)
        
        # Burn enough tokens to reach high priority threshold
        burn_amount = Decimal(str(ReputationConfig.TRANSACTION_PRIORITY_THRESHOLD / ReputationConfig.BURN_REPUTATION_MULTIPLIER))
        reputation_engine.record_voluntary_burn(user_id, burn_amount)
        
        assert reputation_engine.is_high_priority_user(user_id)
    
    def test_reputation_bounds(self, reputation_engine):
        """Test reputation score bounds."""
        user_id = "test_user_1"
        reputation_engine.register_user(user_id)
        
        # Test maximum bound
        huge_burn = Decimal('1000.0')  # Should hit max reputation
        reputation_engine.record_voluntary_burn(user_id, huge_burn)
        
        score = reputation_engine.get_user_reputation(user_id)
        assert score.current_score <= ReputationConfig.MAX_REPUTATION
    
    def test_burn_ratio_calculation(self, reputation_engine):
        """Test burn ratio calculation."""
        user_id = "test_user_1"
        reputation_engine.register_user(user_id)
        
        # No transactions initially
        score = reputation_engine.get_user_reputation(user_id)
        assert score.burn_ratio == 0.0
        
        # Add transactions and burns
        reputation_engine.record_voluntary_burn(user_id, Decimal('10.0'))
        for _ in range(5):
            reputation_engine.record_transaction(user_id)
        
        score = reputation_engine.get_user_reputation(user_id)
        expected_ratio = float(Decimal('10.0')) / 5
        assert score.burn_ratio == expected_ratio
    
    def test_top_users(self, reputation_engine):
        """Test getting top-rated users."""
        # Register multiple users with different burn amounts
        users = ["user_1", "user_2", "user_3", "user_4"]
        burn_amounts = [Decimal('5.0'), Decimal('15.0'), Decimal('10.0'), Decimal('20.0')]
        
        for user_id, burn_amount in zip(users, burn_amounts):
            reputation_engine.register_user(user_id)
            reputation_engine.record_voluntary_burn(user_id, burn_amount)
        
        top_users = reputation_engine.get_top_users(limit=3)
        assert len(top_users) == 3
        
        # Should be sorted by reputation score (highest first)
        assert top_users[0].user_id == "user_4"  # Burned 20.0 tokens
        assert top_users[1].user_id == "user_2"  # Burned 15.0 tokens
        assert top_users[2].user_id == "user_3"  # Burned 10.0 tokens
    
    def test_user_stats(self, reputation_engine):
        """Test user statistics calculation."""
        # Empty system
        stats = reputation_engine.get_user_stats()
        assert stats['total_users'] == 0
        assert stats['average_reputation'] == 0.0
        
        # Add some users
        users = ["user_1", "user_2", "user_3"]
        for i, user_id in enumerate(users):
            reputation_engine.register_user(user_id)
            reputation_engine.record_voluntary_burn(user_id, Decimal(str(5.0 * (i + 1))))
            for _ in range(i + 1):
                reputation_engine.record_transaction(user_id)
        
        stats = reputation_engine.get_user_stats()
        assert stats['total_users'] == 3
        assert stats['average_reputation'] > ReputationConfig.INITIAL_USER_REPUTATION
        assert Decimal(stats['total_burns']) == Decimal('30.0')  # 5 + 10 + 15
        assert stats['total_transactions'] == 6  # 1 + 2 + 3
        assert stats['average_burn_ratio'] > 0
    
    def test_reputation_decay(self, reputation_engine):
        """Test reputation decay for inactive users."""
        user_id = "test_user_1"
        reputation_engine.register_user(user_id)
        
        # Burn tokens to get high reputation
        reputation_engine.record_voluntary_burn(user_id, Decimal('50.0'))
        initial_score = reputation_engine.get_user_reputation(user_id).current_score
        
        # Simulate old last activity (35 days ago)
        score = reputation_engine.get_user_reputation(user_id)
        score.last_activity = datetime.now() - timedelta(days=35)
        
        # Apply decay
        reputation_engine.decay_reputation(decay_rate=0.01)
        
        # Score should have decreased
        new_score = reputation_engine.get_user_reputation(user_id).current_score
        assert new_score < initial_score
        
        # Priority level should also be updated
        assert score.priority_level <= 5
    
    def test_unknown_user_priority(self, reputation_engine):
        """Test priority for unknown users."""
        # Unknown user should get lowest priority
        assert reputation_engine.get_transaction_priority("unknown_user") == 1
        assert reputation_engine.get_priority_multiplier("unknown_user") == 1.0
        assert not reputation_engine.is_high_priority_user("unknown_user")
    
    def test_persistence(self, temp_dir):
        """Test data persistence across engine restarts."""
        user_id = "test_user_1"
        burn_amount = Decimal('25.5')
        
        # Create engine and add data
        engine1 = UserReputationEngine(data_dir=temp_dir)
        engine1.register_user(user_id)
        engine1.record_voluntary_burn(user_id, burn_amount)
        for _ in range(3):
            engine1.record_transaction(user_id)
        
        original_score = engine1.get_user_reputation(user_id)
        
        # Create new engine instance (simulating restart)
        engine2 = UserReputationEngine(data_dir=temp_dir)
        
        # Data should be loaded
        loaded_score = engine2.get_user_reputation(user_id)
        
        assert loaded_score.user_id == original_score.user_id
        assert loaded_score.current_score == original_score.current_score
        assert loaded_score.tokens_burned == original_score.tokens_burned
        assert loaded_score.voluntary_burns == original_score.voluntary_burns
        assert loaded_score.transaction_count == original_score.transaction_count
        assert loaded_score.priority_level == original_score.priority_level
    
    def test_priority_level_boundaries(self, reputation_engine):
        """Test priority level calculation boundaries."""
        user_id = "test_user_1"
        reputation_engine.register_user(user_id)
        
        # Test each priority level boundary
        test_cases = [
            (Decimal('0.0'), 1),      # 50 reputation (initial) -> level 1
            (Decimal('2.5'), 2),      # 75 reputation -> level 2
            (Decimal('10.0'), 3),     # 150 reputation -> level 3
            (Decimal('25.0'), 4),     # 300 reputation -> level 4
            (Decimal('45.0'), 5),     # 500 reputation -> level 5
        ]
        
        for burn_amount, expected_level in test_cases:
            # Reset user
            reputation_engine.user_scores.pop(user_id, None)
            reputation_engine.register_user(user_id)
            
            if burn_amount > 0:
                reputation_engine.record_voluntary_burn(user_id, burn_amount)
            
            score = reputation_engine.get_user_reputation(user_id)
            assert score.priority_level == expected_level, f"Burn {burn_amount} should give level {expected_level}, got {score.priority_level}"