#!/usr/bin/env python3
"""
PlayerGold Network Coordinator - Database Reset

Este script elimina completamente todos los datos de la base de datos del coordinador
para comenzar con una sesión limpia. Útil para eliminar datos corruptos o reiniciar
el coordinador desde cero.

⚠️  ADVERTENCIA: Esta operación es IRREVERSIBLE y eliminará:
- Todos los nodos registrados
- Todo el historial de keepalive
- Todas las métricas y estadísticas
- Cualquier dato corrupto

Uso: sudo python3 reset_coordinator_database.py [--force]
"""

import os
import sys
import sqlite3
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import subprocess

# Configuración
COORDINATOR_HOME = "/opt/playergold"
DATABASE_PATHS = [
    f"{COORDINATOR_HOME}/data/network_nodes.db",
    f"{COORDINATOR_HOME}/network_nodes.db",
    "./data/network_nodes.db",
    "./network_nodes.db"
]
BACKUP_DIR = f"{COORDINATOR_HOME}/data/backups"
COORDINATOR_USER = "playergold"
SERVICE_NAME = "playergold-coordinator"

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
        error("Uso: sudo python3 reset_coordinator_database.py")
        sys.exit(1)

def find_database_file():
    """Encontrar el archivo de base de datos del coordinador"""
    log("Buscando base de datos del coordinador...")
    
    for db_path in DATABASE_PATHS:
        if os.path.exists(db_path):
            log(f"Base de datos encontrada: {db_path}")
            return db_path
    
    warning("No se encontró la base de datos del coordinador")
    print("Ubicaciones buscadas:")
    for path in DATABASE_PATHS:
        print(f"  - {path}")
    
    return None

def analyze_database(db_path):
    """Analizar el contenido actual de la base de datos"""
    log("Analizando contenido actual de la base de datos...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener información de las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Tablas encontradas: {len(tables)}")
        
        total_records = 0
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"  - {table_name}: {count} registros")
        
        print(f"📊 Total de registros: {total_records}")
        
        # Información específica de nodos si existe la tabla
        if ('nodes',) in tables:
            cursor.execute("SELECT COUNT(*) FROM nodes WHERE status = 'active';")
            active_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM nodes WHERE status = 'inactive';")
            inactive_nodes = cursor.fetchone()[0]
            
            print(f"📊 Nodos activos: {active_nodes}")
            print(f"📊 Nodos inactivos: {inactive_nodes}")
            
            # Mostrar algunos nodos recientes
            cursor.execute("SELECT node_id, os_info, node_type, status, created_at FROM nodes ORDER BY created_at DESC LIMIT 5;")
            recent_nodes = cursor.fetchall()
            
            if recent_nodes:
                print("📄 Últimos 5 nodos registrados:")
                for node in recent_nodes:
                    print(f"  - {node[0][:20]}... ({node[2]}) - {node[3]} - {node[4]}")
        
        conn.close()
        return total_records
        
    except Exception as e:
        error(f"Error analizando base de datos: {e}")
        return 0

def create_backup(db_path):
    """Crear backup de la base de datos antes de eliminarla"""
    log("Creando backup de la base de datos...")
    
    try:
        # Crear directorio de backups
        os.makedirs(BACKUP_DIR, mode=0o755, exist_ok=True)
        
        # Nombre del backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"network_nodes_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Copiar base de datos
        shutil.copy2(db_path, backup_path)
        
        # Establecer permisos y propietario
        os.chmod(backup_path, 0o644)
        try:
            import pwd
            coordinator_uid = pwd.getpwnam(COORDINATOR_USER).pw_uid
            coordinator_gid = pwd.getpwnam(COORDINATOR_USER).pw_gid
            os.chown(backup_path, coordinator_uid, coordinator_gid)
            os.chown(BACKUP_DIR, coordinator_uid, coordinator_gid)
        except KeyError:
            warning(f"Usuario {COORDINATOR_USER} no encontrado, backup propiedad de root")
        
        success(f"Backup creado: {backup_path}")
        
        # Crear información del backup
        backup_info = {
            "original_path": db_path,
            "backup_path": backup_path,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reason": "Database reset",
            "script_version": "1.0"
        }
        
        info_path = os.path.join(BACKUP_DIR, f"backup_info_{timestamp}.json")
        with open(info_path, 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        os.chmod(info_path, 0o644)
        try:
            os.chown(info_path, coordinator_uid, coordinator_gid)
        except:
            pass
        
        return backup_path
        
    except Exception as e:
        error(f"Error creando backup: {e}")
        return None

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
            
            # Verificar que se detuvo
            result = subprocess.run(['systemctl', 'is-active', SERVICE_NAME], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() != 'active':
                success("Servicio confirmado como detenido")
                return True
            else:
                warning("Servicio aún aparece como activo")
                return False
                
        else:
            error(f"Error deteniendo servicio: {result.stderr}")
            return False
            
    except Exception as e:
        error(f"Error deteniendo servicio: {e}")
        return False

def delete_database(db_path):
    """Eliminar la base de datos"""
    log(f"Eliminando base de datos: {db_path}")
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(db_path):
            warning("Base de datos ya no existe")
            return True
        
        # Eliminar archivo
        os.remove(db_path)
        
        # Verificar eliminación
        if not os.path.exists(db_path):
            success("Base de datos eliminada correctamente")
            return True
        else:
            error("La base de datos aún existe después de la eliminación")
            return False
            
    except Exception as e:
        error(f"Error eliminando base de datos: {e}")
        return False

def delete_related_files(db_path):
    """Eliminar archivos relacionados con la base de datos"""
    log("Eliminando archivos relacionados...")
    
    db_dir = os.path.dirname(db_path)
    related_patterns = [
        "network_nodes.db-journal",
        "network_nodes.db-wal",
        "network_nodes.db-shm",
        "*.db-journal",
        "*.db-wal", 
        "*.db-shm"
    ]
    
    deleted_files = []
    
    try:
        for pattern in related_patterns:
            if '*' in pattern:
                # Buscar archivos que coincidan con el patrón
                import glob
                matching_files = glob.glob(os.path.join(db_dir, pattern))
                for file_path in matching_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_files.append(file_path)
            else:
                # Archivo específico
                file_path = os.path.join(db_dir, pattern)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files.append(file_path)
        
        if deleted_files:
            success(f"Eliminados {len(deleted_files)} archivos relacionados:")
            for file_path in deleted_files:
                print(f"  - {os.path.basename(file_path)}")
        else:
            log("No se encontraron archivos relacionados para eliminar")
        
        return True
        
    except Exception as e:
        error(f"Error eliminando archivos relacionados: {e}")
        return False

def initialize_clean_database(db_path):
    """Inicializar una nueva base de datos limpia"""
    log("Inicializando nueva base de datos limpia...")
    
    try:
        # Crear nueva base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear tabla de nodos (estructura estándar)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                encrypted_ip BLOB NOT NULL,
                ip_salt BLOB NOT NULL,
                port INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                os_info TEXT NOT NULL,
                is_genesis BOOLEAN NOT NULL DEFAULT 0,
                last_keepalive TIMESTAMP NOT NULL,
                blockchain_height INTEGER NOT NULL DEFAULT 0,
                connected_peers INTEGER NOT NULL DEFAULT 0,
                node_type TEXT NOT NULL DEFAULT 'regular',
                reputation_score REAL NOT NULL DEFAULT 1.0,
                created_at TIMESTAMP NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                public_key TEXT,
                metadata TEXT
            )
        """)
        
        # Crear índices para mejorar rendimiento
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_keepalive ON nodes(last_keepalive);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_created ON nodes(created_at);")
        
        conn.commit()
        conn.close()
        
        # Establecer permisos y propietario
        os.chmod(db_path, 0o644)
        try:
            import pwd
            coordinator_uid = pwd.getpwnam(COORDINATOR_USER).pw_uid
            coordinator_gid = pwd.getpwnam(COORDINATOR_USER).pw_gid
            os.chown(db_path, coordinator_uid, coordinator_gid)
        except KeyError:
            warning(f"Usuario {COORDINATOR_USER} no encontrado, base de datos propiedad de root")
        
        success("Nueva base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        error(f"Error inicializando nueva base de datos: {e}")
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

def verify_clean_database(db_path):
    """Verificar que la nueva base de datos está limpia y funcional"""
    log("Verificando nueva base de datos...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estructura de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if ('nodes',) not in tables:
            error("Tabla 'nodes' no encontrada en la nueva base de datos")
            return False
        
        # Verificar que está vacía
        cursor.execute("SELECT COUNT(*) FROM nodes;")
        count = cursor.fetchone()[0]
        
        if count == 0:
            success("Base de datos limpia verificada (0 registros)")
        else:
            warning(f"Base de datos contiene {count} registros (debería estar vacía)")
        
        # Verificar índices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='nodes';")
        indexes = cursor.fetchall()
        
        success(f"Índices creados: {len(indexes)}")
        
        conn.close()
        return True
        
    except Exception as e:
        error(f"Error verificando base de datos: {e}")
        return False

def main():
    """Función principal"""
    print("🗑️  PlayerGold Network Coordinator - Database Reset")
    print("=" * 60)
    
    # Verificar argumentos
    force_mode = "--force" in sys.argv
    
    if not force_mode:
        print("⚠️  ADVERTENCIA: Esta operación eliminará TODOS los datos del coordinador")
        print("   • Todos los nodos registrados")
        print("   • Todo el historial de keepalive")
        print("   • Todas las métricas y estadísticas")
        print("   • Cualquier dato corrupto")
        print()
        print("   Esta operación es IRREVERSIBLE")
        print()
        
        response = input("¿Estás seguro de que quieres continuar? (escribe 'RESET' para confirmar): ")
        if response != "RESET":
            print("Operación cancelada")
            sys.exit(0)
    
    # Verificaciones
    check_permissions()
    
    # Encontrar base de datos
    db_path = find_database_file()
    if not db_path:
        error("No se puede continuar sin encontrar la base de datos")
        sys.exit(1)
    
    try:
        # Analizar contenido actual
        print("\n" + "="*40)
        total_records = analyze_database(db_path)
        
        if total_records == 0:
            log("La base de datos ya está vacía")
            response = input("¿Quieres recrearla de todos modos? (y/N): ")
            if response.lower() != 'y':
                print("Operación cancelada")
                sys.exit(0)
        
        # Crear backup
        print("\n" + "="*40)
        backup_path = create_backup(db_path)
        if not backup_path:
            error("No se pudo crear backup, abortando operación")
            sys.exit(1)
        
        # Detener servicio
        print("\n" + "="*40)
        if not stop_coordinator_service():
            error("No se pudo detener el servicio, abortando operación")
            sys.exit(1)
        
        # Eliminar base de datos y archivos relacionados
        print("\n" + "="*40)
        if not delete_database(db_path):
            sys.exit(1)
        
        delete_related_files(db_path)
        
        # Inicializar nueva base de datos
        print("\n" + "="*40)
        if not initialize_clean_database(db_path):
            sys.exit(1)
        
        # Verificar nueva base de datos
        print("\n" + "="*40)
        if not verify_clean_database(db_path):
            sys.exit(1)
        
        # Iniciar servicio
        print("\n" + "="*40)
        if not start_coordinator_service():
            warning("Servicio no se pudo iniciar automáticamente")
            print("Inicia manualmente con: sudo systemctl start playergold-coordinator")
        
        # Resumen final
        print("\n" + "=" * 60)
        success("🎉 Reset de base de datos completado exitosamente!")
        print("\n📋 Resumen:")
        print(f"   • Registros eliminados: {total_records}")
        print(f"   • Backup creado: {backup_path}")
        print(f"   • Nueva base de datos: {db_path}")
        print(f"   • Servicio: {'✅ Activo' if start_coordinator_service() else '❌ Inactivo'}")
        
        print("\n🚀 El coordinador ahora tiene:")
        print("   • Base de datos completamente limpia")
        print("   • Estructura de tablas recreada")
        print("   • Índices optimizados")
        print("   • 0 nodos registrados")
        
        print("\n💡 Próximos pasos:")
        print("   • Los nodos se registrarán automáticamente al conectarse")
        print("   • Verifica el estado: sudo systemctl status playergold-coordinator")
        print("   • Monitorea logs: sudo journalctl -u playergold-coordinator -f")
        
        if backup_path:
            print(f"\n💾 Backup disponible en: {backup_path}")
            print("   (Elimínalo cuando estés seguro de que no lo necesitas)")
        
    except Exception as e:
        error(f"Error durante el reset: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()