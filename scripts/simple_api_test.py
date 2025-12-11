#!/usr/bin/env python3
"""
API simple para probar
"""

from flask import Flask, jsonify, request
import time

app = Flask(__name__)

# Simple balance storage
balances = {}

@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'version': '1.0.0'})

@app.route('/api/v1/faucet', methods=['POST'])
def faucet():
    try:
        data = request.get_json()
        
        if not data or 'address' not in data:
            return jsonify({'error': 'Address required'}), 400
        
        address = data['address']
        amount = float(data.get('amount', 1000))
        
        # Add to balance
        if address not in balances:
            balances[address] = 0
        balances[address] += amount
        
        tx_id = f"faucet_{int(time.time())}"
        
        return jsonify({
            'success': True,
            'transactionId': tx_id,
            'amount': amount,
            'address': address,
            'message': f'Faucet: {amount} PRGLD sent to {address}'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/balance/<address>', methods=['GET'])
def get_balance(address):
    balance = balances.get(address, 1000.0)
    return jsonify({
        'success': True,
        'address': address,
        'balance': balance
    })

if __name__ == '__main__':
    print("Simple API Test - Port 18081")
    app.run(host='0.0.0.0', port=18081, debug=False)