#!/usr/bin/env python3
"""
Test script to debug faucet issues
"""

import requests
import json

def test_faucet():
    url = "http://127.0.0.1:18080/api/v1/faucet"
    data = {
        "address": "PG691e12117e193b991d530707967a0a6d0ce879",
        "amount": 1000
    }
    
    print("Testing faucet endpoint...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Faucet request successful!")
            try:
                json_response = response.json()
                print(f"JSON Response: {json.dumps(json_response, indent=2)}")
            except:
                print("Could not parse JSON response")
        else:
            print(f"❌ Faucet request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error making request: {e}")

if __name__ == "__main__":
    test_faucet()