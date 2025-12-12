#!/usr/bin/env python3
"""
Multi-Node PoAIP Consensus for PlayerGold

Implements the Proof-of-AI-Participation consensus mechanism with:
- 66% consensus threshold for block validation
- 10-second guaranteed block production cycle
- Automatic reward distribution from liquidity pool
- Halving mechanism every 100,000 blocks
- Random selection of reward distributor (reputation >90%)

Key Features:
- Distributed consensus among AI nodes
- Guaranteed block production every 10 seconds
- Automatic inclusion of reward transactions
- Fee distribution (30% dev, 10% pool, 60% burn)
- Reputation-based validator selection
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import json

from ..blockchain.enhanced_blockchain import EnhancedBlockchain, Block, Transaction
from ..p2p.network import P2PNetwork, MessageType, P2PMessage
from .bootstrap_manager import BootstrapManager, SystemAddresses

logger = logging.getLogger(__name__)


@dataclass
class ConsensusVote:
    """Vote from an AI node for block validation"""
    node_id: str
    block_hash: str
    vote: bool  # True = approve, False = reject
    reputation: Decimal
    timestamp: float
    signature: str


@dataclass
class BlockProposal:
    """Block proposal for consensus voting"""
    block: Block
    proposer_id: str
    proposal_timestamp: float
    votes: Dict[str, ConsensusVote]
    consensus_reached: bool = False
    consensus_result: bool = False


@dataclass
class ValidatorNode:
    """Information about a validator AI node"""
    node_id: str
    reputation: Decimal
    last_validation: float
    total_validations: int
    validator_address: str  # Internal address for operations
    user_reward_address: str  # Personal address for rewards
    is_active: bool = True


class HalvingManager:
    """Manages the halving mechanism for block rewards and fee redistribution"""
    
    def __init__(self, initial_reward: Decimal = Decimal('1024'), 
                 halving_interval: int = 100000,
                 fee_manager: Optional['HalvingFeeManager'] = None):
        self.initial_reward = initial_reward
        self.halving_interval = halving_interval
        self.current_reward = initial_reward
        self.halvings_occurred = 0
        self.next_halving_block = halving_interval
        
        # Import here to avoid circular imports
        if fee_manager is None:
            from .halving_fee_manager import HalvingFeeManager
            self.fee_manager = HalvingFeeManager()
        else:
            self.fee_manager = fee_manager
    
    def calculate_current_reward(self, block_number: int) -> Decimal:
        """Calculate current reward based on block number"""
        halvings = block_number // self.halving_interval
        current_reward = self.initial_reward / (2 ** halvings)
        return current_reward
    
    def check_halving_event(self, block_number: int) -> bool:
        """Check if current block triggers a halving event"""
        return block_number > 0 and block_number % self.halving_interval == 0
    
    def process_halving(self, block_number: int):
        """Process a halving event - handles both reward halving and fee redistribution"""
        if self.check_halving_event(block_number):
            self.halvings_occurred += 1
            self.current_reward = self.calculate_current_reward(block_number)
            self.next_halving_block = block_number + self.halving_interval
            
            # Process fee redistribution
            new_distribution = self.fee_manager.process_halving_redistribution(
                self.halvings_occurred, block_number
            )
            
            logger.info(f"🎯 HALVING EVENT at block {block_number}")
            logger.info(f"💰 New reward per block: {self.current_reward} PRGLD")
            logger.info(f"📊 New fee distribution: {new_distribution}")
            logger.info(f"📅 Next halving at block: {self.next_halving_block}")
            
            return new_distribution
            
            return new_distribution
        
        return None
            logger.info(f"📅 Next halving at block: {self.next_halving_block}")


class MultiNodeConsensus:
    """
    Multi-node PoAIP consensus implementation with guaranteed 10-second blocks
    and 66% consensus threshold for validation.
    """
    
    def __init__(self, 
                 node_id: str,
                 p2p_network: P2PNetwork,
                 blockchain: EnhancedBlockchain,
                 bootstrap_manager: BootstrapManager):
        self.node_id = node_id
        self.p2p_network = p2p_network
        self.blockchain = blockchain
        self.bootstrap_manager = bootstrap_manager
        
        # Consensus configuration
        self.consensus_threshold = Decimal('0.66')  # 66% threshold
        self.block_interval = 10  # 10 seconds
        self.min_reputation_for_distributor = Decimal('90.0')
        
        # Consensus state
        self.validator_nodes: Dict[str, ValidatorNode] = {}
        self.pending_transactions: List[Transaction] = []
        self.current_proposal: Optional[BlockProposal] = None
        self.is_mining = False
        self.last_block_time = time.time()
        
        # Halving manager
        self.halving_manager = HalvingManager()
        
        # Connect halving fee manager to blockchain
        self.blockchain.set_halving_fee_manager(self.halving_manager.fee_manager)
        
        # Initialize and connect voluntary burn manager
        from .voluntary_burn_manager import VoluntaryBurnManager
        self.voluntary_burn_manager = VoluntaryBurnManager()
        self.blockchain.set_voluntary_burn_manager(self.voluntary_burn_manager)
        
        # Load fee distribution state on startup
        self._load_fee_distribution_state_on_startup()
        
        # System addresses (will be set after genesis)
        self.system_addresses: Optional[SystemAddresses] = None
        
        # Register P2P message handlers
        self.p2p_network.register_message_handler(
            MessageType.BLOCK, self._handle_block_message
        )
        self.p2p_network.register_message_handler(
            MessageType.TRANSACTION, self._handle_transaction_message
        )
        self.p2p_network.register_message_handler(
            MessageType.CHALLENGE, self._handle_consensus_vote
        )
        self.p2p_network.register_message_handler(
            MessageType.FEE_DISTRIBUTION_UPDATE, self._handle_fee_distribution_update
        )
        
        logger.info(f"Multi-Node Consensus initialized for node {node_id}")
        logger.info(f"Consensus threshold: {self.consensus_threshold * 100}%")
        logger.info(f"Block interval: {self.block_interval} seconds")
    
    async def start(self):
        """Start the consensus mechanism"""
        logger.info("🚀 Starting Multi-Node Consensus...")
        
        # Wait for genesis block if not created
        while not self.bootstrap_manager.genesis_created:
            logger.info("⏳ Waiting for genesis block creation...")
            await asyncio.sleep(5)
        
        # Get system addresses from bootstrap manager
        self.system_addresses = self.bootstrap_manager.system_addresses
        
        # Initialize validator nodes from genesis pioneers
        await self._initialize_validators()
        
        # Start block production cycle
        asyncio.create_task(self._block_production_cycle())
        
        # Start validator monitoring
        asyncio.create_task(self._monitor_validators())
        
        logger.info("✅ Multi-Node Consensus started successfully")
    
    async def _initialize_validators(self):
        """Initialize validator nodes from genesis pioneers"""
        genesis_status = self.bootstrap_manager.get_genesis_status()
        
        for node_id, pioneer_info in genesis_status['pioneers'].items():
            validator = ValidatorNode(
                node_id=node_id,
                reputation=Decimal('100.0'),  # Genesis pioneers start with 100% reputation
                last_validation=time.time(),
                total_validations=0,
                validator_address=pioneer_info['validator_address'],
                user_reward_address=pioneer_info['user_reward_address']
            )
            
            self.validator_nodes[node_id] = validator
            logger.info(f"🤖 Initialized validator: {node_id} (reputation: 100%)")
    
    async def _block_production_cycle(self):
        """Main block production cycle - guarantees blocks every 10 seconds"""
        logger.info("⏰ Starting 10-second block production cycle...")
        
        while True:
            try:
                current_time = time.time()
                time_since_last_block = current_time - self.last_block_time
                
                # Check if 10 seconds have passed
                if time_since_last_block >= self.block_interval:
                    logger.info(f"🔨 10 seconds elapsed, producing new block...")
                    await self._produce_block()
                else:
                    # Wait for remaining time
                    remaining_time = self.block_interval - time_since_last_block
                    await asyncio.sleep(min(remaining_time, 1.0))
                
            except Exception as e:
                logger.error(f"Error in block production cycle: {e}")
                await asyncio.sleep(5)
    
    async def _produce_block(self):
        """Produce a new block with consensus validation"""
        if self.is_mining:
            logger.debug("Already mining, skipping block production")
            return
        
        self.is_mining = True
        
        try:
            logger.info("📦 Starting block production...")
            
            # Get current block number
            current_block = self.blockchain.get_latest_block()
            new_block_index = current_block.index + 1
            
            # Check for halving event and update fee distribution if needed
            new_distribution = self.halving_manager.process_halving(new_block_index)
            if new_distribution:
                # Halving occurred, update blockchain fee distribution
                self.blockchain.update_fee_distribution(new_distribution)
                # Save updated state to disk
                self._save_fee_distribution_state()
                # Broadcast fee distribution update to all nodes
                await self._broadcast_fee_distribution_update(new_distribution, new_block_index)
            
            # Collect transactions for the block
            block_transactions = await self._collect_block_transactions(new_block_index)
            
            # Create block proposal
            new_block = Block(
                index=new_block_index,
                previous_hash=current_block.hash,
                timestamp=time.time(),
                transactions=block_transactions,
                validator_nodes=list(self.validator_nodes.keys()),
                nonce=0
            )
            
            # Calculate merkle root and hash
            new_block.merkle_root = self.blockchain.calculate_merkle_root(block_transactions)
            new_block.hash = self.blockchain.calculate_block_hash(new_block)
            
            # Propose block for consensus
            proposal = BlockProposal(
                block=new_block,
                proposer_id=self.node_id,
                proposal_timestamp=time.time(),
                votes={}
            )
            
            # Start consensus process
            consensus_result = await self._run_consensus(proposal)
            
            if consensus_result:
                # Add block to blockchain
                self.blockchain.add_block(new_block)
                self.last_block_time = time.time()
                
                # Clear processed transactions
                self.pending_transactions = []
                
                logger.info(f"🎉 Block #{new_block_index} added to blockchain!")
                logger.info(f"📦 Block hash: {new_block.hash}")
                logger.info(f"📋 Transactions: {len(block_transactions)}")
                
                # Broadcast new block to network
                await self._broadcast_new_block(new_block)
                
            else:
                logger.warning(f"❌ Block #{new_block_index} rejected by consensus")
        
        except Exception as e:
            logger.error(f"Error producing block: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.is_mining = False
    
    async def _collect_block_transactions(self, block_index: int) -> List[Transaction]:
        """Collect transactions for the new block"""
        transactions = []
        
        # Add pending user transactions
        transactions.extend(self.pending_transactions[:100])  # Limit to 100 transactions per block
        
        # Always add reward transactions (guarantees non-empty blocks)
        reward_transactions = await self._create_reward_transactions(block_index)
        transactions.extend(reward_transactions)
        
        logger.info(f"📋 Collected {len(transactions)} transactions for block #{block_index}")
        logger.info(f"   User transactions: {len(self.pending_transactions[:100])}")
        logger.info(f"   Reward transactions: {len(reward_transactions)}")
        
        return transactions
    
    async def _create_reward_transactions(self, block_index: int) -> List[Transaction]:
        """Create reward transactions for active validators"""
        if not self.system_addresses:
            return []
        
        reward_transactions = []
        active_validators = [v for v in self.validator_nodes.values() if v.is_active]
        
        if not active_validators:
            logger.warning("No active validators for reward distribution")
            return []
        
        # Calculate current block reward
        current_reward = self.halving_manager.calculate_current_reward(block_index)
        reward_per_validator = current_reward / len(active_validators)
        
        # Select random distributor with reputation >90%
        eligible_distributors = [
            v for v in active_validators 
            if v.reputation >= self.min_reputation_for_distributor
        ]
        
        if not eligible_distributors:
            # Fallback to highest reputation validator
            eligible_distributors = [max(active_validators, key=lambda v: v.reputation)]
        
        distributor = random.choice(eligible_distributors)
        
        logger.info(f"🎯 Selected reward distributor: {distributor.node_id} (reputation: {distributor.reputation}%)")
        logger.info(f"💰 Total reward: {current_reward} PRGLD")
        logger.info(f"👥 Active validators: {len(active_validators)}")
        logger.info(f"💎 Reward per validator: {reward_per_validator} PRGLD")
        
        # Create reward transactions
        for validator in active_validators:
            reward_tx = Transaction(
                from_address=self.system_addresses.liquidity_pool,
                to_address=validator.user_reward_address,
                amount=reward_per_validator,
                fee=Decimal('0'),  # No fee for internal reward transactions
                timestamp=time.time(),
                transaction_type="MINING_REWARD",
                memo=f"Mining reward - Block #{block_index}"
            )
            
            reward_transactions.append(reward_tx)
            
            logger.debug(f"🎁 Reward: {reward_per_validator} PRGLD → {validator.user_reward_address}")
        
        return reward_transactions
    
    async def _run_consensus(self, proposal: BlockProposal) -> bool:
        """Run consensus process for block proposal"""
        logger.info(f"🗳️  Starting consensus for block #{proposal.block.index}")
        
        # Broadcast block proposal to all validators
        await self._broadcast_block_proposal(proposal)
        
        # Vote on our own proposal
        our_vote = await self._validate_block_proposal(proposal)
        proposal.votes[self.node_id] = ConsensusVote(
            node_id=self.node_id,
            block_hash=proposal.block.hash,
            vote=our_vote,
            reputation=self.validator_nodes.get(self.node_id, ValidatorNode(
                node_id=self.node_id,
                reputation=Decimal('100.0'),
                last_validation=time.time(),
                total_validations=0,
                validator_address="",
                user_reward_address=""
            )).reputation,
            timestamp=time.time(),
            signature=""
        )
        
        # Wait for votes from other validators (max 5 seconds)
        consensus_timeout = 5.0
        start_time = time.time()
        
        while time.time() - start_time < consensus_timeout:
            # Check if we have enough votes for consensus
            if await self._check_consensus_reached(proposal):
                break
            
            await asyncio.sleep(0.1)
        
        # Calculate final consensus result
        consensus_result = await self._calculate_consensus_result(proposal)
        
        logger.info(f"🗳️  Consensus result for block #{proposal.block.index}: {consensus_result}")
        logger.info(f"📊 Votes received: {len(proposal.votes)}")
        
        return consensus_result
    
    async def _broadcast_block_proposal(self, proposal: BlockProposal):
        """Broadcast block proposal to all validators"""
        proposal_message = {
            'action': 'block_proposal',
            'block': {
                'index': proposal.block.index,
                'previous_hash': proposal.block.previous_hash,
                'timestamp': proposal.block.timestamp,
                'transactions': [
                    {
                        'from_address': tx.from_address,
                        'to_address': tx.to_address,
                        'amount': str(tx.amount),
                        'fee': str(tx.fee),
                        'timestamp': tx.timestamp,
                        'transaction_type': tx.transaction_type,
                        'memo': tx.memo
                    }
                    for tx in proposal.block.transactions
                ],
                'validator_nodes': proposal.block.validator_nodes,
                'merkle_root': proposal.block.merkle_root,
                'hash': proposal.block.hash,
                'nonce': proposal.block.nonce
            },
            'proposer_id': proposal.proposer_id,
            'proposal_timestamp': proposal.proposal_timestamp
        }
        
        await self.p2p_network.broadcast_message(
            MessageType.BLOCK,
            proposal_message
        )
        
        logger.debug(f"📡 Block proposal broadcasted to network")
    
    async def _validate_block_proposal(self, proposal: BlockProposal) -> bool:
        """Validate a block proposal using AI capabilities"""
        try:
            # Simulate AI validation process
            logger.debug(f"🤖 AI validating block #{proposal.block.index}...")
            
            # Basic validation checks
            if proposal.block.index != self.blockchain.get_latest_block().index + 1:
                logger.warning("Invalid block index")
                return False
            
            if proposal.block.previous_hash != self.blockchain.get_latest_block().hash:
                logger.warning("Invalid previous hash")
                return False
            
            # Validate transactions
            for tx in proposal.block.transactions:
                if not await self._validate_transaction(tx):
                    logger.warning(f"Invalid transaction: {tx}")
                    return False
            
            # Simulate AI processing time (should be <300ms for real AI)
            await asyncio.sleep(0.1)
            
            logger.debug(f"✅ Block #{proposal.block.index} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating block proposal: {e}")
            return False
    
    async def _validate_transaction(self, transaction: Transaction) -> bool:
        """Validate a single transaction"""
        try:
            # Basic transaction validation
            if transaction.amount < 0:
                return False
            
            if transaction.fee < 0:
                return False
            
            # For reward transactions, skip balance checks
            if transaction.transaction_type == "MINING_REWARD":
                return True
            
            # TODO: Add balance validation, signature verification, etc.
            return True
            
        except Exception as e:
            logger.error(f"Error validating transaction: {e}")
            return False
    
    async def _check_consensus_reached(self, proposal: BlockProposal) -> bool:
        """Check if consensus threshold has been reached"""
        if len(proposal.votes) < 2:  # Need at least 2 votes (minimum network)
            return False
        
        # Calculate total reputation of voting nodes
        total_reputation = sum(vote.reputation for vote in proposal.votes.values())
        approve_reputation = sum(
            vote.reputation for vote in proposal.votes.values() if vote.vote
        )
        
        # Check if we have 66% consensus
        if total_reputation > 0:
            consensus_percentage = approve_reputation / total_reputation
            return consensus_percentage >= self.consensus_threshold
        
        return False
    
    async def _calculate_consensus_result(self, proposal: BlockProposal) -> bool:
        """Calculate final consensus result"""
        if len(proposal.votes) == 0:
            return False
        
        # Calculate reputation-weighted consensus
        total_reputation = sum(vote.reputation for vote in proposal.votes.values())
        approve_reputation = sum(
            vote.reputation for vote in proposal.votes.values() if vote.vote
        )
        
        if total_reputation == 0:
            return False
        
        consensus_percentage = approve_reputation / total_reputation
        
        logger.info(f"📊 Consensus calculation:")
        logger.info(f"   Total reputation: {total_reputation}")
        logger.info(f"   Approve reputation: {approve_reputation}")
        logger.info(f"   Consensus percentage: {consensus_percentage * 100:.1f}%")
        logger.info(f"   Required threshold: {self.consensus_threshold * 100}%")
        
        return consensus_percentage >= self.consensus_threshold
    
    async def _broadcast_new_block(self, block: Block):
        """Broadcast newly created block to network"""
        block_message = {
            'action': 'new_block',
            'block': {
                'index': block.index,
                'previous_hash': block.previous_hash,
                'timestamp': block.timestamp,
                'transactions': [
                    {
                        'from_address': tx.from_address,
                        'to_address': tx.to_address,
                        'amount': str(tx.amount),
                        'fee': str(tx.fee),
                        'timestamp': tx.timestamp,
                        'transaction_type': tx.transaction_type,
                        'memo': tx.memo
                    }
                    for tx in block.transactions
                ],
                'validator_nodes': block.validator_nodes,
                'merkle_root': block.merkle_root,
                'hash': block.hash,
                'nonce': block.nonce
            }
        }
        
        await self.p2p_network.broadcast_message(
            MessageType.BLOCK,
            block_message
        )
        
        logger.info(f"📡 New block #{block.index} broadcasted to network")
    
    async def _handle_block_message(self, message: P2PMessage):
        """Handle incoming block messages"""
        try:
            payload = message.payload
            action = payload.get('action')
            
            if action == 'block_proposal':
                await self._handle_block_proposal(message)
            elif action == 'new_block':
                await self._handle_new_block(message)
            
        except Exception as e:
            logger.error(f"Error handling block message: {e}")
    
    async def _handle_block_proposal(self, message: P2PMessage):
        """Handle incoming block proposal"""
        try:
            payload = message.payload
            block_data = payload['block']
            
            # Reconstruct block from message
            transactions = []
            for tx_data in block_data['transactions']:
                tx = Transaction(
                    from_address=tx_data['from_address'],
                    to_address=tx_data['to_address'],
                    amount=Decimal(tx_data['amount']),
                    fee=Decimal(tx_data['fee']),
                    timestamp=tx_data['timestamp'],
                    transaction_type=tx_data['transaction_type'],
                    memo=tx_data['memo']
                )
                transactions.append(tx)
            
            block = Block(
                index=block_data['index'],
                previous_hash=block_data['previous_hash'],
                timestamp=block_data['timestamp'],
                transactions=transactions,
                validator_nodes=block_data['validator_nodes'],
                nonce=block_data['nonce']
            )
            block.merkle_root = block_data['merkle_root']
            block.hash = block_data['hash']
            
            # Validate and vote on proposal
            vote = await self._validate_block_proposal(BlockProposal(
                block=block,
                proposer_id=payload['proposer_id'],
                proposal_timestamp=payload['proposal_timestamp'],
                votes={}
            ))
            
            # Send vote back to proposer
            vote_message = {
                'action': 'consensus_vote',
                'block_hash': block.hash,
                'vote': vote,
                'voter_id': self.node_id,
                'reputation': str(self.validator_nodes.get(self.node_id, ValidatorNode(
                    node_id=self.node_id,
                    reputation=Decimal('100.0'),
                    last_validation=time.time(),
                    total_validations=0,
                    validator_address="",
                    user_reward_address=""
                )).reputation),
                'timestamp': time.time()
            }
            
            await self.p2p_network.send_message_to_peer(
                message.sender_id,
                P2PMessage(
                    message_type=MessageType.CHALLENGE,
                    sender_id=self.node_id,
                    recipient_id=message.sender_id,
                    payload=vote_message,
                    timestamp=time.time(),
                    signature=""
                )
            )
            
            logger.debug(f"🗳️  Voted {vote} on block #{block.index} from {message.sender_id}")
            
        except Exception as e:
            logger.error(f"Error handling block proposal: {e}")
    
    async def _handle_new_block(self, message: P2PMessage):
        """Handle incoming new block"""
        try:
            payload = message.payload
            block_data = payload['block']
            
            # Reconstruct block
            transactions = []
            for tx_data in block_data['transactions']:
                tx = Transaction(
                    from_address=tx_data['from_address'],
                    to_address=tx_data['to_address'],
                    amount=Decimal(tx_data['amount']),
                    fee=Decimal(tx_data['fee']),
                    timestamp=tx_data['timestamp'],
                    transaction_type=tx_data['transaction_type'],
                    memo=tx_data['memo']
                )
                transactions.append(tx)
            
            block = Block(
                index=block_data['index'],
                previous_hash=block_data['previous_hash'],
                timestamp=block_data['timestamp'],
                transactions=transactions,
                validator_nodes=block_data['validator_nodes'],
                nonce=block_data['nonce']
            )
            block.merkle_root = block_data['merkle_root']
            block.hash = block_data['hash']
            
            # Validate and add block if valid
            if await self._validate_received_block(block):
                self.blockchain.add_block(block)
                self.last_block_time = time.time()
                
                # Remove processed transactions from pending
                self._remove_processed_transactions(block.transactions)
                
                logger.info(f"✅ Received and added block #{block.index} from network")
            else:
                logger.warning(f"❌ Rejected invalid block #{block.index} from network")
            
        except Exception as e:
            logger.error(f"Error handling new block: {e}")
    
    async def _validate_received_block(self, block: Block) -> bool:
        """Validate a block received from the network"""
        try:
            # Check if block is next in sequence
            latest_block = self.blockchain.get_latest_block()
            if block.index != latest_block.index + 1:
                logger.warning(f"Block index mismatch: expected {latest_block.index + 1}, got {block.index}")
                return False
            
            if block.previous_hash != latest_block.hash:
                logger.warning(f"Previous hash mismatch")
                return False
            
            # Validate transactions
            for tx in block.transactions:
                if not await self._validate_transaction(tx):
                    logger.warning(f"Invalid transaction in received block")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating received block: {e}")
            return False
    
    def _remove_processed_transactions(self, processed_transactions: List[Transaction]):
        """Remove processed transactions from pending list"""
        # Create a set of processed transaction signatures for fast lookup
        processed_sigs = set()
        for tx in processed_transactions:
            # Create a simple signature based on transaction data
            sig = f"{tx.from_address}:{tx.to_address}:{tx.amount}:{tx.timestamp}"
            processed_sigs.add(sig)
        
        # Filter out processed transactions
        remaining_transactions = []
        for tx in self.pending_transactions:
            sig = f"{tx.from_address}:{tx.to_address}:{tx.amount}:{tx.timestamp}"
            if sig not in processed_sigs:
                remaining_transactions.append(tx)
        
        removed_count = len(self.pending_transactions) - len(remaining_transactions)
        self.pending_transactions = remaining_transactions
        
        if removed_count > 0:
            logger.debug(f"🗑️  Removed {removed_count} processed transactions from pending")
    
    async def _handle_transaction_message(self, message: P2PMessage):
        """Handle incoming transaction messages"""
        try:
            payload = message.payload
            
            # Reconstruct transaction
            tx = Transaction(
                from_address=payload['from_address'],
                to_address=payload['to_address'],
                amount=Decimal(payload['amount']),
                fee=Decimal(payload['fee']),
                timestamp=payload['timestamp'],
                transaction_type=payload.get('transaction_type', 'TRANSFER'),
                memo=payload.get('memo', '')
            )
            
            # Validate and add to pending
            if await self._validate_transaction(tx):
                self.pending_transactions.append(tx)
                logger.info(f"📥 Added transaction to pending: {tx.amount} PRGLD from {tx.from_address} to {tx.to_address}")
            else:
                logger.warning(f"❌ Rejected invalid transaction from {message.sender_id}")
            
        except Exception as e:
            logger.error(f"Error handling transaction message: {e}")
    
    async def _handle_consensus_vote(self, message: P2PMessage):
        """Handle consensus vote messages"""
        try:
            payload = message.payload
            
            if payload.get('action') == 'consensus_vote' and self.current_proposal:
                vote = ConsensusVote(
                    node_id=payload['voter_id'],
                    block_hash=payload['block_hash'],
                    vote=payload['vote'],
                    reputation=Decimal(payload['reputation']),
                    timestamp=payload['timestamp'],
                    signature=""
                )
                
                # Add vote to current proposal
                if vote.block_hash == self.current_proposal.block.hash:
                    self.current_proposal.votes[vote.node_id] = vote
                    logger.debug(f"🗳️  Received vote from {vote.node_id}: {vote.vote}")
            
        except Exception as e:
            logger.error(f"Error handling consensus vote: {e}")
    
    async def _handle_fee_distribution_update(self, message: P2PMessage):
        """Handle incoming fee distribution update messages"""
        try:
            payload = message.payload
            
            if payload.get('action') == 'fee_distribution_update':
                new_distribution = {
                    'burn': Decimal(payload['distribution']['burn']),
                    'developer': Decimal(payload['distribution']['developer']),
                    'liquidity': Decimal(payload['distribution']['liquidity'])
                }
                block_number = payload['block_number']
                halving_number = payload['halving_number']
                
                # Validate the distribution
                total = sum(new_distribution.values())
                if abs(total - Decimal('1.0')) > Decimal('0.001'):
                    logger.warning(f"❌ Invalid fee distribution received: percentages don't sum to 100%")
                    return
                
                # Update local fee manager and blockchain
                self.halving_manager.fee_manager.current_burn = new_distribution['burn']
                self.halving_manager.fee_manager.current_developer = new_distribution['developer']
                self.halving_manager.fee_manager.current_liquidity = new_distribution['liquidity']
                
                self.blockchain.update_fee_distribution(new_distribution)
                
                # Save updated state to disk
                self._save_fee_distribution_state()
                
                logger.info(f"📊 Fee distribution updated from network: "
                           f"Burn: {new_distribution['burn']*100}%, "
                           f"Dev: {new_distribution['developer']*100}%, "
                           f"Pool: {new_distribution['liquidity']*100}% "
                           f"(Halving {halving_number} at block {block_number})")
            
        except Exception as e:
            logger.error(f"Error handling fee distribution update: {e}")
    
    async def _broadcast_fee_distribution_update(self, new_distribution: Dict[str, Decimal], block_number: int):
        """Broadcast fee distribution update to all network nodes"""
        try:
            halving_number = self.halving_manager.halvings_occurred
            
            message = P2PMessage(
                message_type=MessageType.FEE_DISTRIBUTION_UPDATE,
                sender_id=self.node_id,
                payload={
                    'action': 'fee_distribution_update',
                    'distribution': {
                        'burn': str(new_distribution['burn']),
                        'developer': str(new_distribution['developer']),
                        'liquidity': str(new_distribution['liquidity'])
                    },
                    'block_number': block_number,
                    'halving_number': halving_number,
                    'timestamp': time.time()
                }
            )
            
            await self.p2p_network.broadcast_message(message)
            
            logger.info(f"📡 Fee distribution update broadcasted to network: "
                       f"Halving {halving_number} at block {block_number}")
            
        except Exception as e:
            logger.error(f"Error broadcasting fee distribution update: {e}")
    
    def _load_fee_distribution_state_on_startup(self):
        """Load fee distribution state on node startup"""
        try:
            import os
            
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Try to load existing state
            success = self.blockchain.load_fee_distribution_state()
            if success:
                logger.info("📂 Fee distribution state loaded from previous session")
                
                # Validate consistency
                if not self.blockchain.validate_fee_distribution_consistency():
                    logger.warning("⚠️ Fee distribution state inconsistency detected, resetting to defaults")
                    self.halving_manager.fee_manager.reset_to_initial()
                    self.blockchain.update_fee_distribution(self.halving_manager.fee_manager.get_current_distribution())
            else:
                logger.info("📋 No previous fee distribution state found, using defaults")
                
        except Exception as e:
            logger.error(f"❌ Error loading fee distribution state on startup: {e}")
    
    def _save_fee_distribution_state(self):
        """Save current fee distribution state"""
        try:
            success = self.blockchain.save_fee_distribution_state()
            if success:
                logger.debug("💾 Fee distribution state saved")
            else:
                logger.warning("⚠️ Failed to save fee distribution state")
                
        except Exception as e:
            logger.error(f"❌ Error saving fee distribution state: {e}")
    
    async def _monitor_validators(self):
        """Monitor validator nodes and update their status"""
        while True:
            try:
                current_time = time.time()
                
                # Update validator activity based on P2P connections
                connected_peers = {peer.peer_id for peer in self.p2p_network.get_peer_list()}
                
                for node_id, validator in self.validator_nodes.items():
                    # Mark as inactive if not connected
                    if node_id != self.node_id and node_id not in connected_peers:
                        if validator.is_active:
                            logger.warning(f"⚠️  Validator {node_id} marked as inactive (disconnected)")
                            validator.is_active = False
                    else:
                        if not validator.is_active:
                            logger.info(f"✅ Validator {node_id} marked as active (reconnected)")
                            validator.is_active = True
                            validator.last_validation = current_time
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring validators: {e}")
                await asyncio.sleep(10)
    
    def add_transaction(self, transaction: Transaction):
        """Add a transaction to the pending pool"""
        self.pending_transactions.append(transaction)
        logger.info(f"📝 Transaction added to pending pool: {transaction.amount} PRGLD")
    
    def get_consensus_status(self) -> Dict:
        """Get current consensus status"""
        return {
            'is_mining': self.is_mining,
            'validator_count': len(self.validator_nodes),
            'active_validators': len([v for v in self.validator_nodes.values() if v.is_active]),
            'pending_transactions': len(self.pending_transactions),
            'last_block_time': self.last_block_time,
            'time_to_next_block': max(0, self.block_interval - (time.time() - self.last_block_time)),
            'current_block_reward': str(self.halving_manager.current_reward),
            'next_halving_block': self.halving_manager.next_halving_block,
            'consensus_threshold': str(self.consensus_threshold * 100) + '%'
        }