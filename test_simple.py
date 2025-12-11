import requests
import json

try:
    print("Testing faucet...")
    response = requests.post("http://127.0.0.1:18080/api/v1/faucet", 
                           json={"address": "PG691e12117e193b991d530707967a0a6d0ce879", "amount": 1000},
                           timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")