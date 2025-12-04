#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de verificación de modelos IA de PlayerGold
Demuestra cómo verificar y cargar modelos IA certificados
"""

import sys
import os
from pathlib import Path

# Añadir el directorio src al path para importar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ai_nodes import (
    AIModelLoader,
    ModelHashVerifier,
    CERTIFIED_MODEL_HASHES,
    verify_model_file,
    calculate_model_hash
)


def main():
    """Función principal del ejemplo"""
    print("=== Sistema de Verificación de Modelos IA - PlayerGold ===\n")
    
    # 1. Mostrar modelos certificados disponibles
    print("1. Modelos IA certificados disponibles:")
    print("-" * 50)
    
    verifier = ModelHashVerifier()
    certified_models = verifier.get_certified_models()
    
    for model_id, model_info in certified_models.items():
        print(f"• {model_info['name']} ({model_id})")
        print(f"  - Hash: {model_info['hash'][:16]}...")
        print(f"  - Requisitos: {model_info['min_cpu_cores']} cores, "
              f"{model_info['min_ram_gb']}GB RAM, {model_info['min_vram_gb']}GB VRAM")
        print()
    
    # 2. Verificar especificaciones del sistema
    print("2. Especificaciones del sistema actual:")
    print("-" * 50)
    
    loader = AIModelLoader()
    system_info = loader.get_system_info()
    
    hw_info = system_info['hardware']
    print(f"• CPU: {hw_info['cpu_cores']} cores")
    print(f"• RAM: {hw_info['ram_gb']:.1f} GB")
    print(f"• GPU disponible: {'Sí' if hw_info['gpu_available'] else 'No'}")
    if hw_info['gpu_available']:
        print(f"• GPU: {hw_info['gpu_name']} ({hw_info['gpu_memory_gb']:.1f} GB VRAM)")
    
    fw_info = system_info['frameworks']
    print(f"• PyTorch: {'Disponible' if fw_info['pytorch_available'] else 'No disponible'}")
    if fw_info['pytorch_version']:
        print(f"  Versión: {fw_info['pytorch_version']}")
    print(f"• TensorFlow: {'Disponible' if fw_info['tensorflow_available'] else 'No disponible'}")
    if fw_info['tensorflow_version']:
        print(f"  Versión: {fw_info['tensorflow_version']}")
    print()
    
    # 3. Verificar compatibilidad con modelos certificados
    print("3. Compatibilidad con modelos certificados:")
    print("-" * 50)
    
    for model_id, model_info in certified_models.items():
        requirements = loader.get_model_requirements(model_id)
        if requirements:
            # Simular verificación de compatibilidad (sin archivo real)
            hw_specs = loader.hardware_validator.get_system_specs()
            is_compatible, message = loader.hardware_validator.validate_hardware_requirements(
                hw_specs, requirements
            )
            
            status = "✓ Compatible" if is_compatible else "✗ No compatible"
            print(f"• {model_info['name']}: {status}")
            if not is_compatible:
                print(f"  Razón: {message}")
        print()
    
    # 4. Ejemplo de verificación de hash (archivo ficticio)
    print("4. Ejemplo de verificación de hash:")
    print("-" * 50)
    
    # Crear un archivo temporal para demostrar el cálculo de hash
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pt') as temp_file:
        temp_file.write(b"Contenido de ejemplo de modelo IA")
        temp_file_path = temp_file.name
    
    try:
        # Calcular hash del archivo de ejemplo
        calculated_hash = calculate_model_hash(temp_file_path)
        print(f"• Archivo de ejemplo: {temp_file_path}")
        print(f"• Hash calculado: {calculated_hash}")
        
        # Verificar si coincide con algún modelo certificado
        is_valid, model_id = verify_model_file(temp_file_path)
        if is_valid:
            print(f"• ✓ Modelo identificado como: {model_id}")
        else:
            print("• ✗ Hash no coincide con ningún modelo certificado")
            print("  (Esto es esperado para el archivo de ejemplo)")
        
    finally:
        # Limpiar archivo temporal
        os.unlink(temp_file_path)
    
    print("\n=== Ejemplo completado ===")
    print("\nPara usar el sistema con modelos reales:")
    print("1. Descarga un modelo certificado (Gemma 3 4B, Mistral 3B, o Qwen 3 4B)")
    print("2. Usa verify_model_file() para verificar su autenticidad")
    print("3. Usa AIModelLoader.load_model() para cargarlo si es válido")


if __name__ == "__main__":
    main()