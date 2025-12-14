"""
Data models for Network Coordinator
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import json


class NodeType(Enum):
    """Types of nodes in the network"""
    GENESIS = "genesis"
    REGULAR = "regular"
    AI_MINING = "ai_mining"
    BACKUP = "backup"


class NodeStatus(Enum):
    """Node status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPICIOUS = "suspicious"
    BLACKLISTED = "blacklisted"


@dataclass
class NetworkNode:
    """Represents a node in the PlayerGold network"""
    node_id: str                    # Unique identifier (public key hash)
    public_ip: str                  # Public IP address (will be encrypted)
    port: int                       # P2P port
    latitude: float                 # Geographic latitude
    longitude: float                # Geographic longitude
    os_info: str                    # Operating system info
    is_genesis: bool                # Whether node can create genesis blocks
    last_keepalive: datetime        # Last KeepAlive timestamp
    blockchain_height: int          # Current blockchain height
    connected_peers: int            # Number of connected peers
    node_type: NodeType             # Type of node
    reputation_score: float = 1.0   # Node reputation (0.0-1.0)
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: NodeStatus = NodeStatus.ACTIVE
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'node_id': self.node_id,
            'public_ip': self.public_ip,
            'port': self.port,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'os_info': self.os_info,
            'is_genesis': self.is_genesis,
            'last_keepalive': self.last_keepalive.isoformat(),
            'blockchain_height': self.blockchain_height,
            'connected_peers': self.connected_peers,
            'node_type': self.node_type.value,
            'reputation_score': self.reputation_score,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NetworkNode':
        """Create from dictionary"""
        return cls(
            node_id=data['node_id'],
            public_ip=data['public_ip'],
            port=data['port'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            os_info=data['os_info'],
            is_genesis=data['is_genesis'],
            last_keepalive=datetime.fromisoformat(data['last_keepalive']),
            blockchain_height=data['blockchain_height'],
            connected_peers=data['connected_peers'],
            node_type=NodeType(data['node_type']),
            reputation_score=data.get('reputation_score', 1.0),
            created_at=datetime.fromisoformat(data['created_at']),
            status=NodeStatus(data['status'])
        )


@dataclass
class NodeStatusUpdate:
    """Status update from a node"""
    blockchain_height: int          # Current blockchain height
    connected_peers: int            # Number of connected peers
    cpu_usage: float                # CPU usage percentage
    memory_usage: float             # Memory usage percentage
    network_latency: float          # Average network latency
    ai_model_loaded: bool           # Whether AI model is loaded
    mining_active: bool             # Whether mining is active
    last_block_time: Optional[datetime] = None  # Last block processed


@dataclass
class EncryptedNetworkMap:
    """Encrypted network map for distribution"""
    encrypted_data: bytes           # AES-256 encrypted node list
    salt: bytes                     # Unique salt for encryption
    timestamp: datetime             # Map generation timestamp
    signature: bytes                # Digital signature for integrity
    version: int                    # Map version number
    total_nodes: int                # Total nodes in map
    active_nodes: int               # Currently active nodes
    genesis_nodes: int              # Number of genesis nodes
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'encrypted_data': self.encrypted_data.hex(),
            'salt': self.salt.hex(),
            'timestamp': self.timestamp.isoformat(),
            'signature': self.signature.hex(),
            'version': self.version,
            'total_nodes': self.total_nodes,
            'active_nodes': self.active_nodes,
            'genesis_nodes': self.genesis_nodes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EncryptedNetworkMap':
        """Create from dictionary"""
        return cls(
            encrypted_data=bytes.fromhex(data['encrypted_data']),
            salt=bytes.fromhex(data['salt']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            signature=bytes.fromhex(data['signature']),
            version=data['version'],
            total_nodes=data['total_nodes'],
            active_nodes=data['active_nodes'],
            genesis_nodes=data['genesis_nodes']
        )


@dataclass
class RegistrationRequest:
    """Node registration request"""
    node_id: str
    public_ip: str
    port: int
    latitude: float
    longitude: float
    os_info: str
    node_type: NodeType
    public_key: str                 # For authentication
    signature: str                  # Signature of registration data


@dataclass
class KeepAliveMessage:
    """KeepAlive message from node"""
    node_id: str
    status_update: NodeStatusUpdate
    signature: str                  # Signature for authentication
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Location:
    """Geographic location"""
    latitude: float
    longitude: float
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location using Haversine formula"""
        import math
        
        # Convert to radians
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        r = 6371
        return c * r


@dataclass
class ForkDetection:
    """Fork detection result"""
    fork_id: str
    detected_at: datetime
    conflicting_chains: List[dict]  # Chain info with node counts
    canonical_chain: str            # Selected canonical chain
    affected_nodes: List[str]       # Nodes on wrong chain
    resolution_status: str          # pending, resolved, failed


@dataclass
class NetworkConflict:
    """Network conflict information"""
    conflict_id: str
    conflict_type: str              # fork, partition, inconsistency
    detected_at: datetime
    affected_nodes: List[str]
    severity: str                   # low, medium, high, critical
    auto_resolvable: bool


@dataclass
class BackupResult:
    """Result of backup operation"""
    backup_node_id: str
    success: bool
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class SyncResult:
    """Result of synchronization operation"""
    success: bool
    synced_nodes: int
    conflicts_resolved: int
    timestamp: datetime
    error_message: Optional[str] = None