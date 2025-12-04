"""
Challenge Processor for AI Nodes

This module processes mathematical challenges using AI capabilities
and provides cryptographic signatures to certify AI origin.
"""

import hashlib
import json
import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable
import numpy as np
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend

from src.consensus.challenge_generator import (
    Challenge, 
    Solution, 
    ChallengeType
)


@dataclass
class ProcessingResult:
    """Result of challenge processing"""
    success: bool
    solution: Optional[Solution]
    computation_time_ms: float
    error_message: Optional[str] = None
    timeout_exceeded: bool = False


class AISignatureManager:
    """Manages cryptographic signatures for AI nodes"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        
    def sign_solution(self, solution_data: Dict[str, Any]) -> str:
        """Sign solution data to certify AI origin"""
        # Create deterministic message from solution data
        message = json.dumps(solution_data, sort_keys=True).encode('utf-8')
        
        # Add node identifier and timestamp
        full_message = f"{self.node_id}:{time.time()}:{message.hex()}".encode('utf-8')
        
        # Sign the message
        signature = self.private_key.sign(full_message)
        
        # Return base64 encoded signature with metadata
        signature_data = {
            'signature': signature.hex(),
            'node_id': self.node_id,
            'public_key': self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex(),
            'timestamp': time.time()
        }
        
        return json.dumps(signature_data)
    
    def verify_signature(self, solution_data: Dict[str, Any], signature_json: str) -> bool:
        """Verify that a signature came from an AI node"""
        return self.verify_signature_static(solution_data, signature_json)
    
    @staticmethod
    def verify_signature_static(solution_data: Dict[str, Any], signature_json: str) -> bool:
        """Static method to verify signatures without needing an instance"""
        try:
            signature_data = json.loads(signature_json)
            
            # Reconstruct the message exactly as it was signed
            message = json.dumps(solution_data, sort_keys=True).encode('utf-8')
            node_id = signature_data['node_id']
            timestamp = signature_data['timestamp']
            full_message = f"{node_id}:{timestamp}:{message.hex()}".encode('utf-8')
            
            # Get public key
            public_key_bytes = bytes.fromhex(signature_data['public_key'])
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            # Verify signature
            signature_bytes = bytes.fromhex(signature_data['signature'])
            public_key.verify(signature_bytes, full_message)
            
            return True
        except Exception:
            return False


class ChallengeProcessor:
    """Processes challenges using AI capabilities with timeout enforcement"""
    
    def __init__(self, node_id: str, ai_model_interface: Optional[Any] = None):
        self.node_id = node_id
        self.ai_model = ai_model_interface
        self.signature_manager = AISignatureManager(node_id)
        self.timeout_ms = 100  # Maximum processing time
        
    def process_challenge(self, challenge: Challenge) -> ProcessingResult:
        """Process a challenge with timeout enforcement"""
        start_time = time.time()
        
        # Use threading to enforce timeout
        result_container = {'result': None, 'error': None}
        
        def process_worker():
            try:
                if challenge.challenge_type == ChallengeType.MATRIX_OPERATIONS:
                    result_container['result'] = self._process_matrix_challenge(challenge)
                elif challenge.challenge_type == ChallengeType.PATTERN_RECOGNITION:
                    result_container['result'] = self._process_pattern_challenge(challenge)
                elif challenge.challenge_type == ChallengeType.OPTIMIZATION:
                    result_container['result'] = self._process_optimization_challenge(challenge)
                else:
                    result_container['error'] = f"Unknown challenge type: {challenge.challenge_type}"
            except Exception as e:
                result_container['error'] = str(e)
        
        # Start processing in separate thread
        worker_thread = threading.Thread(target=process_worker)
        worker_thread.daemon = True
        worker_thread.start()
        
        # Wait for completion or timeout
        worker_thread.join(timeout=self.timeout_ms / 1000.0)
        
        computation_time_ms = (time.time() - start_time) * 1000
        
        # Check if timeout exceeded
        if worker_thread.is_alive():
            return ProcessingResult(
                success=False,
                solution=None,
                computation_time_ms=computation_time_ms,
                error_message="Processing timeout exceeded",
                timeout_exceeded=True
            )
        
        # Check for processing errors
        if result_container['error']:
            return ProcessingResult(
                success=False,
                solution=None,
                computation_time_ms=computation_time_ms,
                error_message=result_container['error']
            )
        
        # Create signed solution
        solution_data = result_container['result']
        signature = self.signature_manager.sign_solution(solution_data)
        
        solution = Solution(
            challenge_id=challenge.challenge_id,
            solution_data=solution_data,
            computation_time_ms=computation_time_ms,
            node_signature=signature,
            timestamp=time.time()
        )
        
        return ProcessingResult(
            success=True,
            solution=solution,
            computation_time_ms=computation_time_ms
        )
    
    def _process_matrix_challenge(self, challenge: Challenge) -> Dict[str, Any]:
        """Process matrix multiplication challenge using AI/GPU acceleration"""
        matrix_a = np.array(challenge.data['matrix_a'], dtype=np.float32)
        matrix_b = np.array(challenge.data['matrix_b'], dtype=np.float32)
        
        # Use optimized matrix multiplication (simulates AI/GPU processing)
        if self.ai_model and hasattr(self.ai_model, 'matrix_multiply'):
            # Use AI model's optimized matrix operations
            result = self.ai_model.matrix_multiply(matrix_a, matrix_b)
        else:
            # Fallback to NumPy (still faster than human calculation)
            result = np.dot(matrix_a, matrix_b)
        
        return {
            "result": result.tolist(),
            "operation": "matrix_multiplication",
            "processing_method": "ai_optimized" if self.ai_model else "numpy_optimized"
        }
    
    def _process_pattern_challenge(self, challenge: Challenge) -> Dict[str, Any]:
        """Process pattern recognition challenge using AI pattern analysis"""
        sequence = challenge.data['sequence']
        predict_count = challenge.data['predict_count']
        
        if self.ai_model and hasattr(self.ai_model, 'predict_sequence'):
            # Use AI model for pattern recognition
            predicted_values = self.ai_model.predict_sequence(sequence, predict_count)
        else:
            # Fallback to algorithmic pattern detection
            predicted_values = self._algorithmic_pattern_detection(sequence, predict_count)
        
        return {
            "predicted_values": predicted_values,
            "sequence_length": len(sequence),
            "processing_method": "ai_pattern_recognition" if self.ai_model else "algorithmic_detection"
        }
    
    def _algorithmic_pattern_detection(self, sequence: list, predict_count: int) -> list:
        """Fallback algorithmic pattern detection"""
        # Analyze differences to find patterns
        if len(sequence) < 10:
            return [sequence[-1]] * predict_count
        
        # Try to detect arithmetic progression
        diffs = [sequence[i+1] - sequence[i] for i in range(len(sequence)-1)]
        
        # Check for constant difference (arithmetic sequence)
        if len(set(diffs[-5:])) == 1:
            common_diff = diffs[-1]
            return [sequence[-1] + common_diff * (i+1) for i in range(predict_count)]
        
        # Try to detect geometric progression
        if all(sequence[i] != 0 for i in range(-5, 0, 1) if i + len(sequence) >= 0):
            ratios = [sequence[i+1] / sequence[i] for i in range(len(sequence)-5, len(sequence)-1)]
            if len(set(round(r, 3) for r in ratios)) == 1:
                common_ratio = ratios[-1]
                return [sequence[-1] * (common_ratio ** (i+1)) for i in range(predict_count)]
        
        # Fallback: use moving average
        window_size = min(10, len(sequence) // 4)
        recent_avg = sum(sequence[-window_size:]) / window_size
        trend = (sequence[-1] - sequence[-window_size]) / window_size
        
        return [recent_avg + trend * (i+1) for i in range(predict_count)]
    
    def _process_optimization_challenge(self, challenge: Challenge) -> Dict[str, Any]:
        """Process optimization challenge using AI-guided search"""
        dimensions = challenge.data['dimensions']
        centers = np.array(challenge.data['centers'])
        weights = np.array(challenge.data['weights'])
        bounds = challenge.data['bounds']
        
        if self.ai_model and hasattr(self.ai_model, 'optimize'):
            # Use AI model for optimization
            optimized_point = self.ai_model.optimize(centers, weights, bounds, dimensions)
        else:
            # Fallback to gradient-based optimization
            optimized_point = self._gradient_optimization(centers, weights, bounds, dimensions)
        
        return {
            "optimized_point": optimized_point.tolist(),
            "dimensions": dimensions,
            "processing_method": "ai_optimization" if self.ai_model else "gradient_optimization"
        }
    
    def _gradient_optimization(self, centers: np.ndarray, weights: np.ndarray, 
                             bounds: list, dimensions: int) -> np.ndarray:
        """Fallback gradient-based optimization"""
        # Start from random point
        current_point = np.random.uniform(bounds[0], bounds[1], dimensions)
        learning_rate = 0.1
        
        # Perform gradient descent (simplified)
        for _ in range(50):  # Limited iterations due to timeout
            gradient = self._compute_gradient(current_point, centers, weights)
            current_point -= learning_rate * gradient
            
            # Keep within bounds
            current_point = np.clip(current_point, bounds[0], bounds[1])
            
            # Adaptive learning rate
            learning_rate *= 0.99
        
        return current_point
    
    def _compute_gradient(self, point: np.ndarray, centers: np.ndarray, 
                         weights: np.ndarray) -> np.ndarray:
        """Compute gradient of the objective function"""
        gradient = np.zeros_like(point)
        
        for center, weight in zip(centers, weights):
            diff = point - center
            distance_sq = np.sum(diff ** 2)
            
            # Gradient of the complex objective function
            exp_term = np.exp(-distance_sq / 10)
            sin_term = np.sin(distance_sq)
            
            grad_component = weight * (
                -2 * diff / 10 * exp_term * sin_term ** 2 +
                2 * diff * exp_term * sin_term * np.cos(distance_sq)
            )
            
            gradient += grad_component
        
        return gradient
    
    def verify_solution_signature(self, solution: Solution) -> bool:
        """Verify that a solution has a valid AI signature"""
        return AISignatureManager.verify_signature_static(
            solution.solution_data, 
            solution.node_signature
        )


class MockAIModel:
    """Mock AI model for testing purposes"""
    
    def matrix_multiply(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Optimized matrix multiplication"""
        return np.dot(a, b)
    
    def predict_sequence(self, sequence: list, count: int) -> list:
        """AI-based sequence prediction"""
        # Simulate AI pattern recognition with more sophisticated analysis
        if len(sequence) < 5:
            return [sequence[-1]] * count
        
        # Use polynomial fitting for better prediction
        x = np.arange(len(sequence))
        y = np.array(sequence)
        
        # Fit polynomial of degree 3
        try:
            coeffs = np.polyfit(x, y, min(3, len(sequence) - 1))
            poly = np.poly1d(coeffs)
            
            # Predict next values
            future_x = np.arange(len(sequence), len(sequence) + count)
            predictions = poly(future_x)
            
            return predictions.tolist()
        except:
            # Fallback to simple extrapolation
            trend = sequence[-1] - sequence[-2] if len(sequence) > 1 else 0
            return [sequence[-1] + trend * (i+1) for i in range(count)]
    
    def optimize(self, centers: np.ndarray, weights: np.ndarray, 
                bounds: list, dimensions: int) -> np.ndarray:
        """AI-guided optimization"""
        # Simulate AI optimization with multiple random starts
        best_point = None
        best_value = float('inf')
        
        # Try multiple starting points (AI would use more sophisticated heuristics)
        for _ in range(20):
            start_point = np.random.uniform(bounds[0], bounds[1], dimensions)
            optimized = self._local_optimize(start_point, centers, weights, bounds)
            value = self._objective_function(optimized, centers, weights)
            
            if value < best_value:
                best_value = value
                best_point = optimized
        
        return best_point
    
    def _local_optimize(self, start_point: np.ndarray, centers: np.ndarray, 
                       weights: np.ndarray, bounds: list) -> np.ndarray:
        """Local optimization from starting point"""
        current = start_point.copy()
        learning_rate = 0.2
        
        for _ in range(30):
            gradient = self._compute_gradient(current, centers, weights)
            current -= learning_rate * gradient
            current = np.clip(current, bounds[0], bounds[1])
            learning_rate *= 0.95
        
        return current
    
    def _compute_gradient(self, point: np.ndarray, centers: np.ndarray, 
                         weights: np.ndarray) -> np.ndarray:
        """Compute gradient"""
        gradient = np.zeros_like(point)
        
        for center, weight in zip(centers, weights):
            diff = point - center
            distance_sq = np.sum(diff ** 2)
            
            exp_term = np.exp(-distance_sq / 10)
            sin_term = np.sin(distance_sq)
            
            grad_component = weight * (
                -2 * diff / 10 * exp_term * sin_term ** 2 +
                2 * diff * exp_term * sin_term * np.cos(distance_sq)
            )
            
            gradient += grad_component
        
        return gradient
    
    def _objective_function(self, x: np.ndarray, centers: np.ndarray, 
                           weights: np.ndarray) -> float:
        """Objective function"""
        total = 0
        for center, weight in zip(centers, weights):
            distance = np.sum((x - center) ** 2)
            total += weight * np.exp(-distance / 10) * np.sin(distance) ** 2
        return total