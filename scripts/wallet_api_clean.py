#!/usr/bin/env python3
"""
API REST para wallets PlayerGold - Testnet (Versión Limpia)
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

# Mock balances - cada dirección empieza con 1000 PRGLD
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
    # Return balance for testnet (default 1000 PRGLD for new addresses)
    balance = balances.get(address, 1000.0)
    
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
    # Mock transaction history - solo si la dirección ha usado el faucet
    current_time = time.time()
    mock_transactions = []
    
    # Si la dirección tiene balance, mostrar transacción de faucet inicial
    if address in balances:
        mock_transactions.append({
            'id': f'faucet_tx_initial_{address[-8:]}',
            'type': 'faucet_transfer',
            'from': 'PGfaucet000000000000000000000000000000000',
            'to': address,
            'amount': '1000.0',
            'fee': '0.0',
            'timestamp': datetime.fromtimestamp(current_time - 86400).isoformat(),
            'status': 'confirmed',
            'memo': 'Testnet faucet - Initial 1000 PRGLD',
            'blockNumber': 1,
            'confirmations': 1
        })
    
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
    
    # Validar campos requeridos
    if not data or not all(field in data for field in ['from_address', 'to_address', 'amount']):
        return jsonify({'error': 'Campos requeridos: from_address, to_address, amount'}), 400
    
    try:
        # Validar amount
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        from_addr = data['from_address']
        to_addr = data['to_address']
        fee = float(data.get('fee', 0.01))
        
        # Verificar balance del remitente
        sender_balance = balances.get(from_addr, 1000.0)  # Default testnet balance
        if sender_balance < (amount + fee):
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Crear ID de transacción
        tx_id = f"tx_{int(time.time())}_{hash(str(data)) % 10000}"
        
        # Actualizar balances
        balances[from_addr] = sender_balance - amount - fee
        if to_addr not in balances:
            balances[to_addr] = 0
        balances[to_addr] += amount
        
        return jsonify({
            'success': True,
            'transactionId': tx_id,
            'hash': tx_id,
            'status': 'confirmed',
            'message': 'Transacción creada exitosamente',
            'amount': amount,
            'fee': fee,
            'from_address': from_addr,
            'to_address': to_addr,
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/faucet', methods=['POST'])
@limiter.limit("10 per hour")
def faucet():
    data = request.get_json()
    
    if not data or 'address' not in data:
        return jsonify({'error': 'Dirección requerida'}), 400
    
    address = data['address']
    amount = float(data.get('amount', 1000))
    
    # Agregar al balance
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
    print("🌐 INICIANDO API WALLET PLAYERGOLD (LIMPIA)")
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