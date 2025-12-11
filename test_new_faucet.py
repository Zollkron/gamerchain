import requests
import json

try:
    print("Testing faucet with new address...")
    new_address = "PG123456789abcdef123456789abcdef12345678"
    response = requests.post("http://127.0.0.1:18080/api/v1/faucet", 
                           json={"address": new_address, "amount": 1000},
                           timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Now check transaction history
    print("\nChecking transaction history...")
    history_response = requests.get(f"http://127.0.0.1:18080/api/v1/transactions/history/{new_address}")
    print(f"History Status: {history_response.status_code}")
    print(f"History Response: {history_response.text}")
    
except Exception as e:
    print(f"Error: {e}")