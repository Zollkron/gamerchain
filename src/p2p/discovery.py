"""
Peer discovery system using mDNS and DHT for automatic peer finding.
Implements bootstrap nodes and peer exchange protocols.
"""

import asyncio
import logging
import socket
import struct
import json
import time
import random
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class BootstrapNode:
    """Bootstrap node information"""
    address: str
    port: int
    node_id: str
    public_key: str
    last_seen: float = 0.0


@dataclass
class DiscoveredPeer:
    """Information about a discovered peer"""
    node_id: str
    address: str
    port: int
    discovery_method: str
    capabilities: List[str]
    timestamp: float
    verified: bool = False


class DiscoveryMethod(Enum):
    """Peer discovery methods"""
    BOOTSTRAP = "bootstrap"
    MDNS = "mdns"
    DHT = "dht"
    PEER_EXCHANGE = "peer_exchange"
    MANUAL = "manual"


class PeerDiscovery:
    """
    Comprehensive peer discovery system for PlayerGold P2P network.
    Combines multiple discovery methods for robust peer finding.
    """
    
    def __init__(self, node_id: str, listen_port: int):
        self.node_id = node_id
        self.listen_port = listen_port
        
        # Discovery state
        self.discovered_peers: Dict[str, DiscoveredPeer] = {}
        self.bootstrap_nodes: List[BootstrapNode] = []
        self.running = False
        
        # Discovery components
        self.mdns_discoverer = None
        self.dht_discoverer = None
        
        # Configuration
        self.max_peers = 50
        self.discovery_interval = 30  # seconds
        self.peer_exchange_interval = 60  # seconds
        
        # Statistics
        self.stats = {
            'peers_discovered': 0,
            'bootstrap_attempts': 0,
            'mdns_discoveries': 0,
            'dht_discoveries': 0,
            'peer_exchanges': 0
        }
        
        # Default bootstrap nodes (these would be real nodes in production)
        self._setup_bootstrap_nodes()
        
        logger.info(f"Peer discovery initialized for node {node_id}")
    
    def _setup_bootstrap_nodes(self):
        """Setup default bootstrap nodes"""
        # In production, these would be well-known stable nodes
        default_bootstrap = [
            BootstrapNode("bootstrap1.playergold.com", 8000, "bootstrap1", ""),
            BootstrapNode("bootstrap2.playergold.com", 8000, "bootstrap2", ""),
            BootstrapNode("bootstrap3.playergold.com", 8000, "bootstrap3", ""),
        ]
        
        self.bootstrap_nodes.extend(default_bootstrap)
    
    async def start(self):
        """Start peer discovery"""
        self.running = True
        
        # Start mDNS discovery
        self.mdns_discoverer = MDNSDiscoverer(self.node_id, self.listen_port)
        await self.mdns_discoverer.start()
        
        # Start DHT discovery
        self.dht_discoverer = DHTDiscoverer(self.node_id)
        await self.dht_discoverer.start()
        
        # Start discovery tasks
        asyncio.create_task(self._bootstrap_discovery())
        asyncio.create_task(self._periodic_discovery())
        asyncio.create_task(self._peer_exchange_loop())
        
        logger.info("Peer discovery started")
    
    async def stop(self):
        """Stop peer discovery"""
        self.running = False
        
        if self.mdns_discoverer:
            await self.mdns_discoverer.stop()
        
        if self.dht_discoverer:
            await self.dht_discoverer.stop()
        
        logger.info("Peer discovery stopped")
    
    async def _bootstrap_discovery(self):
        """Discover peers from bootstrap nodes"""
        for bootstrap_node in self.bootstrap_nodes:
            if not self.running:
                break
            
            try:
                logger.info(f"Attempting bootstrap discovery from {bootstrap_node.address}:{bootstrap_node.port}")
                
                # Try to connect to bootstrap node
                peers = await self._query_bootstrap_node(bootstrap_node)
                
                for peer_info in peers:
                    await self._add_discovered_peer(
                        peer_info['node_id'],
                        peer_info['address'],
                        peer_info['port'],
                        DiscoveryMethod.BOOTSTRAP,
                        peer_info.get('capabilities', [])
                    )
                
                self.stats['bootstrap_attempts'] += 1
                bootstrap_node.last_seen = time.time()
                
                logger.info(f"Bootstrap discovery found {len(peers)} peers")
                
            except Exception as e:
                logger.warning(f"Bootstrap discovery failed for {bootstrap_node.address}: {e}")
            
            await asyncio.sleep(1)  # Small delay between bootstrap attempts
    
    async def _query_bootstrap_node(self, bootstrap_node: BootstrapNode) -> List[Dict]:
        """Query a bootstrap node for peer list"""
        try:
            # Simple HTTP-like query to bootstrap node
            reader, writer = await asyncio.open_connection(
                bootstrap_node.address, bootstrap_node.port
            )
            
            # Send peer list request
            request = {
                'type': 'peer_list_request',
                'node_id': self.node_id,
                'timestamp': time.time()
            }
            
            message = json.dumps(request).encode('utf-8')
            writer.write(len(message).to_bytes(4, 'big'))
            writer.write(message)
            await writer.drain()
            
            # Read response
            length_bytes = await reader.read(4)
            if len(length_bytes) == 4:
                length = int.from_bytes(length_bytes, 'big')
                response_bytes = await reader.read(length)
                
                if len(response_bytes) == length:
                    response = json.loads(response_bytes.decode('utf-8'))
                    return response.get('peers', [])
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logger.error(f"Error querying bootstrap node: {e}")
        
        return []
    
    async def _periodic_discovery(self):
        """Periodic discovery using mDNS and DHT"""
        while self.running:
            try:
                # mDNS discovery
                if self.mdns_discoverer:
                    mdns_peers = await self.mdns_discoverer.discover_peers()
                    for peer in mdns_peers:
                        await self._add_discovered_peer(
                            peer.node_id,
                            peer.address,
                            peer.port,
                            DiscoveryMethod.MDNS,
                            peer.capabilities
                        )
                    
                    self.stats['mdns_discoveries'] += len(mdns_peers)
                
                # DHT discovery
                if self.dht_discoverer:
                    dht_peers = await self.dht_discoverer.discover_peers()
                    for peer in dht_peers:
                        await self._add_discovered_peer(
                            peer.node_id,
                            peer.address,
                            peer.port,
                            DiscoveryMethod.DHT,
                            peer.capabilities
                        )
                    
                    self.stats['dht_discoveries'] += len(dht_peers)
                
                await asyncio.sleep(self.discovery_interval)
                
            except Exception as e:
                logger.error(f"Error in periodic discovery: {e}")
                await asyncio.sleep(5)
    
    async def _peer_exchange_loop(self):
        """Exchange peer lists with connected peers"""
        while self.running:
            try:
                # This would integrate with the P2P network to exchange peer lists
                # For now, we'll just log the intent
                logger.debug("Peer exchange loop iteration")
                
                self.stats['peer_exchanges'] += 1
                
                await asyncio.sleep(self.peer_exchange_interval)
                
            except Exception as e:
                logger.error(f"Error in peer exchange: {e}")
                await asyncio.sleep(10)
    
    async def _add_discovered_peer(self, 
                                 node_id: str,
                                 address: str,
                                 port: int,
                                 method: DiscoveryMethod,
                                 capabilities: List[str]):
        """Add a discovered peer to the list"""
        
        # Skip self
        if node_id == self.node_id:
            return
        
        # Check if already discovered
        if node_id in self.discovered_peers:
            # Update last seen time
            self.discovered_peers[node_id].timestamp = time.time()
            return
        
        # Add new peer
        peer = DiscoveredPeer(
            node_id=node_id,
            address=address,
            port=port,
            discovery_method=method.value,
            capabilities=capabilities,
            timestamp=time.time()
        )
        
        self.discovered_peers[node_id] = peer
        self.stats['peers_discovered'] += 1
        
        logger.info(f"Discovered new peer {node_id} via {method.value} at {address}:{port}")
    
    def get_discovered_peers(self, limit: Optional[int] = None) -> List[DiscoveredPeer]:
        """Get list of discovered peers"""
        peers = list(self.discovered_peers.values())
        
        # Sort by timestamp (most recent first)
        peers.sort(key=lambda p: p.timestamp, reverse=True)
        
        if limit:
            peers = peers[:limit]
        
        return peers
    
    def get_ai_node_peers(self) -> List[DiscoveredPeer]:
        """Get discovered AI node peers"""
        return [
            peer for peer in self.discovered_peers.values()
            if 'ai_node' in peer.capabilities
        ]
    
    def add_manual_peer(self, address: str, port: int, node_id: str = None):
        """Manually add a peer"""
        if not node_id:
            node_id = f"manual_{address}_{port}"
        
        asyncio.create_task(
            self._add_discovered_peer(
                node_id, address, port, DiscoveryMethod.MANUAL, []
            )
        )
    
    def get_discovery_stats(self) -> Dict:
        """Get discovery statistics"""
        return {
            **self.stats,
            'total_discovered_peers': len(self.discovered_peers),
            'ai_node_peers': len(self.get_ai_node_peers()),
            'bootstrap_nodes': len(self.bootstrap_nodes)
        }


class MDNSDiscoverer:
    """mDNS-based peer discovery for local network"""
    
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.socket = None
        self.running = False
        
        # mDNS configuration
        self.multicast_group = '224.0.0.251'
        self.multicast_port = 5353
        self.service_name = '_playergold._tcp.local'
    
    async def start(self):
        """Start mDNS discoverer"""
        try:
            # Create multicast socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Join multicast group
            mreq = struct.pack('4sl', socket.inet_aton(self.multicast_group), socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            self.socket.bind(('', self.multicast_port))
            self.socket.settimeout(1.0)
            
            self.running = True
            
            # Start announcement task
            asyncio.create_task(self._announce_loop())
            
            logger.info("mDNS discoverer started")
            
        except Exception as e:
            logger.error(f"Failed to start mDNS discoverer: {e}")
            raise
    
    async def stop(self):
        """Stop mDNS discoverer"""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("mDNS discoverer stopped")
    
    async def _announce_loop(self):
        """Periodically announce our presence"""
        while self.running:
            try:
                announcement = {
                    'type': 'service_announcement',
                    'service': self.service_name,
                    'node_id': self.node_id,
                    'port': self.port,
                    'capabilities': ['ai_node', 'validator'],
                    'timestamp': time.time()
                }
                
                message = json.dumps(announcement).encode('utf-8')
                self.socket.sendto(message, (self.multicast_group, self.multicast_port))
                
                await asyncio.sleep(30)  # Announce every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in mDNS announcement: {e}")
                await asyncio.sleep(5)
    
    async def discover_peers(self) -> List[DiscoveredPeer]:
        """Discover peers using mDNS"""
        discovered = []
        
        if not self.running or not self.socket:
            return discovered
        
        try:
            # Listen for announcements for a short time
            end_time = time.time() + 5.0  # Listen for 5 seconds
            
            while time.time() < end_time and self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    message = json.loads(data.decode('utf-8'))
                    
                    if (message.get('type') == 'service_announcement' and
                        message.get('service') == self.service_name and
                        message.get('node_id') != self.node_id):
                        
                        peer = DiscoveredPeer(
                            node_id=message['node_id'],
                            address=addr[0],
                            port=message['port'],
                            discovery_method='mdns',
                            capabilities=message.get('capabilities', []),
                            timestamp=time.time()
                        )
                        
                        discovered.append(peer)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"Error parsing mDNS message: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Error in mDNS discovery: {e}")
        
        return discovered


class DHTDiscoverer:
    """DHT-based peer discovery for wide area network"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.routing_table = {}
        self.storage = {}
        self.running = False
    
    async def start(self):
        """Start DHT discoverer"""
        self.running = True
        logger.info("DHT discoverer started")
    
    async def stop(self):
        """Stop DHT discoverer"""
        self.running = False
        logger.info("DHT discoverer stopped")
    
    async def discover_peers(self) -> List[DiscoveredPeer]:
        """Discover peers using DHT"""
        # Simplified DHT discovery - in production this would be more complex
        discovered = []
        
        # For now, return empty list as DHT implementation is simplified
        return discovered
    
    async def store_peer_info(self, peer_info: DiscoveredPeer):
        """Store peer information in DHT"""
        key = f"peer:{peer_info.node_id}"
        value = {
            'address': peer_info.address,
            'port': peer_info.port,
            'capabilities': peer_info.capabilities,
            'timestamp': peer_info.timestamp
        }
        self.storage[key] = value
    
    async def find_peer(self, node_id: str) -> Optional[DiscoveredPeer]:
        """Find specific peer in DHT"""
        key = f"peer:{node_id}"
        if key in self.storage:
            data = self.storage[key]
            return DiscoveredPeer(
                node_id=node_id,
                address=data['address'],
                port=data['port'],
                discovery_method='dht',
                capabilities=data['capabilities'],
                timestamp=data['timestamp']
            )
        return None