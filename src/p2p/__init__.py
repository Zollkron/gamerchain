"""
P2P networking module for PlayerGold distributed AI nodes.
Provides libp2p-based networking with auto-discovery and secure communication.
"""

from .network import P2PNetwork, MessageType, P2PMessage, PeerInfo
from .propagation import MessagePropagator, PropagationStrategy, PropagationConfig
from .discovery import PeerDiscovery, DiscoveredPeer, DiscoveryMethod
from .synchronization import BlockchainSynchronizer, SyncState, BlockHeader, PeerSyncInfo

__all__ = [
    'P2PNetwork',
    'MessageType', 
    'P2PMessage',
    'PeerInfo',
    'MessagePropagator',
    'PropagationStrategy',
    'PropagationConfig',
    'PeerDiscovery',
    'DiscoveredPeer',
    'DiscoveryMethod',
    'BlockchainSynchronizer',
    'SyncState',
    'BlockHeader',
    'PeerSyncInfo'
]