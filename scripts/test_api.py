#!/usr/bin/env python3
"""
Script para probar la API REST
"""

import requests
import sys

def test_api():
    """Probar la API REST"""
    try:
        response = requests.get('http://localhost:18080/api/v1/health', timeout=5)
        if response.status_code == 200:
            print('✅ API REST: Health check exitoso')
            print(f'   Respuesta: {response.json()}')
            return True
        else:
            print(f'❌ API REST: Health check falló (status: {response.status_code})')
            return False
    except Exception as e:
        print(f'❌ API REST: No accesible ({e})')
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)