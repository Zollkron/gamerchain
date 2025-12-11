import requests
import time

print("🧪 Testing new genesis node with mining rewards...")

address = "PG691e12117e193b991d530707967a0a6d0ce879"

# 1. Request faucet tokens
print(f"🚰 Requesting faucet tokens for {address}")
response = requests.post("http://127.0.0.1:18080/api/v1/faucet", 
                       json={"address": address, "amount": 1000})
print(f"Faucet Status: {response.status_code}")
print(f"Faucet Response: {response.json()}")

# 2. Wait for mining to complete
print("\n⏳ Waiting for mining to complete...")
time.sleep(5)

# 3. Check balance
print(f"\n💰 Checking balance for {address}")
balance_response = requests.get(f"http://127.0.0.1:18080/api/v1/balance/{address}")
print(f"Balance Status: {balance_response.status_code}")
print(f"Balance: {balance_response.json()['balance']} PRGLD")

# 4. Check transaction history
print(f"\n📋 Checking transaction history for {address}")
history_response = requests.get(f"http://127.0.0.1:18080/api/v1/transactions/history/{address}")
print(f"History Status: {history_response.status_code}")
transactions = history_response.json()['transactions']
print(f"Total transactions: {len(transactions)}")

for i, tx in enumerate(transactions):
    print(f"  {i+1}. {tx['type']}: {tx['amount']} PRGLD from {tx['from'][:10]}... ({tx['status']})")

print("\n✅ Test completed!")