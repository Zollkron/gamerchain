#!/usr/bin/env python3
"""
API REST para wallets PlayerGold - Testnet (FINAL)
"""

import sys
import os

# Limpiar PYTHONPATH para evitar imports automáticos
paths_to_remove = ['', '.', os.getcwd()]
for p in paths_to_remove:
    while p in sys.path:
        sys.path.remove(p)

# Limpiar cualquier módulo ya importado que pueda causar conflictos
modules_to_remove = []
for module_name in sys.modules.keys():
    if module_name.startswith('src.') or module_name == 'src':
        modules_to_remove.append(module_name)

for module_name in modules_to_remove:
    del sys.modules[module_name]

from flask import Flask, jsonify, request
from datetime import datetime
import time

app = Flask(__name__)

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

@app.route('/api/v1/balance/<address>', methods=['GET'])
def get_balance(address):
    balance = balances.get(address, 1000.0)
    return jsonify({
        'success': True,
        'address': address,
        'balance': balance,
        'network': 'testnet',
        'timestamp': datetime.utcnow().isoformat()
    })

# Transaction history storage
transaction_history = {}

@app.route('/api/v1/transactions/history/<address>', methods=['GET'])
def get_transaction_history(address):
    current_time = time.time()
    transactions = transaction_history.get(address, [])
    
    # Add initial transaction if address has balance but no transactions
    if address in balances and len(transactions) == 0:
        initial_tx = {
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
        }
        transactions.append(initial_tx)
        transaction_history[address] = transactions
    
    return jsonify({
        'success': True,
        'address': address,
        'transactions': transactions,
        'total': len(transactions),
        'page': 1,
        'per_page': 20
    })

@app.route('/api/v1/transaction', methods=['POST'])
def create_transaction():
    try:
        data = request.get_json()
        
        if not data or not all(field in data for field in ['from_address', 'to_address', 'amount']):
            return jsonify({'error': 'Campos requeridos: from_address, to_address, amount'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        from_addr = data['from_address']
        to_addr = data['to_address']
        fee = float(data.get('fee', 0.01))
        
        sender_balance = balances.get(from_addr, 1000.0)
        if sender_balance < (amount + fee):
            return jsonify({'error': 'Insufficient balance'}), 400
        
        tx_id = f"tx_{int(time.time())}_{hash(str(data)) % 10000}"
        
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
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/faucet', methods=['POST'])
def faucet():
    try:
        print(f"FAUCET: Request received")
        data = request.get_json()
        print(f"FAUCET: Request data: {data}")
        
        if not data or 'address' not in data:
            print(f"ERROR: Missing address in request")
            return jsonify({'error': 'Dirección requerida'}), 400
        
        address = data['address']
        amount = float(data.get('amount', 1000))
        print(f"FAUCET: Processing {amount} PRGLD to {address}")
        
        if address not in balances:
            balances[address] = 0
        balances[address] += amount
        
        tx_id = f"faucet_tx_{int(time.time())}_{hash(address) % 10000}"
        
        # Register transaction in history
        if address not in transaction_history:
            transaction_history[address] = []
        
        faucet_transaction = {
            'id': tx_id,
            'type': 'faucet_transfer',
            'from': 'PGfaucet000000000000000000000000000000000',
            'to': address,
            'amount': str(amount),
            'fee': '0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'confirmed',
            'memo': f'Testnet faucet - {amount} PRGLD',
            'blockNumber': len(transaction_history[address]) + 1,
            'confirmations': 1
        }
        
        transaction_history[address].append(faucet_transaction)
        
        print(f"SUCCESS: Faucet successful: {tx_id}")
        print(f"BALANCE: New balance for {address}: {balances[address]} PRGLD")
        print(f"TRANSACTION: Added to history: {tx_id}")
        
        return jsonify({
            'success': True,
            'transactionId': tx_id,
            'amount': amount,
            'address': address,
            'message': f'Faucet: {amount} PRGLD enviados a {address}'
        }), 200
        
    except Exception as e:
        print(f"ERROR: Faucet error: {str(e)}")
        import traceback
        print("TRACEBACK:")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/network/status', methods=['GET'])
def network_status():
    return jsonify({
        'network': 'testnet',
        'chain_length': 1,
        'last_block_index': 0,
        'last_block_hash': '8ae3ac88603b190b85301eff394d0258909711fcc556473bf5f3608b96aca7cc',
        'pending_transactions': 0,
        'difficulty': 1,
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("API WALLET PLAYERGOLD - FUNCIONANDO")
    print("=" * 60)
    print("✅ Todos los endpoints operativos")
    print("💡 Puerto 18080 - Las wallets pueden conectarse")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=18080, debug=False)