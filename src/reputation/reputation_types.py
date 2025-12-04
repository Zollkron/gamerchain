"""
Type definitions for the reputation system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class PenaltySeverity(Enum):
    """Severity levels for reputation penalties."""
    NONE = "none"
    LIGHT = "light"      # Minor delays, network issues
    MODERATE = "moderate"  # Repeated minor issues
    SEVERE = "severe"    # Hash modification, malicious behavior
    CRITICAL = "critical"  # Persistent malicious behavior


class NodeBehaviorType(Enum):
    """Types of node behavior events."""
    SUCCESSFUL_VALIDATION = "successful_validation"
    CHALLENGE_TIMEOUT = "challenge_timeout"
    INVALID_SOLUTION = "invalid_solution"
    HASH_MISMATCH = "hash_mismatch"
    NETWORK_DELAY = "network_delay"
    CROSS_VALIDATION_FAILURE = "cross_validation_failure"
    MALICIOUS_BEHAVIOR = "malicious_behavior"
    NODE_OFFLINE = "node_offline"
    MODEL_CORRUPTION = "model_corruption"


@dataclass
class ReputationEvent:
    """Represents a reputation-affecting event."""
    node_id: str
    event_type: NodeBehaviorType
    timestamp: datetime
    severity: PenaltySeverity
    details: Optional[Dict[str, Any]] = None
    block_height: Optional[int] = None
    
    
@dataclass
class ReputationScore:
    """Represents a node's reputation score and metrics."""
    node_id: str
    current_score: float
    total_validations: int
    successful_validations: int
    failed_validations: int
    penalties_applied: int
    last_activity: datetime
    reputation_history: list
    participation_rate: float
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of validations."""
        if self.total_validations == 0:
            return 0.0
        return self.successful_validations / self.total_validations
    
    @property
    def reliability_score(self) -> float:
        """Calculate reliability based on participation and success rate."""
        return (self.participation_rate * 0.6) + (self.success_rate * 0.4)


@dataclass
class UserReputationScore:
    """Represents a user's reputation score."""
    user_id: str
    current_score: float
    tokens_burned: Decimal
    voluntary_burns: int
    transaction_count: int
    last_activity: datetime
    priority_level: int  # 1-5, higher is better priority
    
    @property
    def burn_ratio(self) -> float:
        """Calculate the ratio of burned tokens to transactions."""
        if self.transaction_count == 0:
            return 0.0
        return float(self.tokens_burned) / self.transaction_count


# Reputation configuration constants
class ReputationConfig:
    """Configuration constants for reputation system."""
    
    # Base reputation scores
    INITIAL_NODE_REPUTATION = 100.0
    INITIAL_USER_REPUTATION = 50.0
    
    # Reputation rewards
    SUCCESSFUL_VALIDATION_REWARD = 1.0
    CROSS_VALIDATION_REWARD = 0.5
    
    # Reputation penalties
    LIGHT_PENALTY = -2.0
    MODERATE_PENALTY = -5.0
    SEVERE_PENALTY = -20.0
    CRITICAL_PENALTY = -50.0
    
    # Reputation bounds
    MIN_REPUTATION = 0.0
    MAX_REPUTATION = 1000.0
    
    # Participation tracking
    PARTICIPATION_WINDOW_HOURS = 24
    MIN_PARTICIPATION_RATE = 0.1  # 10% minimum to avoid penalties
    
    # User reputation
    BURN_REPUTATION_MULTIPLIER = 10.0  # 1 token burned = 10 reputation points
    TRANSACTION_PRIORITY_THRESHOLD = 100.0  # Reputation needed for priority
    
    # History retention
    MAX_HISTORY_ENTRIES = 1000
    HISTORY_CLEANUP_DAYS = 30