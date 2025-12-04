"""
Tests for the node reputation engine.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from src.reputation.node_reputation import NodeReputationEngine
from src.reputation.reputation_types import (
    NodeBehaviorType,
    PenaltySeverity,
    ReputationConfig
)


class TestNodeReputationEngine:
    """Test cases for NodeReputationEngine."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def reputation_engine(self, temp_dir):
        """Create a reputation engine instance for testing."""
        return NodeReputationEngine(data_dir=temp_dir)
    
    def test_register_node(self, reputation_engine):
        """Test node registration."""
        node_id = "test_node_1"
        
        # Register new node
        score = reputation_engine.register_node(node_id)
        
        assert score.node_id == node_id
        assert score.current_score == ReputationConfig.INITIAL_NODE_REPUTATION
        assert score.total_validations == 0
        assert score.successful_validations == 0
        assert score.failed_validations == 0
        assert score.penalties_applied == 0
        assert score.participation_rate == 1.0
        
        # Registering same node should return existing score
        score2 = reputation_engine.register_node(node_id)
        assert score2 is score
    
    def test_successful_validation(self, reputation_engine):
        """Test recording successful validations."""
        node_id = "test_node_1"
        reputation_engine.register_node(node_id)
        
        initial_score = reputation_engine.get_node_reputation(node_id).current_score
        
        # Record successful validation
        reputation_engine.record_successful_validation(node_id, block_height=100)
        
        score = reputation_engine.get_node_reputation(node_id)
        assert score.total_validations == 1
        assert score.successful_validations == 1
        assert score.failed_validations == 0
        assert score.current_score == initial_score + ReputationConfig.SUCCESSFUL_VALIDATION_REWARD
        
        # Record multiple validations
        for i in range(5):
            reputation_engine.record_successful_validation(node_id, block_height=101 + i)
        
        score = reputation_engine.get_node_reputation(node_id)
        assert score.total_validations == 6
        assert score.successful_validations == 6
        assert score.success_rate == 1.0
    
    def test_apply_penalties(self, reputation_engine):
        """Test applying various penalties."""
        node_id = "test_node_1"
        reputation_engine.register_node(node_id)
        
        initial_score = reputation_engine.get_node_reputation(node_id).current_score
        
        # Apply light penalty
        reputation_engine.apply_penalty(
            node_id,
            NodeBehaviorType.NETWORK_DELAY,
            PenaltySeverity.LIGHT,
            {"delay_ms": 150}
        )
        
        score = reputation_engine.get_node_reputation(node_id)
        expected_score = initial_score + ReputationConfig.LIGHT_PENALTY
        assert score.current_score == expected_score
        assert score.penalties_applied == 1
        
        # Apply severe penalty
        reputation_engine.apply_penalty(
            node_id,
            NodeBehaviorType.HASH_MISMATCH,
            PenaltySeverity.SEVERE,
            {"expected_hash": "abc123", "actual_hash": "def456"}
        )
        
        score = reputation_engine.get_node_reputation(node_id)
        expected_score += ReputationConfig.SEVERE_PENALTY
        assert score.current_score == expected_score
        assert score.penalties_applied == 2
    
    def test_validation_failure_penalties(self, reputation_engine):
        """Test penalties that affect validation counts."""
        node_id = "test_node_1"
        reputation_engine.register_node(node_id)
        
        # Apply validation-related penalty
        reputation_engine.apply_penalty(
            node_id,
            NodeBehaviorType.INVALID_SOLUTION,
            PenaltySeverity.MODERATE
        )
        
        score = reputation_engine.get_node_reputation(node_id)
        assert score.total_validations == 1
        assert score.successful_validations == 0
        assert score.failed_validations == 1
        assert score.success_rate == 0.0
    
    def test_participation_rate_update(self, reputation_engine):
        """Test participation rate updates and penalties."""
        node_id = "test_node_1"
        reputation_engine.register_node(node_id)
        
        initial_penalties = reputation_engine.get_node_reputation(node_id).penalties_applied
        
        # Update to good participation rate
        reputation_engine.update_participation_rate(node_id, 0.8)
        score = reputation_engine.get_node_reputation(node_id)
        assert score.participation_rate == 0.8
        assert score.penalties_applied == initial_penalties
        
        # Update to low participation rate (should trigger penalty)
        reputation_engine.update_participation_rate(node_id, 0.05)
        score = reputation_engine.get_node_reputation(node_id)
        assert score.participation_rate == 0.05
        assert score.penalties_applied == initial_penalties + 1
    
    def test_node_eligibility(self, reputation_engine):
        """Test node eligibility for consensus participation."""
        node_id = "test_node_1"
        reputation_engine.register_node(node_id)
        
        # Initially eligible
        assert reputation_engine.is_node_eligible(node_id)
        
        # Apply severe penalties to make ineligible
        for _ in range(5):
            reputation_engine.apply_penalty(
                node_id,
                NodeBehaviorType.MALICIOUS_BEHAVIOR,
                PenaltySeverity.SEVERE
            )
        
        assert not reputation_engine.is_node_eligible(node_id)
        
        # Low participation should also make ineligible
        reputation_engine.register_node("test_node_2")
        reputation_engine.update_participation_rate("test_node_2", 0.05)
        assert not reputation_engine.is_node_eligible("test_node_2")
    
    def test_reputation_bounds(self, reputation_engine):
        """Test reputation score bounds."""
        node_id = "test_node_1"
        reputation_engine.register_node(node_id)
        
        # Test maximum bound
        for _ in range(1000):
            reputation_engine.record_successful_validation(node_id)
        
        score = reputation_engine.get_node_reputation(node_id)
        assert score.current_score <= ReputationConfig.MAX_REPUTATION
        
        # Test minimum bound
        reputation_engine.register_node("test_node_2")
        for _ in range(100):
            reputation_engine.apply_penalty(
                "test_node_2",
                NodeBehaviorType.MALICIOUS_BEHAVIOR,
                PenaltySeverity.CRITICAL
            )
        
        score2 = reputation_engine.get_node_reputation("test_node_2")
        assert score2.current_score >= ReputationConfig.MIN_REPUTATION
    
    def test_reputation_history(self, reputation_engine):
        """Test reputation history tracking."""
        node_id = "test_node_1"
        reputation_engine.register_node(node_id)
        
        # Perform some actions
        reputation_engine.record_successful_validation(node_id)
        reputation_engine.apply_penalty(
            node_id,
            NodeBehaviorType.NETWORK_DELAY,
            PenaltySeverity.LIGHT
        )
        
        score = reputation_engine.get_node_reputation(node_id)
        assert len(score.reputation_history) == 2
        
        # Check history entries
        history = score.reputation_history
        assert history[0]['reason'] == 'successful_validation'
        assert history[1]['reason'] == 'penalty_light'
        assert history[0]['change'] > 0  # Positive change for validation
        assert history[1]['change'] < 0  # Negative change for penalty
    
    def test_event_history(self, reputation_engine):
        """Test reputation event history."""
        node_id = "test_node_1"
        reputation_engine.register_node(node_id)
        
        # Record some events
        reputation_engine.record_successful_validation(node_id, block_height=100)
        reputation_engine.apply_penalty(
            node_id,
            NodeBehaviorType.CHALLENGE_TIMEOUT,
            PenaltySeverity.MODERATE,
            {"timeout_ms": 150},
            block_height=101
        )
        
        events = reputation_engine.get_node_history(node_id)
        assert len(events) == 2
        
        # Events should be sorted by timestamp (newest first)
        assert events[0].event_type == NodeBehaviorType.CHALLENGE_TIMEOUT
        assert events[1].event_type == NodeBehaviorType.SUCCESSFUL_VALIDATION
        
        # Check event details
        assert events[0].severity == PenaltySeverity.MODERATE
        assert events[0].details["timeout_ms"] == 150
        assert events[0].block_height == 101
    
    def test_top_nodes(self, reputation_engine):
        """Test getting top-rated nodes."""
        # Register multiple nodes with different scores
        nodes = ["node_1", "node_2", "node_3", "node_4"]
        for node_id in nodes:
            reputation_engine.register_node(node_id)
        
        # Give different validation counts
        for _ in range(10):
            reputation_engine.record_successful_validation("node_1")
        for _ in range(5):
            reputation_engine.record_successful_validation("node_2")
        for _ in range(15):
            reputation_engine.record_successful_validation("node_3")
        
        # Apply penalty to node_4
        reputation_engine.apply_penalty(
            "node_4",
            NodeBehaviorType.MALICIOUS_BEHAVIOR,
            PenaltySeverity.SEVERE
        )
        
        top_nodes = reputation_engine.get_top_nodes(limit=3)
        assert len(top_nodes) == 3
        
        # Should be sorted by reputation score
        assert top_nodes[0].node_id == "node_3"  # Highest score
        assert top_nodes[1].node_id == "node_1"
        assert top_nodes[2].node_id == "node_2"
    
    def test_network_stats(self, reputation_engine):
        """Test network statistics calculation."""
        # Empty network
        stats = reputation_engine.get_network_stats()
        assert stats['total_nodes'] == 0
        assert stats['average_reputation'] == 0.0
        
        # Add some nodes
        nodes = ["node_1", "node_2", "node_3"]
        for node_id in nodes:
            reputation_engine.register_node(node_id)
            reputation_engine.record_successful_validation(node_id)
        
        # Apply penalty to one node
        reputation_engine.apply_penalty(
            "node_2",
            NodeBehaviorType.NETWORK_DELAY,
            PenaltySeverity.LIGHT
        )
        
        stats = reputation_engine.get_network_stats()
        assert stats['total_nodes'] == 3
        assert stats['eligible_nodes'] == 3  # All should still be eligible
        assert stats['total_validations'] == 3  # 3 successful, network_delay doesn't count as validation
        assert stats['average_reputation'] > 0
        assert stats['average_success_rate'] > 0
        assert stats['average_participation'] == 1.0
    
    def test_persistence(self, temp_dir):
        """Test data persistence across engine restarts."""
        node_id = "test_node_1"
        
        # Create engine and add data
        engine1 = NodeReputationEngine(data_dir=temp_dir)
        engine1.register_node(node_id)
        engine1.record_successful_validation(node_id)
        engine1.apply_penalty(
            node_id,
            NodeBehaviorType.NETWORK_DELAY,
            PenaltySeverity.LIGHT
        )
        
        original_score = engine1.get_node_reputation(node_id)
        original_events = engine1.get_node_history(node_id)
        
        # Create new engine instance (simulating restart)
        engine2 = NodeReputationEngine(data_dir=temp_dir)
        
        # Data should be loaded
        loaded_score = engine2.get_node_reputation(node_id)
        loaded_events = engine2.get_node_history(node_id)
        
        assert loaded_score.node_id == original_score.node_id
        assert loaded_score.current_score == original_score.current_score
        assert loaded_score.total_validations == original_score.total_validations
        assert loaded_score.successful_validations == original_score.successful_validations
        assert loaded_score.penalties_applied == original_score.penalties_applied
        
        assert len(loaded_events) == len(original_events)
        assert loaded_events[0].event_type == original_events[0].event_type