"""
Reputation interface for wallet and API integration.

This module provides a unified interface for accessing reputation
data from both node and user reputation engines.
"""

import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from .node_reputation import NodeReputationEngine
from .user_reputation import UserReputationEngine
from .reputation_types import (
    ReputationScore,
    UserReputationScore,
    ReputationEvent,
    NodeBehaviorType,
    PenaltySeverity
)


class ReputationInterface:
    """
    Unified interface for reputation system operations.
    
    Provides methods for wallet integration, API endpoints,
    and transaction prioritization.
    """
    
    def __init__(self, data_dir: str = "data/reputation"):
        """
        Initialize the reputation interface.
        
        Args:
            data_dir: Directory to store reputation data
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize reputation engines
        self.node_engine = NodeReputationEngine(data_dir)
        self.user_engine = UserReputationEngine(data_dir)
    
    # User reputation methods for wallet integration
    
    def get_user_reputation_display(self, user_id: str) -> Dict:
        """
        Get user reputation data formatted for wallet display.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with formatted reputation data
        """
        score = self.user_engine.get_user_reputation(user_id)
        if not score:
            # Return default data for new users
            return {
                'reputation_score': 50.0,
                'priority_level': 1,
                'priority_name': 'Standard',
                'tokens_burned': '0.00',
                'voluntary_burns': 0,
                'transaction_count': 0,
                'priority_multiplier': 1.0,
                'next_level_threshold': 75.0,
                'progress_to_next': 0.0,
                'is_high_priority': False
            }
        
        # Calculate progress to next level
        current_score = score.current_score
        next_threshold = self._get_next_level_threshold(score.priority_level)
        progress = 0.0
        
        if next_threshold > 0:
            prev_threshold = self._get_level_threshold(score.priority_level)
            if next_threshold > prev_threshold:
                progress = (current_score - prev_threshold) / (next_threshold - prev_threshold)
                progress = max(0.0, min(1.0, progress))
        
        return {
            'reputation_score': round(current_score, 2),
            'priority_level': score.priority_level,
            'priority_name': self._get_priority_name(score.priority_level),
            'tokens_burned': str(score.tokens_burned),
            'voluntary_burns': score.voluntary_burns,
            'transaction_count': score.transaction_count,
            'priority_multiplier': self.user_engine.get_priority_multiplier(user_id),
            'next_level_threshold': next_threshold,
            'progress_to_next': round(progress, 3),
            'is_high_priority': self.user_engine.is_high_priority_user(user_id),
            'burn_ratio': round(score.burn_ratio, 4),
            'last_activity': score.last_activity.isoformat()
        }
    
    def burn_tokens_for_reputation(self, user_id: str, amount: Decimal) -> Dict:
        """
        Process voluntary token burn and return updated reputation.
        
        Args:
            user_id: ID of the user burning tokens
            amount: Amount of tokens to burn
            
        Returns:
            Updated reputation display data
        """
        if amount <= 0:
            raise ValueError("Burn amount must be positive")
        
        # Record the burn
        self.user_engine.record_voluntary_burn(user_id, amount)
        
        # Return updated reputation data
        return self.get_user_reputation_display(user_id)
    
    def get_transaction_priority_info(self, user_id: str) -> Dict:
        """
        Get transaction priority information for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Priority information for transaction processing
        """
        priority_level = self.user_engine.get_transaction_priority(user_id)
        multiplier = self.user_engine.get_priority_multiplier(user_id)
        is_high_priority = self.user_engine.is_high_priority_user(user_id)
        
        return {
            'priority_level': priority_level,
            'priority_name': self._get_priority_name(priority_level),
            'priority_multiplier': multiplier,
            'is_high_priority': is_high_priority,
            'estimated_processing_time': self._estimate_processing_time(multiplier),
            'queue_position_estimate': self._estimate_queue_position(priority_level)
        }
    
    # Node reputation methods for network monitoring
    
    def get_node_reputation_summary(self, node_id: str) -> Optional[Dict]:
        """
        Get node reputation summary for monitoring.
        
        Args:
            node_id: ID of the AI node
            
        Returns:
            Node reputation summary or None if not found
        """
        score = self.node_engine.get_node_reputation(node_id)
        if not score:
            return None
        
        return {
            'node_id': node_id,
            'reputation_score': round(score.current_score, 2),
            'total_validations': score.total_validations,
            'success_rate': round(score.success_rate, 4),
            'participation_rate': round(score.participation_rate, 4),
            'reliability_score': round(score.reliability_score, 4),
            'penalties_applied': score.penalties_applied,
            'is_eligible': self.node_engine.is_node_eligible(node_id),
            'last_activity': score.last_activity.isoformat()
        }
    
    def get_network_health(self) -> Dict:
        """
        Get overall network health metrics.
        
        Returns:
            Network health statistics
        """
        node_stats = self.node_engine.get_network_stats()
        user_stats = self.user_engine.get_user_stats()
        
        return {
            'nodes': {
                'total_nodes': node_stats['total_nodes'],
                'eligible_nodes': node_stats['eligible_nodes'],
                'average_reputation': round(node_stats['average_reputation'], 2),
                'total_validations': node_stats['total_validations'],
                'average_success_rate': round(node_stats.get('average_success_rate', 0), 4),
                'average_participation': round(node_stats.get('average_participation', 0), 4)
            },
            'users': {
                'total_users': user_stats['total_users'],
                'high_priority_users': user_stats['high_priority_users'],
                'average_reputation': round(user_stats['average_reputation'], 2),
                'total_burns': user_stats['total_burns'],
                'total_transactions': user_stats['total_transactions']
            }
        }
    
    def get_top_performers(self, limit: int = 10) -> Dict:
        """
        Get top performing nodes and users.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            Top performers data
        """
        top_nodes = self.node_engine.get_top_nodes(limit)
        top_users = self.user_engine.get_top_users(limit)
        
        return {
            'top_nodes': [
                {
                    'node_id': score.node_id,
                    'reputation_score': round(score.current_score, 2),
                    'success_rate': round(score.success_rate, 4),
                    'total_validations': score.total_validations
                }
                for score in top_nodes
            ],
            'top_users': [
                {
                    'user_id': score.user_id,
                    'reputation_score': round(score.current_score, 2),
                    'tokens_burned': str(score.tokens_burned),
                    'priority_level': score.priority_level
                }
                for score in top_users
            ]
        }
    
    # Transaction processing integration
    
    def should_prioritize_transaction(self, user_id: str) -> bool:
        """
        Check if a transaction should be prioritized.
        
        Args:
            user_id: ID of the user making the transaction
            
        Returns:
            True if transaction should be prioritized
        """
        return self.user_engine.is_high_priority_user(user_id)
    
    def get_transaction_fee_discount(self, user_id: str) -> float:
        """
        Calculate fee discount based on user reputation.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Fee discount multiplier (0.0 to 1.0, where 1.0 = no discount)
        """
        priority_level = self.user_engine.get_transaction_priority(user_id)
        
        # Higher priority users get fee discounts
        discount_map = {
            1: 1.0,    # No discount
            2: 0.95,   # 5% discount
            3: 0.90,   # 10% discount
            4: 0.85,   # 15% discount
            5: 0.80    # 20% discount
        }
        
        return discount_map.get(priority_level, 1.0)
    
    def record_user_transaction(self, user_id: str):
        """
        Record a transaction for reputation tracking.
        
        Args:
            user_id: ID of the user making the transaction
        """
        self.user_engine.record_transaction(user_id)
    
    # Helper methods
    
    def _get_priority_name(self, priority_level: int) -> str:
        """Get human-readable priority name."""
        names = {
            1: 'Standard',
            2: 'Bronze',
            3: 'Silver',
            4: 'Gold',
            5: 'Platinum'
        }
        return names.get(priority_level, 'Unknown')
    
    def _get_level_threshold(self, priority_level: int) -> float:
        """Get reputation threshold for a priority level."""
        thresholds = {
            1: 0.0,
            2: 75.0,
            3: 150.0,
            4: 300.0,
            5: 500.0
        }
        return thresholds.get(priority_level, 0.0)
    
    def _get_next_level_threshold(self, current_level: int) -> float:
        """Get reputation threshold for next priority level."""
        if current_level >= 5:
            return 0.0  # Already at max level
        
        return self._get_level_threshold(current_level + 1)
    
    def _estimate_processing_time(self, multiplier: float) -> str:
        """Estimate transaction processing time based on priority."""
        base_time = 2.0  # Base processing time in seconds
        estimated_time = base_time / multiplier
        
        if estimated_time < 1.0:
            return "< 1 second"
        elif estimated_time < 60:
            return f"~{int(estimated_time)} seconds"
        else:
            return f"~{int(estimated_time / 60)} minutes"
    
    def _estimate_queue_position(self, priority_level: int) -> str:
        """Estimate queue position based on priority level."""
        positions = {
            1: "Standard queue",
            2: "Priority queue (top 25%)",
            3: "High priority queue (top 15%)",
            4: "Express queue (top 5%)",
            5: "Instant processing"
        }
        return positions.get(priority_level, "Unknown")