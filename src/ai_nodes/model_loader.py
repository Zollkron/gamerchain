"""
Cargador y validador de modelos IA para PlayerGold
Maneja la carga de modelos PyTorch/TensorFlow y validación de requisitos
"""

import os
import sys
import psutil
import logging
from typing import Optional, Dict, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Importaciones opcionales para frameworks de IA
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from .model_verification import ModelHashVerifier, ModelVerificationError

logger = logging.getLogger(__name__)


class ModelFramework(Enum):
    """Frameworks de IA soportados"""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    UNKNOWN = "unknown"


@dataclass
class HardwareSpecs:
    """Especificaciones de hardware del sistema"""
    cpu_cores: int
    ram_gb: float
    gpu_available: bool
    gpu_memory_gb: float
    gpu_name: Optional[str] = None


@dataclass
class ModelRequirements:
    """Requisitos mínimos de un modelo IA"""
    min_cpu_cores: int
    min_ram_gb: int
    min_vram_gb: int
    framework: ModelFramework
    model_size_mb: Optional[int] = None


class ModelLoadError(Exception):
    """Excepción para errores de carga de modelos"""
    pass


class ModelValidationError(Exception):
    """Excepción para errores de validación de modelos"""
    pass


class HardwareValidator:
    """Validador de requisitos de hardware"""
    
    @staticmethod
    def get_system_specs() -> HardwareSpecs:
        """
        Obtiene las especificaciones del sistema actual
        
        Returns:
            HardwareSpecs con información del hardware
        """
        # CPU cores
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count()
        
        # RAM en GB
        ram_bytes = psutil.virtual_memory().total
        ram_gb = ram_bytes / (1024**3)
        
        # GPU information
        gpu_available = False
        gpu_memory_gb = 0.0
        gpu_name = None
        
        # Verificar GPU NVIDIA con CUDA
        if TORCH_AVAILABLE and torch.cuda.is_available():
            gpu_available = True
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_name = torch.cuda.get_device_name(0)
        
        # Verificar GPU con TensorFlow si PyTorch no está disponible
        elif TF_AVAILABLE:
            try:
                gpus = tf.config.experimental.list_physical_devices('GPU')
                if gpus:
                    gpu_available = True
                    # TensorFlow no proporciona memoria GPU fácilmente, usar estimación
                    gpu_memory_gb = 4.0  # Estimación conservadora
                    gpu_name = "GPU (TensorFlow)"
            except Exception:
                pass
        
        return HardwareSpecs(
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            gpu_available=gpu_available,
            gpu_memory_gb=gpu_memory_gb,
            gpu_name=gpu_name
        )
    
    @staticmethod
    def validate_hardware_requirements(specs: HardwareSpecs, requirements: ModelRequirements) -> Tuple[bool, str]:
        """
        Valida si el hardware cumple los requisitos del modelo
        
        Args:
            specs: Especificaciones del sistema
            requirements: Requisitos del modelo
            
        Returns:
            Tupla (cumple_requisitos, mensaje_error)
        """
        errors = []
        
        # Validar CPU cores
        if specs.cpu_cores < requirements.min_cpu_cores:
            errors.append(f"CPU insuficiente: {specs.cpu_cores} cores disponibles, "
                         f"{requirements.min_cpu_cores} requeridos")
        
        # Validar RAM
        if specs.ram_gb < requirements.min_ram_gb:
            errors.append(f"RAM insuficiente: {specs.ram_gb:.1f}GB disponible, "
                         f"{requirements.min_ram_gb}GB requeridos")
        
        # Validar GPU/VRAM
        if requirements.min_vram_gb > 0:
            if not specs.gpu_available:
                errors.append("GPU requerida pero no disponible")
            elif specs.gpu_memory_gb < requirements.min_vram_gb:
                errors.append(f"VRAM insuficiente: {specs.gpu_memory_gb:.1f}GB disponible, "
                             f"{requirements.min_vram_gb}GB requeridos")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "Hardware cumple todos los requisitos"


class AIModelLoader:
    """
    Cargador principal de modelos IA con validación de requisitos
    """
    
    def __init__(self):
        self.hash_verifier = ModelHashVerifier()
        self.hardware_validator = HardwareValidator()
        self.loaded_models: Dict[str, Any] = {}
        
    def detect_model_framework(self, model_path: str) -> ModelFramework:
        """
        Detecta el framework del modelo basado en la extensión del archivo
        
        Args:
            model_path: Ruta al archivo del modelo
            
        Returns:
            Framework detectado
        """
        path = Path(model_path)
        extension = path.suffix.lower()
        
        # Extensiones comunes de PyTorch
        if extension in ['.pt', '.pth', '.pytorch']:
            return ModelFramework.PYTORCH
        
        # Extensiones comunes de TensorFlow
        if extension in ['.pb', '.h5', '.keras']:
            return ModelFramework.TENSORFLOW
        
        # Detectar por estructura de directorio (TensorFlow SavedModel)
        if path.is_dir():
            if (path / 'saved_model.pb').exists():
                return ModelFramework.TENSORFLOW
        
        logger.warning(f"No se pudo detectar framework para {model_path}")
        return ModelFramework.UNKNOWN
    
    def get_model_requirements(self, model_id: str) -> Optional[ModelRequirements]:
        """
        Obtiene los requisitos de un modelo certificado
        
        Args:
            model_id: ID del modelo certificado
            
        Returns:
            ModelRequirements o None si el modelo no existe
        """
        model_info = self.hash_verifier.get_model_info(model_id)
        if not model_info:
            return None
        
        # Por ahora asumimos PyTorch para todos los modelos certificados
        # En el futuro esto podría venir de la configuración del modelo
        return ModelRequirements(
            min_cpu_cores=model_info["min_cpu_cores"],
            min_ram_gb=model_info["min_ram_gb"],
            min_vram_gb=model_info["min_vram_gb"],
            framework=ModelFramework.PYTORCH
        )
    
    def validate_model_compatibility(self, model_path: str, model_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Valida si un modelo es compatible con el sistema actual
        
        Args:
            model_path: Ruta al archivo del modelo
            model_id: ID del modelo (opcional, se auto-detecta si no se proporciona)
            
        Returns:
            Tupla (es_compatible, mensaje)
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(model_path):
                return False, f"Archivo de modelo no encontrado: {model_path}"
            
            # Verificar hash si no se proporciona model_id
            if not model_id:
                is_valid, detected_id = self.hash_verifier.verify_model_hash(model_path)
                if not is_valid:
                    return False, "Modelo no está en la lista de modelos certificados"
                model_id = detected_id
            else:
                # Verificar hash para el model_id específico
                is_valid, _ = self.hash_verifier.verify_model_hash(model_path, model_id)
                if not is_valid:
                    return False, f"Hash del modelo no coincide con {model_id}"
            
            # Obtener requisitos del modelo
            requirements = self.get_model_requirements(model_id)
            if not requirements:
                return False, f"No se pudieron obtener requisitos para modelo {model_id}"
            
            # Verificar framework disponible
            framework = self.detect_model_framework(model_path)
            if framework == ModelFramework.PYTORCH and not TORCH_AVAILABLE:
                return False, "PyTorch no está instalado pero es requerido para este modelo"
            elif framework == ModelFramework.TENSORFLOW and not TF_AVAILABLE:
                return False, "TensorFlow no está instalado pero es requerido para este modelo"
            
            # Validar hardware
            system_specs = self.hardware_validator.get_system_specs()
            hardware_ok, hardware_msg = self.hardware_validator.validate_hardware_requirements(
                system_specs, requirements
            )
            
            if not hardware_ok:
                return False, f"Hardware insuficiente: {hardware_msg}"
            
            return True, f"Modelo {model_id} es compatible con el sistema"
            
        except Exception as e:
            logger.error(f"Error validando compatibilidad del modelo: {str(e)}")
            return False, f"Error durante validación: {str(e)}"
    
    def load_pytorch_model(self, model_path: str) -> Any:
        """
        Carga un modelo PyTorch
        
        Args:
            model_path: Ruta al modelo PyTorch
            
        Returns:
            Modelo cargado
            
        Raises:
            ModelLoadError: Si hay error cargando el modelo
        """
        if not TORCH_AVAILABLE:
            raise ModelLoadError("PyTorch no está disponible")
        
        try:
            # Cargar modelo en CPU primero para verificar integridad
            model = torch.load(model_path, map_location='cpu')
            
            # Mover a GPU si está disponible
            if torch.cuda.is_available():
                model = model.cuda()
                logger.info(f"Modelo cargado en GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("Modelo cargado en CPU")
            
            # Poner modelo en modo evaluación
            if hasattr(model, 'eval'):
                model.eval()
            
            return model
            
        except Exception as e:
            raise ModelLoadError(f"Error cargando modelo PyTorch: {str(e)}")
    
    def load_tensorflow_model(self, model_path: str) -> Any:
        """
        Carga un modelo TensorFlow
        
        Args:
            model_path: Ruta al modelo TensorFlow
            
        Returns:
            Modelo cargado
            
        Raises:
            ModelLoadError: Si hay error cargando el modelo
        """
        if not TF_AVAILABLE:
            raise ModelLoadError("TensorFlow no está disponible")
        
        try:
            # Cargar modelo según el tipo de archivo
            path = Path(model_path)
            
            if path.suffix.lower() == '.h5':
                model = tf.keras.models.load_model(model_path)
            elif path.is_dir() and (path / 'saved_model.pb').exists():
                model = tf.saved_model.load(model_path)
            else:
                # Intentar cargar como SavedModel por defecto
                model = tf.saved_model.load(model_path)
            
            logger.info("Modelo TensorFlow cargado exitosamente")
            return model
            
        except Exception as e:
            raise ModelLoadError(f"Error cargando modelo TensorFlow: {str(e)}")
    
    def load_model(self, model_path: str, model_id: Optional[str] = None) -> Tuple[Any, str]:
        """
        Carga un modelo IA después de validar compatibilidad
        
        Args:
            model_path: Ruta al archivo del modelo
            model_id: ID del modelo (opcional)
            
        Returns:
            Tupla (modelo_cargado, model_id_detectado)
            
        Raises:
            ModelValidationError: Si el modelo no es compatible
            ModelLoadError: Si hay error cargando el modelo
        """
        # Validar compatibilidad primero
        is_compatible, message = self.validate_model_compatibility(model_path, model_id)
        if not is_compatible:
            raise ModelValidationError(f"Modelo no compatible: {message}")
        
        # Detectar o verificar model_id
        if not model_id:
            is_valid, model_id = self.hash_verifier.verify_model_hash(model_path)
            if not is_valid:
                raise ModelValidationError("No se pudo identificar el modelo")
        
        # Detectar framework y cargar modelo
        framework = self.detect_model_framework(model_path)
        
        try:
            if framework == ModelFramework.PYTORCH:
                model = self.load_pytorch_model(model_path)
            elif framework == ModelFramework.TENSORFLOW:
                model = self.load_tensorflow_model(model_path)
            else:
                raise ModelLoadError(f"Framework no soportado: {framework}")
            
            # Guardar referencia del modelo cargado
            self.loaded_models[model_id] = model
            
            logger.info(f"Modelo {model_id} cargado exitosamente usando {framework.value}")
            return model, model_id
            
        except Exception as e:
            if isinstance(e, (ModelLoadError, ModelValidationError)):
                raise
            else:
                raise ModelLoadError(f"Error inesperado cargando modelo: {str(e)}")
    
    def unload_model(self, model_id: str) -> bool:
        """
        Descarga un modelo de la memoria
        
        Args:
            model_id: ID del modelo a descargar
            
        Returns:
            True si se descargó exitosamente
        """
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            
            # Limpiar cache de GPU si está disponible
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info(f"Modelo {model_id} descargado de memoria")
            return True
        
        return False
    
    def get_loaded_models(self) -> Dict[str, Any]:
        """
        Obtiene la lista de modelos actualmente cargados
        
        Returns:
            Diccionario con modelos cargados
        """
        return self.loaded_models.copy()
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Obtiene información del sistema para diagnóstico
        
        Returns:
            Diccionario con información del sistema
        """
        specs = self.hardware_validator.get_system_specs()
        
        return {
            "hardware": {
                "cpu_cores": specs.cpu_cores,
                "ram_gb": specs.ram_gb,
                "gpu_available": specs.gpu_available,
                "gpu_memory_gb": specs.gpu_memory_gb,
                "gpu_name": specs.gpu_name
            },
            "frameworks": {
                "pytorch_available": TORCH_AVAILABLE,
                "tensorflow_available": TF_AVAILABLE,
                "pytorch_version": torch.__version__ if TORCH_AVAILABLE else None,
                "tensorflow_version": tf.__version__ if TF_AVAILABLE else None
            },
            "loaded_models": list(self.loaded_models.keys())
        }