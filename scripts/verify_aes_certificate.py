#!/usr/bin/env python3
"""
PlayerGold - AES Certificate Verification

Este script verifica que el certificado AES esté correctamente instalado
tanto en el coordinador como en la wallet.

Uso: python3 verify_aes_certificate.py [--coordinator|--wallet]
"""

import os
import sys
import json
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

def verify_coordinator_certificate():
    """Verificar certificado del coordinador"""
    print("🔍 Verificando certificado del coordinador...")
    
    cert_paths = [
        "/opt/playergold/data/.AES_certificate",
        "./data/.AES_certificate",
        "./.AES_certificate"
    ]
    
    cert_dir = None
    for path in cert_paths:
        if os.path.exists(path):
            cert_dir = path
            break
    
    if not cert_dir:
        error("Certificado del coordinador no encontrado")
        print("Ubicaciones buscadas:")
        for path in cert_paths:
            print(f"  - {path}")
        return False
    
    log(f"Certificado encontrado en: {cert_dir}")
    
    # Verificar archivos requeridos
    required_files = [
        "master_key.bin",
        "certificate_info.json",
        "public_key.pem",
        "private_key.pem"
    ]
    
    for file_name in required_files:
        file_path = os.path.join(cert_dir, file_name)
        if not os.path.exists(file_path):
            error(f"Archivo faltante: {file_name}")
            return False
        
        # Verificar permisos
        stat = os.stat(file_path)
        if file_name == "master_key.bin" or file_name == "private_key.pem":
            if stat.st_mode & 0o077:  # Verificar que solo el propietario puede acceder
                warning(f"Permisos inseguros en {file_name}: {oct(stat.st_mode)[-3:]}")
        
        log(f"✓ {file_name} - {stat.st_size} bytes - permisos: {oct(stat.st_mode)[-3:]}")
    
    # Verificar contenido
    try:
        # Cargar master key
        with open(os.path.join(cert_dir, "master_key.bin"), 'rb') as f:
            master_key = f.read()
        
        if len(master_key) != 32:
            error(f"master_key.bin tiene tamaño incorrecto: {len(master_key)} bytes")
            return False
        
        # Cargar info del certificado
        with open(os.path.join(cert_dir, "certificate_info.json"), 'r') as f:
            cert_info = json.load(f)
        
        # Verificar hash
        actual_hash = hashlib.sha256(master_key).hexdigest()
        expected_hash = cert_info["master_key_hash"]
        
        if actual_hash != expected_hash:
            error("Hash de master_key no coincide")
            return False
        
        success("Certificado del coordinador verificado correctamente")
        print(f"  • Algoritmo: {cert_info.get('algorithm', 'N/A')}")
        print(f"  • Creado: {cert_info.get('created_at', 'N/A')}")
        print(f"  • Hash: {actual_hash[:32]}...")
        
        return True
        
    except Exception as e:
        error(f"Error verificando certificado: {e}")
        return False

def verify_wallet_certificate():
    """Verificar certificado de la wallet"""
    print("🔍 Verificando certificado de la wallet...")
    
    cert_paths = [
        "./wallet/.AES_certificate",
        "./.AES_certificate",
        os.path.expanduser("~/.AES_certificate")
    ]
    
    cert_dir = None
    for path in cert_paths:
        if os.path.exists(path):
            cert_dir = path
            break
    
    if not cert_dir:
        error("Certificado de la wallet no encontrado")
        print("Ubicaciones buscadas:")
        for path in cert_paths:
            print(f"  - {path}")
        print("\n💡 Para instalar el certificado:")
        print("   python3 scripts/install_wallet_aes_certificate.py [paquete]")
        return False
    
    log(f"Certificado encontrado en: {cert_dir}")
    
    # Verificar archivos requeridos
    required_files = [
        "master_key.bin",
        "certificate_info.json",
        "public_key.pem"
    ]
    
    for file_name in required_files:
        file_path = os.path.join(cert_dir, file_name)
        if not os.path.exists(file_path):
            error(f"Archivo faltante: {file_name}")
            return False
        
        # Verificar permisos
        stat = os.stat(file_path)
        if file_name == "master_key.bin":
            if stat.st_mode & 0o077:  # Verificar que solo el propietario puede acceder
                warning(f"Permisos inseguros en {file_name}: {oct(stat.st_mode)[-3:]}")
        
        log(f"✓ {file_name} - {stat.st_size} bytes - permisos: {oct(stat.st_mode)[-3:]}")
    
    # Verificar contenido
    try:
        # Cargar master key
        with open(os.path.join(cert_dir, "master_key.bin"), 'rb') as f:
            master_key = f.read()
        
        if len(master_key) != 32:
            error(f"master_key.bin tiene tamaño incorrecto: {len(master_key)} bytes")
            return False
        
        # Cargar info del certificado
        with open(os.path.join(cert_dir, "certificate_info.json"), 'r') as f:
            cert_info = json.load(f)
        
        # Verificar hash
        actual_hash = hashlib.sha256(master_key).hexdigest()
        expected_hash = cert_info["master_key_hash"]
        
        if actual_hash != expected_hash:
            error("Hash de master_key no coincide")
            return False
        
        success("Certificado de la wallet verificado correctamente")
        print(f"  • Algoritmo: {cert_info.get('algorithm', 'N/A')}")
        print(f"  • Creado: {cert_info.get('created_at', 'N/A')}")
        print(f"  • Hash: {actual_hash[:32]}...")
        
        return True
        
    except Exception as e:
        error(f"Error verificando certificado: {e}")
        return False

def test_decryption_compatibility():
    """Probar que ambos certificados son compatibles"""
    print("🔍 Probando compatibilidad de certificados...")
    
    # Buscar certificados
    coordinator_paths = ["/opt/playergold/data/.AES_certificate", "./data/.AES_certificate", "./.AES_certificate"]
    wallet_paths = ["./wallet/.AES_certificate", "./.AES_certificate", os.path.expanduser("~/.AES_certificate")]
    
    coordinator_cert = None
    wallet_cert = None
    
    for path in coordinator_paths:
        if os.path.exists(os.path.join(path, "master_key.bin")):
            coordinator_cert = path
            break
    
    for path in wallet_paths:
        if os.path.exists(os.path.join(path, "master_key.bin")):
            wallet_cert = path
            break
    
    if not coordinator_cert:
        warning("Certificado del coordinador no encontrado para prueba de compatibilidad")
        return False
    
    if not wallet_cert:
        warning("Certificado de la wallet no encontrado para prueba de compatibilidad")
        return False
    
    try:
        # Cargar ambas claves
        with open(os.path.join(coordinator_cert, "master_key.bin"), 'rb') as f:
            coord_key = f.read()
        
        with open(os.path.join(wallet_cert, "master_key.bin"), 'rb') as f:
            wallet_key = f.read()
        
        # Comparar
        if coord_key == wallet_key:
            success("Los certificados son compatibles (misma clave maestra)")
            return True
        else:
            error("Los certificados NO son compatibles (claves diferentes)")
            print(f"  • Coordinador: {hashlib.sha256(coord_key).hexdigest()[:32]}...")
            print(f"  • Wallet: {hashlib.sha256(wallet_key).hexdigest()[:32]}...")
            return False
            
    except Exception as e:
        error(f"Error probando compatibilidad: {e}")
        return False

def main():
    """Función principal"""
    print("🔐 PlayerGold - AES Certificate Verification")
    print("=" * 60)
    
    # Parsear argumentos
    mode = "both"
    if len(sys.argv) > 1:
        if sys.argv[1] == "--coordinator":
            mode = "coordinator"
        elif sys.argv[1] == "--wallet":
            mode = "wallet"
        elif sys.argv[1] == "--help":
            print("Uso: python3 verify_aes_certificate.py [--coordinator|--wallet]")
            print("  --coordinator: Solo verificar certificado del coordinador")
            print("  --wallet: Solo verificar certificado de la wallet")
            print("  (sin argumentos): Verificar ambos y compatibilidad")
            sys.exit(0)
    
    results = []
    
    # Verificar según el modo
    if mode in ["both", "coordinator"]:
        print("\n" + "="*40)
        results.append(("Coordinador", verify_coordinator_certificate()))
    
    if mode in ["both", "wallet"]:
        print("\n" + "="*40)
        results.append(("Wallet", verify_wallet_certificate()))
    
    # Probar compatibilidad si verificamos ambos
    if mode == "both":
        print("\n" + "="*40)
        results.append(("Compatibilidad", test_decryption_compatibility()))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE VERIFICACIÓN:")
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  • {name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        success("🎉 Todos los certificados están correctamente configurados!")
        print("\n✅ La comunicación cifrada entre coordinador y wallet está lista")
    else:
        error("❌ Hay problemas con los certificados")
        print("\n💡 Pasos para solucionar:")
        print("1. Generar certificado en el coordinador: sudo python3 scripts/setup_coordinator_aes_certificate.py")
        print("2. Descargar paquete del servidor")
        print("3. Instalar en wallet: python3 scripts/install_wallet_aes_certificate.py [paquete]")
        sys.exit(1)

if __name__ == "__main__":
    main()