"""
Fork Detector - Detects and resolves blockchain forks in the network
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import uuid

from .models import NetworkNode, ForkDetection, NetworkConflict, NodeStatus
from .registry import NodeRegistry

logger = logging.getLogger(__name__)


class ForkDetector:
    """Detects and resolves blockchain forks"""
    
    def __init__(self, registry: NodeRegistry):
        self.registry = registry
        self.detected_forks: Dict[str, ForkDetection] = {}
        self.fork_threshold = 2  # Minimum height difference to consider a fork
        self.resolution_timeout = 300  # 5 minutes to resolve forks
    
    async def detect_forks(self) -> List[ForkDetection]:
        """Detect potential blockchain forks in the network"""
        try:
            active_nodes = self.registry.get_active_nodes()
            
            if len(active_nodes) < 2:
                return []  # Need at least 2 nodes to detect forks
            
            # Group nodes by blockchain height
            height_groups = defaultdict(list)
            for node in active_nodes:
                height_groups[node.blockchain_height].append(node)
            
            # Find significant height differences
            heights = sorted(height_groups.keys(), reverse=True)
            detected_forks = []
            
            if len(heights) > 1:
                max_height = heights[0]
                
                for height in heights[1:]:
                    height_diff = max_height - height
                    
                    if height_diff >= self.fork_threshold:
                        # Potential fork detected
                        fork = await self._analyze_fork(height_groups[max_height], height_groups[height])
                        if fork:
                            detected_forks.append(fork)
                            self.detected_forks[fork.fork_id] = fork
            
            return detected_forks
            
        except Exception as e:
            logger.error(f"Fork detection failed: {e}")
            return []
    
    async def _analyze_fork(self, higher_nodes: List[NetworkNode], 
                           lower_nodes: List[NetworkNode]) -> Optional[ForkDetection]:
        """Analyze a potential fork between two groups of nodes"""
        try:
            # Count genesis nodes in each group
            higher_genesis = sum(1 for node in higher_nodes if node.is_genesis)
            lower_genesis = sum(1 for node in lower_nodes if node.is_genesis)
            
            # Determine canonical chain based on rules:
            # 1. More genesis nodes
            # 2. More total nodes
            # 3. Higher blockchain height
            
            canonical_chain = None
            affected_nodes = []
            
            if higher_genesis > lower_genesis:
                canonical_chain = "higher"
                affected_nodes = [node.node_id for node in lower_nodes]
            elif lower_genesis > higher_genesis:
                canonical_chain = "lower"
                affected_nodes = [node.node_id for node in higher_nodes]
            elif len(higher_nodes) > len(lower_nodes):
                canonical_chain = "higher"
                affected_nodes = [node.node_id for node in lower_nodes]
            else:
                canonical_chain = "lower"
                affected_nodes = [node.node_id for node in higher_nodes]
            
            fork_id = str(uuid.uuid4())
            
            conflicting_chains = [
                {
                    "chain_id": "higher",
                    "height": higher_nodes[0].blockchain_height if higher_nodes else 0,
                    "node_count": len(higher_nodes),
                    "genesis_count": higher_genesis,
                    "nodes": [node.node_id for node in higher_nodes]
                },
                {
                    "chain_id": "lower", 
                    "height": lower_nodes[0].blockchain_height if lower_nodes else 0,
                    "node_count": len(lower_nodes),
                    "genesis_count": lower_genesis,
                    "nodes": [node.node_id for node in lower_nodes]
                }
            ]
            
            fork = ForkDetection(
                fork_id=fork_id,
                detected_at=datetime.utcnow(),
                conflicting_chains=conflicting_chains,
                canonical_chain=canonical_chain,
                affected_nodes=affected_nodes,
                resolution_status="pending"
            )
            
            logger.warning(f"Fork detected: {len(higher_nodes)} nodes at height {higher_nodes[0].blockchain_height if higher_nodes else 0}, "
                          f"{len(lower_nodes)} nodes at height {lower_nodes[0].blockchain_height if lower_nodes else 0}")
            
            return fork
            
        except Exception as e:
            logger.error(f"Fork analysis failed: {e}")
            return None
    
    async def resolve_fork(self, fork: ForkDetection) -> bool:
        """Resolve a detected fork"""
        try:
            # Mark affected nodes for chain synchronization
            for node_id in fork.affected_nodes:
                # In a real implementation, we would:
                # 1. Notify the node of the canonical chain
                # 2. Provide sync information
                # 3. Monitor the node's progress
                
                # For now, we'll mark them as needing sync
                node = self.registry.get_node(node_id)
                if node:
                    # Add metadata to indicate sync needed
                    logger.info(f"Node {node_id} needs to sync to canonical chain")
            
            # Update fork status
            fork.resolution_status = "resolved"
            self.detected_forks[fork.fork_id] = fork
            
            logger.info(f"Fork {fork.fork_id} resolved: canonical chain is {fork.canonical_chain}")
            
            return True
            
        except Exception as e:
            logger.error(f"Fork resolution failed: {e}")
            fork.resolution_status = "failed"
            return False
    
    async def detect_network_partitions(self) -> List[NetworkConflict]:
        """Detect network partitions based on node connectivity"""
        try:
            active_nodes = self.registry.get_active_nodes()
            conflicts = []
            
            # Group nodes by connected peers count
            low_connectivity_nodes = [node for node in active_nodes if node.connected_peers < 2]
            
            if len(low_connectivity_nodes) > len(active_nodes) * 0.3:  # More than 30% have low connectivity
                conflict = NetworkConflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type="partition",
                    detected_at=datetime.utcnow(),
                    affected_nodes=[node.node_id for node in low_connectivity_nodes],
                    severity="high" if len(low_connectivity_nodes) > len(active_nodes) * 0.5 else "medium",
                    auto_resolvable=False
                )
                conflicts.append(conflict)
                
                logger.warning(f"Network partition detected: {len(low_connectivity_nodes)} nodes with low connectivity")
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Partition detection failed: {e}")
            return []
    
    async def verify_node_chain(self, node_id: str) -> bool:
        """Verify that a node is on the correct blockchain"""
        try:
            node = self.registry.get_node(node_id)
            if not node:
                return False
            
            # Get consensus height from active nodes
            active_nodes = self.registry.get_active_nodes()
            if not active_nodes:
                return True  # No other nodes to compare with
            
            # Calculate consensus height (median of active nodes)
            heights = sorted([n.blockchain_height for n in active_nodes])
            consensus_height = heights[len(heights) // 2]
            
            # Allow some tolerance for sync delays
            height_tolerance = 5
            
            if abs(node.blockchain_height - consensus_height) <= height_tolerance:
                return True
            else:
                logger.warning(f"Node {node_id} height {node.blockchain_height} differs from consensus {consensus_height}")
                return False
                
        except Exception as e:
            logger.error(f"Chain verification failed for node {node_id}: {e}")
            return False
    
    async def handle_isolated_nodes(self) -> int:
        """Handle nodes that appear to be isolated from the network"""
        try:
            active_nodes = self.registry.get_active_nodes()
            isolated_count = 0
            
            for node in active_nodes:
                # Consider a node isolated if it has no peers and old blockchain height
                if node.connected_peers == 0:
                    # Check if it's significantly behind
                    other_nodes = [n for n in active_nodes if n.node_id != node.node_id]
                    if other_nodes:
                        avg_height = sum(n.blockchain_height for n in other_nodes) / len(other_nodes)
                        
                        if node.blockchain_height < avg_height - 10:  # More than 10 blocks behind
                            # Mark as needing assistance
                            logger.info(f"Isolated node detected: {node.node_id} (height: {node.blockchain_height}, avg: {avg_height:.1f})")
                            isolated_count += 1
                            
                            # In a real implementation, we would:
                            # 1. Provide bootstrap peers
                            # 2. Offer sync assistance
                            # 3. Monitor recovery progress
            
            return isolated_count
            
        except Exception as e:
            logger.error(f"Isolated node handling failed: {e}")
            return 0
    
    def get_fork_status(self) -> Dict:
        """Get current fork detection status"""
        active_forks = [fork for fork in self.detected_forks.values() 
                       if fork.resolution_status == "pending"]
        
        resolved_forks = [fork for fork in self.detected_forks.values() 
                         if fork.resolution_status == "resolved"]
        
        return {
            "active_forks": len(active_forks),
            "resolved_forks": len(resolved_forks),
            "total_forks_detected": len(self.detected_forks),
            "fork_threshold": self.fork_threshold,
            "last_check": datetime.utcnow().isoformat(),
            "forks": [
                {
                    "fork_id": fork.fork_id,
                    "detected_at": fork.detected_at.isoformat(),
                    "status": fork.resolution_status,
                    "affected_nodes": len(fork.affected_nodes),
                    "canonical_chain": fork.canonical_chain
                }
                for fork in self.detected_forks.values()
            ]
        }
    
    async def cleanup_old_forks(self, days_old: int = 7) -> int:
        """Clean up old resolved forks"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)
            removed_count = 0
            
            fork_ids_to_remove = []
            for fork_id, fork in self.detected_forks.items():
                if (fork.resolution_status in ["resolved", "failed"] and 
                    fork.detected_at < cutoff_time):
                    fork_ids_to_remove.append(fork_id)
            
            for fork_id in fork_ids_to_remove:
                del self.detected_forks[fork_id]
                removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old fork records")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Fork cleanup failed: {e}")
            return 0