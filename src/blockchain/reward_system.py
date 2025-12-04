"""
Reward Distribution System for PlayerGold blockchain.
Implements 90/10 distribution between AI validators and stakers.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Optional
from enum import Enum

from .transaction import Transaction, TransactionType


class StakeType(Enum):
    """Types of staking in PlayerGold."""
    DELEGATED = "delegated"  # Delegated to AI nodes
    POOL = "pool"           # Staking pool


@dataclass
class AIValidatorReward:
    """Reward information for an AI validator."""
    node_id: str
    model_hash: str
    reward_amount: Decimal
    participation_score: float  # 0.0 to 1.0 based on performance
    validation_count: int
    
    
@dataclass
class StakerReward:
    """Reward information for a staker."""
    staker_address: str
    stake_amount: Decimal
    reward_amount: Decimal
    stake_type: StakeType
    delegated_node_id: Optional[str] = None  # For delegated stakes


@dataclass
class RewardDistribution:
    """Complete reward distribution for a block."""
    block_index: int
    total_reward: Decimal
    ai_validator_rewards: List[AIValidatorReward]
    staker_rewards: List[StakerReward]
    ai_portion: Decimal  # 90% of total
    staker_portion: Decimal  # 10% of total
    
    
class RewardCalculator:
    """
    Calculates and distributes rewards according to PlayerGold tokenomics.
    90% to AI validators, 10% to stakers.
    """
    
    def __init__(self):
        self.ai_reward_percentage = Decimal('0.90')  # 90%
        self.staker_reward_percentage = Decimal('0.10')  # 10%
    
    def calculate_block_rewards(
        self,
        block_index: int,
        total_reward: Decimal,
        ai_validators: List[Dict],
        stakers: List[Dict]
    ) -> RewardDistribution:
        """
        Calculate reward distribution for a block.
        
        Args:
            block_index: Index of the block being rewarded
            total_reward: Total reward amount (base + fees)
            ai_validators: List of AI validator participation data
            stakers: List of staker information
            
        Returns:
            RewardDistribution: Complete reward distribution
        """
        # Split total reward
        ai_portion = total_reward * self.ai_reward_percentage
        staker_portion = total_reward * self.staker_reward_percentage
        
        # Calculate AI validator rewards (equal distribution)
        ai_rewards = self._calculate_ai_rewards(ai_validators, ai_portion)
        
        # Calculate staker rewards (proportional to stake)
        staker_rewards = self._calculate_staker_rewards(stakers, staker_portion)
        
        return RewardDistribution(
            block_index=block_index,
            total_reward=total_reward,
            ai_validator_rewards=ai_rewards,
            staker_rewards=staker_rewards,
            ai_portion=ai_portion,
            staker_portion=staker_portion
        )
    
    def _calculate_ai_rewards(
        self,
        validators: List[Dict],
        total_ai_reward: Decimal
    ) -> List[AIValidatorReward]:
        """
        Calculate rewards for AI validators (equal distribution).
        
        Args:
            validators: List of validator participation data
            total_ai_reward: Total amount to distribute to AI validators
            
        Returns:
            List[AIValidatorReward]: Individual validator rewards
        """
        if not validators:
            return []
        
        # Equal distribution among all participating validators
        reward_per_validator = total_ai_reward / len(validators)
        
        ai_rewards = []
        for validator in validators:
            reward = AIValidatorReward(
                node_id=validator['node_id'],
                model_hash=validator['model_hash'],
                reward_amount=reward_per_validator,
                participation_score=validator.get('participation_score', 1.0),
                validation_count=validator.get('validation_count', 1)
            )
            ai_rewards.append(reward)
        
        return ai_rewards
    
    def _calculate_staker_rewards(
        self,
        stakers: List[Dict],
        total_staker_reward: Decimal
    ) -> List[StakerReward]:
        """
        Calculate rewards for stakers (proportional to stake amount).
        
        Args:
            stakers: List of staker information
            total_staker_reward: Total amount to distribute to stakers
            
        Returns:
            List[StakerReward]: Individual staker rewards
        """
        if not stakers:
            return []
        
        # Calculate total stake amount
        total_stake = sum(Decimal(str(staker['stake_amount'])) for staker in stakers)
        
        if total_stake == 0:
            return []
        
        staker_rewards = []
        for staker in stakers:
            stake_amount = Decimal(str(staker['stake_amount']))
            
            # Proportional reward based on stake
            reward_amount = (stake_amount / total_stake) * total_staker_reward
            
            reward = StakerReward(
                staker_address=staker['address'],
                stake_amount=stake_amount,
                reward_amount=reward_amount,
                stake_type=StakeType(staker.get('stake_type', 'pool')),
                delegated_node_id=staker.get('delegated_node_id')
            )
            staker_rewards.append(reward)
        
        return staker_rewards
    
    def create_reward_transactions(
        self,
        distribution: RewardDistribution,
        network_address: str = "network"
    ) -> List[Transaction]:
        """
        Create reward transactions for distribution.
        
        Args:
            distribution: Reward distribution to convert to transactions
            network_address: Address representing the network (source of rewards)
            
        Returns:
            List[Transaction]: Reward transactions
        """
        transactions = []
        current_time = __import__('time').time()
        nonce = 0
        
        # Create transactions for AI validators
        for ai_reward in distribution.ai_validator_rewards:
            tx = Transaction(
                from_address=network_address,
                to_address=ai_reward.node_id,
                amount=ai_reward.reward_amount,
                fee=Decimal('0.0'),  # No fee for reward transactions
                timestamp=current_time,
                transaction_type=TransactionType.REWARD,
                nonce=nonce
            )
            transactions.append(tx)
            nonce += 1
        
        # Create transactions for stakers
        for staker_reward in distribution.staker_rewards:
            tx = Transaction(
                from_address=network_address,
                to_address=staker_reward.staker_address,
                amount=staker_reward.reward_amount,
                fee=Decimal('0.0'),  # No fee for reward transactions
                timestamp=current_time,
                transaction_type=TransactionType.REWARD,
                nonce=nonce
            )
            transactions.append(tx)
            nonce += 1
        
        return transactions


class StakeManager:
    """
    Manages staking operations and stake tracking.
    """
    
    def __init__(self):
        self.stakes: Dict[str, Dict] = {}  # address -> stake info
        self.delegations: Dict[str, List[str]] = {}  # node_id -> list of delegator addresses
    
    def add_stake(
        self,
        staker_address: str,
        amount: Decimal,
        stake_type: StakeType,
        delegated_node_id: Optional[str] = None
    ) -> bool:
        """
        Add or update a stake.
        
        Args:
            staker_address: Address of the staker
            amount: Amount being staked
            stake_type: Type of stake (delegated or pool)
            delegated_node_id: Node ID if delegating to specific AI node
            
        Returns:
            bool: True if stake was added successfully
        """
        if amount <= 0:
            return False
        
        stake_info = {
            'address': staker_address,
            'stake_amount': amount,
            'stake_type': stake_type.value,
            'delegated_node_id': delegated_node_id,
            'timestamp': __import__('time').time()
        }
        
        self.stakes[staker_address] = stake_info
        
        # Track delegation
        if delegated_node_id and stake_type == StakeType.DELEGATED:
            if delegated_node_id not in self.delegations:
                self.delegations[delegated_node_id] = []
            if staker_address not in self.delegations[delegated_node_id]:
                self.delegations[delegated_node_id].append(staker_address)
        
        return True
    
    def remove_stake(self, staker_address: str) -> bool:
        """
        Remove a stake (unstaking).
        
        Args:
            staker_address: Address of the staker
            
        Returns:
            bool: True if stake was removed successfully
        """
        if staker_address not in self.stakes:
            return False
        
        stake_info = self.stakes[staker_address]
        
        # Remove from delegations if applicable
        delegated_node_id = stake_info.get('delegated_node_id')
        if delegated_node_id and delegated_node_id in self.delegations:
            if staker_address in self.delegations[delegated_node_id]:
                self.delegations[delegated_node_id].remove(staker_address)
        
        del self.stakes[staker_address]
        return True
    
    def get_all_stakes(self) -> List[Dict]:
        """
        Get all current stakes.
        
        Returns:
            List[Dict]: List of all stake information
        """
        return list(self.stakes.values())
    
    def get_node_delegations(self, node_id: str) -> List[Dict]:
        """
        Get all delegations to a specific AI node.
        
        Args:
            node_id: ID of the AI node
            
        Returns:
            List[Dict]: List of delegations to the node
        """
        if node_id not in self.delegations:
            return []
        
        delegations = []
        for staker_address in self.delegations[node_id]:
            if staker_address in self.stakes:
                delegations.append(self.stakes[staker_address])
        
        return delegations
    
    def get_total_staked(self) -> Decimal:
        """
        Get total amount staked across all stakers.
        
        Returns:
            Decimal: Total staked amount
        """
        return sum(
            Decimal(str(stake['stake_amount'])) 
            for stake in self.stakes.values()
        )
    
    def get_staker_info(self, staker_address: str) -> Optional[Dict]:
        """
        Get stake information for a specific staker.
        
        Args:
            staker_address: Address of the staker
            
        Returns:
            Optional[Dict]: Stake information or None if not found
        """
        return self.stakes.get(staker_address)


def calculate_proportional_rewards(
    participants: List[Dict],
    total_reward: Decimal,
    weight_key: str = 'amount'
) -> List[Dict]:
    """
    Calculate proportional rewards based on participation weight.
    
    Args:
        participants: List of participant data with weight information
        total_reward: Total reward to distribute
        weight_key: Key in participant dict containing weight value
        
    Returns:
        List[Dict]: Participants with calculated reward amounts
    """
    if not participants:
        return []
    
    # Calculate total weight
    total_weight = sum(
        Decimal(str(participant.get(weight_key, 0))) 
        for participant in participants
    )
    
    if total_weight == 0:
        return participants
    
    # Calculate proportional rewards
    results = []
    for participant in participants:
        weight = Decimal(str(participant.get(weight_key, 0)))
        reward = (weight / total_weight) * total_reward
        
        participant_result = participant.copy()
        participant_result['reward_amount'] = reward
        results.append(participant_result)
    
    return results