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

# ===== FEE DISTRIBUTION ENDPOINTS =====

@app.route('/api/v1/fee-distribution/current', methods=['GET'])
def get_current_fee_distribution():
    """Get current fee distribution percentages"""
    # Mock data - in real implementation, this would come from HalvingFeeManager
    return jsonify({
        'success': True,
        'distribution': {
            'burn': '0.60',
            'developer': '0.30',
            'liquidity': '0.10'
        },
        'halving_number': 0,
        'last_update': None,
        'redistribution_complete': False,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/fee-distribution/history', methods=['GET'])
def get_fee_distribution_history():
    """Get fee distribution history"""
    # Mock data - in real implementation, this would come from HalvingFeeManager
    return jsonify({
        'success': True,
        'history': [],
        'total_redistributions': 0,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/fee-distribution/next-halving', methods=['GET'])
def get_next_halving_info():
    """Get information about the next halving event"""
    current_block = request.args.get('current_block', 0, type=int)
    
    # Mock calculation
    halving_interval = 100000
    next_halving_block = ((current_block // halving_interval) + 1) * halving_interval
    blocks_remaining = next_halving_block - current_block
    
    return jsonify({
        'success': True,
        'current_block': current_block,
        'next_halving_block': next_halving_block,
        'blocks_remaining': blocks_remaining,
        'current_distribution': {
            'burn': '0.60',
            'developer': '0.30',
            'liquidity': '0.10'
        },
        'next_distribution': {
            'burn': '0.50',
            'developer': '0.35',
            'liquidity': '0.15'
        },
        'redistribution_complete': False,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/fee-distribution/timeline', methods=['GET'])
def get_halving_timeline():
    """Get complete timeline of halvings and redistributions"""
    return jsonify({
        'success': True,
        'timeline': [],
        'total_events': 0,
        'projected_events': 6,
        'timestamp': datetime.utcnow().isoformat()
    })

# ===== VOLUNTARY BURN ENDPOINTS =====

@app.route('/api/v1/voluntary-burn/statistics', methods=['GET'])
def get_voluntary_burn_statistics():
    """Get voluntary burn statistics"""
    return jsonify({
        'success': True,
        'overview': {
            'total_voluntary_burned': '0.0',
            'total_users': 0,
            'total_burn_transactions': 0,
            'average_reputation': '0.0',
            'total_reputation_points': '0.0'
        },
        'configuration': {
            'reputation_per_token': '1.0',
            'max_priority_multiplier': '10.0',
            'reputation_decay_rate': '0.01'
        },
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/voluntary-burn/leaderboard', methods=['GET'])
def get_voluntary_burn_leaderboard():
    """Get voluntary burn leaderboard"""
    leaderboard_type = request.args.get('type', 'total_burned')  # 'total_burned' or 'reputation'
    limit = request.args.get('limit', 10, type=int)
    
    return jsonify({
        'success': True,
        'leaderboard_type': leaderboard_type,
        'limit': limit,
        'users': [],
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/voluntary-burn/user/<address>', methods=['GET'])
def get_user_burn_reputation(address):
    """Get user's burn reputation and analytics"""
    return jsonify({
        'success': True,
        'user_address': address,
        'reputation_data': {
            'total_burned': '0.0',
            'reputation_score': '0.0',
            'burn_count': 0,
            'priority_multiplier': '1.0',
            'last_burn_timestamp': None
        },
        'burn_statistics': {
            'total_burns': 0,
            'average_burn_amount': '0.0',
            'burn_frequency_per_day': 0,
            'first_burn': None,
            'last_burn': None
        },
        'ranking': {
            'by_total_burned': -1,
            'by_reputation': -1
        },
        'burn_history': [],
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/voluntary-burn/history', methods=['GET'])
def get_voluntary_burn_history():
    """Get voluntary burn history"""
    user_address = request.args.get('user_address')
    limit = request.args.get('limit', 100, type=int)
    
    return jsonify({
        'success': True,
        'user_address': user_address,
        'limit': limit,
        'burns': [],
        'total_burns': 0,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/voluntary-burn/create', methods=['POST'])
def create_voluntary_burn():
    """Create a voluntary burn transaction"""
    data = request.get_json()
    
    if not data or 'from_address' not in data or 'amount' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: from_address, amount'
        }), 400
    
    from_address = data['from_address']
    amount = float(data['amount'])
    memo = data.get('memo', f'Voluntary burn of {amount} PRGLD')
    
    if amount <= 0:
        return jsonify({
            'success': False,
            'error': 'Amount must be positive'
        }), 400
    
    # Mock transaction creation
    transaction_id = f"voluntary_burn_{int(time.time())}_{hash(from_address) % 10000}"
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'from_address': from_address,
        'amount': amount,
        'memo': memo,
        'reputation_gained': amount * 1.0,  # 1 reputation per token
        'estimated_priority_increase': '1.5x',
        'timestamp': datetime.utcnow().isoformat()
    })

# ===== MONITORING ENDPOINTS =====

@app.route('/api/v1/monitoring/fee-distribution', methods=['GET'])
def get_fee_distribution_monitoring():
    """Get comprehensive fee distribution monitoring data"""
    return jsonify({
        'success': True,
        'current_state': {
            'distribution': {
                'burn': '0.60',
                'developer': '0.30',
                'liquidity': '0.10'
            },
            'total_redistributions': 0,
            'burn_exhausted': False,
            'last_update': None
        },
        'statistics': {
            'total_burn_reduction': '0.0',
            'total_developer_increase': '0.0',
            'total_liquidity_increase': '0.0',
            'redistribution_efficiency': '0.0'
        },
        'recent_events': [],
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/monitoring/voluntary-burn', methods=['GET'])
def get_voluntary_burn_monitoring():
    """Get comprehensive voluntary burn monitoring data"""
    return jsonify({
        'success': True,
        'overview': {
            'total_voluntary_burned': '0.0',
            'total_users': 0,
            'total_burn_transactions': 0,
            'average_reputation': '0.0'
        },
        'leaderboards': {
            'top_burners': [],
            'top_reputation': []
        },
        'recent_activity': [],
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