#!/usr/bin/env python3
"""
Script para verificar la conexión entre nodos testnet PlayerGold
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Configuración de nodos (usando variables de entorno)
NODOS = {
    'nodo1': {
        'ip': os.getenv('NODE1_IP', '192.168.1.100'),
        'puerto': int(os.getenv('P2P_PORT', '18333')),
        'nombre': 'Nodo 1 (Principal)'
    },
    'nodo2': {
        'ip': os.getenv('NODE2_IP', '192.168.1.101'), 
        'puerto': int(os.getenv('P2P_PORT', '18333')),
        'nombre': 'Nodo 2 (Portátil)'
    }
}

async def verificar_nodo(session, nodo_id, config):
    """Verificar el estado de un nodo individual"""
    url = f"http://{config['ip']}:{config['puerto']}/api/status"
    
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'nodo': nodo_id,
                    'nombre': config['nombre'],
                    'estado': 'CONECTADO',
                    'peers': data.get('peers', 0),
                    'altura_bloque': data.get('block_height', 0),
                    'minando': data.get('mining', False),
                    'modelo_ia': data.get('ai_model', 'No cargado')
                }
            else:
                return {
                    'nodo': nodo_id,
                    'nombre': config['nombre'],
                    'estado': 'ERROR HTTP',
                    'error': f"Status {response.status}"
                }
                
    except asyncio.TimeoutError:
        return {
            'nodo': nodo_id,
            'nombre': config['nombre'],
            'estado': 'TIMEOUT',
            'error': 'No responde en 5 segundos'
        }
    except Exception as e:
        return {
            'nodo': nodo_id,
            'nombre': config['nombre'],
            'estado': 'ERROR',
            'error': str(e)
        }

async def verificar_conectividad_red():
    """Verificar conectividad básica de red"""
    import subprocess
    
    resultados = {}
    
    for nodo_id, config in NODOS.items():
        try:
            # Ping básico
            result = subprocess.run(
                ['ping', '-n', '1', config['ip']], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                resultados[nodo_id] = 'PING OK'
            else:
                resultados[nodo_id] = 'PING FAILED'
                
        except Exception as e:
            resultados[nodo_id] = f'PING ERROR: {e}'
    
    return resultados

async def main():
    print("🔍 Verificación de Conexión de Nodos PlayerGold Testnet")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Verificar conectividad de red básica
    print("1. 🌐 Verificando conectividad de red...")
    ping_results = await verificar_conectividad_red()
    
    for nodo_id, resultado in ping_results.items():
        config = NODOS[nodo_id]
        status_icon = "✅" if "OK" in resultado else "❌"
        print(f"   {status_icon} {config['nombre']} ({config['ip']}): {resultado}")
    
    print()
    
    # 2. Verificar estado de nodos
    print("2. 🖥️  Verificando estado de nodos...")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for nodo_id, config in NODOS.items():
            task = verificar_nodo(session, nodo_id, config)
            tasks.append(task)
        
        resultados = await asyncio.gather(*tasks, return_exceptions=True)
        
        nodos_activos = 0
        total_peers = 0
        
        for resultado in resultados:
            if isinstance(resultado, dict):
                nombre = resultado['nombre']
                estado = resultado['estado']
                
                if estado == 'CONECTADO':
                    nodos_activos += 1
                    peers = resultado.get('peers', 0)
                    total_peers += peers
                    altura = resultado.get('altura_bloque', 0)
                    minando = resultado.get('minando', False)
                    modelo = resultado.get('modelo_ia', 'No cargado')
                    
                    print(f"   ✅ {nombre}: ACTIVO")
                    print(f"      - Peers conectados: {peers}")
                    print(f"      - Altura de bloque: {altura}")
                    print(f"      - Minando: {'Sí' if minando else 'No'}")
                    print(f"      - Modelo IA: {modelo}")
                else:
                    error = resultado.get('error', 'Error desconocido')
                    print(f"   ❌ {nombre}: {estado}")
                    print(f"      - Error: {error}")
                
                print()
    
    # 3. Resumen final
    print("3. 📊 Resumen de la Red")
    print(f"   - Nodos activos: {nodos_activos}/2")
    print(f"   - Total de conexiones peer: {total_peers}")
    
    if nodos_activos == 2:
        print("   🎉 ¡Red testnet completamente operativa!")
        if total_peers >= 2:
            print("   🔗 Los nodos están conectados entre sí")
        else:
            print("   ⚠️  Los nodos no están conectados entre sí")
    elif nodos_activos == 1:
        print("   ⚠️  Solo un nodo activo - Iniciar el segundo nodo")
    else:
        print("   ❌ Ningún nodo activo - Verificar configuración")
    
    print()
    print("💡 Próximos pasos:")
    if nodos_activos < 2:
        print("   1. Iniciar nodos faltantes con los scripts .bat")
        print("   2. Verificar firewall (puerto 18333)")
        print("   3. Comprobar que ambas máquinas están en la misma red")
    else:
        print("   1. Abrir wallets en ambas máquinas")
        print("   2. Descargar modelos IA en la pestaña Minería")
        print("   3. Iniciar minería para comenzar el consenso PoAIP")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Verificación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        sys.exit(1)