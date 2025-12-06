"""
Script para actualizar información del proyecto en todos los archivos

Actualiza:
- playergold.com -> playergold.es
- PlayerGold Team -> Zollkron
- dev@playergold.com -> (eliminar o actualizar)
- github.com/playergold -> github.com/Zollkron/gamerchain
"""

import os
import re
from pathlib import Path

# Mapeo de reemplazos
REPLACEMENTS = {
    # URLs
    r'playergold\.com': 'playergold.es',
    r'https://github\.com/playergold/playergold': 'https://github.com/Zollkron/gamerchain',
    r'github\.com/playergold/wallet-desktop': 'github.com/Zollkron/gamerchain',
    
    # Equipo/Autor
    r'PlayerGold Team': 'Zollkron',
    r'Autores:.*PlayerGold.*Team': 'Desarrollador: Zollkron',
    
    # Emails (comentar o eliminar)
    r'dev@playergold\.com': 'github.com/Zollkron',
    r'support@playergold\.com': 'github.com/Zollkron/gamerchain/issues',
}

# Archivos a excluir
EXCLUDE_PATTERNS = [
    '*.pyc',
    '__pycache__',
    '.git',
    'node_modules',
    '.pytest_cache',
    'dist',
    'build',
    '*.egg-info',
    'update_project_info.py'  # Este script
]

# Extensiones de archivo a procesar
INCLUDE_EXTENSIONS = [
    '.md', '.py', '.js', '.yaml', '.yml', '.toml', 
    '.json', '.txt', '.html', '.css', '.cpp', '.h', '.cs'
]

def should_process_file(file_path):
    """Determina si un archivo debe ser procesado"""
    # Verificar extensión
    if not any(str(file_path).endswith(ext) for ext in INCLUDE_EXTENSIONS):
        return False
    
    # Verificar patrones de exclusión
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(file_path):
            return False
    
    return True

def update_file(file_path):
    """Actualiza un archivo con los reemplazos"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Aplicar reemplazos
        for pattern, replacement in REPLACEMENTS.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"  - {pattern} -> {replacement}")
        
        # Si hubo cambios, escribir el archivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Actualizado: {file_path}")
            for change in changes_made:
                print(change)
            return True
        
        return False
        
    except Exception as e:
        print(f"✗ Error procesando {file_path}: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("Actualizando información del proyecto PlayerGold")
    print("=" * 60)
    print()
    
    # Obtener directorio raíz del proyecto
    root_dir = Path(__file__).parent
    
    files_updated = 0
    files_processed = 0
    
    # Recorrer todos los archivos
    for file_path in root_dir.rglob('*'):
        if file_path.is_file() and should_process_file(file_path):
            files_processed += 1
            if update_file(file_path):
                files_updated += 1
    
    print()
    print("=" * 60)
    print(f"Proceso completado:")
    print(f"  - Archivos procesados: {files_processed}")
    print(f"  - Archivos actualizados: {files_updated}")
    print("=" * 60)

if __name__ == "__main__":
    main()
