#!/usr/bin/env python3
"""
PlayerGold Network Coordinator - Clean Node Data

Limpia SOLO los datos de nodos de la base de datos del coordinador,
manteniendo intactos los certificados AES y toda la configuración.

Esto permite hacer una prueba limpia con solo los nodos reales.

Uso: sudo python3 clean_coordinator_nodes.py
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def log(message):
    """Log con timestamp"""
    from datetime import datetime
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

def stop_coordinator():
    """Parar el coordinador"""
    log("Parando servicio del coordinador...")
    try:
        result = subprocess.run(['systemctl', 'stop', 'playergold-coordinator'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            success("Servicio parado")
        else:
            warning(f"Error parando servicio: {result.stderr}")
    except Exception as e:
        warning(f"Error parando servicio: {e}")

def show_current_nodes():
    """Mostrar nodos actuales en la base de datos"""
    log("Mostrando nodos actuales en la base de datos...")
    
    db_path = "/opt/playergold/src/network_coordinator.db"
    
    if not os.path.exists(db_path):
        error(f"Base de datos no encontrada: {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todos los nodos
        cursor.execute("""
            SELECT node_id, public_ip, port, node_type, is_genesis, status, created_at, last_seen
            FROM network_nodes 
            ORDER BY created_at
        """)
        
        nodes = cursor.fetchall()
        conn.close()
        
        if nodes:
            print(f"\n📊 Nodos encontrados en la base de datos: {len(nodes)}")
            print("-" * 80)
            
            for i, node in enumerate(nodes, 1):
                node_id, public_ip, port, node_type, is_genesis, status, created_at, last_seen = node
                genesis_mark = "🔥 GÉNESIS" if is_genesis else "📡 Regular"
                
                print(f"{i}. {node_id}")
                print(f"   {genesis_mark} | {node_type} | {status}")
                print(f"   IP: {public_ip}:{port}")
                print(f"   Creado: {created_at}")
                print(f"   Última vez visto: {last_seen}")
                print()
        else:
            log("No hay nodos en la base de datos")
        
        return nodes
        
    except Exception as e:
        error(f"Error leyendo base de datos: {e}")
        return []

def clean_all_nodes():
    """Limpiar todos los nodos de la base de datos"""
    log("Limpiando TODOS los nodos de la base de datos...")
    
    db_path = "/opt/playergold/src/network_coordinator.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar nodos antes de limpiar
        cursor.execute("SELECT COUNT(*) FROM network_nodes")
        count_before = cursor.fetchone()[0]
        
        # Limpiar todos los nodos
        cursor.execute("DELETE FROM network_nodes")
        
        # Resetear el autoincrement si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='network_nodes'")
        
        conn.commit()
        
        # Verificar limpieza
        cursor.execute("SELECT COUNT(*) FROM network_nodes")
        count_after = cursor.fetchone()[0]
        
        conn.close()
        
        success(f"Nodos eliminados: {count_before} → {count_after}")
        
        if count_after == 0:
            success("Base de datos de nodos completamente limpia")
            return True
        else:
            error(f"Aún quedan {count_after} nodos en la base de datos")
            return False
            
    except Exception as e:
        error(f"Error limpiando base de datos: {e}")
        return False

def verify_certificates_intact():
    """Verificar que los certificados AES siguen intactos"""
    log("Verificando que los certificados AES siguen intactos...")
    
    cert_dir = "/opt/playergold/data/.AES_certificate"
    
    required_files = [
        "master_key.bin",
        "certificate_info.json",
        "public_key.pem"
    ]
    
    all_present = True
    
    for file_name in required_files:
        file_path = os.path.join(cert_dir, file_name)
        if os.path.exists(file_path):
            success(f"✅ {file_name} - Presente")
        else:
            error(f"❌ {file_name} - FALTA")
            all_present = False
    
    if all_present:
        success("Todos los certificados AES están intactos")
        return True
    else:
        error("Algunos certificados AES faltan")
        return False

def start_coordinator():
    """Iniciar el coordinador"""
    log("Iniciando servicio del coordinador...")
    try:
        result = subprocess.run(['systemctl', 'start', 'playergold-coordinator'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            success("Servicio iniciado")
            
            # Verificar estado
            import time
            time.sleep(2)
            
            result = subprocess.run(['systemctl', 'is-active', 'playergold-coordinator'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() == 'active':
                success("Servicio está activo")
                return True
            else:
                warning("Servicio iniciado pero no está activo")
                return False
        else:
            error(f"Error iniciando servicio: {result.stderr}")
            return False
    except Exception as e:
        error(f"Error iniciando servicio: {e}")
        return False

def test_coordinator_functionality():
    """Probar que el coordinador sigue funcionando"""
    log("Probando funcionalidad del coordinador...")
    
    import time
    time.sleep(3)  # Esperar a que se inicie completamente
    
    try:
        import requests
        
        # Probar endpoint de stats
        response = requests.get(
            "https://playergold.es/api/v1/stats",
            headers={"User-Agent": "PlayerGold-Wallet/1.0.0"},
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            success(f"Coordinador funcionando - Nodos activos: {data.get('active_nodes', 0)}")
            return True
        else:
            error(f"Coordinador no responde correctamente: {response.status_code}")
            return False
            
    except Exception as e:
        error(f"Error probando coordinador: {e}")
        return False

def main():
    """Función principal"""
    print("🧹 PlayerGold Network Coordinator - Clean Node Data")
    print("=" * 60)
    
    check_permissions()
    
    try:
        # Mostrar nodos actuales
        nodes = show_current_nodes()
        
        if not nodes:
            log("No hay nodos para limpiar")
            return
        
        # Confirmar limpieza
        print("\n" + "⚠️ " * 20)
        print("ADVERTENCIA: Esto eliminará TODOS los nodos de la base de datos")
        print("Los certificados AES y la configuración se mantendrán intactos")
        print("⚠️ " * 20)
        
        response = input(f"\n¿Estás seguro de que quieres eliminar {len(nodes)} nodos? (y/N): ")
        
        if response.lower() != 'y':
            log("Operación cancelada")
            return
        
        # Parar servicio
        stop_coordinator()
        
        # Limpiar nodos
        if not clean_all_nodes():
            sys.exit(1)
        
        # Verificar certificados
        if not verify_certificates_intact():
            warning("Algunos certificados pueden estar dañados")
        
        # Iniciar servicio
        if not start_coordinator():
            error("No se pudo iniciar el servicio")
            sys.exit(1)
        
        # Probar funcionalidad
        if test_coordinator_functionality():
            print("\n" + "=" * 60)
            success("🎉 Limpieza completada exitosamente!")
            print("\n✅ Estado después de la limpieza:")
            print("   • Base de datos de nodos: LIMPIA (0 nodos)")
            print("   • Certificados AES: INTACTOS")
            print("   • Coordinador: FUNCIONANDO")
            print("   • Listo para prueba limpia con nodos reales")
            
            print("\n🚀 Próximos pasos:")
            print("   1. Inicia la wallet del escritorio")
            print("   2. Inicia la wallet del portátil")
            print("   3. Ambas deberían registrarse como nodos génesis")
            print("   4. Deberían encontrarse y crear el bloque génesis")
            
        else:
            warning("Limpieza completada pero el coordinador tiene problemas")
        
    except Exception as e:
        error(f"Error durante la limpieza: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()