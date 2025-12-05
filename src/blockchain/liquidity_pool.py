"""
Liquidity Pool System with Automated Market Maker (AMM) for PlayerGold.
Implements constant product formula (x * y = k) for decentralized trading.
"""

import time
from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .transaction import Transaction, TransactionType

# Set high precision for calculations
getcontext().prec = 50


class PoolStatus(Enum):
    """Status of a liquidity pool."""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


@dataclass
class LiquidityPosition:
    """Represents a liquidity provider's position in a pool."""
    provider_address: str
    pool_id: str
    lp_tokens: Decimal  # Liquidity provider tokens
    token_a_deposited: Decimal
    token_b_deposited: Decimal
    timestamp: float
    accumulated_fees: Decimal = Decimal('0.0')
    
    def to_dict(self) -> dict:
        """Convert position to dictionary."""
        return {
            'provider_address': self.provider_address,
            'pool_id': self.pool_id,
            'lp_tokens': str(self.lp_tokens),
            'token_a_deposited': str(self.token_a_deposited),
            'token_b_deposited': str(self.token_b_deposited),
            'timestamp': self.timestamp,
            'accumulated_fees': str(self.accumulated_fees)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LiquidityPosition':
        """Create position from dictionary."""
        return cls(
            provider_address=data['provider_address'],
            pool_id=data['pool_id'],
            lp_tokens=Decimal(data['lp_tokens']),
            token_a_deposited=Decimal(data['token_a_deposited']),
            token_b_deposited=Decimal(data['token_b_deposited']),
            timestamp=data['timestamp'],
            accumulated_fees=Decimal(data['accumulated_fees'])
        )


@dataclass
class LiquidityPool:
    """
    Automated Market Maker liquidity pool using constant product formula.
    Implements x * y = k where x and y are token reserves.
    """
    pool_id: str
    token_a_symbol: str
    token_b_symbol: str
    reserve_a: Decimal = Decimal('0.0')
    reserve_b: Decimal = Decimal('0.0')
    total_lp_tokens: Decimal = Decimal('0.0')
    fee_percentage: Decimal = Decimal('0.003')  # 0.3% trading fee
    status: PoolStatus = PoolStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    total_volume_a: Decimal = Decimal('0.0')
    total_volume_b: Decimal = Decimal('0.0')
    total_fees_collected: Decimal = Decimal('0.0')
    
    def get_constant_product(self) -> Decimal:
        """
        Calculate the constant product k = x * y.
        
        Returns:
            Decimal: Constant product value
        """
        return self.reserve_a * self.reserve_b
    
    def calculate_price_a_to_b(self) -> Optional[Decimal]:
        """
        Calculate price of token A in terms of token B.
        
        Returns:
            Optional[Decimal]: Price or None if no liquidity
        """
        if self.reserve_a == 0:
            return None
        return self.reserve_b / self.reserve_a
    
    def calculate_price_b_to_a(self) -> Optional[Decimal]:
        """
        Calculate price of token B in terms of token A.
        
        Returns:
            Optional[Decimal]: Price or None if no liquidity
        """
        if self.reserve_b == 0:
            return None
        return self.reserve_a / self.reserve_b
    
    def calculate_output_amount(self, input_amount: Decimal, 
                               input_is_token_a: bool) -> Tuple[Decimal, Decimal]:
        """
        Calculate output amount for a swap using constant product formula.
        Formula: (x + Δx * (1 - fee)) * (y - Δy) = k
        
        Args:
            input_amount: Amount of input token
            input_is_token_a: True if input is token A, False if token B
            
        Returns:
            Tuple[Decimal, Decimal]: (output_amount, fee_amount)
        """
        if input_amount <= 0:
            return Decimal('0.0'), Decimal('0.0')
        
        # Calculate fee
        fee_amount = input_amount * self.fee_percentage
        input_after_fee = input_amount - fee_amount
        
        if input_is_token_a:
            # Swapping A for B
            if self.reserve_a == 0 or self.reserve_b == 0:
                return Decimal('0.0'), Decimal('0.0')
            
            # (reserve_a + input_after_fee) * (reserve_b - output) = k
            # output = reserve_b - k / (reserve_a + input_after_fee)
            k = self.get_constant_product()
            new_reserve_a = self.reserve_a + input_after_fee
            output_amount = self.reserve_b - (k / new_reserve_a)
        else:
            # Swapping B for A
            if self.reserve_a == 0 or self.reserve_b == 0:
                return Decimal('0.0'), Decimal('0.0')
            
            k = self.get_constant_product()
            new_reserve_b = self.reserve_b + input_after_fee
            output_amount = self.reserve_a - (k / new_reserve_b)
        
        # Ensure output is positive
        if output_amount < 0:
            output_amount = Decimal('0.0')
        
        return output_amount, fee_amount
    
    def calculate_input_amount(self, output_amount: Decimal,
                              output_is_token_a: bool) -> Tuple[Decimal, Decimal]:
        """
        Calculate required input amount for desired output.
        
        Args:
            output_amount: Desired output amount
            output_is_token_a: True if output is token A, False if token B
            
        Returns:
            Tuple[Decimal, Decimal]: (input_amount, fee_amount)
        """
        if output_amount <= 0:
            return Decimal('0.0'), Decimal('0.0')
        
        if output_is_token_a:
            # Want A, need to provide B
            if self.reserve_a <= output_amount or self.reserve_b == 0:
                return Decimal('0.0'), Decimal('0.0')
            
            k = self.get_constant_product()
            new_reserve_a = self.reserve_a - output_amount
            required_reserve_b = k / new_reserve_a
            input_before_fee = required_reserve_b - self.reserve_b
        else:
            # Want B, need to provide A
            if self.reserve_b <= output_amount or self.reserve_a == 0:
                return Decimal('0.0'), Decimal('0.0')
            
            k = self.get_constant_product()
            new_reserve_b = self.reserve_b - output_amount
            required_reserve_a = k / new_reserve_b
            input_before_fee = required_reserve_a - self.reserve_a
        
        # Account for fee: input_after_fee = input * (1 - fee)
        # So: input = input_after_fee / (1 - fee)
        input_amount = input_before_fee / (Decimal('1.0') - self.fee_percentage)
        fee_amount = input_amount * self.fee_percentage
        
        return input_amount, fee_amount
    
    def to_dict(self) -> dict:
        """Convert pool to dictionary."""
        return {
            'pool_id': self.pool_id,
            'token_a_symbol': self.token_a_symbol,
            'token_b_symbol': self.token_b_symbol,
            'reserve_a': str(self.reserve_a),
            'reserve_b': str(self.reserve_b),
            'total_lp_tokens': str(self.total_lp_tokens),
            'fee_percentage': str(self.fee_percentage),
            'status': self.status.value,
            'created_at': self.created_at,
            'total_volume_a': str(self.total_volume_a),
            'total_volume_b': str(self.total_volume_b),
            'total_fees_collected': str(self.total_fees_collected)
        }


class LiquidityPoolManager:
    """
    Manages liquidity pools and AMM operations.
    """
    
    def __init__(self):
        self.pools: Dict[str, LiquidityPool] = {}
        self.positions: Dict[str, List[LiquidityPosition]] = {}  # provider_address -> positions
        self.pool_positions: Dict[str, List[str]] = {}  # pool_id -> provider addresses
    
    def create_pool(self, token_a_symbol: str, token_b_symbol: str,
                   fee_percentage: Decimal = Decimal('0.003')) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new liquidity pool.
        
        Args:
            token_a_symbol: Symbol of token A
            token_b_symbol: Symbol of token B
            fee_percentage: Trading fee percentage (default 0.3%)
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, pool_id)
        """
        # Create pool ID from token symbols (sorted for consistency)
        tokens = sorted([token_a_symbol, token_b_symbol])
        pool_id = f"{tokens[0]}-{tokens[1]}"
        
        if pool_id in self.pools:
            return False, "Pool already exists", None
        
        # Ensure token_a is the first in sorted order
        if token_a_symbol > token_b_symbol:
            token_a_symbol, token_b_symbol = token_b_symbol, token_a_symbol
        
        pool = LiquidityPool(
            pool_id=pool_id,
            token_a_symbol=token_a_symbol,
            token_b_symbol=token_b_symbol,
            fee_percentage=fee_percentage
        )
        
        self.pools[pool_id] = pool
        self.pool_positions[pool_id] = []
        
        return True, f"Pool {pool_id} created successfully", pool_id
    
    def add_liquidity(self, pool_id: str, provider_address: str,
                     amount_a: Decimal, amount_b: Decimal) -> Tuple[bool, str, Decimal]:
        """
        Add liquidity to a pool.
        
        Args:
            pool_id: ID of the pool
            provider_address: Address of liquidity provider
            amount_a: Amount of token A to add
            amount_b: Amount of token B to add
            
        Returns:
            Tuple[bool, str, Decimal]: (success, message, lp_tokens_minted)
        """
        if pool_id not in self.pools:
            return False, "Pool not found", Decimal('0.0')
        
        pool = self.pools[pool_id]
        
        if pool.status != PoolStatus.ACTIVE:
            return False, f"Pool is {pool.status.value}", Decimal('0.0')
        
        if amount_a <= 0 or amount_b <= 0:
            return False, "Amounts must be positive", Decimal('0.0')
        
        # Calculate LP tokens to mint
        if pool.total_lp_tokens == 0:
            # First liquidity provider
            # LP tokens = sqrt(amount_a * amount_b)
            lp_tokens = (amount_a * amount_b).sqrt()
        else:
            # Subsequent providers
            # Maintain price ratio: amount_a / reserve_a = amount_b / reserve_b
            # LP tokens proportional to contribution
            lp_tokens_a = (amount_a * pool.total_lp_tokens) / pool.reserve_a
            lp_tokens_b = (amount_b * pool.total_lp_tokens) / pool.reserve_b
            
            # Use minimum to maintain ratio
            lp_tokens = min(lp_tokens_a, lp_tokens_b)
        
        # Update pool reserves
        pool.reserve_a += amount_a
        pool.reserve_b += amount_b
        pool.total_lp_tokens += lp_tokens
        
        # Create or update position
        position = LiquidityPosition(
            provider_address=provider_address,
            pool_id=pool_id,
            lp_tokens=lp_tokens,
            token_a_deposited=amount_a,
            token_b_deposited=amount_b,
            timestamp=time.time()
        )
        
        if provider_address not in self.positions:
            self.positions[provider_address] = []
        
        self.positions[provider_address].append(position)
        
        if provider_address not in self.pool_positions[pool_id]:
            self.pool_positions[pool_id].append(provider_address)
        
        return True, f"Added liquidity: {lp_tokens} LP tokens minted", lp_tokens
    
    def remove_liquidity(self, pool_id: str, provider_address: str,
                        lp_tokens: Decimal) -> Tuple[bool, str, Decimal, Decimal]:
        """
        Remove liquidity from a pool.
        
        Args:
            pool_id: ID of the pool
            provider_address: Address of liquidity provider
            lp_tokens: Amount of LP tokens to burn
            
        Returns:
            Tuple[bool, str, Decimal, Decimal]: (success, message, amount_a, amount_b)
        """
        if pool_id not in self.pools:
            return False, "Pool not found", Decimal('0.0'), Decimal('0.0')
        
        pool = self.pools[pool_id]
        
        if lp_tokens <= 0:
            return False, "LP tokens must be positive", Decimal('0.0'), Decimal('0.0')
        
        # Find provider's positions
        if provider_address not in self.positions:
            return False, "No positions found", Decimal('0.0'), Decimal('0.0')
        
        # Calculate total LP tokens for this provider in this pool
        total_provider_lp = sum(
            pos.lp_tokens for pos in self.positions[provider_address]
            if pos.pool_id == pool_id
        )
        
        if total_provider_lp < lp_tokens:
            return False, "Insufficient LP tokens", Decimal('0.0'), Decimal('0.0')
        
        # Calculate amounts to return (proportional to LP tokens)
        amount_a = (lp_tokens * pool.reserve_a) / pool.total_lp_tokens
        amount_b = (lp_tokens * pool.reserve_b) / pool.total_lp_tokens
        
        # Update pool reserves
        pool.reserve_a -= amount_a
        pool.reserve_b -= amount_b
        pool.total_lp_tokens -= lp_tokens
        
        # Update positions (burn LP tokens from oldest positions first)
        remaining_to_burn = lp_tokens
        positions_to_remove = []
        
        for i, pos in enumerate(self.positions[provider_address]):
            if pos.pool_id != pool_id:
                continue
            
            if remaining_to_burn <= 0:
                break
            
            if pos.lp_tokens <= remaining_to_burn:
                # Burn entire position
                remaining_to_burn -= pos.lp_tokens
                positions_to_remove.append(i)
            else:
                # Partial burn
                pos.lp_tokens -= remaining_to_burn
                remaining_to_burn = Decimal('0.0')
        
        # Remove fully burned positions
        for i in reversed(positions_to_remove):
            self.positions[provider_address].pop(i)
        
        return True, f"Removed liquidity: {amount_a} {pool.token_a_symbol}, {amount_b} {pool.token_b_symbol}", amount_a, amount_b
    
    def swap(self, pool_id: str, trader_address: str, input_token: str,
            input_amount: Decimal) -> Tuple[bool, str, Decimal, Decimal]:
        """
        Execute a token swap.
        
        Args:
            pool_id: ID of the pool
            trader_address: Address of the trader
            input_token: Symbol of input token
            input_amount: Amount of input token
            
        Returns:
            Tuple[bool, str, Decimal, Decimal]: (success, message, output_amount, fee_amount)
        """
        if pool_id not in self.pools:
            return False, "Pool not found", Decimal('0.0'), Decimal('0.0')
        
        pool = self.pools[pool_id]
        
        if pool.status != PoolStatus.ACTIVE:
            return False, f"Pool is {pool.status.value}", Decimal('0.0'), Decimal('0.0')
        
        if input_amount <= 0:
            return False, "Input amount must be positive", Decimal('0.0'), Decimal('0.0')
        
        # Determine which token is input
        if input_token == pool.token_a_symbol:
            input_is_token_a = True
            output_token = pool.token_b_symbol
        elif input_token == pool.token_b_symbol:
            input_is_token_a = False
            output_token = pool.token_a_symbol
        else:
            return False, "Invalid input token", Decimal('0.0'), Decimal('0.0')
        
        # Calculate output amount
        output_amount, fee_amount = pool.calculate_output_amount(input_amount, input_is_token_a)
        
        if output_amount <= 0:
            return False, "Insufficient liquidity", Decimal('0.0'), Decimal('0.0')
        
        # Update reserves
        if input_is_token_a:
            pool.reserve_a += input_amount
            pool.reserve_b -= output_amount
            pool.total_volume_a += input_amount
        else:
            pool.reserve_b += input_amount
            pool.reserve_a -= output_amount
            pool.total_volume_b += input_amount
        
        pool.total_fees_collected += fee_amount
        
        # Distribute fees to liquidity providers (fees stay in pool, increasing value of LP tokens)
        
        return True, f"Swapped {input_amount} {input_token} for {output_amount} {output_token}", output_amount, fee_amount
    
    def get_pool_info(self, pool_id: str) -> Optional[Dict]:
        """
        Get detailed pool information.
        
        Args:
            pool_id: ID of the pool
            
        Returns:
            Optional[Dict]: Pool information or None
        """
        if pool_id not in self.pools:
            return None
        
        pool = self.pools[pool_id]
        
        return {
            'pool': pool.to_dict(),
            'price_a_to_b': str(pool.calculate_price_a_to_b()) if pool.calculate_price_a_to_b() else None,
            'price_b_to_a': str(pool.calculate_price_b_to_a()) if pool.calculate_price_b_to_a() else None,
            'constant_product': str(pool.get_constant_product()),
            'provider_count': len(self.pool_positions.get(pool_id, []))
        }
    
    def get_provider_positions(self, provider_address: str) -> List[Dict]:
        """
        Get all positions for a liquidity provider.
        
        Args:
            provider_address: Address of the provider
            
        Returns:
            List[Dict]: List of positions
        """
        if provider_address not in self.positions:
            return []
        
        return [pos.to_dict() for pos in self.positions[provider_address]]
    
    def get_all_pools(self) -> List[Dict]:
        """
        Get information about all pools.
        
        Returns:
            List[Dict]: List of pool information
        """
        return [self.get_pool_info(pool_id) for pool_id in self.pools.keys()]
    
    def calculate_swap_quote(self, pool_id: str, input_token: str,
                            input_amount: Decimal) -> Optional[Dict]:
        """
        Get a quote for a swap without executing it.
        
        Args:
            pool_id: ID of the pool
            input_token: Symbol of input token
            input_amount: Amount of input token
            
        Returns:
            Optional[Dict]: Quote information or None
        """
        if pool_id not in self.pools:
            return None
        
        pool = self.pools[pool_id]
        
        if input_token == pool.token_a_symbol:
            input_is_token_a = True
            output_token = pool.token_b_symbol
        elif input_token == pool.token_b_symbol:
            input_is_token_a = False
            output_token = pool.token_a_symbol
        else:
            return None
        
        output_amount, fee_amount = pool.calculate_output_amount(input_amount, input_is_token_a)
        
        if output_amount <= 0:
            return None
        
        price = output_amount / input_amount if input_amount > 0 else Decimal('0.0')
        price_impact = self._calculate_price_impact(pool, input_amount, input_is_token_a)
        
        return {
            'input_token': input_token,
            'input_amount': str(input_amount),
            'output_token': output_token,
            'output_amount': str(output_amount),
            'fee_amount': str(fee_amount),
            'price': str(price),
            'price_impact_percentage': str(price_impact * 100)
        }
    
    def _calculate_price_impact(self, pool: LiquidityPool, input_amount: Decimal,
                               input_is_token_a: bool) -> Decimal:
        """Calculate price impact of a swap."""
        if input_is_token_a:
            if pool.reserve_a == 0:
                return Decimal('0.0')
            return input_amount / (pool.reserve_a + input_amount)
        else:
            if pool.reserve_b == 0:
                return Decimal('0.0')
            return input_amount / (pool.reserve_b + input_amount)
