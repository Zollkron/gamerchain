"""
Reputation system for PlayerGold distributed AI nodes.

This module implements the reputation tracking and management system
for both AI nodes and users in the GamerChain network.
"""

from .node_reputation import NodeReputationEngine
from .user_reputation import UserReputationEngine
from .reputation_interface import ReputationInterface
from .reputation_types import (
    ReputationEvent,
    PenaltySeverity,
    NodeBehaviorType,
    ReputationScore,
    UserReputationScore
)

__all__ = [
    'NodeReputationEngine',
    'UserReputationEngine',
    'ReputationInterface',
    'ReputationEvent',
    'PenaltySeverity',
    'NodeBehaviorType',
    'ReputationScore',
    'UserReputationScore'
]