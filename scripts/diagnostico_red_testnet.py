#!/usr/bin/env python3
"""
Script de diagnóstico para la red testnet PlayerGold
Identifica problemas de conectividad entre nodos
"""

import asyncio
import socket
import subprocess
import sys
import json
import os
from datetime import datetime

# Configuración de nodos testnet (usando variables de entorno)
NODOS_TESTNET = {
    'nodo1': {
        'ip': os.getenv('NODE1_IP', '192.168.1.100'),
        'puerto': int(os.getenv('P2P_PORT', '18333')),
        'nombre': 'Nodo 1 (Principal)',
        'node_id': 'validator-node-1'
    },
    'nodo2': {
        'ip': os.getenv('NODE2_IP', '192.168.1.101'), 
        'puerto': int(os.getenv('P2P_PORT', '18333')),
        'nombre': 'Nodo 2 (Portátil)',
        'node_id': 'validator-node-2'
    }
}

def print_header(titulo):
    """Imprimir encabezado de sección"""
    print(f"\n{'='*60}")
    print(f"🔍 {titulo}")
    print(f"{'='*60}")

def print_resultado(test, resultado, detalles=""):
    """Imprimir resultado de test"""
    icono = "✅" if resultado else "❌"
    print(f"{icono} {test}")
    if detalles:
        print(f"   {detalles}")

async def test_ping(ip):
    """Test de ping básico"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '3000', ip], 
                capture_output=True, 
                text=True,
                timeout=5
            )
        else:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '3', ip], 
                capture_output=True, 
                text=True,
                timeout=5
            )
        
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

async def test_puerto_abierto(ip, puerto):
    """Test si el puerto está abierto"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, puerto))
        sock.close()
        return result == 0
    except Exception:
        return False

async def test_firewall_windows():
    """Test configuración de firewall en Windows"""
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Buscar reglas para puerto 18333
        reglas_18333 = []
        if "18333" in result.stdout:
            for linea in result.stdout.split('\n'):
                if "18333" in linea:
                    reglas_18333.append(linea.strip())
        
        return len(reglas_18333) > 0, reglas_18333
    except Exception as e:
        return False, [str(e)]

async def test_procesos_activos():
    """Test si hay procesos Python ejecutándose (nodos)"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                capture_output=True,
                text=True,
                timeout=5
            )
        else:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
        
        procesos_python = []
        for linea in result.stdout.split('\n'):
            if 'python' in linea.lower() and 'start_testnet_node' in linea:
                procesos_python.append(linea.strip())
        
        return len(procesos_python) > 0, procesos_python
    except Exception as e:
        return False, [str(e)]

async def test_configuracion_genesis():
    """Test si los archivos de configuración existen"""
    import os
    
    archivos_requeridos = [
        'data/testnet/genesis.json',
        'config/testnet/node1.yaml',
        'config/testnet/node2.yaml',
        'config/testnet/testnet.yaml'
    ]
    
    archivos_encontrados = []
    archivos_faltantes = []
    
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            archivos_encontrados.append(archivo)
        else:
            archivos_faltantes.append(archivo)
    
    return len(archivos_faltantes) == 0, {
        'encontrados': archivos_encontrados,
        'faltantes': archivos_faltantes
    }

async def test_red_local():
    """Test configuración de red local"""
    try:
        # Obtener IP local
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip_local = sock.getsockname()[0]
        sock.close()
        
        # Verificar si estamos en la red correcta
        red_correcta = ip_local.startswith('192.168.1.')
        
        return red_correcta, {
            'ip_local': ip_local,
            'red_esperada': '192.168.1.x',
            'en_red_correcta': red_correcta
        }
    except Exception as e:
        return False, {'error': str(e)}

async def main():
    """Función principal de diagnóstico"""
    print_header("DIAGNÓSTICO DE RED TESTNET PLAYERGOLD")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Configuración de red local
    print_header("1. CONFIGURACIÓN DE RED LOCAL")
    red_ok, red_info = await test_red_local()
    if red_ok:
        print_resultado("Red local configurada correctamente", True, 
                       f"IP local: {red_info['ip_local']}")
    else:
        print_resultado("Problema con red local", False, 
                       f"Error: {red_info.get('error', 'IP no está en 192.168.1.x')}")
    
    # Test 2: Archivos de configuración
    print_header("2. ARCHIVOS DE CONFIGURACIÓN")
    config_ok, config_info = await test_configuracion_genesis()
    print_resultado("Archivos de configuración", config_ok)
    
    if config_info['encontrados']:
        print("   📁 Archivos encontrados:")
        for archivo in config_info['encontrados']:
            print(f"      ✅ {archivo}")
    
    if config_info['faltantes']:
        print("   📁 Archivos faltantes:")
        for archivo in config_info['faltantes']:
            print(f"      ❌ {archivo}")
    
    # Test 3: Procesos activos
    print_header("3. PROCESOS DE NODOS")
    procesos_ok, procesos_info = await test_procesos_activos()
    print_resultado("Nodos ejecutándose", procesos_ok)
    
    if procesos_info:
        print("   🖥️  Procesos encontrados:")
        for proceso in procesos_info:
            print(f"      • {proceso}")
    
    # Test 4: Conectividad entre nodos
    print_header("4. CONECTIVIDAD ENTRE NODOS")
    
    for nodo_id, config in NODOS_TESTNET.items():
        print(f"\n🖥️  Probando {config['nombre']} ({config['ip']}):")
        
        # Test ping
        ping_ok, ping_info = await test_ping(config['ip'])
        print_resultado(f"Ping a {config['ip']}", ping_ok, 
                       "Responde" if ping_ok else "No responde")
        
        # Test puerto
        puerto_ok = await test_puerto_abierto(config['ip'], config['puerto'])
        print_resultado(f"Puerto {config['puerto']} abierto", puerto_ok,
                       "Accesible" if puerto_ok else "Cerrado o filtrado")
    
    # Test 5: Firewall (solo Windows)
    if sys.platform == "win32":
        print_header("5. CONFIGURACIÓN DE FIREWALL")
        firewall_ok, firewall_info = await test_firewall_windows()
        print_resultado("Reglas de firewall para puerto 18333", firewall_ok)
        
        if firewall_info:
            print("   🔥 Reglas encontradas:")
            for regla in firewall_info[:3]:  # Mostrar solo las primeras 3
                print(f"      • {regla}")
    
    # Resumen y recomendaciones
    print_header("RESUMEN Y RECOMENDACIONES")
    
    problemas = []
    soluciones = []
    
    if not red_ok:
        problemas.append("❌ Red local no configurada correctamente")
        soluciones.append("🔧 Verificar que ambas máquinas estén en la red 192.168.1.x")
    
    if not config_ok:
        problemas.append("❌ Archivos de configuración faltantes")
        soluciones.append("🔧 Ejecutar setup_testnet_genesis.py para generar configuración")
    
    if not procesos_ok:
        problemas.append("❌ Nodos no están ejecutándose")
        soluciones.append("🔧 Iniciar nodos con start_node1_testnet.bat y start_node2_testnet.bat")
    
    # Verificar conectividad específica
    conectividad_problemas = 0
    for nodo_id, config in NODOS_TESTNET.items():
        ping_ok, _ = await test_ping(config['ip'])
        puerto_ok = await test_puerto_abierto(config['ip'], config['puerto'])
        
        if not ping_ok:
            conectividad_problemas += 1
        if not puerto_ok:
            conectividad_problemas += 1
    
    if conectividad_problemas > 0:
        problemas.append(f"❌ Problemas de conectividad ({conectividad_problemas} tests fallaron)")
        soluciones.append("🔧 Abrir puerto 18333 en firewall de Windows")
        soluciones.append("🔧 Verificar que no hay antivirus bloqueando conexiones")
    
    if not problemas:
        print("🎉 ¡Todo parece estar configurado correctamente!")
        print("\n💡 Si los nodos siguen mostrando '0 peers', el problema puede ser:")
        print("   • Los nodos no están intentando conectarse automáticamente")
        print("   • Falta implementar la conexión a bootstrap nodes")
        print("   • Problema en el código de handshake P2P")
    else:
        print("⚠️  Se encontraron los siguientes problemas:")
        for problema in problemas:
            print(f"   {problema}")
        
        print("\n🔧 Soluciones recomendadas:")
        for solucion in soluciones:
            print(f"   {solucion}")
    
    print("\n📋 Comandos útiles para solucionar problemas:")
    print("   • Abrir puerto en firewall:")
    print("     netsh advfirewall firewall add rule name=\"PlayerGold\" dir=in action=allow protocol=TCP localport=18333")
    print("   • Verificar procesos Python:")
    print("     tasklist /FI \"IMAGENAME eq python.exe\"")
    print("   • Test manual de conectividad:")
    print(f"     telnet {os.getenv('NODE1_IP', '192.168.1.100')} {os.getenv('P2P_PORT', '18333')}")
    print(f"     telnet {os.getenv('NODE2_IP', '192.168.1.101')} {os.getenv('P2P_PORT', '18333')}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Diagnóstico cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        sys.exit(1)