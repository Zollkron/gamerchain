"""
User reputation engine for PlayerGold users.

This module handles reputation tracking for users based on their
token burning behavior and transaction patterns.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from pathlib import Path

from .reputation_types import UserReputationScore, ReputationConfig


class UserReputationEngine:
    """
    Manages reputation for users in the PlayerGold network.
    
    Handles:
    - Reputation scoring based on voluntary token burning
    - Transaction prioritization based on reputation
    - Historical tracking of user behavior
    """
    
    def __init__(self, data_dir: str = "data/reputation"):
        """
        Initialize the user reputation engine.
        
        Args:
            data_dir: Directory to store reputation data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # In-memory reputation data
        self.user_scores: Dict[str, UserReputationScore] = {}
        
        # Load existing data
        self._load_reputation_data()
    
    def _load_reputation_data(self):
        """Load user reputation data from persistent storage."""
        try:
            scores_file = self.data_dir / "user_scores.json"
            
            if scores_file.exists():
                with open(scores_file, 'r') as f:
                    data = json.load(f)
                    for user_id, score_data in data.items():
                        self.user_scores[user_id] = UserReputationScore(
                            user_id=score_data['user_id'],
                            current_score=score_data['current_score'],
                            tokens_burned=Decimal(str(score_data['tokens_burned'])),
                            voluntary_burns=score_data['voluntary_burns'],
                            transaction_count=score_data['transaction_count'],
                            last_activity=datetime.fromisoformat(score_data['last_activity']),
                            priority_level=score_data['priority_level']
                        )
                        
        except Exception as e:
            self.logger.error(f"Error loading user reputation data: {e}")
    
    def _save_reputation_data(self):
        """Save user reputation data to persistent storage."""
        try:
            scores_data = {}
            for user_id, score in self.user_scores.items():
                scores_data[user_id] = {
                    'user_id': score.user_id,
                    'current_score': score.current_score,
                    'tokens_burned': str(score.tokens_burned),
                    'voluntary_burns': score.voluntary_burns,
                    'transaction_count': score.transaction_count,
                    'last_activity': score.last_activity.isoformat(),
                    'priority_level': score.priority_level
                }
            
            with open(self.data_dir / "user_scores.json", 'w') as f:
                json.dump(scores_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving user reputation data: {e}")
    
    def register_user(self, user_id: str) -> UserReputationScore:
        """
        Register a new user with initial reputation.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Initial reputation score for the user
        """
        if user_id not in self.user_scores:
            self.user_scores[user_id] = UserReputationScore(
                user_id=user_id,
                current_score=ReputationConfig.INITIAL_USER_REPUTATION,
                tokens_burned=Decimal('0'),
                voluntary_burns=0,
                transaction_count=0,
                last_activity=datetime.now(),
                priority_level=1
            )
            
            self.logger.info(f"Registered new user: {user_id}")
            self._save_reputation_data()
        
        return self.user_scores[user_id]
    
    def record_voluntary_burn(self, user_id: str, amount: Decimal):
        """
        Record a voluntary token burn by a user.
        
        Args:
            user_id: ID of the user burning tokens
            amount: Amount of tokens burned
        """
        if user_id not in self.user_scores:
            self.register_user(user_id)
        
        score = self.user_scores[user_id]
        
        # Update burn statistics
        score.tokens_burned += amount
        score.voluntary_burns += 1
        score.last_activity = datetime.now()
        
        # Calculate reputation increase
        reputation_increase = float(amount) * ReputationConfig.BURN_REPUTATION_MULTIPLIER
        old_score = score.current_score
        
        score.current_score = min(
            score.current_score + reputation_increase,
            ReputationConfig.MAX_REPUTATION
        )
        
        # Update priority level
        score.priority_level = self._calculate_priority_level(score.current_score)
        
        self.logger.info(f"User {user_id} burned {amount} tokens. "
                        f"Reputation: {old_score} -> {score.current_score}")
        
        self._save_reputation_data()
    
    def record_transaction(self, user_id: str):
        """
        Record a transaction by a user.
        
        Args:
            user_id: ID of the user making the transaction
        """
        if user_id not in self.user_scores:
            self.register_user(user_id)
        
        score = self.user_scores[user_id]
        score.transaction_count += 1
        score.last_activity = datetime.now()
        
        # Save data periodically (every 10 transactions) or immediately for testing
        if score.transaction_count % 10 == 0 or score.transaction_count <= 10:
            self._save_reputation_data()
    
    def get_user_reputation(self, user_id: str) -> Optional[UserReputationScore]:
        """
        Get the current reputation score for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Reputation score or None if user not found
        """
        return self.user_scores.get(user_id)
    
    def get_transaction_priority(self, user_id: str) -> int:
        """
        Get the transaction priority level for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Priority level (1-5, higher is better)
        """
        score = self.get_user_reputation(user_id)
        if not score:
            return 1  # Lowest priority for unknown users
        
        return score.priority_level
    
    def get_priority_multiplier(self, user_id: str) -> float:
        """
        Get the priority multiplier for transaction processing.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Priority multiplier (higher means faster processing)
        """
        priority = self.get_transaction_priority(user_id)
        
        # Priority multipliers: 1=1x, 2=1.5x, 3=2x, 4=3x, 5=5x
        multipliers = {1: 1.0, 2: 1.5, 3: 2.0, 4: 3.0, 5: 5.0}
        return multipliers.get(priority, 1.0)
    
    def is_high_priority_user(self, user_id: str) -> bool:
        """
        Check if a user qualifies for high priority processing.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if user has high priority, False otherwise
        """
        score = self.get_user_reputation(user_id)
        if not score:
            return False
        
        return score.current_score >= ReputationConfig.TRANSACTION_PRIORITY_THRESHOLD
    
    def get_top_users(self, limit: int = 10) -> List[UserReputationScore]:
        """
        Get the top-rated users by reputation score.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of top reputation scores
        """
        sorted_scores = sorted(
            self.user_scores.values(),
            key=lambda x: (x.current_score, x.tokens_burned),
            reverse=True
        )
        return sorted_scores[:limit]
    
    def get_user_stats(self) -> Dict:
        """
        Get overall user reputation statistics.
        
        Returns:
            Dictionary with user reputation metrics
        """
        if not self.user_scores:
            return {
                'total_users': 0,
                'average_reputation': 0.0,
                'high_priority_users': 0,
                'total_burns': '0',
                'total_transactions': 0
            }
        
        scores = list(self.user_scores.values())
        
        return {
            'total_users': len(scores),
            'average_reputation': sum(s.current_score for s in scores) / len(scores),
            'high_priority_users': sum(1 for s in scores if self.is_high_priority_user(s.user_id)),
            'total_burns': str(sum(s.tokens_burned for s in scores)),
            'total_transactions': sum(s.transaction_count for s in scores),
            'average_burn_ratio': sum(s.burn_ratio for s in scores) / len(scores)
        }
    
    def _calculate_priority_level(self, reputation_score: float) -> int:
        """
        Calculate priority level based on reputation score.
        
        Args:
            reputation_score: Current reputation score
            
        Returns:
            Priority level (1-5)
        """
        if reputation_score >= 500:
            return 5  # Highest priority
        elif reputation_score >= 300:
            return 4
        elif reputation_score >= 150:
            return 3
        elif reputation_score >= 75:
            return 2
        else:
            return 1  # Lowest priority
    
    def decay_reputation(self, decay_rate: float = 0.01):
        """
        Apply reputation decay for inactive users.
        
        Args:
            decay_rate: Rate of reputation decay per day of inactivity
        """
        current_time = datetime.now()
        cutoff_date = current_time - timedelta(days=30)  # 30 days of inactivity
        
        for user_id, score in self.user_scores.items():
            if score.last_activity < cutoff_date:
                days_inactive = (current_time - score.last_activity).days
                decay_amount = score.current_score * decay_rate * days_inactive
                
                old_score = score.current_score
                score.current_score = max(
                    score.current_score - decay_amount,
                    ReputationConfig.MIN_REPUTATION
                )
                
                # Update priority level
                score.priority_level = self._calculate_priority_level(score.current_score)
                
                if old_score != score.current_score:
                    self.logger.debug(f"Applied reputation decay to user {user_id}: "
                                    f"{old_score} -> {score.current_score}")
        
        self._save_reputation_data()