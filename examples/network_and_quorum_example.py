"""
Example demonstrating Network Manager and Quorum Manager

This example shows how to use the network management and quorum systems
for testnet/mainnet switching and dynamic quorum calculation.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.network.network_manager import NetworkManager, NetworkType
from src.consensus.quorum_manager import QuorumManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_network_manager():
    """Example of using Network Manager"""
    logger.info("=== Network Manager Example ===\n")
    
    # Initialize network manager
    network_manager = NetworkManager()
    
    # Get current network info
    info = network_manager.get_network_info()
    logger.info(f"Current Network: {info['network_type']}")
    logger.info(f"Network ID: {info['network_id']}")
    logger.info(f"P2P Port: {info['p2p_port']}")
    logger.info(f"API Port: {info['api_port']}")
    logger.info(f"Bootstrap Nodes: {info['bootstrap_nodes']}")
    logger.info(f"Min Nodes: {info['min_nodes']}")
    logger.info(f"Quorum: {info['quorum_percentage']*100}%\n")
    
    # Check network type
    if network_manager.is_testnet():
        logger.info("✓ Running on TESTNET (safe for testing)")
        logger.info("  - Tokens have no real value")
        logger.info("  - Blockchain can be reset")
        logger.info("  - Perfect for development\n")
    
    # Get data directory
    data_dir = network_manager.get_data_directory()
    logger.info(f"Data Directory: {data_dir}\n")
    
    # Validate network compatibility
    peer_network_id = "playergold-testnet"
    is_compatible = network_manager.validate_network_compatibility(peer_network_id)
    logger.info(f"Peer compatibility check: {is_compatible}\n")
    
    # Switch to mainnet (demonstration only)
    logger.info("Switching to MAINNET...")
    network_manager.switch_network(NetworkType.MAINNET)
    
    mainnet_info = network_manager.get_network_info()
    logger.info(f"New Network: {mainnet_info['network_type']}")
    logger.info(f"Network ID: {mainnet_info['network_id']}")
    logger.info(f"P2P Port: {mainnet_info['p2p_port']}\n")
    
    if network_manager.is_mainnet():
        logger.warning("⚠️ Running on MAINNET")
        logger.warning("  - Tokens have REAL value")
        logger.warning("  - Transactions are PERMANENT")
        logger.warning("  - Use with caution!\n")


def example_quorum_manager():
    """Example of using Quorum Manager"""
    logger.info("\n=== Quorum Manager Example ===\n")
    
    # Initialize quorum manager
    quorum_manager = QuorumManager(quorum_percentage=0.66, min_nodes=2)
    
    logger.info(f"Quorum Configuration:")
    logger.info(f"  - Quorum Percentage: 66%")
    logger.info(f"  - Minimum Nodes: 2")
    logger.info(f"  - Principle: 'Donde hayan dos reunidos...'\n")
    
    # Example 1: 2 nodes (minimum)
    logger.info("Example 1: Network with 2 nodes")
    all_nodes_2 = {'node1', 'node2'}
    active_nodes_2 = {'node1', 'node2'}
    
    result = quorum_manager.check_quorum(active_nodes_2, all_nodes_2)
    logger.info(f"  Status: {result.status.value}")
    logger.info(f"  {result.message}")
    logger.info(f"  Can proceed: {result.can_proceed}\n")
    
    # Example 2: 3 nodes, 2 active
    logger.info("Example 2: Network with 3 nodes, 2 active")
    all_nodes_3 = {'node1', 'node2', 'node3'}
    active_nodes_3 = {'node1', 'node2'}
    
    result = quorum_manager.check_quorum(active_nodes_3, all_nodes_3)
    logger.info(f"  Status: {result.status.value}")
    logger.info(f"  {result.message}")
    logger.info(f"  Can proceed: {result.can_proceed}\n")
    
    # Example 3: 10 nodes, 7 active
    logger.info("Example 3: Network with 10 nodes, 7 active")
    all_nodes_10 = {f'node{i}' for i in range(10)}
    active_nodes_10 = {f'node{i}' for i in range(7)}
    
    result = quorum_manager.check_quorum(active_nodes_10, all_nodes_10)
    logger.info(f"  Status: {result.status.value}")
    logger.info(f"  {result.message}")
    logger.info(f"  Can proceed: {result.can_proceed}\n")
    
    # Example 4: 10 nodes, only 6 active (not enough)
    logger.info("Example 4: Network with 10 nodes, only 6 active")
    active_nodes_6 = {f'node{i}' for i in range(6)}
    
    result = quorum_manager.check_quorum(active_nodes_6, all_nodes_10)
    logger.info(f"  Status: {result.status.value}")
    logger.info(f"  {result.message}")
    logger.info(f"  Can proceed: {result.can_proceed}")
    
    missing = quorum_manager.get_missing_nodes_count(active_nodes_6, all_nodes_10)
    logger.info(f"  Missing nodes: {missing}\n")
    
    # Show quorum table
    logger.info("Quorum Requirements Table:")
    logger.info("  Nodes | Required | Percentage")
    logger.info("  ------|----------|------------")
    
    table = quorum_manager.get_quorum_table(max_nodes=10)
    for row in table:
        if row['can_operate']:
            logger.info(
                f"  {row['total_nodes']:5} | {row['required_nodes']:8} | "
                f"{row['actual_percentage']:6.1f}%"
            )
    
    logger.info("")


def example_consensus_validation():
    """Example of consensus validation with votes"""
    logger.info("\n=== Consensus Validation Example ===\n")
    
    quorum_manager = QuorumManager()
    
    # Scenario 1: Consensus achieved
    logger.info("Scenario 1: Block validation with 3 nodes")
    all_nodes = {'node1', 'node2', 'node3'}
    votes = {
        'node1': True,   # Validates block
        'node2': True,   # Validates block
        'node3': False   # Rejects block
    }
    
    consensus, message = quorum_manager.validate_consensus(votes, all_nodes)
    logger.info(f"  Votes: {votes}")
    logger.info(f"  Consensus: {consensus}")
    logger.info(f"  {message}\n")
    
    # Scenario 2: Consensus not achieved
    logger.info("Scenario 2: Block validation with split votes")
    votes_split = {
        'node1': True,
        'node2': False,
        'node3': False
    }
    
    consensus, message = quorum_manager.validate_consensus(votes_split, all_nodes)
    logger.info(f"  Votes: {votes_split}")
    logger.info(f"  Consensus: {consensus}")
    logger.info(f"  {message}\n")


def example_scaling():
    """Example showing how quorum scales with network size"""
    logger.info("\n=== Quorum Scaling Example ===\n")
    
    quorum_manager = QuorumManager()
    
    logger.info("How quorum scales with network growth:")
    logger.info("")
    
    test_sizes = [2, 3, 5, 10, 50, 100, 500, 1000]
    
    for size in test_sizes:
        info = quorum_manager.get_quorum_info(size)
        logger.info(
            f"  {size:4} nodes → {info['required_nodes']:4} required "
            f"({info['actual_percentage']:5.1f}%)"
        )
    
    logger.info("")
    logger.info("Key observations:")
    logger.info("  - With 2 nodes: 100% agreement required (both must agree)")
    logger.info("  - With 3+ nodes: ~66% required (2/3 majority)")
    logger.info("  - Scales linearly: 1000 nodes need 660 for quorum")
    logger.info("  - Network can't be compromised without controlling 66%+")
    logger.info("")


def main():
    """Run all examples"""
    try:
        # Network Manager examples
        example_network_manager()
        
        # Quorum Manager examples
        example_quorum_manager()
        
        # Consensus validation
        example_consensus_validation()
        
        # Scaling demonstration
        example_scaling()
        
        logger.info("=== All examples completed successfully ===")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    main()
