"""
Example usage of the Liquidity Pool System with AMM for PlayerGold.
Demonstrates pool creation, liquidity provision, and token swapping.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from decimal import Decimal
from src.blockchain.liquidity_pool import LiquidityPoolManager


def main():
    print("=" * 80)
    print("PlayerGold Liquidity Pool & AMM Example")
    print("=" * 80)
    
    # Initialize pool manager
    manager = LiquidityPoolManager()
    
    print("\n1. Creating Liquidity Pools")
    print("-" * 80)
    
    # Create PRGLD-USDT pool
    success, message, pool_id = manager.create_pool(
        token_a_symbol="PRGLD",
        token_b_symbol="USDT",
        fee_percentage=Decimal('0.003')  # 0.3% fee
    )
    print(f"✓ {message}")
    
    # Create PRGLD-ETH pool
    success, message, pool_id = manager.create_pool(
        token_a_symbol="PRGLD",
        token_b_symbol="ETH",
        fee_percentage=Decimal('0.003')
    )
    print(f"✓ {message}")
    
    print("\n2. Adding Initial Liquidity (First Provider)")
    print("-" * 80)
    
    # Provider 1 adds liquidity to PRGLD-USDT pool
    success, message, lp_tokens = manager.add_liquidity(
        pool_id="PRGLD-USDT",
        provider_address="provider1",
        amount_a=Decimal('10000.0'),  # 10,000 PRGLD
        amount_b=Decimal('20000.0')   # 20,000 USDT (1 PRGLD = 2 USDT)
    )
    print(f"Provider1 -> PRGLD-USDT Pool:")
    print(f"  Deposited: 10,000 PRGLD + 20,000 USDT")
    print(f"  Received: {lp_tokens} LP tokens")
    
    # Check pool info
    info = manager.get_pool_info("PRGLD-USDT")
    print(f"  Pool Price: 1 PRGLD = {info['price_a_to_b']} USDT")
    
    print("\n3. Adding More Liquidity (Subsequent Providers)")
    print("-" * 80)
    
    # Provider 2 adds liquidity (same ratio)
    success, message, lp_tokens2 = manager.add_liquidity(
        pool_id="PRGLD-USDT",
        provider_address="provider2",
        amount_a=Decimal('5000.0'),   # 5,000 PRGLD
        amount_b=Decimal('10000.0')   # 10,000 USDT
    )
    print(f"Provider2 -> PRGLD-USDT Pool:")
    print(f"  Deposited: 5,000 PRGLD + 10,000 USDT")
    print(f"  Received: {lp_tokens2} LP tokens")
    
    # Provider 3 adds liquidity
    success, message, lp_tokens3 = manager.add_liquidity(
        pool_id="PRGLD-USDT",
        provider_address="provider3",
        amount_a=Decimal('2500.0'),   # 2,500 PRGLD
        amount_b=Decimal('5000.0')    # 5,000 USDT
    )
    print(f"Provider3 -> PRGLD-USDT Pool:")
    print(f"  Deposited: 2,500 PRGLD + 5,000 USDT")
    print(f"  Received: {lp_tokens3} LP tokens")
    
    print("\n4. Pool Statistics")
    print("-" * 80)
    
    info = manager.get_pool_info("PRGLD-USDT")
    pool_data = info['pool']
    print(f"PRGLD-USDT Pool:")
    print(f"  Total Liquidity: {pool_data['reserve_a']} PRGLD + {pool_data['reserve_b']} USDT")
    print(f"  Total LP Tokens: {pool_data['total_lp_tokens']}")
    print(f"  Current Price: 1 PRGLD = {info['price_a_to_b']} USDT")
    print(f"  Liquidity Providers: {info['provider_count']}")
    print(f"  Trading Fee: {float(Decimal(pool_data['fee_percentage']) * 100)}%")
    
    print("\n5. Getting Swap Quotes")
    print("-" * 80)
    
    # Quote for swapping 1000 PRGLD for USDT
    quote = manager.calculate_swap_quote(
        pool_id="PRGLD-USDT",
        input_token="PRGLD",
        input_amount=Decimal('1000.0')
    )
    
    print(f"Quote: Swap 1,000 PRGLD for USDT")
    print(f"  You will receive: {quote['output_amount']} USDT")
    print(f"  Trading fee: {quote['fee_amount']} PRGLD")
    print(f"  Effective price: {quote['price']} USDT per PRGLD")
    print(f"  Price impact: {quote['price_impact_percentage']}%")
    
    # Quote for reverse swap
    quote2 = manager.calculate_swap_quote(
        pool_id="PRGLD-USDT",
        input_token="USDT",
        input_amount=Decimal('2000.0')
    )
    
    print(f"\nQuote: Swap 2,000 USDT for PRGLD")
    print(f"  You will receive: {quote2['output_amount']} PRGLD")
    print(f"  Trading fee: {quote2['fee_amount']} USDT")
    print(f"  Effective price: {quote2['price']} PRGLD per USDT")
    print(f"  Price impact: {quote2['price_impact_percentage']}%")
    
    print("\n6. Executing Swaps")
    print("-" * 80)
    
    # Trader 1 swaps PRGLD for USDT
    success, message, output, fee = manager.swap(
        pool_id="PRGLD-USDT",
        trader_address="trader1",
        input_token="PRGLD",
        input_amount=Decimal('1000.0')
    )
    print(f"Trader1: {message}")
    print(f"  Fee paid: {fee} PRGLD")
    
    # Check updated price
    info = manager.get_pool_info("PRGLD-USDT")
    print(f"  New price: 1 PRGLD = {info['price_a_to_b']} USDT (price moved due to swap)")
    
    # Trader 2 swaps USDT for PRGLD
    success, message, output, fee = manager.swap(
        pool_id="PRGLD-USDT",
        trader_address="trader2",
        input_token="USDT",
        input_amount=Decimal('5000.0')
    )
    print(f"\nTrader2: {message}")
    print(f"  Fee paid: {fee} USDT")
    
    # Check updated price again
    info = manager.get_pool_info("PRGLD-USDT")
    print(f"  New price: 1 PRGLD = {info['price_a_to_b']} USDT")
    
    print("\n7. Viewing Provider Positions")
    print("-" * 80)
    
    for provider in ["provider1", "provider2", "provider3"]:
        positions = manager.get_provider_positions(provider)
        if positions:
            print(f"\n{provider}:")
            for pos in positions:
                print(f"  Pool: {pos['pool_id']}")
                print(f"  LP Tokens: {pos['lp_tokens']}")
                print(f"  Deposited: {pos['token_a_deposited']} PRGLD + {pos['token_b_deposited']} USDT")
    
    print("\n8. Removing Liquidity")
    print("-" * 80)
    
    # Provider 2 removes half their liquidity
    positions = manager.get_provider_positions("provider2")
    lp_to_remove = Decimal(positions[0]['lp_tokens']) / 2
    
    success, message, amount_a, amount_b = manager.remove_liquidity(
        pool_id="PRGLD-USDT",
        provider_address="provider2",
        lp_tokens=lp_to_remove
    )
    
    print(f"Provider2 removes 50% of liquidity:")
    print(f"  Burned: {lp_to_remove} LP tokens")
    print(f"  Received: {amount_a} PRGLD + {amount_b} USDT")
    
    # Check updated pool
    info = manager.get_pool_info("PRGLD-USDT")
    pool_data = info['pool']
    print(f"\nUpdated Pool Liquidity:")
    print(f"  {pool_data['reserve_a']} PRGLD + {pool_data['reserve_b']} USDT")
    
    print("\n9. Pool Trading Statistics")
    print("-" * 80)
    
    info = manager.get_pool_info("PRGLD-USDT")
    pool_data = info['pool']
    
    print(f"PRGLD-USDT Pool Stats:")
    print(f"  Total Volume (PRGLD): {pool_data['total_volume_a']}")
    print(f"  Total Volume (USDT): {pool_data['total_volume_b']}")
    print(f"  Total Fees Collected: {pool_data['total_fees_collected']}")
    print(f"  Constant Product (k): {info['constant_product']}")
    
    print("\n10. Comparing Large vs Small Swaps (Price Impact)")
    print("-" * 80)
    
    # Small swap
    small_quote = manager.calculate_swap_quote(
        "PRGLD-USDT", "PRGLD", Decimal('100.0')
    )
    
    # Large swap
    large_quote = manager.calculate_swap_quote(
        "PRGLD-USDT", "PRGLD", Decimal('5000.0')
    )
    
    print(f"Small Swap (100 PRGLD):")
    print(f"  Output: {small_quote['output_amount']} USDT")
    print(f"  Price Impact: {small_quote['price_impact_percentage']}%")
    
    print(f"\nLarge Swap (5,000 PRGLD):")
    print(f"  Output: {large_quote['output_amount']} USDT")
    print(f"  Price Impact: {large_quote['price_impact_percentage']}%")
    print(f"  Note: Larger swaps have higher price impact due to slippage")
    
    print("\n11. All Pools Overview")
    print("-" * 80)
    
    all_pools = manager.get_all_pools()
    print(f"Total Pools: {len(all_pools)}")
    for pool_info in all_pools:
        if pool_info:
            pool = pool_info['pool']
            print(f"\n{pool['pool_id']}:")
            print(f"  Reserves: {pool['reserve_a']} {pool['token_a_symbol']} + {pool['reserve_b']} {pool['token_b_symbol']}")
            print(f"  Status: {pool['status']}")
    
    print("\n" + "=" * 80)
    print("Liquidity Pool & AMM Example Complete!")
    print("=" * 80)
    
    print("\nKey Features Demonstrated:")
    print("  ✓ Automated Market Maker (AMM) with constant product formula")
    print("  ✓ Multiple liquidity providers in same pool")
    print("  ✓ Proportional LP token distribution")
    print("  ✓ Token swapping with automatic pricing")
    print("  ✓ Trading fees (0.3%) distributed to liquidity providers")
    print("  ✓ Price impact calculation for different swap sizes")
    print("  ✓ Add and remove liquidity operations")
    print("  ✓ Real-time price updates based on supply/demand")


if __name__ == '__main__':
    main()
