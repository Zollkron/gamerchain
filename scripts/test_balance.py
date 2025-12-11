#!/usr/bin/env python3
"""
Script para probar el endpoint de balance
"""

import requests
import sys

def test_balance():
    """Probar el endpoint de balance"""
    try:
        # Test address
        test_address = "PG1234567890123456789012345678901234567890"
        
        response = requests.get(f'http://127.0.0.1:18080/api/v1/balance/{test_address}', timeout=5)
        if response.status_code == 200:
            print('✅ Balance endpoint: Funcionando')
            print(f'   Respuesta: {response.json()}')
            return True
        else:
            print(f'❌ Balance endpoint: Error (status: {response.status_code})')
            print(f'   Respuesta: {response.text}')
            return False
    except Exception as e:
        print(f'❌ Balance endpoint: No accesible ({e})')
        return False

if __name__ == "__main__":
    success = test_balance()
    sys.exit(0 if success else 1)