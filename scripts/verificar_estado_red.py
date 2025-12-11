#!/usr/bin/env python3
"""
Script para verificar el estado actual de la red testnet
"""

import os
import socket
import subprocess
import time
import json
from datetime import datetime

def load_env_local():
    """Cargar variables de entorno desde .env.local"""
    env_file = '.env.local'
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails
            with open(env_file, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

# Cargar variables de entorno al inicio
load_env_local()

def get_local_ip():
    """Obtener IP local de la máquina"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except:
        return "127.0.0.1"

def test_port_connectivity(ip, port):
    """Probar conectividad a un puerto específico"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def check_local_node_running():
    """Verificar si el nodo local está ejecutándose"""
    try:
        result = subprocess.run([
            'netstat', '-ano'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if ':18333' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        return True, pid
        
        return False, None
    except:
        return False, None

def main():
    print("=" * 60)
    print("🔍 VERIFICACIÓN RÁPIDA DE ESTADO - RED TESTNET")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Obtener información local
    local_ip = get_local_ip()
    node1_ip = os.getenv('NODE1_IP', '192.168.1.100')
    node2_ip = os.getenv('NODE2_IP', '192.168.1.101')
    port = 18333
    
    # Determinar qué nodo somos
    if local_ip == node1_ip:
        current_node = "Nodo 1 (Principal)"
        remote_ip = node2_ip
    elif local_ip == node2_ip:
        current_node = "Nodo 2 (Portátil)"
        remote_ip = node1_ip
    else:
        current_node = f"Nodo Desconocido ({local_ip})"
        remote_ip = node1_ip
    
    print(f"🖥️  Esta máquina: {current_node}")
    print(f"🎯 Nodo remoto: {remote_ip}:{port}")
    print()
    
    # Verificar nodo local
    print("📍 NODO LOCAL:")
    local_running, local_pid = check_local_node_running()
    if local_running:
        print(f"   ✅ Ejecutándose (PID: {local_pid})")
    else:
        print(f"   ❌ No está ejecutándose")
        print(f"   💡 Iniciar con: scripts\\start_node{'1' if local_ip == node1_ip else '2'}_testnet_seguro.bat")
    
    # Verificar nodo remoto
    print("🌐 NODO REMOTO:")
    remote_reachable = test_port_connectivity(remote_ip, port)
    if remote_reachable:
        print(f"   ✅ Accesible en {remote_ip}:{port}")
    else:
        print(f"   ❌ No accesible en {remote_ip}:{port}")
        print(f"   💡 Verificar que esté ejecutándose en {remote_ip}")
    
    # Estado general
    print()
    print("📊 ESTADO GENERAL:")
    if local_running and remote_reachable:
        print("   🎉 ¡RED TESTNET OPERATIVA!")
        print("   ✅ Ambos nodos están ejecutándose")
        print("   ✅ Conectividad entre nodos OK")
        print()
        print("   💡 Si aún ves '0 peers' en los logs:")
        print("      - Espera 30-60 segundos más")
        print("      - Los nodos pueden tardar en conectarse")
        print("      - Verifica los logs para errores específicos")
    elif local_running and not remote_reachable:
        print("   ⚠️  NODO LOCAL OK, PROBLEMA CON NODO REMOTO")
        print("   ✅ Tu nodo está ejecutándose")
        print("   ❌ No se puede conectar al nodo remoto")
        print()
        print("   🔧 SOLUCIONES:")
        print(f"      1. Iniciar nodo en {remote_ip}")
        print(f"      2. Verificar firewall en {remote_ip}")
        print(f"      3. Probar conectividad: ping {remote_ip}")
    elif not local_running and remote_reachable:
        print("   ⚠️  NODO REMOTO OK, PROBLEMA LOCAL")
        print("   ❌ Tu nodo no está ejecutándose")
        print("   ✅ El nodo remoto está accesible")
        print()
        print("   🔧 SOLUCIÓN:")
        print(f"      Iniciar tu nodo: scripts\\start_node{'1' if local_ip == node1_ip else '2'}_testnet_seguro.bat")
    else:
        print("   ❌ AMBOS NODOS CON PROBLEMAS")
        print("   ❌ Tu nodo no está ejecutándose")
        print("   ❌ El nodo remoto no es accesible")
        print()
        print("   🔧 SOLUCIONES:")
        print("      1. Ejecutar scripts\\iniciar_red_testnet_completa.bat")
        print("      2. Configurar firewall en ambas máquinas")
        print("      3. Verificar conectividad de red")
    
    print()
    print("🛠️  HERRAMIENTAS ADICIONALES:")
    print("   📋 Diagnóstico completo: python scripts\\diagnosticar_conexion_nodos.py")
    print("   🔍 Verificar puerto: python scripts\\diagnosticar_puerto_ocupado.py")
    print("   🌐 Monitoreo de red: python scripts\\diagnostico_red_testnet.py")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Verificación cancelada")
    except Exception as e:
        print(f"\n❌ Error: {e}")