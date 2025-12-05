"""
Example usage of the Staking System for PlayerGold.
Demonstrates delegation to AI nodes and reward calculation.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from decimal import Decimal
from src.blockchain.staking_system import StakingSystem, AINodeInfo


def main():
    print("=" * 80)
    print("PlayerGold Staking System Example")
    print("=" * 80)
    
    # Initialize staking system
    staking_system = StakingSystem(
        min_stake_amount=Decimal('100.0'),
        withdrawal_delay_seconds=86400  # 24 hours
    )
    
    print("\n1. Registering AI Nodes")
    print("-" * 80)
    
    # Register AI nodes
    nodes = [
        AINodeInfo(
            node_id="node1",
            model_name="Gemma 3 4B",
            model_hash="abc123def456",
            reputation_score=0.95,
            total_validations=1500,
            uptime_percentage=99.5
        ),
        AINodeInfo(
            node_id="node2",
            model_name="Mistral 3B",
            model_hash="789ghi012jkl",
            reputation_score=0.92,
            total_validations=1200,
            uptime_percentage=98.8
        ),
        AINodeInfo(
            node_id="node3",
            model_name="Qwen 3 4B",
            model_hash="345mno678pqr",
            reputation_score=0.98,
            total_validations=1800,
            uptime_percentage=99.9
        )
    ]
    
    for node in nodes:
        staking_system.register_ai_node(node)
        print(f"✓ Registered {node.model_name} (Node ID: {node.node_id})")
        print(f"  Reputation: {node.reputation_score:.2f}, Uptime: {node.uptime_percentage}%")
    
    print("\n2. Getting Available Nodes for Staking")
    print("-" * 80)
    
    available_nodes = staking_system.get_available_nodes(min_reputation=0.90)
    print(f"Found {len(available_nodes)} nodes with reputation >= 0.90:")
    for node in available_nodes:
        print(f"  • {node.model_name} (ID: {node.node_id}) - Reputation: {node.reputation_score:.2f}")
    
    print("\n3. Delegating Stakes to AI Nodes")
    print("-" * 80)
    
    # Staker 1 delegates to node1
    success, message = staking_system.delegate_stake(
        staker_address="staker1",
        amount=Decimal('1000.0'),
        delegated_node_id="node1"
    )
    print(f"Staker1 -> Node1: {message}")
    
    # Staker 2 delegates to node1 (same node)
    success, message = staking_system.delegate_stake(
        staker_address="staker2",
        amount=Decimal('500.0'),
        delegated_node_id="node1"
    )
    print(f"Staker2 -> Node1: {message}")
    
    # Staker 3 delegates to node3
    success, message = staking_system.delegate_stake(
        staker_address="staker3",
        amount=Decimal('2000.0'),
        delegated_node_id="node3"
    )
    print(f"Staker3 -> Node3: {message}")
    
    # Staker 4 delegates to node2
    success, message = staking_system.delegate_stake(
        staker_address="staker4",
        amount=Decimal('750.0'),
        delegated_node_id="node2"
    )
    print(f"Staker4 -> Node2: {message}")
    
    print("\n4. Viewing Staking Statistics")
    print("-" * 80)
    
    stats = staking_system.get_staking_stats()
    print(f"Total Staked: {stats['total_staked']} $PRGLD")
    print(f"Active Stakes: {stats['active_stakes_count']}")
    print(f"Registered Nodes: {stats['registered_nodes_count']}")
    print(f"Active Nodes: {stats['active_nodes_count']}")
    
    print("\n5. Node Delegation Details")
    print("-" * 80)
    
    for node_id in ["node1", "node2", "node3"]:
        info = staking_system.get_node_delegations_info(node_id)
        if info:
            print(f"\n{info['node_info']['model_name']} (Node {node_id}):")
            print(f"  Total Delegated: {info['total_delegated']} $PRGLD")
            print(f"  Delegator Count: {info['delegator_count']}")
            print(f"  Delegators:")
            for delegator in info['delegators']:
                print(f"    - {delegator['staker_address']}: {delegator['amount']} $PRGLD")
    
    print("\n6. Calculating Staking Rewards (10% of Block Reward)")
    print("-" * 80)
    
    # Simulate block reward: 1000 $PRGLD total
    # 90% goes to AI validators, 10% goes to stakers
    block_reward = Decimal('1000.0')
    staker_portion = block_reward * Decimal('0.10')  # 100 $PRGLD
    
    print(f"Block Reward: {block_reward} $PRGLD")
    print(f"Staker Portion (10%): {staker_portion} $PRGLD")
    print(f"\nDistributing rewards proportionally by stake amount...")
    
    rewards = staking_system.calculate_staking_rewards(staker_portion)
    
    print("\nRewards Distribution:")
    for staker_address, reward_amount in sorted(rewards.items()):
        stake_info = staking_system.get_stake_info(staker_address)
        stake_amount = Decimal(stake_info['stake']['amount'])
        percentage = (stake_amount / Decimal(stats['total_staked'])) * 100
        print(f"  {staker_address}: {reward_amount:.4f} $PRGLD ({percentage:.2f}% of total stake)")
    
    print("\n7. Viewing Individual Stake Information")
    print("-" * 80)
    
    stake_info = staking_system.get_stake_info("staker1")
    if stake_info:
        print(f"\nStaker1 Details:")
        print(f"  Staked Amount: {stake_info['stake']['amount']} $PRGLD")
        print(f"  Delegated to: {stake_info['stake']['delegated_node_id']}")
        print(f"  Accumulated Rewards: {stake_info['stake']['accumulated_rewards']} $PRGLD")
        print(f"  Stake Duration: {stake_info['stake_duration_seconds']:.2f} seconds")
        print(f"  Status: {stake_info['stake']['status']}")
        print(f"  Can Withdraw: {stake_info['can_withdraw']}")
    
    print("\n8. Requesting Unstake")
    print("-" * 80)
    
    success, message = staking_system.request_unstake("staker2")
    print(f"Staker2 unstake request: {message}")
    
    # Check updated status
    stake_info = staking_system.get_stake_info("staker2")
    print(f"Staker2 status: {stake_info['stake']['status']}")
    print(f"Can withdraw: {stake_info['can_withdraw']}")
    
    print("\n9. Creating Stake Transaction")
    print("-" * 80)
    
    tx = staking_system.create_stake_transaction(
        staker_address="staker5",
        amount=Decimal('1500.0'),
        delegated_node_id="node1",
        nonce=0
    )
    
    print(f"Stake Transaction Created:")
    print(f"  From: {tx.from_address}")
    print(f"  To: {tx.to_address}")
    print(f"  Amount: {tx.amount} $PRGLD")
    print(f"  Type: {tx.transaction_type.value}")
    print(f"  Hash: {tx.hash}")
    
    print("\n" + "=" * 80)
    print("Staking System Example Complete!")
    print("=" * 80)
    
    print("\nKey Features Demonstrated:")
    print("  ✓ AI node registration and discovery")
    print("  ✓ Delegated staking to trusted AI nodes")
    print("  ✓ Proportional reward calculation (10% of block rewards)")
    print("  ✓ Automatic reward accumulation")
    print("  ✓ Withdrawal delay mechanism")
    print("  ✓ Transaction creation for staking operations")


if __name__ == '__main__':
    main()
