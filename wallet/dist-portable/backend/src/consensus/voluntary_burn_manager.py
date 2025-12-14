"""
Voluntary Burn Manager - Manages voluntary token burning and reputation system

This module implements the voluntary token burning system that allows users to
burn tokens to gain reputation and transaction priority after mandatory burning
ends (when burn percentage reaches 0%).
"""

import logging
import time
from decimal import Decimal
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class VoluntaryBurnRecord:
    """Record of a voluntary token burn"""
    user_address: str
    amount: Decimal
    timestamp: float
    transaction_hash: str
    reputation_gained: Decimal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'user_address': self.user_address,
            'amount': str(self.amount),
            'timestamp': self.timestamp,
            'transaction_hash': self.transaction_hash,
            'reputation_gained': str(self.reputation_gained)
        }


@dataclass
class UserReputation:
    """User reputation data"""
    address: str
    total_burned: Decimal
    reputation_score: Decimal
    burn_count: int
    last_burn_timestamp: float
    priority_multiplier: Decimal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'address': self.address,
            'total_burned': str(self.total_burned),
            'reputation_score': str(self.reputation_score),
            'burn_count': self.burn_count,
            'last_burn_timestamp': self.last_burn_timestamp,
            'priority_multiplier': str(self.priority_multiplier)
        }


class VoluntaryBurnManager:
    """
    Manages voluntary token burning and reputation system.
    
    Users can burn tokens voluntarily to gain reputation and transaction priority.
    This is especially useful after mandatory burning ends (burn percentage = 0%).
    """
    
    def __init__(self, 
                 reputation_per_token: Decimal = Decimal('1.0'),
                 max_priority_multiplier: Decimal = Decimal('10.0'),
                 reputation_decay_rate: Decimal = Decimal('0.01')):
        """
        Initialize voluntary burn manager
        
        Args:
            reputation_per_token: Reputation points gained per token burned
            max_priority_multiplier: Maximum transaction priority multiplier
            reputation_decay_rate: Daily reputation decay rate (1% default)
        """
        self.reputation_per_token = reputation_per_token
        self.max_priority_multiplier = max_priority_multiplier
        self.reputation_decay_rate = reputation_decay_rate
        
        # User reputation tracking
        self.user_reputations: Dict[str, UserReputation] = {}
        
        # Burn history
        self.burn_history: List[VoluntaryBurnRecord] = []
        
        # Statistics
        self.total_voluntary_burned = Decimal('0')
        self.total_users_with_reputation = 0
        
        logger.info(f"🔥 VoluntaryBurnManager initialized: "
                   f"{reputation_per_token} reputation per token, "
                   f"max priority: {max_priority_multiplier}x")
    
    def process_voluntary_burn(self, user_address: str, amount: Decimal, transaction_hash: str) -> bool:
        """
        Process a voluntary token burn and update user reputation
        
        Args:
            user_address: Address of the user burning tokens
            amount: Amount of tokens to burn
            transaction_hash: Hash of the burn transaction
            
        Returns:
            bool: True if burn was processed successfully
        """
        if amount <= Decimal('0'):
            logger.warning(f"❌ Invalid burn amount: {amount}")
            return False
        
        timestamp = time.time()
        
        # Calculate reputation gained
        reputation_gained = amount * self.reputation_per_token
        
        # Get or create user reputation
        if user_address not in self.user_reputations:
            self.user_reputations[user_address] = UserReputation(
                address=user_address,
                total_burned=Decimal('0'),
                reputation_score=Decimal('0'),
                burn_count=0,
                last_burn_timestamp=0.0,
                priority_multiplier=Decimal('1.0')
            )
            self.total_users_with_reputation += 1
        
        user_rep = self.user_reputations[user_address]
        
        # Apply reputation decay since last burn
        self._apply_reputation_decay(user_rep, timestamp)
        
        # Update user reputation
        user_rep.total_burned += amount
        user_rep.reputation_score += reputation_gained
        user_rep.burn_count += 1
        user_rep.last_burn_timestamp = timestamp
        
        # Calculate new priority multiplier
        user_rep.priority_multiplier = self._calculate_priority_multiplier(user_rep.reputation_score)
        
        # Record the burn
        burn_record = VoluntaryBurnRecord(
            user_address=user_address,
            amount=amount,
            timestamp=timestamp,
            transaction_hash=transaction_hash,
            reputation_gained=reputation_gained
        )
        
        self.burn_history.append(burn_record)
        self.total_voluntary_burned += amount
        
        logger.info(f"🔥 Voluntary burn processed: {amount} PRGLD by {user_address}")
        logger.info(f"📈 Reputation gained: {reputation_gained}, "
                   f"Total reputation: {user_rep.reputation_score}, "
                   f"Priority: {user_rep.priority_multiplier}x")
        
        return True
    
    def _apply_reputation_decay(self, user_rep: UserReputation, current_timestamp: float):
        """Apply reputation decay based on time elapsed"""
        if user_rep.last_burn_timestamp == 0:
            return  # No previous burns
        
        days_elapsed = (current_timestamp - user_rep.last_burn_timestamp) / (24 * 60 * 60)
        if days_elapsed <= 0:
            return  # No time elapsed
        
        # Apply exponential decay
        decay_factor = (Decimal('1') - self.reputation_decay_rate) ** int(days_elapsed)
        old_reputation = user_rep.reputation_score
        user_rep.reputation_score *= decay_factor
        
        # Recalculate priority multiplier
        user_rep.priority_multiplier = self._calculate_priority_multiplier(user_rep.reputation_score)
        
        if old_reputation != user_rep.reputation_score:
            logger.debug(f"📉 Reputation decay applied to {user_rep.address}: "
                        f"{old_reputation} → {user_rep.reputation_score} "
                        f"({days_elapsed:.1f} days)")
    
    def _calculate_priority_multiplier(self, reputation_score: Decimal) -> Decimal:
        """Calculate transaction priority multiplier based on reputation"""
        if reputation_score <= Decimal('0'):
            return Decimal('1.0')
        
        # Logarithmic scaling: multiplier = 1 + log10(reputation + 1)
        # Capped at max_priority_multiplier
        import math
        
        try:
            log_value = math.log10(float(reputation_score) + 1)
            multiplier = Decimal('1.0') + Decimal(str(log_value))
            return min(multiplier, self.max_priority_multiplier)
        except (ValueError, OverflowError):
            return Decimal('1.0')
    
    def get_user_reputation(self, user_address: str) -> Optional[UserReputation]:
        """Get user reputation data"""
        if user_address not in self.user_reputations:
            return None
        
        user_rep = self.user_reputations[user_address]
        
        # Apply decay before returning
        self._apply_reputation_decay(user_rep, time.time())
        
        return user_rep
    
    def get_transaction_priority(self, user_address: str) -> Decimal:
        """Get transaction priority multiplier for a user"""
        user_rep = self.get_user_reputation(user_address)
        if user_rep:
            return user_rep.priority_multiplier
        else:
            return Decimal('1.0')  # Default priority
    
    def get_top_burners(self, limit: int = 10) -> List[UserReputation]:
        """Get top users by total burned tokens"""
        # Update all reputations with decay
        current_time = time.time()
        for user_rep in self.user_reputations.values():
            self._apply_reputation_decay(user_rep, current_time)
        
        # Sort by total burned (descending)
        sorted_users = sorted(
            self.user_reputations.values(),
            key=lambda x: x.total_burned,
            reverse=True
        )
        
        return sorted_users[:limit]
    
    def get_top_reputation(self, limit: int = 10) -> List[UserReputation]:
        """Get top users by current reputation score"""
        # Update all reputations with decay
        current_time = time.time()
        for user_rep in self.user_reputations.values():
            self._apply_reputation_decay(user_rep, current_time)
        
        # Sort by reputation score (descending)
        sorted_users = sorted(
            self.user_reputations.values(),
            key=lambda x: x.reputation_score,
            reverse=True
        )
        
        return sorted_users[:limit]
    
    def get_burn_history(self, user_address: Optional[str] = None, limit: int = 100) -> List[VoluntaryBurnRecord]:
        """Get burn history, optionally filtered by user"""
        if user_address:
            filtered_history = [
                record for record in self.burn_history
                if record.user_address == user_address
            ]
            return filtered_history[-limit:]  # Most recent
        else:
            return self.burn_history[-limit:]  # Most recent
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall burn statistics"""
        current_time = time.time()
        
        # Update all reputations with decay
        for user_rep in self.user_reputations.values():
            self._apply_reputation_decay(user_rep, current_time)
        
        total_reputation = sum(
            user_rep.reputation_score for user_rep in self.user_reputations.values()
        )
        
        avg_reputation = (
            total_reputation / len(self.user_reputations)
            if self.user_reputations else Decimal('0')
        )
        
        return {
            'total_voluntary_burned': str(self.total_voluntary_burned),
            'total_users_with_reputation': len(self.user_reputations),
            'total_burn_transactions': len(self.burn_history),
            'total_reputation_points': str(total_reputation),
            'average_reputation': str(avg_reputation),
            'reputation_per_token': str(self.reputation_per_token),
            'max_priority_multiplier': str(self.max_priority_multiplier)
        }
    
    def serialize_state(self) -> Dict[str, Any]:
        """Serialize state for persistence"""
        return {
            'config': {
                'reputation_per_token': str(self.reputation_per_token),
                'max_priority_multiplier': str(self.max_priority_multiplier),
                'reputation_decay_rate': str(self.reputation_decay_rate)
            },
            'user_reputations': {
                address: user_rep.to_dict()
                for address, user_rep in self.user_reputations.items()
            },
            'burn_history': [record.to_dict() for record in self.burn_history],
            'statistics': {
                'total_voluntary_burned': str(self.total_voluntary_burned),
                'total_users_with_reputation': self.total_users_with_reputation
            },
            'version': '1.0'
        }
    
    def deserialize_state(self, state_data: Dict[str, Any]) -> bool:
        """Deserialize state from persistence data"""
        try:
            # Restore configuration
            config = state_data['config']
            self.reputation_per_token = Decimal(config['reputation_per_token'])
            self.max_priority_multiplier = Decimal(config['max_priority_multiplier'])
            self.reputation_decay_rate = Decimal(config['reputation_decay_rate'])
            
            # Restore user reputations
            self.user_reputations.clear()
            for address, rep_data in state_data['user_reputations'].items():
                user_rep = UserReputation(
                    address=rep_data['address'],
                    total_burned=Decimal(rep_data['total_burned']),
                    reputation_score=Decimal(rep_data['reputation_score']),
                    burn_count=rep_data['burn_count'],
                    last_burn_timestamp=rep_data['last_burn_timestamp'],
                    priority_multiplier=Decimal(rep_data['priority_multiplier'])
                )
                self.user_reputations[address] = user_rep
            
            # Restore burn history
            self.burn_history.clear()
            for record_data in state_data['burn_history']:
                burn_record = VoluntaryBurnRecord(
                    user_address=record_data['user_address'],
                    amount=Decimal(record_data['amount']),
                    timestamp=record_data['timestamp'],
                    transaction_hash=record_data['transaction_hash'],
                    reputation_gained=Decimal(record_data['reputation_gained'])
                )
                self.burn_history.append(burn_record)
            
            # Restore statistics
            stats = state_data['statistics']
            self.total_voluntary_burned = Decimal(stats['total_voluntary_burned'])
            self.total_users_with_reputation = stats['total_users_with_reputation']
            
            logger.info(f"✅ Voluntary burn state restored: "
                       f"{len(self.user_reputations)} users, "
                       f"{len(self.burn_history)} burns, "
                       f"{self.total_voluntary_burned} PRGLD burned")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to deserialize voluntary burn state: {e}")
            return False
    def get_monitoring_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring data for voluntary burns"""
        current_time = time.time()
        
        # Update all reputations with decay
        for user_rep in self.user_reputations.values():
            self._apply_reputation_decay(user_rep, current_time)
        
        # Calculate statistics
        total_reputation = sum(
            user_rep.reputation_score for user_rep in self.user_reputations.values()
        )
        
        avg_reputation = (
            total_reputation / len(self.user_reputations)
            if self.user_reputations else Decimal('0')
        )
        
        # Get top users
        top_burners = self.get_top_burners(5)
        top_reputation = self.get_top_reputation(5)
        
        # Recent activity
        recent_burns = self.burn_history[-10:] if len(self.burn_history) > 10 else self.burn_history
        
        return {
            'overview': {
                'total_voluntary_burned': str(self.total_voluntary_burned),
                'total_users': len(self.user_reputations),
                'total_burn_transactions': len(self.burn_history),
                'average_reputation': str(avg_reputation),
                'total_reputation_points': str(total_reputation)
            },
            'configuration': {
                'reputation_per_token': str(self.reputation_per_token),
                'max_priority_multiplier': str(self.max_priority_multiplier),
                'reputation_decay_rate': str(self.reputation_decay_rate)
            },
            'leaderboards': {
                'top_burners': [
                    {
                        'address': user.address,
                        'total_burned': str(user.total_burned),
                        'burn_count': user.burn_count,
                        'priority_multiplier': str(user.priority_multiplier)
                    }
                    for user in top_burners
                ],
                'top_reputation': [
                    {
                        'address': user.address,
                        'reputation_score': str(user.reputation_score),
                        'priority_multiplier': str(user.priority_multiplier),
                        'last_burn': user.last_burn_timestamp
                    }
                    for user in top_reputation
                ]
            },
            'recent_activity': [
                {
                    'user_address': record.user_address,
                    'amount': str(record.amount),
                    'timestamp': record.timestamp,
                    'reputation_gained': str(record.reputation_gained)
                }
                for record in recent_burns
            ],
            'timestamp': current_time
        }
    
    def get_user_analytics(self, user_address: str) -> Optional[Dict[str, Any]]:
        """Get detailed analytics for a specific user"""
        user_rep = self.get_user_reputation(user_address)
        if not user_rep:
            return None
        
        # Get user's burn history
        user_burns = self.get_burn_history(user_address)
        
        # Calculate burn frequency
        if len(user_burns) > 1:
            time_span = user_burns[-1].timestamp - user_burns[0].timestamp
            burn_frequency = len(user_burns) / (time_span / (24 * 60 * 60))  # Burns per day
        else:
            burn_frequency = 0
        
        # Calculate average burn amount
        avg_burn = (
            sum(record.amount for record in user_burns) / len(user_burns)
            if user_burns else Decimal('0')
        )
        
        return {
            'user_address': user_address,
            'reputation_data': user_rep.to_dict(),
            'burn_statistics': {
                'total_burns': len(user_burns),
                'average_burn_amount': str(avg_burn),
                'burn_frequency_per_day': burn_frequency,
                'first_burn': user_burns[0].timestamp if user_burns else None,
                'last_burn': user_burns[-1].timestamp if user_burns else None
            },
            'burn_history': [record.to_dict() for record in user_burns],
            'ranking': {
                'by_total_burned': self._get_user_rank_by_total_burned(user_address),
                'by_reputation': self._get_user_rank_by_reputation(user_address)
            }
        }
    
    def _get_user_rank_by_total_burned(self, user_address: str) -> int:
        """Get user's rank by total burned tokens"""
        sorted_users = sorted(
            self.user_reputations.values(),
            key=lambda x: x.total_burned,
            reverse=True
        )
        
        for i, user in enumerate(sorted_users):
            if user.address == user_address:
                return i + 1
        
        return -1  # User not found
    
    def _get_user_rank_by_reputation(self, user_address: str) -> int:
        """Get user's rank by current reputation score"""
        # Update all reputations with decay
        current_time = time.time()
        for user_rep in self.user_reputations.values():
            self._apply_reputation_decay(user_rep, current_time)
        
        sorted_users = sorted(
            self.user_reputations.values(),
            key=lambda x: x.reputation_score,
            reverse=True
        )
        
        for i, user in enumerate(sorted_users):
            if user.address == user_address:
                return i + 1
        
        return -1  # User not found