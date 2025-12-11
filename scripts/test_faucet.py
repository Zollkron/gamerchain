#!/usr/bin/env python3
"""
Test script para verificar el faucet
"""

import requests
import json

def test_faucet():
    url = 'http://127.0.0.1:18080/api/v1/faucet'
    test_address = 'PG691e12117e193b991d530707967a0a6d0ce879'
    
    data = {
        'address': test_address,
        'amount': 1000
    }
    
    print(f"🚰 Testing faucet...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Faucet test PASSED")
        else:
            print("❌ Faucet test FAILED")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_balance():
    url = 'http://127.0.0.1:18080/api/v1/balance/PG691e12117e193b991d530707967a0a6d0ce879'
    
    print(f"\n💰 Testing balance...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_faucet()
    test_balance()