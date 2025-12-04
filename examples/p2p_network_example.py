"""
Example demonstrating P2P network functionality for PlayerGold distributed AI nodes.
Shows how to set up networking, discovery, propagation, and synchronization.
"""

import asyncio
import logging
import time
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.p2p import (
    P2PNetwork, MessageType, P2PMessage,
    MessagePropagator, PropagationStrategy,
    PeerDiscovery, BlockchainSynchronizer
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockBlockchainManager:
    """Mock blockchain manager for the example"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.blocks = []
        self.latest_index = 0
        self.latest_hash = "genesis_hash"
        self.node_reputation = 1.0
        
        # Add genesis block
        genesis_block = {
            'index': 0,
            'hash': 'genesis_hash',
            'previous_hash': '',
            'timestamp': time.time(),
            'merkle_root': 'genesis_merkle',
            'ai_validators': []
        }
        self.blocks.append(genesis_block)
    
    async def get_latest_block_index(self):
        return len(self.blocks) - 1
    
    async def get_latest_block_hash(self):
        return self.blocks[-1]['hash'] if self.blocks else 'genesis_hash'
    
    async def get_blocks_range(self, start_index, end_index):
        return [
            block for block in self.blocks
            if start_index <= block['index'] <= end_index
        ]
    
    async def get_block_by_index(self, index):
        if 0 <= index < len(self.blocks):
            return self.blocks[index]
        return None
    
    async def add_block(self, block):
        self.blocks.append(block)
        logger.info(f"Node {self.node_id}: Added block {block['index']}")
    
    async def replace_block(self, block):
        index = block['index']
        if 0 <= index < len(self.blocks):
            self.blocks[index] = block
            logger.info(f"Node {self.node_id}: Replaced block {index}")
    
    async def get_node_reputation(self, node_id):
        return self.node_reputation
    
    def create_new_block(self, transactions: list = None) -> Dict[str, Any]:
        """Create a new block for demonstration"""
        if transactions is None:
            transactions = []
        
        new_index = len(self.blocks)
        previous_hash = self.blocks[-1]['hash'] if self.blocks else ''
        
        block = {
            'index': new_index,
            'hash': f'block_hash_{new_index}_{self.node_id}',
            'previous_hash': previous_hash,
            'timestamp': time.time(),
            'merkle_root': f'merkle_{new_index}',
            'transactions': transactions,
            'ai_validators': [self.node_id]
        }
        
        return block


class P2PNode:
    """Complete P2P node with networking, discovery, and synchronization"""
    
    def __init__(self, node_id: str, listen_port: int):
        self.node_id = node_id
        self.listen_port = listen_port
        
        # Initialize components
        self.network = P2PNetwork(node_id, listen_port)
        self.blockchain = MockBlockchainManager(node_id)
        self.propagator = MessagePropagator(self.network)
        self.discovery = PeerDiscovery(node_id, listen_port)
        self.synchronizer = BlockchainSynchronizer(self.network, self.blockchain)
        
        # Register message handlers
        self._register_handlers()
        
        logger.info(f"P2P Node {node_id} initialized on port {listen_port}")
    
    def _register_handlers(self):
        """Register custom message handlers"""
        self.network.register_message_handler(
            MessageType.TRANSACTION, self._handle_transaction
        )
        self.network.register_message_handler(
            MessageType.HEARTBEAT, self._handle_heartbeat
        )
    
    async def start(self):
        """Start all P2P components"""
        try:
            logger.info(f"Starting P2P node {self.node_id}...")
            
            # Start network
            await self.network.start()
            
            # Start propagator
            await self.propagator.start()
            
            # Start discovery
            await self.discovery.start()
            
            # Start synchronizer
            await self.synchronizer.start()
            
            logger.info(f"P2P node {self.node_id} started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start P2P node {self.node_id}: {e}")
            raise
    
    async def stop(self):
        """Stop all P2P components"""
        logger.info(f"Stopping P2P node {self.node_id}...")
        
        await self.synchronizer.stop()
        await self.discovery.stop()
        await self.propagator.stop()
        await self.network.stop()
        
        logger.info(f"P2P node {self.node_id} stopped")
    
    async def connect_to_peer(self, address: str, port: int):
        """Connect to another peer"""
        success = await self.network.connect_to_peer(address, port)
        if success:
            logger.info(f"Node {self.node_id} connected to peer at {address}:{port}")
        else:
            logger.warning(f"Node {self.node_id} failed to connect to {address}:{port}")
        return success
    
    async def create_and_propagate_transaction(self, from_addr: str, to_addr: str, amount: float):
        """Create and propagate a transaction"""
        transaction = {
            'from': from_addr,
            'to': to_addr,
            'amount': amount,
            'timestamp': time.time(),
            'signature': f'sig_{self.node_id}_{time.time()}'
        }
        
        message_id = await self.propagator.propagate_transaction(transaction)
        logger.info(f"Node {self.node_id} propagated transaction {message_id}")
        return message_id
    
    async def create_and_propagate_block(self, transactions: list = None):
        """Create and propagate a new block"""
        block = self.blockchain.create_new_block(transactions)
        await self.blockchain.add_block(block)
        
        message_id = await self.propagator.propagate_block(block)
        logger.info(f"Node {self.node_id} propagated block {block['index']}")
        return message_id
    
    async def _handle_transaction(self, message: P2PMessage):
        """Handle received transaction"""
        transaction = message.payload.get('data', {})
        logger.info(f"Node {self.node_id} received transaction from {message.sender_id}")
        
        # In a real implementation, this would validate and process the transaction
        # For now, just log it
        logger.debug(f"Transaction: {transaction}")
    
    async def _handle_heartbeat(self, message: P2PMessage):
        """Handle heartbeat message"""
        logger.debug(f"Node {self.node_id} received heartbeat from {message.sender_id}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get node status"""
        return {
            'node_id': self.node_id,
            'listen_port': self.listen_port,
            'network_stats': self.network.get_network_stats(),
            'propagation_stats': self.propagator.get_propagation_stats(),
            'discovery_stats': self.discovery.get_discovery_stats(),
            'sync_status': self.synchronizer.get_sync_status(),
            'blockchain_height': len(self.blockchain.blocks),
            'latest_block_hash': self.blockchain.blocks[-1]['hash'] if self.blockchain.blocks else None
        }


async def run_single_node_example():
    """Run a single node example"""
    logger.info("=== Single Node Example ===")
    
    node = P2PNode("node1", 8000)
    
    try:
        await node.start()
        
        # Wait a bit for initialization
        await asyncio.sleep(2)
        
        # Create some transactions
        await node.create_and_propagate_transaction("addr1", "addr2", 100.0)
        await node.create_and_propagate_transaction("addr2", "addr3", 50.0)
        
        # Create a block
        await node.create_and_propagate_block()
        
        # Show status
        status = node.get_status()
        logger.info(f"Node status: {status}")
        
        # Wait a bit more
        await asyncio.sleep(3)
        
    finally:
        await node.stop()


async def run_multi_node_example():
    """Run a multi-node network example"""
    logger.info("=== Multi-Node Network Example ===")
    
    # Create multiple nodes
    nodes = [
        P2PNode("node1", 8001),
        P2PNode("node2", 8002),
        P2PNode("node3", 8003)
    ]
    
    try:
        # Start all nodes
        for node in nodes:
            await node.start()
            await asyncio.sleep(1)  # Stagger startup
        
        # Connect nodes to each other
        await nodes[1].connect_to_peer("127.0.0.1", 8001)  # node2 -> node1
        await nodes[2].connect_to_peer("127.0.0.1", 8001)  # node3 -> node1
        await nodes[2].connect_to_peer("127.0.0.1", 8002)  # node3 -> node2
        
        # Wait for connections to establish
        await asyncio.sleep(3)
        
        # Create transactions from different nodes
        await nodes[0].create_and_propagate_transaction("alice", "bob", 100.0)
        await nodes[1].create_and_propagate_transaction("bob", "charlie", 50.0)
        await nodes[2].create_and_propagate_transaction("charlie", "alice", 25.0)
        
        # Wait for propagation
        await asyncio.sleep(2)
        
        # Create blocks from different nodes
        await nodes[0].create_and_propagate_block()
        await asyncio.sleep(1)
        await nodes[1].create_and_propagate_block()
        
        # Wait for synchronization
        await asyncio.sleep(5)
        
        # Show status of all nodes
        for i, node in enumerate(nodes):
            status = node.get_status()
            logger.info(f"Node {i+1} status:")
            logger.info(f"  Peers: {status['network_stats']['peer_count']}")
            logger.info(f"  Blockchain height: {status['blockchain_height']}")
            logger.info(f"  Messages sent: {status['network_stats']['messages_sent']}")
            logger.info(f"  Messages received: {status['network_stats']['messages_received']}")
            logger.info(f"  Sync state: {status['sync_status']['state']}")
        
    finally:
        # Stop all nodes
        for node in reversed(nodes):
            await node.stop()
            await asyncio.sleep(0.5)


async def run_discovery_example():
    """Run peer discovery example"""
    logger.info("=== Peer Discovery Example ===")
    
    node = P2PNode("discovery_node", 8004)
    
    try:
        await node.start()
        
        # Add some manual peers
        node.discovery.add_manual_peer("127.0.0.1", 8005, "manual_peer1")
        node.discovery.add_manual_peer("192.168.1.100", 8006, "manual_peer2")
        
        # Wait for discovery
        await asyncio.sleep(3)
        
        # Show discovered peers
        discovered_peers = node.discovery.get_discovered_peers()
        logger.info(f"Discovered {len(discovered_peers)} peers:")
        for peer in discovered_peers:
            logger.info(f"  {peer.node_id} at {peer.address}:{peer.port} via {peer.discovery_method}")
        
        # Show discovery stats
        stats = node.discovery.get_discovery_stats()
        logger.info(f"Discovery stats: {stats}")
        
    finally:
        await node.stop()


async def main():
    """Run all examples"""
    try:
        # Run single node example
        await run_single_node_example()
        await asyncio.sleep(2)
        
        # Run multi-node example
        await run_multi_node_example()
        await asyncio.sleep(2)
        
        # Run discovery example
        await run_discovery_example()
        
    except KeyboardInterrupt:
        logger.info("Examples interrupted by user")
    except Exception as e:
        logger.error(f"Error running examples: {e}")


if __name__ == "__main__":
    asyncio.run(main())