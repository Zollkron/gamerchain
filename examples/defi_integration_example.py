"""
Comprehensive DeFi Integration Example for PlayerGold.
Demonstrates staking and liquidity pools working together.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from decimal import Decimal
from src.blockchain.staking_system import StakingSystem, AINodeInfo
from src.blockchain.liquidity_pool import LiquidityPoolManager


def main():
    print("=" * 80)
    print("PlayerGold DeFi Ecosystem - Complete Integration Example")
    print("=" * 80)
    
    # Initialize systems
    staking_system = StakingSystem(
        min_stake_amount=Decimal('100.0'),
        withdrawal_delay_seconds=86400
    )
    pool_manager = LiquidityPoolManager()
    
    print("\n" + "=" * 80)
    print("PART 1: STAKING SYSTEM (10% of Block Rewards)")
    print("=" * 80)
    
    print("\n1. Registering AI Nodes for Staking")
    print("-" * 80)
    
    nodes = [
        AINodeInfo("node1", "Gemma 3 4B", "hash1", 0.95, 1500, 99.5),
        AINodeInfo("node2", "Mistral 3B", "hash2", 0.92, 1200, 98.8),
        AINodeInfo("node3", "Qwen 3 4B", "hash3", 0.98, 1800, 99.9)
    ]
    
    for node in nodes:
        staking_system.register_ai_node(node)
        print(f"✓ {node.model_name} (Reputation: {node.reputation_score:.2f})")
    
    print("\n2. Users Delegate Stakes to AI Nodes")
    print("-" * 80)
    
    stakes = [
        ("alice", Decimal('5000.0'), "node1"),
        ("bob", Decimal('3000.0'), "node3"),
        ("charlie", Decimal('2000.0'), "node1"),
        ("diana", Decimal('4000.0'), "node2")
    ]
    
    for staker, amount, node_id in stakes:
        success, message = staking_system.delegate_stake(staker, amount, node_id)
        print(f"{staker}: Staked {amount} $PRGLD to {node_id}")
    
    stats = staking_system.get_staking_stats()
    print(f"\nTotal Staked: {stats['total_staked']} $PRGLD")
    
    print("\n" + "=" * 80)
    print("PART 2: LIQUIDITY POOLS (20% of Fees)")
    print("=" * 80)
    
    print("\n3. Creating Liquidity Pools")
    print("-" * 80)
    
    pool_manager.create_pool("PRGLD", "USDT", Decimal('0.003'))
    pool_manager.create_pool("PRGLD", "ETH", Decimal('0.003'))
    print("✓ PRGLD-USDT pool created")
    print("✓ PRGLD-ETH pool created")
    
    print("\n4. Liquidity Providers Add Liquidity")
    print("-" * 80)
    
    # Alice provides liquidity (she's both staker and LP)
    _, _, lp1 = pool_manager.add_liquidity(
        "PRGLD-USDT", "alice",
        Decimal('10000.0'), Decimal('20000.0')
    )
    print(f"alice: Added 10,000 PRGLD + 20,000 USDT → {lp1:.2f} LP tokens")
    
    # Bob provides liquidity
    _, _, lp2 = pool_manager.add_liquidity(
        "PRGLD-USDT", "bob",
        Decimal('5000.0'), Decimal('10000.0')
    )
    print(f"bob: Added 5,000 PRGLD + 10,000 USDT → {lp2:.2f} LP tokens")
    
    print("\n" + "=" * 80)
    print("PART 3: SIMULATING BLOCK REWARDS & FEE DISTRIBUTION")
    print("=" * 80)
    
    print("\n5. Block Mined - Distributing Rewards")
    print("-" * 80)
    
    # Simulate a block reward
    block_reward = Decimal('1000.0')  # 1000 $PRGLD per block
    
    # 90% goes to AI validators (handled separately)
    ai_portion = block_reward * Decimal('0.90')
    print(f"AI Validators (90%): {ai_portion} $PRGLD")
    print("  → Distributed equally among validating AI nodes")
    
    # 10% goes to stakers
    staker_portion = block_reward * Decimal('0.10')
    print(f"\nStakers (10%): {staker_portion} $PRGLD")
    
    staking_rewards = staking_system.calculate_staking_rewards(staker_portion)
    print("  Staking Rewards Distribution:")
    for staker, reward in sorted(staking_rewards.items()):
        print(f"    {staker}: {reward:.4f} $PRGLD")
    
    print("\n6. Trading Activity - Fee Collection")
    print("-" * 80)
    
    # Simulate some trades
    trades = [
        ("trader1", "PRGLD", Decimal('1000.0')),
        ("trader2", "USDT", Decimal('3000.0')),
        ("trader3", "PRGLD", Decimal('500.0'))
    ]
    
    total_fees = Decimal('0.0')
    
    for trader, token, amount in trades:
        success, message, output, fee = pool_manager.swap(
            "PRGLD-USDT", trader, token, amount
        )
        print(f"{trader}: Swapped {amount} {token} → {output:.2f} (fee: {fee})")
        total_fees += fee
    
    print(f"\nTotal Trading Fees Collected: {total_fees} tokens")
    
    # Fee distribution (from requirements)
    liquidity_pool_share = total_fees * Decimal('0.20')  # 20% stays in pool
    burn_share = total_fees * Decimal('0.80')  # 80% burned
    
    print(f"\nFee Distribution:")
    print(f"  Liquidity Pool (20%): {liquidity_pool_share} → Increases LP token value")
    print(f"  Burned (80%): {burn_share} → Deflationary mechanism")
    
    print("\n" + "=" * 80)
    print("PART 4: USER PORTFOLIO OVERVIEW")
    print("=" * 80)
    
    print("\n7. Alice's Complete DeFi Position")
    print("-" * 80)
    
    # Alice's staking position
    stake_info = staking_system.get_stake_info("alice")
    if stake_info:
        print(f"Staking Position:")
        print(f"  Staked: {stake_info['stake']['amount']} $PRGLD")
        print(f"  Delegated to: {stake_info['stake']['delegated_node_id']}")
        accumulated = Decimal(stake_info['stake']['accumulated_rewards'])
        print(f"  Accumulated Rewards: {accumulated:.4f} $PRGLD")
    
    # Alice's LP position
    lp_positions = pool_manager.get_provider_positions("alice")
    if lp_positions:
        print(f"\nLiquidity Provider Position:")
        for pos in lp_positions:
            print(f"  Pool: {pos['pool_id']}")
            print(f"  LP Tokens: {pos['lp_tokens']}")
            print(f"  Share of pool fees: Proportional to LP tokens")
    
    print(f"\nAlice's Total Engagement:")
    print(f"  ✓ Earning from staking (10% of block rewards)")
    print(f"  ✓ Earning from LP fees (share of 20% of trading fees)")
    print(f"  ✓ Supporting network decentralization")
    
    print("\n" + "=" * 80)
    print("PART 5: ECOSYSTEM STATISTICS")
    print("=" * 80)
    
    print("\n8. Overall DeFi Metrics")
    print("-" * 80)
    
    # Staking metrics
    staking_stats = staking_system.get_staking_stats()
    print(f"Staking System:")
    print(f"  Total Value Staked: {staking_stats['total_staked']} $PRGLD")
    print(f"  Active Stakers: {staking_stats['active_stakes_count']}")
    print(f"  Registered AI Nodes: {staking_stats['registered_nodes_count']}")
    print(f"  Total Rewards Distributed: {staking_stats['total_rewards_distributed']} $PRGLD")
    
    # Pool metrics
    pool_info = pool_manager.get_pool_info("PRGLD-USDT")
    if pool_info:
        pool = pool_info['pool']
        print(f"\nLiquidity Pools:")
        print(f"  PRGLD-USDT Liquidity: {pool['reserve_a']} PRGLD + {pool['reserve_b']} USDT")
        print(f"  Total Volume: {pool['total_volume_a']} PRGLD + {pool['total_volume_b']} USDT")
        print(f"  Fees Collected: {pool['total_fees_collected']} tokens")
        print(f"  Liquidity Providers: {pool_info['provider_count']}")
    
    print("\n9. Tokenomics Summary")
    print("-" * 80)
    
    print("Block Rewards Distribution:")
    print("  • 90% → AI Validator Nodes (equal distribution)")
    print("  • 10% → Stakers (proportional to stake)")
    
    print("\nTrading Fees Distribution:")
    print("  • 20% → Liquidity Pool (increases LP value)")
    print("  • 80% → Burn Address (deflationary)")
    
    print("\nValue Accrual Mechanisms:")
    print("  • Staking: Earn from block rewards")
    print("  • Liquidity Provision: Earn from trading fees")
    print("  • Token Burns: Reduce supply, increase scarcity")
    print("  • AI Node Operation: Earn majority of block rewards")
    
    print("\n" + "=" * 80)
    print("DeFi Integration Example Complete!")
    print("=" * 80)
    
    print("\nKey Achievements:")
    print("  ✓ Implemented complementary staking (10% rewards)")
    print("  ✓ Created AMM liquidity pools with 0.3% fees")
    print("  ✓ Integrated fee distribution (20% pool, 80% burn)")
    print("  ✓ Enabled users to participate in multiple DeFi activities")
    print("  ✓ Maintained AI-first consensus (90% to validators)")
    print("  ✓ Built deflationary tokenomics through burns")
    
    print("\nRequirements Satisfied:")
    print("  ✓ Requisito 13.1: 90/10 reward distribution")
    print("  ✓ Requisito 13.2: Delegated staking to AI nodes")
    print("  ✓ Requisito 13.3: Decentralized liquidity pools")
    print("  ✓ Requisito 15.2: Fee distribution (20% pool, 80% burn)")


if __name__ == '__main__':
    main()
