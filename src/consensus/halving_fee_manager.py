"""
Halving Fee Manager - Manages fee redistribution during halving events

This module implements the progressive reduction of mandatory token burning
and redistribution of fees to network maintenance and liquidity pool during
halving events in the PlayerGold blockchain.
"""

import logging
import time
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class FeeDistribution:
    """Represents fee distribution percentages at a point in time"""
    burn_percentage: Decimal
    developer_percentage: Decimal
    liquidity_percentage: Decimal
    halving_number: int
    block_number: int
    timestamp: float
    
    def validate(self) -> bool:
        """Validate that percentages sum to 100%"""
        total = self.burn_percentage + self.developer_percentage + self.liquidity_percentage
        return abs(total - Decimal('1.0')) < Decimal('0.001')  # Allow small rounding errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'burn_percentage': str(self.burn_percentage),
            'developer_percentage': str(self.developer_percentage),
            'liquidity_percentage': str(self.liquidity_percentage),
            'halving_number': self.halving_number,
            'block_number': self.block_number,
            'timestamp': self.timestamp
        }


@dataclass
class RedistributionEvent:
    """Represents a fee redistribution event"""
    halving_number: int
    block_number: int
    timestamp: float
    old_distribution: FeeDistribution
    new_distribution: FeeDistribution
    redistribution_amount: Decimal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and storage"""
        return {
            'halving_number': self.halving_number,
            'block_number': self.block_number,
            'timestamp': self.timestamp,
            'old_distribution': self.old_distribution.to_dict(),
            'new_distribution': self.new_distribution.to_dict(),
            'redistribution_amount': str(self.redistribution_amount)
        }


class HalvingFeeManager:
    """
    Manages fee distribution changes during halving events.
    
    Implements progressive reduction of burn percentage from 60% to 0%,
    redistributing 10% per halving with +5% to developer fee and +5% to liquidity pool.
    """
    
    def __init__(self, 
                 initial_burn: Decimal = Decimal('0.60'),
                 initial_developer: Decimal = Decimal('0.30'),
                 initial_liquidity: Decimal = Decimal('0.10'),
                 redistribution_amount: Decimal = Decimal('0.10')):
        """
        Initialize fee manager with starting percentages
        
        Args:
            initial_burn: Starting burn percentage (60%)
            initial_developer: Starting developer fee percentage (30%)
            initial_liquidity: Starting liquidity pool percentage (10%)
            redistribution_amount: Amount to redistribute per halving (10%)
        """
        self.initial_burn = initial_burn
        self.initial_developer = initial_developer
        self.initial_liquidity = initial_liquidity
        self.redistribution_amount = redistribution_amount
        
        # Current distribution percentages
        self.current_burn = initial_burn
        self.current_developer = initial_developer
        self.current_liquidity = initial_liquidity
        
        # History tracking
        self.redistribution_history: List[RedistributionEvent] = []
        
        # Validate initial percentages
        if not self._validate_percentages(self.current_burn, self.current_developer, self.current_liquidity):
            raise ValueError("Initial percentages must sum to 100%")
        
        logger.info(f"🔧 HalvingFeeManager initialized with distribution: "
                   f"Burn: {self.current_burn*100}%, "
                   f"Developer: {self.current_developer*100}%, "
                   f"Liquidity: {self.current_liquidity*100}%")
    
    def _validate_percentages(self, burn: Decimal, developer: Decimal, liquidity: Decimal) -> bool:
        """Validate that percentages sum to exactly 100%"""
        total = burn + developer + liquidity
        return abs(total - Decimal('1.0')) < Decimal('0.001')  # Allow small rounding errors
    
    def _round_percentage(self, value: Decimal) -> Decimal:
        """Round percentage to 2 decimal places to avoid precision errors"""
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def process_halving_redistribution(self, halving_number: int, block_number: int) -> Dict[str, Decimal]:
        """
        Process fee redistribution for a halving event
        
        Args:
            halving_number: The number of halvings that have occurred
            block_number: The block number where halving occurred
            
        Returns:
            Dict with new fee percentages
        """
        timestamp = time.time()
        
        # Store old distribution
        old_distribution = FeeDistribution(
            burn_percentage=self.current_burn,
            developer_percentage=self.current_developer,
            liquidity_percentage=self.current_liquidity,
            halving_number=halving_number - 1,  # Previous halving number
            block_number=block_number,
            timestamp=timestamp
        )
        
        # Check if burn percentage is already 0%
        if self.current_burn <= Decimal('0.0'):
            logger.info(f"🔒 Halving {halving_number}: Burn percentage already at 0%, no redistribution needed")
            return self.get_current_distribution()
        
        # Calculate new percentages
        burn_reduction = min(self.redistribution_amount, self.current_burn)  # Don't go below 0%
        developer_increase = burn_reduction / 2  # 5% (half of 10%)
        liquidity_increase = burn_reduction / 2  # 5% (half of 10%)
        
        # Apply changes
        new_burn = self._round_percentage(self.current_burn - burn_reduction)
        new_developer = self._round_percentage(self.current_developer + developer_increase)
        new_liquidity = self._round_percentage(self.current_liquidity + liquidity_increase)
        
        # Ensure we don't go below 0% for burn
        if new_burn < Decimal('0.0'):
            new_burn = Decimal('0.0')
        
        # Validate new percentages
        if not self._validate_percentages(new_burn, new_developer, new_liquidity):
            logger.error(f"❌ Invalid percentages after redistribution: "
                        f"Burn: {new_burn}, Developer: {new_developer}, Liquidity: {new_liquidity}")
            return self.get_current_distribution()  # Return current distribution on error
        
        # Update current percentages
        self.current_burn = new_burn
        self.current_developer = new_developer
        self.current_liquidity = new_liquidity
        
        # Create new distribution record
        new_distribution = FeeDistribution(
            burn_percentage=self.current_burn,
            developer_percentage=self.current_developer,
            liquidity_percentage=self.current_liquidity,
            halving_number=halving_number,
            block_number=block_number,
            timestamp=timestamp
        )
        
        # Record redistribution event
        redistribution_event = RedistributionEvent(
            halving_number=halving_number,
            block_number=block_number,
            timestamp=timestamp,
            old_distribution=old_distribution,
            new_distribution=new_distribution,
            redistribution_amount=burn_reduction
        )
        
        self.redistribution_history.append(redistribution_event)
        
        # Log the redistribution
        logger.info(f"🎯 HALVING {halving_number} FEE REDISTRIBUTION at block {block_number}")
        logger.info(f"📊 Old distribution: Burn: {old_distribution.burn_percentage*100}%, "
                   f"Dev: {old_distribution.developer_percentage*100}%, "
                   f"Liquidity: {old_distribution.liquidity_percentage*100}%")
        logger.info(f"📊 New distribution: Burn: {new_distribution.burn_percentage*100}%, "
                   f"Dev: {new_distribution.developer_percentage*100}%, "
                   f"Liquidity: {new_distribution.liquidity_percentage*100}%")
        logger.info(f"🔄 Redistributed: {burn_reduction*100}% from burn "
                   f"(+{developer_increase*100}% dev, +{liquidity_increase*100}% liquidity)")
        
        return self.get_current_distribution()
    
    def get_current_distribution(self) -> Dict[str, Decimal]:
        """Get current fee distribution percentages"""
        return {
            'burn': self.current_burn,
            'developer': self.current_developer,
            'liquidity': self.current_liquidity
        }
    
    def validate_percentages(self) -> bool:
        """Validate that current percentages sum to 100%"""
        return self._validate_percentages(self.current_burn, self.current_developer, self.current_liquidity)
    
    def get_redistribution_history(self) -> List[Dict]:
        """Get history of all fee redistributions"""
        return [event.to_dict() for event in self.redistribution_history]
    
    def get_current_distribution_info(self) -> Dict[str, Any]:
        """Get detailed information about current distribution"""
        return {
            'current_distribution': self.get_current_distribution(),
            'total_redistributions': len(self.redistribution_history),
            'burn_exhausted': self.current_burn <= Decimal('0.0'),
            'next_redistribution_amount': min(self.redistribution_amount, self.current_burn) if self.current_burn > Decimal('0.0') else Decimal('0.0'),
            'initial_distribution': {
                'burn': self.initial_burn,
                'developer': self.initial_developer,
                'liquidity': self.initial_liquidity
            }
        }
    
    def reset_to_initial(self):
        """Reset fee distribution to initial values (for testing/debugging)"""
        self.current_burn = self.initial_burn
        self.current_developer = self.initial_developer
        self.current_liquidity = self.initial_liquidity
        self.redistribution_history.clear()
        
        logger.warning(f"⚠️ Fee distribution reset to initial values: "
                      f"Burn: {self.current_burn*100}%, "
                      f"Developer: {self.current_developer*100}%, "
                      f"Liquidity: {self.current_liquidity*100}%")
    
    def serialize_state(self) -> Dict[str, Any]:
        """Serialize current state for persistence"""
        return {
            'current_distribution': {
                'burn': str(self.current_burn),
                'developer': str(self.current_developer),
                'liquidity': str(self.current_liquidity)
            },
            'initial_distribution': {
                'burn': str(self.initial_burn),
                'developer': str(self.initial_developer),
                'liquidity': str(self.initial_liquidity)
            },
            'redistribution_amount': str(self.redistribution_amount),
            'redistribution_history': [event.to_dict() for event in self.redistribution_history],
            'version': '1.0'
        }
    
    def deserialize_state(self, state_data: Dict[str, Any]) -> bool:
        """Deserialize state from persistence data"""
        try:
            # Validate version compatibility
            version = state_data.get('version', '1.0')
            if version != '1.0':
                logger.warning(f"⚠️ State version mismatch: {version} vs 1.0")
            
            # Restore current distribution
            current_dist = state_data['current_distribution']
            self.current_burn = Decimal(current_dist['burn'])
            self.current_developer = Decimal(current_dist['developer'])
            self.current_liquidity = Decimal(current_dist['liquidity'])
            
            # Validate restored percentages
            if not self.validate_percentages():
                logger.error("❌ Invalid percentages in restored state")
                return False
            
            # Restore initial distribution
            initial_dist = state_data['initial_distribution']
            self.initial_burn = Decimal(initial_dist['burn'])
            self.initial_developer = Decimal(initial_dist['developer'])
            self.initial_liquidity = Decimal(initial_dist['liquidity'])
            
            # Restore redistribution amount
            self.redistribution_amount = Decimal(state_data['redistribution_amount'])
            
            # Restore redistribution history
            self.redistribution_history.clear()
            for event_data in state_data['redistribution_history']:
                # Reconstruct FeeDistribution objects
                old_dist = FeeDistribution(
                    burn_percentage=Decimal(event_data['old_distribution']['burn_percentage']),
                    developer_percentage=Decimal(event_data['old_distribution']['developer_percentage']),
                    liquidity_percentage=Decimal(event_data['old_distribution']['liquidity_percentage']),
                    halving_number=event_data['old_distribution']['halving_number'],
                    block_number=event_data['old_distribution']['block_number'],
                    timestamp=event_data['old_distribution']['timestamp']
                )
                
                new_dist = FeeDistribution(
                    burn_percentage=Decimal(event_data['new_distribution']['burn_percentage']),
                    developer_percentage=Decimal(event_data['new_distribution']['developer_percentage']),
                    liquidity_percentage=Decimal(event_data['new_distribution']['liquidity_percentage']),
                    halving_number=event_data['new_distribution']['halving_number'],
                    block_number=event_data['new_distribution']['block_number'],
                    timestamp=event_data['new_distribution']['timestamp']
                )
                
                # Reconstruct RedistributionEvent
                event = RedistributionEvent(
                    halving_number=event_data['halving_number'],
                    block_number=event_data['block_number'],
                    timestamp=event_data['timestamp'],
                    old_distribution=old_dist,
                    new_distribution=new_dist,
                    redistribution_amount=Decimal(event_data['redistribution_amount'])
                )
                
                self.redistribution_history.append(event)
            
            logger.info(f"✅ Fee distribution state restored: "
                       f"Burn: {self.current_burn*100}%, "
                       f"Dev: {self.current_developer*100}%, "
                       f"Pool: {self.current_liquidity*100}%, "
                       f"History: {len(self.redistribution_history)} events")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to deserialize fee distribution state: {e}")
            return False
    
    def save_state_to_file(self, filepath: str) -> bool:
        """Save current state to file"""
        try:
            import json
            state_data = self.serialize_state()
            
            with open(filepath, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.info(f"💾 Fee distribution state saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save state to file {filepath}: {e}")
            return False
    
    def load_state_from_file(self, filepath: str) -> bool:
        """Load state from file"""
        try:
            import json
            import os
            
            if not os.path.exists(filepath):
                logger.warning(f"⚠️ State file not found: {filepath}")
                return False
            
            with open(filepath, 'r') as f:
                state_data = json.load(f)
            
            success = self.deserialize_state(state_data)
            if success:
                logger.info(f"📂 Fee distribution state loaded from {filepath}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to load state from file {filepath}: {e}")
            return False
    
    def get_next_halving_info(self, current_block: int, halving_interval: int = 100000) -> Dict[str, Any]:
        """Get information about the next halving event"""
        next_halving_block = ((current_block // halving_interval) + 1) * halving_interval
        blocks_remaining = next_halving_block - current_block
        
        # Calculate what the distribution will be after next halving
        next_burn = max(Decimal('0.0'), self.current_burn - self.redistribution_amount)
        next_developer = self.current_developer + (self.redistribution_amount / 2)
        next_liquidity = self.current_liquidity + (self.redistribution_amount / 2)
        
        return {
            'current_block': current_block,
            'next_halving_block': next_halving_block,
            'blocks_remaining': blocks_remaining,
            'current_distribution': self.get_current_distribution(),
            'next_distribution': {
                'burn': str(next_burn),
                'developer': str(next_developer),
                'liquidity': str(next_liquidity)
            } if next_burn >= Decimal('0.0') else None,
            'redistribution_complete': self.current_burn <= Decimal('0.0')
        }
    
    def get_halving_timeline(self, halving_interval: int = 100000) -> List[Dict[str, Any]]:
        """Get complete timeline of all halvings and redistributions"""
        timeline = []
        
        # Add historical events
        for event in self.redistribution_history:
            timeline.append({
                'halving_number': event.halving_number,
                'block_number': event.block_number,
                'timestamp': event.timestamp,
                'type': 'completed',
                'distribution': event.new_distribution.to_dict(),
                'redistribution_amount': str(event.redistribution_amount)
            })
        
        # Add future projections if burn > 0%
        if self.current_burn > Decimal('0.0'):
            current_halving = len(self.redistribution_history)
            temp_burn = self.current_burn
            temp_dev = self.current_developer
            temp_liq = self.current_liquidity
            
            while temp_burn > Decimal('0.0') and current_halving < 20:  # Limit projections
                current_halving += 1
                next_block = current_halving * halving_interval
                
                # Calculate next distribution
                burn_reduction = min(self.redistribution_amount, temp_burn)
                temp_burn -= burn_reduction
                temp_dev += burn_reduction / 2
                temp_liq += burn_reduction / 2
                
                timeline.append({
                    'halving_number': current_halving,
                    'block_number': next_block,
                    'timestamp': None,  # Future event
                    'type': 'projected',
                    'distribution': {
                        'burn_percentage': str(temp_burn),
                        'developer_percentage': str(temp_dev),
                        'liquidity_percentage': str(temp_liq)
                    },
                    'redistribution_amount': str(burn_reduction)
                })
                
                if temp_burn <= Decimal('0.0'):
                    break
        
        return timeline
    
    def get_monitoring_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring data for dashboards"""
        current_time = time.time()
        
        return {
            'current_state': {
                'distribution': self.get_current_distribution(),
                'total_redistributions': len(self.redistribution_history),
                'burn_exhausted': self.current_burn <= Decimal('0.0'),
                'last_update': max([event.timestamp for event in self.redistribution_history]) if self.redistribution_history else None
            },
            'configuration': {
                'initial_distribution': {
                    'burn': str(self.initial_burn),
                    'developer': str(self.initial_developer),
                    'liquidity': str(self.initial_liquidity)
                },
                'redistribution_amount': str(self.redistribution_amount)
            },
            'statistics': {
                'total_burn_reduction': str(self.initial_burn - self.current_burn),
                'total_developer_increase': str(self.current_developer - self.initial_developer),
                'total_liquidity_increase': str(self.current_liquidity - self.initial_liquidity),
                'redistribution_efficiency': str((self.initial_burn - self.current_burn) / self.initial_burn * 100) if self.initial_burn > 0 else "0"
            },
            'recent_events': [
                event.to_dict() for event in self.redistribution_history[-5:]  # Last 5 events
            ],
            'timestamp': current_time
        }