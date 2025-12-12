#!/usr/bin/env python3
"""
Bootstrap Manager for PlayerGold Multi-Node Network

Manages the initial bootstrap process where exactly 2 pioneer nodes
create the genesis block and establish the distributed network.

Key Features:
- Detects when exactly 2 AI nodes are connected
- Creates genesis block with system addresses (pool, burn, developer)
- Establishes initial reputation (100%) for genesis pioneers
- Sends developer address recovery data via email
- Manages genesis privileges for testnet reset capabilities
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from decimal import Decimal
from datetime import datetime
# Email imports commented out due to import issues
# import smtplib
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart
import hashlib
import secrets
from pathlib import Path

from ..blockchain.enhanced_blockchain import EnhancedBlockchain, Block, Transaction
from ..p2p.network import P2PNetwork, MessageType
from ..crypto.wallet import generate_keypair, derive_address

logger = logging.getLogger(__name__)


@dataclass
class GenesisConfig:
    """Configuration for genesis block creation"""
    liquidity_pool_initial: Decimal = Decimal('1024000000')  # 1,024M PRGLD
    initial_block_reward: Decimal = Decimal('1024')  # 1,024 PRGLD per block
    halving_interval: int = 100000  # Every 100,000 blocks
    developer_email: str = "mfp_zollkron@yahoo.com"
    
    # Fee distribution percentages
    developer_fee_percentage: Decimal = Decimal('0.30')  # 30%
    liquidity_fee_percentage: Decimal = Decimal('0.10')  # 10%
    burn_fee_percentage: Decimal = Decimal('0.60')  # 60%


@dataclass
class SystemAddresses:
    """System addresses created during genesis"""
    liquidity_pool: str
    burn_address: str
    developer_address: str
    developer_private_key: str
    developer_mnemonic: str


@dataclass
class PioneerNode:
    """Information about a pioneer node"""
    node_id: str
    ai_model_hash: str
    validator_address: str  # Internal address for node operations
    user_reward_address: str  # Personal address for receiving rewards
    reputation: Decimal = Decimal('100.0')
    is_genesis_pioneer: bool = True
    connected_at: float = 0.0


class BootstrapManager:
    """
    Manages the bootstrap process for creating the initial blockchain
    when exactly 2 pioneer AI nodes connect to the network.
    """
    
    def __init__(self, 
                 p2p_network: P2PNetwork,
                 blockchain: EnhancedBlockchain,
                 network_type: str = "testnet"):
        self.p2p_network = p2p_network
        self.blockchain = blockchain
        self.network_type = network_type
        self.config = GenesisConfig()
        
        # Bootstrap state
        self.pioneer_nodes: Dict[str, PioneerNode] = {}
        self.genesis_created = False
        self.system_addresses: Optional[SystemAddresses] = None
        self.waiting_for_pioneers = True
        
        # Register P2P message handlers
        self.p2p_network.register_message_handler(
            MessageType.PEER_DISCOVERY, 
            self._handle_peer_discovery
        )
        self.p2p_network.register_message_handler(
            MessageType.AI_NODE_DISCOVERY, 
            self._handle_ai_node_discovery
        )
        
        logger.info(f"Bootstrap Manager initialized for {network_type}")
        logger.info(f"Waiting for exactly 2 pioneer AI nodes to create genesis block...")
    
    async def _register_self_as_ai_node(self):
        """Register ourselves as an AI node"""
        try:
            # Get our node ID from the P2P network
            our_node_id = self.p2p_network.node_id
            
            # Create our pioneer node entry
            pioneer = PioneerNode(
                node_id=our_node_id,
                ai_model_hash=f"ai_model_{our_node_id}_{int(time.time())}",
                validator_address=f"PGval_{our_node_id}",
                user_reward_address=f"PGuser_{our_node_id}",
                connected_at=time.time()
            )
            
            self.pioneer_nodes[our_node_id] = pioneer
            
            logger.info(f"🤖 Registered self as AI node: {our_node_id}")
            logger.info(f"   Model hash: {pioneer.ai_model_hash[:16]}...")
            logger.info(f"   Validator: {pioneer.validator_address}")
            logger.info(f"   Reward addr: {pioneer.user_reward_address}")
            
        except Exception as e:
            logger.error(f"Error registering self as AI node: {e}")
    
    async def start(self):
        """Start the bootstrap manager"""
        logger.info("🏗️  Starting Bootstrap Manager...")
        
        # Check if genesis block already exists
        if self.blockchain.get_latest_block().index > 0:
            logger.info("Genesis block already exists, skipping bootstrap")
            self.genesis_created = True
            self.waiting_for_pioneers = False
            return
        
        # Register ourselves as an AI node
        await self._register_self_as_ai_node()
        
        # Start monitoring for pioneer nodes
        asyncio.create_task(self._monitor_pioneer_nodes())
        
        logger.info("✅ Bootstrap Manager started - waiting for pioneer nodes")
    
    async def _handle_peer_discovery(self, message):
        """Handle peer discovery messages to identify AI nodes"""
        try:
            payload = message.payload
            node_id = payload.get('node_id')
            
            logger.info(f"📡 Received peer discovery from {node_id}: {payload}")
            
            if not node_id or node_id in self.pioneer_nodes:
                logger.debug(f"Skipping {node_id}: already known or invalid")
                return
            
            # Check if this is an AI node
            if payload.get('is_ai_node', False):
                ai_model_hash = payload.get('ai_model_hash')
                validator_address = payload.get('validator_address')
                user_reward_address = payload.get('user_reward_address')
                
                if ai_model_hash and validator_address and user_reward_address:
                    pioneer = PioneerNode(
                        node_id=node_id,
                        ai_model_hash=ai_model_hash,
                        validator_address=validator_address,
                        user_reward_address=user_reward_address,
                        connected_at=time.time()
                    )
                    
                    self.pioneer_nodes[node_id] = pioneer
                    
                    logger.info(f"🤖 Pioneer AI node discovered: {node_id}")
                    logger.info(f"   Model hash: {ai_model_hash[:16]}...")
                    logger.info(f"   Validator: {validator_address}")
                    logger.info(f"   Reward addr: {user_reward_address}")
                    
                    # Check if we have exactly 2 pioneers
                    await self._check_genesis_conditions()
                else:
                    logger.warning(f"❌ AI node {node_id} missing required fields")
            else:
                logger.debug(f"Node {node_id} is not marked as AI node")
        
        except Exception as e:
            logger.error(f"Error handling peer discovery: {e}")
    
    async def _handle_ai_node_discovery(self, message):
        """Handle AI node discovery messages to identify pioneer nodes"""
        try:
            payload = message.payload
            node_id = payload.get('node_id')
            
            logger.info(f"🤖 Received AI node discovery from {node_id}: {payload}")
            
            if not node_id or node_id in self.pioneer_nodes:
                logger.debug(f"Skipping {node_id}: already known or invalid")
                return
            
            # Check if this is an AI node
            if payload.get('is_ai_node', False):
                ai_model_hash = payload.get('ai_model_hash')
                validator_address = payload.get('validator_address')
                user_reward_address = payload.get('user_reward_address')
                
                if ai_model_hash and validator_address and user_reward_address:
                    pioneer = PioneerNode(
                        node_id=node_id,
                        ai_model_hash=ai_model_hash,
                        validator_address=validator_address,
                        user_reward_address=user_reward_address,
                        connected_at=time.time()
                    )
                    
                    self.pioneer_nodes[node_id] = pioneer
                    
                    logger.info(f"🎯 Pioneer AI node registered: {node_id}")
                    logger.info(f"   Model hash: {ai_model_hash[:16]}...")
                    logger.info(f"   Validator: {validator_address}")
                    logger.info(f"   Reward addr: {user_reward_address}")
                    
                    # Check if we have exactly 2 pioneers
                    await self._check_genesis_conditions()
                else:
                    logger.warning(f"❌ AI node {node_id} missing required fields")
            else:
                logger.debug(f"Node {node_id} is not marked as AI node")
        
        except Exception as e:
            logger.error(f"Error handling AI node discovery: {e}")
    
    async def _monitor_pioneer_nodes(self):
        """Monitor pioneer nodes and trigger genesis creation"""
        while self.waiting_for_pioneers and not self.genesis_created:
            try:
                # Clean up disconnected pioneers
                current_time = time.time()
                disconnected = []
                
                for node_id, pioneer in self.pioneer_nodes.items():
                    # Don't remove ourselves - we're always "connected"
                    if node_id == self.p2p_network.node_id:
                        continue
                    
                    # Check if node is still connected (timeout after 60 seconds)
                    if current_time - pioneer.connected_at > 60:
                        if node_id not in [peer.peer_id for peer in self.p2p_network.get_peer_list()]:
                            disconnected.append(node_id)
                            logger.debug(f"🔍 Node {node_id} marked for disconnection (timeout: {current_time - pioneer.connected_at:.1f}s)")
                
                for node_id in disconnected:
                    logger.warning(f"🚫 Pioneer node {node_id} disconnected and removed")
                    del self.pioneer_nodes[node_id]
                
                # Check genesis conditions
                await self._check_genesis_conditions()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in pioneer monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _check_genesis_conditions(self):
        """Check if conditions are met to create genesis block"""
        if self.genesis_created or not self.waiting_for_pioneers:
            return
        
        pioneer_count = len(self.pioneer_nodes)
        
        # Debug logging
        logger.debug(f"🔍 Pioneer nodes in registry: {list(self.pioneer_nodes.keys())}")
        logger.debug(f"🔍 Connected peers: {[peer.peer_id for peer in self.p2p_network.get_peer_list()]}")
        
        if pioneer_count == 2:
            logger.info("🎯 Exactly 2 pioneer AI nodes detected!")
            logger.info("🏗️  Initiating genesis block creation...")
            
            await self._create_genesis_block()
            
        elif pioneer_count > 2:
            logger.warning(f"⚠️  Too many pioneer nodes ({pioneer_count}), need exactly 2")
            # Keep only the first 2 pioneers
            pioneer_list = list(self.pioneer_nodes.items())
            pioneer_list.sort(key=lambda x: x[1].connected_at)
            
            # Remove excess pioneers
            for node_id, _ in pioneer_list[2:]:
                logger.info(f"Removing excess pioneer: {node_id}")
                del self.pioneer_nodes[node_id]
        
        else:
            logger.info(f"⏳ Waiting for more pioneers ({pioneer_count}/2)")
    
    async def _create_genesis_block(self):
        """Create the genesis block with system initialization"""
        try:
            logger.info("=" * 60)
            logger.info("🏗️  CREATING GENESIS BLOCK")
            logger.info("=" * 60)
            
            # Generate system addresses
            self.system_addresses = await self._generate_system_addresses()
            
            # Create genesis transactions
            genesis_transactions = await self._create_genesis_transactions()
            
            # Create genesis block
            genesis_block = Block(
                index=0,
                previous_hash="0" * 64,
                timestamp=time.time(),
                transactions=genesis_transactions,
                validator_nodes=list(self.pioneer_nodes.keys()),
                nonce=0
            )
            
            # Calculate merkle root and hash
            genesis_block.merkle_root = self.blockchain.calculate_merkle_root(genesis_transactions)
            genesis_block.hash = self.blockchain.calculate_block_hash(genesis_block)
            
            # Add genesis block to blockchain
            self.blockchain.add_block(genesis_block)
            
            # Send developer recovery email
            await self._send_developer_recovery_email()
            
            # Mark genesis as created
            self.genesis_created = True
            self.waiting_for_pioneers = False
            
            # Broadcast genesis creation to network
            await self._broadcast_genesis_created()
            
            # Schedule first reward distribution for block 1
            await self._schedule_first_rewards()
            
            logger.info("🎉 GENESIS BLOCK CREATED SUCCESSFULLY!")
            logger.info(f"📦 Block hash: {genesis_block.hash}")
            logger.info(f"💰 Liquidity pool: {self.system_addresses.liquidity_pool}")
            logger.info(f"🔥 Burn address: {self.system_addresses.burn_address}")
            logger.info(f"👨‍💻 Developer address: {self.system_addresses.developer_address}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Failed to create genesis block: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _generate_system_addresses(self) -> SystemAddresses:
        """Generate system addresses for liquidity pool, burn, and developer"""
        logger.info("🔑 Generating system addresses...")
        
        # Generate liquidity pool address
        pool_keypair = generate_keypair()
        liquidity_pool = derive_address(pool_keypair['public_key'])
        
        # Generate burn address (deterministic)
        burn_seed = hashlib.sha256(b"PLAYERGOLD_BURN_ADDRESS").digest()
        burn_address = "PGburn" + burn_seed.hex()[:58]  # 64 char address
        
        # Generate developer address
        dev_keypair = generate_keypair()
        developer_address = derive_address(dev_keypair['public_key'])
        developer_private_key = dev_keypair['private_key']
        developer_mnemonic = dev_keypair.get('mnemonic', '')
        
        logger.info(f"💰 Liquidity pool: {liquidity_pool}")
        logger.info(f"🔥 Burn address: {burn_address}")
        logger.info(f"👨‍💻 Developer address: {developer_address}")
        
        return SystemAddresses(
            liquidity_pool=liquidity_pool,
            burn_address=burn_address,
            developer_address=developer_address,
            developer_private_key=developer_private_key,
            developer_mnemonic=developer_mnemonic
        )
    
    async def _create_genesis_transactions(self) -> List[Transaction]:
        """Create initial transactions for genesis block"""
        transactions = []
        
        # Initialize liquidity pool
        pool_init_tx = Transaction(
            from_address="GENESIS",
            to_address=self.system_addresses.liquidity_pool,
            amount=self.config.liquidity_pool_initial,
            fee=Decimal('0'),
            timestamp=time.time(),
            transaction_type="GENESIS_INIT",
            memo=f"Initialize liquidity pool - {self.config.liquidity_pool_initial} PRGLD"
        )
        transactions.append(pool_init_tx)
        
        logger.info(f"💰 Liquidity pool initialized: {self.config.liquidity_pool_initial} PRGLD")
        
        return transactions
    
    async def _send_developer_recovery_email(self):
        """Send developer address recovery data via email"""
        try:
            logger.info("📧 Sending developer recovery email...")
            
            # Prepare email content
            subject = "PlayerGold - Developer Address Recovery Data"
            
            body = f"""
PlayerGold Developer Address - Recovery Information

Network: {self.network_type.upper()}
Generated: {datetime.utcnow().isoformat()}

DEVELOPER ADDRESS INFORMATION:
Address: {self.system_addresses.developer_address}
Private Key: {self.system_addresses.developer_private_key}
Mnemonic: {self.system_addresses.developer_mnemonic}

PURPOSE:
This address will receive 30% of all transaction fees for network maintenance.

FEE DISTRIBUTION:
- Developer (maintenance): 30%
- Liquidity pool: 10%
- Token burn: 60%

IMPORTANT SECURITY NOTES:
- Keep this information secure and private
- You can import this wallet using either the private key or mnemonic phrase
- This address is automatically configured in the genesis block
- Fees will be distributed automatically to this address

SYSTEM ADDRESSES:
- Liquidity Pool: {self.system_addresses.liquidity_pool}
- Burn Address: {self.system_addresses.burn_address}
- Developer Address: {self.system_addresses.developer_address}

GENESIS PIONEERS:
"""
            
            for node_id, pioneer in self.pioneer_nodes.items():
                body += f"- {node_id}: {pioneer.user_reward_address}\n"
            
            body += f"""
NETWORK CONFIGURATION:
- Initial block reward: {self.config.initial_block_reward} PRGLD
- Halving interval: {self.config.halving_interval} blocks
- Network type: {self.network_type}

This email contains sensitive information. Please store it securely.
"""
            
            # For now, just log the email content (implement actual email sending later)
            logger.info("📧 Developer recovery email content prepared:")
            logger.info(f"To: {self.config.developer_email}")
            logger.info(f"Subject: {subject}")
            logger.info("Body content logged to secure location")
            
            # Save to secure file as backup
            recovery_file = Path("data/developer_recovery.json")
            recovery_file.parent.mkdir(exist_ok=True)
            
            recovery_data = {
                'address': self.system_addresses.developer_address,
                'private_key': self.system_addresses.developer_private_key,
                'mnemonic': self.system_addresses.developer_mnemonic,
                'email': self.config.developer_email,
                'network': self.network_type,
                'generated_at': datetime.utcnow().isoformat(),
                'system_addresses': asdict(self.system_addresses)
            }
            
            with open(recovery_file, 'w') as f:
                json.dump(recovery_data, f, indent=2, default=str)
            
            logger.info(f"💾 Recovery data saved to: {recovery_file}")
            logger.info("✅ Developer recovery email prepared successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to send developer recovery email: {e}")
            # Don't fail genesis creation if email fails
    
    async def _broadcast_genesis_created(self):
        """Broadcast genesis creation to all connected nodes"""
        try:
            genesis_message = {
                'genesis_block_hash': self.blockchain.get_latest_block().hash,
                'system_addresses': asdict(self.system_addresses),
                'pioneer_nodes': {
                    node_id: {
                        'validator_address': pioneer.validator_address,
                        'user_reward_address': pioneer.user_reward_address,
                        'reputation': str(pioneer.reputation)
                    }
                    for node_id, pioneer in self.pioneer_nodes.items()
                },
                'network_type': self.network_type,
                'timestamp': time.time()
            }
            
            await self.p2p_network.broadcast_message(
                MessageType.BLOCK,
                genesis_message
            )
            
            logger.info("📡 Genesis creation broadcasted to network")
            
        except Exception as e:
            logger.error(f"Error broadcasting genesis creation: {e}")
    
    async def _schedule_first_rewards(self):
        """Schedule reward distribution for the first block (block 1)"""
        try:
            logger.info("⏰ Scheduling first reward distribution for block 1...")
            
            # Calculate reward for each pioneer (split equally)
            reward_per_pioneer = self.config.initial_block_reward / 2
            
            # Create reward transactions for block 1
            reward_transactions = []
            
            for node_id, pioneer in self.pioneer_nodes.items():
                reward_tx = Transaction(
                    from_address=self.system_addresses.liquidity_pool,
                    to_address=pioneer.user_reward_address,
                    amount=reward_per_pioneer,
                    fee=Decimal('0'),
                    timestamp=time.time(),
                    transaction_type="MINING_REWARD",
                    memo=f"Genesis validation reward - Block 0"
                )
                reward_transactions.append(reward_tx)
                
                logger.info(f"🎁 Scheduled reward: {reward_per_pioneer} PRGLD → {pioneer.user_reward_address}")
            
            # Store pending rewards for block 1
            # This will be processed when the first regular block is mined
            self.blockchain.pending_reward_transactions = reward_transactions
            
            logger.info("✅ First rewards scheduled successfully")
            
        except Exception as e:
            logger.error(f"Error scheduling first rewards: {e}")
    
    def get_genesis_status(self) -> Dict:
        """Get current genesis/bootstrap status"""
        return {
            'genesis_created': self.genesis_created,
            'waiting_for_pioneers': self.waiting_for_pioneers,
            'pioneer_count': len(self.pioneer_nodes),
            'pioneers': {
                node_id: {
                    'validator_address': pioneer.validator_address,
                    'user_reward_address': pioneer.user_reward_address,
                    'reputation': str(pioneer.reputation),
                    'connected_at': pioneer.connected_at
                }
                for node_id, pioneer in self.pioneer_nodes.items()
            },
            'system_addresses': asdict(self.system_addresses) if self.system_addresses else None,
            'network_type': self.network_type
        }
    
    def is_genesis_pioneer(self, node_id: str) -> bool:
        """Check if a node is a genesis pioneer"""
        return node_id in self.pioneer_nodes
    
    def can_reset_blockchain(self, node_id: str) -> bool:
        """Check if a node can reset the blockchain (testnet only)"""
        if self.network_type != "testnet":
            return False
        
        return self.is_genesis_pioneer(node_id)
    
    async def reset_blockchain(self, requesting_node_id: str) -> Dict:
        """Reset the blockchain (testnet only, genesis pioneers only)"""
        if not self.can_reset_blockchain(requesting_node_id):
            return {
                'success': False,
                'reason': f'Node {requesting_node_id} does not have reset privileges',
                'network_type': self.network_type
            }
        
        try:
            logger.warning("🚨 BLOCKCHAIN RESET initiated by genesis pioneer")
            logger.warning(f"🗑️  Requesting node: {requesting_node_id}")
            
            # Reset blockchain state
            self.blockchain.reset()
            
            # Reset bootstrap state
            self.genesis_created = False
            self.waiting_for_pioneers = True
            self.system_addresses = None
            self.pioneer_nodes.clear()
            
            # Broadcast reset to network
            await self.p2p_network.broadcast_message(
                MessageType.SYNC_REQUEST,
                {
                    'action': 'blockchain_reset',
                    'reset_by': requesting_node_id,
                    'timestamp': time.time()
                }
            )
            
            logger.warning("✅ Blockchain reset completed - ready for new genesis")
            
            return {
                'success': True,
                'reason': f'Blockchain reset by genesis pioneer {requesting_node_id}',
                'network_type': self.network_type,
                'reset_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ Blockchain reset failed: {e}")
            return {
                'success': False,
                'reason': f'Reset failed: {str(e)}',
                'network_type': self.network_type
            }