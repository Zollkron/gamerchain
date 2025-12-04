"""
Módulo de verificación de modelos IA para PlayerGold
Implementa verificación de hash SHA-256 y lista blanca de modelos certificados
"""

import hashlib
import os
from typing import Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Lista blanca de hashes certificados para modelos IA aprobados
CERTIFIED_MODEL_HASHES = {
    # Gemma 3 4B
    "gemma-3-4b": {
        "hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        "name": "Gemma 3 4B",
        "min_vram_gb": 4,
        "min_ram_gb": 8,
        "min_cpu_cores": 4
    },
    # Mistral 3B
    "mistral-3b": {
        "hash": "b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567a",
        "name": "Mistral 3B", 
        "min_vram_gb": 3,
        "min_ram_gb": 6,
        "min_cpu_cores": 4
    },
    # Qwen 3 4B
    "qwen-3-4b": {
        "hash": "c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567ab2",
        "name": "Qwen 3 4B",
        "min_vram_gb": 4,
        "min_ram_gb": 8,
        "min_cpu_cores": 4
    }
}


class ModelVerificationError(Exception):
    """Excepción personalizada para errores de verificación de modelos"""
    pass


class ModelHashVerifier:
    """
    Clase para verificar hashes SHA-256 de modelos IA y validar contra lista blanca
    """
    
    def __init__(self):
        self.certified_hashes = CERTIFIED_MODEL_HASHES
        
    def calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """
        Calcula el hash SHA-256 de un archivo de modelo
        
        Args:
            file_path: Ruta al archivo del modelo
            chunk_size: Tamaño del chunk para lectura (default 8192 bytes)
            
        Returns:
            Hash SHA-256 en formato hexadecimal
            
        Raises:
            ModelVerificationError: Si el archivo no existe o no se puede leer
        """
        if not os.path.exists(file_path):
            raise ModelVerificationError(f"Archivo de modelo no encontrado: {file_path}")
            
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                # Leer archivo en chunks para manejar archivos grandes
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(chunk)
                    
            calculated_hash = sha256_hash.hexdigest()
            logger.info(f"Hash calculado para {file_path}: {calculated_hash}")
            return calculated_hash
            
        except IOError as e:
            raise ModelVerificationError(f"Error leyendo archivo de modelo {file_path}: {str(e)}")
        except Exception as e:
            raise ModelVerificationError(f"Error calculando hash para {file_path}: {str(e)}")
    
    def verify_model_hash(self, file_path: str, expected_model_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Verifica si el hash de un modelo coincide con algún modelo certificado
        
        Args:
            file_path: Ruta al archivo del modelo
            expected_model_id: ID esperado del modelo (opcional)
            
        Returns:
            Tupla (es_válido, model_id_encontrado)
            
        Raises:
            ModelVerificationError: Si hay errores en el cálculo del hash
        """
        calculated_hash = self.calculate_file_hash(file_path)
        
        # Si se especifica un modelo esperado, verificar solo ese
        if expected_model_id:
            if expected_model_id not in self.certified_hashes:
                logger.error(f"Modelo ID no reconocido: {expected_model_id}")
                return False, None
                
            expected_hash = self.certified_hashes[expected_model_id]["hash"]
            is_valid = calculated_hash == expected_hash
            
            if is_valid:
                logger.info(f"Hash verificado exitosamente para modelo {expected_model_id}")
                return True, expected_model_id
            else:
                logger.error(f"Hash no coincide para modelo {expected_model_id}. "
                           f"Esperado: {expected_hash}, Calculado: {calculated_hash}")
                return False, None
        
        # Buscar el hash en todos los modelos certificados
        for model_id, model_info in self.certified_hashes.items():
            if calculated_hash == model_info["hash"]:
                logger.info(f"Modelo identificado como {model_id} ({model_info['name']})")
                return True, model_id
                
        logger.error(f"Hash no encontrado en lista blanca: {calculated_hash}")
        return False, None
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """
        Obtiene información de un modelo certificado
        
        Args:
            model_id: ID del modelo
            
        Returns:
            Diccionario con información del modelo o None si no existe
        """
        return self.certified_hashes.get(model_id)
    
    def get_certified_models(self) -> Dict[str, Dict]:
        """
        Obtiene la lista completa de modelos certificados
        
        Returns:
            Diccionario con todos los modelos certificados
        """
        return self.certified_hashes.copy()
    
    def is_model_certified(self, model_id: str) -> bool:
        """
        Verifica si un modelo ID está en la lista de certificados
        
        Args:
            model_id: ID del modelo a verificar
            
        Returns:
            True si el modelo está certificado, False en caso contrario
        """
        return model_id in self.certified_hashes


def verify_model_file(file_path: str, expected_model_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Función de conveniencia para verificar un archivo de modelo
    
    Args:
        file_path: Ruta al archivo del modelo
        expected_model_id: ID esperado del modelo (opcional)
        
    Returns:
        Tupla (es_válido, model_id_encontrado)
    """
    verifier = ModelHashVerifier()
    return verifier.verify_model_hash(file_path, expected_model_id)


def calculate_model_hash(file_path: str) -> str:
    """
    Función de conveniencia para calcular el hash de un modelo
    
    Args:
        file_path: Ruta al archivo del modelo
        
    Returns:
        Hash SHA-256 en formato hexadecimal
    """
    verifier = ModelHashVerifier()
    return verifier.calculate_file_hash(file_path)