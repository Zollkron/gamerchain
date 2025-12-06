"""
Tests for PlayerGold transaction functionality.
"""

import pytest
import time
from decimal import Decimal
from cryptography.hazmat.primitives.asymmetric import ed25519

from src.blockchain.transaction import Transaction, TransactionType, FeeDistribution


class TestTransaction:
    """Test cases for Transaction class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        
        self.valid_transaction = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
    
    def test_transaction_creation(self):
        """Test basic transaction creation."""
        tx = self.valid_transaction
        
        assert tx.from_address == "sender123"
        assert tx.to_address == "receiver456"
        assert tx.amount == Decimal('100.0')
        assert tx.fee == Decimal('1.0')
        assert tx.transaction_type == TransactionType.TRANSFER
        assert tx.nonce == 1
        assert tx.hash is not None
        assert tx.signature is None
    
    def test_transaction_hash_calculation(self):
        """Test transaction hash calculation."""
        tx1 = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=1234567890.0,
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        
        tx2 = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=1234567890.0,
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        
        # Same data should produce same hash
        assert tx1.hash == tx2.hash
        
        # Different data should produce different hash
        tx3 = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('200.0'),  # Different amount
            fee=Decimal('1.0'),
            timestamp=1234567890.0,
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        
        assert tx1.hash != tx3.hash
    
    def test_transaction_signing(self):
        """Test transaction signing and verification."""
        tx = self.valid_transaction
        
        # Sign transaction
        tx.sign_transaction(self.private_key)
        assert tx.signature is not None
        
        # Verify signature
        assert tx.verify_signature(self.public_key) is True
        
        # Test signing already signed transaction
        with pytest.raises(ValueError):
            tx.sign_transaction(self.private_key)
    
    def test_transaction_signature_verification(self):
        """Test signature verification with different keys."""
        tx = self.valid_transaction
        tx.sign_transaction(self.private_key)
        
        # Verify with correct key
        assert tx.verify_signature(self.public_key) is True
        
        # Verify with wrong key
        wrong_private_key = ed25519.Ed25519PrivateKey.generate()
        wrong_public_key = wrong_private_key.public_key()
        assert tx.verify_signature(wrong_public_key) is False
    
    def test_transaction_validation(self):
        """Test transaction validation rules."""
        # Valid transaction
        assert self.valid_transaction.is_valid() is True
        
        # Invalid amount (negative)
        invalid_tx = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('-100.0'),
            fee=Decimal('1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        assert invalid_tx.is_valid() is False
        
        # Invalid fee (negative)
        invalid_tx = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('-1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        assert invalid_tx.is_valid() is False
        
        # Invalid nonce (negative)
        invalid_tx = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=-1
        )
        assert invalid_tx.is_valid() is False
        
        # Empty addresses
        invalid_tx = Transaction(
            from_address="",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        assert invalid_tx.is_valid() is False
        
        # Future timestamp (too far)
        invalid_tx = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=time.time() + 1000,  # 1000 seconds in future
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        assert invalid_tx.is_valid() is False
    
    def test_transaction_serialization(self):
        """Test transaction to/from dictionary conversion."""
        tx = self.valid_transaction
        tx.sign_transaction(self.private_key)
        
        # Convert to dict
        tx_dict = tx.to_dict()
        assert isinstance(tx_dict, dict)
        assert tx_dict['from_address'] == tx.from_address
        assert tx_dict['amount'] == str(tx.amount)
        assert tx_dict['transaction_type'] == tx.transaction_type.value
        
        # Convert back from dict
        tx_restored = Transaction.from_dict(tx_dict)
        assert tx_restored.from_address == tx.from_address
        assert tx_restored.amount == tx.amount
        assert tx_restored.transaction_type == tx.transaction_type
        assert tx_restored.signature == tx.signature
        assert tx_restored.hash == tx.hash


class TestFeeDistribution:
    """Test cases for FeeDistribution class."""
    
    def test_fee_distribution_calculation(self):
        """Test fee distribution calculation (60% burn, 30% maintenance, 10% liquidity)."""
        total_fee = Decimal('100.0')
        
        distribution = FeeDistribution.calculate_distribution(total_fee)
        
        assert distribution.burn_address == Decimal('60.0')           # 60%
        assert distribution.network_maintenance == Decimal('30.0')    # 30%
        assert distribution.liquidity_pool == Decimal('10.0')         # 10%
        
        # Verify total adds up
        total = (distribution.burn_address + 
                distribution.network_maintenance + 
                distribution.liquidity_pool)
        assert total == total_fee
    
    def test_fee_distribution_precision(self):
        """Test fee distribution with decimal precision."""
        total_fee = Decimal('1.23')
        
        distribution = FeeDistribution.calculate_distribution(total_fee)
        
        expected_burn = Decimal('0.738')         # 60% of 1.23
        expected_maintenance = Decimal('0.369')  # 30% of 1.23
        expected_liquidity = Decimal('0.123')    # 10% of 1.23
        
        assert distribution.burn_address == expected_burn
        assert distribution.network_maintenance == expected_maintenance
        assert distribution.liquidity_pool == expected_liquidity
    
    def test_fee_distribution_zero_fee(self):
        """Test fee distribution with zero fee."""
        total_fee = Decimal('0.0')
        
        distribution = FeeDistribution.calculate_distribution(total_fee)
        
        assert distribution.burn_address == Decimal('0.0')
        assert distribution.network_maintenance == Decimal('0.0')
        assert distribution.liquidity_pool == Decimal('0.0')


class TestTransactionTypes:
    """Test cases for different transaction types."""
    
    def test_transfer_transaction(self):
        """Test TRANSFER transaction type."""
        tx = Transaction(
            from_address="sender123",
            to_address="receiver456",
            amount=Decimal('100.0'),
            fee=Decimal('1.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.TRANSFER,
            nonce=1
        )
        
        assert tx.transaction_type == TransactionType.TRANSFER
        assert tx.is_valid() is True
    
    def test_burn_transaction(self):
        """Test BURN transaction type."""
        tx = Transaction(
            from_address="sender123",
            to_address="0x0000000000000000000000000000000000000000",  # Burn address
            amount=Decimal('50.0'),
            fee=Decimal('0.5'),
            timestamp=time.time(),
            transaction_type=TransactionType.BURN,
            nonce=1
        )
        
        assert tx.transaction_type == TransactionType.BURN
        assert tx.is_valid() is True
    
    def test_stake_transaction(self):
        """Test STAKE transaction type."""
        tx = Transaction(
            from_address="staker123",
            to_address="stake_pool_456",
            amount=Decimal('1000.0'),
            fee=Decimal('2.0'),
            timestamp=time.time(),
            transaction_type=TransactionType.STAKE,
            nonce=1
        )
        
        assert tx.transaction_type == TransactionType.STAKE
        assert tx.is_valid() is True
    
    def test_reward_transaction(self):
        """Test REWARD transaction type."""
        tx = Transaction(
            from_address="network",
            to_address="ai_validator_123",
            amount=Decimal('10.0'),
            fee=Decimal('0.0'),  # No fee for rewards
            timestamp=time.time(),
            transaction_type=TransactionType.REWARD,
            nonce=1
        )
        
        assert tx.transaction_type == TransactionType.REWARD
        assert tx.is_valid() is True