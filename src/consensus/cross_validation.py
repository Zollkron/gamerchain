"""
Cross-Validation System for AI Nodes

This module implements cross-validation between AI nodes to ensure
consensus integrity and detect non-AI behavior.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import statistics
from collections import defaultdict

from src.consensus.challenge_generator import Challenge, Solution
from src.consensus.challenge_processor import ChallengeProcessor, AISignatureManager


class ValidationResult(Enum):
    """Result of cross-validation"""
    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"
    TIMEOUT = "timeout"
    ERROR = "error"


class BehaviorFlag(Enum):
    """Flags for detecting non-AI behavior"""
    TIMING_ANOMALY = "timing_anomaly"
    SOLUTION_PATTERN = "solution_pattern"
    SIGNATURE_INVALID = "signature_invalid"
    CROSS_VALIDATION_FAILURE = "cross_validation_failure"
    REPEATED_ERRORS = "repeated_errors"


@dataclass
class ValidationEntry:
    """Single validation entry from a validator node"""
    validator_node_id: str
    validation_result: ValidationResult
    confidence_score: float  # 0.0 to 1.0
    validation_time_ms: float
    validator_signature: str
    timestamp: float
    notes: Optional[str] = None


@dataclass
class CrossValidationResult:
    """Result of cross-validation process"""
    challenge_id: str
    solution_node_id: str
    validations: List[ValidationEntry]
    consensus_result: ValidationResult
    consensus_confidence: float
    behavior_flags: List[BehaviorFlag] = field(default_factory=list)
    arbitration_required: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class NodeReputationEntry:
    """Reputation tracking for a node"""
    node_id: str
    successful_validations: int = 0
    failed_validations: int = 0
    suspicious_behavior_count: int = 0
    last_activity: float = field(default_factory=time.time)
    behavior_flags: List[BehaviorFlag] = field(default_factory=list)
    penalty_score: float = 0.0
    
    @property
    def reputation_score(self) -> float:
        """Calculate overall reputation score (0.0 to 1.0)"""
        total_validations = self.successful_validations + self.failed_validations
        if total_validations == 0:
            return 0.5  # Neutral for new nodes
        
        success_rate = self.successful_validations / total_validations
        penalty_factor = max(0.0, 1.0 - (self.penalty_score / 100.0))
        
        return success_rate * penalty_factor


class CrossValidator:
    """Manages cross-validation between AI nodes"""
    
    def __init__(self, min_validators: int = 3, consensus_threshold: float = 0.67):
        self.min_validators = min_validators
        self.consensus_threshold = consensus_threshold
        self.node_reputations: Dict[str, NodeReputationEntry] = {}
        self.validation_history: List[CrossValidationResult] = []
        self.active_validators: Set[str] = set()
        
    def register_validator(self, node_id: str) -> bool:
        """Register a node as an active validator"""
        if node_id not in self.node_reputations:
            self.node_reputations[node_id] = NodeReputationEntry(node_id=node_id)
        
        self.active_validators.add(node_id)
        return True
    
    def unregister_validator(self, node_id: str) -> bool:
        """Remove a node from active validators"""
        self.active_validators.discard(node_id)
        return True
    
    def select_validators(self, solution_node_id: str, exclude_nodes: Optional[Set[str]] = None) -> List[str]:
        """Select validators for cross-validation, excluding the solution node"""
        exclude_nodes = exclude_nodes or set()
        exclude_nodes.add(solution_node_id)
        
        # Get available validators
        available_validators = [
            node_id for node_id in self.active_validators 
            if node_id not in exclude_nodes
        ]
        
        # Sort by reputation score (highest first)
        available_validators.sort(
            key=lambda node_id: self.node_reputations.get(node_id, NodeReputationEntry(node_id)).reputation_score,
            reverse=True
        )
        
        # Select minimum required validators, or all available if less than minimum
        selected_count = min(len(available_validators), max(self.min_validators, 5))
        return available_validators[:selected_count]
    
    def validate_solution(self, challenge: Challenge, solution: Solution, 
                         validator_processors: Dict[str, ChallengeProcessor]) -> CrossValidationResult:
        """Perform cross-validation of a solution"""
        
        # Select validators
        solution_node_id = self._extract_node_id(solution.node_signature)
        selected_validators = self.select_validators(solution_node_id)
        
        if len(selected_validators) < self.min_validators:
            return CrossValidationResult(
                challenge_id=challenge.challenge_id,
                solution_node_id=self._extract_node_id(solution.node_signature),
                validations=[],
                consensus_result=ValidationResult.ERROR,
                consensus_confidence=0.0,
                behavior_flags=[BehaviorFlag.CROSS_VALIDATION_FAILURE]
            )
        
        # Collect validations from selected validators
        validations = []
        for validator_id in selected_validators:
            if validator_id in validator_processors:
                validation = self._perform_single_validation(
                    challenge, solution, validator_id, validator_processors[validator_id]
                )
                validations.append(validation)
        
        # Analyze validations and determine consensus
        result = self._analyze_validations(challenge.challenge_id, solution, validations)
        
        # Update node reputations based on results
        self._update_reputations(result)
        
        # Store in history
        self.validation_history.append(result)
        
        return result
    
    def _perform_single_validation(self, challenge: Challenge, solution: Solution,
                                 validator_id: str, validator_processor: ChallengeProcessor) -> ValidationEntry:
        """Perform validation by a single validator node"""
        start_time = time.time()
        
        try:
            # Verify signature first
            if not AISignatureManager.verify_signature_static(
                solution.solution_data, solution.node_signature
            ):
                return ValidationEntry(
                    validator_node_id=validator_id,
                    validation_result=ValidationResult.INVALID,
                    confidence_score=1.0,
                    validation_time_ms=(time.time() - start_time) * 1000,
                    validator_signature=self._create_validator_signature(validator_processor, "signature_invalid"),
                    timestamp=time.time(),
                    notes="Invalid signature"
                )
            
            # Check timing anomalies
            if solution.computation_time_ms > 100:
                return ValidationEntry(
                    validator_node_id=validator_id,
                    validation_result=ValidationResult.SUSPICIOUS,
                    confidence_score=0.8,
                    validation_time_ms=(time.time() - start_time) * 1000,
                    validator_signature=self._create_validator_signature(validator_processor, "timing_anomaly"),
                    timestamp=time.time(),
                    notes=f"Computation time {solution.computation_time_ms}ms exceeds 100ms limit"
                )
            
            # Re-solve the challenge independently
            validator_result = validator_processor.process_challenge(challenge)
            
            if not validator_result.success:
                return ValidationEntry(
                    validator_node_id=validator_id,
                    validation_result=ValidationResult.ERROR,
                    confidence_score=0.0,
                    validation_time_ms=(time.time() - start_time) * 1000,
                    validator_signature=self._create_validator_signature(validator_processor, "validation_error"),
                    timestamp=time.time(),
                    notes="Validator failed to solve challenge"
                )
            
            # Compare solutions
            similarity_score = self._compare_solutions(
                solution.solution_data, 
                validator_result.solution.solution_data
            )
            
            # Determine validation result based on similarity
            if similarity_score >= 0.95:
                validation_result = ValidationResult.VALID
                confidence = similarity_score
            elif similarity_score >= 0.8:
                validation_result = ValidationResult.SUSPICIOUS
                confidence = similarity_score * 0.8
            else:
                validation_result = ValidationResult.INVALID
                confidence = 1.0 - similarity_score
            
            return ValidationEntry(
                validator_node_id=validator_id,
                validation_result=validation_result,
                confidence_score=confidence,
                validation_time_ms=(time.time() - start_time) * 1000,
                validator_signature=self._create_validator_signature(
                    validator_processor, 
                    f"similarity_{similarity_score:.3f}"
                ),
                timestamp=time.time(),
                notes=f"Solution similarity: {similarity_score:.3f}"
            )
            
        except Exception as e:
            return ValidationEntry(
                validator_node_id=validator_id,
                validation_result=ValidationResult.ERROR,
                confidence_score=0.0,
                validation_time_ms=(time.time() - start_time) * 1000,
                validator_signature=self._create_validator_signature(validator_processor, "exception"),
                timestamp=time.time(),
                notes=f"Validation error: {str(e)}"
            )
    
    def _compare_solutions(self, solution1: Dict, solution2: Dict) -> float:
        """Compare two solutions and return similarity score (0.0 to 1.0)"""
        try:
            # For matrix operations
            if 'result' in solution1 and 'result' in solution2:
                import numpy as np
                arr1 = np.array(solution1['result'])
                arr2 = np.array(solution2['result'])
                
                if arr1.shape != arr2.shape:
                    return 0.0
                
                # Calculate relative error
                diff = np.abs(arr1 - arr2)
                max_val = np.maximum(np.abs(arr1), np.abs(arr2))
                max_val[max_val == 0] = 1  # Avoid division by zero
                relative_error = np.mean(diff / max_val)
                
                return max(0.0, 1.0 - relative_error)
            
            # For pattern recognition
            elif 'predicted_values' in solution1 and 'predicted_values' in solution2:
                pred1 = solution1['predicted_values']
                pred2 = solution2['predicted_values']
                
                if len(pred1) != len(pred2):
                    return 0.0
                
                # Calculate similarity for predictions
                total_error = 0.0
                for p1, p2 in zip(pred1, pred2):
                    if abs(p1) + abs(p2) == 0:
                        continue
                    relative_error = abs(p1 - p2) / (abs(p1) + abs(p2))
                    total_error += relative_error
                
                avg_error = total_error / len(pred1) if pred1 else 0
                return max(0.0, 1.0 - avg_error)
            
            # For optimization
            elif 'optimized_point' in solution1 and 'optimized_point' in solution2:
                import numpy as np
                point1 = np.array(solution1['optimized_point'])
                point2 = np.array(solution2['optimized_point'])
                
                if point1.shape != point2.shape:
                    return 0.0
                
                # Calculate distance similarity
                distance = np.linalg.norm(point1 - point2)
                max_distance = np.linalg.norm(point1) + np.linalg.norm(point2)
                
                if max_distance == 0:
                    return 1.0
                
                similarity = 1.0 - (distance / max_distance)
                return max(0.0, similarity)
            
            # Fallback: JSON comparison
            else:
                json1 = json.dumps(solution1, sort_keys=True)
                json2 = json.dumps(solution2, sort_keys=True)
                return 1.0 if json1 == json2 else 0.0
                
        except Exception:
            return 0.0
    
    def _analyze_validations(self, challenge_id: str, solution: Solution, 
                           validations: List[ValidationEntry]) -> CrossValidationResult:
        """Analyze validation results and determine consensus"""
        
        if not validations:
            return CrossValidationResult(
                challenge_id=challenge_id,
                solution_node_id=self._extract_node_id(solution.node_signature),
                validations=[],
                consensus_result=ValidationResult.ERROR,
                consensus_confidence=0.0,
                behavior_flags=[BehaviorFlag.CROSS_VALIDATION_FAILURE]
            )
        
        # Count validation results
        result_counts = defaultdict(int)
        confidence_scores = defaultdict(list)
        
        for validation in validations:
            result_counts[validation.validation_result] += 1
            confidence_scores[validation.validation_result].append(validation.confidence_score)
        
        # Determine consensus
        total_validations = len(validations)
        valid_count = result_counts[ValidationResult.VALID]
        invalid_count = result_counts[ValidationResult.INVALID]
        suspicious_count = result_counts[ValidationResult.SUSPICIOUS]
        
        # Calculate consensus
        valid_ratio = valid_count / total_validations
        invalid_ratio = invalid_count / total_validations
        
        behavior_flags = []
        
        if valid_ratio >= self.consensus_threshold:
            consensus_result = ValidationResult.VALID
            consensus_confidence = statistics.mean(confidence_scores[ValidationResult.VALID])
        elif invalid_ratio >= self.consensus_threshold:
            consensus_result = ValidationResult.INVALID
            consensus_confidence = statistics.mean(confidence_scores[ValidationResult.INVALID])
            behavior_flags.append(BehaviorFlag.CROSS_VALIDATION_FAILURE)
        else:
            consensus_result = ValidationResult.SUSPICIOUS
            all_confidences = []
            for conf_list in confidence_scores.values():
                all_confidences.extend(conf_list)
            consensus_confidence = statistics.mean(all_confidences) if all_confidences else 0.0
            behavior_flags.append(BehaviorFlag.SOLUTION_PATTERN)
        
        # Check for timing anomalies
        if solution.computation_time_ms > 100:
            behavior_flags.append(BehaviorFlag.TIMING_ANOMALY)
        
        # Check if arbitration is needed
        arbitration_required = (
            suspicious_count > 0 or 
            (valid_count > 0 and invalid_count > 0) or
            consensus_confidence < 0.8
        )
        
        return CrossValidationResult(
            challenge_id=challenge_id,
            solution_node_id=self._extract_node_id(solution.node_signature),
            validations=validations,
            consensus_result=consensus_result,
            consensus_confidence=consensus_confidence,
            behavior_flags=behavior_flags,
            arbitration_required=arbitration_required
        )
    
    def _update_reputations(self, result: CrossValidationResult):
        """Update node reputations based on validation results"""
        solution_node_id = result.solution_node_id
        
        # Update solution node reputation
        if solution_node_id not in self.node_reputations:
            self.node_reputations[solution_node_id] = NodeReputationEntry(node_id=solution_node_id)
        
        solution_reputation = self.node_reputations[solution_node_id]
        
        if result.consensus_result == ValidationResult.VALID:
            solution_reputation.successful_validations += 1
        elif result.consensus_result == ValidationResult.INVALID:
            solution_reputation.failed_validations += 1
            solution_reputation.penalty_score += 10.0
        elif result.consensus_result == ValidationResult.SUSPICIOUS:
            solution_reputation.suspicious_behavior_count += 1
            solution_reputation.penalty_score += 5.0
        
        # Add behavior flags
        for flag in result.behavior_flags:
            if flag not in solution_reputation.behavior_flags:
                solution_reputation.behavior_flags.append(flag)
        
        solution_reputation.last_activity = time.time()
        
        # Update validator reputations
        for validation in result.validations:
            validator_id = validation.validator_node_id
            
            if validator_id not in self.node_reputations:
                self.node_reputations[validator_id] = NodeReputationEntry(node_id=validator_id)
            
            validator_reputation = self.node_reputations[validator_id]
            
            # Reward validators for participating
            if validation.validation_result != ValidationResult.ERROR:
                validator_reputation.successful_validations += 1
            else:
                validator_reputation.failed_validations += 1
            
            validator_reputation.last_activity = time.time()
    
    def _extract_node_id(self, signature_json: str) -> str:
        """Extract node ID from signature"""
        try:
            signature_data = json.loads(signature_json)
            return signature_data.get('node_id', 'unknown')
        except:
            return 'unknown'
    
    def _create_validator_signature(self, processor: ChallengeProcessor, validation_data: str) -> str:
        """Create signature for validation result"""
        return processor.signature_manager.sign_solution({
            'validation_data': validation_data,
            'timestamp': time.time()
        })
    
    def get_node_reputation(self, node_id: str) -> Optional[NodeReputationEntry]:
        """Get reputation information for a node"""
        return self.node_reputations.get(node_id)
    
    def apply_penalty(self, node_id: str, penalty_type: BehaviorFlag, penalty_score: float = 10.0):
        """Apply penalty to a node for detected anomalies"""
        if node_id not in self.node_reputations:
            self.node_reputations[node_id] = NodeReputationEntry(node_id=node_id)
        
        reputation = self.node_reputations[node_id]
        reputation.penalty_score += penalty_score
        
        if penalty_type not in reputation.behavior_flags:
            reputation.behavior_flags.append(penalty_type)
        
        # Severe penalties may result in temporary exclusion
        if penalty_score >= 50.0:
            self.unregister_validator(node_id)
    
    def get_validation_stats(self) -> Dict:
        """Get statistics about cross-validation performance"""
        if not self.validation_history:
            return {}
        
        total_validations = len(self.validation_history)
        valid_count = sum(1 for r in self.validation_history if r.consensus_result == ValidationResult.VALID)
        invalid_count = sum(1 for r in self.validation_history if r.consensus_result == ValidationResult.INVALID)
        suspicious_count = sum(1 for r in self.validation_history if r.consensus_result == ValidationResult.SUSPICIOUS)
        
        avg_confidence = statistics.mean([r.consensus_confidence for r in self.validation_history])
        
        return {
            'total_validations': total_validations,
            'valid_percentage': (valid_count / total_validations) * 100,
            'invalid_percentage': (invalid_count / total_validations) * 100,
            'suspicious_percentage': (suspicious_count / total_validations) * 100,
            'average_confidence': avg_confidence,
            'active_validators': len(self.active_validators),
            'total_nodes': len(self.node_reputations)
        }