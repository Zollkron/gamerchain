#!/usr/bin/env python3
"""
Script para generar archivo .env.local de forma segura
"""

import os
import socket
import sys
from pathlib import Path

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

def main():
    """Función principal"""
    print("=" * 60)
    print("🔧 GENERADOR DE CONFIGURACIÓN SEGURA - PLAYERGOLD")
    print("=" * 60)
    print()
    
    # Verificar si ya existe .env.local
    env_file = Path('.env.local')
    if env_file.exists():
        print("⚠️  El archivo .env.local ya existe.")
        respuesta = input("¿Deseas sobrescribirlo? (s/N): ").lower().strip()
        if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada.")
            return
    
    # Obtener IP local actual
    local_ip = get_local_ip()
    print(f"🖥️  IP local detectada: {local_ip}")
    print()
    
    # Solicitar configuración
    print("📋 Configuración de Nodos:")
    print("Ingresa las IPs de tus dos nodos testnet:")
    print()
    
    # IP Nodo 1
    node1_ip = input(f"🔹 IP del Nodo 1 (Principal) [{local_ip}]: ").strip()
    if not node1_ip:
        node1_ip = local_ip
    
    # IP Nodo 2
    node2_ip = input("🔹 IP del Nodo 2 (Secundario): ").strip()
    while not node2_ip:
        print("❌ La IP del Nodo 2 es requerida.")
        node2_ip = input("🔹 IP del Nodo 2 (Secundario): ").strip()
    
    # Determinar nodo actual
    print()
    print("📍 Identificación del Nodo Actual:")
    print(f"Tu IP local es: {local_ip}")
    
    if local_ip == node1_ip:
        current_node = "1"
        print("✅ Esta máquina será el Nodo 1 (Principal)")
    elif local_ip == node2_ip:
        current_node = "2"
        print("✅ Esta máquina será el Nodo 2 (Secundario)")
    else:
        print("⚠️  Tu IP local no coincide con ninguno de los nodos configurados.")
        print("Selecciona manualmente:")
        print("1. Nodo 1 (Principal)")
        print("2. Nodo 2 (Secundario)")
        
        while True:
            opcion = input("Selecciona (1 o 2): ").strip()
            if opcion in ['1', '2']:
                current_node = opcion
                break
            print("❌ Selecciona 1 o 2")
    
    # Configuración adicional
    print()
    print("⚙️  Configuración Adicional:")
    
    network_id = input("🔹 Network ID [playergold-testnet-genesis]: ").strip()
    if not network_id:
        network_id = "playergold-testnet-genesis"
    
    p2p_port = input("🔹 Puerto P2P [18333]: ").strip()
    if not p2p_port:
        p2p_port = "18333"
    
    api_port = input("🔹 Puerto API [18080]: ").strip()
    if not api_port:
        api_port = "18080"
    
    # Generar contenido del archivo
    env_content = f"""# PlayerGold Testnet Configuration - ARCHIVO LOCAL
# ⚠️  ESTE ARCHIVO CONTIENE INFORMACIÓN SENSIBLE - NO COMMITEAR
# Generado automáticamente el {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# IPs de los nodos (específicas de tu red local)
NODE1_IP={node1_ip}
NODE2_IP={node2_ip}

# Configuración del nodo actual ({current_node} = {'Principal' if current_node == '1' else 'Secundario'})
CURRENT_NODE={current_node}

# Configuración de red
NETWORK_ID={network_id}
P2P_PORT={p2p_port}
API_PORT={api_port}

# Configuración de genesis (se generarán automáticamente)
GENESIS_TIME=2025-01-01T00:00:00.000000
INITIAL_SUPPLY=1000000
VALIDATOR_STAKE=100000

# Configuración de minería
CHALLENGE_TIMEOUT=0.3
MIN_VALIDATORS=2

# Direcciones de validadores (se generarán con setup_testnet_genesis.py)
NODE1_VALIDATOR_ADDRESS=PGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NODE2_VALIDATOR_ADDRESS=PGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Claves públicas de validadores (se generarán con setup_testnet_genesis.py)
NODE1_PUBLIC_KEY=pub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NODE2_PUBLIC_KEY=pub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""
    
    # Escribir archivo
    try:
        with open('.env.local', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print()
        print("✅ Archivo .env.local generado exitosamente!")
        print()
        print("📋 Configuración guardada:")
        print(f"   🔹 Nodo 1 (Principal): {node1_ip}")
        print(f"   🔹 Nodo 2 (Secundario): {node2_ip}")
        print(f"   🔹 Esta máquina: Nodo {current_node}")
        print(f"   🔹 Network ID: {network_id}")
        print(f"   🔹 Puerto P2P: {p2p_port}")
        print()
        print("🔒 IMPORTANTE:")
        print("   • Este archivo está en .gitignore y NO se commitea")
        print("   • Copia este script a la otra máquina y ejecútalo allí")
        print("   • En la otra máquina, configura CURRENT_NODE con el valor opuesto")
        print()
        print("🚀 Próximos pasos:")
        print("   1. Ejecutar en la otra máquina: python scripts/generar_env_local.py")
        print("   2. Generar genesis: python scripts/setup_testnet_genesis.py")
        print("   3. Iniciar red: scripts\\iniciar_red_testnet_completa.bat")
        
    except Exception as e:
        print(f"❌ Error escribiendo archivo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)