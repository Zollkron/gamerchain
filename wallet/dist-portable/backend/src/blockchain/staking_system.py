"""
Staking System for PlayerGold blockchain.
Implements delegated staking with 10% reward distribution and AI node selection.
"""

import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Set
from enum import Enum

from .transaction import Transaction, TransactionType


class StakeStatus(Enum):
    """Status of a stake."""
    ACTIVE = "active"
    PENDING_WITHDRAWAL = "pending_withdrawal"
    WITHDRAWN = "withdrawn"


@dataclass
class Stake:
    """Represents a stake in the system."""
    staker_address: str
    amount: Decimal
    delegated_node_id: str
    timestamp: float
    status: StakeStatus = StakeStatus.ACTIVE
    accumulated_rewards: Decimal = Decimal('0.0')
    last_reward_time: float = field(default_factory=time.time)
    withdrawal_request_time: Optional[float] = None
    
    def calculate_stake_duration(self, current_time: Optional[float] = None) -> float:
        """
        Calculate duration of stake in seconds.
        
        Args:
            current_time: Current timestamp (defaults to now)
            
        Returns:
            float: Duration in seconds
        """
        if current_time is None:
            current_time = time.time()
        return current_time - self.timestamp
    
    def to_dict(self) -> dict:
        """Convert stake to dictionary."""
        return {
            'staker_address': self.staker_address,
            'amount': str(self.amount),
            'delegated_node_id': self.delegated_node_id,
            'timestamp': self.timestamp,
            'status': self.status.value,
            'accumulated_rewards': str(self.accumulated_rewards),
            'last_reward_time': self.last_reward_time,
            'withdrawal_request_time': self.withdrawal_request_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Stake':
        """Create stake from dictionary."""
        return cls(
            staker_address=data['staker_address'],
            amount=Decimal(data['amount']),
            delegated_node_id=data['delegated_node_id'],
            timestamp=data['timestamp'],
            status=StakeStatus(data['status']),
            accumulated_rewards=Decimal(data['accumulated_rewards']),
            last_reward_time=data['last_reward_time'],
            withdrawal_request_time=data.get('withdrawal_request_time')
        )


@dataclass
class AINodeInfo:
    """Information about an AI node available for staking."""
    node_id: str
    model_name: str
    model_hash: str
    reputation_score: float
    total_validations: int
    uptime_percentage: float
    total_delegated: Decimal = Decimal('0.0')
    delegator_count: int = 0
    is_active: bool = True
    
    def to_dict(self) -> dict:
        """Convert node info to dictionary."""
        return {
            'node_id': self.node_id,
            'model_name': self.model_name,
            'model_hash': self.model_hash,
            'reputation_score': self.reputation_score,
            'total_validations': self.total_validations,
            'uptime_percentage': self.uptime_percentage,
            'total_delegated': str(self.total_delegated),
            'delegator_count': self.delegator_count,
            'is_active': self.is_active
        }


class StakingSystem:
    """
    Manages staking operations with delegation to AI nodes.
    Implements 10% reward distribution and automatic reward calculation.
    """
    
    def __init__(self, min_stake_amount: Decimal = Decimal('100.0'),
                 withdrawal_delay_seconds: int = 86400):  # 24 hours
        """
        Initialize staking system.
        
        Args:
            min_stake_amount: Minimum amount required to stake
            withdrawal_delay_seconds: Delay before withdrawal is allowed
        """
        self.min_stake_amount = min_stake_amount
        self.withdrawal_delay_seconds = withdrawal_delay_seconds
        
        # Staking data structures
        self.stakes: Dict[str, Stake] = {}  # staker_address -> Stake
        self.node_delegations: Dict[str, Set[str]] = {}  # node_id -> set of staker addresses
        self.ai_nodes: Dict[str, AINodeInfo] = {}  # node_id -> AINodeInfo
        
        # Reward tracking
        self.total_staked: Decimal = Decimal('0.0')
        self.total_rewards_distributed: Decimal = Decimal('0.0')
    
    def register_ai_node(self, node_info: AINodeInfo) -> bool:
        """
        Register an AI node as available for delegation.
        
        Args:
            node_info: Information about the AI node
            
        Returns:
            bool: True if registration successful
        """
        if node_info.node_id in self.ai_nodes:
            return False
        
        self.ai_nodes[node_info.node_id] = node_info
        self.node_delegations[node_info.node_id] = set()
        return True
    
    def update_ai_node(self, node_id: str, **kwargs) -> bool:
        """
        Update AI node information.
        
        Args:
            node_id: ID of the node to update
            **kwargs: Fields to update
            
        Returns:
            bool: True if update successful
        """
        if node_id not in self.ai_nodes:
            return False
        
        node = self.ai_nodes[node_id]
        for key, value in kwargs.items():
            if hasattr(node, key):
                setattr(node, key, value)
        
        return True
    
    def get_available_nodes(self, min_reputation: float = 0.0) -> List[AINodeInfo]:
        """
        Get list of AI nodes available for delegation.
        
        Args:
            min_reputation: Minimum reputation score filter
            
        Returns:
            List[AINodeInfo]: List of available nodes
        """
        return [
            node for node in self.ai_nodes.values()
            if node.is_active and node.reputation_score >= min_reputation
        ]
    
    def delegate_stake(self, staker_address: str, amount: Decimal,
                      delegated_node_id: str) -> tuple[bool, str]:
        """
        Delegate tokens to an AI node for staking.
        
        Args:
            staker_address: Address of the staker
            amount: Amount to stake
            delegated_node_id: ID of AI node to delegate to
            
        Returns:
            tuple[bool, str]: (Success status, message)
        """
        # Validate amount
        if amount < self.min_stake_amount:
            return False, f"Minimum stake amount is {self.min_stake_amount}"
        
        # Check if node exists and is active
        if delegated_node_id not in self.ai_nodes:
            return False, "AI node not found"
        
        if not self.ai_nodes[delegated_node_id].is_active:
            return False, "AI node is not active"
        
        # Check if staker already has an active stake
        if staker_address in self.stakes:
            existing_stake = self.stakes[staker_address]
            if existing_stake.status == StakeStatus.ACTIVE:
                return False, "Already have an active stake. Unstake first to change delegation."
        
        # Create new stake
        stake = Stake(
            staker_address=staker_address,
            amount=amount,
            delegated_node_id=delegated_node_id,
            timestamp=time.time()
        )
        
        self.stakes[staker_address] = stake
        self.node_delegations[delegated_node_id].add(staker_address)
        
        # Update node stats
        node = self.ai_nodes[delegated_node_id]
        node.total_delegated += amount
        node.delegator_count += 1
        
        # Update total staked
        self.total_staked += amount
        
        return True, f"Successfully delegated {amount} to node {delegated_node_id}"
    
    def request_unstake(self, staker_address: str) -> tuple[bool, str]:
        """
        Request to unstake tokens (initiates withdrawal delay).
        
        Args:
            staker_address: Address of the staker
            
        Returns:
            tuple[bool, str]: (Success status, message)
        """
        if staker_address not in self.stakes:
            return False, "No active stake found"
        
        stake = self.stakes[staker_address]
        
        if stake.status != StakeStatus.ACTIVE:
            return False, f"Stake is not active (status: {stake.status.value})"
        
        # Mark as pending withdrawal
        stake.status = StakeStatus.PENDING_WITHDRAWAL
        stake.withdrawal_request_time = time.time()
        
        return True, f"Withdrawal requested. Available after {self.withdrawal_delay_seconds} seconds"
    
    def complete_unstake(self, staker_address: str) -> tuple[bool, str, Optional[Decimal]]:
        """
        Complete unstaking and return tokens to staker.
        
        Args:
            staker_address: Address of the staker
            
        Returns:
            tuple[bool, str, Optional[Decimal]]: (Success, message, amount to return)
        """
        if staker_address not in self.stakes:
            return False, "No stake found", None
        
        stake = self.stakes[staker_address]
        
        if stake.status != StakeStatus.PENDING_WITHDRAWAL:
            return False, "Withdrawal not requested", None
        
        # Check if withdrawal delay has passed
        current_time = time.time()
        time_since_request = current_time - stake.withdrawal_request_time
        
        if time_since_request < self.withdrawal_delay_seconds:
            remaining = self.withdrawal_delay_seconds - time_since_request
            return False, f"Withdrawal delay not met. {remaining:.0f} seconds remaining", None
        
        # Process withdrawal
        total_return = stake.amount + stake.accumulated_rewards
        
        # Update node stats
        node = self.ai_nodes[stake.delegated_node_id]
        node.total_delegated -= stake.amount
        node.delegator_count -= 1
        
        # Remove from delegations
        self.node_delegations[stake.delegated_node_id].discard(staker_address)
        
        # Update total staked
        self.total_staked -= stake.amount
        
        # Mark as withdrawn
        stake.status = StakeStatus.WITHDRAWN
        
        return True, f"Unstaked successfully. Returning {total_return}", total_return
    
    def calculate_staking_rewards(self, staker_portion: Decimal,
                                  current_time: Optional[float] = None) -> Dict[str, Decimal]:
        """
        Calculate staking rewards for all active stakers (10% of block rewards).
        
        Args:
            staker_portion: Total amount to distribute (10% of block reward)
            current_time: Current timestamp (defaults to now)
            
        Returns:
            Dict[str, Decimal]: Mapping of staker_address to reward amount
        """
        if current_time is None:
            current_time = time.time()
        
        # Get all active stakes
        active_stakes = [
            stake for stake in self.stakes.values()
            if stake.status == StakeStatus.ACTIVE
        ]
        
        if not active_stakes or self.total_staked == 0:
            return {}
        
        rewards = {}
        
        # Calculate proportional rewards based on stake amount and duration
        for stake in active_stakes:
            # Weight by amount and time
            stake_weight = stake.amount
            
            # Calculate proportional reward
            reward = (stake_weight / self.total_staked) * staker_portion
            
            # Update stake
            stake.accumulated_rewards += reward
            stake.last_reward_time = current_time
            
            rewards[stake.staker_address] = reward
        
        self.total_rewards_distributed += staker_portion
        
        return rewards
    
    def get_stake_info(self, staker_address: str) -> Optional[Dict]:
        """
        Get detailed stake information for a staker.
        
        Args:
            staker_address: Address of the staker
            
        Returns:
            Optional[Dict]: Stake information or None
        """
        if staker_address not in self.stakes:
            return None
        
        stake = self.stakes[staker_address]
        node = self.ai_nodes.get(stake.delegated_node_id)
        
        return {
            'stake': stake.to_dict(),
            'node_info': node.to_dict() if node else None,
            'stake_duration_seconds': stake.calculate_stake_duration(),
            'can_withdraw': self._can_withdraw(stake)
        }
    
    def _can_withdraw(self, stake: Stake) -> bool:
        """Check if a stake can be withdrawn."""
        if stake.status != StakeStatus.PENDING_WITHDRAWAL:
            return False
        
        if stake.withdrawal_request_time is None:
            return False
        
        time_since_request = time.time() - stake.withdrawal_request_time
        return time_since_request >= self.withdrawal_delay_seconds
    
    def get_node_delegations_info(self, node_id: str) -> Optional[Dict]:
        """
        Get delegation information for a specific AI node.
        
        Args:
            node_id: ID of the AI node
            
        Returns:
            Optional[Dict]: Delegation information or None
        """
        if node_id not in self.ai_nodes:
            return None
        
        node = self.ai_nodes[node_id]
        delegators = self.node_delegations.get(node_id, set())
        
        delegator_stakes = [
            self.stakes[addr].to_dict()
            for addr in delegators
            if addr in self.stakes and self.stakes[addr].status == StakeStatus.ACTIVE
        ]
        
        return {
            'node_info': node.to_dict(),
            'delegators': delegator_stakes,
            'total_delegated': str(node.total_delegated),
            'delegator_count': node.delegator_count
        }
    
    def get_staking_stats(self) -> Dict:
        """
        Get overall staking statistics.
        
        Returns:
            Dict: Staking statistics
        """
        active_stakes = sum(
            1 for stake in self.stakes.values()
            if stake.status == StakeStatus.ACTIVE
        )
        
        return {
            'total_staked': str(self.total_staked),
            'total_rewards_distributed': str(self.total_rewards_distributed),
            'active_stakes_count': active_stakes,
            'total_stakes_count': len(self.stakes),
            'registered_nodes_count': len(self.ai_nodes),
            'active_nodes_count': sum(1 for node in self.ai_nodes.values() if node.is_active)
        }
    
    def create_stake_transaction(self, staker_address: str, amount: Decimal,
                                 delegated_node_id: str, nonce: int) -> Transaction:
        """
        Create a stake transaction.
        
        Args:
            staker_address: Address of the staker
            amount: Amount to stake
            delegated_node_id: Node to delegate to
            nonce: Transaction nonce
            
        Returns:
            Transaction: Stake transaction
        """
        return Transaction(
            from_address=staker_address,
            to_address=f"stake:{delegated_node_id}",
            amount=amount,
            fee=Decimal('0.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.STAKE,
            nonce=nonce
        )
    
    def create_unstake_transaction(self, staker_address: str, nonce: int) -> Optional[Transaction]:
        """
        Create an unstake transaction.
        
        Args:
            staker_address: Address of the staker
            nonce: Transaction nonce
            
        Returns:
            Optional[Transaction]: Unstake transaction or None
        """
        if staker_address not in self.stakes:
            return None
        
        stake = self.stakes[staker_address]
        total_amount = stake.amount + stake.accumulated_rewards
        
        return Transaction(
            from_address=f"stake:{stake.delegated_node_id}",
            to_address=staker_address,
            amount=total_amount,
            fee=Decimal('0.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.UNSTAKE,
            nonce=nonce
        )
