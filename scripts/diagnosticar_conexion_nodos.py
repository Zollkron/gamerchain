#!/usr/bin/env python3
"""
Script para diagnosticar y solucionar problemas de conexión entre nodos testnet
"""

import os
import sys
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

def print_header(titulo):
    """Imprimir encabezado de sección"""
    print(f"\n{'='*60}")
    print(f"🔍 {titulo}")
    print(f"{'='*60}")

def test_port_connectivity(ip, port):
    """Probar conectividad a un puerto específico"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error probando conectividad: {e}")
        return False

def get_local_ip():
    """Obtener IP local de la máquina"""
    try:
        # Conectar a un servidor externo para obtener nuestra IP local
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except:
        return "127.0.0.1"

def check_firewall_rules():
    """Verificar reglas de firewall para puerto 18333"""
    try:
        result = subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'show', 'rule', 
            'name="PlayerGold Testnet - Entrada"'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "PlayerGold Testnet - Entrada" in result.stdout:
            return True, "Regla de firewall encontrada"
        else:
            return False, "Regla de firewall no encontrada"
    except Exception as e:
        return False, f"Error verificando firewall: {e}"

def check_process_listening(port):
    """Verificar si hay un proceso escuchando en el puerto"""
    try:
        result = subprocess.run([
            'netstat', '-ano'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        address = parts[1]
                        return True, f"Proceso PID {pid} escuchando en {address}"
            
            return False, f"Ningún proceso escuchando en puerto {port}"
        else:
            return False, "Error ejecutando netstat"
    except Exception as e:
        return False, f"Error verificando procesos: {e}"

def main():
    """Función principal de diagnóstico"""
    print_header("DIAGNÓSTICO DE CONEXIÓN NODOS TESTNET")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Obtener IP local
    local_ip = get_local_ip()
    print(f"🖥️  IP Local detectada: {local_ip}")
    
    # IPs de los nodos testnet (desde variables de entorno)
    node1_ip = os.getenv('NODE1_IP', '192.168.1.100')
    node2_ip = os.getenv('NODE2_IP', '192.168.1.101')
    port = 18333
    
    print(f"🎯 Nodos objetivo:")
    print(f"   Nodo 1: {node1_ip}:{port}")
    print(f"   Nodo 2: {node2_ip}:{port}")
    
    # Determinar qué nodo somos
    current_node = None
    if local_ip == node1_ip:
        current_node = "Nodo 1"
        target_ip = node2_ip
    elif local_ip == node2_ip:
        current_node = "Nodo 2"
        target_ip = node1_ip
    else:
        print(f"⚠️  Esta máquina ({local_ip}) no coincide con ningún nodo configurado")
        target_ip = node1_ip if local_ip != node1_ip else node2_ip
    
    if current_node:
        print(f"📍 Esta máquina es: {current_node}")
        print(f"🎯 Nodo objetivo: {target_ip}:{port}")
    
    # 1. Verificar si nuestro nodo está escuchando
    print_header("1. VERIFICACIÓN LOCAL")
    
    listening, listen_msg = check_process_listening(port)
    if listening:
        print(f"✅ {listen_msg}")
    else:
        print(f"❌ {listen_msg}")
        print("💡 Solución: Iniciar el nodo local")
        print(f"   scripts\\start_node{'1' if local_ip == node1_ip else '2'}_testnet_seguro.bat")
    
    # 2. Verificar firewall
    print_header("2. VERIFICACIÓN DE FIREWALL")
    
    firewall_ok, firewall_msg = check_firewall_rules()
    if firewall_ok:
        print(f"✅ {firewall_msg}")
    else:
        print(f"❌ {firewall_msg}")
        print("💡 Solución: Configurar firewall")
        print("   scripts\\configurar_firewall_testnet.bat (como Administrador)")
    
    # 3. Verificar conectividad al nodo remoto
    print_header("3. VERIFICACIÓN DE CONECTIVIDAD REMOTA")
    
    print(f"🔍 Probando conexión a {target_ip}:{port}...")
    
    if test_port_connectivity(target_ip, port):
        print(f"✅ Conectividad exitosa a {target_ip}:{port}")
    else:
        print(f"❌ No se puede conectar a {target_ip}:{port}")
        
        print("\n🔧 POSIBLES CAUSAS Y SOLUCIONES:")
        print("1. 🖥️  El nodo remoto no está ejecutándose")
        print(f"   - Iniciar nodo en {target_ip}")
        print("   - Verificar que el script esté corriendo")
        
        print("2. 🔥 Firewall bloqueando conexión")
        print("   - Ejecutar configurar_firewall_testnet.bat en ambas máquinas")
        print("   - Verificar Windows Defender Firewall")
        
        print("3. 🌐 Problema de red")
        print(f"   - Verificar que ambas máquinas estén en la misma red")
        print(f"   - Ping a {target_ip}: ping {target_ip}")
        
        print("4. 🔌 Puerto ocupado por otro proceso")
        print("   - Ejecutar scripts\\diagnosticar_puerto_ocupado.py")
        print("   - Liberar puerto con scripts\\liberar_puerto_18333.bat")
    
    # 4. Verificar configuración de red
    print_header("4. VERIFICACIÓN DE CONFIGURACIÓN")
    
    try:
        # Verificar que existe el archivo de configuración testnet
        config_file = "config/testnet/testnet.yaml"
        if os.path.exists(config_file):
            print(f"✅ Archivo de configuración encontrado: {config_file}")
            
            # Leer configuración
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            bootstrap_nodes = config.get('bootstrap_nodes', [])
            network_id = config.get('network_id', 'unknown')
            
            print(f"📋 Network ID: {network_id}")
            print(f"📋 Bootstrap nodes configurados:")
            for node in bootstrap_nodes:
                print(f"   - {node}")
                
            # Verificar que nuestros nodos están en la lista
            expected_nodes = [f"{node1_ip}:18333", f"{node2_ip}:18333"]
            for expected in expected_nodes:
                if expected in bootstrap_nodes:
                    print(f"   ✅ {expected} configurado correctamente")
                else:
                    print(f"   ❌ {expected} NO encontrado en bootstrap_nodes")
        else:
            print(f"❌ Archivo de configuración no encontrado: {config_file}")
            print("💡 Ejecutar: python scripts\\setup_testnet_genesis.py")
            
    except Exception as e:
        print(f"❌ Error leyendo configuración: {e}")
    
    # 5. Resumen y recomendaciones
    print_header("5. RESUMEN Y PRÓXIMOS PASOS")
    
    if listening and firewall_ok:
        if test_port_connectivity(target_ip, port):
            print("🎉 ¡DIAGNÓSTICO EXITOSO!")
            print("✅ Nodo local ejecutándose")
            print("✅ Firewall configurado")
            print("✅ Conectividad al nodo remoto")
            print("\n💡 Si los nodos aún muestran 0 peers:")
            print("1. Esperar 30-60 segundos para que se conecten")
            print("2. Verificar logs de los nodos para errores")
            print("3. Reiniciar ambos nodos si es necesario")
        else:
            print("⚠️  PROBLEMA DE CONECTIVIDAD")
            print("✅ Nodo local OK")
            print("✅ Firewall OK")
            print("❌ No se puede conectar al nodo remoto")
            print(f"\n🔧 ACCIÓN REQUERIDA:")
            print(f"1. Verificar que el nodo en {target_ip} esté ejecutándose")
            print(f"2. Configurar firewall en {target_ip}")
            print(f"3. Verificar conectividad de red: ping {target_ip}")
    else:
        print("⚠️  PROBLEMAS LOCALES DETECTADOS")
        
        if not listening:
            print("❌ Nodo local no está ejecutándose")
            print("🔧 Iniciar nodo local primero")
        
        if not firewall_ok:
            print("❌ Firewall no configurado")
            print("🔧 Ejecutar configurar_firewall_testnet.bat como Administrador")
        
        print(f"\n📋 ORDEN DE EJECUCIÓN RECOMENDADO:")
        print("1. scripts\\configurar_firewall_testnet.bat (Administrador)")
        print("2. scripts\\liberar_puerto_18333.bat")
        print(f"3. scripts\\start_node{'1' if local_ip == node1_ip else '2'}_testnet_seguro.bat")
        print("4. Ejecutar este diagnóstico nuevamente")
    
    print(f"\n🕒 Diagnóstico completado: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Diagnóstico cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        sys.exit(1)