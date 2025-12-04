"""
Tests for Cross-Validation System

Verifies that cross-validation between AI nodes works correctly
and detects non-AI behavior and anomalies.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch

from src.consensus.challenge_generator import ChallengeGenerator, ChallengeType
from src.consensus.challenge_processor import ChallengeProcessor, MockAIModel
from src.consensus.cross_validation import (
    CrossValidator,
    ValidationResult,
    BehaviorFlag,
    ValidationEntry,
    CrossValidationResult,
    NodeReputationEntry
)


class TestCrossValidator:
    """Test the main cross-validation functionality"""
    
    def setup_method(self):
        self.cross_validator = CrossValidator(min_validators=3, consensus_threshold=0.67)
        self.challenge_generator = ChallengeGenerator()
        
        # Create test processors
        self.processors = {}
        for i in range(5):
            node_id = f"test_node_{i:03d}"
            processor = ChallengeProcessor(node_id, MockAIModel())
            self.processors[node_id] = processor
            self.cross_validator.register_validator(node_id)
    
    def test_validator_registration(self):
        """Test validator registration and unregistration"""
        new_node = "test_node_new"
        
        # Register new validator
        success = self.cross_validator.register_validator(new_node)
        assert success
        assert new_node in self.cross_validator.active_validators
        assert new_node in self.cross_validator.node_reputations
        
        # Unregister validator
        success = self.cross_validator.unregister_validator(new_node)
        assert success
        assert new_node not in self.cross_validator.active_validators
    
    def test_validator_selection(self):
        """Test validator selection for cross-validation"""
        solution_node = "test_node_000"
        
        validators = self.cross_validator.select_validators(solution_node)
        
        # Should select validators excluding the solution node
        assert solution_node not in validators
        assert len(validators) >= self.cross_validator.min_validators
        assert all(v in self.cross_validator.active_validators for v in validators)
    
    def test_validator_selection_with_reputation(self):
        """Test that validator selection considers reputation"""
        # Artificially boost reputation of one node
        self.cross_validator.node_reputations["test_node_001"].successful_validations = 100
        
        # Lower reputation of another node
        self.cross_validator.node_reputations["test_node_002"].penalty_score = 50.0
        
        validators = self.cross_validator.select_validators("test_node_000")
        
        # Higher reputation node should be selected first
        assert "test_node_001" in validators[:2]  # Should be in top selections
    
    def test_successful_cross_validation(self):
        """Test successful cross-validation with valid solution"""
        # Generate challenge and solution
        challenge = self.challenge_generator.generate_challenge(
            difficulty=1, 
            force_type=ChallengeType.MATRIX_OPERATIONS
        )
        
        # Get solution from one processor
        solution_processor = self.processors["test_node_000"]
        solution_result = solution_processor.process_challenge(challenge)
        
        assert solution_result.success
        
        # Mock the signature verification to return True for this test
        with patch('src.consensus.challenge_processor.AISignatureManager.verify_signature_static', return_value=True):
            # Perform cross-validation
            validation_result = self.cross_validator.validate_solution(
                challenge, 
                solution_result.solution, 
                self.processors
            )
        
        # With valid signatures, should get valid or suspicious result
        assert validation_result.consensus_result in [ValidationResult.VALID, ValidationResult.SUSPICIOUS]
        assert len(validation_result.validations) >= self.cross_validator.min_validators
        assert validation_result.consensus_confidence > 0.0
    
    def test_invalid_signature_detection(self):
        """Test detection of invalid signatures"""
        challenge = self.challenge_generator.generate_challenge(
            difficulty=1, 
            force_type=ChallengeType.MATRIX_OPERATIONS
        )
        
        solution_processor = self.processors["test_node_000"]
        solution_result = solution_processor.process_challenge(challenge)
        
        # Corrupt the signature
        solution_result.solution.node_signature = "invalid_signature"
        
        validation_result = self.cross_validator.validate_solution(
            challenge, 
            solution_result.solution, 
            self.processors
        )
        
        # Should detect invalid signature
        assert validation_result.consensus_result == ValidationResult.INVALID
        assert BehaviorFlag.SIGNATURE_INVALID in [
            flag for validation in validation_result.validations 
            for flag in getattr(validation, 'behavior_flags', [])
        ] or any("Invalid signature" in (v.notes or "") for v in validation_result.validations)
    
    def test_timeout_detection(self):
        """Test detection of timeout anomalies"""
        challenge = self.challenge_generator.generate_challenge(
            difficulty=1, 
            force_type=ChallengeType.MATRIX_OPERATIONS
        )
        
        solution_processor = self.processors["test_node_000"]
        solution_result = solution_processor.process_challenge(challenge)
        
        # Artificially set high computation time
        solution_result.solution.computation_time_ms = 150.0  # Over 100ms limit
        
        validation_result = self.cross_validator.validate_solution(
            challenge, 
            solution_result.solution, 
            self.processors
        )
        
        # Should detect timing anomaly
        assert BehaviorFlag.TIMING_ANOMALY in validation_result.behavior_flags
    
    def test_insufficient_validators(self):
        """Test handling when insufficient validators are available"""
        # Remove most validators
        for node_id in list(self.cross_validator.active_validators)[1:]:
            self.cross_validator.unregister_validator(node_id)
        
        challenge = self.challenge_generator.generate_challenge(
            difficulty=1, 
            force_type=ChallengeType.MATRIX_OPERATIONS
        )
        
        solution_processor = self.processors["test_node_000"]
        solution_result = solution_processor.process_challenge(challenge)
        
        validation_result = self.cross_validator.validate_solution(
            challenge, 
            solution_result.solution, 
            self.processors
        )
        
        # Should return error due to insufficient validators
        assert validation_result.consensus_result == ValidationResult.ERROR
        assert BehaviorFlag.CROSS_VALIDATION_FAILURE in validation_result.behavior_flags
    
    def test_reputation_updates(self):
        """Test that node reputations are updated correctly"""
        initial_reputation = self.cross_validator.get_node_reputation("test_node_000")
        initial_successful = initial_reputation.successful_validations if initial_reputation else 0
        
        challenge = self.challenge_generator.generate_challenge(
            difficulty=1, 
            force_type=ChallengeType.MATRIX_OPERATIONS
        )
        
        solution_processor = self.processors["test_node_000"]
        solution_result = solution_processor.process_challenge(challenge)
        
        validation_result = self.cross_validator.validate_solution(
            challenge, 
            solution_result.solution, 
            self.processors
        )
        
        # Check reputation was updated
        updated_reputation = self.cross_validator.get_node_reputation("test_node_000")
        assert updated_reputation is not None
        
        if validation_result.consensus_result == ValidationResult.VALID:
            assert updated_reputation.successful_validations > initial_successful
        
        # Check validator reputations were also updated
        for validation in validation_result.validations:
            validator_reputation = self.cross_validator.get_node_reputation(validation.validator_node_id)
            assert validator_reputation is not None
            assert validator_reputation.last_activity > 0
    
    def test_penalty_application(self):
        """Test penalty application for detected anomalies"""
        node_id = "test_node_000"
        initial_reputation = self.cross_validator.get_node_reputation(node_id)
        initial_penalty = initial_reputation.penalty_score if initial_reputation else 0.0
        
        # Apply penalty
        self.cross_validator.apply_penalty(
            node_id, 
            BehaviorFlag.TIMING_ANOMALY, 
            penalty_score=25.0
        )
        
        updated_reputation = self.cross_validator.get_node_reputation(node_id)
        assert updated_reputation.penalty_score == initial_penalty + 25.0
        assert BehaviorFlag.TIMING_ANOMALY in updated_reputation.behavior_flags
    
    def test_severe_penalty_exclusion(self):
        """Test that severe penalties result in validator exclusion"""
        node_id = "test_node_000"
        
        # Apply severe penalty
        self.cross_validator.apply_penalty(
            node_id, 
            BehaviorFlag.CROSS_VALIDATION_FAILURE, 
            penalty_score=60.0
        )
        
        # Node should be excluded from active validators
        assert node_id not in self.cross_validator.active_validators
    
    def test_arbitration_detection(self):
        """Test detection of cases requiring arbitration"""
        challenge = self.challenge_generator.generate_challenge(
            difficulty=1, 
            force_type=ChallengeType.MATRIX_OPERATIONS
        )
        
        solution_processor = self.processors["test_node_000"]
        solution_result = solution_processor.process_challenge(challenge)
        
        # Mock validators to return mixed results
        def mock_validation_side_effect(*args, **kwargs):
            validator_id = args[2] if len(args) > 2 else "unknown"
            if "001" in validator_id:
                return ValidationEntry(
                    validator_node_id=validator_id,
                    validation_result=ValidationResult.VALID,
                    confidence_score=0.9,
                    validation_time_ms=50.0,
                    validator_signature="mock_sig_1",
                    timestamp=time.time()
                )
            elif "002" in validator_id:
                return ValidationEntry(
                    validator_node_id=validator_id,
                    validation_result=ValidationResult.INVALID,
                    confidence_score=0.8,
                    validation_time_ms=45.0,
                    validator_signature="mock_sig_2",
                    timestamp=time.time()
                )
            else:
                return ValidationEntry(
                    validator_node_id=validator_id,
                    validation_result=ValidationResult.SUSPICIOUS,
                    confidence_score=0.6,
                    validation_time_ms=55.0,
                    validator_signature="mock_sig_3",
                    timestamp=time.time()
                )
        
        with patch.object(self.cross_validator, '_perform_single_validation', side_effect=mock_validation_side_effect):
            validation_result = self.cross_validator.validate_solution(
                challenge, 
                solution_result.solution, 
                self.processors
            )
            
            # Should require arbitration due to mixed results
            assert validation_result.arbitration_required


class TestNodeReputationEntry:
    """Test node reputation tracking"""
    
    def test_reputation_score_calculation(self):
        """Test reputation score calculation"""
        # New node should have neutral reputation
        new_node = NodeReputationEntry("new_node")
        assert new_node.reputation_score == 0.5
        
        # Node with successful validations
        good_node = NodeReputationEntry("good_node")
        good_node.successful_validations = 80
        good_node.failed_validations = 20
        assert good_node.reputation_score == 0.8  # 80% success rate
        
        # Node with penalties
        penalized_node = NodeReputationEntry("penalized_node")
        penalized_node.successful_validations = 80
        penalized_node.failed_validations = 20
        penalized_node.penalty_score = 50.0  # 50% penalty
        expected_score = 0.8 * 0.5  # success_rate * penalty_factor
        assert abs(penalized_node.reputation_score - expected_score) < 0.01
    
    def test_reputation_edge_cases(self):
        """Test reputation calculation edge cases"""
        # Node with no validations
        no_activity = NodeReputationEntry("no_activity")
        assert no_activity.reputation_score == 0.5
        
        # Node with extreme penalty
        extreme_penalty = NodeReputationEntry("extreme_penalty")
        extreme_penalty.successful_validations = 100
        extreme_penalty.penalty_score = 200.0  # Over 100%
        assert extreme_penalty.reputation_score == 0.0  # Should be capped at 0


class TestSolutionComparison:
    """Test solution comparison algorithms"""
    
    def setup_method(self):
        self.cross_validator = CrossValidator()
    
    def test_matrix_solution_comparison(self):
        """Test comparison of matrix solutions"""
        solution1 = {"result": [[1, 2], [3, 4]]}
        solution2 = {"result": [[1, 2], [3, 4]]}  # Identical
        solution3 = {"result": [[1, 2], [3, 5]]}  # Slightly different
        solution4 = {"result": [[10, 20], [30, 40]]}  # Very different
        
        # Identical solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution2)
        assert similarity == 1.0
        
        # Slightly different solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution3)
        assert 0.8 < similarity < 1.0
        
        # Very different solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution4)
        assert similarity < 0.5
    
    def test_pattern_solution_comparison(self):
        """Test comparison of pattern recognition solutions"""
        solution1 = {"predicted_values": [10, 12, 14, 16, 18]}
        solution2 = {"predicted_values": [10, 12, 14, 16, 18]}  # Identical
        solution3 = {"predicted_values": [10, 12, 14, 16, 19]}  # Slightly different
        solution4 = {"predicted_values": [1, 2, 3, 4, 5]}  # Very different
        
        # Identical solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution2)
        assert similarity == 1.0
        
        # Slightly different solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution3)
        assert 0.8 < similarity < 1.0
        
        # Very different solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution4)
        assert similarity < 0.5
    
    def test_optimization_solution_comparison(self):
        """Test comparison of optimization solutions"""
        solution1 = {"optimized_point": [1.0, 2.0, 3.0]}
        solution2 = {"optimized_point": [1.0, 2.0, 3.0]}  # Identical
        solution3 = {"optimized_point": [1.1, 2.1, 3.1]}  # Close
        solution4 = {"optimized_point": [10.0, 20.0, 30.0]}  # Far
        
        # Identical solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution2)
        assert similarity == 1.0
        
        # Close solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution3)
        assert 0.8 < similarity < 1.0
        
        # Far solutions
        similarity = self.cross_validator._compare_solutions(solution1, solution4)
        assert similarity < 0.5


class TestValidationStatistics:
    """Test validation statistics and reporting"""
    
    def setup_method(self):
        self.cross_validator = CrossValidator()
        
        # Add some mock validation history
        for i in range(10):
            result = CrossValidationResult(
                challenge_id=f"challenge_{i}",
                solution_node_id=f"node_{i % 3}",
                validations=[],
                consensus_result=ValidationResult.VALID if i < 7 else ValidationResult.INVALID,
                consensus_confidence=0.9 if i < 7 else 0.3
            )
            self.cross_validator.validation_history.append(result)
    
    def test_validation_statistics(self):
        """Test validation statistics calculation"""
        stats = self.cross_validator.get_validation_stats()
        
        assert stats['total_validations'] == 10
        assert stats['valid_percentage'] == 70.0  # 7 out of 10
        assert stats['invalid_percentage'] == 30.0  # 3 out of 10
        assert stats['suspicious_percentage'] == 0.0  # 0 out of 10
        assert 0.0 < stats['average_confidence'] < 1.0
    
    def test_empty_statistics(self):
        """Test statistics with no validation history"""
        empty_validator = CrossValidator()
        stats = empty_validator.get_validation_stats()
        
        assert stats == {}


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    def setup_method(self):
        self.cross_validator = CrossValidator(min_validators=3)
        self.challenge_generator = ChallengeGenerator()
        
        # Create processors with different characteristics
        self.processors = {}
        
        # Normal AI processors
        for i in range(4):
            node_id = f"normal_node_{i}"
            processor = ChallengeProcessor(node_id, MockAIModel())
            self.processors[node_id] = processor
            self.cross_validator.register_validator(node_id)
        
        # One potentially problematic processor
        problematic_node = "problematic_node"
        problematic_processor = ChallengeProcessor(problematic_node)  # No AI model
        self.processors[problematic_node] = problematic_processor
        self.cross_validator.register_validator(problematic_node)
    
    def test_network_consensus_scenario(self):
        """Test a complete network consensus scenario"""
        # Generate multiple challenges and validate them
        consensus_results = []
        
        for i in range(5):
            challenge = self.challenge_generator.generate_challenge(
                difficulty=1, 
                force_type=ChallengeType.MATRIX_OPERATIONS
            )
            
            # Get solution from a normal node
            solution_processor = self.processors["normal_node_0"]
            solution_result = solution_processor.process_challenge(challenge)
            
            if solution_result.success:
                validation_result = self.cross_validator.validate_solution(
                    challenge, 
                    solution_result.solution, 
                    self.processors
                )
                consensus_results.append(validation_result)
        
        # Most should reach valid consensus
        valid_count = sum(1 for r in consensus_results if r.consensus_result == ValidationResult.VALID)
        assert valid_count >= len(consensus_results) * 0.6  # At least 60% should be valid
        
        # Check that reputations were updated
        for node_id in self.processors.keys():
            reputation = self.cross_validator.get_node_reputation(node_id)
            assert reputation is not None
            assert reputation.last_activity > 0
    
    def test_malicious_node_detection(self):
        """Test detection and handling of malicious nodes"""
        # Simulate malicious behavior by corrupting solutions
        challenge = self.challenge_generator.generate_challenge(
            difficulty=1, 
            force_type=ChallengeType.MATRIX_OPERATIONS
        )
        
        solution_processor = self.processors["normal_node_0"]
        solution_result = solution_processor.process_challenge(challenge)
        
        # Corrupt the solution to simulate malicious behavior
        if 'result' in solution_result.solution.solution_data:
            solution_result.solution.solution_data['result'] = [[999, 999], [999, 999]]
        
        validation_result = self.cross_validator.validate_solution(
            challenge, 
            solution_result.solution, 
            self.processors
        )
        
        # Should detect the malicious solution
        assert validation_result.consensus_result in [ValidationResult.INVALID, ValidationResult.SUSPICIOUS]
        
        # Node reputation should be penalized
        reputation = self.cross_validator.get_node_reputation("normal_node_0")
        assert reputation.penalty_score > 0 or reputation.failed_validations > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])