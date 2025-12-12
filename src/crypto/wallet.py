#!/usr/bin/env python3
"""
Wallet and cryptographic utilities for PlayerGold

Provides:
- Key pair generation
- Address derivation
- Mnemonic phrase generation
- Digital signatures
"""

import hashlib
import secrets
import base58
from typing import Dict, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import mnemonic
import logging

logger = logging.getLogger(__name__)


def generate_keypair() -> Dict[str, str]:
    """
    Generate a new Ed25519 key pair for PlayerGold addresses
    
    Returns:
        Dict containing private_key, public_key, and mnemonic
    """
    try:
        # Generate Ed25519 private key
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Serialize keys
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Convert to hex strings
        private_key_hex = private_key_bytes.hex()
        public_key_hex = public_key_bytes.hex()
        
        # Generate mnemonic phrase
        mnemonic_phrase = generate_mnemonic_from_key(private_key_bytes)
        
        logger.debug(f"Generated new key pair")
        logger.debug(f"Public key: {public_key_hex}")
        
        return {
            'private_key': private_key_hex,
            'public_key': public_key_hex,
            'mnemonic': mnemonic_phrase
        }
        
    except Exception as e:
        logger.error(f"Error generating key pair: {e}")
        raise


def derive_address(public_key_hex: str) -> str:
    """
    Derive a PlayerGold address from a public key
    
    Args:
        public_key_hex: Hexadecimal public key string
        
    Returns:
        PlayerGold address string (PG prefix + base58 encoded)
    """
    try:
        # Convert hex to bytes
        public_key_bytes = bytes.fromhex(public_key_hex)
        
        # Create address hash (SHA-256 + RIPEMD-160)
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
        
        # Add version byte (0x00 for PlayerGold mainnet)
        versioned_hash = b'\x00' + ripemd160_hash
        
        # Calculate checksum (double SHA-256)
        checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]
        
        # Combine versioned hash + checksum
        full_address = versioned_hash + checksum
        
        # Encode with base58 and add PG prefix
        base58_address = base58.b58encode(full_address).decode('utf-8')
        playergold_address = 'PG' + base58_address
        
        logger.debug(f"Derived address: {playergold_address}")
        
        return playergold_address
        
    except Exception as e:
        logger.error(f"Error deriving address: {e}")
        raise


def generate_mnemonic_from_key(private_key_bytes: bytes) -> str:
    """
    Generate a mnemonic phrase from private key bytes
    
    Args:
        private_key_bytes: Raw private key bytes
        
    Returns:
        12-word mnemonic phrase
    """
    try:
        # Use the private key as entropy for mnemonic generation
        entropy = hashlib.sha256(private_key_bytes).digest()[:16]  # 128 bits for 12 words
        
        # Generate mnemonic
        mnemo = mnemonic.Mnemonic("english")
        mnemonic_phrase = mnemo.to_mnemonic(entropy)
        
        logger.debug(f"Generated mnemonic phrase")
        
        return mnemonic_phrase
        
    except Exception as e:
        logger.error(f"Error generating mnemonic: {e}")
        raise


def validate_address(address: str) -> bool:
    """
    Validate a PlayerGold address
    
    Args:
        address: PlayerGold address to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check prefix
        if not address.startswith('PG'):
            return False
        
        # Remove prefix
        base58_part = address[2:]
        
        # Decode base58
        try:
            decoded = base58.b58decode(base58_part)
        except:
            return False
        
        # Check length (1 version byte + 20 hash bytes + 4 checksum bytes)
        if len(decoded) != 25:
            return False
        
        # Split components
        versioned_hash = decoded[:-4]
        checksum = decoded[-4:]
        
        # Verify checksum
        calculated_checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]
        
        return checksum == calculated_checksum
        
    except Exception as e:
        logger.error(f"Error validating address: {e}")
        return False


def sign_transaction(private_key_hex: str, transaction_data: str) -> str:
    """
    Sign transaction data with private key
    
    Args:
        private_key_hex: Hexadecimal private key string
        transaction_data: Transaction data to sign
        
    Returns:
        Hexadecimal signature string
    """
    try:
        # Convert hex to bytes
        private_key_bytes = bytes.fromhex(private_key_hex)
        
        # Create Ed25519 private key object
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        
        # Sign the transaction data
        signature = private_key.sign(transaction_data.encode('utf-8'))
        
        # Convert to hex
        signature_hex = signature.hex()
        
        logger.debug(f"Transaction signed")
        
        return signature_hex
        
    except Exception as e:
        logger.error(f"Error signing transaction: {e}")
        raise


def verify_signature(public_key_hex: str, signature_hex: str, transaction_data: str) -> bool:
    """
    Verify a transaction signature
    
    Args:
        public_key_hex: Hexadecimal public key string
        signature_hex: Hexadecimal signature string
        transaction_data: Original transaction data
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Convert hex to bytes
        public_key_bytes = bytes.fromhex(public_key_hex)
        signature_bytes = bytes.fromhex(signature_hex)
        
        # Create Ed25519 public key object
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        # Verify signature
        try:
            public_key.verify(signature_bytes, transaction_data.encode('utf-8'))
            return True
        except:
            return False
            
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


def generate_system_address(purpose: str) -> str:
    """
    Generate a deterministic system address for specific purposes
    
    Args:
        purpose: Purpose string (e.g., "LIQUIDITY_POOL", "BURN_ADDRESS")
        
    Returns:
        PlayerGold system address
    """
    try:
        # Create deterministic seed from purpose
        seed = hashlib.sha256(f"PLAYERGOLD_SYSTEM_{purpose}".encode()).digest()
        
        # Generate deterministic key pair
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed[:32])
        public_key = private_key.public_key()
        
        # Get public key bytes
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Derive address
        address = derive_address(public_key_bytes.hex())
        
        logger.info(f"Generated system address for {purpose}: {address}")
        
        return address
        
    except Exception as e:
        logger.error(f"Error generating system address: {e}")
        raise


def restore_keypair_from_mnemonic(mnemonic_phrase: str) -> Optional[Dict[str, str]]:
    """
    Restore key pair from mnemonic phrase
    
    Args:
        mnemonic_phrase: 12-word mnemonic phrase
        
    Returns:
        Dict containing private_key and public_key, or None if invalid
    """
    try:
        # Validate mnemonic
        mnemo = mnemonic.Mnemonic("english")
        if not mnemo.check(mnemonic_phrase):
            logger.error("Invalid mnemonic phrase")
            return None
        
        # Convert mnemonic to entropy
        entropy = mnemo.to_entropy(mnemonic_phrase)
        
        # Generate private key from entropy
        private_key_bytes = hashlib.sha256(entropy).digest()[:32]
        
        # Create Ed25519 key pair
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        public_key = private_key.public_key()
        
        # Serialize keys
        private_key_hex = private_key_bytes.hex()
        public_key_hex = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()
        
        logger.info("Key pair restored from mnemonic")
        
        return {
            'private_key': private_key_hex,
            'public_key': public_key_hex,
            'mnemonic': mnemonic_phrase
        }
        
    except Exception as e:
        logger.error(f"Error restoring key pair from mnemonic: {e}")
        return None


# Utility functions for address generation
def generate_faucet_address() -> str:
    """Generate the standard faucet address"""
    return generate_system_address("FAUCET")


def generate_validator_address(node_id: str) -> str:
    """Generate a validator address for a specific node"""
    return generate_system_address(f"VALIDATOR_{node_id}")


def generate_burn_address() -> str:
    """Generate the standard burn address"""
    return generate_system_address("BURN_ADDRESS")


def generate_liquidity_pool_address() -> str:
    """Generate the standard liquidity pool address"""
    return generate_system_address("LIQUIDITY_POOL")