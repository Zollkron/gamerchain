"""
Tests for Challenge Generator

Verifies that challenges are impossible for humans to solve in <100ms
and that AI nodes can solve them correctly.
"""

import pytest
import time
import numpy as np
from unittest.mock import patch, MagicMock

from src.consensus.challenge_generator import (
    ChallengeGenerator,
    ChallengeType,
    Challenge,
    Solution,
    MatrixOperationsGenerator,
    PatternRecognitionGenerator,
    OptimizationGenerator
)


class TestChallengeGenerator:
    """Test the main challenge generator"""
    
    def setup_method(self):
        self.generator = ChallengeGenerator()
    
    def test_challenge_generation(self):
        """Test basic challenge generation"""
        challenge = self.generator.generate_challenge(difficulty=1)
        
        assert isinstance(challenge, Challenge)
        assert challenge.challenge_id is not None
        assert challenge.challenge_type in ChallengeType
        assert challenge.difficulty_level == 1
        assert challenge.timeout_ms == 100
        assert challenge.timestamp > 0
    
    def test_challenge_rotation(self):
        """Test that challenge types rotate to prevent optimization"""
        challenges = []
        for _ in range(10):
            challenge = self.generator.generate_challenge(difficulty=1)
            challenges.append(challenge.challenge_type)
        
        # Should have different types (rotation)
        unique_types = set(challenges)
        assert len(unique_types) > 1, "Challenge types should rotate"
    
    def test_forced_challenge_type(self):
        """Test generating specific challenge types"""
        challenge = self.generator.generate_challenge(
            difficulty=1, 
            force_type=ChallengeType.MATRIX_OPERATIONS
        )
        
        assert challenge.challenge_type == ChallengeType.MATRIX_OPERATIONS
    
    def test_challenge_stats(self):
        """Test challenge statistics tracking"""
        # Generate some challenges
        for _ in range(5):
            self.generator.generate_challenge(difficulty=1)
        
        stats = self.generator.get_challenge_stats()
        
        assert stats['total_challenges'] == 5
        assert 'type_distribution' in stats
        assert 'last_challenge_time' in stats


class TestMatrixOperationsGenerator:
    """Test matrix operations challenge generator"""
    
    def setup_method(self):
        self.generator = MatrixOperationsGenerator()
    
    def test_matrix_challenge_generation(self):
        """Test matrix multiplication challenge generation"""
        challenge = self.generator.generate(difficulty=1, seed=42)
        
        assert challenge.challenge_type == ChallengeType.MATRIX_OPERATIONS
        assert 'matrix_a' in challenge.data
        assert 'matrix_b' in challenge.data
        assert 'size' in challenge.data
        assert challenge.expected_solution_hash is not None
    
    def test_matrix_difficulty_scaling(self):
        """Test that difficulty affects matrix size"""
        easy_challenge = self.generator.generate(difficulty=1, seed=42)
        hard_challenge = self.generator.generate(difficulty=5, seed=42)
        
        easy_size = easy_challenge.data['size']
        hard_size = hard_challenge.data['size']
        
        assert hard_size > easy_size, "Higher difficulty should create larger matrices"
    
    def test_matrix_solution_verification(self):
        """Test matrix solution verification"""
        challenge = self.generator.generate(difficulty=1, seed=42)
        
        # Calculate correct solution
        matrix_a = np.array(challenge.data['matrix_a'])
        matrix_b = np.array(challenge.data['matrix_b'])
        correct_result = np.dot(matrix_a, matrix_b)
        
        # Create correct solution
        correct_solution = Solution(
            challenge_id=challenge.challenge_id,
            solution_data={"result": correct_result.tolist()},
            computation_time_ms=50.0,
            node_signature="test_signature",
            timestamp=time.time()
        )
        
        assert self.generator.verify_solution(challenge, correct_solution)
        
        # Test incorrect solution
        incorrect_solution = Solution(
            challenge_id=challenge.challenge_id,
            solution_data={"result": [[1, 2], [3, 4]]},
            computation_time_ms=50.0,
            node_signature="test_signature",
            timestamp=time.time()
        )
        
        assert not self.generator.verify_solution(challenge, incorrect_solution)
    
    def test_human_impossibility_matrix(self):
        """Test that matrix challenges are impossible for humans in <100ms"""
        challenge = self.generator.generate(difficulty=3, seed=42)
        
        # Simulate human attempt (random guessing)
        start_time = time.time()
        
        # Human would need to multiply large matrices manually
        matrix_size = challenge.data['size']
        assert matrix_size >= 80, "Matrix should be large enough to be impossible for humans"
        
        # Even reading the matrices would take more than 100ms for humans
        matrix_elements = matrix_size * matrix_size * 2  # Two matrices
        assert matrix_elements > 1000, "Should have enough elements to be humanly impossible"


class TestPatternRecognitionGenerator:
    """Test pattern recognition challenge generator"""
    
    def setup_method(self):
        self.generator = PatternRecognitionGenerator()
    
    def test_pattern_challenge_generation(self):
        """Test pattern recognition challenge generation"""
        challenge = self.generator.generate(difficulty=1, seed=42)
        
        assert challenge.challenge_type == ChallengeType.PATTERN_RECOGNITION
        assert 'sequence' in challenge.data
        assert 'predict_count' in challenge.data
        assert len(challenge.data['sequence']) > 100
    
    def test_pattern_complexity_scaling(self):
        """Test that difficulty affects pattern complexity"""
        easy_challenge = self.generator.generate(difficulty=1, seed=42)
        hard_challenge = self.generator.generate(difficulty=5, seed=42)
        
        easy_length = len(easy_challenge.data['sequence'])
        hard_length = len(hard_challenge.data['sequence'])
        
        assert hard_length > easy_length, "Higher difficulty should create longer sequences"
    
    def test_pattern_types(self):
        """Test different pattern generation methods"""
        # Test fibonacci pattern
        fib_pattern = self.generator._generate_pattern('fibonacci', 10)
        assert fib_pattern[:5] == [1, 1, 2, 3, 5], "Fibonacci pattern should be correct"
        
        # Test prime pattern
        prime_pattern = self.generator._generate_pattern('prime', 5)
        assert prime_pattern == [2, 3, 5, 7, 11], "Prime pattern should be correct"
        
        # Test geometric pattern
        geom_pattern = self.generator._generate_pattern('geometric', 5)
        assert len(geom_pattern) == 5, "Geometric pattern should have correct length"
    
    def test_human_impossibility_pattern(self):
        """Test that pattern challenges are impossible for humans in <100ms"""
        challenge = self.generator.generate(difficulty=3, seed=42)
        
        sequence_length = len(challenge.data['sequence'])
        pattern_complexity = challenge.data['pattern_complexity']
        
        # Complex patterns with multiple overlapping sequences
        assert sequence_length >= 160, "Sequence should be long enough"
        assert pattern_complexity >= 3, "Should have multiple overlapping patterns"
        
        # Humans cannot analyze 160+ numbers and find multiple patterns in <100ms
        assert sequence_length * pattern_complexity > 400, "Complexity should be humanly impossible"


class TestOptimizationGenerator:
    """Test optimization challenge generator"""
    
    def setup_method(self):
        self.generator = OptimizationGenerator()
    
    def test_optimization_challenge_generation(self):
        """Test optimization challenge generation"""
        challenge = self.generator.generate(difficulty=1, seed=42)
        
        assert challenge.challenge_type == ChallengeType.OPTIMIZATION
        assert 'dimensions' in challenge.data
        assert 'centers' in challenge.data
        assert 'weights' in challenge.data
        assert challenge.data['dimensions'] >= 15
    
    def test_optimization_difficulty_scaling(self):
        """Test that difficulty affects optimization complexity"""
        easy_challenge = self.generator.generate(difficulty=1, seed=42)
        hard_challenge = self.generator.generate(difficulty=5, seed=42)
        
        easy_dims = easy_challenge.data['dimensions']
        hard_dims = hard_challenge.data['dimensions']
        
        assert hard_dims > easy_dims, "Higher difficulty should create more dimensions"
    
    def test_objective_function(self):
        """Test the objective function calculation"""
        centers = np.array([[0, 0], [1, 1]])
        weights = np.array([1.0, 1.0])
        point = np.array([0.5, 0.5])
        
        result = self.generator._objective_function(point, centers, weights)
        assert isinstance(result, float), "Objective function should return float"
        assert result >= 0, "Objective function should be non-negative"
    
    def test_human_impossibility_optimization(self):
        """Test that optimization challenges are impossible for humans in <100ms"""
        challenge = self.generator.generate(difficulty=3, seed=42)
        
        dimensions = challenge.data['dimensions']
        num_centers = len(challenge.data['centers'])
        
        # Multi-dimensional optimization with multiple local minima
        assert dimensions >= 25, "Should have many dimensions"
        assert num_centers >= 8, "Should have multiple local minima"
        
        # Humans cannot solve 25+ dimensional optimization in <100ms
        complexity_factor = dimensions * num_centers
        assert complexity_factor >= 200, "Optimization should be humanly impossible"


class TestHumanImpossibilityBenchmarks:
    """Comprehensive tests to verify human impossibility within 100ms"""
    
    def setup_method(self):
        self.generator = ChallengeGenerator()
    
    def test_reading_time_benchmark(self):
        """Test that just reading the challenge data exceeds human capability"""
        challenge = self.generator.generate_challenge(difficulty=3)
        
        # Estimate reading time based on data size
        if challenge.challenge_type == ChallengeType.MATRIX_OPERATIONS:
            matrix_size = challenge.data['size']
            total_numbers = matrix_size * matrix_size * 2
            # Humans read ~3-5 numbers per second under pressure
            estimated_reading_time_ms = (total_numbers / 4) * 1000
            assert estimated_reading_time_ms > 100, f"Reading {total_numbers} numbers should take >{estimated_reading_time_ms}ms"
        
        elif challenge.challenge_type == ChallengeType.PATTERN_RECOGNITION:
            sequence_length = len(challenge.data['sequence'])
            # Humans need ~50ms per number to process for patterns
            estimated_analysis_time_ms = sequence_length * 50
            assert estimated_analysis_time_ms > 100, f"Analyzing {sequence_length} numbers should take >{estimated_analysis_time_ms}ms"
        
        elif challenge.challenge_type == ChallengeType.OPTIMIZATION:
            dimensions = challenge.data['dimensions']
            # Multi-dimensional optimization requires iterative computation
            # Even one gradient calculation would take >100ms manually
            assert dimensions > 20, f"Optimizing {dimensions} dimensions should be impossible manually"
    
    def test_computational_complexity(self):
        """Test computational complexity exceeds human capability"""
        challenge = self.generator.generate_challenge(difficulty=4)
        
        if challenge.challenge_type == ChallengeType.MATRIX_OPERATIONS:
            size = challenge.data['size']
            # Matrix multiplication is O(n³) - impossible for humans with large n
            operations = size ** 3
            assert operations >= 500000, f"Matrix multiplication requires {operations} operations"
        
        elif challenge.challenge_type == ChallengeType.PATTERN_RECOGNITION:
            sequence_length = len(challenge.data['sequence'])
            complexity = challenge.data['pattern_complexity']
            # Pattern analysis requires examining all combinations
            analysis_complexity = sequence_length * complexity
            assert analysis_complexity > 500, f"Pattern analysis complexity: {analysis_complexity}"
    
    @pytest.mark.parametrize("difficulty", [1, 3, 5])
    def test_all_challenge_types_impossible(self, difficulty):
        """Test that all challenge types are impossible for humans at all difficulties"""
        for challenge_type in ChallengeType:
            if challenge_type in [ChallengeType.MATRIX_OPERATIONS, 
                                ChallengeType.PATTERN_RECOGNITION, 
                                ChallengeType.OPTIMIZATION]:
                
                challenge = self.generator.generate_challenge(
                    difficulty=difficulty, 
                    force_type=challenge_type
                )
                
                # Verify challenge has sufficient complexity
                assert challenge.timeout_ms == 100, "Timeout should be 100ms"
                assert challenge.difficulty_level == difficulty
                
                # Each challenge type should have specific complexity markers
                if challenge_type == ChallengeType.MATRIX_OPERATIONS:
                    assert challenge.data['size'] >= 50 + difficulty * 10
                elif challenge_type == ChallengeType.PATTERN_RECOGNITION:
                    assert len(challenge.data['sequence']) >= 100 + difficulty * 20
                elif challenge_type == ChallengeType.OPTIMIZATION:
                    assert challenge.data['dimensions'] >= 10 + difficulty * 5


class TestChallengeReproducibility:
    """Test that challenges are reproducible for testing"""
    
    def setup_method(self):
        self.generator = ChallengeGenerator()
    
    def test_seed_reproducibility(self):
        """Test that same seed produces same challenge"""
        gen1 = MatrixOperationsGenerator()
        gen2 = MatrixOperationsGenerator()
        
        challenge1 = gen1.generate(difficulty=2, seed=12345)
        challenge2 = gen2.generate(difficulty=2, seed=12345)
        
        # Should produce identical challenges
        assert challenge1.data['matrix_a'] == challenge2.data['matrix_a']
        assert challenge1.data['matrix_b'] == challenge2.data['matrix_b']
        assert challenge1.expected_solution_hash == challenge2.expected_solution_hash
    
    def test_different_seeds_different_challenges(self):
        """Test that different seeds produce different challenges"""
        gen = MatrixOperationsGenerator()
        
        challenge1 = gen.generate(difficulty=2, seed=12345)
        challenge2 = gen.generate(difficulty=2, seed=54321)
        
        # Should produce different challenges
        assert challenge1.data['matrix_a'] != challenge2.data['matrix_a']
        assert challenge1.expected_solution_hash != challenge2.expected_solution_hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])