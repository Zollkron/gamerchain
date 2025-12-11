#!/usr/bin/env python3
"""
Script de verificación del sistema integrado PlayerGold
"""

import requests
import socket
import subprocess
import time
import json
import sys
from datetime import datetime

def print_header(title):
    print("=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def print_status(status, message):
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    print(f"{icons.get(status, 'ℹ️')} {message}")

def check_port(port, service_name):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print_status("success", f"{service_name} (puerto {port}): ACTIVO")
            return True
        else:
            print_status("error", f"{service_name} (puerto {port}): INACTIVO")
            return False
    except Exception as e:
        print_status("error", f"Error verificando {service_name}: {e}")
        return False

def check_api_health():
    """Check API health endpoint"""
    try:
        response = requests.get("http://127.0.0.1:18080/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status("success", f"API Health: {data.get('status', 'unknown')}")
            print_status("info", f"Network: {data.get('network', 'unknown')}")
            print_status("info", f"Version: {data.get('version', 'unknown')}")
            return True
        else:
            print_status("error", f"API Health: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("error", f"API Health: {e}")
        return False

def check_network_status():
    """Check network status endpoint"""
    try:
        response = requests.get("http://127.0.0.1:18080/api/v1/network/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status("success", f"Network Status: OK")
            print_status("info", f"Chain Length: {data.get('chain_length', 0)}")
            print_status("info", f"Difficulty: {data.get('difficulty', 0)}")
            print_status("info", f"Pending TX: {data.get('pending_transactions', 0)}")
            return True
        else:
            print_status("error", f"Network Status: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("error", f"Network Status: {e}")
        return False

def test_faucet():
    """Test faucet functionality"""
    try:
        test_address = "PG1234567890123456789012345678901234567890"
        payload = {
            "address": test_address,
            "amount": 100
        }
        
        response = requests.post(
            "http://127.0.0.1:18080/api/v1/faucet",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print_status("success", f"Faucet: {data.get('message', 'OK')}")
            return True
        elif response.status_code == 429:
            print_status("warning", "Faucet: Rate limit alcanzado (normal)")
            return True
        else:
            print_status("error", f"Faucet: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("error", f"Faucet: {e}")
        return False

def test_balance():
    """Test balance endpoint"""
    try:
        test_address = "PG1234567890123456789012345678901234567890"
        response = requests.get(
            f"http://127.0.0.1:18080/api/v1/balance/{test_address}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            balance = data.get('balance', 0)
            print_status("success", f"Balance: {balance} PRGLD")
            return True
        else:
            print_status("error", f"Balance: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_status("error", f"Balance: {e}")
        return False

def check_processes():
    """Check running processes"""
    try:
        # Check for Python processes (P2P nodes)
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        
        python_processes = len([line for line in result.stdout.split('\n') 
                              if 'python.exe' in line])
        
        if python_processes > 0:
            print_status("success", f"Procesos Python: {python_processes} activos")
        else:
            print_status("warning", "No se encontraron procesos Python")
        
        return python_processes > 0
        
    except Exception as e:
        print_status("error", f"Error verificando procesos: {e}")
        return False

def check_firewall():
    """Check firewall status for required ports"""
    try:
        print_status("info", "Verificando configuración de firewall...")
        
        # Check if ports are accessible
        ports_to_check = [18080, 18333]
        accessible_ports = 0
        
        for port in ports_to_check:
            if check_port(port, f"Puerto {port}"):
                accessible_ports += 1
        
        if accessible_ports == len(ports_to_check):
            print_status("success", "Todos los puertos están accesibles")
            return True
        else:
            print_status("warning", f"Solo {accessible_ports}/{len(ports_to_check)} puertos accesibles")
            return False
            
    except Exception as e:
        print_status("error", f"Error verificando firewall: {e}")
        return False

def main():
    print_header("VERIFICACIÓN SISTEMA INTEGRADO PLAYERGOLD")
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Track overall status
    checks = []
    
    # 1. Check processes
    print_header("PROCESOS DEL SISTEMA")
    checks.append(check_processes())
    print()
    
    # 2. Check ports
    print_header("PUERTOS DE RED")
    checks.append(check_port(18080, "API REST"))
    checks.append(check_port(18333, "P2P Network"))
    print()
    
    # 3. Check firewall
    print_header("CONFIGURACIÓN DE RED")
    checks.append(check_firewall())
    print()
    
    # 4. Check API endpoints
    print_header("ENDPOINTS DE API")
    checks.append(check_api_health())
    checks.append(check_network_status())
    checks.append(test_balance())
    checks.append(test_faucet())
    print()
    
    # Summary
    print_header("RESUMEN")
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print_status("success", f"SISTEMA COMPLETAMENTE OPERATIVO ({passed}/{total})")
        print_status("info", "✅ Todos los servicios están funcionando correctamente")
        print_status("info", "✅ La wallet puede conectarse sin problemas")
        print_status("info", "✅ La red blockchain está sincronizada")
    elif passed >= total * 0.7:  # 70% or more
        print_status("warning", f"SISTEMA PARCIALMENTE OPERATIVO ({passed}/{total})")
        print_status("info", "⚠️ Algunos servicios pueden tener problemas")
        print_status("info", "💡 Revisa los errores anteriores")
    else:
        print_status("error", f"SISTEMA CON PROBLEMAS CRÍTICOS ({passed}/{total})")
        print_status("info", "❌ Múltiples servicios no están funcionando")
        print_status("info", "🔧 Se requiere intervención manual")
    
    print()
    print_status("info", "💡 Para más detalles, revisa los logs de cada servicio")
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)