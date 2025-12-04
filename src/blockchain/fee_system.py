"""
Fee Management System for PlayerGold blockchain.
Implements dynamic fees with token burning (20% liquidity, 80% burn).
"""

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from enum import Enum

from .transaction import Transaction, TransactionType, FeeDistribution


class NetworkCongestion(Enum):
    """Network congestion levels for dynamic fee calculation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FeeStructure:
    """Fee structure configuration for different transaction types."""
    base_fee: Decimal
    congestion_multiplier: Decimal
    min_fee: Decimal
    max_fee: Decimal


@dataclass
class NetworkMetrics:
    """Network metrics for fee calculation."""
    transactions_per_second: float
    pending_transactions: int
    average_block_time: float
    network_capacity: int  # Max TPS
    timestamp: float


@dataclass
class BurnRecord:
    """Record of token burning transaction."""
    transaction_hash: str
    amount_burned: Decimal
    block_index: int
    timestamp: float
    burn_reason: str  # "fee_burn", "voluntary_burn", etc.


@dataclass
class SupplyInfo:
    """Token supply information."""
    total_supply: Decimal
    circulating_supply: Decimal
    total_burned: Decimal
    last_updated: float


class FeeCalculator:
    """
    Calculates dynamic fees based on network congestion.
    Implements PlayerGold tokenomics with fee burning.
    """
    
    def __init__(self):
        # Fee structures for different transaction types
        self.fee_structures = {
            TransactionType.TRANSFER: FeeStructure(
                base_fee=Decimal('0.01'),
                congestion_multiplier=Decimal('2.0'),
                min_fee=Decimal('0.001'),
                max_fee=Decimal('1.0')
            ),
            TransactionType.STAKE: FeeStructure(
                base_fee=Decimal('0.05'),
                congestion_multiplier=Decimal('1.5'),
                min_fee=Decimal('0.01'),
                max_fee=Decimal('2.0')
            ),
            TransactionType.UNSTAKE: FeeStructure(
                base_fee=Decimal('0.05'),
                congestion_multiplier=Decimal('1.5'),
                min_fee=Decimal('0.01'),
                max_fee=Decimal('2.0')
            ),
            TransactionType.BURN: FeeStructure(
                base_fee=Decimal('0.0'),  # No fee for voluntary burns
                congestion_multiplier=Decimal('0.0'),
                min_fee=Decimal('0.0'),
                max_fee=Decimal('0.0')
            ),
            TransactionType.REWARD: FeeStructure(
                base_fee=Decimal('0.0'),  # No fee for rewards
                congestion_multiplier=Decimal('0.0'),
                min_fee=Decimal('0.0'),
                max_fee=Decimal('0.0')
            )
        }
        
        # Network congestion thresholds (TPS)
        self.congestion_thresholds = {
            NetworkCongestion.LOW: 25,      # < 25 TPS
            NetworkCongestion.MEDIUM: 50,   # 25-50 TPS
            NetworkCongestion.HIGH: 75,     # 50-75 TPS
            NetworkCongestion.CRITICAL: 100 # > 75 TPS
        }
    
    def calculate_fee(
        self,
        transaction_type: TransactionType,
        network_metrics: NetworkMetrics,
        amount: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate dynamic fee for a transaction.
        
        Args:
            transaction_type: Type of transaction
            network_metrics: Current network metrics
            amount: Transaction amount (for percentage-based fees)
            
        Returns:
            Decimal: Calculated fee amount
        """
        fee_structure = self.fee_structures.get(transaction_type)
        if not fee_structure:
            # Default fee structure for unknown types
            fee_structure = self.fee_structures[TransactionType.TRANSFER]
        
        # Get congestion level
        congestion = self._get_congestion_level(network_metrics)
        
        # Calculate base fee with congestion multiplier
        congestion_multiplier = self._get_congestion_multiplier(congestion)
        calculated_fee = fee_structure.base_fee * congestion_multiplier
        
        # Apply min/max limits
        calculated_fee = max(calculated_fee, fee_structure.min_fee)
        calculated_fee = min(calculated_fee, fee_structure.max_fee)
        
        return calculated_fee
    
    def _get_congestion_level(self, metrics: NetworkMetrics) -> NetworkCongestion:
        """
        Determine network congestion level from metrics.
        
        Args:
            metrics: Network metrics
            
        Returns:
            NetworkCongestion: Current congestion level
        """
        tps = metrics.transactions_per_second
        
        if tps < self.congestion_thresholds[NetworkCongestion.LOW]:
            return NetworkCongestion.LOW
        elif tps < self.congestion_thresholds[NetworkCongestion.MEDIUM]:
            return NetworkCongestion.MEDIUM
        elif tps < self.congestion_thresholds[NetworkCongestion.HIGH]:
            return NetworkCongestion.HIGH
        else:
            return NetworkCongestion.CRITICAL
    
    def _get_congestion_multiplier(self, congestion: NetworkCongestion) -> Decimal:
        """
        Get fee multiplier based on congestion level.
        
        Args:
            congestion: Network congestion level
            
        Returns:
            Decimal: Fee multiplier
        """
        multipliers = {
            NetworkCongestion.LOW: Decimal('1.0'),
            NetworkCongestion.MEDIUM: Decimal('1.5'),
            NetworkCongestion.HIGH: Decimal('2.0'),
            NetworkCongestion.CRITICAL: Decimal('3.0')
        }
        
        return multipliers[congestion]
    
    def estimate_fee(
        self,
        transaction_type: TransactionType,
        current_tps: float,
        network_capacity: int = 100
    ) -> Decimal:
        """
        Estimate fee for a transaction type given current network conditions.
        
        Args:
            transaction_type: Type of transaction
            current_tps: Current transactions per second
            network_capacity: Maximum network capacity
            
        Returns:
            Decimal: Estimated fee
        """
        metrics = NetworkMetrics(
            transactions_per_second=current_tps,
            pending_transactions=0,
            average_block_time=2.0,
            network_capacity=network_capacity,
            timestamp=time.time()
        )
        
        return self.calculate_fee(transaction_type, metrics)


class TokenBurnManager:
    """
    Manages token burning operations and supply tracking.
    """
    
    def __init__(self, initial_supply: Decimal = Decimal('1000000000')):  # 1B tokens
        self.burn_address = "0x0000000000000000000000000000000000000000"
        self.liquidity_pool_address = "liquidity_pool"
        
        self.supply_info = SupplyInfo(
            total_supply=initial_supply,
            circulating_supply=initial_supply,
            total_burned=Decimal('0'),
            last_updated=time.time()
        )
        
        self.burn_records: List[BurnRecord] = []
    
    def process_fee_distribution(
        self,
        total_fee: Decimal,
        block_index: int,
        transaction_hash: str
    ) -> Tuple[Transaction, Transaction]:
        """
        Process fee distribution (20% liquidity, 80% burn).
        
        Args:
            total_fee: Total fee amount to distribute
            block_index: Current block index
            transaction_hash: Hash of the fee-generating transaction
            
        Returns:
            Tuple[Transaction, Transaction]: Liquidity and burn transactions
        """
        distribution = FeeDistribution.calculate_distribution(total_fee)
        current_time = time.time()
        
        # Create liquidity pool transaction (20%)
        liquidity_tx = Transaction(
            from_address="fee_collector",
            to_address=self.liquidity_pool_address,
            amount=distribution.liquidity_pool,
            fee=Decimal('0.0'),  # No fee on fee distribution
            timestamp=current_time,
            transaction_type=TransactionType.TRANSFER,
            nonce=0
        )
        
        # Create burn transaction (80%)
        burn_tx = Transaction(
            from_address="fee_collector",
            to_address=self.burn_address,
            amount=distribution.burn_address,
            fee=Decimal('0.0'),  # No fee on burning
            timestamp=current_time,
            transaction_type=TransactionType.BURN,
            nonce=1
        )
        
        # Record the burn
        self._record_burn(
            transaction_hash=burn_tx.hash,
            amount=distribution.burn_address,
            block_index=block_index,
            reason="fee_burn"
        )
        
        return liquidity_tx, burn_tx
    
    def process_voluntary_burn(
        self,
        burner_address: str,
        amount: Decimal,
        block_index: int
    ) -> Transaction:
        """
        Process voluntary token burning by users.
        
        Args:
            burner_address: Address of the user burning tokens
            amount: Amount to burn
            block_index: Current block index
            
        Returns:
            Transaction: Burn transaction
        """
        burn_tx = Transaction(
            from_address=burner_address,
            to_address=self.burn_address,
            amount=amount,
            fee=Decimal('0.0'),  # No fee for voluntary burns
            timestamp=time.time(),
            transaction_type=TransactionType.BURN,
            nonce=0
        )
        
        # Record the burn
        self._record_burn(
            transaction_hash=burn_tx.hash,
            amount=amount,
            block_index=block_index,
            reason="voluntary_burn"
        )
        
        return burn_tx
    
    def _record_burn(
        self,
        transaction_hash: str,
        amount: Decimal,
        block_index: int,
        reason: str
    ) -> None:
        """
        Record a token burn and update supply information.
        
        Args:
            transaction_hash: Hash of the burn transaction
            amount: Amount burned
            block_index: Block index where burn occurred
            reason: Reason for burning
        """
        burn_record = BurnRecord(
            transaction_hash=transaction_hash,
            amount_burned=amount,
            block_index=block_index,
            timestamp=time.time(),
            burn_reason=reason
        )
        
        self.burn_records.append(burn_record)
        
        # Update supply info
        self.supply_info.total_burned += amount
        self.supply_info.circulating_supply -= amount
        self.supply_info.last_updated = time.time()
    
    def get_supply_info(self) -> SupplyInfo:
        """
        Get current token supply information.
        
        Returns:
            SupplyInfo: Current supply data
        """
        return self.supply_info
    
    def get_burn_history(
        self,
        limit: Optional[int] = None,
        reason_filter: Optional[str] = None
    ) -> List[BurnRecord]:
        """
        Get burn history with optional filtering.
        
        Args:
            limit: Maximum number of records to return
            reason_filter: Filter by burn reason
            
        Returns:
            List[BurnRecord]: Filtered burn records
        """
        records = self.burn_records
        
        # Filter by reason if specified
        if reason_filter:
            records = [r for r in records if r.burn_reason == reason_filter]
        
        # Sort by timestamp (most recent first)
        records = sorted(records, key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit if specified
        if limit:
            records = records[:limit]
        
        return records
    
    def get_total_burned_by_reason(self, reason: str) -> Decimal:
        """
        Get total amount burned for a specific reason.
        
        Args:
            reason: Burn reason to filter by
            
        Returns:
            Decimal: Total amount burned for the reason
        """
        return sum(
            record.amount_burned
            for record in self.burn_records
            if record.burn_reason == reason
        )
    
    def calculate_burn_rate(self, time_period_hours: int = 24) -> Decimal:
        """
        Calculate burn rate over a specified time period.
        
        Args:
            time_period_hours: Time period in hours
            
        Returns:
            Decimal: Burn rate (tokens per hour)
        """
        cutoff_time = time.time() - (time_period_hours * 3600)
        
        recent_burns = [
            record for record in self.burn_records
            if record.timestamp >= cutoff_time
        ]
        
        total_burned = sum(record.amount_burned for record in recent_burns)
        
        if time_period_hours == 0:
            return Decimal('0')
        
        return total_burned / Decimal(str(time_period_hours))


class NetworkMetricsTracker:
    """
    Tracks network metrics for fee calculation.
    """
    
    def __init__(self, capacity: int = 100):
        self.network_capacity = capacity
        self.metrics_history: List[NetworkMetrics] = []
        self.current_metrics = NetworkMetrics(
            transactions_per_second=0.0,
            pending_transactions=0,
            average_block_time=2.0,
            network_capacity=capacity,
            timestamp=time.time()
        )
    
    def update_metrics(
        self,
        tps: float,
        pending_tx: int,
        avg_block_time: float
    ) -> None:
        """
        Update network metrics.
        
        Args:
            tps: Current transactions per second
            pending_tx: Number of pending transactions
            avg_block_time: Average block time in seconds
        """
        self.current_metrics = NetworkMetrics(
            transactions_per_second=tps,
            pending_transactions=pending_tx,
            average_block_time=avg_block_time,
            network_capacity=self.network_capacity,
            timestamp=time.time()
        )
        
        # Keep history (last 100 entries)
        self.metrics_history.append(self.current_metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
    
    def get_current_metrics(self) -> NetworkMetrics:
        """
        Get current network metrics.
        
        Returns:
            NetworkMetrics: Current metrics
        """
        return self.current_metrics
    
    def get_average_tps(self, time_period_minutes: int = 10) -> float:
        """
        Get average TPS over a time period.
        
        Args:
            time_period_minutes: Time period in minutes
            
        Returns:
            float: Average TPS
        """
        cutoff_time = time.time() - (time_period_minutes * 60)
        
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return self.current_metrics.transactions_per_second
        
        total_tps = sum(m.transactions_per_second for m in recent_metrics)
        return total_tps / len(recent_metrics)


def calculate_deflationary_impact(
    current_supply: Decimal,
    burn_rate_per_hour: Decimal,
    time_horizon_hours: int
) -> Dict[str, Decimal]:
    """
    Calculate the deflationary impact of token burning.
    
    Args:
        current_supply: Current circulating supply
        burn_rate_per_hour: Tokens burned per hour
        time_horizon_hours: Time horizon for projection
        
    Returns:
        Dict[str, Decimal]: Deflationary impact metrics
    """
    total_burned = burn_rate_per_hour * Decimal(str(time_horizon_hours))
    final_supply = current_supply - total_burned
    
    if current_supply == 0:
        deflation_percentage = Decimal('0')
    else:
        deflation_percentage = (total_burned / current_supply) * Decimal('100')
    
    return {
        'total_burned': total_burned,
        'final_supply': final_supply,
        'deflation_percentage': deflation_percentage,
        'burn_rate_per_hour': burn_rate_per_hour,
        'time_horizon_hours': Decimal(str(time_horizon_hours))
    }