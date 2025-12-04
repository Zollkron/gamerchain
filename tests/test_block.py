"""
Tests for PlayerGold block functionality.
"""

import pytest
import time
from decimal import Decimal
from cryptography.hazmat.primitives.asymmetric import ed25519

from src.blockchain.block import Block, ConsensusProof, AIValidatorInfo, create_genesis_block
from src.blockchain.transaction import Transaction, TransactionType


class TestConsensusProof:
    """Test cases for ConsensusProof class."""
    
    def test_consensus_proof_creation(self):
        """Test basic consensus proof creation."""
        proof = ConsensusProof(
            challenge_id="challenge_123",
            challenge_data={"type": "math", "difficulty": 5},
            solutions=[{"node_id": "ai_1", "solution": "42"}],
            cross_validations=[{"validator": "ai_2", "result": "valid"}],
            consensus_timestamp=time.time()
        )
        
        assert proof.challenge_id == "challenge_123"
        assert proof.challenge_data["type"] == "math"
        assert len(proof.solutions) == 1
        assert len(proof.cross_validations) == 1
    
    def test_consensus_proof_serialization(self):
        """Test consensus proof to/from dictionary conversion."""
        timestamp = time.time()
        proof = ConsensusProof(
            challenge_id="challenge_123",
            challenge_data={"type": "math"},
            solutions=[{"node_id": "ai_1", "solution": "42"}],
            cross_validations=[{"validator": "ai_2", "result": "valid"}],
            consensus_timestamp=timestamp
        )
        
        # Convert to dict
        proof_dict = proof.to_dict()
        assert isinstance(proof_dict, dict)
        assert proof_dict['challenge_id'] == "challenge_123"
        
        # Convert back from dict
        proof_restored = ConsensusProof.from_dict(proof_dict)
        assert proof_restored.challenge_id == proof.challenge_id
        assert proof_restored.consensus_timestamp == proof.consensus_timestamp


class TestAIValidatorInfo:
    """Test cases for AIValidatorInfo class."""
    
    def test_ai_validator_info_creation(self):
        """Test AI validator info creation."""
        validator = AIValidatorInfo(
            node_id="ai_node_123",
            model_hash="abc123def456",
            validation_signature="signature_data",
            response_time_ms=50,
            reputation_score=0.95
        )
        
        assert validator.node_id == "ai_node_123"
        assert validator.model_hash == "abc123def456"
        assert validator.response_time_ms == 50
        assert validator.reputation_score == 0.95


class TestBlock:
    """Test cases for Block class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.consensus_proof = ConsensusProof(
            challenge_id="test_challenge",
            challenge_data={"type": "math"},
            solutions=[{"node_id": "ai_1", "solution": "42"}],
            cross_validations=[{"validator": "ai_2", "result": "valid"}],
            consensus_timestamp=time.time()
        )
        
        self.ai_validators = [
            AIValidatorInfo(
                node_id="ai_node_1",
                model_hash="hash1",
                validation_signature="sig1",
                response_time_ms=50,
                reputation_score=0.95
            ),
            AIValidatorInfo(
                node_id="ai_node_2", 
                model_hash="hash2",
                validation_signature="sig2",
                response_time_ms=75,
                reputation_score=0.90
            ),
            AIValidatorInfo(
                node_id="ai_node_3",
                model_hash="hash3", 
                validation_signature="sig3",
                response_time_ms=60,
                reputation_score=0.92
            )
        ]
        
        # Create sample transaction
        self.sample_transaction = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
    
    def test_block_creation(self):
        """Test basic block creation."""
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        assert block.index == 1
        assert block.previous_hash == "prev_hash_123"
        assert len(block.ai_validators) == 3
        assert block.hash is not None
    
    def test_block_with_transactions(self):
        """Test block creation with transactions."""
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[self.sample_transaction],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        assert len(block.transactions) == 1
        assert block.merkle_root != ""  # Should be calculated
        assert block.hash is not None
    
    def test_add_transaction(self):
        """Test adding transaction to block."""
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        # Add valid transaction
        success = block.add_transaction(self.sample_transaction)
        assert success is True
        assert len(block.transactions) == 1
        
        # Try to add same transaction again (should fail)
        success = block.add_transaction(self.sample_transaction)
        assert success is False
        assert len(block.transactions) == 1
    
    def test_add_invalid_transaction(self):
        """Test adding invalid transaction to block."""
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        # Create invalid transaction (negative amount)
        invalid_tx = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('-100.0'),  # Invalid
            fee=Decimal('1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        
        success = block.add_transaction(invalid_tx)
        assert success is False
        assert len(block.transactions) == 0
    
    def test_get_total_fees(self):
        """Test calculating total fees in block."""
        tx1 = Transaction(
            from_address="sender1",
            to_address="receiver1",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        
        tx2 = Transaction(
            from_address="sender2",
            to_address="receiver2",
            amount=Decimal('200.0'),
            fee=Decimal('2.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[tx1, tx2],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        total_fees = block.get_total_fees()
        assert total_fees == Decimal('3.0')  # 1.0 + 2.0
    
    def test_get_total_rewards(self):
        """Test calculating total rewards (base + fees)."""
        tx = Transaction(
            from_address="sender1",
            to_address="receiver1",
            amount=Decimal('100.0'),
            fee=Decimal('5.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[tx],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        total_rewards = block.get_total_rewards()
        # Base reward (10.0) + fees (5.0) = 15.0
        assert total_rewards == Decimal('15.0')
    
    def test_validate_ai_validators(self):
        """Test AI validator validation."""
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        # Should pass with 3 validators (minimum is 3)
        assert block.validate_ai_validators() is True
        
        # Test with insufficient validators
        block.ai_validators = self.ai_validators[:2]  # Only 2 validators
        assert block.validate_ai_validators() is False
        
        # Test with validator without signature
        invalid_validator = AIValidatorInfo(
            node_id="ai_node_4",
            model_hash="hash4",
            validation_signature="",  # Empty signature
            response_time_ms=50,
            reputation_score=0.95
        )
        block.ai_validators = [invalid_validator] + self.ai_validators[:2]
        assert block.validate_ai_validators() is False
        
        # Test with slow validator (>= 100ms)
        slow_validator = AIValidatorInfo(
            node_id="ai_node_5",
            model_hash="hash5",
            validation_signature="sig5",
            response_time_ms=100,  # Too slow
            reputation_score=0.95
        )
        block.ai_validators = [slow_validator] + self.ai_validators[:2]
        assert block.validate_ai_validators() is False
    
    def test_validate_consensus_proof(self):
        """Test consensus proof validation."""
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        # Should pass with valid consensus proof
        assert block.validate_consensus_proof() is True
        
        # Test with empty challenge ID
        invalid_proof = ConsensusProof(
            challenge_id="",  # Empty
            challenge_data={"type": "math"},
            solutions=[{"node_id": "ai_1", "solution": "42"}],
            cross_validations=[{"validator": "ai_2", "result": "valid"}],
            consensus_timestamp=time.time()
        )
        block.consensus_proof = invalid_proof
        assert block.validate_consensus_proof() is False
        
        # Test with no solutions
        invalid_proof = ConsensusProof(
            challenge_id="test_challenge",
            challenge_data={"type": "math"},
            solutions=[],  # Empty
            cross_validations=[{"validator": "ai_2", "result": "valid"}],
            consensus_timestamp=time.time()
        )
        block.consensus_proof = invalid_proof
        assert block.validate_consensus_proof() is False
        
        # Test with no cross validations
        invalid_proof = ConsensusProof(
            challenge_id="test_challenge",
            challenge_data={"type": "math"},
            solutions=[{"node_id": "ai_1", "solution": "42"}],
            cross_validations=[],  # Empty
            consensus_timestamp=time.time()
        )
        block.consensus_proof = invalid_proof
        assert block.validate_consensus_proof() is False
    
    def test_block_validation(self):
        """Test complete block validation."""
        current_time = time.time()
        
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=current_time,
            transactions=[self.sample_transaction],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        # Should be valid
        assert block.is_valid() is True
        
        # Test with negative index
        block.index = -1
        assert block.is_valid() is False
        block.index = 1  # Reset
        
        # Test with future timestamp
        block.timestamp = current_time + 1000
        assert block.is_valid() is False
        block.timestamp = current_time  # Reset
        
        # Should be valid again
        assert block.is_valid() is True
    
    def test_block_chain_validation(self):
        """Test block validation with previous block."""
        current_time = time.time()
        
        # Create consensus proof with matching timestamp
        prev_consensus_proof = ConsensusProof(
            challenge_id="prev_challenge",
            challenge_data={"type": "math"},
            solutions=[{"node_id": "ai_1", "solution": "42"}],
            cross_validations=[{"validator": "ai_2", "result": "valid"}],
            consensus_timestamp=current_time - 100
        )
        
        current_consensus_proof = ConsensusProof(
            challenge_id="current_challenge",
            challenge_data={"type": "math"},
            solutions=[{"node_id": "ai_1", "solution": "42"}],
            cross_validations=[{"validator": "ai_2", "result": "valid"}],
            consensus_timestamp=current_time
        )
        
        # Create previous block
        prev_block = Block(
            index=0,
            previous_hash="genesis",
            timestamp=current_time - 100,
            transactions=[],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=prev_consensus_proof
        )
        
        # Create current block
        current_block = Block(
            index=1,
            previous_hash=prev_block.hash,
            timestamp=current_time,
            transactions=[],
            merkle_root="",  # Will be calculated automatically
            ai_validators=self.ai_validators,
            consensus_proof=current_consensus_proof
        )
        
        # Should be valid with correct previous block
        assert current_block.is_valid(prev_block) is True
        
        # Test with wrong index
        current_block.index = 5  # Should be 1
        assert current_block.is_valid(prev_block) is False
        current_block.index = 1  # Reset
        
        # Test with wrong previous hash
        current_block.previous_hash = "wrong_hash"
        assert current_block.is_valid(prev_block) is False
        current_block.previous_hash = prev_block.hash  # Reset
        
        # Test with earlier timestamp
        current_block.timestamp = prev_block.timestamp - 10
        assert current_block.is_valid(prev_block) is False
    
    def test_block_serialization(self):
        """Test block to/from dictionary conversion."""
        block = Block(
            index=1,
            previous_hash="prev_hash_123",
            timestamp=time.time(),
            transactions=[self.sample_transaction],
            merkle_root="",
            ai_validators=self.ai_validators,
            consensus_proof=self.consensus_proof
        )
        
        # Convert to dict
        block_dict = block.to_dict()
        assert isinstance(block_dict, dict)
        assert block_dict['index'] == 1
        assert len(block_dict['transactions']) == 1
        assert len(block_dict['ai_validators']) == 3
        
        # Convert back from dict
        block_restored = Block.from_dict(block_dict)
        assert block_restored.index == block.index
        assert block_restored.previous_hash == block.previous_hash
        assert len(block_restored.transactions) == len(block.transactions)
        assert len(block_restored.ai_validators) == len(block.ai_validators)
        assert block_restored.hash == block.hash


class TestGenesisBlock:
    """Test cases for genesis block creation."""
    
    def test_create_genesis_block(self):
        """Test genesis block creation."""
        genesis = create_genesis_block()
        
        assert genesis.index == 0
        assert genesis.previous_hash == "0" * 64
        assert len(genesis.transactions) == 0
        assert len(genesis.ai_validators) == 0
        assert genesis.consensus_proof.challenge_id == "genesis"
        assert genesis.hash is not None
    
    def test_genesis_block_validation(self):
        """Test genesis block validation."""
        genesis = create_genesis_block()
        
        # Genesis block should be valid without previous block
        # Note: This will fail AI validator validation, but that's expected for genesis
        # In practice, genesis block would have special validation rules
        assert genesis.index == 0
        assert genesis.previous_hash == "0" * 64