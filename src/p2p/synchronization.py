"""
Blockchain synchronization system for P2P network.
Handles automatic blockchain sync, conflict resolution, and network partition recovery.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from collections import defaultdict

from .network import P2PNetwork, MessageType, P2PMessage

logger = logging.getLogger(__name__)


class SyncState(Enum):
    """Synchronization states"""
    SYNCED = "synced"
    SYNCING = "syncing"
    BEHIND = "behind"
    AHEAD = "ahead"
    CONFLICTED = "conflicted"
    PARTITIONED = "partitioned"


@dataclass
class BlockHeader:
    """Simplified block header for sync purposes"""
    index: int
    hash: str
    previous_hash: str
    timestamp: float
    merkle_root: str
    validator_count: int
    reputation_score: float


@dataclass
class SyncRequest:
    """Synchronization request"""
    request_id: str
    start_index: int
    end_index: int
    requester_id: str
    timestamp: float


@dataclass
class SyncResponse:
    """Synchronization response"""
    request_id: str
    blocks: List[Dict[str, Any]]
    headers: List[BlockHeader]
    responder_id: str
    timestamp: float


@dataclass
class PeerSyncInfo:
    """Peer synchronization information"""
    peer_id: str
    latest_block_index: int
    latest_block_hash: str
    reputation: float
    last_sync: float
    sync_speed: float  # blocks per second
    is_reliable: bool = True


class BlockchainSynchronizer:
    """
    Handles blockchain synchronization across the P2P network.
    Implements conflict resolution and partition recovery.
    """
    
    def __init__(self, network: P2PNetwork, blockchain_manager):
        self.network = network
        self.blockchain = blockchain_manager
        
        # Sync state
        self.sync_state = SyncState.SYNCED
        self.peer_sync_info: Dict[str, PeerSyncInfo] = {}
        self.pending_requests: Dict[str, SyncRequest] = {}
        self.sync_queue = asyncio.Queue()
        
        # Configuration
        self.sync_batch_size = 100  # blocks per request
        self.max_concurrent_syncs = 5
        self.sync_timeout = 30.0  # seconds
        self.reputation_threshold = 0.5
        self.partition_timeout = 300.0  # 5 minutes
        
        # Conflict resolution
        self.conflict_resolution_strategy = "timestamp_reputation"
        self.min_confirmations = 3
        
        # Statistics
        self.stats = {
            'sync_requests_sent': 0,
            'sync_requests_received': 0,
            'blocks_synced': 0,
            'conflicts_resolved': 0,
            'partitions_recovered': 0,
            'sync_errors': 0
        }
        
        # Register message handlers
        self._register_handlers()
        
        # Running state
        self.running = False
        
        logger.info("Blockchain synchronizer initialized")
    
    def _register_handlers(self):
        """Register synchronization message handlers"""
        self.network.register_message_handler(
            MessageType.SYNC_REQUEST, self._handle_sync_request
        )
        self.network.register_message_handler(
            MessageType.SYNC_RESPONSE, self._handle_sync_response
        )
        self.network.register_message_handler(
            MessageType.BLOCK, self._handle_new_block
        )
    
    async def start(self):
        """Start the synchronizer"""
        self.running = True
        
        # Start sync tasks
        asyncio.create_task(self._sync_worker())
        asyncio.create_task(self._peer_monitoring_loop())
        asyncio.create_task(self._partition_detection_loop())
        
        # Initial sync with peers
        await self._initial_sync()
        
        logger.info("Blockchain synchronizer started")
    
    async def stop(self):
        """Stop the synchronizer"""
        self.running = False
        logger.info("Blockchain synchronizer stopped")
    
    async def _initial_sync(self):
        """Perform initial synchronization with network"""
        try:
            # Request peer status from all connected peers
            await self._request_peer_status()
            
            # Wait a bit for responses
            await asyncio.sleep(2.0)
            
            # Determine if we need to sync
            await self._check_sync_status()
            
        except Exception as e:
            logger.error(f"Error in initial sync: {e}")
    
    async def _request_peer_status(self):
        """Request status from all peers"""
        status_request = {
            'type': 'status_request',
            'latest_block_index': await self.blockchain.get_latest_block_index(),
            'latest_block_hash': await self.blockchain.get_latest_block_hash(),
            'timestamp': time.time()
        }
        
        await self.network.broadcast_message(
            MessageType.SYNC_REQUEST,
            status_request
        )
    
    async def _check_sync_status(self):
        """Check if we need to synchronize"""
        if not self.peer_sync_info:
            logger.info("No peers available for sync")
            return
        
        our_latest_index = await self.blockchain.get_latest_block_index()
        
        # Find the highest block index among peers
        max_peer_index = max(
            info.latest_block_index for info in self.peer_sync_info.values()
        )
        
        if max_peer_index > our_latest_index:
            logger.info(f"We are behind (our: {our_latest_index}, max peer: {max_peer_index})")
            self.sync_state = SyncState.BEHIND
            await self._start_sync_from_peers()
        elif our_latest_index > max_peer_index:
            logger.info(f"We are ahead (our: {our_latest_index}, max peer: {max_peer_index})")
            self.sync_state = SyncState.AHEAD
        else:
            logger.info("We are synced with the network")
            self.sync_state = SyncState.SYNCED
    
    async def _start_sync_from_peers(self):
        """Start synchronization from peers"""
        self.sync_state = SyncState.SYNCING
        
        our_latest_index = await self.blockchain.get_latest_block_index()
        
        # Select best peers for sync (highest reputation and latest blocks)
        sync_peers = self._select_sync_peers()
        
        if not sync_peers:
            logger.warning("No suitable peers for synchronization")
            self.sync_state = SyncState.CONFLICTED
            return
        
        # Request blocks from selected peers
        for peer_info in sync_peers[:self.max_concurrent_syncs]:
            await self._request_blocks_from_peer(
                peer_info.peer_id,
                our_latest_index + 1,
                peer_info.latest_block_index
            )
    
    def _select_sync_peers(self) -> List[PeerSyncInfo]:
        """Select best peers for synchronization"""
        # Filter reliable peers with good reputation
        reliable_peers = [
            info for info in self.peer_sync_info.values()
            if info.is_reliable and info.reputation >= self.reputation_threshold
        ]
        
        if not reliable_peers:
            # Fallback to any available peers
            reliable_peers = list(self.peer_sync_info.values())
        
        # Sort by reputation and latest block index
        reliable_peers.sort(
            key=lambda p: (p.reputation, p.latest_block_index),
            reverse=True
        )
        
        return reliable_peers
    
    async def _request_blocks_from_peer(self, peer_id: str, start_index: int, end_index: int):
        """Request blocks from a specific peer"""
        request_id = self._generate_request_id()
        
        # Limit batch size
        actual_end = min(end_index, start_index + self.sync_batch_size - 1)
        
        sync_request = SyncRequest(
            request_id=request_id,
            start_index=start_index,
            end_index=actual_end,
            requester_id=self.network.node_id,
            timestamp=time.time()
        )
        
        self.pending_requests[request_id] = sync_request
        
        # Send request
        request_data = {
            'request_id': request_id,
            'start_index': start_index,
            'end_index': actual_end,
            'requester_id': self.network.node_id,
            'timestamp': time.time()
        }
        
        message = P2PMessage(
            message_type=MessageType.SYNC_REQUEST,
            sender_id=self.network.node_id,
            recipient_id=peer_id,
            payload=request_data,
            timestamp=time.time(),
            signature=''
        )
        
        await self.network.send_message_to_peer(peer_id, message)
        self.stats['sync_requests_sent'] += 1
        
        logger.debug(f"Requested blocks {start_index}-{actual_end} from peer {peer_id}")
        
        # Set timeout for request
        asyncio.create_task(self._timeout_request(request_id))
    
    async def _timeout_request(self, request_id: str):
        """Handle request timeout"""
        await asyncio.sleep(self.sync_timeout)
        
        if request_id in self.pending_requests:
            logger.warning(f"Sync request {request_id} timed out")
            del self.pending_requests[request_id]
            self.stats['sync_errors'] += 1
    
    async def _handle_sync_request(self, message: P2PMessage):
        """Handle incoming sync request"""
        try:
            payload = message.payload
            
            if payload.get('type') == 'status_request':
                # Respond with our status
                await self._send_status_response(message.sender_id)
                return
            
            request_id = payload.get('request_id')
            start_index = payload.get('start_index')
            end_index = payload.get('end_index')
            
            if not all([request_id, start_index is not None, end_index is not None]):
                logger.warning("Invalid sync request received")
                return
            
            # Get requested blocks
            blocks = await self.blockchain.get_blocks_range(start_index, end_index)
            headers = [self._create_block_header(block) for block in blocks]
            
            # Send response
            response_data = {
                'request_id': request_id,
                'blocks': blocks,
                'headers': [self._header_to_dict(h) for h in headers],
                'responder_id': self.network.node_id,
                'timestamp': time.time()
            }
            
            response_message = P2PMessage(
                message_type=MessageType.SYNC_RESPONSE,
                sender_id=self.network.node_id,
                recipient_id=message.sender_id,
                payload=response_data,
                timestamp=time.time(),
                signature=''
            )
            
            await self.network.send_message_to_peer(message.sender_id, response_message)
            self.stats['sync_requests_received'] += 1
            
            logger.debug(f"Sent {len(blocks)} blocks to peer {message.sender_id}")
            
        except Exception as e:
            logger.error(f"Error handling sync request: {e}")
    
    async def _send_status_response(self, peer_id: str):
        """Send status response to peer"""
        status_response = {
            'type': 'status_response',
            'latest_block_index': await self.blockchain.get_latest_block_index(),
            'latest_block_hash': await self.blockchain.get_latest_block_hash(),
            'reputation': await self.blockchain.get_node_reputation(self.network.node_id),
            'timestamp': time.time()
        }
        
        message = P2PMessage(
            message_type=MessageType.SYNC_REQUEST,
            sender_id=self.network.node_id,
            recipient_id=peer_id,
            payload=status_response,
            timestamp=time.time(),
            signature=''
        )
        
        await self.network.send_message_to_peer(peer_id, message)
    
    async def _handle_sync_response(self, message: P2PMessage):
        """Handle incoming sync response"""
        try:
            payload = message.payload
            
            if payload.get('type') == 'status_response':
                # Update peer sync info
                await self._update_peer_sync_info(message.sender_id, payload)
                return
            
            request_id = payload.get('request_id')
            
            if request_id not in self.pending_requests:
                logger.warning(f"Received response for unknown request {request_id}")
                return
            
            # Remove from pending
            request = self.pending_requests.pop(request_id)
            
            # Process received blocks
            blocks = payload.get('blocks', [])
            headers = [self._dict_to_header(h) for h in payload.get('headers', [])]
            
            if blocks:
                await self._process_synced_blocks(blocks, headers, message.sender_id)
                self.stats['blocks_synced'] += len(blocks)
                
                logger.info(f"Synced {len(blocks)} blocks from peer {message.sender_id}")
                
                # Check if we need more blocks
                last_block_index = blocks[-1].get('index', 0)
                peer_info = self.peer_sync_info.get(message.sender_id)
                
                if peer_info and last_block_index < peer_info.latest_block_index:
                    # Request next batch
                    await self._request_blocks_from_peer(
                        message.sender_id,
                        last_block_index + 1,
                        peer_info.latest_block_index
                    )
                else:
                    # Sync complete with this peer
                    await self._check_sync_completion()
            
        except Exception as e:
            logger.error(f"Error handling sync response: {e}")
            self.stats['sync_errors'] += 1
    
    async def _update_peer_sync_info(self, peer_id: str, status_data: Dict):
        """Update peer synchronization information"""
        self.peer_sync_info[peer_id] = PeerSyncInfo(
            peer_id=peer_id,
            latest_block_index=status_data.get('latest_block_index', 0),
            latest_block_hash=status_data.get('latest_block_hash', ''),
            reputation=status_data.get('reputation', 0.0),
            last_sync=time.time(),
            sync_speed=0.0  # Will be calculated over time
        )
    
    async def _process_synced_blocks(self, blocks: List[Dict], headers: List[BlockHeader], peer_id: str):
        """Process blocks received from synchronization"""
        try:
            # Validate blocks before adding
            for i, block in enumerate(blocks):
                header = headers[i] if i < len(headers) else None
                
                # Basic validation
                if not await self._validate_synced_block(block, header):
                    logger.warning(f"Invalid block {block.get('index')} from peer {peer_id}")
                    continue
                
                # Check for conflicts
                existing_block = await self.blockchain.get_block_by_index(block.get('index'))
                
                if existing_block and existing_block.get('hash') != block.get('hash'):
                    # Conflict detected
                    await self._handle_block_conflict(existing_block, block, peer_id)
                else:
                    # Add block to blockchain
                    await self.blockchain.add_block(block)
            
        except Exception as e:
            logger.error(f"Error processing synced blocks: {e}")
    
    async def _validate_synced_block(self, block: Dict, header: Optional[BlockHeader]) -> bool:
        """Validate a synced block"""
        try:
            # Basic structure validation
            required_fields = ['index', 'hash', 'previous_hash', 'timestamp']
            if not all(field in block for field in required_fields):
                return False
            
            # Hash validation
            if header and header.hash != block.get('hash'):
                return False
            
            # Previous hash validation
            if block.get('index') > 0:
                prev_block = await self.blockchain.get_block_by_index(block.get('index') - 1)
                if prev_block and prev_block.get('hash') != block.get('previous_hash'):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating block: {e}")
            return False
    
    async def _handle_block_conflict(self, existing_block: Dict, new_block: Dict, peer_id: str):
        """Handle block conflict using resolution strategy"""
        try:
            logger.warning(f"Block conflict at index {existing_block.get('index')}")
            
            if self.conflict_resolution_strategy == "timestamp_reputation":
                # Resolve based on timestamp and peer reputation
                peer_info = self.peer_sync_info.get(peer_id)
                peer_reputation = peer_info.reputation if peer_info else 0.0
                
                # Prefer newer blocks from high-reputation peers
                existing_timestamp = existing_block.get('timestamp', 0)
                new_timestamp = new_block.get('timestamp', 0)
                
                if (new_timestamp > existing_timestamp and 
                    peer_reputation >= self.reputation_threshold):
                    # Replace with new block
                    await self.blockchain.replace_block(new_block)
                    logger.info(f"Replaced block {new_block.get('index')} with version from peer {peer_id}")
                    self.stats['conflicts_resolved'] += 1
            
        except Exception as e:
            logger.error(f"Error handling block conflict: {e}")
    
    async def _handle_new_block(self, message: P2PMessage):
        """Handle new block announcement"""
        try:
            block_data = message.payload.get('data', {})
            
            # Update peer info
            if message.sender_id in self.peer_sync_info:
                peer_info = self.peer_sync_info[message.sender_id]
                peer_info.latest_block_index = max(
                    peer_info.latest_block_index,
                    block_data.get('index', 0)
                )
                peer_info.latest_block_hash = block_data.get('hash', '')
                peer_info.last_sync = time.time()
            
            # Check if we need to sync
            our_latest = await self.blockchain.get_latest_block_index()
            new_block_index = block_data.get('index', 0)
            
            if new_block_index > our_latest + 1:
                # We're missing blocks, start sync
                logger.info(f"Missing blocks detected, starting sync from peer {message.sender_id}")
                await self._request_blocks_from_peer(
                    message.sender_id,
                    our_latest + 1,
                    new_block_index - 1
                )
            
        except Exception as e:
            logger.error(f"Error handling new block: {e}")
    
    async def _check_sync_completion(self):
        """Check if synchronization is complete"""
        our_latest = await self.blockchain.get_latest_block_index()
        
        # Check if we're caught up with all peers
        all_synced = True
        for peer_info in self.peer_sync_info.values():
            if peer_info.latest_block_index > our_latest:
                all_synced = False
                break
        
        if all_synced:
            self.sync_state = SyncState.SYNCED
            logger.info("Blockchain synchronization completed")
    
    async def _sync_worker(self):
        """Background worker for sync operations"""
        while self.running:
            try:
                # Process sync queue
                if not self.sync_queue.empty():
                    sync_task = await self.sync_queue.get()
                    await self._process_sync_task(sync_task)
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in sync worker: {e}")
                await asyncio.sleep(5.0)
    
    async def _process_sync_task(self, task):
        """Process a sync task"""
        # Implementation depends on task type
        pass
    
    async def _peer_monitoring_loop(self):
        """Monitor peer synchronization status"""
        while self.running:
            try:
                # Request status updates from peers periodically
                await self._request_peer_status()
                
                # Clean up old peer info
                current_time = time.time()
                expired_peers = [
                    peer_id for peer_id, info in self.peer_sync_info.items()
                    if current_time - info.last_sync > 300  # 5 minutes
                ]
                
                for peer_id in expired_peers:
                    del self.peer_sync_info[peer_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in peer monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _partition_detection_loop(self):
        """Detect and handle network partitions"""
        while self.running:
            try:
                # Check for network partitions
                if await self._detect_partition():
                    logger.warning("Network partition detected")
                    self.sync_state = SyncState.PARTITIONED
                    await self._handle_partition_recovery()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in partition detection: {e}")
                await asyncio.sleep(10)
    
    async def _detect_partition(self) -> bool:
        """Detect if we're in a network partition"""
        # Simple partition detection based on peer connectivity
        connected_peers = len(self.network.connections)
        
        if connected_peers == 0:
            return True
        
        # Check if we haven't heard from any peers recently
        current_time = time.time()
        recent_peers = [
            info for info in self.peer_sync_info.values()
            if current_time - info.last_sync < self.partition_timeout
        ]
        
        return len(recent_peers) == 0
    
    async def _handle_partition_recovery(self):
        """Handle recovery from network partition"""
        try:
            logger.info("Attempting partition recovery")
            
            # Try to reconnect to known peers
            # This would integrate with the discovery system
            
            # Once reconnected, perform full sync
            await self._initial_sync()
            
            self.stats['partitions_recovered'] += 1
            logger.info("Partition recovery completed")
            
        except Exception as e:
            logger.error(f"Error in partition recovery: {e}")
    
    def _create_block_header(self, block: Dict) -> BlockHeader:
        """Create block header from block data"""
        return BlockHeader(
            index=block.get('index', 0),
            hash=block.get('hash', ''),
            previous_hash=block.get('previous_hash', ''),
            timestamp=block.get('timestamp', 0.0),
            merkle_root=block.get('merkle_root', ''),
            validator_count=len(block.get('ai_validators', [])),
            reputation_score=0.0  # Would be calculated from validators
        )
    
    def _header_to_dict(self, header: BlockHeader) -> Dict:
        """Convert block header to dictionary"""
        return {
            'index': header.index,
            'hash': header.hash,
            'previous_hash': header.previous_hash,
            'timestamp': header.timestamp,
            'merkle_root': header.merkle_root,
            'validator_count': header.validator_count,
            'reputation_score': header.reputation_score
        }
    
    def _dict_to_header(self, data: Dict) -> BlockHeader:
        """Convert dictionary to block header"""
        return BlockHeader(
            index=data.get('index', 0),
            hash=data.get('hash', ''),
            previous_hash=data.get('previous_hash', ''),
            timestamp=data.get('timestamp', 0.0),
            merkle_root=data.get('merkle_root', ''),
            validator_count=data.get('validator_count', 0),
            reputation_score=data.get('reputation_score', 0.0)
        )
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return hashlib.sha256(
            f"{self.network.node_id}:{time.time()}".encode()
        ).hexdigest()[:16]
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        return {
            'state': self.sync_state.value,
            'peer_count': len(self.peer_sync_info),
            'pending_requests': len(self.pending_requests),
            'stats': self.stats
        }