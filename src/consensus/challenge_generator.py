"""
Challenge Generator for PoAIP Consensus

This module generates mathematical challenges that require AI capabilities
and are impossible for humans to solve in under 100ms.
"""

import hashlib
import json
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional
import numpy as np


class ChallengeType(Enum):
    """Types of challenges that can be generated"""
    MATRIX_OPERATIONS = "matrix_operations"
    PATTERN_RECOGNITION = "pattern_recognition"
    OPTIMIZATION = "optimization"
    SEQUENCE_PREDICTION = "sequence_prediction"
    MULTI_DIMENSIONAL_ANALYSIS = "multi_dimensional_analysis"


@dataclass
class Challenge:
    """Represents a mathematical challenge for AI nodes"""
    challenge_id: str
    challenge_type: ChallengeType
    data: Dict[str, Any]
    expected_solution_hash: str
    difficulty_level: int
    timestamp: float
    timeout_ms: int = 100


@dataclass
class Solution:
    """Represents a solution to a challenge"""
    challenge_id: str
    solution_data: Dict[str, Any]
    computation_time_ms: float
    node_signature: str
    timestamp: float


class BaseChallengeGenerator(ABC):
    """Abstract base class for challenge generators"""
    
    @abstractmethod
    def generate(self, difficulty: int, seed: Optional[int] = None) -> Challenge:
        """Generate a challenge of specified difficulty"""
        pass
    
    @abstractmethod
    def verify_solution(self, challenge: Challenge, solution: Solution) -> bool:
        """Verify if a solution is correct"""
        pass


class MatrixOperationsGenerator(BaseChallengeGenerator):
    """Generates matrix operation challenges"""
    
    def generate(self, difficulty: int, seed: Optional[int] = None) -> Challenge:
        if seed:
            np.random.seed(seed)
        
        # Generate matrices based on difficulty
        size = min(50 + difficulty * 10, 200)  # Scale with difficulty
        
        matrix_a = np.random.randint(-100, 100, (size, size))
        matrix_b = np.random.randint(-100, 100, (size, size))
        
        # Calculate expected result
        expected_result = np.dot(matrix_a, matrix_b)
        expected_hash = hashlib.sha256(expected_result.tobytes()).hexdigest()
        
        challenge_data = {
            "operation": "matrix_multiplication",
            "matrix_a": matrix_a.tolist(),
            "matrix_b": matrix_b.tolist(),
            "size": size
        }
        
        challenge_id = hashlib.sha256(
            json.dumps(challenge_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return Challenge(
            challenge_id=challenge_id,
            challenge_type=ChallengeType.MATRIX_OPERATIONS,
            data=challenge_data,
            expected_solution_hash=expected_hash,
            difficulty_level=difficulty,
            timestamp=time.time()
        )
    
    def verify_solution(self, challenge: Challenge, solution: Solution) -> bool:
        try:
            result_matrix = np.array(solution.solution_data["result"])
            result_hash = hashlib.sha256(result_matrix.tobytes()).hexdigest()
            return result_hash == challenge.expected_solution_hash
        except (KeyError, ValueError, TypeError):
            return False


class PatternRecognitionGenerator(BaseChallengeGenerator):
    """Generates pattern recognition challenges"""
    
    def generate(self, difficulty: int, seed: Optional[int] = None) -> Challenge:
        if seed:
            random.seed(seed)
        
        # Generate a complex sequence with hidden pattern
        sequence_length = 100 + difficulty * 20
        
        # Create multiple overlapping patterns
        patterns = []
        for _ in range(3 + difficulty):
            pattern_type = random.choice(['fibonacci', 'prime', 'geometric', 'polynomial'])
            patterns.append(self._generate_pattern(pattern_type, sequence_length))
        
        # Combine patterns with noise
        combined_sequence = []
        for i in range(sequence_length):
            value = sum(pattern[i % len(pattern)] for pattern in patterns)
            noise = random.randint(-10, 10) if difficulty < 5 else 0
            combined_sequence.append(value + noise)
        
        # Expected next values
        next_values = []
        for i in range(5):  # Predict next 5 values
            idx = sequence_length + i
            value = sum(pattern[idx % len(pattern)] for pattern in patterns)
            next_values.append(value)
        
        expected_hash = hashlib.sha256(
            json.dumps(next_values).encode()
        ).hexdigest()
        
        challenge_data = {
            "sequence": combined_sequence,
            "predict_count": 5,
            "pattern_complexity": difficulty
        }
        
        challenge_id = hashlib.sha256(
            json.dumps(challenge_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return Challenge(
            challenge_id=challenge_id,
            challenge_type=ChallengeType.PATTERN_RECOGNITION,
            data=challenge_data,
            expected_solution_hash=expected_hash,
            difficulty_level=difficulty,
            timestamp=time.time()
        )
    
    def _generate_pattern(self, pattern_type: str, length: int) -> List[int]:
        """Generate a specific type of pattern"""
        if pattern_type == 'fibonacci':
            pattern = [1, 1]
            while len(pattern) < length:
                pattern.append(pattern[-1] + pattern[-2])
            return pattern[:length]
        
        elif pattern_type == 'prime':
            primes = []
            num = 2
            while len(primes) < length:
                if self._is_prime(num):
                    primes.append(num)
                num += 1
            return primes
        
        elif pattern_type == 'geometric':
            ratio = random.choice([2, 3, 5])
            return [ratio ** i for i in range(length)]
        
        elif pattern_type == 'polynomial':
            coeffs = [random.randint(1, 5) for _ in range(3)]
            return [sum(c * (i ** p) for p, c in enumerate(coeffs)) for i in range(length)]
        
        return [0] * length
    
    def _is_prime(self, n: int) -> bool:
        """Check if a number is prime"""
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    def verify_solution(self, challenge: Challenge, solution: Solution) -> bool:
        try:
            predicted_values = solution.solution_data["predicted_values"]
            result_hash = hashlib.sha256(
                json.dumps(predicted_values).encode()
            ).hexdigest()
            return result_hash == challenge.expected_solution_hash
        except (KeyError, ValueError, TypeError):
            return False


class OptimizationGenerator(BaseChallengeGenerator):
    """Generates optimization challenges"""
    
    def generate(self, difficulty: int, seed: Optional[int] = None) -> Challenge:
        if seed:
            np.random.seed(seed)
        
        # Generate a multi-dimensional optimization problem
        dimensions = 10 + difficulty * 5
        
        # Create a complex objective function with multiple local minima
        centers = np.random.uniform(-10, 10, (5 + difficulty, dimensions))
        weights = np.random.uniform(0.1, 2.0, 5 + difficulty)
        
        # Calculate the global minimum (approximately)
        best_point = None
        best_value = float('inf')
        
        # Sample many points to find approximate global minimum
        for _ in range(10000):
            point = np.random.uniform(-15, 15, dimensions)
            value = self._objective_function(point, centers, weights)
            if value < best_value:
                best_value = value
                best_point = point.copy()
        
        expected_hash = hashlib.sha256(
            f"{best_value:.6f}".encode()
        ).hexdigest()
        
        challenge_data = {
            "dimensions": dimensions,
            "centers": centers.tolist(),
            "weights": weights.tolist(),
            "bounds": [-15, 15],
            "target_precision": 6
        }
        
        challenge_id = hashlib.sha256(
            json.dumps(challenge_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return Challenge(
            challenge_id=challenge_id,
            challenge_type=ChallengeType.OPTIMIZATION,
            data=challenge_data,
            expected_solution_hash=expected_hash,
            difficulty_level=difficulty,
            timestamp=time.time()
        )
    
    def _objective_function(self, x: np.ndarray, centers: np.ndarray, weights: np.ndarray) -> float:
        """Complex multi-modal objective function"""
        total = 0
        for i, (center, weight) in enumerate(zip(centers, weights)):
            distance = np.sum((x - center) ** 2)
            total += weight * np.exp(-distance / 10) * np.sin(distance) ** 2
        return total
    
    def verify_solution(self, challenge: Challenge, solution: Solution) -> bool:
        try:
            optimized_point = np.array(solution.solution_data["optimized_point"])
            centers = np.array(challenge.data["centers"])
            weights = np.array(challenge.data["weights"])
            
            value = self._objective_function(optimized_point, centers, weights)
            result_hash = hashlib.sha256(
                f"{value:.6f}".encode()
            ).hexdigest()
            
            return result_hash == challenge.expected_solution_hash
        except (KeyError, ValueError, TypeError):
            return False


class ChallengeGenerator:
    """Main challenge generator that rotates between different types"""
    
    def __init__(self):
        self.generators = {
            ChallengeType.MATRIX_OPERATIONS: MatrixOperationsGenerator(),
            ChallengeType.PATTERN_RECOGNITION: PatternRecognitionGenerator(),
            ChallengeType.OPTIMIZATION: OptimizationGenerator(),
        }
        self.challenge_history = []
        self.rotation_index = 0
    
    def generate_challenge(self, difficulty: int = 1, force_type: Optional[ChallengeType] = None) -> Challenge:
        """Generate a challenge with automatic type rotation"""
        if force_type:
            challenge_type = force_type
        else:
            # Rotate through challenge types to prevent optimization
            available_types = list(self.generators.keys())
            challenge_type = available_types[self.rotation_index % len(available_types)]
            self.rotation_index += 1
        
        # Use timestamp as seed for reproducibility in testing
        seed = int(time.time() * 1000) % 1000000
        
        generator = self.generators[challenge_type]
        challenge = generator.generate(difficulty, seed)
        
        # Store in history for analysis
        self.challenge_history.append({
            'challenge_id': challenge.challenge_id,
            'type': challenge_type,
            'difficulty': difficulty,
            'timestamp': challenge.timestamp
        })
        
        return challenge
    
    def verify_solution(self, challenge: Challenge, solution: Solution) -> bool:
        """Verify a solution against its challenge"""
        if challenge.challenge_type not in self.generators:
            return False
        
        generator = self.generators[challenge.challenge_type]
        return generator.verify_solution(challenge, solution)
    
    def get_challenge_stats(self) -> Dict[str, Any]:
        """Get statistics about generated challenges"""
        if not self.challenge_history:
            return {}
        
        type_counts = {}
        for entry in self.challenge_history:
            challenge_type = entry['type'].value
            type_counts[challenge_type] = type_counts.get(challenge_type, 0) + 1
        
        return {
            'total_challenges': len(self.challenge_history),
            'type_distribution': type_counts,
            'last_challenge_time': self.challenge_history[-1]['timestamp']
        }