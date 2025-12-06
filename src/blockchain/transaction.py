"""
Transaction module for PlayerGold blockchain with PoAIP support.
Implements transaction structure with fees and validation.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from decimal import Decimal
from enum import Enum
from typing import Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class TransactionType(Enum):
    """Types of transactions supported in PlayerGold blockchain."""
    TRANSFER = "transfer"
    BURN = "burn"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"


@dataclass
class Transaction:
    """
    Transaction structure for PlayerGold blockchain.
    Supports PoAIP consensus with fee distribution and token burning.
    """
    from_address: str
    to_address: str
    amount: Decimal
    fee: Decimal
    timestamp: float
    transaction_type: TransactionType
    nonce: int
    signature: Optional[str] = None
    hash: Optional[str] = None
    
    def __post_init__(self):
        """Initialize transaction hash after creation."""
        if self.hash is None:
            self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calculate SHA-256 hash of transaction data.
        
        Returns:
            str: Hexadecimal hash of transaction
        """
        # Create transaction data without signature and hash for hashing
        tx_data = {
            'from_address': self.from_address,
            'to_address': self.to_address,
            'amount': str(self.amount),
            'fee': str(self.fee),
            'timestamp': self.timestamp,
            'transaction_type': self.transaction_type.value,
            'nonce': self.nonce
        }
        
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def sign_transaction(self, private_key: ed25519.Ed25519PrivateKey) -> None:
        """
        Sign transaction with Ed25519 private key.
        
        Args:
            private_key: Ed25519 private key for signing
        """
        if self.signature is not None:
            raise ValueError("Transaction already signed")
        
        message = self.hash.encode()
        signature = private_key.sign(message)
        self.signature = signature.hex()
    
    def verify_signature(self, public_key: ed25519.Ed25519PublicKey) -> bool:
        """
        Verify transaction signature with Ed25519 public key.
        
        Args:
            public_key: Ed25519 public key for verification
            
        Returns:
            bool: True if signature is valid
        """
        if self.signature is None:
            return False
        
        try:
            message = self.hash.encode()
            signature = bytes.fromhex(self.signature)
            public_key.verify(signature, message)
            return True
        except Exception:
            return False
    
    def is_valid(self) -> bool:
        """
        Validate transaction structure and constraints.
        
        Returns:
            bool: True if transaction is valid
        """
        # Check basic constraints
        if self.amount < 0 or self.fee < 0:
            return False
        
        if self.nonce < 0:
            return False
        
        # Check addresses are not empty
        if not self.from_address or not self.to_address:
            return False
        
        # Check timestamp is reasonable (not too far in future)
        current_time = time.time()
        if self.timestamp > current_time + 300:  # 5 minutes tolerance
            return False
        
        # Verify hash matches calculated hash
        calculated_hash = self.calculate_hash()
        if self.hash != calculated_hash:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary for serialization.
        
        Returns:
            dict: Transaction data as dictionary
        """
        data = asdict(self)
        data['amount'] = str(self.amount)
        data['fee'] = str(self.fee)
        data['transaction_type'] = self.transaction_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """
        Create transaction from dictionary.
        
        Args:
            data: Transaction data as dictionary
            
        Returns:
            Transaction: New transaction instance
        """
        return cls(
            from_address=data['from_address'],
            to_address=data['to_address'],
            amount=Decimal(data['amount']),
            fee=Decimal(data['fee']),
            timestamp=data['timestamp'],
            transaction_type=TransactionType(data['transaction_type']),
            nonce=data['nonce'],
            signature=data.get('signature'),
            hash=data.get('hash')
        )


@dataclass
class FeeDistribution:
    """
    Fee distribution structure for PlayerGold tokenomics.
    
    Nueva distribución justa:
    - 60% quemado (deflación del token)
    - 30% mantenimiento de red (dominio, hosting, desarrollo, infraestructura)
    - 10% pool de liquidez
    """
    burn_address: Decimal           # 60% quemado
    network_maintenance: Decimal    # 30% mantenimiento de red
    liquidity_pool: Decimal         # 10% liquidez
    
    @classmethod
    def calculate_distribution(cls, total_fee: Decimal) -> 'FeeDistribution':
        """
        Calculate fee distribution according to PlayerGold tokenomics.
        
        Args:
            total_fee: Total fee amount to distribute
            
        Returns:
            FeeDistribution: Calculated distribution
        """
        # Nueva distribución: 60% quema, 30% mantenimiento, 10% liquidez
        burn_amount = total_fee * Decimal('0.60')
        network_maintenance_amount = total_fee * Decimal('0.30')
        liquidity_amount = total_fee * Decimal('0.10')
        
        return cls(
            burn_address=burn_amount,
            network_maintenance=network_maintenance_amount,
            liquidity_pool=liquidity_amount
        )