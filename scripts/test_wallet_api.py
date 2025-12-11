#!/usr/bin/env python3
"""
Script de prueba para la API de wallets
"""

import requests
import json
import time

API_BASE = "http://127.0.0.1:18080/api/v1"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check: OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_balance():
    """Test balance endpoint"""
    print("\n🔍 Testing balance endpoint...")
    test_address = "PG1234567890123456789012345678901234567890"
    try:
        response = requests.get(f"{API_BASE}/balance/{test_address}", timeout=5)
        if response.status_code == 200:
            print("✅ Balance check: OK")
            data = response.json()
            print(f"   Address: {data['address']}")
            print(f"   Balance: {data['balance']} PRGLD")
        else:
            print(f"❌ Balance check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Balance check error: {e}")

def test_transaction_history():
    """Test transaction history endpoint"""
    print("\n🔍 Testing transaction history endpoint...")
    test_address = "PG1234567890123456789012345678901234567890"
    try:
        response = requests.get(f"{API_BASE}/transactions/history/{test_address}", timeout=5)
        if response.status_code == 200:
            print("✅ Transaction history: OK")
            data = response.json()
            print(f"   Address: {data['address']}")
            print(f"   Total transactions: {data['total']}")
            if data['transactions']:
                tx = data['transactions'][0]
                print(f"   First transaction:")
                print(f"     ID: {tx['id']}")
                print(f"     Amount: {tx['amount']} PRGLD")
                print(f"     From: {tx['from']}")
                print(f"     To: {tx['to']}")
                print(f"     Status: {tx['status']}")
        else:
            print(f"❌ Transaction history failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Transaction history error: {e}")

def test_create_transaction():
    """Test create transaction endpoint"""
    print("\n🔍 Testing create transaction endpoint...")
    
    transaction_data = {
        "from_address": "PG1234567890123456789012345678901234567890",
        "to_address": "PG9876543210987654321098765432109876543210",
        "amount": 100.0,
        "fee": 0.01,
        "memo": "Test transaction"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/transaction", 
            json=transaction_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ Create transaction: OK")
            data = response.json()
            print(f"   Transaction ID: {data['transactionId']}")
            print(f"   Status: {data['status']}")
            print(f"   Amount: {data['amount']} PRGLD")
            print(f"   Fee: {data['fee']} PRGLD")
        else:
            print(f"❌ Create transaction failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Create transaction error: {e}")

def test_faucet():
    """Test faucet endpoint"""
    print("\n🔍 Testing faucet endpoint...")
    
    faucet_data = {
        "address": "PG1111111111111111111111111111111111111111",
        "amount": 500
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/faucet", 
            json=faucet_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ Faucet request: OK")
            data = response.json()
            print(f"   Transaction ID: {data['transactionId']}")
            print(f"   Amount: {data['amount']} PRGLD")
            print(f"   Address: {data['address']}")
            print(f"   Message: {data['message']}")
        else:
            print(f"❌ Faucet request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Faucet request error: {e}")

def test_network_status():
    """Test network status endpoint"""
    print("\n🔍 Testing network status endpoint...")
    try:
        response = requests.get(f"{API_BASE}/network/status", timeout=5)
        if response.status_code == 200:
            print("✅ Network status: OK")
            data = response.json()
            print(f"   Network: {data['network']}")
            print(f"   Chain length: {data['chain_length']}")
            print(f"   Difficulty: {data['difficulty']}")
            print(f"   Pending transactions: {data['pending_transactions']}")
        else:
            print(f"❌ Network status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Network status error: {e}")

def main():
    print("=" * 60)
    print("🧪 TESTING WALLET API")
    print("=" * 60)
    
    # Run all tests
    test_health()
    test_network_status()
    test_balance()
    test_transaction_history()
    test_create_transaction()
    test_faucet()
    
    print("\n" + "=" * 60)
    print("✅ API testing completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()