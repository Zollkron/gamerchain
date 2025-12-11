#!/usr/bin/env python3
"""
Script para diagnosticar qué proceso está ocupando el puerto 18333
"""

import subprocess
import sys
import re
import psutil
from datetime import datetime

def print_header(titulo):
    """Imprimir encabezado de sección"""
    print(f"\n{'='*60}")
    print(f"🔍 {titulo}")
    print(f"{'='*60}")

def encontrar_proceso_por_puerto(puerto):
    """Encontrar qué proceso está usando un puerto específico"""
    try:
        # Usar psutil para encontrar conexiones
        conexiones = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == puerto:
                        conexiones.append({
                            'pid': proc.info['pid'],
                            'nombre': proc.info['name'],
                            'cmdline': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else '',
                            'estado': conn.status,
                            'direccion': f"{conn.laddr.ip}:{conn.laddr.port}"
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return conexiones
    except Exception as e:
        print(f"❌ Error usando psutil: {e}")
        return []

def usar_netstat_windows(puerto):
    """Usar netstat en Windows para encontrar el proceso"""
    try:
        # Ejecutar netstat
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        conexiones = []
        for linea in result.stdout.split('\n'):
            if f':{puerto}' in linea and 'LISTENING' in linea:
                partes = linea.split()
                if len(partes) >= 5:
                    pid = partes[-1]
                    direccion = partes[1]
                    
                    # Obtener nombre del proceso
                    try:
                        tasklist_result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        nombre_proceso = "Desconocido"
                        if tasklist_result.returncode == 0:
                            lineas_tasklist = tasklist_result.stdout.strip().split('\n')
                            if lineas_tasklist and lineas_tasklist[0]:
                                nombre_proceso = lineas_tasklist[0].split(',')[0].strip('"')
                        
                        conexiones.append({
                            'pid': pid,
                            'nombre': nombre_proceso,
                            'cmdline': '',
                            'estado': 'LISTENING',
                            'direccion': direccion
                        })
                    except Exception as e:
                        print(f"⚠️  Error obteniendo info del proceso {pid}: {e}")
        
        return conexiones
    except Exception as e:
        print(f"❌ Error usando netstat: {e}")
        return []

def main():
    """Función principal"""
    print_header("DIAGNÓSTICO DE PUERTO OCUPADO - PLAYERGOLD")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Verificando puerto: 18333")
    
    # Método 1: Usar psutil (más detallado)
    print_header("MÉTODO 1: USANDO PSUTIL")
    conexiones_psutil = encontrar_proceso_por_puerto(18333)
    
    if conexiones_psutil:
        print(f"✅ Encontrados {len(conexiones_psutil)} procesos usando puerto 18333:")
        for i, conn in enumerate(conexiones_psutil, 1):
            print(f"\n📋 Proceso {i}:")
            print(f"   PID: {conn['pid']}")
            print(f"   Nombre: {conn['nombre']}")
            print(f"   Dirección: {conn['direccion']}")
            print(f"   Estado: {conn['estado']}")
            if conn['cmdline']:
                print(f"   Comando: {conn['cmdline'][:100]}...")
    else:
        print("✅ No se encontraron procesos usando puerto 18333 (psutil)")
    
    # Método 2: Usar netstat (Windows)
    if sys.platform == "win32":
        print_header("MÉTODO 2: USANDO NETSTAT (WINDOWS)")
        conexiones_netstat = usar_netstat_windows(18333)
        
        if conexiones_netstat:
            print(f"✅ Encontrados {len(conexiones_netstat)} procesos usando puerto 18333:")
            for i, conn in enumerate(conexiones_netstat, 1):
                print(f"\n📋 Proceso {i}:")
                print(f"   PID: {conn['pid']}")
                print(f"   Nombre: {conn['nombre']}")
                print(f"   Dirección: {conn['direccion']}")
                print(f"   Estado: {conn['estado']}")
        else:
            print("✅ No se encontraron procesos usando puerto 18333 (netstat)")
    
    # Resumen y recomendaciones
    print_header("RESUMEN Y RECOMENDACIONES")
    
    todas_conexiones = conexiones_psutil + conexiones_netstat
    procesos_unicos = {}
    
    for conn in todas_conexiones:
        pid = conn['pid']
        if pid not in procesos_unicos:
            procesos_unicos[pid] = conn
    
    if procesos_unicos:
        print(f"⚠️  Puerto 18333 está ocupado por {len(procesos_unicos)} proceso(s):")
        
        for pid, conn in procesos_unicos.items():
            print(f"\n🔍 PID {pid} - {conn['nombre']}")
            
            # Determinar tipo de proceso y recomendación
            nombre = conn['nombre'].lower()
            if 'python' in nombre:
                print("   💡 Recomendación: Probablemente otro nodo PlayerGold")
                print("      - Terminar con: taskkill /PID {pid} /F")
                print("      - O cerrar la ventana del nodo anterior")
            elif 'java' in nombre:
                print("   💡 Recomendación: Aplicación Java (posible Minecraft server)")
                print("      - Verificar si es necesario antes de terminar")
            elif 'node' in nombre or 'npm' in nombre:
                print("   💡 Recomendación: Aplicación Node.js")
                print("      - Verificar si es un servidor de desarrollo")
            else:
                print("   💡 Recomendación: Proceso desconocido")
                print("      - Investigar antes de terminar")
            
            print(f"      - Comando para terminar: taskkill /PID {pid} /F")
        
        print("\n🔧 SOLUCIONES:")
        print("1. 🛑 Terminar procesos específicos:")
        for pid in procesos_unicos.keys():
            print(f"   taskkill /PID {pid} /F")
        
        print("\n2. 🔄 Usar script automático:")
        print("   scripts\\liberar_puerto_18333.bat")
        
        print("\n3. 🔀 Cambiar puerto (alternativa):")
        print("   - Editar config/testnet/node*.yaml")
        print("   - Cambiar listen_port: 18334")
        print("   - Actualizar bootstrap_nodes con nuevo puerto")
        
        print("\n4. 🔄 Reiniciar sistema (última opción)")
        
    else:
        print("🎉 ¡Puerto 18333 está libre!")
        print("\n✅ Puedes iniciar el nodo testnet:")
        print("   scripts\\start_node1_testnet.bat")
        
        print("\n🔍 Si aún obtienes error de puerto ocupado:")
        print("   - El proceso puede haberse iniciado después de este diagnóstico")
        print("   - Ejecuta este script nuevamente")
        print("   - O usa el script de liberación automática")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Diagnóstico cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        sys.exit(1)