import requests

print("Making direct faucet request...")
try:
    response = requests.post("http://127.0.0.1:18080/api/v1/faucet", 
                           json={"address": "PGtest123456789abcdef123456789abcdef123", "amount": 500})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request error: {e}")