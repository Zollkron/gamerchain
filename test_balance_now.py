#!/usr/bin/env python3
import requests

try:
    # Test current balance
    response = requests.get("http://127.0.0.1:18080/api/v1/balance/PG691e12117e193b991d530707967a0a6d0ce879", timeout=5)
    balance_data = response.json()
    print(f"💰 Current Balance: {balance_data['balance']} PRGLD")
    
    # Test transaction history
    response = requests.get("http://127.0.0.1:18080/api/v1/transactions/history/PG691e12117e193b991d530707967a0a6d0ce879", timeout=5)
    tx_data = response.json()
    print(f"📋 Transaction Count: {len(tx_data['transactions'])}")
    
    for i, tx in enumerate(tx_data['transactions']):
        print(f"   TX {i+1}: {tx['type']} - {tx['amount']} PRGLD - {tx['status']}")
    
    # Test mining stats
    response = requests.get("http://127.0.0.1:18080/api/v1/mining/stats/PG691e12117e193b991d530707967a0a6d0ce879", timeout=5)
    stats_data = response.json()
    mining_stats = stats_data['mining_stats']
    print(f"⛏️  Blocks Validated: {mining_stats['blocks_validated']}")
    print(f"🏆 Rewards Earned: {mining_stats['rewards_earned']} PRGLD")
    
except Exception as e:
    print(f"❌ Error: {e}")