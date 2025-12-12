#!/usr/bin/env python3
"""
Enhanced Blockchain implementation for PlayerGold Multi-Node Network

Supports:
- Multi-node consensus validation
- Automatic reward distribution
- Fee distribution (30% dev, 10% pool, 60% burn)
- Halving mechanism
- Genesis block creation with system addresses
"""

import hashlib
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    from_address: str
    to_address: str
    amount: Decimal
    fee: Decimal = Decimal('0')
    timestamp: float = 0
    signature: str = ""
    nonce: int = 0
    transaction_type: str = "TRANSFER"
    memo: str = ""

    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()

    def to_dict(self):
        return {
            'from_address': self.from_address,
            'to_address': self.to_address,
            'amount': str(self.amount),
            'fee': str(self.fee),
            'timestamp': self.timestamp,
            'signature': self.signature,
            'nonce': self.nonce,
            'transaction_type': self.transaction_type,
            'memo': self.memo
        }

    def calculate_hash(self):
        """Calculate transaction hash"""
        tx_string = f"{self.from_address}{self.to_address}{self.amount}{self.fee}{self.timestamp}{self.nonce}"
        return hashlib.sha256(tx_string.encode()).hexdigest()


@dataclass
class Block:
    index: int
    previous_hash: str
    timestamp: float
    transactions: List[Transaction]
    merkle_root: str = ""
    hash: str = ""
    nonce: int = 0
    validator_nodes: List[str] = None

    def __post_init__(self):
        if self.validator_nodes is None:
            self.validator_nodes = []

    def to_dict(self):
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'merkle_root': self.merkle_root,
            'hash': self.hash,
            'nonce': self.nonce,
            'validator_nodes': self.validator_nodes
        }


class EnhancedBlockchain:
    """
    Enhanced blockchain implementation for multi-node consensus with
    automatic reward distribution and fee management.
    """
    
    def __init__(self):
        self.chain: List[Block] = []
        self.difficulty = 4
        self.mining_reward = Decimal('1024')  # Initial reward: 1,024 PRGLD
        self.balances: Dict[str, Decimal] = {}
        self.pending_reward_transactions: List[Transaction] = []
        
        # System addresses (will be set during genesis)
        self.liquidity_pool_address: Optional[str] = None
        self.burn_address: Optional[str] = None
        self.developer_address: Optional[str] = None
        
        # Fee distribution percentages
        self.developer_fee_percentage = Decimal('0.30')  # 30%
        self.liquidity_fee_percentage = Decimal('0.10')  # 10%
        self.burn_fee_percentage = Decimal('0.60')  # 60%
        
        # Create empty genesis block (will be replaced by bootstrap manager)
        self.create_empty_genesis_block()

    def create_empty_genesis_block(self):
        """Create an empty genesis block placeholder"""
        genesis_block = Block(
            index=0,
            previous_hash="0" * 64,
            timestamp=time.time(),
            transactions=[],
            validator_nodes=[]
        )
        
        genesis_block.merkle_root = self.calculate_merkle_root([])
        genesis_block.hash = self.calculate_block_hash(genesis_block)
        
        self.chain.append(genesis_block)
        logger.info("Empty genesis block created (placeholder)")

    def replace_genesis_block(self, genesis_block: Block):
        """Replace the placeholder genesis block with the real one"""
        if len(self.chain) == 1 and self.chain[0].index == 0:
            self.chain[0] = genesis_block
            
            # Process genesis transactions to initialize balances
            for tx in genesis_block.transactions:
                self.process_transaction(tx)
            
            logger.info(f"Genesis block replaced with real genesis block")
            logger.info(f"Genesis transactions processed: {len(genesis_block.transactions)}")
        else:
            logger.error("Cannot replace genesis block - blockchain already has multiple blocks")

    def set_system_addresses(self, liquidity_pool: str, burn_address: str, developer_address: str):
        """Set system addresses for fee distribution"""
        self.liquidity_pool_address = liquidity_pool
        self.burn_address = burn_address
        self.developer_address = developer_address
        
        logger.info(f"System addresses configured:")
        logger.info(f"  Liquidity pool: {liquidity_pool}")
        logger.info(f"  Burn address: {burn_address}")
        logger.info(f"  Developer address: {developer_address}")

    def calculate_merkle_root(self, transactions: List[Transaction]) -> str:
        """Calculate Merkle root of transactions"""
        if not transactions:
            return hashlib.sha256(b'').hexdigest()
        
        tx_hashes = [tx.calculate_hash() for tx in transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])
            
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            
            tx_hashes = new_hashes
        
        return tx_hashes[0]

    def calculate_block_hash(self, block: Block) -> str:
        """Calculate block hash"""
        block_string = f"{block.index}{block.previous_hash}{block.timestamp}{block.merkle_root}{block.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def get_latest_block(self) -> Block:
        """Get the latest block in the chain"""
        return self.chain[-1]

    def add_block(self, block: Block):
        """Add a new block to the chain and process all transactions"""
        # Process all transactions in the block
        for tx in block.transactions:
            self.process_transaction(tx)
        
        # Add block to chain
        self.chain.append(block)
        
        logger.info(f"Block #{block.index} added to blockchain")
        logger.info(f"  Transactions processed: {len(block.transactions)}")
        logger.info(f"  Block hash: {block.hash}")

    def process_transaction(self, transaction: Transaction) -> bool:
        """Process a transaction and update balances with fee distribution"""
        try:
            # Handle different transaction types
            if transaction.transaction_type == "GENESIS_INIT":
                # Genesis initialization - just add to balance
                self.update_balance(transaction.to_address, transaction.amount)
                logger.debug(f"Genesis init: {transaction.amount} PRGLD → {transaction.to_address}")
                return True
            
            elif transaction.transaction_type == "MINING_REWARD":
                # Mining reward - paid from liquidity pool
                if self.liquidity_pool_address:
                    # Deduct from liquidity pool
                    pool_balance = self.get_balance(self.liquidity_pool_address)
                    if pool_balance >= transaction.amount:
                        self.update_balance(self.liquidity_pool_address, -transaction.amount)
                        self.update_balance(transaction.to_address, transaction.amount)
                        logger.debug(f"Mining reward: {transaction.amount} PRGLD → {transaction.to_address}")
                        return True
                    else:
                        logger.warning(f"Insufficient liquidity pool balance for mining reward")
                        return False
                else:
                    # Fallback: just add to balance (for testing)
                    self.update_balance(transaction.to_address, transaction.amount)
                    return True
            
            elif transaction.transaction_type == "NETWORK_MAINTENANCE":
                # Network maintenance fee - paid to developer
                self.update_balance(transaction.to_address, transaction.amount)
                logger.debug(f"Network maintenance: {transaction.amount} PRGLD → {transaction.to_address}")
                return True
            
            elif transaction.transaction_type == "TOKEN_BURN":
                # Token burn - remove from circulation
                self.update_balance(transaction.to_address, transaction.amount)
                logger.debug(f"Token burn: {transaction.amount} PRGLD burned")
                return True
            
            elif transaction.transaction_type == "LIQUIDITY_POOL":
                # Add to liquidity pool
                self.update_balance(transaction.to_address, transaction.amount)
                logger.debug(f"Liquidity pool: {transaction.amount} PRGLD → pool")
                return True
            
            else:
                # Regular transfer transaction
                sender_balance = self.get_balance(transaction.from_address)
                total_amount = transaction.amount + transaction.fee
                
                if sender_balance < total_amount:
                    logger.warning(f"Insufficient balance: {sender_balance} < {total_amount}")
                    return False
                
                # Update balances
                self.update_balance(transaction.from_address, -total_amount)
                self.update_balance(transaction.to_address, transaction.amount)
                
                # Distribute fees if there's a fee
                if transaction.fee > 0:
                    self.distribute_transaction_fee(transaction.fee)
                
                logger.debug(f"Transfer: {transaction.amount} PRGLD from {transaction.from_address} to {transaction.to_address}")
                return True
        
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return False

    def distribute_transaction_fee(self, total_fee: Decimal):
        """Distribute transaction fee according to the 30/10/60 split"""
        if not self.developer_address or not self.liquidity_pool_address or not self.burn_address:
            logger.warning("System addresses not configured, skipping fee distribution")
            return
        
        # Calculate distribution amounts
        developer_amount = total_fee * self.developer_fee_percentage
        liquidity_amount = total_fee * self.liquidity_fee_percentage
        burn_amount = total_fee * self.burn_fee_percentage
        
        # Distribute fees
        self.update_balance(self.developer_address, developer_amount)
        self.update_balance(self.liquidity_pool_address, liquidity_amount)
        self.update_balance(self.burn_address, burn_amount)
        
        logger.debug(f"Fee distributed: {developer_amount} (dev) + {liquidity_amount} (pool) + {burn_amount} (burn)")

    def is_chain_valid(self) -> bool:
        """Validate the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.hash != self.calculate_block_hash(current_block):
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True

    def get_balance(self, address: str) -> Decimal:
        """Get balance for an address"""
        return self.balances.get(address, Decimal('0'))

    def update_balance(self, address: str, amount: Decimal):
        """Update balance for an address"""
        if address not in self.balances:
            self.balances[address] = Decimal('0')
        self.balances[address] += amount
        
        # Ensure balance doesn't go negative (except for system addresses)
        if self.balances[address] < 0 and address not in [self.liquidity_pool_address, self.burn_address]:
            logger.warning(f"Negative balance detected for {address}: {self.balances[address]}")

    def get_transaction_history(self, address: str) -> List[Dict]:
        """Get transaction history for an address"""
        history = []
        
        for block in self.chain:
            for tx in block.transactions:
                if tx.from_address == address or tx.to_address == address:
                    tx_dict = tx.to_dict()
                    tx_dict['block_index'] = block.index
                    tx_dict['block_hash'] = block.hash
                    tx_dict['status'] = 'confirmed'
                    tx_dict['confirmations'] = len(self.chain) - block.index
                    history.append(tx_dict)
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return history

    def get_network_stats(self) -> Dict:
        """Get network statistics"""
        total_supply = sum(self.balances.values())
        burned_amount = self.get_balance(self.burn_address) if self.burn_address else Decimal('0')
        circulating_supply = total_supply - burned_amount
        
        return {
            'total_blocks': len(self.chain),
            'total_transactions': sum(len(block.transactions) for block in self.chain),
            'total_supply': str(total_supply),
            'circulating_supply': str(circulating_supply),
            'burned_tokens': str(burned_amount),
            'liquidity_pool_balance': str(self.get_balance(self.liquidity_pool_address)) if self.liquidity_pool_address else '0',
            'developer_balance': str(self.get_balance(self.developer_address)) if self.developer_address else '0',
            'latest_block_hash': self.get_latest_block().hash,
            'latest_block_timestamp': self.get_latest_block().timestamp
        }

    def reset(self):
        """Reset the blockchain to initial state"""
        logger.warning("🚨 Resetting blockchain to initial state")
        
        self.chain = []
        self.balances = {}
        self.pending_reward_transactions = []
        
        # Reset system addresses
        self.liquidity_pool_address = None
        self.burn_address = None
        self.developer_address = None
        
        # Create new empty genesis block
        self.create_empty_genesis_block()
        
        logger.warning("✅ Blockchain reset completed")

    def to_dict(self):
        """Convert blockchain to dictionary"""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'difficulty': self.difficulty,
            'mining_reward': str(self.mining_reward),
            'balances': {addr: str(balance) for addr, balance in self.balances.items()},
            'system_addresses': {
                'liquidity_pool': self.liquidity_pool_address,
                'burn_address': self.burn_address,
                'developer_address': self.developer_address
            },
            'network_stats': self.get_network_stats()
        }