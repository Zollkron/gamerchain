"""
Message propagation system for efficient distribution of transactions and blocks.
Implements gossip protocol with flood control and deduplication.
"""

import asyncio
import logging
import time
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from collections import defaultdict, deque

from .network import P2PNetwork, MessageType, P2PMessage

logger = logging.getLogger(__name__)


class PropagationStrategy(Enum):
    """Message propagation strategies"""
    FLOOD = "flood"           # Flood to all peers
    GOSSIP = "gossip"         # Gossip to random subset
    DIRECTED = "directed"     # Send to specific peers


@dataclass
class PropagationConfig:
    """Configuration for message propagation"""
    max_hops: int = 7                    # Maximum hops for message
    gossip_factor: float = 0.5           # Fraction of peers to gossip to
    duplicate_cache_size: int = 10000    # Size of duplicate detection cache
    duplicate_cache_ttl: int = 300       # TTL for duplicate cache entries
    batch_size: int = 100                # Batch size for bulk operations
    retry_attempts: int = 3              # Number of retry attempts
    retry_delay: float = 1.0             # Delay between retries


@dataclass
class MessageMetadata:
    """Metadata for propagated messages"""
    message_id: str
    origin_node: str
    hop_count: int
    timestamp: float
    propagation_strategy: PropagationStrategy
    priority: int = 0  # Higher priority = faster propagation


class MessagePropagator:
    """
    Handles efficient propagation of messages across the P2P network.
    Implements gossip protocol with flood control and deduplication.
    """
    
    def __init__(self, network: P2PNetwork, config: PropagationConfig = None):
        self.network = network
        self.config = config or PropagationConfig()
        
        # Message tracking
        self.seen_messages: Dict[str, float] = {}  # message_id -> timestamp
        self.pending_messages: deque = deque()
        self.message_stats: Dict[str, Dict] = defaultdict(dict)
        
        # Propagation state
        self.propagation_queue = asyncio.Queue()
        self.running = False
        
        # Performance metrics
        self.metrics = {
            'messages_propagated': 0,
            'messages_deduplicated': 0,
            'propagation_latency': [],
            'network_coverage': []
        }
        
        # Register message handlers
        self._register_handlers()
        
        logger.info("Message propagator initialized")
    
    def _register_handlers(self):
        """Register message handlers with the network"""
        self.network.register_message_handler(
            MessageType.TRANSACTION, self._handle_transaction
        )
        self.network.register_message_handler(
            MessageType.BLOCK, self._handle_block
        )
        self.network.register_message_handler(
            MessageType.CHALLENGE, self._handle_challenge
        )
        self.network.register_message_handler(
            MessageType.SOLUTION, self._handle_solution
        )
    
    async def start(self):
        """Start the message propagator"""
        self.running = True
        
        # Start propagation worker
        asyncio.create_task(self._propagation_worker())
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
        
        logger.info("Message propagator started")
    
    async def stop(self):
        """Stop the message propagator"""
        self.running = False
        logger.info("Message propagator stopped")
    
    async def propagate_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Propagate a transaction across the network"""
        return await self._propagate_message(
            MessageType.TRANSACTION,
            transaction_data,
            PropagationStrategy.GOSSIP,
            priority=1
        )
    
    async def propagate_block(self, block_data: Dict[str, Any]) -> str:
        """Propagate a block across the network"""
        return await self._propagate_message(
            MessageType.BLOCK,
            block_data,
            PropagationStrategy.FLOOD,
            priority=2
        )
    
    async def propagate_challenge(self, challenge_data: Dict[str, Any]) -> str:
        """Propagate a challenge to AI nodes"""
        return await self._propagate_message(
            MessageType.CHALLENGE,
            challenge_data,
            PropagationStrategy.DIRECTED,
            priority=3
        )
    
    async def propagate_solution(self, solution_data: Dict[str, Any]) -> str:
        """Propagate a solution from AI node"""
        return await self._propagate_message(
            MessageType.SOLUTION,
            solution_data,
            PropagationStrategy.FLOOD,
            priority=3
        )
    
    async def _propagate_message(self, 
                               message_type: MessageType,
                               payload: Dict[str, Any],
                               strategy: PropagationStrategy,
                               priority: int = 0) -> str:
        """Internal method to propagate a message"""
        
        # Generate unique message ID
        message_id = self._generate_message_id(message_type, payload)
        
        # Check for duplicates
        if self._is_duplicate(message_id):
            logger.debug(f"Skipping duplicate message {message_id}")
            self.metrics['messages_deduplicated'] += 1
            return message_id
        
        # Create metadata
        metadata = MessageMetadata(
            message_id=message_id,
            origin_node=self.network.node_id,
            hop_count=0,
            timestamp=time.time(),
            propagation_strategy=strategy,
            priority=priority
        )
        
        # Add to propagation queue
        await self.propagation_queue.put((message_type, payload, metadata))
        
        # Track message
        self.seen_messages[message_id] = time.time()
        self.message_stats[message_id] = {
            'created': time.time(),
            'type': message_type.value,
            'strategy': strategy.value,
            'hops': 0
        }
        
        logger.debug(f"Queued message {message_id} for propagation")
        return message_id
    
    async def _propagation_worker(self):
        """Worker task that handles message propagation"""
        while self.running:
            try:
                # Get message from queue
                message_type, payload, metadata = await asyncio.wait_for(
                    self.propagation_queue.get(), timeout=1.0
                )
                
                # Execute propagation strategy
                await self._execute_propagation(message_type, payload, metadata)
                
                self.metrics['messages_propagated'] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in propagation worker: {e}")
                await asyncio.sleep(1)
    
    async def _execute_propagation(self, 
                                 message_type: MessageType,
                                 payload: Dict[str, Any],
                                 metadata: MessageMetadata):
        """Execute the propagation strategy for a message"""
        
        # Get target peers based on strategy
        target_peers = self._select_target_peers(metadata.propagation_strategy)
        
        if not target_peers:
            logger.warning("No target peers available for propagation")
            return
        
        # Create P2P message
        p2p_message = P2PMessage(
            message_type=message_type,
            sender_id=self.network.node_id,
            recipient_id=None,  # Broadcast
            payload={
                'data': payload,
                'metadata': {
                    'message_id': metadata.message_id,
                    'origin_node': metadata.origin_node,
                    'hop_count': metadata.hop_count,
                    'timestamp': metadata.timestamp,
                    'strategy': metadata.propagation_strategy.value
                }
            },
            timestamp=time.time(),
            signature=''  # TODO: Add signature
        )
        
        # Send to target peers
        successful_sends = 0
        for peer_id in target_peers:
            try:
                if await self.network.send_message_to_peer(peer_id, p2p_message):
                    successful_sends += 1
            except Exception as e:
                logger.error(f"Failed to send to peer {peer_id}: {e}")
        
        logger.debug(f"Propagated message {metadata.message_id} to {successful_sends}/{len(target_peers)} peers")
        
        # Update metrics
        if metadata.message_id in self.message_stats:
            self.message_stats[metadata.message_id]['propagated_to'] = successful_sends
    
    def _select_target_peers(self, strategy: PropagationStrategy) -> List[str]:
        """Select target peers based on propagation strategy"""
        all_peers = list(self.network.connections.keys())
        
        if not all_peers:
            return []
        
        if strategy == PropagationStrategy.FLOOD:
            # Send to all peers
            return all_peers
        
        elif strategy == PropagationStrategy.GOSSIP:
            # Send to random subset of peers
            import random
            gossip_count = max(1, int(len(all_peers) * self.config.gossip_factor))
            return random.sample(all_peers, min(gossip_count, len(all_peers)))
        
        elif strategy == PropagationStrategy.DIRECTED:
            # Send to AI nodes only
            ai_peers = [
                peer_id for peer_id, peer_info in self.network.peers.items()
                if peer_info.is_ai_node
            ]
            return ai_peers
        
        return all_peers
    
    async def _handle_transaction(self, message: P2PMessage):
        """Handle received transaction message"""
        await self._handle_propagated_message(message, MessageType.TRANSACTION)
    
    async def _handle_block(self, message: P2PMessage):
        """Handle received block message"""
        await self._handle_propagated_message(message, MessageType.BLOCK)
    
    async def _handle_challenge(self, message: P2PMessage):
        """Handle received challenge message"""
        await self._handle_propagated_message(message, MessageType.CHALLENGE)
    
    async def _handle_solution(self, message: P2PMessage):
        """Handle received solution message"""
        await self._handle_propagated_message(message, MessageType.SOLUTION)
    
    async def _handle_propagated_message(self, message: P2PMessage, expected_type: MessageType):
        """Handle a propagated message"""
        try:
            # Extract metadata
            payload_data = message.payload.get('data', {})
            metadata_dict = message.payload.get('metadata', {})
            
            message_id = metadata_dict.get('message_id')
            if not message_id:
                logger.warning("Received message without message_id")
                return
            
            # Check for duplicates
            if self._is_duplicate(message_id):
                logger.debug(f"Ignoring duplicate message {message_id}")
                self.metrics['messages_deduplicated'] += 1
                return
            
            # Mark as seen
            self.seen_messages[message_id] = time.time()
            
            # Check hop count
            hop_count = metadata_dict.get('hop_count', 0)
            if hop_count >= self.config.max_hops:
                logger.debug(f"Message {message_id} exceeded max hops")
                return
            
            # Re-propagate if needed
            strategy = PropagationStrategy(metadata_dict.get('strategy', 'gossip'))
            if hop_count < self.config.max_hops - 1:
                # Create new metadata for re-propagation
                new_metadata = MessageMetadata(
                    message_id=message_id,
                    origin_node=metadata_dict.get('origin_node', message.sender_id),
                    hop_count=hop_count + 1,
                    timestamp=metadata_dict.get('timestamp', time.time()),
                    propagation_strategy=strategy
                )
                
                # Re-propagate to other peers (excluding sender)
                await self._re_propagate_message(expected_type, payload_data, new_metadata, message.sender_id)
            
            # Process message locally (this would be handled by other components)
            logger.debug(f"Processing {expected_type.value} message {message_id}")
            
        except Exception as e:
            logger.error(f"Error handling propagated message: {e}")
    
    async def _re_propagate_message(self, 
                                  message_type: MessageType,
                                  payload: Dict[str, Any],
                                  metadata: MessageMetadata,
                                  exclude_peer: str):
        """Re-propagate a message to other peers"""
        
        # Get target peers (excluding sender)
        all_target_peers = self._select_target_peers(metadata.propagation_strategy)
        target_peers = [peer for peer in all_target_peers if peer != exclude_peer]
        
        if not target_peers:
            return
        
        # Create P2P message
        p2p_message = P2PMessage(
            message_type=message_type,
            sender_id=self.network.node_id,
            recipient_id=None,
            payload={
                'data': payload,
                'metadata': {
                    'message_id': metadata.message_id,
                    'origin_node': metadata.origin_node,
                    'hop_count': metadata.hop_count,
                    'timestamp': metadata.timestamp,
                    'strategy': metadata.propagation_strategy.value
                }
            },
            timestamp=time.time(),
            signature=''
        )
        
        # Send to target peers
        for peer_id in target_peers:
            try:
                await self.network.send_message_to_peer(peer_id, p2p_message)
            except Exception as e:
                logger.error(f"Failed to re-propagate to peer {peer_id}: {e}")
    
    def _generate_message_id(self, message_type: MessageType, payload: Dict[str, Any]) -> str:
        """Generate unique message ID"""
        content = f"{message_type.value}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, message_id: str) -> bool:
        """Check if message is a duplicate"""
        return message_id in self.seen_messages
    
    async def _cleanup_task(self):
        """Clean up old message tracking data"""
        while self.running:
            try:
                current_time = time.time()
                
                # Clean up seen messages
                expired_messages = [
                    msg_id for msg_id, timestamp in self.seen_messages.items()
                    if current_time - timestamp > self.config.duplicate_cache_ttl
                ]
                
                for msg_id in expired_messages:
                    del self.seen_messages[msg_id]
                    if msg_id in self.message_stats:
                        del self.message_stats[msg_id]
                
                # Limit cache size
                if len(self.seen_messages) > self.config.duplicate_cache_size:
                    # Remove oldest entries
                    sorted_messages = sorted(
                        self.seen_messages.items(), 
                        key=lambda x: x[1]
                    )
                    
                    to_remove = len(self.seen_messages) - self.config.duplicate_cache_size
                    for msg_id, _ in sorted_messages[:to_remove]:
                        del self.seen_messages[msg_id]
                        if msg_id in self.message_stats:
                            del self.message_stats[msg_id]
                
                logger.debug(f"Cleaned up {len(expired_messages)} expired messages")
                
                await asyncio.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(10)
    
    def get_propagation_stats(self) -> Dict[str, Any]:
        """Get propagation statistics"""
        return {
            **self.metrics,
            'seen_messages_count': len(self.seen_messages),
            'pending_messages_count': self.propagation_queue.qsize(),
            'message_stats_count': len(self.message_stats)
        }