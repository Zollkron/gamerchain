"""
Tests for PlayerGold fee management and token burning system.
"""

import pytest
import time
from decimal import Decimal

from src.blockchain.fee_system import (
    FeeCalculator, TokenBurnManager, NetworkMetricsTracker,
    NetworkCongestion, NetworkMetrics, FeeStructure,
    calculate_deflationary_impact
)
from src.blockchain.transaction import TransactionType


class TestFeeCalculator:
    """Test cases for FeeCalculator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = FeeCalculator()
        
        self.low_congestion_metrics = NetworkMetrics(
            transactions_per_second=10.0,
            pending_transactions=5,
            average_block_time=2.0,
            network_capacity=100,
            timestamp=time.time()
        )
        
        self.high_congestion_metrics = NetworkMetrics(
            transactions_per_second=80.0,
            pending_transactions=200,
            average_block_time=5.0,
            network_capacity=100,
            timestamp=time.time()
        )
    
    def test_fee_calculator_initialization(self):
        """Test fee calculator initialization."""
        assert TransactionType.TRANSFER in self.calculator.fee_structures
        assert TransactionType.STAKE in self.calculator.fee_structures
        assert TransactionType.BURN in self.calculator.fee_structures
        
        # Check burn transactions have no fees
        burn_fee_structure = self.calculator.fee_structures[TransactionType.BURN]
        assert burn_fee_structure.base_fee == Decimal('0.0')
        assert burn_fee_structure.max_fee == Decimal('0.0')
    
    def test_calculate_fee_low_congestion(self):
        """Test fee calculation under low congestion."""
        fee = self.calculator.calculate_fee(
            TransactionType.TRANSFER,
            self.low_congestion_metrics
        )
        
        # Should be base fee with low congestion multiplier (1.0)
        expected_fee = Decimal('0.01')  # Base fee for transfers
        assert fee == expected_fee
    
    def test_calculate_fee_high_congestion(self):
        """Test fee calculation under high congestion."""
        fee = self.calculator.calculate_fee(
            TransactionType.TRANSFER,
            self.high_congestion_metrics
        )
        
        # 80 TPS is CRITICAL congestion (>75), which has 3.0 multiplier
        base_fee = Decimal('0.01')
        expected_fee = base_fee * Decimal('3.0')  # Critical congestion multiplier
        assert fee == expected_fee
    
    def test_calculate_fee_burn_transaction(self):
        """Test fee calculation for burn transactions (should be zero)."""
        fee = self.calculator.calculate_fee(
            TransactionType.BURN,
            self.high_congestion_metrics
        )
        
        assert fee == Decimal('0.0')
    
    def test_calculate_fee_reward_transaction(self):
        """Test fee calculation for reward transactions (should be zero)."""
        fee = self.calculator.calculate_fee(
            TransactionType.REWARD,
            self.low_congestion_metrics
        )
        
        assert fee == Decimal('0.0')
    
    def test_calculate_fee_stake_transaction(self):
        """Test fee calculation for stake transactions."""
        fee = self.calculator.calculate_fee(
            TransactionType.STAKE,
            self.low_congestion_metrics
        )
        
        # Should be stake base fee (0.05) with low congestion
        expected_fee = Decimal('0.05')
        assert fee == expected_fee
    
    def test_fee_min_max_limits(self):
        """Test that fees respect min/max limits."""
        # Create extreme congestion metrics
        extreme_metrics = NetworkMetrics(
            transactions_per_second=1000.0,  # Very high
            pending_transactions=10000,
            average_block_time=30.0,
            network_capacity=100,
            timestamp=time.time()
        )
        
        fee = self.calculator.calculate_fee(
            TransactionType.TRANSFER,
            extreme_metrics
        )
        
        # Should not exceed max fee
        max_fee = self.calculator.fee_structures[TransactionType.TRANSFER].max_fee
        assert fee <= max_fee
    
    def test_get_congestion_level(self):
        """Test congestion level determination."""
        # Low congestion
        low_metrics = NetworkMetrics(
            transactions_per_second=10.0,
            pending_transactions=5,
            average_block_time=2.0,
            network_capacity=100,
            timestamp=time.time()
        )
        
        congestion = self.calculator._get_congestion_level(low_metrics)
        assert congestion == NetworkCongestion.LOW
        
        # High congestion
        high_metrics = NetworkMetrics(
            transactions_per_second=60.0,
            pending_transactions=200,
            average_block_time=5.0,
            network_capacity=100,
            timestamp=time.time()
        )
        
        congestion = self.calculator._get_congestion_level(high_metrics)
        assert congestion == NetworkCongestion.HIGH
        
        # Critical congestion
        critical_metrics = NetworkMetrics(
            transactions_per_second=90.0,
            pending_transactions=500,
            average_block_time=10.0,
            network_capacity=100,
            timestamp=time.time()
        )
        
        congestion = self.calculator._get_congestion_level(critical_metrics)
        assert congestion == NetworkCongestion.CRITICAL
    
    def test_get_congestion_multiplier(self):
        """Test congestion multiplier calculation."""
        assert self.calculator._get_congestion_multiplier(NetworkCongestion.LOW) == Decimal('1.0')
        assert self.calculator._get_congestion_multiplier(NetworkCongestion.MEDIUM) == Decimal('1.5')
        assert self.calculator._get_congestion_multiplier(NetworkCongestion.HIGH) == Decimal('2.0')
        assert self.calculator._get_congestion_multiplier(NetworkCongestion.CRITICAL) == Decimal('3.0')
    
    def test_estimate_fee(self):
        """Test fee estimation."""
        # Low TPS
        low_fee = self.calculator.estimate_fee(TransactionType.TRANSFER, 10.0)
        assert low_fee == Decimal('0.01')  # Base fee
        
        # High TPS
        high_fee = self.calculator.estimate_fee(TransactionType.TRANSFER, 80.0)
        assert high_fee > low_fee  # Should be higher due to congestion


class TestTokenBurnManager:
    """Test cases for TokenBurnManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.burn_manager = TokenBurnManager(initial_supply=Decimal('1000000'))
    
    def test_burn_manager_initialization(self):
        """Test burn manager initialization."""
        supply_info = self.burn_manager.get_supply_info()
        
        assert supply_info.total_supply == Decimal('1000000')
        assert supply_info.circulating_supply == Decimal('1000000')
        assert supply_info.total_burned == Decimal('0')
        assert self.burn_manager.burn_address == "0x0000000000000000000000000000000000000000"
    
    def test_process_fee_distribution(self):
        """Test fee distribution processing (60% burn, 30% maintenance, 10% liquidity)."""
        total_fee = Decimal('100.0')
        
        burn_tx, maintenance_tx, liquidity_tx = self.burn_manager.process_fee_distribution(
            total_fee=total_fee,
            block_index=1,
            transaction_hash="test_hash"
        )
        
        # Check burn transaction (60%)
        assert burn_tx.to_address == self.burn_manager.burn_address
        assert burn_tx.amount == Decimal('60.0')  # 60% of 100
        assert burn_tx.transaction_type == TransactionType.BURN
        
        # Check maintenance transaction (30%)
        assert maintenance_tx.to_address == "network_maintenance"
        assert maintenance_tx.amount == Decimal('30.0')  # 30% of 100
        assert maintenance_tx.fee == Decimal('0.0')
        
        # Check liquidity transaction (10%)
        assert liquidity_tx.to_address == "liquidity_pool"
        assert liquidity_tx.amount == Decimal('10.0')  # 10% of 100
        assert liquidity_tx.fee == Decimal('0.0')
        
        # Check burn was recorded
        assert len(self.burn_manager.burn_records) == 1
        burn_record = self.burn_manager.burn_records[0]
        assert burn_record.amount_burned == Decimal('60.0')
        assert burn_record.burn_reason == "fee_burn"
        
        # Check supply was updated
        supply_info = self.burn_manager.get_supply_info()
        assert supply_info.total_burned == Decimal('60.0')
        assert supply_info.circulating_supply == Decimal('999940.0')  # 1000000 - 60
    
    def test_process_voluntary_burn(self):
        """Test voluntary token burning."""
        burn_amount = Decimal('1000.0')
        
        burn_tx = self.burn_manager.process_voluntary_burn(
            burner_address="user123",
            amount=burn_amount,
            block_index=2
        )
        
        # Check burn transaction
        assert burn_tx.from_address == "user123"
        assert burn_tx.to_address == self.burn_manager.burn_address
        assert burn_tx.amount == burn_amount
        assert burn_tx.fee == Decimal('0.0')
        assert burn_tx.transaction_type == TransactionType.BURN
        
        # Check burn was recorded
        assert len(self.burn_manager.burn_records) == 1
        burn_record = self.burn_manager.burn_records[0]
        assert burn_record.amount_burned == burn_amount
        assert burn_record.burn_reason == "voluntary_burn"
        
        # Check supply was updated
        supply_info = self.burn_manager.get_supply_info()
        assert supply_info.total_burned == burn_amount
        assert supply_info.circulating_supply == Decimal('999000.0')  # 1000000 - 1000
    
    def test_multiple_burns(self):
        """Test multiple burn operations."""
        # Fee burn
        self.burn_manager.process_fee_distribution(
            total_fee=Decimal('50.0'),
            block_index=1,
            transaction_hash="fee_hash"
        )
        
        # Voluntary burn
        self.burn_manager.process_voluntary_burn(
            burner_address="user1",
            amount=Decimal('200.0'),
            block_index=2
        )
        
        # Another voluntary burn
        self.burn_manager.process_voluntary_burn(
            burner_address="user2",
            amount=Decimal('300.0'),
            block_index=3
        )
        
        # Check total burns
        assert len(self.burn_manager.burn_records) == 3
        
        supply_info = self.burn_manager.get_supply_info()
        # Fee burn: 40 (80% of 50) + Voluntary: 200 + 300 = 540
        expected_burned = Decimal('40.0') + Decimal('200.0') + Decimal('300.0')
        assert supply_info.total_burned == expected_burned
        assert supply_info.circulating_supply == Decimal('1000000') - expected_burned
    
    def test_get_burn_history(self):
        """Test burn history retrieval."""
        # Add some burns
        self.burn_manager.process_fee_distribution(Decimal('100.0'), 1, "hash1")
        self.burn_manager.process_voluntary_burn("user1", Decimal('200.0'), 2)
        self.burn_manager.process_voluntary_burn("user2", Decimal('300.0'), 3)
        
        # Get all history
        all_history = self.burn_manager.get_burn_history()
        assert len(all_history) == 3
        
        # Get limited history
        limited_history = self.burn_manager.get_burn_history(limit=2)
        assert len(limited_history) == 2
        
        # Get filtered history
        fee_burns = self.burn_manager.get_burn_history(reason_filter="fee_burn")
        assert len(fee_burns) == 1
        assert fee_burns[0].burn_reason == "fee_burn"
        
        voluntary_burns = self.burn_manager.get_burn_history(reason_filter="voluntary_burn")
        assert len(voluntary_burns) == 2
        for burn in voluntary_burns:
            assert burn.burn_reason == "voluntary_burn"
    
    def test_get_total_burned_by_reason(self):
        """Test getting total burned by reason."""
        # Add burns
        self.burn_manager.process_fee_distribution(Decimal('100.0'), 1, "hash1")  # Burns 60
        self.burn_manager.process_voluntary_burn("user1", Decimal('200.0'), 2)
        self.burn_manager.process_voluntary_burn("user2", Decimal('300.0'), 3)
        
        fee_burned = self.burn_manager.get_total_burned_by_reason("fee_burn")
        assert fee_burned == Decimal('60.0')  # 60% of 100
        
        voluntary_burned = self.burn_manager.get_total_burned_by_reason("voluntary_burn")
        assert voluntary_burned == Decimal('500.0')  # 200 + 300
    
    def test_calculate_burn_rate(self):
        """Test burn rate calculation."""
        # Add burns at different times
        current_time = time.time()
        
        # Mock timestamps for testing
        self.burn_manager.burn_records = [
            type('BurnRecord', (), {
                'amount_burned': Decimal('100.0'),
                'timestamp': current_time - 1800,  # 30 minutes ago
                'burn_reason': 'fee_burn'
            })(),
            type('BurnRecord', (), {
                'amount_burned': Decimal('200.0'),
                'timestamp': current_time - 900,   # 15 minutes ago
                'burn_reason': 'voluntary_burn'
            })(),
            type('BurnRecord', (), {
                'amount_burned': Decimal('300.0'),
                'timestamp': current_time - 7200,  # 2 hours ago (outside 1 hour window)
                'burn_reason': 'fee_burn'
            })()
        ]
        
        # Calculate burn rate for last 1 hour
        burn_rate = self.burn_manager.calculate_burn_rate(time_period_hours=1)
        
        # Should include first two burns (300 tokens in 1 hour = 300 per hour)
        expected_rate = Decimal('300.0')  # 100 + 200
        assert burn_rate == expected_rate
    
    def test_calculate_burn_rate_zero_period(self):
        """Test burn rate calculation with zero time period."""
        burn_rate = self.burn_manager.calculate_burn_rate(time_period_hours=0)
        assert burn_rate == Decimal('0')


class TestNetworkMetricsTracker:
    """Test cases for NetworkMetricsTracker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = NetworkMetricsTracker(capacity=100)
    
    def test_tracker_initialization(self):
        """Test metrics tracker initialization."""
        assert self.tracker.network_capacity == 100
        
        current = self.tracker.get_current_metrics()
        assert current.transactions_per_second == 0.0
        assert current.network_capacity == 100
    
    def test_update_metrics(self):
        """Test updating network metrics."""
        self.tracker.update_metrics(
            tps=50.0,
            pending_tx=25,
            avg_block_time=2.5
        )
        
        current = self.tracker.get_current_metrics()
        assert current.transactions_per_second == 50.0
        assert current.pending_transactions == 25
        assert current.average_block_time == 2.5
        
        # Check history was updated
        assert len(self.tracker.metrics_history) == 1
    
    def test_metrics_history_limit(self):
        """Test that metrics history is limited to 100 entries."""
        # Add 150 metrics updates
        for i in range(150):
            self.tracker.update_metrics(
                tps=float(i),
                pending_tx=i,
                avg_block_time=2.0
            )
        
        # Should only keep last 100
        assert len(self.tracker.metrics_history) == 100
        
        # Should have the most recent entries
        latest = self.tracker.metrics_history[-1]
        assert latest.transactions_per_second == 149.0
    
    def test_get_average_tps(self):
        """Test average TPS calculation."""
        # Add some metrics
        tps_values = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        for tps in tps_values:
            self.tracker.update_metrics(tps, 10, 2.0)
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Get average (should be mean of all values)
        avg_tps = self.tracker.get_average_tps(time_period_minutes=60)  # Large window
        expected_avg = sum(tps_values) / len(tps_values)
        
        assert abs(avg_tps - expected_avg) < 0.1  # Allow small floating point differences
    
    def test_get_average_tps_no_history(self):
        """Test average TPS when no history exists."""
        # Set current metrics
        self.tracker.update_metrics(25.0, 5, 2.0)
        
        # Clear history
        self.tracker.metrics_history = []
        
        # Should return current TPS
        avg_tps = self.tracker.get_average_tps(time_period_minutes=10)
        assert avg_tps == 25.0


class TestDeflationary:
    """Test cases for deflationary impact calculations."""
    
    def test_calculate_deflationary_impact(self):
        """Test deflationary impact calculation."""
        current_supply = Decimal('1000000')
        burn_rate = Decimal('100')  # 100 tokens per hour
        time_horizon = 24  # 24 hours
        
        impact = calculate_deflationary_impact(
            current_supply=current_supply,
            burn_rate_per_hour=burn_rate,
            time_horizon_hours=time_horizon
        )
        
        expected_burned = burn_rate * Decimal('24')  # 2400 tokens
        expected_final_supply = current_supply - expected_burned  # 997600
        expected_deflation_pct = (expected_burned / current_supply) * Decimal('100')  # 0.24%
        
        assert impact['total_burned'] == expected_burned
        assert impact['final_supply'] == expected_final_supply
        assert abs(impact['deflation_percentage'] - expected_deflation_pct) < Decimal('0.01')
        assert impact['burn_rate_per_hour'] == burn_rate
        assert impact['time_horizon_hours'] == Decimal('24')
    
    def test_deflationary_impact_zero_supply(self):
        """Test deflationary impact with zero supply."""
        impact = calculate_deflationary_impact(
            current_supply=Decimal('0'),
            burn_rate_per_hour=Decimal('100'),
            time_horizon_hours=24
        )
        
        assert impact['deflation_percentage'] == Decimal('0')
        assert impact['final_supply'] == Decimal('-2400')  # Negative supply
    
    def test_deflationary_impact_zero_burn_rate(self):
        """Test deflationary impact with zero burn rate."""
        current_supply = Decimal('1000000')
        
        impact = calculate_deflationary_impact(
            current_supply=current_supply,
            burn_rate_per_hour=Decimal('0'),
            time_horizon_hours=24
        )
        
        assert impact['total_burned'] == Decimal('0')
        assert impact['final_supply'] == current_supply
        assert impact['deflation_percentage'] == Decimal('0')