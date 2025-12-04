"""
Módulo de nodos IA para PlayerGold
Proporciona funcionalidades de verificación y carga de modelos IA
"""

from .model_verification import (
    ModelHashVerifier,
    ModelVerificationError,
    CERTIFIED_MODEL_HASHES,
    verify_model_file,
    calculate_model_hash
)

from .model_loader import (
    AIModelLoader,
    HardwareValidator,
    HardwareSpecs,
    ModelRequirements,
    ModelFramework,
    ModelLoadError,
    ModelValidationError
)

__all__ = [
    # Model verification
    'ModelHashVerifier',
    'ModelVerificationError', 
    'CERTIFIED_MODEL_HASHES',
    'verify_model_file',
    'calculate_model_hash',
    
    # Model loading
    'AIModelLoader',
    'HardwareValidator',
    'HardwareSpecs',
    'ModelRequirements',
    'ModelFramework',
    'ModelLoadError',
    'ModelValidationError'
]