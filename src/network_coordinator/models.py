#!/usr/bin/env python3
"""
Network Coordinator Database Models

Fixed version that properly handles node registration and genesis node detection
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import json

Base = declarative_base()


class NodeType(PyEnum):
    """Node type enumeration"""
    GENESIS = "genesis"
    VALIDATOR = "validator" 
    MINER = "miner"
    RELAY = "relay"
    LIGHT = "light"


class NodeStatus(PyEnum):
    """Node status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OFFLINE = "offline"


class NetworkNode(Base):
    """Network node model with proper genesis node support"""
    __tablename__ = 'network_nodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(255), unique=True, nullable=False, index=True)
    public_ip = Column(String(45), nullable=False)  # IPv4/IPv6
    port = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    os_info = Column(String(255), nullable=True)
    
    # FIXED: Use proper enum handling for node_type
    node_type = Column(Enum(NodeType), nullable=False, default=NodeType.GENESIS)
    
    # FIXED: Add explicit is_genesis boolean field for easy querying
    is_genesis = Column(Boolean, nullable=False, default=False)
    
    public_key = Column(Text, nullable=True)
    signature = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(Enum(NodeStatus), nullable=False, default=NodeStatus.ACTIVE)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    # Keepalive data
    blockchain_height = Column(Integer, default=0)
    connected_peers = Column(Integer, default=0)
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    network_latency = Column(Float, default=0.0)
    ai_model_loaded = Column(Boolean, default=False)
    mining_active = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<NetworkNode(node_id='{self.node_id}', type='{self.node_type}', genesis={self.is_genesis})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'ip': self.public_ip,
            'port': self.port,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'os_info': self.os_info,
            'node_type': self.node_type.value if self.node_type else 'unknown',
            'is_genesis': self.is_genesis,
            'public_key': self.public_key,
            'status': self.status.value if self.status else 'unknown',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'blockchain_height': self.blockchain_height,
            'connected_peers': self.connected_peers,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'network_latency': self.network_latency,
            'ai_model_loaded': self.ai_model_loaded,
            'mining_active': self.mining_active
        }
    
    @classmethod
    def from_registration_data(cls, data):
        """Create NetworkNode from registration data with proper type handling"""
        # FIXED: Properly handle node_type conversion
        node_type_str = data.get('node_type', 'genesis').lower()
        
        # Map string to enum
        node_type = NodeType.GENESIS  # Default
        if node_type_str == 'genesis':
            node_type = NodeType.GENESIS
        elif node_type_str == 'validator':
            node_type = NodeType.VALIDATOR
        elif node_type_str == 'miner':
            node_type = NodeType.MINER
        elif node_type_str == 'relay':
            node_type = NodeType.RELAY
        elif node_type_str == 'light':
            node_type = NodeType.LIGHT
        
        # FIXED: Set is_genesis based on node_type
        is_genesis = (node_type == NodeType.GENESIS)
        
        return cls(
            node_id=data['node_id'],
            public_ip=data['public_ip'],
            port=data['port'],
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            os_info=data.get('os_info'),
            node_type=node_type,
            is_genesis=is_genesis,  # FIXED: Explicitly set this field
            public_key=data.get('public_key'),
            signature=data.get('signature'),
            status=NodeStatus.ACTIVE
        )
    
    def update_keepalive(self, data):
        """Update node with keepalive data"""
        self.blockchain_height = data.get('blockchain_height', 0)
        self.connected_peers = data.get('connected_peers', 0)
        self.cpu_usage = data.get('cpu_usage', 0.0)
        self.memory_usage = data.get('memory_usage', 0.0)
        self.network_latency = data.get('network_latency', 0.0)
        self.ai_model_loaded = data.get('ai_model_loaded', False)
        self.mining_active = data.get('mining_active', False)
        self.status = NodeStatus.ACTIVE
        # last_seen will be updated automatically by onupdate=func.now()