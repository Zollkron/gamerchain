"""
Node reputation engine for AI nodes in the GamerChain network.

This module handles reputation tracking, scoring, and penalty management
for AI nodes participating in the PoAIP consensus.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from pathlib import Path

from .reputation_types import (
    ReputationEvent,
    ReputationScore,
    NodeBehaviorType,
    PenaltySeverity,
    ReputationConfig
)


class NodeReputationEngine:
    """
    Manages reputation for AI nodes in the network.
    
    Handles:
    - Reputation scoring based on validation performance
    - Penalty application for various misbehaviors
    - Historical tracking of node behavior
    - Participation rate monitoring
    """
    
    def __init__(self, data_dir: str = "data/reputation"):
        """
        Initialize the node reputation engine.
        
        Args:
            data_dir: Directory to store reputation data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # In-memory reputation data
        self.node_scores: Dict[str, ReputationScore] = {}
        self.reputation_events: Dict[str, List[ReputationEvent]] = {}
        
        # Load existing data
        self._load_reputation_data()
        
    def _load_reputation_data(self):
        """Load reputation data from persistent storage."""
        try:
            scores_file = self.data_dir / "node_scores.json"
            events_file = self.data_dir / "reputation_events.json"
            
            if scores_file.exists():
                with open(scores_file, 'r') as f:
                    data = json.load(f)
                    for node_id, score_data in data.items():
                        self.node_scores[node_id] = ReputationScore(
                            node_id=score_data['node_id'],
                            current_score=score_data['current_score'],
                            total_validations=score_data['total_validations'],
                            successful_validations=score_data['successful_validations'],
                            failed_validations=score_data['failed_validations'],
                            penalties_applied=score_data['penalties_applied'],
                            last_activity=datetime.fromisoformat(score_data['last_activity']),
                            reputation_history=score_data['reputation_history'],
                            participation_rate=score_data['participation_rate']
                        )
            
            if events_file.exists():
                with open(events_file, 'r') as f:
                    data = json.load(f)
                    for node_id, events_data in data.items():
                        self.reputation_events[node_id] = [
                            ReputationEvent(
                                node_id=event['node_id'],
                                event_type=NodeBehaviorType(event['event_type']),
                                timestamp=datetime.fromisoformat(event['timestamp']),
                                severity=PenaltySeverity(event['severity']),
                                details=event.get('details'),
                                block_height=event.get('block_height')
                            )
                            for event in events_data
                        ]
                        
        except Exception as e:
            self.logger.error(f"Error loading reputation data: {e}")
    
    def _save_reputation_data(self):
        """Save reputation data to persistent storage."""
        try:
            # Save node scores
            scores_data = {}
            for node_id, score in self.node_scores.items():
                scores_data[node_id] = {
                    'node_id': score.node_id,
                    'current_score': score.current_score,
                    'total_validations': score.total_validations,
                    'successful_validations': score.successful_validations,
                    'failed_validations': score.failed_validations,
                    'penalties_applied': score.penalties_applied,
                    'last_activity': score.last_activity.isoformat(),
                    'reputation_history': score.reputation_history,
                    'participation_rate': score.participation_rate
                }
            
            with open(self.data_dir / "node_scores.json", 'w') as f:
                json.dump(scores_data, f, indent=2)
            
            # Save reputation events
            events_data = {}
            for node_id, events in self.reputation_events.items():
                events_data[node_id] = [
                    {
                        'node_id': event.node_id,
                        'event_type': event.event_type.value,
                        'timestamp': event.timestamp.isoformat(),
                        'severity': event.severity.value,
                        'details': event.details,
                        'block_height': event.block_height
                    }
                    for event in events
                ]
            
            with open(self.data_dir / "reputation_events.json", 'w') as f:
                json.dump(events_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving reputation data: {e}")
    
    def register_node(self, node_id: str) -> ReputationScore:
        """
        Register a new AI node with initial reputation.
        
        Args:
            node_id: Unique identifier for the AI node
            
        Returns:
            Initial reputation score for the node
        """
        if node_id not in self.node_scores:
            self.node_scores[node_id] = ReputationScore(
                node_id=node_id,
                current_score=ReputationConfig.INITIAL_NODE_REPUTATION,
                total_validations=0,
                successful_validations=0,
                failed_validations=0,
                penalties_applied=0,
                last_activity=datetime.now(),
                reputation_history=[],
                participation_rate=1.0
            )
            self.reputation_events[node_id] = []
            
            self.logger.info(f"Registered new AI node: {node_id}")
            self._save_reputation_data()
        
        return self.node_scores[node_id]
    
    def record_successful_validation(self, node_id: str, block_height: Optional[int] = None):
        """
        Record a successful validation by an AI node.
        
        Args:
            node_id: ID of the validating node
            block_height: Height of the validated block
        """
        if node_id not in self.node_scores:
            self.register_node(node_id)
        
        score = self.node_scores[node_id]
        
        # Update validation counts
        score.total_validations += 1
        score.successful_validations += 1
        score.last_activity = datetime.now()
        
        # Apply reputation reward
        old_score = score.current_score
        score.current_score = min(
            score.current_score + ReputationConfig.SUCCESSFUL_VALIDATION_REWARD,
            ReputationConfig.MAX_REPUTATION
        )
        
        # Record the event
        event = ReputationEvent(
            node_id=node_id,
            event_type=NodeBehaviorType.SUCCESSFUL_VALIDATION,
            timestamp=datetime.now(),
            severity=PenaltySeverity.NONE,
            block_height=block_height
        )
        
        self._record_event(event)
        self._update_reputation_history(node_id, old_score, score.current_score, "successful_validation")
        
        self.logger.debug(f"Node {node_id} successful validation. Score: {old_score} -> {score.current_score}")
    
    def apply_penalty(self, node_id: str, behavior_type: NodeBehaviorType, 
                     severity: PenaltySeverity, details: Optional[Dict] = None,
                     block_height: Optional[int] = None):
        """
        Apply a reputation penalty to an AI node.
        
        Args:
            node_id: ID of the penalized node
            behavior_type: Type of misbehavior
            severity: Severity of the penalty
            details: Additional details about the incident
            block_height: Block height where incident occurred
        """
        if node_id not in self.node_scores:
            self.register_node(node_id)
        
        score = self.node_scores[node_id]
        
        # Update failure counts for validation-related penalties
        if behavior_type in [NodeBehaviorType.INVALID_SOLUTION, 
                           NodeBehaviorType.CHALLENGE_TIMEOUT,
                           NodeBehaviorType.CROSS_VALIDATION_FAILURE]:
            score.total_validations += 1
            score.failed_validations += 1
        
        # Apply penalty based on severity
        penalty_map = {
            PenaltySeverity.LIGHT: ReputationConfig.LIGHT_PENALTY,
            PenaltySeverity.MODERATE: ReputationConfig.MODERATE_PENALTY,
            PenaltySeverity.SEVERE: ReputationConfig.SEVERE_PENALTY,
            PenaltySeverity.CRITICAL: ReputationConfig.CRITICAL_PENALTY
        }
        
        penalty = penalty_map.get(severity, 0.0)
        old_score = score.current_score
        
        score.current_score = max(
            score.current_score + penalty,  # penalty is negative
            ReputationConfig.MIN_REPUTATION
        )
        
        score.penalties_applied += 1
        score.last_activity = datetime.now()
        
        # Record the event
        event = ReputationEvent(
            node_id=node_id,
            event_type=behavior_type,
            timestamp=datetime.now(),
            severity=severity,
            details=details,
            block_height=block_height
        )
        
        self._record_event(event)
        self._update_reputation_history(node_id, old_score, score.current_score, 
                                      f"penalty_{severity.value}")
        
        self.logger.warning(f"Applied {severity.value} penalty to node {node_id} for {behavior_type.value}. "
                          f"Score: {old_score} -> {score.current_score}")
    
    def update_participation_rate(self, node_id: str, participation_rate: float):
        """
        Update the participation rate for a node.
        
        Args:
            node_id: ID of the node
            participation_rate: Participation rate (0.0 to 1.0)
        """
        if node_id not in self.node_scores:
            self.register_node(node_id)
        
        score = self.node_scores[node_id]
        old_rate = score.participation_rate
        score.participation_rate = max(0.0, min(1.0, participation_rate))
        
        # Apply penalty for low participation
        if score.participation_rate < ReputationConfig.MIN_PARTICIPATION_RATE:
            self.apply_penalty(
                node_id,
                NodeBehaviorType.NODE_OFFLINE,
                PenaltySeverity.LIGHT,
                {"participation_rate": score.participation_rate}
            )
        
        self.logger.debug(f"Node {node_id} participation rate: {old_rate} -> {score.participation_rate}")
    
    def get_node_reputation(self, node_id: str) -> Optional[ReputationScore]:
        """
        Get the current reputation score for a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Reputation score or None if node not found
        """
        return self.node_scores.get(node_id)
    
    def get_top_nodes(self, limit: int = 10) -> List[ReputationScore]:
        """
        Get the top-rated nodes by reputation score.
        
        Args:
            limit: Maximum number of nodes to return
            
        Returns:
            List of top reputation scores
        """
        sorted_scores = sorted(
            self.node_scores.values(),
            key=lambda x: (x.current_score, x.reliability_score),
            reverse=True
        )
        return sorted_scores[:limit]
    
    def get_node_history(self, node_id: str, limit: int = 100) -> List[ReputationEvent]:
        """
        Get the reputation event history for a node.
        
        Args:
            node_id: ID of the node
            limit: Maximum number of events to return
            
        Returns:
            List of reputation events
        """
        events = self.reputation_events.get(node_id, [])
        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def is_node_eligible(self, node_id: str, min_score: float = 50.0) -> bool:
        """
        Check if a node is eligible for consensus participation.
        
        Args:
            node_id: ID of the node
            min_score: Minimum reputation score required
            
        Returns:
            True if node is eligible, False otherwise
        """
        score = self.get_node_reputation(node_id)
        if not score:
            return False
        
        return (score.current_score >= min_score and 
                score.participation_rate >= ReputationConfig.MIN_PARTICIPATION_RATE)
    
    def _record_event(self, event: ReputationEvent):
        """Record a reputation event."""
        if event.node_id not in self.reputation_events:
            self.reputation_events[event.node_id] = []
        
        self.reputation_events[event.node_id].append(event)
        
        # Cleanup old events
        self._cleanup_old_events(event.node_id)
        
        # Save data periodically
        self._save_reputation_data()
    
    def _update_reputation_history(self, node_id: str, old_score: float, 
                                 new_score: float, reason: str):
        """Update the reputation history for a node."""
        score = self.node_scores[node_id]
        
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'old_score': old_score,
            'new_score': new_score,
            'change': new_score - old_score,
            'reason': reason
        }
        
        score.reputation_history.append(history_entry)
        
        # Keep only recent history
        if len(score.reputation_history) > ReputationConfig.MAX_HISTORY_ENTRIES:
            score.reputation_history = score.reputation_history[-ReputationConfig.MAX_HISTORY_ENTRIES:]
    
    def _cleanup_old_events(self, node_id: str):
        """Clean up old reputation events."""
        if node_id not in self.reputation_events:
            return
        
        cutoff_date = datetime.now() - timedelta(days=ReputationConfig.HISTORY_CLEANUP_DAYS)
        
        self.reputation_events[node_id] = [
            event for event in self.reputation_events[node_id]
            if event.timestamp > cutoff_date
        ]
    
    def get_network_stats(self) -> Dict:
        """
        Get overall network reputation statistics.
        
        Returns:
            Dictionary with network reputation metrics
        """
        if not self.node_scores:
            return {
                'total_nodes': 0,
                'average_reputation': 0.0,
                'eligible_nodes': 0,
                'total_validations': 0
            }
        
        scores = list(self.node_scores.values())
        
        return {
            'total_nodes': len(scores),
            'average_reputation': sum(s.current_score for s in scores) / len(scores),
            'eligible_nodes': sum(1 for s in scores if self.is_node_eligible(s.node_id)),
            'total_validations': sum(s.total_validations for s in scores),
            'average_success_rate': sum(s.success_rate for s in scores) / len(scores),
            'average_participation': sum(s.participation_rate for s in scores) / len(scores)
        }