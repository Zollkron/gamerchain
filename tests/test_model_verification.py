"""
Tests unitarios para el módulo de verificación de modelos IA
"""

import os
import tempfile
import hashlib
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

from src.ai_nodes.model_verification import (
    ModelHashVerifier,
    ModelVerificationError,
    CERTIFIED_MODEL_HASHES,
    verify_model_file,
    calculate_model_hash
)


class TestModelHashVerifier:
    """Tests para la clase ModelHashVerifier"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.verifier = ModelHashVerifier()
        
    def test_init(self):
        """Test inicialización del verificador"""
        assert self.verifier.certified_hashes == CERTIFIED_MODEL_HASHES
        assert len(self.verifier.certified_hashes) == 3
        assert "gemma-3-4b" in self.verifier.certified_hashes
        assert "mistral-3b" in self.verifier.certified_hashes
        assert "qwen-3-4b" in self.verifier.certified_hashes
    
    def test_calculate_file_hash_success(self):
        """Test cálculo exitoso de hash de archivo"""
        # Crear archivo temporal con contenido conocido
        test_content = b"test model content for hash calculation"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
            
        try:
            calculated_hash = self.verifier.calculate_file_hash(temp_file_path)
            assert calculated_hash == expected_hash
        finally:
            os.unlink(temp_file_path)
    
    def test_calculate_file_hash_file_not_found(self):
        """Test error cuando archivo no existe"""
        with pytest.raises(ModelVerificationError, match="Archivo de modelo no encontrado"):
            self.verifier.calculate_file_hash("/path/that/does/not/exist")
    
    def test_calculate_file_hash_large_file(self):
        """Test cálculo de hash para archivo grande (usando chunks)"""
        # Crear archivo de 20KB para probar lectura por chunks
        test_content = b"x" * 20480  # 20KB
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
            
        try:
            calculated_hash = self.verifier.calculate_file_hash(temp_file_path, chunk_size=1024)
            assert calculated_hash == expected_hash
        finally:
            os.unlink(temp_file_path)
    
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_calculate_file_hash_io_error(self, mock_file, mock_exists):
        """Test error de IO al leer archivo"""
        with pytest.raises(ModelVerificationError, match="Error leyendo archivo de modelo"):
            self.verifier.calculate_file_hash("some_file.bin")
    
    def test_verify_model_hash_with_expected_model_valid(self):
        """Test verificación exitosa con modelo esperado específico"""
        # Usar hash conocido de gemma-3-4b
        expected_hash = CERTIFIED_MODEL_HASHES["gemma-3-4b"]["hash"]
        test_content = b"fake gemma model content"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
            
        try:
            # Mock el cálculo de hash para devolver el hash esperado
            with patch.object(self.verifier, 'calculate_file_hash', return_value=expected_hash):
                is_valid, model_id = self.verifier.verify_model_hash(temp_file_path, "gemma-3-4b")
                assert is_valid is True
                assert model_id == "gemma-3-4b"
        finally:
            os.unlink(temp_file_path)
    
    def test_verify_model_hash_with_expected_model_invalid(self):
        """Test verificación fallida con modelo esperado específico"""
        wrong_hash = "wrong_hash_value"
        test_content = b"fake model content"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
            
        try:
            with patch.object(self.verifier, 'calculate_file_hash', return_value=wrong_hash):
                is_valid, model_id = self.verifier.verify_model_hash(temp_file_path, "gemma-3-4b")
                assert is_valid is False
                assert model_id is None
        finally:
            os.unlink(temp_file_path)
    
    def test_verify_model_hash_unknown_expected_model(self):
        """Test verificación con modelo esperado no reconocido"""
        test_content = b"fake model content"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
            
        try:
            is_valid, model_id = self.verifier.verify_model_hash(temp_file_path, "unknown-model")
            assert is_valid is False
            assert model_id is None
        finally:
            os.unlink(temp_file_path)
    
    def test_verify_model_hash_auto_detect_valid(self):
        """Test auto-detección exitosa de modelo por hash"""
        # Usar hash conocido de mistral-3b
        expected_hash = CERTIFIED_MODEL_HASHES["mistral-3b"]["hash"]
        test_content = b"fake mistral model content"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
            
        try:
            with patch.object(self.verifier, 'calculate_file_hash', return_value=expected_hash):
                is_valid, model_id = self.verifier.verify_model_hash(temp_file_path)
                assert is_valid is True
                assert model_id == "mistral-3b"
        finally:
            os.unlink(temp_file_path)
    
    def test_verify_model_hash_auto_detect_invalid(self):
        """Test auto-detección fallida con hash no certificado"""
        unknown_hash = "unknown_hash_not_in_whitelist"
        test_content = b"fake unknown model content"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
            
        try:
            with patch.object(self.verifier, 'calculate_file_hash', return_value=unknown_hash):
                is_valid, model_id = self.verifier.verify_model_hash(temp_file_path)
                assert is_valid is False
                assert model_id is None
        finally:
            os.unlink(temp_file_path)
    
    def test_get_model_info_existing(self):
        """Test obtener información de modelo existente"""
        info = self.verifier.get_model_info("gemma-3-4b")
        assert info is not None
        assert info["name"] == "Gemma 3 4B"
        assert info["min_vram_gb"] == 4
        assert info["min_ram_gb"] == 8
        assert info["min_cpu_cores"] == 4
        assert "hash" in info
    
    def test_get_model_info_non_existing(self):
        """Test obtener información de modelo no existente"""
        info = self.verifier.get_model_info("non-existing-model")
        assert info is None
    
    def test_get_certified_models(self):
        """Test obtener lista completa de modelos certificados"""
        models = self.verifier.get_certified_models()
        assert len(models) == 3
        assert "gemma-3-4b" in models
        assert "mistral-3b" in models
        assert "qwen-3-4b" in models
        
        # Verificar que es una copia (no referencia)
        models["test"] = "value"
        assert "test" not in self.verifier.certified_hashes
    
    def test_is_model_certified_true(self):
        """Test verificar si modelo está certificado (verdadero)"""
        assert self.verifier.is_model_certified("gemma-3-4b") is True
        assert self.verifier.is_model_certified("mistral-3b") is True
        assert self.verifier.is_model_certified("qwen-3-4b") is True
    
    def test_is_model_certified_false(self):
        """Test verificar si modelo está certificado (falso)"""
        assert self.verifier.is_model_certified("unknown-model") is False
        assert self.verifier.is_model_certified("") is False
        assert self.verifier.is_model_certified("gemma-2-7b") is False


class TestConvenienceFunctions:
    """Tests para las funciones de conveniencia"""
    
    def test_verify_model_file_success(self):
        """Test función de conveniencia verify_model_file exitosa"""
        expected_hash = CERTIFIED_MODEL_HASHES["qwen-3-4b"]["hash"]
        
        with patch('src.ai_nodes.model_verification.ModelHashVerifier') as mock_verifier_class:
            mock_verifier = mock_verifier_class.return_value
            mock_verifier.verify_model_hash.return_value = (True, "qwen-3-4b")
            
            is_valid, model_id = verify_model_file("/fake/path/model.bin", "qwen-3-4b")
            
            assert is_valid is True
            assert model_id == "qwen-3-4b"
            mock_verifier.verify_model_hash.assert_called_once_with("/fake/path/model.bin", "qwen-3-4b")
    
    def test_calculate_model_hash_success(self):
        """Test función de conveniencia calculate_model_hash exitosa"""
        expected_hash = "abc123def456"
        
        with patch('src.ai_nodes.model_verification.ModelHashVerifier') as mock_verifier_class:
            mock_verifier = mock_verifier_class.return_value
            mock_verifier.calculate_file_hash.return_value = expected_hash
            
            result_hash = calculate_model_hash("/fake/path/model.bin")
            
            assert result_hash == expected_hash
            mock_verifier.calculate_file_hash.assert_called_once_with("/fake/path/model.bin")


class TestCertifiedModelHashes:
    """Tests para la configuración de hashes certificados"""
    
    def test_certified_hashes_structure(self):
        """Test estructura correcta de hashes certificados"""
        assert isinstance(CERTIFIED_MODEL_HASHES, dict)
        assert len(CERTIFIED_MODEL_HASHES) > 0
        
        for model_id, model_info in CERTIFIED_MODEL_HASHES.items():
            assert isinstance(model_id, str)
            assert isinstance(model_info, dict)
            
            # Verificar campos requeridos
            required_fields = ["hash", "name", "min_vram_gb", "min_ram_gb", "min_cpu_cores"]
            for field in required_fields:
                assert field in model_info, f"Campo {field} faltante en modelo {model_id}"
            
            # Verificar tipos de datos
            assert isinstance(model_info["hash"], str)
            assert isinstance(model_info["name"], str)
            assert isinstance(model_info["min_vram_gb"], int)
            assert isinstance(model_info["min_ram_gb"], int)
            assert isinstance(model_info["min_cpu_cores"], int)
            
            # Verificar longitud del hash (SHA-256 = 64 caracteres hex)
            assert len(model_info["hash"]) == 64
            
            # Verificar que el hash solo contiene caracteres hexadecimales
            assert all(c in "0123456789abcdef" for c in model_info["hash"].lower())
    
    def test_certified_hashes_uniqueness(self):
        """Test que todos los hashes certificados sean únicos"""
        hashes = [info["hash"] for info in CERTIFIED_MODEL_HASHES.values()]
        assert len(hashes) == len(set(hashes)), "Hashes duplicados encontrados"
    
    def test_certified_hashes_reasonable_requirements(self):
        """Test que los requisitos de hardware sean razonables"""
        for model_id, model_info in CERTIFIED_MODEL_HASHES.items():
            # VRAM entre 1GB y 32GB
            assert 1 <= model_info["min_vram_gb"] <= 32
            
            # RAM entre 4GB y 128GB
            assert 4 <= model_info["min_ram_gb"] <= 128
            
            # CPU cores entre 2 y 64
            assert 2 <= model_info["min_cpu_cores"] <= 64


if __name__ == "__main__":
    pytest.main([__file__])