"""
P2P Network implementation for PlayerGold distributed AI nodes.
Implements libp2p-based networking with auto-discovery and TLS encryption.
Integrated with NetworkManager for testnet/mainnet support.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import json
import time
import ssl
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import socket
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

from ..network.network_manager import NetworkManager, NetworkType

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of P2P messages"""
    TRANSACTION = "transaction"
    BLOCK = "block"
    CHALLENGE = "challenge"
    SOLUTION = "solution"
    PEER_DISCOVERY = "peer_discovery"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    HEARTBEAT = "heartbeat"


@dataclass
class PeerInfo:
    """Information about a network peer"""
    peer_id: str
    address: str
    port: int
    public_key: str
    network_id: str  # Network ID for compatibility validation
    reputation: float = 0.0
    last_seen: float = 0.0
    is_ai_node: bool = False
    model_hash: Optional[str] = None


@dataclass
class P2PMessage:
    """P2P network message structure"""
    message_type: MessageType
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast
    payload: Dict[str, Any]
    timestamp: float
    signature: str


class P2PNetwork:
    """
    P2P Network implementation with libp2p-like functionality.
    Provides auto-discovery, secure communication, and message propagation.
    """
    
    def __init__(self, 
                 node_id: str,
                 listen_port: Optional[int] = None,
                 max_peers: int = 50,
                 enable_mdns: bool = True,
                 enable_dht: bool = True,
                 network_manager: Optional[NetworkManager] = None):
        self.node_id = node_id
        
        # Initialize or use provided NetworkManager
        self.network_manager = network_manager or NetworkManager()
        network_config = self.network_manager.get_network_config()
        
        # Use network-specific port if not provided
        self.listen_port = listen_port or network_config.p2p_port
        self.max_peers = max_peers
        self.enable_mdns = enable_mdns
        self.enable_dht = enable_dht
        
        # Store network info
        self.network_id = network_config.network_id
        self.network_type = self.network_manager.get_current_network()
        
        # Network state
        self.peers: Dict[str, PeerInfo] = {}
        self.connections: Dict[str, Any] = {}
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # TLS configuration
        self.ssl_context = None
        self.certificate = None
        self.private_key = None
        
        # Network components
        self.server = None
        self.mdns_service = None
        self.dht_node = None
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running = False
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'connections_established': 0,
            'connections_lost': 0,
            'incompatible_peers_rejected': 0
        }
        
        logger.info(f"P2P Network initialized for node {node_id}")
        logger.info(f"Network: {self.network_type.value} ({self.network_id})")
        logger.info(f"Port: {self.listen_port}")
    
    async def start(self):
        """Start the P2P network"""
        try:
            logger.info("Starting P2P network...")
            
            # Generate TLS certificate
            await self._setup_tls()
            
            # Start TCP server
            await self._start_server()
            
            # Start mDNS discovery if enabled
            if self.enable_mdns:
                await self._start_mdns()
            
            # Start DHT if enabled
            if self.enable_dht:
                await self._start_dht()
            
            # Start periodic tasks
            asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._peer_cleanup_loop())
            
            self.running = True
            
            # Connect to bootstrap nodes
            asyncio.create_task(self._connect_to_bootstrap_nodes())
            
            logger.info(f"P2P network started successfully on port {self.listen_port}")
            
        except Exception as e:
            logger.error(f"Failed to start P2P network: {e}")
            raise
    
    async def stop(self):
        """Stop the P2P network"""
        logger.info("Stopping P2P network...")
        
        self.running = False
        
        # Close all connections
        for peer_id, connection in self.connections.items():
            try:
                connection.close()
            except Exception as e:
                logger.warning(f"Error closing connection to {peer_id}: {e}")
        
        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Stop mDNS
        if self.mdns_service:
            await self._stop_mdns()
        
        # Stop DHT
        if self.dht_node:
            await self._stop_dht()
        
        self.executor.shutdown(wait=True)
        logger.info("P2P network stopped")
    
    async def _setup_tls(self):
        """Setup TLS 1.3 encryption for secure communication"""
        try:
            # Generate private key
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create self-signed certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PlayerGold"),
                x509.NameAttribute(NameOID.COMMON_NAME, f"node-{self.node_id}"),
            ])
            
            self.certificate = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                self.private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).sign(self.private_key, hashes.SHA256())
            
            # Create SSL context
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
            
            logger.info("TLS 1.3 encryption configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup TLS: {e}")
            raise
    
    async def _start_server(self):
        """Start TCP server for incoming connections"""
        try:
            self.server = await asyncio.start_server(
                self._handle_connection,
                '0.0.0.0',
                self.listen_port
            )
            logger.info(f"TCP server started on port {self.listen_port}")
            
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
            raise
    
    async def _handle_connection(self, reader, writer):
        """Handle incoming P2P connection"""
        peer_address = writer.get_extra_info('peername')
        logger.debug(f"New connection from {peer_address}")
        
        try:
            # Perform handshake
            peer_info = await self._perform_handshake(reader, writer)
            
            if peer_info:
                # Add peer and handle messages
                self.peers[peer_info.peer_id] = peer_info
                self.connections[peer_info.peer_id] = writer
                self.stats['connections_established'] += 1
                
                logger.info(f"Connected to peer {peer_info.peer_id}")
                
                # Handle messages from this peer
                await self._handle_peer_messages(peer_info.peer_id, reader, writer)
            
        except Exception as e:
            logger.error(f"Error handling connection from {peer_address}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _perform_handshake(self, reader, writer) -> Optional[PeerInfo]:
        """Perform P2P handshake with peer and validate network compatibility"""
        try:
            # Send our node info including network_id
            handshake_data = {
                'node_id': self.node_id,
                'network_id': self.network_id,  # Include network ID
                'network_type': self.network_type.value,
                'version': '1.0.0',
                'capabilities': ['ai_node', 'validator'],
                'timestamp': time.time()
            }
            
            await self._send_raw_message(writer, handshake_data)
            
            # Receive peer info
            peer_data = await self._receive_raw_message(reader)
            
            if peer_data and 'node_id' in peer_data:
                # Validate network compatibility
                peer_network_id = peer_data.get('network_id', 'unknown')
                
                if not self.network_manager.validate_network_compatibility(peer_network_id):
                    logger.warning(
                        f"Rejecting peer {peer_data['node_id']}: "
                        f"incompatible network (peer={peer_network_id}, local={self.network_id})"
                    )
                    self.stats['incompatible_peers_rejected'] += 1
                    return None
                
                peer_info = PeerInfo(
                    peer_id=peer_data['node_id'],
                    address=writer.get_extra_info('peername')[0],
                    port=writer.get_extra_info('peername')[1],
                    public_key='',  # TODO: Extract from TLS certificate
                    network_id=peer_network_id,
                    last_seen=time.time()
                )
                
                logger.info(
                    f"Handshake successful with {peer_info.peer_id} "
                    f"on {peer_network_id}"
                )
                
                return peer_info
            
        except Exception as e:
            logger.error(f"Handshake failed: {e}")
        
        return None
    
    async def _handle_peer_messages(self, peer_id: str, reader, writer):
        """Handle messages from a connected peer"""
        try:
            while self.running:
                message_data = await self._receive_raw_message(reader)
                
                if not message_data:
                    break
                
                # Parse P2P message
                try:
                    message = P2PMessage(
                        message_type=MessageType(message_data['type']),
                        sender_id=message_data['sender_id'],
                        recipient_id=message_data.get('recipient_id'),
                        payload=message_data['payload'],
                        timestamp=message_data['timestamp'],
                        signature=message_data['signature']
                    )
                    
                    # Update peer last seen
                    if peer_id in self.peers:
                        self.peers[peer_id].last_seen = time.time()
                    
                    # Handle message
                    await self._handle_message(message)
                    
                    self.stats['messages_received'] += 1
                    
                except Exception as e:
                    logger.error(f"Error parsing message from {peer_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error handling messages from {peer_id}: {e}")
        finally:
            # Clean up connection
            if peer_id in self.connections:
                del self.connections[peer_id]
            if peer_id in self.peers:
                del self.peers[peer_id]
            self.stats['connections_lost'] += 1
    
    async def _send_raw_message(self, writer, data: Dict):
        """Send raw message over connection"""
        try:
            message_bytes = json.dumps(data).encode('utf-8')
            length = len(message_bytes)
            
            # Send length prefix + message
            writer.write(length.to_bytes(4, 'big'))
            writer.write(message_bytes)
            await writer.drain()
            
            self.stats['bytes_sent'] += 4 + length
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def _receive_raw_message(self, reader) -> Optional[Dict]:
        """Receive raw message from connection"""
        try:
            # Read length prefix
            length_bytes = await reader.read(4)
            if len(length_bytes) != 4:
                return None
            
            length = int.from_bytes(length_bytes, 'big')
            
            # Read message
            message_bytes = await reader.read(length)
            if len(message_bytes) != length:
                return None
            
            self.stats['bytes_received'] += 4 + length
            
            return json.loads(message_bytes.decode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    async def _start_mdns(self):
        """Start mDNS service discovery"""
        try:
            # Simple mDNS implementation for peer discovery
            self.mdns_service = MDNSService(self.node_id, self.listen_port)
            await self.mdns_service.start()
            logger.info("mDNS service discovery started")
            
        except Exception as e:
            logger.error(f"Failed to start mDNS: {e}")
    
    async def _stop_mdns(self):
        """Stop mDNS service"""
        if self.mdns_service:
            await self.mdns_service.stop()
    
    async def _start_dht(self):
        """Start DHT for distributed peer discovery"""
        try:
            self.dht_node = DHTNode(self.node_id)
            await self.dht_node.start()
            logger.info("DHT node started")
            
        except Exception as e:
            logger.error(f"Failed to start DHT: {e}")
    
    async def _stop_dht(self):
        """Stop DHT node"""
        if self.dht_node:
            await self.dht_node.stop()
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to peers"""
        while self.running:
            try:
                await self.broadcast_message(
                    MessageType.HEARTBEAT,
                    {'timestamp': time.time(), 'node_id': self.node_id}
                )
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
    
    async def _peer_cleanup_loop(self):
        """Clean up inactive peers"""
        while self.running:
            try:
                current_time = time.time()
                inactive_peers = []
                
                for peer_id, peer_info in self.peers.items():
                    if current_time - peer_info.last_seen > 120:  # 2 minutes timeout
                        inactive_peers.append(peer_id)
                
                for peer_id in inactive_peers:
                    logger.info(f"Removing inactive peer {peer_id}")
                    if peer_id in self.connections:
                        self.connections[peer_id].close()
                        del self.connections[peer_id]
                    del self.peers[peer_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in peer cleanup: {e}")
                await asyncio.sleep(10)
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for specific message types"""
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type}")
    
    async def _handle_message(self, message: P2PMessage):
        """Handle received P2P message"""
        try:
            # Check if message is for us or broadcast
            if message.recipient_id and message.recipient_id != self.node_id:
                # Forward message if we have the recipient
                await self._forward_message(message)
                return
            
            # Handle message locally
            if message.message_type in self.message_handlers:
                handler = self.message_handlers[message.message_type]
                await handler(message)
            else:
                logger.warning(f"No handler for message type {message.message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _forward_message(self, message: P2PMessage):
        """Forward message to intended recipient"""
        if message.recipient_id in self.connections:
            try:
                await self.send_message_to_peer(message.recipient_id, message)
                logger.debug(f"Forwarded message to {message.recipient_id}")
            except Exception as e:
                logger.error(f"Error forwarding message: {e}")
    
    async def send_message_to_peer(self, peer_id: str, message: P2PMessage):
        """Send message to specific peer"""
        if peer_id not in self.connections:
            logger.warning(f"No connection to peer {peer_id}")
            return False
        
        try:
            writer = self.connections[peer_id]
            message_data = {
                'type': message.message_type.value,
                'sender_id': message.sender_id,
                'recipient_id': message.recipient_id,
                'payload': message.payload,
                'timestamp': message.timestamp,
                'signature': message.signature
            }
            
            await self._send_raw_message(writer, message_data)
            self.stats['messages_sent'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {peer_id}: {e}")
            return False
    
    async def broadcast_message(self, message_type: MessageType, payload: Dict[str, Any]):
        """Broadcast message to all connected peers"""
        message = P2PMessage(
            message_type=message_type,
            sender_id=self.node_id,
            recipient_id=None,  # Broadcast
            payload=payload,
            timestamp=time.time(),
            signature=''  # TODO: Add cryptographic signature
        )
        
        successful_sends = 0
        for peer_id in list(self.connections.keys()):
            if await self.send_message_to_peer(peer_id, message):
                successful_sends += 1
        
        logger.debug(f"Broadcast message to {successful_sends} peers")
        return successful_sends
    
    async def connect_to_peer(self, address: str, port: int) -> bool:
        """Connect to a specific peer"""
        try:
            reader, writer = await asyncio.open_connection(address, port)
            
            # Perform handshake
            peer_info = await self._perform_handshake(reader, writer)
            
            if peer_info:
                self.peers[peer_info.peer_id] = peer_info
                self.connections[peer_info.peer_id] = writer
                self.stats['connections_established'] += 1
                
                # Start handling messages from this peer
                asyncio.create_task(
                    self._handle_peer_messages(peer_info.peer_id, reader, writer)
                )
                
                logger.info(f"Successfully connected to peer {peer_info.peer_id}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {address}:{port}: {e}")
        
        return False
    
    def get_peer_count(self) -> int:
        """Get number of connected peers"""
        return len(self.connections)
    
    def get_peer_list(self) -> List[PeerInfo]:
        """Get list of connected peers"""
        return list(self.peers.values())
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        return {
            **self.stats,
            'peer_count': len(self.peers),
            'active_connections': len(self.connections),
            'uptime': time.time() - (self.stats.get('start_time', time.time()))
        }

    async def _connect_to_bootstrap_nodes(self):
        """Connect to bootstrap nodes from network configuration"""
        try:
            # Get bootstrap nodes from network manager
            network_config = self.network_manager.get_network_config()
            bootstrap_nodes = getattr(network_config, 'bootstrap_nodes', [])
            
            if not bootstrap_nodes:
                logger.warning("No bootstrap nodes configured")
                return
            
            logger.info(f"Attempting to connect to {len(bootstrap_nodes)} bootstrap nodes...")
            
            # Wait a bit for server to be fully ready
            await asyncio.sleep(2)
            
            successful_connections = 0
            for node_address in bootstrap_nodes:
                try:
                    # Parse address (format: "ip:port")
                    if ':' in node_address:
                        ip, port_str = node_address.split(':')
                        port = int(port_str)
                    else:
                        ip = node_address
                        port = self.listen_port
                    
                    # Don't connect to ourselves
                    if ip == '127.0.0.1' or ip == 'localhost':
                        # Get our external IP to compare
                        try:
                            import socket
                            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock.connect(("8.8.8.8", 80))
                            our_ip = sock.getsockname()[0]
                            sock.close()
                            
                            if ip == our_ip and port == self.listen_port:
                                logger.debug(f"Skipping connection to self: {node_address}")
                                continue
                        except:
                            pass
                    
                    logger.info(f"Attempting to connect to bootstrap node: {ip}:{port}")
                    
                    # Try to connect
                    success = await self.connect_to_peer(ip, port)
                    if success:
                        successful_connections += 1
                        logger.info(f"✅ Connected to bootstrap node {ip}:{port}")
                    else:
                        logger.warning(f"❌ Failed to connect to bootstrap node {ip}:{port}")
                    
                    # Small delay between connection attempts
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error connecting to bootstrap node {node_address}: {e}")
            
            if successful_connections > 0:
                logger.info(f"✅ Successfully connected to {successful_connections} bootstrap nodes")
            else:
                logger.warning("❌ Failed to connect to any bootstrap nodes")
                
                # Schedule retry in 30 seconds
                logger.info("Scheduling bootstrap connection retry in 30 seconds...")
                await asyncio.sleep(30)
                asyncio.create_task(self._connect_to_bootstrap_nodes())
                
        except Exception as e:
            logger.error(f"Error in bootstrap connection process: {e}")


class MDNSService:
    """Simple mDNS service for local peer discovery"""
    
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.socket = None
        self.running = False
    
    async def start(self):
        """Start mDNS service"""
        try:
            # Create multicast socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Join multicast group
            mreq = socket.inet_aton('224.0.0.251') + socket.inet_aton('0.0.0.0')
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            self.socket.bind(('', 5353))
            self.running = True
            
            # Start discovery loop
            asyncio.create_task(self._discovery_loop())
            
            logger.info("mDNS service started")
            
        except Exception as e:
            logger.error(f"Failed to start mDNS: {e}")
            raise
    
    async def stop(self):
        """Stop mDNS service"""
        self.running = False
        if self.socket:
            self.socket.close()
    
    async def _discovery_loop(self):
        """mDNS discovery loop"""
        while self.running:
            try:
                # Announce our presence
                announcement = {
                    'node_id': self.node_id,
                    'port': self.port,
                    'service': 'playergold-p2p',
                    'timestamp': time.time()
                }
                
                message = json.dumps(announcement).encode('utf-8')
                self.socket.sendto(message, ('224.0.0.251', 5353))
                
                await asyncio.sleep(30)  # Announce every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in mDNS discovery: {e}")
                await asyncio.sleep(5)


class DHTNode:
    """Simple DHT implementation for distributed peer discovery"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.routing_table = {}
        self.storage = {}
        self.running = False
    
    async def start(self):
        """Start DHT node"""
        self.running = True
        logger.info("DHT node started")
    
    async def stop(self):
        """Stop DHT node"""
        self.running = False
        logger.info("DHT node stopped")
    
    async def store(self, key: str, value: Any):
        """Store value in DHT"""
        self.storage[key] = value
    
    async def find(self, key: str) -> Optional[Any]:
        """Find value in DHT"""
        return self.storage.get(key)