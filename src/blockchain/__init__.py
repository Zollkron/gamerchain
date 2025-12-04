"""
PlayerGold Blockchain Core Module

This module provides the core blockchain functionality for PlayerGold ($PRGLD)
including blocks, transactions, and Merkle tree implementation with PoAIP consensus support.
"""

from .block import Block, ConsensusProof, AIValidatorInfo, create_genesis_block
from .transaction import Transaction, TransactionType, FeeDistribution
from .merkle_tree import MerkleTree, MerkleNode
from .reward_system import (
    RewardCalculator, StakeManager, StakeType,
    AIValidatorReward, StakerReward, RewardDistribution
)
from .fee_system import (
    FeeCalculator, TokenBurnManager, NetworkMetricsTracker,
    NetworkCongestion, NetworkMetrics, BurnRecord, SupplyInfo
)

__all__ = [
    'Block',
    'ConsensusProof', 
    'AIValidatorInfo',
    'create_genesis_block',
    'Transaction',
    'TransactionType',
    'FeeDistribution',
    'MerkleTree',
    'MerkleNode',
    'RewardCalculator',
    'StakeManager',
    'StakeType',
    'AIValidatorReward',
    'StakerReward',
    'RewardDistribution',
    'FeeCalculator',
    'TokenBurnManager',
    'NetworkMetricsTracker',
    'NetworkCongestion',
    'NetworkMetrics',
    'BurnRecord',
    'SupplyInfo'
]