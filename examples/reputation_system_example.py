#!/usr/bin/env python3
"""
Example demonstrating the PlayerGold reputation system.

This example shows how to use the reputation system for both
AI nodes and users in the GamerChain network.
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reputation import (
    ReputationInterface,
    NodeBehaviorType,
    PenaltySeverity
)


def demonstrate_user_reputation():
    """Demonstrate user reputation features."""
    print("=== User Reputation System Demo ===\n")
    
    # Initialize reputation interface
    reputation = ReputationInterface(data_dir="data/reputation_demo")
    
    user_id = "demo_user_123"
    
    # Show initial reputation
    print("1. Initial User Reputation:")
    display_data = reputation.get_user_reputation_display(user_id)
    print(f"   Reputation Score: {display_data['reputation_score']}")
    print(f"   Priority Level: {display_data['priority_level']} ({display_data['priority_name']})")
    print(f"   Priority Multiplier: {display_data['priority_multiplier']}x")
    print(f"   High Priority: {display_data['is_high_priority']}")
    print()
    
    # Demonstrate token burning for reputation
    print("2. Burning Tokens for Reputation:")
    burn_amounts = [Decimal('2.5'), Decimal('7.5'), Decimal('15.0'), Decimal('20.0')]
    
    for i, amount in enumerate(burn_amounts):
        print(f"   Burning {amount} tokens...")
        result = reputation.burn_tokens_for_reputation(user_id, amount)
        
        print(f"   → Reputation: {result['reputation_score']}")
        print(f"   → Priority: {result['priority_level']} ({result['priority_name']})")
        print(f"   → Multiplier: {result['priority_multiplier']}x")
        print(f"   → Progress to next: {result['progress_to_next']:.1%}")
        print(f"   → Fee discount: {(1 - reputation.get_transaction_fee_discount(user_id)) * 100:.0f}%")
        print()
    
    # Demonstrate transaction priority
    print("3. Transaction Priority Information:")
    priority_info = reputation.get_transaction_priority_info(user_id)
    print(f"   Priority Level: {priority_info['priority_level']} ({priority_info['priority_name']})")
    print(f"   Processing Time: {priority_info['estimated_processing_time']}")
    print(f"   Queue Position: {priority_info['queue_position_estimate']}")
    print()
    
    # Record some transactions
    print("4. Recording Transactions:")
    for i in range(5):
        reputation.record_user_transaction(user_id)
        print(f"   Transaction {i+1} recorded")
    
    final_data = reputation.get_user_reputation_display(user_id)
    print(f"   Total transactions: {final_data['transaction_count']}")
    print(f"   Burn ratio: {final_data['burn_ratio']:.4f} tokens per transaction")
    print()


def demonstrate_node_reputation():
    """Demonstrate AI node reputation features."""
    print("=== AI Node Reputation System Demo ===\n")
    
    # Initialize reputation interface
    reputation = ReputationInterface(data_dir="data/reputation_demo")
    
    node_ids = ["ai_node_gemma_001", "ai_node_mistral_002", "ai_node_qwen_003"]
    
    print("1. Registering AI Nodes:")
    for node_id in node_ids:
        reputation.node_engine.register_node(node_id)
        print(f"   Registered: {node_id}")
    print()
    
    print("2. Simulating Node Activity:")
    
    # Node 1: Good performance
    print("   Node 1 (Gemma) - Good Performance:")
    for i in range(10):
        reputation.node_engine.record_successful_validation(node_ids[0], block_height=100+i)
    print(f"   → 10 successful validations")
    
    # Node 2: Mixed performance
    print("   Node 2 (Mistral) - Mixed Performance:")
    for i in range(7):
        reputation.node_engine.record_successful_validation(node_ids[1], block_height=200+i)
    
    reputation.node_engine.apply_penalty(
        node_ids[1],
        NodeBehaviorType.CHALLENGE_TIMEOUT,
        PenaltySeverity.LIGHT,
        {"timeout_ms": 120}
    )
    reputation.node_engine.apply_penalty(
        node_ids[1],
        NodeBehaviorType.NETWORK_DELAY,
        PenaltySeverity.LIGHT,
        {"delay_ms": 200}
    )
    print(f"   → 7 successful validations, 2 light penalties")
    
    # Node 3: Poor performance
    print("   Node 3 (Qwen) - Poor Performance:")
    for i in range(3):
        reputation.node_engine.record_successful_validation(node_ids[2], block_height=300+i)
    
    reputation.node_engine.apply_penalty(
        node_ids[2],
        NodeBehaviorType.HASH_MISMATCH,
        PenaltySeverity.SEVERE,
        {"expected_hash": "abc123", "actual_hash": "def456"}
    )
    reputation.node_engine.apply_penalty(
        node_ids[2],
        NodeBehaviorType.INVALID_SOLUTION,
        PenaltySeverity.MODERATE
    )
    print(f"   → 3 successful validations, 1 severe + 1 moderate penalty")
    print()
    
    print("3. Node Reputation Summary:")
    for node_id in node_ids:
        summary = reputation.get_node_reputation_summary(node_id)
        print(f"   {node_id}:")
        print(f"   → Reputation: {summary['reputation_score']}")
        print(f"   → Success Rate: {summary['success_rate']:.2%}")
        print(f"   → Validations: {summary['total_validations']}")
        print(f"   → Penalties: {summary['penalties_applied']}")
        print(f"   → Eligible: {summary['is_eligible']}")
        print()
    
    # Update participation rates
    print("4. Updating Participation Rates:")
    participation_rates = [0.95, 0.80, 0.05]  # Last one will trigger penalty
    
    for node_id, rate in zip(node_ids, participation_rates):
        reputation.node_engine.update_participation_rate(node_id, rate)
        print(f"   {node_id}: {rate:.0%} participation")
    print()


def demonstrate_network_overview():
    """Demonstrate network-wide reputation metrics."""
    print("=== Network Overview ===\n")
    
    reputation = ReputationInterface(data_dir="data/reputation_demo")
    
    # Get network health
    health = reputation.get_network_health()
    
    print("1. Network Health Metrics:")
    print(f"   Total AI Nodes: {health['nodes']['total_nodes']}")
    print(f"   Eligible Nodes: {health['nodes']['eligible_nodes']}")
    print(f"   Average Node Reputation: {health['nodes']['average_reputation']:.1f}")
    print(f"   Total Validations: {health['nodes']['total_validations']}")
    print(f"   Average Success Rate: {health['nodes']['average_success_rate']:.2%}")
    print()
    
    print(f"   Total Users: {health['users']['total_users']}")
    print(f"   High Priority Users: {health['users']['high_priority_users']}")
    print(f"   Average User Reputation: {health['users']['average_reputation']:.1f}")
    print(f"   Total Tokens Burned: {health['users']['total_burns']}")
    print(f"   Total Transactions: {health['users']['total_transactions']}")
    print()
    
    # Get top performers
    performers = reputation.get_top_performers(limit=3)
    
    print("2. Top Performing AI Nodes:")
    for i, node in enumerate(performers['top_nodes'], 1):
        print(f"   {i}. {node['node_id']}")
        print(f"      Reputation: {node['reputation_score']}")
        print(f"      Success Rate: {node['success_rate']:.2%}")
        print(f"      Validations: {node['total_validations']}")
    print()
    
    print("3. Top Users by Reputation:")
    for i, user in enumerate(performers['top_users'], 1):
        print(f"   {i}. {user['user_id']}")
        print(f"      Reputation: {user['reputation_score']}")
        print(f"      Tokens Burned: {user['tokens_burned']}")
        print(f"      Priority Level: {user['priority_level']}")
    print()


def demonstrate_transaction_processing():
    """Demonstrate transaction processing with reputation."""
    print("=== Transaction Processing Integration ===\n")
    
    reputation = ReputationInterface(data_dir="data/reputation_demo")
    
    # Test users with different reputation levels
    test_users = [
        ("low_rep_user", Decimal('0')),
        ("medium_rep_user", Decimal('10')),
        ("high_rep_user", Decimal('50'))
    ]
    
    print("1. Transaction Priority by Reputation:")
    for user_id, burn_amount in test_users:
        if burn_amount > 0:
            reputation.burn_tokens_for_reputation(user_id, burn_amount)
        
        should_prioritize = reputation.should_prioritize_transaction(user_id)
        fee_discount = reputation.get_transaction_fee_discount(user_id)
        priority_info = reputation.get_transaction_priority_info(user_id)
        
        print(f"   {user_id}:")
        print(f"   → Should Prioritize: {should_prioritize}")
        print(f"   → Fee Discount: {(1 - fee_discount) * 100:.0f}%")
        print(f"   → Processing Time: {priority_info['estimated_processing_time']}")
        print(f"   → Queue Position: {priority_info['queue_position_estimate']}")
        print()


def main():
    """Run all reputation system demonstrations."""
    print("PlayerGold Reputation System Demonstration")
    print("=" * 50)
    print()
    
    try:
        demonstrate_user_reputation()
        demonstrate_node_reputation()
        demonstrate_network_overview()
        demonstrate_transaction_processing()
        
        print("Demonstration completed successfully!")
        print("\nReputation data saved to: data/reputation_demo/")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()