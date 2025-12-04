"""
Tests unitarios para el cargador y validador de modelos IA
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from src.ai_nodes.model_loader import (
    AIModelLoader,
    HardwareValidator,
    HardwareSpecs,
    ModelRequirements,
    ModelFramework,
    ModelLoadError,
    ModelValidationError,
    TORCH_AVAILABLE,
    TF_AVAILABLE
)


class TestHardwareSpecs:
    """Tests para la clase HardwareSpecs"""
    
    def test_hardware_specs_creation(self):
        """Test creación de HardwareSpecs"""
        specs = HardwareSpecs(
            cpu_cores=8,
            ram_gb=16.0,
            gpu_available=True,
            gpu_memory_gb=8.0,
            gpu_name="RTX 3070"
        )
        
        assert specs.cpu_cores == 8
        assert specs.ram_gb == 16.0
        assert specs.gpu_available is True
        assert specs.gpu_memory_gb == 8.0
        assert specs.gpu_name == "RTX 3070"


class TestModelRequirements:
    """Tests para la clase ModelRequirements"""
    
    def test_model_requirements_creation(self):
        """Test creación de ModelRequirements"""
        req = ModelRequirements(
            min_cpu_cores=4,
            min_ram_gb=8,
            min_vram_gb=4,
            framework=ModelFramework.PYTORCH,
            model_size_mb=1024
        )
        
        assert req.min_cpu_cores == 4
        assert req.min_ram_gb == 8
        assert req.min_vram_gb == 4
        assert req.framework == ModelFramework.PYTORCH
        assert req.model_size_mb == 1024


class TestHardwareValidator:
    """Tests para la clase HardwareValidator"""
    
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('src.ai_nodes.model_loader.TORCH_AVAILABLE', True)
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    @patch('torch.cuda.get_device_name')
    def test_get_system_specs_with_gpu(self, mock_gpu_name, mock_gpu_props, mock_cuda_available, 
                                      mock_memory, mock_cpu_count):
        """Test obtener especificaciones del sistema con GPU"""
        # Mock CPU
        mock_cpu_count.return_value = 8
        
        # Mock RAM (16GB)
        mock_memory_obj = MagicMock()
        mock_memory_obj.total = 16 * 1024**3
        mock_memory.return_value = mock_memory_obj
        
        # Mock GPU
        mock_cuda_available.return_value = True
        mock_gpu_props_obj = MagicMock()
        mock_gpu_props_obj.total_memory = 8 * 1024**3
        mock_gpu_props.return_value = mock_gpu_props_obj
        mock_gpu_name.return_value = "RTX 3070"
        
        specs = HardwareValidator.get_system_specs()
        
        assert specs.cpu_cores == 8
        assert specs.ram_gb == 16.0
        assert specs.gpu_available is True
        assert specs.gpu_memory_gb == 8.0
        assert specs.gpu_name == "RTX 3070"
    
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('src.ai_nodes.model_loader.TORCH_AVAILABLE', False)
    @patch('src.ai_nodes.model_loader.TF_AVAILABLE', False)
    def test_get_system_specs_no_gpu(self, mock_memory, mock_cpu_count):
        """Test obtener especificaciones del sistema sin GPU"""
        # Mock CPU
        mock_cpu_count.return_value = 4
        
        # Mock RAM (8GB)
        mock_memory_obj = MagicMock()
        mock_memory_obj.total = 8 * 1024**3
        mock_memory.return_value = mock_memory_obj
        
        specs = HardwareValidator.get_system_specs()
        
        assert specs.cpu_cores == 4
        assert specs.ram_gb == 8.0
        assert specs.gpu_available is False
        assert specs.gpu_memory_gb == 0.0
        assert specs.gpu_name is None
    
    def test_validate_hardware_requirements_success(self):
        """Test validación exitosa de requisitos de hardware"""
        specs = HardwareSpecs(
            cpu_cores=8,
            ram_gb=16.0,
            gpu_available=True,
            gpu_memory_gb=8.0
        )
        
        requirements = ModelRequirements(
            min_cpu_cores=4,
            min_ram_gb=8,
            min_vram_gb=4,
            framework=ModelFramework.PYTORCH
        )
        
        is_valid, message = HardwareValidator.validate_hardware_requirements(specs, requirements)
        
        assert is_valid is True
        assert "cumple todos los requisitos" in message
    
    def test_validate_hardware_requirements_insufficient_cpu(self):
        """Test validación fallida por CPU insuficiente"""
        specs = HardwareSpecs(
            cpu_cores=2,
            ram_gb=16.0,
            gpu_available=True,
            gpu_memory_gb=8.0
        )
        
        requirements = ModelRequirements(
            min_cpu_cores=4,
            min_ram_gb=8,
            min_vram_gb=4,
            framework=ModelFramework.PYTORCH
        )
        
        is_valid, message = HardwareValidator.validate_hardware_requirements(specs, requirements)
        
        assert is_valid is False
        assert "CPU insuficiente" in message
    
    def test_validate_hardware_requirements_insufficient_ram(self):
        """Test validación fallida por RAM insuficiente"""
        specs = HardwareSpecs(
            cpu_cores=8,
            ram_gb=4.0,
            gpu_available=True,
            gpu_memory_gb=8.0
        )
        
        requirements = ModelRequirements(
            min_cpu_cores=4,
            min_ram_gb=8,
            min_vram_gb=4,
            framework=ModelFramework.PYTORCH
        )
        
        is_valid, message = HardwareValidator.validate_hardware_requirements(specs, requirements)
        
        assert is_valid is False
        assert "RAM insuficiente" in message
    
    def test_validate_hardware_requirements_no_gpu(self):
        """Test validación fallida por GPU no disponible"""
        specs = HardwareSpecs(
            cpu_cores=8,
            ram_gb=16.0,
            gpu_available=False,
            gpu_memory_gb=0.0
        )
        
        requirements = ModelRequirements(
            min_cpu_cores=4,
            min_ram_gb=8,
            min_vram_gb=4,
            framework=ModelFramework.PYTORCH
        )
        
        is_valid, message = HardwareValidator.validate_hardware_requirements(specs, requirements)
        
        assert is_valid is False
        assert "GPU requerida pero no disponible" in message
    
    def test_validate_hardware_requirements_insufficient_vram(self):
        """Test validación fallida por VRAM insuficiente"""
        specs = HardwareSpecs(
            cpu_cores=8,
            ram_gb=16.0,
            gpu_available=True,
            gpu_memory_gb=2.0
        )
        
        requirements = ModelRequirements(
            min_cpu_cores=4,
            min_ram_gb=8,
            min_vram_gb=4,
            framework=ModelFramework.PYTORCH
        )
        
        is_valid, message = HardwareValidator.validate_hardware_requirements(specs, requirements)
        
        assert is_valid is False
        assert "VRAM insuficiente" in message


class TestAIModelLoader:
    """Tests para la clase AIModelLoader"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.loader = AIModelLoader()
    
    def test_init(self):
        """Test inicialización del loader"""
        assert self.loader.hash_verifier is not None
        assert self.loader.hardware_validator is not None
        assert isinstance(self.loader.loaded_models, dict)
        assert len(self.loader.loaded_models) == 0
    
    def test_detect_model_framework_pytorch(self):
        """Test detección de framework PyTorch"""
        assert self.loader.detect_model_framework("model.pt") == ModelFramework.PYTORCH
        assert self.loader.detect_model_framework("model.pth") == ModelFramework.PYTORCH
        assert self.loader.detect_model_framework("model.pytorch") == ModelFramework.PYTORCH
    
    def test_detect_model_framework_tensorflow(self):
        """Test detección de framework TensorFlow"""
        assert self.loader.detect_model_framework("model.pb") == ModelFramework.TENSORFLOW
        assert self.loader.detect_model_framework("model.h5") == ModelFramework.TENSORFLOW
        assert self.loader.detect_model_framework("model.keras") == ModelFramework.TENSORFLOW
    
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.exists')
    def test_detect_model_framework_tensorflow_savedmodel(self, mock_exists, mock_is_dir):
        """Test detección de TensorFlow SavedModel"""
        mock_is_dir.return_value = True
        mock_exists.return_value = True
        
        framework = self.loader.detect_model_framework("/path/to/savedmodel")
        assert framework == ModelFramework.TENSORFLOW
    
    def test_detect_model_framework_unknown(self):
        """Test detección de framework desconocido"""
        assert self.loader.detect_model_framework("model.unknown") == ModelFramework.UNKNOWN
    
    def test_get_model_requirements_existing(self):
        """Test obtener requisitos de modelo existente"""
        with patch.object(self.loader.hash_verifier, 'get_model_info') as mock_get_info:
            mock_get_info.return_value = {
                "min_cpu_cores": 4,
                "min_ram_gb": 8,
                "min_vram_gb": 4
            }
            
            requirements = self.loader.get_model_requirements("gemma-3-4b")
            
            assert requirements is not None
            assert requirements.min_cpu_cores == 4
            assert requirements.min_ram_gb == 8
            assert requirements.min_vram_gb == 4
            assert requirements.framework == ModelFramework.PYTORCH
    
    def test_get_model_requirements_non_existing(self):
        """Test obtener requisitos de modelo no existente"""
        with patch.object(self.loader.hash_verifier, 'get_model_info') as mock_get_info:
            mock_get_info.return_value = None
            
            requirements = self.loader.get_model_requirements("non-existing")
            assert requirements is None
    
    @patch('os.path.exists')
    def test_validate_model_compatibility_success(self, mock_exists):
        """Test validación exitosa de compatibilidad de modelo"""
        # Setup mocks
        mock_exists.return_value = True
        
        with patch.object(self.loader.hash_verifier, 'verify_model_hash') as mock_verify, \
             patch.object(self.loader, 'get_model_requirements') as mock_get_req, \
             patch.object(self.loader, 'detect_model_framework') as mock_detect, \
             patch.object(self.loader.hardware_validator, 'get_system_specs') as mock_get_specs, \
             patch.object(self.loader.hardware_validator, 'validate_hardware_requirements') as mock_validate_hw, \
             patch('src.ai_nodes.model_loader.TORCH_AVAILABLE', True):
            
            mock_verify.return_value = (True, "gemma-3-4b")
            mock_get_req.return_value = ModelRequirements(4, 8, 4, ModelFramework.PYTORCH)
            mock_detect.return_value = ModelFramework.PYTORCH
            mock_get_specs.return_value = HardwareSpecs(8, 16.0, True, 8.0)
            mock_validate_hw.return_value = (True, "OK")
            
            is_compatible, message = self.loader.validate_model_compatibility("/fake/path/model.pt")
        
        assert is_compatible is True
        assert "compatible con el sistema" in message
    
    @patch('os.path.exists')
    def test_validate_model_compatibility_file_not_found(self, mock_exists):
        """Test validación fallida por archivo no encontrado"""
        mock_exists.return_value = False
        
        is_compatible, message = self.loader.validate_model_compatibility("/fake/path/model.pt")
        
        assert is_compatible is False
        assert "no encontrado" in message
    
    @patch('os.path.exists')
    def test_validate_model_compatibility_invalid_hash(self, mock_exists):
        """Test validación fallida por hash inválido"""
        mock_exists.return_value = True
        
        with patch.object(self.loader.hash_verifier, 'verify_model_hash') as mock_verify:
            mock_verify.return_value = (False, None)
            
            is_compatible, message = self.loader.validate_model_compatibility("/fake/path/model.pt")
            
            assert is_compatible is False
            assert "no está en la lista" in message
    
    @patch('src.ai_nodes.model_loader.TORCH_AVAILABLE', True)
    def test_load_pytorch_model_success(self):
        """Test carga exitosa de modelo PyTorch"""
        mock_model = MagicMock()
        mock_model.eval = MagicMock()
        
        with patch('torch.load', return_value=mock_model), \
             patch('torch.cuda.is_available', return_value=False):
            
            loaded_model = self.loader.load_pytorch_model("/fake/path/model.pt")
            
            assert loaded_model == mock_model
            mock_model.eval.assert_called_once()
    
    @patch('src.ai_nodes.model_loader.TORCH_AVAILABLE', False)
    def test_load_pytorch_model_torch_not_available(self):
        """Test error cuando PyTorch no está disponible"""
        with pytest.raises(ModelLoadError, match="PyTorch no está disponible"):
            self.loader.load_pytorch_model("/fake/path/model.pt")
    
    @patch('src.ai_nodes.model_loader.TORCH_AVAILABLE', True)
    def test_load_pytorch_model_load_error(self):
        """Test error al cargar modelo PyTorch"""
        with patch('torch.load', side_effect=Exception("Load failed")):
            with pytest.raises(ModelLoadError, match="Error cargando modelo PyTorch"):
                self.loader.load_pytorch_model("/fake/path/model.pt")
    
    @pytest.mark.skipif(not TF_AVAILABLE, reason="TensorFlow not available")
    def test_load_tensorflow_model_h5_success(self):
        """Test carga exitosa de modelo TensorFlow H5"""
        pytest.skip("TensorFlow not installed - skipping TensorFlow specific test")
    
    @patch('src.ai_nodes.model_loader.TF_AVAILABLE', False)
    def test_load_tensorflow_model_tf_not_available(self):
        """Test error cuando TensorFlow no está disponible"""
        with pytest.raises(ModelLoadError, match="TensorFlow no está disponible"):
            self.loader.load_tensorflow_model("/fake/path/model.h5")
    
    def test_load_model_success(self):
        """Test carga exitosa de modelo completa"""
        mock_model = MagicMock()
        
        with patch.object(self.loader, 'validate_model_compatibility') as mock_validate, \
             patch.object(self.loader.hash_verifier, 'verify_model_hash') as mock_verify, \
             patch.object(self.loader, 'detect_model_framework') as mock_detect, \
             patch.object(self.loader, 'load_pytorch_model') as mock_load_pytorch:
            
            mock_validate.return_value = (True, "Compatible")
            mock_verify.return_value = (True, "gemma-3-4b")
            mock_detect.return_value = ModelFramework.PYTORCH
            mock_load_pytorch.return_value = mock_model
            
            loaded_model, model_id = self.loader.load_model("/fake/path/model.pt")
            
            assert loaded_model == mock_model
            assert model_id == "gemma-3-4b"
            assert "gemma-3-4b" in self.loader.loaded_models
    
    def test_load_model_validation_error(self):
        """Test error de validación al cargar modelo"""
        with patch.object(self.loader, 'validate_model_compatibility') as mock_validate:
            mock_validate.return_value = (False, "Not compatible")
            
            with pytest.raises(ModelValidationError, match="Modelo no compatible"):
                self.loader.load_model("/fake/path/model.pt")
    
    def test_unload_model_success(self):
        """Test descarga exitosa de modelo"""
        # Simular modelo cargado
        self.loader.loaded_models["test-model"] = MagicMock()
        
        with patch('src.ai_nodes.model_loader.TORCH_AVAILABLE', True), \
             patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.empty_cache') as mock_empty_cache:
            
            result = self.loader.unload_model("test-model")
            
            assert result is True
            assert "test-model" not in self.loader.loaded_models
            mock_empty_cache.assert_called_once()
    
    def test_unload_model_not_loaded(self):
        """Test descarga de modelo no cargado"""
        result = self.loader.unload_model("non-existing-model")
        assert result is False
    
    def test_get_loaded_models(self):
        """Test obtener modelos cargados"""
        # Simular modelos cargados
        self.loader.loaded_models["model1"] = MagicMock()
        self.loader.loaded_models["model2"] = MagicMock()
        
        loaded = self.loader.get_loaded_models()
        
        assert len(loaded) == 2
        assert "model1" in loaded
        assert "model2" in loaded
        
        # Verificar que es una copia
        loaded["model3"] = MagicMock()
        assert "model3" not in self.loader.loaded_models
    
    def test_get_system_info(self):
        """Test obtener información del sistema"""
        # Simular modelo cargado
        self.loader.loaded_models["test-model"] = MagicMock()
        
        with patch.object(self.loader.hardware_validator, 'get_system_specs') as mock_get_specs, \
             patch('src.ai_nodes.model_loader.TORCH_AVAILABLE', True), \
             patch('src.ai_nodes.model_loader.TF_AVAILABLE', False), \
             patch('src.ai_nodes.model_loader.torch.__version__', "1.12.0"):
            
            mock_get_specs.return_value = HardwareSpecs(
                cpu_cores=8,
                ram_gb=16.0,
                gpu_available=True,
                gpu_memory_gb=8.0,
                gpu_name="RTX 3070"
            )
            
            info = self.loader.get_system_info()
        
        assert info["hardware"]["cpu_cores"] == 8
        assert info["hardware"]["ram_gb"] == 16.0
        assert info["hardware"]["gpu_available"] is True
        assert info["frameworks"]["pytorch_available"] is True
        assert info["frameworks"]["tensorflow_available"] is False
        assert info["frameworks"]["pytorch_version"] == "1.12.0"
        assert "test-model" in info["loaded_models"]


if __name__ == "__main__":
    pytest.main([__file__])