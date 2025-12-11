#!/usr/bin/env python3
"""
Test script for Genesis Node API
"""

import requests
import json

def test_api():
    base_url = "http://127.0.0.1:18080"
    test_address = "PG691e12117e193b991d530707967a0a6d0ce879"
    
    print("🧪 Testing Genesis Node API...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        print(f"✅ Health: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health failed: {e}")
        return
    
    # Test balance endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/balance/{test_address}", timeout=5)
        print(f"✅ Balance: {response.status_code}")
        balance_data = response.json()
        print(f"   Balance: {balance_data['balance']} PRGLD")
    except Exception as e:
        print(f"❌ Balance failed: {e}")
    
    # Test transaction history
    try:
        response = requests.get(f"{base_url}/api/v1/transactions/history/{test_address}", timeout=5)
        print(f"✅ Transaction History: {response.status_code}")
        tx_data = response.json()
        print(f"   Transactions: {len(tx_data['transactions'])}")
        for i, tx in enumerate(tx_data['transactions']):
            print(f"   TX {i+1}: {tx['type']} - {tx['amount']} PRGLD - {tx['status']}")
    except Exception as e:
        print(f"❌ Transaction History failed: {e}")
    
    # Test mining stats
    try:
        response = requests.get(f"{base_url}/api/v1/mining/stats/{test_address}", timeout=5)
        print(f"✅ Mining Stats: {response.status_code}")
        stats_data = response.json()
        mining_stats = stats_data['mining_stats']
        print(f"   Blocks Validated: {mining_stats['blocks_validated']}")
        print(f"   Rewards Earned: {mining_stats['rewards_earned']} PRGLD")
        print(f"   Success Rate: {mining_stats['success_rate']}%")
    except Exception as e:
        print(f"❌ Mining Stats failed: {e}")
    
    # Test faucet request
    try:
        response = requests.post(f"{base_url}/api/v1/faucet", 
                               json={"address": test_address, "amount": 1000}, 
                               timeout=10)
        print(f"✅ Faucet Request: {response.status_code}")
        faucet_data = response.json()
        print(f"   Transaction ID: {faucet_data.get('transactionId', 'N/A')}")
        print(f"   Message: {faucet_data.get('message', 'N/A')}")
    except Exception as e:
        print(f"❌ Faucet Request failed: {e}")

if __name__ == "__main__":
    test_api()