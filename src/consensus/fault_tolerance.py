"""
Fault Tolerance and Automatic Recovery System for AI Nodes

This module implements automatic detection of unresponsive nodes,
load redistribution, and automatic restart with integrity verification.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Status of an AI node"""
    ACTIVE = "active"
    UNRESPONSIVE = "unresponsive"
    RECOVERING = "recovering"
    FAILED = "failed"
    EXCLUDED = "excluded"


class HealthCheckType(Enum):
    """Types of health checks"""
    HEARTBEAT = "heartbeat"
    CHALLENGE_RESPONSE = "challenge_response"
    VALIDATION_PARTICIPATION = "validation_participation"
    NETWORK_CONNECTIVITY = "network_connectivity"


@dataclass
class NodeHealthMetrics:
    """Health metrics for a node"""
    node_id: str
    status: NodeStatus = NodeStatus.ACTIVE
    last_heartbeat: float = field(default_factory=time.time)
    last_challenge_response: float = field(default_factory=time.time)
    last_validation: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    total_failures: int = 0
    recovery_attempts: int = 0
    last_recovery_attempt: float = 0.0
    response_times: List[float] = field(default_factory=list)
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times[-100:])  # Last 100 responses
    
    @property
    def is_healthy(self) -> bool:
        """Check if node is healthy"""
        current_time = time.time()
        return (
            self.status == NodeStatus.ACTIVE and
            current_time - self.last_heartbeat < 60 and  # Heartbeat within 60s
            self.consecutive_failures < 3
        )


@dataclass
class RecoveryAction:
    """Recovery action to be performed"""
    node_id: str
    action_type: str
    timestamp: float = field(default_factory=time.time)
    parameters: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    error_message: Optional[str] = None


class NodeHealthMonitor:
    """Monitors health of AI nodes and detects unresponsive nodes"""
    
    def __init__(self, 
                 heartbeat_timeout: float = 60.0,
                 challenge_timeout: float = 120.0,
                 max_consecutive_failures: int = 3):
        self.heartbeat_timeout = heartbeat_timeout
        self.challenge_timeout = challenge_timeout
        self.max_consecutive_failures = max_consecutive_failures
        
        self.node_metrics: Dict[str, NodeHealthMetrics] = {}
        self.health_check_callbacks: Dict[HealthCheckType, Callable] = {}
        self.running = False
        
        logger.info("Node Health Monitor initialized")
    
    def register_node(self, node_id: str) -> bool:
        """Register a node for health monitoring"""
        if node_id not in self.node_metrics:
            self.node_metrics[node_id] = NodeHealthMetrics(node_id=node_id)
            logger.info(f"Registered node {node_id} for health monitoring")
            return True
        return False
    
    def unregister_node(self, node_id: str) -> bool:
        """Unregister a node from health monitoring"""
        if node_id in self.node_metrics:
            del self.node_metrics[node_id]
            logger.info(f"Unregistered node {node_id} from health monitoring")
            return True
        return False
    
    def update_heartbeat(self, node_id: str) -> bool:
        """Update heartbeat timestamp for a node"""
        if node_id in self.node_metrics:
            self.node_metrics[node_id].last_heartbeat = time.time()
            return True
        return False
    
    def update_challenge_response(self, node_id: str, response_time_ms: float) -> bool:
        """Update challenge response metrics for a node"""
        if node_id in self.node_metrics:
            metrics = self.node_metrics[node_id]
            metrics.last_challenge_response = time.time()
            metrics.response_times.append(response_time_ms)
            
            # Keep only last 100 response times
            if len(metrics.response_times) > 100:
                metrics.response_times = metrics.response_times[-100:]
            
            return True
        return False
    
    def update_validation_participation(self, node_id: str) -> bool:
        """Update validation participation timestamp"""
        if node_id in self.node_metrics:
            self.node_metrics[node_id].last_validation = time.time()
            return True
        return False
    
    def record_failure(self, node_id: str) -> bool:
        """Record a failure for a node"""
        if node_id in self.node_metrics:
            metrics = self.node_metrics[node_id]
            metrics.consecutive_failures += 1
            metrics.total_failures += 1
            
            # Update status if too many consecutive failures
            if metrics.consecutive_failures >= self.max_consecutive_failures:
                metrics.status = NodeStatus.UNRESPONSIVE
                logger.warning(f"Node {node_id} marked as unresponsive after {metrics.consecutive_failures} failures")
            
            return True
        return False
    
    def record_success(self, node_id: str) -> bool:
        """Record a successful operation for a node"""
        if node_id in self.node_metrics:
            metrics = self.node_metrics[node_id]
            metrics.consecutive_failures = 0
            
            # Restore to active if recovering
            if metrics.status == NodeStatus.RECOVERING:
                metrics.status = NodeStatus.ACTIVE
                logger.info(f"Node {node_id} recovered and marked as active")
            
            return True
        return False
    
    def check_node_health(self, node_id: str) -> bool:
        """Check if a specific node is healthy"""
        if node_id not in self.node_metrics:
            return False
        
        metrics = self.node_metrics[node_id]
        current_time = time.time()
        
        # Check heartbeat timeout
        if current_time - metrics.last_heartbeat > self.heartbeat_timeout:
            logger.warning(f"Node {node_id} heartbeat timeout")
            self.record_failure(node_id)
            return False
        
        # Check challenge response timeout
        if current_time - metrics.last_challenge_response > self.challenge_timeout:
            logger.warning(f"Node {node_id} challenge response timeout")
            self.record_failure(node_id)
            return False
        
        return metrics.is_healthy
    
    def get_unresponsive_nodes(self) -> List[str]:
        """Get list of unresponsive nodes"""
        unresponsive = []
        current_time = time.time()
        
        for node_id, metrics in self.node_metrics.items():
            if (metrics.status == NodeStatus.UNRESPONSIVE or
                current_time - metrics.last_heartbeat > self.heartbeat_timeout):
                unresponsive.append(node_id)
        
        return unresponsive
    
    def get_active_nodes(self) -> List[str]:
        """Get list of active healthy nodes"""
        return [
            node_id for node_id, metrics in self.node_metrics.items()
            if metrics.status == NodeStatus.ACTIVE and metrics.is_healthy
        ]
    
    def get_node_metrics(self, node_id: str) -> Optional[NodeHealthMetrics]:
        """Get health metrics for a specific node"""
        return self.node_metrics.get(node_id)
    
    def get_all_metrics(self) -> Dict[str, NodeHealthMetrics]:
        """Get all node health metrics"""
        return self.node_metrics.copy()


class LoadBalancer:
    """Redistributes load among active nodes when nodes fail"""
    
    def __init__(self, health_monitor: NodeHealthMonitor):
        self.health_monitor = health_monitor
        self.node_loads: Dict[str, int] = defaultdict(int)
        self.pending_tasks: List[Dict[str, Any]] = []
        
        logger.info("Load Balancer initialized")
    
    def assign_task(self, task: Dict[str, Any]) -> Optional[str]:
        """Assign a task to the least loaded active node"""
        active_nodes = self.health_monitor.get_active_nodes()
        
        if not active_nodes:
            logger.warning("No active nodes available for task assignment")
            self.pending_tasks.append(task)
            return None
        
        # Find node with minimum load
        min_load_node = min(active_nodes, key=lambda n: self.node_loads[n])
        
        # Assign task
        self.node_loads[min_load_node] += 1
        logger.debug(f"Assigned task to node {min_load_node} (load: {self.node_loads[min_load_node]})")
        
        return min_load_node
    
    def complete_task(self, node_id: str) -> bool:
        """Mark a task as completed for a node"""
        if node_id in self.node_loads and self.node_loads[node_id] > 0:
            self.node_loads[node_id] -= 1
            return True
        return False
    
    def redistribute_load(self, failed_node_id: str) -> List[Dict[str, Any]]:
        """Redistribute tasks from a failed node to active nodes"""
        if failed_node_id not in self.node_loads:
            return []
        
        failed_load = self.node_loads[failed_node_id]
        self.node_loads[failed_node_id] = 0
        
        logger.info(f"Redistributing {failed_load} tasks from failed node {failed_node_id}")
        
        # Create placeholder tasks for redistribution
        redistributed_tasks = []
        for i in range(failed_load):
            task = {
                'type': 'redistributed',
                'original_node': failed_node_id,
                'task_index': i
            }
            redistributed_tasks.append(task)
            
            # Try to assign immediately
            assigned_node = self.assign_task(task)
            if assigned_node:
                logger.debug(f"Redistributed task {i} to node {assigned_node}")
        
        return redistributed_tasks
    
    def process_pending_tasks(self) -> int:
        """Process pending tasks when nodes become available"""
        if not self.pending_tasks:
            return 0
        
        processed = 0
        remaining_tasks = []
        
        for task in self.pending_tasks:
            assigned_node = self.assign_task(task)
            if assigned_node:
                processed += 1
                logger.debug(f"Processed pending task, assigned to {assigned_node}")
            else:
                remaining_tasks.append(task)
        
        self.pending_tasks = remaining_tasks
        
        if processed > 0:
            logger.info(f"Processed {processed} pending tasks")
        
        return processed
    
    def get_load_distribution(self) -> Dict[str, int]:
        """Get current load distribution across nodes"""
        return dict(self.node_loads)
    
    def get_pending_task_count(self) -> int:
        """Get number of pending tasks"""
        return len(self.pending_tasks)


class AutoRecoveryManager:
    """Manages automatic recovery of failed nodes"""
    
    def __init__(self, 
                 health_monitor: NodeHealthMonitor,
                 load_balancer: LoadBalancer,
                 max_recovery_attempts: int = 3,
                 recovery_cooldown: float = 300.0):
        self.health_monitor = health_monitor
        self.load_balancer = load_balancer
        self.max_recovery_attempts = max_recovery_attempts
        self.recovery_cooldown = recovery_cooldown
        
        self.recovery_callbacks: Dict[str, Callable] = {}
        self.recovery_history: List[RecoveryAction] = []
        self.running = False
        
        logger.info("Auto Recovery Manager initialized")
    
    def register_recovery_callback(self, action_type: str, callback: Callable) -> bool:
        """Register a callback for recovery actions"""
        self.recovery_callbacks[action_type] = callback
        logger.debug(f"Registered recovery callback for {action_type}")
        return True
    
    async def attempt_node_recovery(self, node_id: str) -> RecoveryAction:
        """Attempt to recover a failed node"""
        metrics = self.health_monitor.get_node_metrics(node_id)
        
        if not metrics:
            return RecoveryAction(
                node_id=node_id,
                action_type="recovery_failed",
                success=False,
                error_message="Node not found in health monitor"
            )
        
        # Check if we can attempt recovery
        current_time = time.time()
        if metrics.recovery_attempts >= self.max_recovery_attempts:
            logger.error(f"Node {node_id} exceeded max recovery attempts")
            metrics.status = NodeStatus.FAILED
            return RecoveryAction(
                node_id=node_id,
                action_type="recovery_failed",
                success=False,
                error_message="Max recovery attempts exceeded"
            )
        
        # Check cooldown period
        if current_time - metrics.last_recovery_attempt < self.recovery_cooldown:
            remaining = self.recovery_cooldown - (current_time - metrics.last_recovery_attempt)
            logger.debug(f"Node {node_id} in recovery cooldown ({remaining:.0f}s remaining)")
            return RecoveryAction(
                node_id=node_id,
                action_type="recovery_cooldown",
                success=False,
                error_message=f"Cooldown period active ({remaining:.0f}s remaining)"
            )
        
        # Update recovery attempt
        metrics.recovery_attempts += 1
        metrics.last_recovery_attempt = current_time
        metrics.status = NodeStatus.RECOVERING
        
        logger.info(f"Attempting recovery for node {node_id} (attempt {metrics.recovery_attempts}/{self.max_recovery_attempts})")
        
        # Perform recovery steps
        recovery_action = RecoveryAction(
            node_id=node_id,
            action_type="node_restart",
            parameters={'attempt': metrics.recovery_attempts}
        )
        
        try:
            # Step 1: Verify node integrity
            integrity_ok = await self._verify_node_integrity(node_id)
            if not integrity_ok:
                recovery_action.success = False
                recovery_action.error_message = "Node integrity verification failed"
                self.recovery_history.append(recovery_action)
                return recovery_action
            
            # Step 2: Restart node
            if 'restart_node' in self.recovery_callbacks:
                restart_success = await self.recovery_callbacks['restart_node'](node_id)
                if not restart_success:
                    recovery_action.success = False
                    recovery_action.error_message = "Node restart failed"
                    self.recovery_history.append(recovery_action)
                    return recovery_action
            
            # Step 3: Wait for node to come back online
            await asyncio.sleep(5)
            
            # Step 4: Verify node is responsive
            if 'verify_responsive' in self.recovery_callbacks:
                is_responsive = await self.recovery_callbacks['verify_responsive'](node_id)
                if not is_responsive:
                    recovery_action.success = False
                    recovery_action.error_message = "Node not responsive after restart"
                    self.recovery_history.append(recovery_action)
                    return recovery_action
            
            # Recovery successful
            recovery_action.success = True
            metrics.status = NodeStatus.ACTIVE
            metrics.consecutive_failures = 0
            
            logger.info(f"Successfully recovered node {node_id}")
            
        except Exception as e:
            recovery_action.success = False
            recovery_action.error_message = f"Recovery exception: {str(e)}"
            logger.error(f"Error recovering node {node_id}: {e}")
        
        self.recovery_history.append(recovery_action)
        return recovery_action
    
    async def _verify_node_integrity(self, node_id: str) -> bool:
        """Verify integrity of a node before recovery"""
        try:
            if 'verify_integrity' in self.recovery_callbacks:
                return await self.recovery_callbacks['verify_integrity'](node_id)
            
            # Default: assume integrity is OK
            return True
            
        except Exception as e:
            logger.error(f"Error verifying integrity for node {node_id}: {e}")
            return False
    
    async def recovery_loop(self):
        """Main recovery loop that monitors and recovers failed nodes"""
        logger.info("Starting auto-recovery loop")
        self.running = True
        
        while self.running:
            try:
                # Get unresponsive nodes
                unresponsive_nodes = self.health_monitor.get_unresponsive_nodes()
                
                for node_id in unresponsive_nodes:
                    # Redistribute load from failed node
                    self.load_balancer.redistribute_load(node_id)
                    
                    # Attempt recovery
                    recovery_result = await self.attempt_node_recovery(node_id)
                    
                    if recovery_result.success:
                        logger.info(f"Node {node_id} recovered successfully")
                        # Process any pending tasks
                        self.load_balancer.process_pending_tasks()
                    else:
                        logger.warning(f"Failed to recover node {node_id}: {recovery_result.error_message}")
                
                # Sleep before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in recovery loop: {e}")
                await asyncio.sleep(10)
        
        logger.info("Auto-recovery loop stopped")
    
    def stop(self):
        """Stop the recovery loop"""
        self.running = False
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        if not self.recovery_history:
            return {
                'total_attempts': 0,
                'successful_recoveries': 0,
                'failed_recoveries': 0,
                'success_rate': 0.0
            }
        
        total = len(self.recovery_history)
        successful = sum(1 for r in self.recovery_history if r.success)
        failed = total - successful
        
        return {
            'total_attempts': total,
            'successful_recoveries': successful,
            'failed_recoveries': failed,
            'success_rate': (successful / total) * 100 if total > 0 else 0.0,
            'recent_recoveries': self.recovery_history[-10:]
        }


class FaultToleranceSystem:
    """Main fault tolerance system coordinating all components"""
    
    def __init__(self,
                 heartbeat_timeout: float = 60.0,
                 challenge_timeout: float = 120.0,
                 max_recovery_attempts: int = 3):
        self.health_monitor = NodeHealthMonitor(
            heartbeat_timeout=heartbeat_timeout,
            challenge_timeout=challenge_timeout
        )
        self.load_balancer = LoadBalancer(self.health_monitor)
        self.recovery_manager = AutoRecoveryManager(
            self.health_monitor,
            self.load_balancer,
            max_recovery_attempts=max_recovery_attempts
        )
        
        self.running = False
        
        logger.info("Fault Tolerance System initialized")
    
    async def start(self):
        """Start the fault tolerance system"""
        logger.info("Starting Fault Tolerance System")
        self.running = True
        
        # Start recovery loop
        asyncio.create_task(self.recovery_manager.recovery_loop())
        
        logger.info("Fault Tolerance System started")
    
    async def stop(self):
        """Stop the fault tolerance system"""
        logger.info("Stopping Fault Tolerance System")
        self.running = False
        self.recovery_manager.stop()
        logger.info("Fault Tolerance System stopped")
    
    def register_node(self, node_id: str) -> bool:
        """Register a node with the fault tolerance system"""
        return self.health_monitor.register_node(node_id)
    
    def unregister_node(self, node_id: str) -> bool:
        """Unregister a node from the fault tolerance system"""
        return self.health_monitor.unregister_node(node_id)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        active_nodes = self.health_monitor.get_active_nodes()
        unresponsive_nodes = self.health_monitor.get_unresponsive_nodes()
        load_distribution = self.load_balancer.get_load_distribution()
        recovery_stats = self.recovery_manager.get_recovery_stats()
        
        return {
            'active_nodes': len(active_nodes),
            'unresponsive_nodes': len(unresponsive_nodes),
            'total_nodes': len(self.health_monitor.node_metrics),
            'pending_tasks': self.load_balancer.get_pending_task_count(),
            'load_distribution': load_distribution,
            'recovery_stats': recovery_stats,
            'system_healthy': len(active_nodes) > 0
        }
