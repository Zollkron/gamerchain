"""
Block structure for PlayerGold blockchain with PoAIP consensus support.
Includes AI validator tracking and consensus proof integration.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from decimal import Decimal

from .transaction import Transaction
from .merkle_tree import MerkleTree


@dataclass
class ConsensusProof:
    """
    Proof of AI Participation (PoAIP) consensus data.
    Contains challenge and validation information from AI nodes.
    """
    challenge_id: str
    challenge_data: Dict[str, Any]
    solutions: List[Dict[str, Any]]  # AI solutions with signatures
    cross_validations: List[Dict[str, Any]]  # Cross-validation results
    consensus_timestamp: float
    
    def to_dict(self) -> dict:
        """Convert consensus proof to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConsensusProof':
        """Create consensus proof from dictionary."""
        return cls(**data)


@dataclass
class AIValidatorInfo:
    """Information about AI validators that participated in block validation."""
    node_id: str
    model_hash: str
    validation_signature: str
    response_time_ms: int
    reputation_score: float


@dataclass
class Block:
    """
    Block structure for PlayerGold blockchain with PoAIP consensus.
    Tracks AI validators and includes consensus proof.
    """
    index: int
    previous_hash: str
    timestamp: float
    transactions: List[Transaction]
    merkle_root: str
    ai_validators: List[AIValidatorInfo]
    consensus_proof: ConsensusProof
    nonce: int = 0
    hash: Optional[str] = None
    
    def __post_init__(self):
        """Initialize block hash and merkle root after creation."""
        # Always calculate merkle root if not provided
        if not self.merkle_root:
            self.merkle_root = self._calculate_merkle_root()
        
        if self.hash is None:
            self.hash = self.calculate_hash()
    
    def _calculate_merkle_root(self) -> str:
        """
        Calculate Merkle root of transactions in block.
        
        Returns:
            str: Merkle root hash
        """
        if not self.transactions:
            return hashlib.sha256(b'').hexdigest()
        
        transaction_hashes = [tx.hash for tx in self.transactions]
        merkle_tree = MerkleTree(transaction_hashes)
        return merkle_tree.get_root_hash()
    
    def calculate_hash(self) -> str:
        """
        Calculate SHA-256 hash of block header.
        
        Returns:
            str: Block hash as hexadecimal string
        """
        # Create block header data for hashing
        header_data = {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'merkle_root': self.merkle_root,
            'ai_validators': [
                {
                    'node_id': validator.node_id,
                    'model_hash': validator.model_hash,
                    'validation_signature': validator.validation_signature
                }
                for validator in self.ai_validators
            ],
            'consensus_proof': {
                'challenge_id': self.consensus_proof.challenge_id,
                'consensus_timestamp': self.consensus_proof.consensus_timestamp
            },
            'nonce': self.nonce
        }
        
        header_string = json.dumps(header_data, sort_keys=True)
        return hashlib.sha256(header_string.encode()).hexdigest()
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a transaction to the block.
        
        Args:
            transaction: Transaction to add
            
        Returns:
            bool: True if transaction was added successfully
        """
        if not transaction.is_valid():
            return False
        
        # Check for duplicate transactions
        for existing_tx in self.transactions:
            if existing_tx.hash == transaction.hash:
                return False
        
        self.transactions.append(transaction)
        
        # Recalculate merkle root and block hash
        self.merkle_root = self._calculate_merkle_root()
        self.hash = self.calculate_hash()
        
        return True
    
    def get_total_fees(self) -> Decimal:
        """
        Calculate total fees collected in this block.
        
        Returns:
            Decimal: Total fee amount
        """
        return sum(tx.fee for tx in self.transactions)
    
    def get_total_rewards(self) -> Decimal:
        """
        Calculate total rewards for this block (fees + block reward).
        
        Returns:
            Decimal: Total reward amount
        """
        # Base block reward (this could be configurable)
        base_reward = Decimal('10.0')  # 10 PRGLD per block
        
        return base_reward + self.get_total_fees()
    
    def validate_ai_validators(self, min_validators: int = 3) -> bool:
        """
        Validate that sufficient AI validators participated.
        
        Args:
            min_validators: Minimum number of required validators
            
        Returns:
            bool: True if validation requirements are met
        """
        if len(self.ai_validators) < min_validators:
            return False
        
        # Check that all validators have valid signatures
        for validator in self.ai_validators:
            if not validator.validation_signature:
                return False
            
            # Check response time is within AI limits (<300ms)
            if validator.response_time_ms >= 300:
                return False
        
        return True
    
    def validate_consensus_proof(self) -> bool:
        """
        Validate the consensus proof structure.
        
        Returns:
            bool: True if consensus proof is valid
        """
        if not self.consensus_proof.challenge_id:
            return False
        
        if not self.consensus_proof.solutions:
            return False
        
        if not self.consensus_proof.cross_validations:
            return False
        
        # Verify consensus timestamp is reasonable
        if abs(self.consensus_proof.consensus_timestamp - self.timestamp) > 10:
            return False
        
        return True
    
    def is_valid(self, previous_block: Optional['Block'] = None) -> bool:
        """
        Validate block structure and constraints.
        
        Args:
            previous_block: Previous block for chain validation
            
        Returns:
            bool: True if block is valid
        """
        # Check basic structure
        if self.index < 0:
            return False
        
        # Validate timestamp
        current_time = time.time()
        if self.timestamp > current_time + 300:  # 5 minutes tolerance
            return False
        
        # Validate previous block connection
        if previous_block:
            if self.index != previous_block.index + 1:
                return False
            if self.previous_hash != previous_block.hash:
                return False
            if self.timestamp <= previous_block.timestamp:
                return False
        
        # Validate transactions
        for transaction in self.transactions:
            if not transaction.is_valid():
                return False
        
        # Validate merkle root
        calculated_merkle = self._calculate_merkle_root()
        if self.merkle_root != calculated_merkle:
            return False
        
        # Validate AI validators
        if not self.validate_ai_validators():
            return False
        
        # Validate consensus proof
        if not self.validate_consensus_proof():
            return False
        
        # Validate block hash
        calculated_hash = self.calculate_hash()
        if self.hash != calculated_hash:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """
        Convert block to dictionary for serialization.
        
        Returns:
            dict: Block data as dictionary
        """
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'merkle_root': self.merkle_root,
            'ai_validators': [asdict(validator) for validator in self.ai_validators],
            'consensus_proof': self.consensus_proof.to_dict(),
            'nonce': self.nonce,
            'hash': self.hash
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Block':
        """
        Create block from dictionary.
        
        Args:
            data: Block data as dictionary
            
        Returns:
            Block: New block instance
        """
        transactions = [Transaction.from_dict(tx_data) for tx_data in data['transactions']]
        ai_validators = [AIValidatorInfo(**validator_data) for validator_data in data['ai_validators']]
        consensus_proof = ConsensusProof.from_dict(data['consensus_proof'])
        
        return cls(
            index=data['index'],
            previous_hash=data['previous_hash'],
            timestamp=data['timestamp'],
            transactions=transactions,
            merkle_root=data['merkle_root'],
            ai_validators=ai_validators,
            consensus_proof=consensus_proof,
            nonce=data['nonce'],
            hash=data['hash']
        )


def create_genesis_block() -> Block:
    """
    Create the genesis block for PlayerGold blockchain.
    
    Returns:
        Block: Genesis block with initial configuration
    """
    # Create empty consensus proof for genesis
    genesis_consensus = ConsensusProof(
        challenge_id="genesis",
        challenge_data={},
        solutions=[],
        cross_validations=[],
        consensus_timestamp=time.time()
    )
    
    genesis_block = Block(
        index=0,
        previous_hash="0" * 64,  # 64 zeros for genesis
        timestamp=time.time(),
        transactions=[],
        merkle_root="",
        ai_validators=[],
        consensus_proof=genesis_consensus,
        nonce=0
    )
    
    return genesis_block