#!/usr/bin/env python3
"""
PlayerGold Network Coordinator - AES Certificate Setup

Este script genera un certificado AES permanente para el coordinador
y lo guarda en /opt/playergold/data/.AES_certificate/

El certificado incluye:
- master_key.bin: Clave maestra AES-256 (32 bytes)
- certificate_info.json: Metadatos del certificado
- public_key.pem: Clave pública para verificación (opcional)

Uso: sudo python3 setup_coordinator_aes_certificate.py
"""

import os
import sys
import json
import secrets
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configuración
COORDINATOR_HOME = "/opt/playergold"
CERTIFICATE_DIR = f"{COORDINATOR_HOME}/data/.AES_certificate"
COORDINATOR_USER = "playergold"

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

def check_permissions():
    """Verificar que se ejecuta como root"""
    if os.geteuid() != 0:
        error("Este script debe ejecutarse como root (sudo)")
        sys.exit(1)

def check_coordinator_installation():
    """Verificar que el coordinador está instalado"""
    if not os.path.exists(COORDINATOR_HOME):
        error(f"Directorio del coordinador no encontrado: {COORDINATOR_HOME}")
        error("Ejecuta primero el script de deployment del coordinador")
        sys.exit(1)
    
    if not os.path.exists(f"{COORDINATOR_HOME}/data"):
        error(f"Directorio de datos no encontrado: {COORDINATOR_HOME}/data")
        sys.exit(1)

def generate_master_key():
    """Generar clave maestra AES-256 criptográficamente segura"""
    log("Generando clave maestra AES-256...")
    
    # Generar 32 bytes aleatorios para AES-256
    master_key = secrets.token_bytes(32)
    
    # Verificar que la clave es válida (no todos ceros, no patrones obvios)
    if master_key == b'\x00' * 32:
        error("Clave generada inválida (todos ceros)")
        return None
    
    # Calcular hash para verificación
    key_hash = hashlib.sha256(master_key).hexdigest()
    
    log(f"Clave generada: {len(master_key)} bytes")
    log(f"Hash SHA256: {key_hash[:16]}...{key_hash[-16:]}")
    
    return master_key, key_hash

def generate_rsa_keypair():
    """Generar par de claves RSA para verificación adicional"""
    log("Generando par de claves RSA para verificación...")
    
    # Generar clave privada RSA
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Obtener clave pública
    public_key = private_key.public_key()
    
    # Serializar clave pública
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Serializar clave privada
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    return public_pem, private_pem

def create_certificate_directory():
    """Crear directorio del certificado con permisos seguros"""
    log(f"Creando directorio del certificado: {CERTIFICATE_DIR}")
    
    # Crear directorio (oculto)
    os.makedirs(CERTIFICATE_DIR, mode=0o700, exist_ok=True)
    
    # Establecer propietario
    import pwd
    try:
        coordinator_uid = pwd.getpwnam(COORDINATOR_USER).pw_uid
        coordinator_gid = pwd.getpwnam(COORDINATOR_USER).pw_gid
        os.chown(CERTIFICATE_DIR, coordinator_uid, coordinator_gid)
        success(f"Directorio creado con permisos 700 para usuario {COORDINATOR_USER}")
    except KeyError:
        warning(f"Usuario {COORDINATOR_USER} no encontrado, usando root")

def save_certificate(master_key, key_hash, public_pem, private_pem):
    """Guardar certificado en archivos"""
    log("Guardando certificado AES...")
    
    # Archivo de clave maestra
    master_key_file = f"{CERTIFICATE_DIR}/master_key.bin"
    with open(master_key_file, 'wb') as f:
        f.write(master_key)
    os.chmod(master_key_file, 0o600)
    
    # Archivo de clave pública RSA
    public_key_file = f"{CERTIFICATE_DIR}/public_key.pem"
    with open(public_key_file, 'wb') as f:
        f.write(public_pem)
    os.chmod(public_key_file, 0o644)
    
    # Archivo de clave privada RSA
    private_key_file = f"{CERTIFICATE_DIR}/private_key.pem"
    with open(private_key_file, 'wb') as f:
        f.write(private_pem)
    os.chmod(private_key_file, 0o600)
    
    # Información del certificado
    cert_info = {
        "version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "coordinator_domain": "playergold.es",
        "master_key_hash": key_hash,
        "key_size_bits": 256,
        "algorithm": "AES-256-GCM",
        "kdf": "PBKDF2-HMAC-SHA256",
        "iterations": 100000,
        "description": "PlayerGold Network Coordinator AES Certificate",
        "permanent": True,
        "auto_renew": False
    }
    
    cert_info_file = f"{CERTIFICATE_DIR}/certificate_info.json"
    with open(cert_info_file, 'w') as f:
        json.dump(cert_info, f, indent=2)
    os.chmod(cert_info_file, 0o644)
    
    # Establecer propietario de todos los archivos
    import pwd
    try:
        coordinator_uid = pwd.getpwnam(COORDINATOR_USER).pw_uid
        coordinator_gid = pwd.getpwnam(COORDINATOR_USER).pw_gid
        
        for file_path in [master_key_file, public_key_file, private_key_file, cert_info_file]:
            os.chown(file_path, coordinator_uid, coordinator_gid)
            
    except KeyError:
        warning(f"Usuario {COORDINATOR_USER} no encontrado, archivos propiedad de root")
    
    success("Certificado AES guardado correctamente")
    return cert_info

def update_gitignore():
    """Actualizar .gitignore para excluir certificados"""
    gitignore_path = f"{COORDINATOR_HOME}/../.gitignore"
    
    if os.path.exists(gitignore_path):
        log("Actualizando .gitignore...")
        
        # Leer .gitignore actual
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        # Patrones a añadir
        patterns = [
            "# AES Certificates (NEVER COMMIT)",
            ".AES_certificate/",
            "**/.AES_certificate/",
            "*.AES_certificate",
        ]
        
        # Añadir patrones si no existen
        updated = False
        for pattern in patterns:
            if pattern not in content:
                content += f"\n{pattern}"
                updated = True
        
        if updated:
            with open(gitignore_path, 'w') as f:
                f.write(content)
            success(".gitignore actualizado")
        else:
            log(".gitignore ya contiene los patrones necesarios")

def create_download_package():
    """Crear paquete para descargar (solo archivos necesarios para el cliente)"""
    log("Creando paquete de descarga para el cliente...")
    
    package_dir = f"{COORDINATOR_HOME}/certificate_download"
    os.makedirs(package_dir, mode=0o755, exist_ok=True)
    
    # Copiar archivos necesarios para el cliente
    import shutil
    
    files_to_copy = [
        "master_key.bin",
        "certificate_info.json",
        "public_key.pem"
    ]
    
    for file_name in files_to_copy:
        src = f"{CERTIFICATE_DIR}/{file_name}"
        dst = f"{package_dir}/{file_name}"
        shutil.copy2(src, dst)
        os.chmod(dst, 0o644)
    
    # Crear README para el cliente
    readme_content = f"""# PlayerGold AES Certificate

Este paquete contiene el certificado AES para la comunicación entre
el coordinador y la wallet.

## Instalación en la wallet:

1. Crea el directorio: wallet/.AES_certificate/
2. Copia estos archivos al directorio creado:
   - master_key.bin
   - certificate_info.json  
   - public_key.pem

## Permisos recomendados:
- Directorio: 700 (solo propietario)
- Archivos: 600 (solo propietario)

## Generado:
- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Servidor: playergold.es
- Versión: 1.0

⚠️  IMPORTANTE: Estos archivos contienen claves criptográficas.
   NO los subas a repositorios públicos.
"""
    
    with open(f"{package_dir}/README.md", 'w') as f:
        f.write(readme_content)
    
    success(f"Paquete de descarga creado en: {package_dir}")
    return package_dir

def restart_coordinator_service():
    """Reiniciar el servicio del coordinador"""
    log("Reiniciando servicio del coordinador...")
    
    try:
        import subprocess
        
        # Reiniciar servicio
        result = subprocess.run(['systemctl', 'restart', 'playergold-coordinator'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            success("Servicio del coordinador reiniciado")
            
            # Verificar estado
            result = subprocess.run(['systemctl', 'is-active', 'playergold-coordinator'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() == 'active':
                success("Servicio está activo y funcionando")
            else:
                warning("Servicio reiniciado pero no está activo")
                
        else:
            error(f"Error reiniciando servicio: {result.stderr}")
            
    except Exception as e:
        error(f"Error reiniciando servicio: {e}")

def main():
    """Función principal"""
    print("🔐 PlayerGold Network Coordinator - AES Certificate Setup")
    print("=" * 60)
    
    # Verificaciones
    check_permissions()
    check_coordinator_installation()
    
    # Verificar si ya existe certificado
    if os.path.exists(CERTIFICATE_DIR):
        print(f"\n⚠️  Ya existe un certificado en: {CERTIFICATE_DIR}")
        response = input("¿Quieres regenerar el certificado? (y/N): ")
        if response.lower() != 'y':
            print("Operación cancelada")
            sys.exit(0)
        
        log("Eliminando certificado existente...")
        import shutil
        shutil.rmtree(CERTIFICATE_DIR)
    
    try:
        # Generar certificado
        master_key, key_hash = generate_master_key()
        if not master_key:
            sys.exit(1)
        
        public_pem, private_pem = generate_rsa_keypair()
        
        # Crear directorio y guardar certificado
        create_certificate_directory()
        cert_info = save_certificate(master_key, key_hash, public_pem, private_pem)
        
        # Actualizar .gitignore
        update_gitignore()
        
        # Crear paquete de descarga
        package_dir = create_download_package()
        
        # Reiniciar servicio
        restart_coordinator_service()
        
        # Resumen final
        print("\n" + "=" * 60)
        success("🎉 Certificado AES generado exitosamente!")
        print("\n📋 Información del certificado:")
        print(f"   • Ubicación: {CERTIFICATE_DIR}")
        print(f"   • Hash: {key_hash[:32]}...")
        print(f"   • Creado: {cert_info['created_at']}")
        print(f"   • Algoritmo: {cert_info['algorithm']}")
        
        print("\n📦 Paquete para descarga:")
        print(f"   • Ubicación: {package_dir}")
        print(f"   • Archivos: master_key.bin, certificate_info.json, public_key.pem")
        
        print("\n🔽 Próximos pasos:")
        print("1. Descarga el paquete del servidor")
        print("2. Copia los archivos a wallet/.AES_certificate/")
        print("3. Configura permisos 700 para el directorio")
        print("4. Configura permisos 600 para los archivos")
        print("5. Actualiza la wallet para usar el certificado")
        
        print(f"\n💾 Comando de descarga sugerido:")
        print(f"   scp -r user@playergold.es:{package_dir}/* ./wallet/.AES_certificate/")
        
    except Exception as e:
        error(f"Error generando certificado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()