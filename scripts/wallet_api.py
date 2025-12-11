#!/usr/bin/env python3
"""
API REST para wallets PlayerGold - Testnet
"""

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import time

app = Flask(__name__)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://"
)

# Mock blockchain data
blockchain_data = {
    'chain_length': 1,
    'difficulty': 1,
    'last_block_hash': '8ae3ac88603b190b85301eff394d0258909711fcc556473bf5f3608b96aca7cc',
    'last_block_index': 0,
    'pending_transactions': 0
}

# Mock balances
balances = {}

@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'network': 'testnet',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/v1/network/status', methods=['GET'])
@limiter.limit("60 per minute")
def network_status():
    return jsonify({
        'network': 'testnet',
        'chain_length': blockchain_data['chain_length'],
        'last_block_index': blockchain_data['last_block_index'],
        'last_block_hash': blockchain_data['last_block_hash'],
        'pending_transactions': blockchain_data['pending_transactions'],
        'difficulty': blockchain_data['difficulty'],
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/balance/<address>', methods=['GET'])
@limiter.limit("120 per minute")
def get_balance(address):
    # Return mock balance for testnet
    balance = balances.get(address, 1000.0)  # Default 1000 PRGLD for testnet
    
    return jsonify({
        'success': True,
        'address': address,
        'balance': balance,
        'network': 'testnet',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/transactions/history/<address>', methods=['GET'])
@limiter.limit("60 per minute")
def get_transaction_history(address):
    # Mock transaction history
    mock_transactions = [
        {
            'transaction': {
                'id': 'mock_tx_1',
                'from_address': 'PGfaucet000000000000000000000000000000000',
                'to_address': address,
                'amount': 1000.0,
                'fee': 0.0,
                'timestamp': time.time() - 86400  # 1 day ago
            },
            'block_index': 1,
            'timestamp': time.time() - 86400,
            'confirmations': 1
        }
    ]
    
    return jsonify({
        'success': True,
        'address': address,
        'transactions': mock_transactions,
        'total': len(mock_transactions),
        'page': 1,
        'per_page': 20
    })

@app.route('/api/v1/transaction', methods=['POST'])
@limiter.limit("60 per minute")
def create_transaction():
    data = request.get_json()
    
    if not data or not all(field in data for field in ['from_address', 'to_address', 'amount']):
        return jsonify({'error': 'Campos requeridos: from_address, to_address, amount'}), 400
    
    # Mock transaction creation
    tx_id = f"mock_tx_{int(time.time())}_{hash(str(data)) % 10000}"
    
    # Update mock balances
    from_addr = data['from_address']
    to_addr = data['to_address']
    amount = float(data['amount'])
    
    if from_addr in balances:
        balances[from_addr] -= amount
    if to_addr not in balances:
        balances[to_addr] = 0
    balances[to_addr] += amount
    
    return jsonify({
        'success': True,
        'transactionId': tx_id,
        'status': 'pending',
        'message': 'Transacción creada exitosamente'
    }), 201

@app.route('/api/v1/faucet', methods=['POST'])
@limiter.limit("10 per hour")
def faucet():
    data = request.get_json()
    
    if not data or 'address' not in data:
        return jsonify({'error': 'Dirección requerida'}), 400
    
    address = data['address']
    amount = float(data.get('amount', 1000))
    
    # Add to balance
    if address not in balances:
        balances[address] = 0
    balances[address] += amount
    
    tx_id = f"faucet_tx_{int(time.time())}_{hash(address) % 10000}"
    
    return jsonify({
        'success': True,
        'transactionId': tx_id,
        'amount': amount,
        'address': address,
        'message': f'Faucet: {amount} PRGLD enviados a {address}'
    }), 201

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 INICIANDO API WALLET PLAYERGOLD")
    print("=" * 60)
    print()
    print("✅ API Wallet lista!")
    print()
    print("🌐 Endpoints disponibles:")
    print("   • Health Check: http://localhost:18080/api/v1/health")
    print("   • Network Status: http://localhost:18080/api/v1/network/status")
    print("   • Balance: http://localhost:18080/api/v1/balance/<address>")
    print("   • Transaction History: http://localhost:18080/api/v1/transactions/history/<address>")
    print("   • Send Transaction: POST http://localhost:18080/api/v1/transaction")
    print("   • Faucet: POST http://localhost:18080/api/v1/faucet")
    print()
    print("💡 Las wallets pueden conectarse sin problemas")
    print("💡 Presiona Ctrl+C para detener la API")
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=18080, debug=False)