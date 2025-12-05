"""
Example demonstrating Fault Tolerance and Resilient Consensus System

This example shows how to use the fault tolerance and resilient consensus
systems to create a robust AI node network that can handle failures,
network partitions, and attacks.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.consensus.fault_tolerance import (
    FaultToleranceSystem,
    NodeStatus
)
from src.consensus.resilient_consensus import (
    ResilientConsensusSystem,
    NetworkState,
    AttackType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_fault_tolerance():
    """Example of using the fault tolerance system"""
    logger.info("=== Fault Tolerance System Example ===")
    
    # Initialize fault tolerance system
    ft_system = FaultToleranceSystem(
        heartbeat_timeout=60.0,
        challenge_timeout=120.0,
        max_recovery_attempts=3
    )
    
    # Start the system
    await ft_system.start()
    
    # Register some nodes
    logger.info("Registering nodes...")
    for i in range(5):
        ft_system.register_node(f"node{i}")
    
    # Simulate heartbeats
    logger.info("Simulating heartbeats...")
    for i in range(5):
        ft_system.health_monitor.update_heartbeat(f"node{i}")
        ft_system.health_monitor.update_challenge_response(f"node{i}", 50.0 + i * 5)
    
    # Get system status
    status = ft_system.get_system_status()
    logger.info(f"System Status: {status}")
    
    # Simulate a node failure
    logger.info("Simulating node2 failure...")
    ft_system.health_monitor.record_failure("node2")
    ft_system.health_monitor.record_failure("node2")
    ft_system.health_monitor.record_failure("node2")
    
    # Check node status
    node2_metrics = ft_system.health_monitor.get_node_metrics("node2")
    logger.info(f"Node2 status: {node2_metrics.status}")
    
    # Assign tasks to demonstrate load balancing
    logger.info("Assigning tasks...")
    for i in range(10):
        task = {'type': 'validation', 'index': i}
        assigned_node = ft_system.load_balancer.assign_task(task)
        if assigned_node:
            logger.info(f"Task {i} assigned to {assigned_node}")
    
    # Get load distribution
    load_dist = ft_system.load_balancer.get_load_distribution()
    logger.info(f"Load distribution: {load_dist}")
    
    # Register recovery callbacks
    async def mock_restart_node(node_id: str) -> bool:
        logger.info(f"Restarting node {node_id}...")
        await asyncio.sleep(0.1)
        return True
    
    async def mock_verify_responsive(node_id: str) -> bool:
        logger.info(f"Verifying node {node_id} is responsive...")
        await asyncio.sleep(0.1)
        return True
    
    async def mock_verify_integrity(node_id: str) -> bool:
        logger.info(f"Verifying integrity of node {node_id}...")
        await asyncio.sleep(0.1)
        return True
    
    ft_system.recovery_manager.register_recovery_callback('restart_node', mock_restart_node)
    ft_system.recovery_manager.register_recovery_callback('verify_responsive', mock_verify_responsive)
    ft_system.recovery_manager.register_recovery_callback('verify_integrity', mock_verify_integrity)
    
    # Attempt recovery
    logger.info("Attempting to recover node2...")
    recovery_result = await ft_system.recovery_manager.attempt_node_recovery("node2")
    logger.info(f"Recovery result: success={recovery_result.success}")
    
    # Get recovery stats
    recovery_stats = ft_system.recovery_manager.get_recovery_stats()
    logger.info(f"Recovery stats: {recovery_stats}")
    
    # Stop the system
    await ft_system.stop()
    logger.info("Fault tolerance system stopped")


async def example_resilient_consensus():
    """Example of using the resilient consensus system"""
    logger.info("\n=== Resilient Consensus System Example ===")
    
    # Initialize resilient consensus system
    rc_system = ResilientConsensusSystem(total_nodes=10)
    
    # Start the system
    await rc_system.start()
    
    # Simulate network partition
    logger.info("Simulating network partition...")
    all_nodes = {f"node{i}" for i in range(10)}
    reachable_nodes = {f"node{i}" for i in range(7)}  # 70% reachable
    
    can_continue = await rc_system.handle_partition(reachable_nodes, all_nodes)
    logger.info(f"Can continue consensus: {can_continue}")
    logger.info(f"Network state: {rc_system.network_state}")
    
    # Check partition status
    partition = rc_system.partition_detector.get_partition("node0")
    if partition:
        logger.info(f"Node0 is in partition {partition.partition_id}")
        logger.info(f"Partition size: {partition.partition_size}")
        logger.info(f"Is majority: {partition.is_majority}")
    
    # Simulate attack detection
    logger.info("\nSimulating attack detection...")
    
    # Detect flooding attack
    message_rates = {
        f"node{i}": 100 + i * 10 for i in range(10)
    }
    message_rates['node8'] = 10000  # Flooding node
    message_rates['node9'] = 15000  # Flooding node
    
    flooding_attack = rc_system.attack_defense.detect_flooding_attack(message_rates)
    if flooding_attack:
        logger.info(f"Flooding attack detected!")
        logger.info(f"Suspected nodes: {flooding_attack.suspected_nodes}")
        logger.info(f"Confidence: {flooding_attack.confidence}")
        
        # Mitigate attack
        logger.info("Mitigating attack...")
        
        async def mock_block_node(node_id: str):
            logger.info(f"Blocking node {node_id}")
        
        rc_system.attack_defense.register_defense_callback('block_node', mock_block_node)
        
        await rc_system.attack_defense.mitigate_attack(flooding_attack)
        logger.info(f"Attack mitigated: {flooding_attack.mitigated}")
    
    # Check blocked nodes
    blocked_nodes = rc_system.attack_defense.blocked_nodes
    logger.info(f"Blocked nodes: {blocked_nodes}")
    
    # Get defense stats
    defense_stats = rc_system.attack_defense.get_defense_stats()
    logger.info(f"Defense stats: {defense_stats}")
    
    # Simulate partition recovery
    logger.info("\nSimulating partition recovery...")
    
    # Register sync callbacks
    async def mock_get_blockchain_state(node_id: str):
        return {'block_height': 100, 'blocks': []}
    
    async def mock_get_local_state(node_id: str):
        return {'block_height': 95, 'blocks': []}
    
    async def mock_download_blocks(node_id: str, start: int, end: int):
        logger.info(f"Downloading blocks {start} to {end} for {node_id}")
        await asyncio.sleep(0.1)
        return True
    
    async def mock_validate_and_apply_blocks(node_id: str):
        logger.info(f"Validating and applying blocks for {node_id}")
        await asyncio.sleep(0.1)
        return True
    
    rc_system.auto_synchronizer.register_sync_callback('get_blockchain_state', mock_get_blockchain_state)
    rc_system.auto_synchronizer.register_sync_callback('get_local_state', mock_get_local_state)
    rc_system.auto_synchronizer.register_sync_callback('download_blocks', mock_download_blocks)
    rc_system.auto_synchronizer.register_sync_callback('validate_and_apply_blocks', mock_validate_and_apply_blocks)
    
    # Synchronize a node
    logger.info("Synchronizing node3...")
    sync_success = await rc_system.auto_synchronizer.synchronize_node("node3", ["node0"])
    logger.info(f"Synchronization success: {sync_success}")
    
    # Get sync progress
    sync_progress = rc_system.auto_synchronizer.get_sync_progress("node3")
    logger.info(f"Sync progress: {sync_progress * 100:.1f}%")
    
    # Get system state
    system_state = rc_system.get_system_state()
    logger.info(f"\nSystem state: {system_state}")
    
    # Stop the system
    await rc_system.stop()
    logger.info("Resilient consensus system stopped")


async def example_integrated_system():
    """Example of using both systems together"""
    logger.info("\n=== Integrated System Example ===")
    
    # Initialize both systems
    ft_system = FaultToleranceSystem()
    rc_system = ResilientConsensusSystem(total_nodes=10)
    
    # Start both systems
    await ft_system.start()
    await rc_system.start()
    
    # Register nodes in both systems
    logger.info("Registering nodes in both systems...")
    for i in range(10):
        node_id = f"node{i}"
        ft_system.register_node(node_id)
    
    # Simulate normal operation
    logger.info("Simulating normal operation...")
    for i in range(10):
        node_id = f"node{i}"
        ft_system.health_monitor.update_heartbeat(node_id)
        ft_system.health_monitor.update_challenge_response(node_id, 50.0 + i * 2)
    
    # Get combined status
    ft_status = ft_system.get_system_status()
    rc_status = rc_system.get_system_state()
    
    logger.info(f"Fault Tolerance Status: {ft_status}")
    logger.info(f"Resilient Consensus Status: {rc_status}")
    
    # Simulate a complex scenario: node failure + network partition
    logger.info("\nSimulating complex failure scenario...")
    
    # Node failures
    for i in [3, 7]:
        for _ in range(3):
            ft_system.health_monitor.record_failure(f"node{i}")
    
    # Network partition
    all_nodes = {f"node{i}" for i in range(10)}
    reachable_nodes = {f"node{i}" for i in range(6)}  # Nodes 0-5 reachable
    
    await rc_system.handle_partition(reachable_nodes, all_nodes)
    
    # Check if we can continue
    active_nodes = ft_system.health_monitor.get_active_nodes()
    can_continue = len(active_nodes) >= 3  # Need at least 3 nodes
    
    logger.info(f"Active nodes: {len(active_nodes)}")
    logger.info(f"Can continue operation: {can_continue}")
    
    # Stop both systems
    await ft_system.stop()
    await rc_system.stop()
    
    logger.info("Integrated system stopped")


async def main():
    """Run all examples"""
    try:
        # Run fault tolerance example
        await example_fault_tolerance()
        
        # Run resilient consensus example
        await example_resilient_consensus()
        
        # Run integrated example
        await example_integrated_system()
        
        logger.info("\n=== All examples completed successfully ===")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
