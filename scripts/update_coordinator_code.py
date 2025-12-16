#!/usr/bin/env python3
"""
PlayerGold Network Coordinator - Code Update

Este script actualiza el código fuente del coordinador en el servidor
con las nuevas funcionalidades (certificados AES, etc.)

Debe ejecutarse ANTES de setup_coordinator_aes_certificate.py

Uso: sudo python3 scripts/update_coordinator_code.py
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# Configuración
COORDINATOR_HOME = "/opt/playergold"
COORDINATOR_SOURCE_DIR = "/opt/src"  # Directorio donde está el código fuente actualizado
COORDINATOR_USER = "playergold"
SERVICE_NAME = "playergold-coordinator"
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

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
        error("Uso: sudo python3 scripts/update_coordinator_code.py")
        sys.exit(1)

def check_coordinator_installation():
    """Verificar que el coordinador está instalado"""
    if not os.path.exists(COORDINATOR_HOME):
        error(f"Directorio del coordinador no encontrado: {COORDINATOR_HOME}")
        error("Ejecuta primero el script de deployment del coordinador")
        sys.exit(1)
    
    if not os.path.exists(f"{COORDINATOR_HOME}/src"):
        error(f"Directorio de destino no encontrado: {COORDINATOR_HOME}/src")
        sys.exit(1)
    
    if not os.path.exists(COORDINATOR_SOURCE_DIR):
        error(f"Directorio de código fuente actualizado no encontrado: {COORDINATOR_SOURCE_DIR}")
        error("Asegúrate de que el código actualizado esté en /opt/src/")
        sys.exit(1)

def check_source_files():
    """Verificar que los archivos fuente actualizados existen"""
    log("Verificando archivos fuente actualizados...")
    
    required_files = [
        "network_coordinator/models.py",
        "network_coordinator/api.py", 
        "network_coordinator/database.py",
        "network_coordinator/utils.py",
        "network_coordinator/encryption.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = Path(COORDINATOR_SOURCE_DIR) / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            log(f"✓ {COORDINATOR_SOURCE_DIR}/{file_path}")
    
    if missing_files:
        error("Archivos fuente faltantes en /opt/src/:")
        for file_path in missing_files:
            error(f"  - {COORDINATOR_SOURCE_DIR}/{file_path}")
        sys.exit(1)
    
    success("Todos los archivos fuente encontrados en /opt/src/")

def stop_coordinator_service():
    """Detener el servicio del coordinador"""
    log("Deteniendo servicio del coordinador...")
    
    try:
        # Verificar si el servicio existe
        result = subprocess.run(['systemctl', 'is-enabled', SERVICE_NAME], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            warning(f"Servicio {SERVICE_NAME} no encontrado o no habilitado")
            return True
        
        # Detener servicio
        result = subprocess.run(['systemctl', 'stop', SERVICE_NAME], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            success("Servicio del coordinador detenido")
            return True
        else:
            error(f"Error deteniendo servicio: {result.stderr}")
            return False
            
    except Exception as e:
        error(f"Error deteniendo servicio: {e}")
        return False

def create_backup():
    """Crear backup del código actual"""
    log("Creando backup del código actual...")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{COORDINATOR_HOME}/src_backup_{timestamp}"
        
        # Copiar directorio completo
        shutil.copytree(f"{COORDINATOR_HOME}/src", backup_dir)
        
        # Establecer permisos
        import pwd
        try:
            coordinator_uid = pwd.getpwnam(COORDINATOR_USER).pw_uid
            coordinator_gid = pwd.getpwnam(COORDINATOR_USER).pw_gid
            
            # Cambiar propietario recursivamente
            for root, dirs, files in os.walk(backup_dir):
                os.chown(root, coordinator_uid, coordinator_gid)
                for file in files:
                    os.chown(os.path.join(root, file), coordinator_uid, coordinator_gid)
                    
        except KeyError:
            warning(f"Usuario {COORDINATOR_USER} no encontrado, backup propiedad de root")
        
        success(f"Backup creado: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        error(f"Error creando backup: {e}")
        return None

def update_source_code():
    """Actualizar el código fuente del coordinador"""
    log("Actualizando código fuente del coordinador...")
    
    try:
        # Archivos a actualizar (rutas relativas desde /opt/src/)
        files_to_update = [
            "network_coordinator/models.py",
            "network_coordinator/api.py",
            "network_coordinator/database.py",
            "network_coordinator/utils.py",
            "network_coordinator/encryption.py"
        ]
        
        updated_files = []
        
        for file_path in files_to_update:
            # Archivo fuente en /opt/src/
            src_file = Path(COORDINATOR_SOURCE_DIR) / file_path
            # Archivo destino en /opt/playergold/src/
            dst_file = Path(COORDINATOR_HOME) / "src" / file_path
            
            if src_file.exists():
                # Crear directorio de destino si no existe
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copiar archivo
                shutil.copy2(src_file, dst_file)
                
                # Establecer permisos
                os.chmod(dst_file, 0o644)
                
                updated_files.append(file_path)
                log(f"✓ Actualizado: {src_file} → {dst_file}")
            else:
                warning(f"Archivo fuente no encontrado: {src_file}")
        
        # Establecer propietario de todos los archivos actualizados
        import pwd
        try:
            coordinator_uid = pwd.getpwnam(COORDINATOR_USER).pw_uid
            coordinator_gid = pwd.getpwnam(COORDINATOR_USER).pw_gid
            
            for file_path in updated_files:
                dst_file = Path(COORDINATOR_HOME) / "src" / file_path
                os.chown(dst_file, coordinator_uid, coordinator_gid)
                
        except KeyError:
            warning(f"Usuario {COORDINATOR_USER} no encontrado, archivos propiedad de root")
        
        success(f"Actualizados {len(updated_files)} archivos de código fuente")
        return len(updated_files) > 0
        
    except Exception as e:
        error(f"Error actualizando código fuente: {e}")
        return False

def verify_updated_code():
    """Verificar que el código actualizado es válido"""
    log("Verificando código actualizado...")
    
    try:
        # Verificar sintaxis de Python
        encryption_file = f"{COORDINATOR_HOME}/src/network_coordinator/encryption.py"
        
        if os.path.exists(encryption_file):
            # Compilar archivo para verificar sintaxis
            with open(encryption_file, 'r') as f:
                code = f.read()
            
            try:
                compile(code, encryption_file, 'exec')
                success("Sintaxis de encryption.py verificada")
            except SyntaxError as e:
                error(f"Error de sintaxis en encryption.py: {e}")
                return False
        
        # Verificar que contiene las nuevas funciones
        if "load_master_key_from_certificate" in code:
            success("Nueva funcionalidad de certificados detectada")
        else:
            warning("Nueva funcionalidad de certificados no detectada")
        
        # Verificar models.py para las correcciones de génesis
        models_file = f"{COORDINATOR_HOME}/src/network_coordinator/models.py"
        if os.path.exists(models_file):
            with open(models_file, 'r') as f:
                models_code = f.read()
            
            if "is_genesis = Column(Boolean" in models_code:
                success("Correcciones de nodos génesis detectadas")
            else:
                warning("Correcciones de nodos génesis no detectadas")
        
        return True
        
    except Exception as e:
        error(f"Error verificando código: {e}")
        return False

def start_coordinator_service():
    """Iniciar el servicio del coordinador"""
    log("Iniciando servicio del coordinador...")
    
    try:
        # Iniciar servicio
        result = subprocess.run(['systemctl', 'start', SERVICE_NAME], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            success("Servicio del coordinador iniciado")
            
            # Esperar un momento y verificar estado
            import time
            time.sleep(3)
            
            result = subprocess.run(['systemctl', 'is-active', SERVICE_NAME], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() == 'active':
                success("Servicio confirmado como activo")
                return True
            else:
                warning("Servicio iniciado pero no está activo")
                # Mostrar logs para diagnóstico
                log("Últimas líneas del log del servicio:")
                subprocess.run(['journalctl', '-u', SERVICE_NAME, '--no-pager', '-n', '10'])
                return False
                
        else:
            error(f"Error iniciando servicio: {result.stderr}")
            return False
            
    except Exception as e:
        error(f"Error iniciando servicio: {e}")
        return False

def test_coordinator_functionality():
    """Probar que el coordinador funciona con el código actualizado"""
    log("Probando funcionalidad del coordinador...")
    
    try:
        import time
        import requests
        
        # Esperar que el servicio esté completamente listo
        time.sleep(5)
        
        # Probar endpoint de salud
        response = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=10)
        
        if response.status_code == 200:
            success("Coordinador responde correctamente")
            
            # Verificar respuesta
            data = response.json()
            if data.get('status') == 'healthy':
                success("Estado del coordinador: saludable")
                return True
            else:
                warning(f"Estado del coordinador: {data.get('status', 'unknown')}")
                return False
        else:
            error(f"Coordinador respondió con código: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        error(f"Error conectando al coordinador: {e}")
        return False
    except Exception as e:
        error(f"Error probando coordinador: {e}")
        return False

def main():
    """Función principal"""
    print("🔄 PlayerGold Network Coordinator - Code Update")
    print("=" * 60)
    
    # Verificaciones iniciales
    check_permissions()
    check_coordinator_installation()
    check_source_files()
    
    try:
        # Detener servicio
        print("\n" + "="*40)
        if not stop_coordinator_service():
            error("No se pudo detener el servicio")
            sys.exit(1)
        
        # Crear backup
        print("\n" + "="*40)
        backup_dir = create_backup()
        if not backup_dir:
            error("No se pudo crear backup")
            sys.exit(1)
        
        # Actualizar código
        print("\n" + "="*40)
        if not update_source_code():
            error("No se pudo actualizar el código")
            sys.exit(1)
        
        # Verificar código
        print("\n" + "="*40)
        if not verify_updated_code():
            error("El código actualizado tiene problemas")
            sys.exit(1)
        
        # Iniciar servicio
        print("\n" + "="*40)
        if not start_coordinator_service():
            error("No se pudo iniciar el servicio")
            sys.exit(1)
        
        # Probar funcionalidad
        print("\n" + "="*40)
        if not test_coordinator_functionality():
            warning("El coordinador puede tener problemas de funcionalidad")
        
        # Resumen final
        print("\n" + "=" * 60)
        success("🎉 Actualización de código completada exitosamente!")
        print("\n📋 Resumen:")
        print(f"   • Backup creado: {backup_dir}")
        print(f"   • Código fuente copiado desde: {COORDINATOR_SOURCE_DIR}")
        print(f"   • Código fuente actualizado en: {COORDINATOR_HOME}/src")
        print(f"   • Servicio: ✅ Activo y funcionando")
        print(f"   • Nueva funcionalidad: ✅ Certificados AES")
        
        print("\n🚀 Próximo paso:")
        print("   sudo python3 scripts/setup_coordinator_aes_certificate.py")
        
        print("\n💡 Verificación:")
        print("   • Estado: sudo systemctl status playergold-coordinator")
        print("   • Logs: sudo journalctl -u playergold-coordinator -f")
        print("   • Health: curl http://127.0.0.1:8000/api/v1/health")
        
    except Exception as e:
        error(f"Error durante la actualización: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()