"""
Resilient Consensus System for AI Nodes

This module implements consensus in network partitions, automatic synchronization
when connectivity is restored, and automatic defenses against attacks.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)


class NetworkState(Enum):
    """State of the network"""
    NORMAL = "normal"
    PARTITIONED = "partitioned"
    RECOVERING = "recovering"
    UNDER_ATTACK = "under_attack"


class AttackType(Enum):
    """Types of detected attacks"""
    SYBIL_ATTACK = "sybil_attack"
    ECLIPSE_ATTACK = "eclipse_attack"
    DOUBLE_SPEND = "double_spend"
    CONSENSUS_MANIPULATION = "consensus_manipulation"
    FLOODING = "flooding"
    TIMING_ATTACK = "timing_attack"


@dataclass
class NetworkPartition:
    """Represents a network partition"""
    partition_id: str
    node_ids: Set[str]
    partition_size: int
    is_majority: bool
    created_at: float = field(default_factory=time.time)
    last_block_hash: Optional[str] = None
    block_height: int = 0


@dataclass
class SyncState:
    """Synchronization state between nodes"""
    node_id: str
    last_sync_time: float
    blocks_behind: int
    sync_in_progress: bool = False
    sync_progress: float = 0.0  # 0.0 to 1.0


@dataclass
class AttackDetection:
    """Attack detection record"""
    attack_type: AttackType
    suspected_nodes: List[str]
    detection_time: float = field(default_factory=time.time)
    confidence: float = 0.0  # 0.0 to 1.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    mitigated: bool = False


class PartitionDetector:
    """Detects and manages network partitions"""
    
    def __init__(self, total_nodes: int, partition_threshold: float = 0.5):
        self.total_nodes = total_nodes
        self.partition_threshold = partition_threshold
        self.partitions: Dict[str, NetworkPartition] = {}
        self.node_to_partition: Dict[str, str] = {}
        
        logger.info("Partition Detector initialized")
    
    def detect_partition(self, reachable_nodes: Set[str], all_nodes: Set[str]) -> Optional[NetworkPartition]:
        """Detect if a network partition has occurred"""
        unreachable_nodes = all_nodes - reachable_nodes
        
        if len(unreachable_nodes) == 0:
            return None
        
        # Calculate partition sizes
        reachable_size = len(reachable_nodes)
        unreachable_size = len(unreachable_nodes)
        
        # Check if this is a significant partition
        if unreachable_size / len(all_nodes) < 0.1:
            # Less than 10% unreachable, likely just node failures
            return None
        
        # Create partition for reachable nodes
        is_majority = reachable_size > (len(all_nodes) * self.partition_threshold)
        
        partition_id = hashlib.sha256(
            f"{sorted(reachable_nodes)}_{time.time()}".encode()
        ).hexdigest()[:16]
        
        partition = NetworkPartition(
            partition_id=partition_id,
            node_ids=reachable_nodes,
            partition_size=reachable_size,
            is_majority=is_majority
        )
        
        self.partitions[partition_id] = partition
        
        # Update node to partition mapping
        for node_id in reachable_nodes:
            self.node_to_partition[node_id] = partition_id
        
        logger.warning(f"Network partition detected: {partition_id} with {reachable_size} nodes (majority: {is_majority})")
        
        return partition
    
    def get_partition(self, node_id: str) -> Optional[NetworkPartition]:
        """Get the partition a node belongs to"""
        partition_id = self.node_to_partition.get(node_id)
        if partition_id:
            return self.partitions.get(partition_id)
        return None
    
    def is_in_majority_partition(self, node_id: str) -> bool:
        """Check if a node is in the majority partition"""
        partition = self.get_partition(node_id)
        return partition.is_majority if partition else False
    
    def merge_partitions(self, partition_ids: List[str]) -> Optional[NetworkPartition]:
        """Merge multiple partitions when connectivity is restored"""
        if not partition_ids:
            return None
        
        # Collect all nodes from partitions
        merged_nodes = set()
        for partition_id in partition_ids:
            if partition_id in self.partitions:
                merged_nodes.update(self.partitions[partition_id].node_ids)
        
        # Create new merged partition
        is_majority = len(merged_nodes) > (self.total_nodes * self.partition_threshold)
        
        merged_partition_id = hashlib.sha256(
            f"{sorted(merged_nodes)}_{time.time()}".encode()
        ).hexdigest()[:16]
        
        merged_partition = NetworkPartition(
            partition_id=merged_partition_id,
            node_ids=merged_nodes,
            partition_size=len(merged_nodes),
            is_majority=is_majority
        )
        
        self.partitions[merged_partition_id] = merged_partition
        
        # Update mappings
        for node_id in merged_nodes:
            self.node_to_partition[node_id] = merged_partition_id
        
        # Remove old partitions
        for partition_id in partition_ids:
            if partition_id in self.partitions:
                del self.partitions[partition_id]
        
        logger.info(f"Merged {len(partition_ids)} partitions into {merged_partition_id}")
        
        return merged_partition
    
    def clear_partition(self, partition_id: str):
        """Clear a partition when network is restored"""
        if partition_id in self.partitions:
            partition = self.partitions[partition_id]
            
            # Clear node mappings
            for node_id in partition.node_ids:
                if self.node_to_partition.get(node_id) == partition_id:
                    del self.node_to_partition[node_id]
            
            del self.partitions[partition_id]
            logger.info(f"Cleared partition {partition_id}")


class AutoSynchronizer:
    """Automatically synchronizes nodes when connectivity is restored"""
    
    def __init__(self):
        self.sync_states: Dict[str, SyncState] = {}
        self.sync_callbacks: Dict[str, Any] = {}
        
        logger.info("Auto Synchronizer initialized")
    
    def register_sync_callback(self, callback_name: str, callback: Any):
        """Register a callback for synchronization operations"""
        self.sync_callbacks[callback_name] = callback
    
    async def synchronize_node(self, node_id: str, reference_nodes: List[str]) -> bool:
        """Synchronize a node with reference nodes"""
        if node_id not in self.sync_states:
            self.sync_states[node_id] = SyncState(
                node_id=node_id,
                last_sync_time=0.0,
                blocks_behind=0
            )
        
        sync_state = self.sync_states[node_id]
        
        if sync_state.sync_in_progress:
            logger.debug(f"Sync already in progress for node {node_id}")
            return False
        
        sync_state.sync_in_progress = True
        sync_state.sync_progress = 0.0
        
        try:
            logger.info(f"Starting synchronization for node {node_id}")
            
            # Step 1: Get blockchain state from reference nodes
            if 'get_blockchain_state' in self.sync_callbacks:
                reference_state = await self.sync_callbacks['get_blockchain_state'](reference_nodes[0])
            else:
                reference_state = {'block_height': 0, 'blocks': []}
            
            sync_state.sync_progress = 0.2
            
            # Step 2: Get local blockchain state
            if 'get_local_state' in self.sync_callbacks:
                local_state = await self.sync_callbacks['get_local_state'](node_id)
            else:
                local_state = {'block_height': 0, 'blocks': []}
            
            sync_state.sync_progress = 0.4
            
            # Step 3: Calculate blocks behind
            blocks_behind = reference_state['block_height'] - local_state['block_height']
            sync_state.blocks_behind = max(0, blocks_behind)
            
            if blocks_behind <= 0:
                logger.info(f"Node {node_id} is already synchronized")
                sync_state.sync_progress = 1.0
                sync_state.last_sync_time = time.time()
                sync_state.sync_in_progress = False
                return True
            
            logger.info(f"Node {node_id} is {blocks_behind} blocks behind")
            
            # Step 4: Download missing blocks
            if 'download_blocks' in self.sync_callbacks:
                success = await self.sync_callbacks['download_blocks'](
                    node_id,
                    local_state['block_height'] + 1,
                    reference_state['block_height']
                )
                
                if not success:
                    logger.error(f"Failed to download blocks for node {node_id}")
                    sync_state.sync_in_progress = False
                    return False
            
            sync_state.sync_progress = 0.8
            
            # Step 5: Validate and apply blocks
            if 'validate_and_apply_blocks' in self.sync_callbacks:
                success = await self.sync_callbacks['validate_and_apply_blocks'](node_id)
                
                if not success:
                    logger.error(f"Failed to validate blocks for node {node_id}")
                    sync_state.sync_in_progress = False
                    return False
            
            sync_state.sync_progress = 1.0
            sync_state.last_sync_time = time.time()
            sync_state.blocks_behind = 0
            
            logger.info(f"Successfully synchronized node {node_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing node {node_id}: {e}")
            return False
        finally:
            sync_state.sync_in_progress = False
    
    async def synchronize_partition(self, partition: NetworkPartition, reference_partition: NetworkPartition) -> int:
        """Synchronize all nodes in a partition with a reference partition"""
        logger.info(f"Synchronizing partition {partition.partition_id} with {reference_partition.partition_id}")
        
        # Get reference nodes from the reference partition
        reference_nodes = list(reference_partition.node_ids)[:3]  # Use top 3 nodes
        
        # Synchronize each node in the partition
        successful_syncs = 0
        
        for node_id in partition.node_ids:
            success = await self.synchronize_node(node_id, reference_nodes)
            if success:
                successful_syncs += 1
        
        logger.info(f"Synchronized {successful_syncs}/{len(partition.node_ids)} nodes in partition")
        
        return successful_syncs
    
    def get_sync_state(self, node_id: str) -> Optional[SyncState]:
        """Get synchronization state for a node"""
        return self.sync_states.get(node_id)
    
    def get_sync_progress(self, node_id: str) -> float:
        """Get synchronization progress for a node"""
        sync_state = self.sync_states.get(node_id)
        return sync_state.sync_progress if sync_state else 0.0


class AttackDefenseSystem:
    """Automatic defense system against attacks and anomalous behavior"""
    
    def __init__(self, detection_threshold: float = 0.7):
        self.detection_threshold = detection_threshold
        self.detected_attacks: List[AttackDetection] = []
        self.node_behavior_scores: Dict[str, float] = defaultdict(lambda: 1.0)
        self.blocked_nodes: Set[str] = set()
        self.defense_callbacks: Dict[str, Any] = {}
        
        logger.info("Attack Defense System initialized")
    
    def register_defense_callback(self, callback_name: str, callback: Any):
        """Register a callback for defense actions"""
        self.defense_callbacks[callback_name] = callback
    
    def analyze_node_behavior(self, node_id: str, behavior_data: Dict[str, Any]) -> float:
        """Analyze node behavior and return anomaly score (0.0 = normal, 1.0 = highly anomalous)"""
        anomaly_score = 0.0
        
        # Check for timing anomalies
        if 'response_times' in behavior_data:
            response_times = behavior_data['response_times']
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                if avg_time > 100:  # More than 100ms average
                    anomaly_score += 0.3
        
        # Check for validation failures
        if 'validation_failures' in behavior_data:
            failure_rate = behavior_data['validation_failures'] / max(behavior_data.get('total_validations', 1), 1)
            if failure_rate > 0.2:  # More than 20% failures
                anomaly_score += 0.4
        
        # Check for suspicious patterns
        if 'pattern_score' in behavior_data:
            anomaly_score += behavior_data['pattern_score'] * 0.3
        
        return min(anomaly_score, 1.0)
    
    def detect_sybil_attack(self, node_connections: Dict[str, Set[str]]) -> Optional[AttackDetection]:
        """Detect potential Sybil attack"""
        # Look for clusters of nodes that only connect to each other
        suspicious_clusters = []
        
        for node_id, connections in node_connections.items():
            # Check if node has very few connections
            if len(connections) < 3:
                continue
            
            # Check if connections are isolated
            external_connections = 0
            for connected_node in connections:
                if connected_node in node_connections:
                    external_connections += len(node_connections[connected_node] - connections)
            
            isolation_ratio = external_connections / (len(connections) * len(node_connections))
            
            if isolation_ratio < 0.1:  # Less than 10% external connections
                suspicious_clusters.append(node_id)
        
        if len(suspicious_clusters) >= 3:
            attack = AttackDetection(
                attack_type=AttackType.SYBIL_ATTACK,
                suspected_nodes=suspicious_clusters,
                confidence=0.7,
                evidence={'isolation_ratio': 'low', 'cluster_size': len(suspicious_clusters)}
            )
            
            self.detected_attacks.append(attack)
            logger.warning(f"Potential Sybil attack detected: {len(suspicious_clusters)} suspicious nodes")
            
            return attack
        
        return None
    
    def detect_flooding_attack(self, message_rates: Dict[str, int]) -> Optional[AttackDetection]:
        """Detect flooding attack based on message rates"""
        suspicious_nodes = []
        
        # Calculate average message rate
        if not message_rates:
            return None
        
        avg_rate = sum(message_rates.values()) / len(message_rates)
        threshold = avg_rate * 5  # 5x average is suspicious
        
        for node_id, rate in message_rates.items():
            if rate > threshold:
                suspicious_nodes.append(node_id)
        
        if suspicious_nodes:
            attack = AttackDetection(
                attack_type=AttackType.FLOODING,
                suspected_nodes=suspicious_nodes,
                confidence=0.8,
                evidence={'avg_rate': avg_rate, 'threshold': threshold}
            )
            
            self.detected_attacks.append(attack)
            logger.warning(f"Flooding attack detected from {len(suspicious_nodes)} nodes")
            
            return attack
        
        return None
    
    def detect_consensus_manipulation(self, validation_patterns: Dict[str, List[bool]]) -> Optional[AttackDetection]:
        """Detect attempts to manipulate consensus"""
        suspicious_nodes = []
        
        for node_id, validations in validation_patterns.items():
            if len(validations) < 10:
                continue
            
            # Check for alternating pattern (trying to stay under radar)
            alternations = sum(1 for i in range(len(validations) - 1) 
                             if validations[i] != validations[i + 1])
            alternation_rate = alternations / (len(validations) - 1)
            
            # Check for consistent disagreement
            agreement_rate = sum(validations) / len(validations)
            
            if alternation_rate > 0.7 or agreement_rate < 0.3:
                suspicious_nodes.append(node_id)
        
        if suspicious_nodes:
            attack = AttackDetection(
                attack_type=AttackType.CONSENSUS_MANIPULATION,
                suspected_nodes=suspicious_nodes,
                confidence=0.75,
                evidence={'pattern': 'suspicious_validation_pattern'}
            )
            
            self.detected_attacks.append(attack)
            logger.warning(f"Consensus manipulation detected from {len(suspicious_nodes)} nodes")
            
            return attack
        
        return None
    
    async def mitigate_attack(self, attack: AttackDetection) -> bool:
        """Mitigate a detected attack"""
        if attack.mitigated:
            return True
        
        logger.info(f"Mitigating {attack.attack_type.value} attack")
        
        try:
            # Block suspected nodes
            for node_id in attack.suspected_nodes:
                self.blocked_nodes.add(node_id)
                self.node_behavior_scores[node_id] = 0.0
                
                # Call defense callback if available
                if 'block_node' in self.defense_callbacks:
                    await self.defense_callbacks['block_node'](node_id)
            
            # Apply specific mitigations based on attack type
            if attack.attack_type == AttackType.FLOODING:
                if 'enable_rate_limiting' in self.defense_callbacks:
                    await self.defense_callbacks['enable_rate_limiting']()
            
            elif attack.attack_type == AttackType.SYBIL_ATTACK:
                if 'increase_validation_requirements' in self.defense_callbacks:
                    await self.defense_callbacks['increase_validation_requirements']()
            
            elif attack.attack_type == AttackType.CONSENSUS_MANIPULATION:
                if 'increase_consensus_threshold' in self.defense_callbacks:
                    await self.defense_callbacks['increase_consensus_threshold']()
            
            attack.mitigated = True
            logger.info(f"Successfully mitigated {attack.attack_type.value} attack")
            
            return True
            
        except Exception as e:
            logger.error(f"Error mitigating attack: {e}")
            return False
    
    def is_node_blocked(self, node_id: str) -> bool:
        """Check if a node is blocked"""
        return node_id in self.blocked_nodes
    
    def unblock_node(self, node_id: str) -> bool:
        """Unblock a node (after manual review or timeout)"""
        if node_id in self.blocked_nodes:
            self.blocked_nodes.remove(node_id)
            self.node_behavior_scores[node_id] = 0.5  # Start with reduced score
            logger.info(f"Unblocked node {node_id}")
            return True
        return False
    
    def get_attack_history(self) -> List[AttackDetection]:
        """Get history of detected attacks"""
        return self.detected_attacks.copy()
    
    def get_defense_stats(self) -> Dict[str, Any]:
        """Get defense system statistics"""
        total_attacks = len(self.detected_attacks)
        mitigated_attacks = sum(1 for a in self.detected_attacks if a.mitigated)
        
        attack_types = defaultdict(int)
        for attack in self.detected_attacks:
            attack_types[attack.attack_type.value] += 1
        
        return {
            'total_attacks_detected': total_attacks,
            'mitigated_attacks': mitigated_attacks,
            'blocked_nodes': len(self.blocked_nodes),
            'attack_types': dict(attack_types),
            'mitigation_rate': (mitigated_attacks / total_attacks * 100) if total_attacks > 0 else 0.0
        }


class ResilientConsensusSystem:
    """Main resilient consensus system coordinating all components"""
    
    def __init__(self, total_nodes: int):
        self.total_nodes = total_nodes
        self.partition_detector = PartitionDetector(total_nodes)
        self.auto_synchronizer = AutoSynchronizer()
        self.attack_defense = AttackDefenseSystem()
        
        self.network_state = NetworkState.NORMAL
        self.running = False
        
        logger.info("Resilient Consensus System initialized")
    
    async def start(self):
        """Start the resilient consensus system"""
        logger.info("Starting Resilient Consensus System")
        self.running = True
        
        # Start monitoring loops
        asyncio.create_task(self._partition_monitoring_loop())
        asyncio.create_task(self._attack_detection_loop())
        
        logger.info("Resilient Consensus System started")
    
    async def stop(self):
        """Stop the resilient consensus system"""
        logger.info("Stopping Resilient Consensus System")
        self.running = False
        logger.info("Resilient Consensus System stopped")
    
    async def _partition_monitoring_loop(self):
        """Monitor for network partitions"""
        while self.running:
            try:
                # This would be called with actual network data
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in partition monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _attack_detection_loop(self):
        """Monitor for attacks"""
        while self.running:
            try:
                # This would be called with actual behavior data
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in attack detection: {e}")
                await asyncio.sleep(10)
    
    async def handle_partition(self, reachable_nodes: Set[str], all_nodes: Set[str]) -> bool:
        """Handle a detected network partition"""
        partition = self.partition_detector.detect_partition(reachable_nodes, all_nodes)
        
        if not partition:
            return False
        
        self.network_state = NetworkState.PARTITIONED
        
        if partition.is_majority:
            logger.info(f"Node is in majority partition, continuing consensus")
            return True
        else:
            logger.warning(f"Node is in minority partition, pausing consensus")
            return False
    
    async def handle_partition_recovery(self, partition_ids: List[str]) -> bool:
        """Handle recovery from network partition"""
        logger.info("Network partition recovery initiated")
        self.network_state = NetworkState.RECOVERING
        
        try:
            # Merge partitions
            merged_partition = self.partition_detector.merge_partitions(partition_ids)
            
            if not merged_partition:
                return False
            
            # Synchronize nodes
            # In a real implementation, we would identify which partition has the canonical chain
            # For now, assume the first partition is canonical
            reference_partition_id = partition_ids[0]
            reference_partition = self.partition_detector.partitions.get(reference_partition_id)
            
            if reference_partition:
                await self.auto_synchronizer.synchronize_partition(merged_partition, reference_partition)
            
            # Clear partition state
            for partition_id in partition_ids:
                self.partition_detector.clear_partition(partition_id)
            
            self.network_state = NetworkState.NORMAL
            logger.info("Network partition recovery completed")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during partition recovery: {e}")
            return False
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        return {
            'network_state': self.network_state.value,
            'active_partitions': len(self.partition_detector.partitions),
            'blocked_nodes': len(self.attack_defense.blocked_nodes),
            'detected_attacks': len(self.attack_defense.detected_attacks),
            'defense_stats': self.attack_defense.get_defense_stats()
        }
