"""
Tests for the Liquidity Pool System with AMM.
"""

import pytest
from decimal import Decimal

from src.blockchain.liquidity_pool import (
    LiquidityPoolManager, LiquidityPool, LiquidityPosition, PoolStatus
)


class TestLiquidityPool:
    """Tests for LiquidityPool class."""
    
    def test_pool_creation(self):
        """Test creating a liquidity pool."""
        pool = LiquidityPool(
            pool_id="PRGLD-USDT",
            token_a_symbol="PRGLD",
            token_b_symbol="USDT"
        )
        
        assert pool.pool_id == "PRGLD-USDT"
        assert pool.reserve_a == Decimal('0.0')
        assert pool.reserve_b == Decimal('0.0')
        assert pool.status == PoolStatus.ACTIVE
    
    def test_constant_product(self):
        """Test constant product calculation."""
        pool = LiquidityPool(
            pool_id="PRGLD-USDT",
            token_a_symbol="PRGLD",
            token_b_symbol="USDT",
            reserve_a=Decimal('1000.0'),
            reserve_b=Decimal('2000.0')
        )
        
        k = pool.get_constant_product()
        assert k == Decimal('2000000.0')
    
    def test_price_calculation(self):
        """Test price calculations."""
        pool = LiquidityPool(
            pool_id="PRGLD-USDT",
            token_a_symbol="PRGLD",
            token_b_symbol="USDT",
            reserve_a=Decimal('1000.0'),
            reserve_b=Decimal('2000.0')
        )
        
        price_a_to_b = pool.calculate_price_a_to_b()
        assert price_a_to_b == Decimal('2.0')  # 1 PRGLD = 2 USDT
        
        price_b_to_a = pool.calculate_price_b_to_a()
        assert price_b_to_a == Decimal('0.5')  # 1 USDT = 0.5 PRGLD
    
    def test_calculate_output_amount(self):
        """Test calculating swap output amount."""
        pool = LiquidityPool(
            pool_id="PRGLD-USDT",
            token_a_symbol="PRGLD",
            token_b_symbol="USDT",
            reserve_a=Decimal('1000.0'),
            reserve_b=Decimal('2000.0'),
            fee_percentage=Decimal('0.003')  # 0.3%
        )
        
        # Swap 100 PRGLD for USDT
        output, fee = pool.calculate_output_amount(Decimal('100.0'), input_is_token_a=True)
        
        assert fee == Decimal('0.3')  # 0.3% of 100
        assert output > Decimal('0.0')
        assert output < Decimal('200.0')  # Should be less than 2:1 ratio due to slippage
    
    def test_pool_serialization(self):
        """Test pool to/from dict conversion."""
        pool = LiquidityPool(
            pool_id="PRGLD-USDT",
            token_a_symbol="PRGLD",
            token_b_symbol="USDT",
            reserve_a=Decimal('1000.0'),
            reserve_b=Decimal('2000.0')
        )
        
        pool_dict = pool.to_dict()
        assert pool_dict['pool_id'] == "PRGLD-USDT"
        assert pool_dict['reserve_a'] == '1000.0'


class TestLiquidityPosition:
    """Tests for LiquidityPosition class."""
    
    def test_position_creation(self):
        """Test creating a liquidity position."""
        position = LiquidityPosition(
            provider_address="provider1",
            pool_id="PRGLD-USDT",
            lp_tokens=Decimal('100.0'),
            token_a_deposited=Decimal('1000.0'),
            token_b_deposited=Decimal('2000.0'),
            timestamp=1234567890.0
        )
        
        assert position.provider_address == "provider1"
        assert position.lp_tokens == Decimal('100.0')
        assert position.accumulated_fees == Decimal('0.0')
    
    def test_position_serialization(self):
        """Test position to/from dict conversion."""
        position = LiquidityPosition(
            provider_address="provider1",
            pool_id="PRGLD-USDT",
            lp_tokens=Decimal('100.0'),
            token_a_deposited=Decimal('1000.0'),
            token_b_deposited=Decimal('2000.0'),
            timestamp=1234567890.0
        )
        
        pos_dict = position.to_dict()
        restored = LiquidityPosition.from_dict(pos_dict)
        
        assert restored.provider_address == position.provider_address
        assert restored.lp_tokens == position.lp_tokens


class TestLiquidityPoolManager:
    """Tests for LiquidityPoolManager."""
    
    @pytest.fixture
    def manager(self):
        """Create a pool manager for testing."""
        return LiquidityPoolManager()
    
    def test_create_pool(self, manager):
        """Test creating a new pool."""
        success, message, pool_id = manager.create_pool("PRGLD", "USDT")
        
        assert success is True
        assert pool_id == "PRGLD-USDT"
        assert pool_id in manager.pools
    
    def test_create_pool_reversed_tokens(self, manager):
        """Test pool creation with reversed token order."""
        success1, _, pool_id1 = manager.create_pool("PRGLD", "USDT")
        success2, message2, pool_id2 = manager.create_pool("USDT", "PRGLD")
        
        # Should recognize it's the same pool regardless of order
        assert pool_id1 == "PRGLD-USDT"
        assert success2 is False  # Second attempt should fail
        assert "already exists" in message2
    
    def test_add_liquidity_first_provider(self, manager):
        """Test adding liquidity as first provider."""
        manager.create_pool("PRGLD", "USDT")
        
        success, message, lp_tokens = manager.add_liquidity(
            pool_id="PRGLD-USDT",
            provider_address="provider1",
            amount_a=Decimal('1000.0'),
            amount_b=Decimal('2000.0')
        )
        
        assert success is True
        assert lp_tokens > Decimal('0.0')
        
        pool = manager.pools["PRGLD-USDT"]
        assert pool.reserve_a == Decimal('1000.0')
        assert pool.reserve_b == Decimal('2000.0')
        assert pool.total_lp_tokens == lp_tokens
    
    def test_add_liquidity_subsequent_provider(self, manager):
        """Test adding liquidity as subsequent provider."""
        manager.create_pool("PRGLD", "USDT")
        
        # First provider
        manager.add_liquidity("PRGLD-USDT", "provider1", 
                            Decimal('1000.0'), Decimal('2000.0'))
        
        # Second provider (same ratio)
        success, message, lp_tokens = manager.add_liquidity(
            pool_id="PRGLD-USDT",
            provider_address="provider2",
            amount_a=Decimal('500.0'),
            amount_b=Decimal('1000.0')
        )
        
        assert success is True
        assert lp_tokens > Decimal('0.0')
        
        pool = manager.pools["PRGLD-USDT"]
        assert pool.reserve_a == Decimal('1500.0')
        assert pool.reserve_b == Decimal('3000.0')
    
    def test_remove_liquidity(self, manager):
        """Test removing liquidity."""
        manager.create_pool("PRGLD", "USDT")
        
        # Add liquidity
        _, _, lp_tokens = manager.add_liquidity(
            "PRGLD-USDT", "provider1",
            Decimal('1000.0'), Decimal('2000.0')
        )
        
        # Remove half
        success, message, amount_a, amount_b = manager.remove_liquidity(
            pool_id="PRGLD-USDT",
            provider_address="provider1",
            lp_tokens=lp_tokens / 2
        )
        
        assert success is True
        assert amount_a == Decimal('500.0')
        assert amount_b == Decimal('1000.0')
        
        pool = manager.pools["PRGLD-USDT"]
        assert pool.reserve_a == Decimal('500.0')
        assert pool.reserve_b == Decimal('1000.0')
    
    def test_swap_token_a_for_b(self, manager):
        """Test swapping token A for token B."""
        manager.create_pool("PRGLD", "USDT")
        
        # Add liquidity
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('1000.0'), Decimal('2000.0'))
        
        # Swap 100 PRGLD for USDT
        success, message, output, fee = manager.swap(
            pool_id="PRGLD-USDT",
            trader_address="trader1",
            input_token="PRGLD",
            input_amount=Decimal('100.0')
        )
        
        assert success is True
        assert output > Decimal('0.0')
        assert fee == Decimal('0.3')  # 0.3% of 100
        
        pool = manager.pools["PRGLD-USDT"]
        assert pool.reserve_a == Decimal('1100.0')  # Increased by input
        assert pool.reserve_b < Decimal('2000.0')  # Decreased by output
    
    def test_swap_token_b_for_a(self, manager):
        """Test swapping token B for token A."""
        manager.create_pool("PRGLD", "USDT")
        
        # Add liquidity
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('1000.0'), Decimal('2000.0'))
        
        # Swap 200 USDT for PRGLD
        success, message, output, fee = manager.swap(
            pool_id="PRGLD-USDT",
            trader_address="trader1",
            input_token="USDT",
            input_amount=Decimal('200.0')
        )
        
        assert success is True
        assert output > Decimal('0.0')
        assert fee == Decimal('0.6')  # 0.3% of 200
        
        pool = manager.pools["PRGLD-USDT"]
        assert pool.reserve_b == Decimal('2200.0')  # Increased by input
        assert pool.reserve_a < Decimal('1000.0')  # Decreased by output
    
    def test_constant_product_maintained(self, manager):
        """Test that constant product is maintained after swap."""
        manager.create_pool("PRGLD", "USDT")
        
        # Add liquidity
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('1000.0'), Decimal('2000.0'))
        
        pool = manager.pools["PRGLD-USDT"]
        k_before = pool.get_constant_product()
        
        # Perform swap
        manager.swap("PRGLD-USDT", "trader1", "PRGLD", Decimal('100.0'))
        
        k_after = pool.get_constant_product()
        
        # k should increase slightly due to fees
        assert k_after >= k_before
    
    def test_get_pool_info(self, manager):
        """Test getting pool information."""
        manager.create_pool("PRGLD", "USDT")
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('1000.0'), Decimal('2000.0'))
        
        info = manager.get_pool_info("PRGLD-USDT")
        
        assert info is not None
        assert info['pool']['pool_id'] == "PRGLD-USDT"
        assert Decimal(info['price_a_to_b']) == Decimal('2.0')
        assert info['provider_count'] == 1
    
    def test_get_provider_positions(self, manager):
        """Test getting provider positions."""
        manager.create_pool("PRGLD", "USDT")
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('1000.0'), Decimal('2000.0'))
        
        positions = manager.get_provider_positions("provider1")
        
        assert len(positions) == 1
        assert positions[0]['pool_id'] == "PRGLD-USDT"
    
    def test_calculate_swap_quote(self, manager):
        """Test getting a swap quote."""
        manager.create_pool("PRGLD", "USDT")
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('1000.0'), Decimal('2000.0'))
        
        quote = manager.calculate_swap_quote(
            pool_id="PRGLD-USDT",
            input_token="PRGLD",
            input_amount=Decimal('100.0')
        )
        
        assert quote is not None
        assert quote['input_token'] == "PRGLD"
        assert quote['output_token'] == "USDT"
        assert Decimal(quote['output_amount']) > Decimal('0.0')
        assert Decimal(quote['fee_amount']) == Decimal('0.3')
    
    def test_multiple_providers_same_pool(self, manager):
        """Test multiple providers in same pool."""
        manager.create_pool("PRGLD", "USDT")
        
        # Three providers
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('1000.0'), Decimal('2000.0'))
        manager.add_liquidity("PRGLD-USDT", "provider2",
                            Decimal('500.0'), Decimal('1000.0'))
        manager.add_liquidity("PRGLD-USDT", "provider3",
                            Decimal('250.0'), Decimal('500.0'))
        
        pool = manager.pools["PRGLD-USDT"]
        assert pool.reserve_a == Decimal('1750.0')
        assert pool.reserve_b == Decimal('3500.0')
        
        info = manager.get_pool_info("PRGLD-USDT")
        assert info['provider_count'] == 3
    
    def test_price_impact(self, manager):
        """Test price impact of large swaps."""
        manager.create_pool("PRGLD", "USDT")
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('1000.0'), Decimal('2000.0'))
        
        # Small swap
        quote_small = manager.calculate_swap_quote(
            "PRGLD-USDT", "PRGLD", Decimal('10.0')
        )
        
        # Large swap
        quote_large = manager.calculate_swap_quote(
            "PRGLD-USDT", "PRGLD", Decimal('500.0')
        )
        
        # Large swap should have higher price impact
        impact_small = Decimal(quote_small['price_impact_percentage'])
        impact_large = Decimal(quote_large['price_impact_percentage'])
        
        assert impact_large > impact_small
    
    def test_insufficient_liquidity(self, manager):
        """Test swap with insufficient liquidity."""
        manager.create_pool("PRGLD", "USDT")
        manager.add_liquidity("PRGLD-USDT", "provider1",
                            Decimal('100.0'), Decimal('200.0'))
        
        # Try to swap more than available
        success, message, output, fee = manager.swap(
            pool_id="PRGLD-USDT",
            trader_address="trader1",
            input_token="PRGLD",
            input_amount=Decimal('10000.0')
        )
        
        # Should succeed but with high slippage
        assert success is True
        assert output < Decimal('200.0')  # Can't get more than reserve
    
    def test_get_all_pools(self, manager):
        """Test getting all pools."""
        manager.create_pool("PRGLD", "USDT")
        manager.create_pool("PRGLD", "ETH")
        
        pools = manager.get_all_pools()
        assert len(pools) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
