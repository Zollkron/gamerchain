#!/usr/bin/env python3
"""
PlayerGold Wallet - AES Certificate Installation

Este script instala el certificado AES descargado del coordinador
en el directorio wallet/.AES_certificate/

Uso: python3 install_wallet_aes_certificate.py [ruta_del_paquete]
"""

import os
import sys
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

def log(message):
    """Log con timestamp"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def error(message):
    """Error log"""
    print(f"❌ ERROR: {message}", file=sys.stderr)

def success(message):
    """Success log"""
    print(f"✅ {message}")

def warning(message):
    """Warning log"""
    print(f"⚠️  {message}")

def find_wallet_directory():
    """Encontrar el directorio de la wallet"""
    possible_locations = [
        "./wallet",
        "../wallet",
        "../../wallet",
        "./",
    ]
    
    for location in possible_locations:
        wallet_path = os.path.abspath(location)
        if os.path.exists(wallet_path) and (
            os.path.exists(f"{wallet_path}/package.json") or
            os.path.exists(f"{wallet_path}/src") or
            "wallet" in wallet_path.lower()
        ):
            return wallet_path
    
    return None

def verify_certificate_package(package_path):
    """Verificar que el paquete del certificado es válido"""
    log(f"Verificando paquete: {package_path}")
    
    required_files = [
        "master_key.bin",
        "certificate_info.json",
        "public_key.pem"
    ]
    
    for file_name in required_files:
        file_path = os.path.join(package_path, file_name)
        if not os.path.exists(file_path):
            error(f"Archivo requerido no encontrado: {file_name}")
            return False
    
    # Verificar master_key.bin
    master_key_path = os.path.join(package_path, "master_key.bin")
    with open(master_key_path, 'rb') as f:
        master_key = f.read()
    
    if len(master_key) != 32:
        error(f"master_key.bin tiene tamaño incorrecto: {len(master_key)} bytes (esperado: 32)")
        return False
    
    # Verificar certificate_info.json
    cert_info_path = os.path.join(package_path, "certificate_info.json")
    try:
        with open(cert_info_path, 'r') as f:
            cert_info = json.load(f)
        
        required_fields = ["version", "created_at", "master_key_hash", "algorithm"]
        for field in required_fields:
            if field not in cert_info:
                error(f"Campo requerido no encontrado en certificate_info.json: {field}")
                return False
        
        # Verificar hash de la clave
        expected_hash = cert_info["master_key_hash"]
        actual_hash = hashlib.sha256(master_key).hexdigest()
        
        if expected_hash != actual_hash:
            error("Hash de master_key no coincide con certificate_info.json")
            return False
        
        success("Paquete del certificado verificado correctamente")
        return True, cert_info
        
    except json.JSONDecodeError as e:
        error(f"certificate_info.json no es válido: {e}")
        return False
    except Exception as e:
        error(f"Error verificando certificado: {e}")
        return False

def create_wallet_certificate_directory(wallet_path):
    """Crear directorio del certificado en la wallet"""
    cert_dir = os.path.join(wallet_path, ".AES_certificate")
    
    log(f"Creando directorio del certificado: {cert_dir}")
    
    # Crear directorio (oculto) con permisos seguros
    os.makedirs(cert_dir, mode=0o700, exist_ok=True)
    
    success(f"Directorio creado: {cert_dir}")
    return cert_dir

def install_certificate(package_path, cert_dir):
    """Instalar certificado en la wallet"""
    log("Instalando certificado AES en la wallet...")
    
    files_to_copy = [
        "master_key.bin",
        "certificate_info.json",
        "public_key.pem"
    ]
    
    for file_name in files_to_copy:
        src = os.path.join(package_path, file_name)
        dst = os.path.join(cert_dir, file_name)
        
        # Copiar archivo
        shutil.copy2(src, dst)
        
        # Establecer permisos seguros
        if file_name == "master_key.bin":
            os.chmod(dst, 0o600)  # Solo propietario puede leer/escribir
        else:
            os.chmod(dst, 0o644)  # Propietario puede leer/escribir, otros solo leer
        
        log(f"Instalado: {file_name}")
    
    success("Certificado instalado correctamente")

def update_wallet_gitignore(wallet_path):
    """Actualizar .gitignore de la wallet"""
    gitignore_path = os.path.join(wallet_path, ".gitignore")
    
    log("Actualizando .gitignore de la wallet...")
    
    # Patrones a añadir
    patterns = [
        "",
        "# AES Certificate (NEVER COMMIT - CONTAINS CRYPTOGRAPHIC KEYS)",
        ".AES_certificate/",
        "**/.AES_certificate/",
        "*.AES_certificate",
    ]
    
    if os.path.exists(gitignore_path):
        # Leer .gitignore actual
        with open(gitignore_path, 'r') as f:
            content = f.read()
    else:
        content = ""
    
    # Añadir patrones si no existen
    updated = False
    for pattern in patterns:
        if pattern and pattern not in content:
            content += f"\n{pattern}"
            updated = True
    
    if updated or not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write(content)
        success(".gitignore actualizado")
    else:
        log(".gitignore ya contiene los patrones necesarios")

def create_installation_info(cert_dir, cert_info):
    """Crear archivo de información de la instalación"""
    install_info = {
        "installed_at": datetime.now().isoformat(),
        "coordinator_certificate": cert_info,
        "installation_version": "1.0",
        "wallet_location": os.path.dirname(cert_dir)
    }
    
    install_info_path = os.path.join(cert_dir, "installation_info.json")
    with open(install_info_path, 'w') as f:
        json.dump(install_info, f, indent=2)
    
    os.chmod(install_info_path, 0o644)
    log("Información de instalación guardada")

def test_certificate_loading(cert_dir):
    """Probar que el certificado se puede cargar correctamente"""
    log("Probando carga del certificado...")
    
    try:
        # Cargar master key
        master_key_path = os.path.join(cert_dir, "master_key.bin")
        with open(master_key_path, 'rb') as f:
            master_key = f.read()
        
        # Cargar info del certificado
        cert_info_path = os.path.join(cert_dir, "certificate_info.json")
        with open(cert_info_path, 'r') as f:
            cert_info = json.load(f)
        
        # Verificar hash
        actual_hash = hashlib.sha256(master_key).hexdigest()
        expected_hash = cert_info["master_key_hash"]
        
        if actual_hash == expected_hash:
            success("Certificado cargado y verificado correctamente")
            return True
        else:
            error("Hash del certificado no coincide")
            return False
            
    except Exception as e:
        error(f"Error probando certificado: {e}")
        return False

def main():
    """Función principal"""
    print("🔐 PlayerGold Wallet - AES Certificate Installation")
    print("=" * 60)
    
    # Obtener ruta del paquete
    if len(sys.argv) > 1:
        package_path = sys.argv[1]
    else:
        package_path = input("Ruta del paquete del certificado: ").strip()
    
    if not package_path:
        error("Ruta del paquete requerida")
        sys.exit(1)
    
    package_path = os.path.abspath(package_path)
    
    if not os.path.exists(package_path):
        error(f"Paquete no encontrado: {package_path}")
        sys.exit(1)
    
    # Encontrar directorio de la wallet
    wallet_path = find_wallet_directory()
    if not wallet_path:
        error("Directorio de la wallet no encontrado")
        error("Ejecuta este script desde el directorio del proyecto")
        sys.exit(1)
    
    log(f"Directorio de la wallet: {wallet_path}")
    
    try:
        # Verificar paquete
        verification_result = verify_certificate_package(package_path)
        if not verification_result:
            sys.exit(1)
        
        is_valid, cert_info = verification_result
        
        # Crear directorio del certificado
        cert_dir = create_wallet_certificate_directory(wallet_path)
        
        # Verificar si ya existe certificado
        if os.path.exists(os.path.join(cert_dir, "master_key.bin")):
            warning("Ya existe un certificado instalado")
            response = input("¿Quieres reemplazarlo? (y/N): ")
            if response.lower() != 'y':
                print("Instalación cancelada")
                sys.exit(0)
        
        # Instalar certificado
        install_certificate(package_path, cert_dir)
        
        # Actualizar .gitignore
        update_wallet_gitignore(wallet_path)
        
        # Crear información de instalación
        create_installation_info(cert_dir, cert_info)
        
        # Probar certificado
        if not test_certificate_loading(cert_dir):
            sys.exit(1)
        
        # Resumen final
        print("\n" + "=" * 60)
        success("🎉 Certificado AES instalado exitosamente!")
        print("\n📋 Información del certificado:")
        print(f"   • Ubicación: {cert_dir}")
        print(f"   • Algoritmo: {cert_info['algorithm']}")
        print(f"   • Creado: {cert_info['created_at']}")
        print(f"   • Hash: {cert_info['master_key_hash'][:32]}...")
        
        print("\n✅ La wallet ahora puede:")
        print("   • Descifrar network maps del coordinador")
        print("   • Comunicarse de forma segura con playergold.es")
        print("   • Mantener comunicación cifrada permanente")
        
        print("\n🔒 Seguridad:")
        print("   • Certificado guardado en directorio oculto")
        print("   • Permisos seguros configurados")
        print("   • .gitignore actualizado para prevenir commits")
        
        print(f"\n🚀 Próximo paso:")
        print("   • Reinicia la wallet para usar el nuevo certificado")
        
    except Exception as e:
        error(f"Error durante la instalación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()