"""
Tests for Fault Tolerance and Auto-Recovery System
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from src.consensus.fault_tolerance import (
    NodeHealthMonitor,
    LoadBalancer,
    AutoRecoveryManager,
    FaultToleranceSystem,
    NodeStatus,
    NodeHealthMetrics,
    RecoveryAction
)


class TestNodeHealthMonitor:
    """Tests for NodeHealthMonitor"""
    
    def test_register_node(self):
        """Test node registration"""
        monitor = NodeHealthMonitor()
        
        assert monitor.register_node("node1")
        assert "node1" in monitor.node_metrics
        assert monitor.node_metrics["node1"].status == NodeStatus.ACTIVE
    
    def test_register_duplicate_node(self):
        """Test registering same node twice"""
        monitor = NodeHealthMonitor()
        
        assert monitor.register_node("node1")
        assert not monitor.register_node("node1")  # Should return False
    
    def test_unregister_node(self):
        """Test node unregistration"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        
        assert monitor.unregister_node("node1")
        assert "node1" not in monitor.node_metrics
    
    def test_update_heartbeat(self):
        """Test heartbeat update"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        
        initial_time = monitor.node_metrics["node1"].last_heartbeat
        time.sleep(0.1)
        
        assert monitor.update_heartbeat("node1")
        assert monitor.node_metrics["node1"].last_heartbeat > initial_time
    
    def test_update_challenge_response(self):
        """Test challenge response update"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        
        assert monitor.update_challenge_response("node1", 50.0)
        assert 50.0 in monitor.node_metrics["node1"].response_times
    
    def test_record_failure(self):
        """Test failure recording"""
        monitor = NodeHealthMonitor(max_consecutive_failures=3)
        monitor.register_node("node1")
        
        # Record failures
        monitor.record_failure("node1")
        assert monitor.node_metrics["node1"].consecutive_failures == 1
        assert monitor.node_metrics["node1"].status == NodeStatus.ACTIVE
        
        monitor.record_failure("node1")
        monitor.record_failure("node1")
        
        # Should be marked unresponsive after 3 failures
        assert monitor.node_metrics["node1"].consecutive_failures == 3
        assert monitor.node_metrics["node1"].status == NodeStatus.UNRESPONSIVE
    
    def test_record_success(self):
        """Test success recording resets failures"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        
        # Record some failures
        monitor.record_failure("node1")
        monitor.record_failure("node1")
        assert monitor.node_metrics["node1"].consecutive_failures == 2
        
        # Record success should reset
        monitor.record_success("node1")
        assert monitor.node_metrics["node1"].consecutive_failures == 0
    
    def test_check_node_health_timeout(self):
        """Test node health check with timeout"""
        monitor = NodeHealthMonitor(heartbeat_timeout=0.1, max_consecutive_failures=1)
        monitor.register_node("node1")
        
        # Initially healthy
        assert monitor.check_node_health("node1")
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Should be unhealthy now
        assert not monitor.check_node_health("node1")
        # After one failure with max_consecutive_failures=1, should be unresponsive
        assert monitor.node_metrics["node1"].status == NodeStatus.UNRESPONSIVE
    
    def test_get_unresponsive_nodes(self):
        """Test getting list of unresponsive nodes"""
        monitor = NodeHealthMonitor(heartbeat_timeout=0.1)
        monitor.register_node("node1")
        monitor.register_node("node2")
        monitor.register_node("node3")
        
        # Update node1 heartbeat to keep it fresh
        monitor.update_heartbeat("node1")
        
        # Mark node2 as unresponsive
        monitor.node_metrics["node2"].status = NodeStatus.UNRESPONSIVE
        
        # Wait for node3 to timeout
        time.sleep(0.2)
        
        unresponsive = monitor.get_unresponsive_nodes()
        assert "node2" in unresponsive
        assert "node3" in unresponsive
        # node1 should not be in unresponsive since we just updated its heartbeat
        # But it might be if the sleep caused it to timeout too, so let's update it again
        monitor.update_heartbeat("node1")
        unresponsive = monitor.get_unresponsive_nodes()
        assert "node1" not in unresponsive  # Still has recent heartbeat
    
    def test_get_active_nodes(self):
        """Test getting list of active nodes"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.register_node("node2")
        monitor.register_node("node3")
        
        # Mark node2 as unresponsive
        monitor.node_metrics["node2"].status = NodeStatus.UNRESPONSIVE
        
        active = monitor.get_active_nodes()
        assert "node1" in active
        assert "node3" in active
        assert "node2" not in active
    
    def test_avg_response_time(self):
        """Test average response time calculation"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        
        # Add response times
        monitor.update_challenge_response("node1", 50.0)
        monitor.update_challenge_response("node1", 60.0)
        monitor.update_challenge_response("node1", 70.0)
        
        metrics = monitor.get_node_metrics("node1")
        assert metrics.avg_response_time == 60.0


class TestLoadBalancer:
    """Tests for LoadBalancer"""
    
    def test_assign_task_to_active_node(self):
        """Test task assignment to active node"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.register_node("node2")
        
        balancer = LoadBalancer(monitor)
        
        task = {'type': 'validation', 'data': 'test'}
        assigned_node = balancer.assign_task(task)
        
        assert assigned_node in ["node1", "node2"]
        assert balancer.node_loads[assigned_node] == 1
    
    def test_assign_task_no_active_nodes(self):
        """Test task assignment when no nodes are active"""
        monitor = NodeHealthMonitor()
        balancer = LoadBalancer(monitor)
        
        task = {'type': 'validation', 'data': 'test'}
        assigned_node = balancer.assign_task(task)
        
        assert assigned_node is None
        assert len(balancer.pending_tasks) == 1
    
    def test_load_distribution(self):
        """Test load is distributed evenly"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.register_node("node2")
        
        balancer = LoadBalancer(monitor)
        
        # Assign multiple tasks
        for i in range(10):
            task = {'type': 'validation', 'index': i}
            balancer.assign_task(task)
        
        # Load should be distributed
        load_dist = balancer.get_load_distribution()
        assert load_dist["node1"] + load_dist["node2"] == 10
        assert abs(load_dist["node1"] - load_dist["node2"]) <= 1  # Roughly even
    
    def test_complete_task(self):
        """Test task completion"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        
        balancer = LoadBalancer(monitor)
        
        task = {'type': 'validation'}
        balancer.assign_task(task)
        
        assert balancer.node_loads["node1"] == 1
        assert balancer.complete_task("node1")
        assert balancer.node_loads["node1"] == 0
    
    def test_redistribute_load(self):
        """Test load redistribution from failed node"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.register_node("node2")
        monitor.register_node("node3")
        
        balancer = LoadBalancer(monitor)
        
        # Assign tasks to node1
        for i in range(5):
            task = {'type': 'validation', 'index': i}
            # Manually assign to node1
            balancer.node_loads["node1"] += 1
        
        # Mark node1 as failed and redistribute
        monitor.node_metrics["node1"].status = NodeStatus.FAILED
        redistributed = balancer.redistribute_load("node1")
        
        assert len(redistributed) == 5
        assert balancer.node_loads["node1"] == 0
        # Load should be redistributed to node2 and node3
        assert balancer.node_loads["node2"] + balancer.node_loads["node3"] == 5
    
    def test_process_pending_tasks(self):
        """Test processing of pending tasks"""
        monitor = NodeHealthMonitor()
        balancer = LoadBalancer(monitor)
        
        # Add pending tasks when no nodes available
        for i in range(3):
            task = {'type': 'validation', 'index': i}
            balancer.assign_task(task)
        
        assert balancer.get_pending_task_count() == 3
        
        # Register a node
        monitor.register_node("node1")
        
        # Process pending tasks
        processed = balancer.process_pending_tasks()
        
        assert processed == 3
        assert balancer.get_pending_task_count() == 0
        assert balancer.node_loads["node1"] == 3


class TestAutoRecoveryManager:
    """Tests for AutoRecoveryManager"""
    
    @pytest.mark.asyncio
    async def test_register_recovery_callback(self):
        """Test registering recovery callbacks"""
        monitor = NodeHealthMonitor()
        balancer = LoadBalancer(monitor)
        manager = AutoRecoveryManager(monitor, balancer)
        
        callback = AsyncMock()
        assert manager.register_recovery_callback("restart_node", callback)
        assert "restart_node" in manager.recovery_callbacks
    
    @pytest.mark.asyncio
    async def test_attempt_node_recovery_success(self):
        """Test successful node recovery"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.node_metrics["node1"].status = NodeStatus.UNRESPONSIVE
        
        balancer = LoadBalancer(monitor)
        manager = AutoRecoveryManager(monitor, balancer, recovery_cooldown=0.1)
        
        # Register callbacks
        manager.register_recovery_callback("verify_integrity", AsyncMock(return_value=True))
        manager.register_recovery_callback("restart_node", AsyncMock(return_value=True))
        manager.register_recovery_callback("verify_responsive", AsyncMock(return_value=True))
        
        # Attempt recovery
        result = await manager.attempt_node_recovery("node1")
        
        assert result.success
        assert monitor.node_metrics["node1"].status == NodeStatus.ACTIVE
        assert monitor.node_metrics["node1"].recovery_attempts == 1
    
    @pytest.mark.asyncio
    async def test_attempt_node_recovery_failure(self):
        """Test failed node recovery"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.node_metrics["node1"].status = NodeStatus.UNRESPONSIVE
        
        balancer = LoadBalancer(monitor)
        manager = AutoRecoveryManager(monitor, balancer, recovery_cooldown=0.1)
        
        # Register callbacks that fail
        manager.register_recovery_callback("verify_integrity", AsyncMock(return_value=False))
        
        # Attempt recovery
        result = await manager.attempt_node_recovery("node1")
        
        assert not result.success
        assert "integrity verification failed" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_max_recovery_attempts(self):
        """Test max recovery attempts limit"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.node_metrics["node1"].status = NodeStatus.UNRESPONSIVE
        
        balancer = LoadBalancer(monitor)
        manager = AutoRecoveryManager(monitor, balancer, max_recovery_attempts=2, recovery_cooldown=0.1)
        
        # Register failing callbacks
        manager.register_recovery_callback("verify_integrity", AsyncMock(return_value=False))
        
        # Attempt recovery multiple times
        result1 = await manager.attempt_node_recovery("node1")
        assert not result1.success
        
        await asyncio.sleep(0.2)  # Wait for cooldown
        
        result2 = await manager.attempt_node_recovery("node1")
        assert not result2.success
        
        await asyncio.sleep(0.2)  # Wait for cooldown
        
        # Third attempt should fail due to max attempts
        result3 = await manager.attempt_node_recovery("node1")
        assert not result3.success
        assert "max recovery attempts" in result3.error_message.lower()
        assert monitor.node_metrics["node1"].status == NodeStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_recovery_cooldown(self):
        """Test recovery cooldown period"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.node_metrics["node1"].status = NodeStatus.UNRESPONSIVE
        
        balancer = LoadBalancer(monitor)
        manager = AutoRecoveryManager(monitor, balancer, recovery_cooldown=1.0)
        
        # Register callbacks
        manager.register_recovery_callback("verify_integrity", AsyncMock(return_value=False))
        
        # First attempt
        result1 = await manager.attempt_node_recovery("node1")
        assert not result1.success
        
        # Immediate second attempt should be blocked by cooldown
        result2 = await manager.attempt_node_recovery("node1")
        assert not result2.success
        assert "cooldown" in result2.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_get_recovery_stats(self):
        """Test recovery statistics"""
        monitor = NodeHealthMonitor()
        monitor.register_node("node1")
        monitor.register_node("node2")
        
        balancer = LoadBalancer(monitor)
        manager = AutoRecoveryManager(monitor, balancer, recovery_cooldown=0.1)
        
        # Register callbacks
        manager.register_recovery_callback("verify_integrity", AsyncMock(return_value=True))
        manager.register_recovery_callback("restart_node", AsyncMock(return_value=True))
        manager.register_recovery_callback("verify_responsive", AsyncMock(return_value=True))
        
        # Perform some recoveries
        await manager.attempt_node_recovery("node1")
        
        await asyncio.sleep(0.2)
        
        # Fail one
        manager.register_recovery_callback("verify_integrity", AsyncMock(return_value=False))
        await manager.attempt_node_recovery("node2")
        
        stats = manager.get_recovery_stats()
        
        assert stats['total_attempts'] == 2
        assert stats['successful_recoveries'] == 1
        assert stats['failed_recoveries'] == 1
        assert stats['success_rate'] == 50.0


class TestFaultToleranceSystem:
    """Tests for FaultToleranceSystem"""
    
    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test fault tolerance system initialization"""
        system = FaultToleranceSystem()
        
        assert system.health_monitor is not None
        assert system.load_balancer is not None
        assert system.recovery_manager is not None
        assert not system.running
    
    @pytest.mark.asyncio
    async def test_register_unregister_node(self):
        """Test node registration and unregistration"""
        system = FaultToleranceSystem()
        
        assert system.register_node("node1")
        assert "node1" in system.health_monitor.node_metrics
        
        assert system.unregister_node("node1")
        assert "node1" not in system.health_monitor.node_metrics
    
    @pytest.mark.asyncio
    async def test_get_system_status(self):
        """Test getting system status"""
        system = FaultToleranceSystem()
        
        system.register_node("node1")
        system.register_node("node2")
        system.register_node("node3")
        
        # Mark one as unresponsive
        system.health_monitor.node_metrics["node2"].status = NodeStatus.UNRESPONSIVE
        
        status = system.get_system_status()
        
        assert status['active_nodes'] == 2
        assert status['unresponsive_nodes'] == 1
        assert status['total_nodes'] == 3
        assert status['system_healthy']
    
    @pytest.mark.asyncio
    async def test_system_start_stop(self):
        """Test starting and stopping the system"""
        system = FaultToleranceSystem()
        
        await system.start()
        assert system.running
        
        await system.stop()
        assert not system.running


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
