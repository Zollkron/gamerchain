"""
Dynamic Quorum Manager for PlayerGold
Implements the 66% quorum rule with minimum 2 nodes

"Donde hayan dos reunidos, mi espíritu está con ellos"
"""

import logging
import math
from typing import Set, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QuorumStatus(Enum):
    """Status of quorum"""
    ACHIEVED = "achieved"
    NOT_ACHIEVED = "not_achieved"
    INSUFFICIENT_NODES = "insufficient_nodes"


@dataclass
class QuorumResult:
    """Result of quorum calculation"""
    status: QuorumStatus
    total_nodes: int
    active_nodes: int
    required_nodes: int
    quorum_percentage: float
    can_proceed: bool
    message: str


class QuorumManager:
    """
    Manages dynamic quorum calculation for consensus.
    
    Implements the principle: "Donde hayan dos reunidos, mi espíritu está con ellos"
    - Minimum 2 nodes required for network operation
    - 66% (2/3) quorum of active nodes
    - Scales dynamically with network size
    """
    
    def __init__(self, 
                 quorum_percentage: float = 0.66,
                 min_nodes: int = 2):
        """
        Initialize Quorum Manager.
        
        Args:
            quorum_percentage: Percentage of nodes required for quorum (default 66%)
            min_nodes: Minimum nodes required for network operation (default 2)
        """
        if quorum_percentage <= 0 or quorum_percentage > 1:
            raise ValueError("Quorum percentage must be between 0 and 1")
        
        if min_nodes < 2:
            raise ValueError("Minimum nodes must be at least 2")
        
        self.quorum_percentage = quorum_percentage
        self.min_nodes = min_nodes
        
        logger.info(
            f"Quorum Manager initialized: {quorum_percentage*100:.1f}% quorum, "
            f"min {min_nodes} nodes"
        )
    
    def calculate_required_nodes(self, total_nodes: int) -> int:
        """
        Calculate number of nodes required for quorum.
        
        Args:
            total_nodes: Total number of nodes in network
            
        Returns:
            int: Number of nodes required for quorum
        """
        if total_nodes < self.min_nodes:
            return total_nodes  # Need all nodes if below minimum
        
        # Calculate 66% and round up
        required = math.ceil(total_nodes * self.quorum_percentage)
        
        # Ensure at least minimum nodes
        required = max(required, self.min_nodes)
        
        # Cannot require more than total nodes
        required = min(required, total_nodes)
        
        return required
    
    def check_quorum(self, 
                     active_nodes: Set[str], 
                     all_nodes: Set[str]) -> QuorumResult:
        """
        Check if quorum is achieved.
        
        Args:
            active_nodes: Set of currently active node IDs
            all_nodes: Set of all known node IDs
            
        Returns:
            QuorumResult with status and details
        """
        total_nodes = len(all_nodes)
        active_count = len(active_nodes)
        
        # Check minimum nodes requirement
        if total_nodes < self.min_nodes:
            return QuorumResult(
                status=QuorumStatus.INSUFFICIENT_NODES,
                total_nodes=total_nodes,
                active_nodes=active_count,
                required_nodes=self.min_nodes,
                quorum_percentage=self.quorum_percentage,
                can_proceed=False,
                message=f"Insufficient nodes: {total_nodes} < {self.min_nodes} minimum required"
            )
        
        # Calculate required nodes for quorum
        required_nodes = self.calculate_required_nodes(total_nodes)
        
        # Check if quorum is achieved
        if active_count >= required_nodes:
            actual_percentage = (active_count / total_nodes) * 100
            return QuorumResult(
                status=QuorumStatus.ACHIEVED,
                total_nodes=total_nodes,
                active_nodes=active_count,
                required_nodes=required_nodes,
                quorum_percentage=self.quorum_percentage,
                can_proceed=True,
                message=f"Quorum achieved: {active_count}/{total_nodes} nodes ({actual_percentage:.1f}%)"
            )
        else:
            actual_percentage = (active_count / total_nodes) * 100
            return QuorumResult(
                status=QuorumStatus.NOT_ACHIEVED,
                total_nodes=total_nodes,
                active_nodes=active_count,
                required_nodes=required_nodes,
                quorum_percentage=self.quorum_percentage,
                can_proceed=False,
                message=f"Quorum not achieved: {active_count}/{required_nodes} required ({actual_percentage:.1f}%)"
            )
    
    def can_add_block(self, 
                      validating_nodes: Set[str], 
                      all_nodes: Set[str]) -> bool:
        """
        Check if enough nodes have validated to add a block.
        
        Args:
            validating_nodes: Set of nodes that have validated the block
            all_nodes: Set of all known nodes
            
        Returns:
            bool: True if block can be added
        """
        result = self.check_quorum(validating_nodes, all_nodes)
        return result.can_proceed
    
    def get_quorum_info(self, total_nodes: int) -> dict:
        """
        Get quorum information for a given number of nodes.
        
        Args:
            total_nodes: Number of nodes to calculate for
            
        Returns:
            dict: Quorum information
        """
        required = self.calculate_required_nodes(total_nodes)
        actual_percentage = (required / total_nodes * 100) if total_nodes > 0 else 0
        
        return {
            'total_nodes': total_nodes,
            'required_nodes': required,
            'quorum_percentage_target': self.quorum_percentage * 100,
            'actual_percentage': actual_percentage,
            'min_nodes': self.min_nodes,
            'can_operate': total_nodes >= self.min_nodes
        }
    
    def get_quorum_table(self, max_nodes: int = 20) -> List[dict]:
        """
        Generate a quorum table showing requirements for different node counts.
        
        Args:
            max_nodes: Maximum number of nodes to show
            
        Returns:
            List of quorum information for each node count
        """
        table = []
        
        for n in range(1, max_nodes + 1):
            info = self.get_quorum_info(n)
            table.append(info)
        
        return table
    
    def validate_consensus(self, 
                          votes: dict[str, bool], 
                          all_nodes: Set[str]) -> tuple[bool, str]:
        """
        Validate if consensus is reached based on votes.
        
        Args:
            votes: Dictionary mapping node_id to vote (True/False)
            all_nodes: Set of all known nodes
            
        Returns:
            tuple: (consensus_reached, message)
        """
        # Get nodes that voted yes
        yes_votes = {node_id for node_id, vote in votes.items() if vote}
        
        # Check quorum
        result = self.check_quorum(yes_votes, all_nodes)
        
        if not result.can_proceed:
            return False, result.message
        
        # Quorum achieved with yes votes
        return True, f"Consensus reached: {len(yes_votes)}/{len(all_nodes)} nodes agreed"
    
    def get_missing_nodes_count(self, 
                                active_nodes: Set[str], 
                                all_nodes: Set[str]) -> int:
        """
        Get number of additional nodes needed to reach quorum.
        
        Args:
            active_nodes: Currently active nodes
            all_nodes: All known nodes
            
        Returns:
            int: Number of additional nodes needed (0 if quorum already achieved)
        """
        result = self.check_quorum(active_nodes, all_nodes)
        
        if result.can_proceed:
            return 0
        
        return result.required_nodes - result.active_nodes
    
    def log_quorum_status(self, active_nodes: Set[str], all_nodes: Set[str]):
        """
        Log current quorum status.
        
        Args:
            active_nodes: Currently active nodes
            all_nodes: All known nodes
        """
        result = self.check_quorum(active_nodes, all_nodes)
        
        if result.can_proceed:
            logger.info(f"✓ {result.message}")
        else:
            logger.warning(f"✗ {result.message}")
