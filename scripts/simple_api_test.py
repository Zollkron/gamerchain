#!/usr/bin/env python3
"""
API simple para testing
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Simple API working'})

@app.route('/api/v1/balance/<address>', methods=['GET'])
def balance(address):
    return jsonify({
        'success': True,
        'address': address,
        'balance': 1000.0,
        'network': 'testnet'
    })

if __name__ == '__main__':
    print("🚀 Iniciando API simple en puerto 18080...")
    app.run(host='0.0.0.0', port=18080, debug=False)