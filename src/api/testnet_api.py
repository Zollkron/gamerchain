"""
API REST simplificada para testnet PlayerGold
Sin autenticación para facilitar el desarrollo
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import secrets

from ..blockchain.transaction import Transaction
from ..blockchain.block import Block


class TestnetAPI:
    """API REST simplificada para testnet"""
    
    def __init__(self, blockchain):
        self.app = Flask(__name__)
        self.blockchain = blockchain
        
        # Rate limiting básico
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["200 per minute"],
            storage_uri="memory://"
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API"""
        
        # Health check
        self.app.route('/api/v1/health', methods=['GET'])(self.health_check)
        
        # Network status
        self.app.route('/api/v1/network/status', methods=['GET'])(
            self.limiter.limit("60 per minute")(self.get_network_status)
        )
        
        # Balance
        self.app.route('/api/v1/balance/<address>', methods=['GET'])(
            self.limiter.limit("120 per minute")(self.get_balance)
        )
        
        # Transactions
        self.app.route('/api/v1/transaction', methods=['POST'])(
            self.limiter.limit("60 per minute")(self.create_transaction)
        )
        
        self.app.route('/api/v1/transaction/<tx_hash>', methods=['GET'])(
            self.limiter.limit("120 per minute")(self.get_transaction)
        )
        
        self.app.route('/api/v1/transactions/history/<address>', methods=['GET'])(
            self.limiter.limit("60 per minute")(self.get_transaction_history)
        )
        
        # Faucet
        self.app.route('/api/v1/faucet', methods=['POST'])(
            self.limiter.limit("10 per hour")(self.testnet_faucet)
        )
    
    def health_check(self):
        """Endpoint de health check"""
        return jsonify({
            'status': 'healthy',
            'network': 'testnet',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    def get_network_status(self):
        """Obtiene el estado actual de la red"""
        try:
            chain_length = len(self.blockchain.chain)
            last_block = self.blockchain.chain[-1] if chain_length > 0 else None
            
            return jsonify({
                'network': 'testnet',
                'chain_length': chain_length,
                'last_block_index': last_block.index if last_block else 0,
                'last_block_hash': last_block.hash if last_block else None,
                'pending_transactions': len(self.blockchain.pending_transactions),
                'difficulty': getattr(self.blockchain, 'difficulty', 1),
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_balance(self, address: str):
        """Obtiene el saldo de una dirección"""
        try:
            balance = self.blockchain.get_balance(address)
            
            return jsonify({
                'success': True,
                'address': address,
                'balance': float(balance),
                'network': 'testnet',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def create_transaction(self):
        """Crea una nueva transacción"""
        data = request.get_json()
        
        required_fields = ['from_address', 'to_address', 'amount']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Campos requeridos: from_address, to_address, amount'}), 400
        
        try:
            # Crear transacción
            transaction = Transaction(
                from_address=data['from_address'],
                to_address=data['to_address'],
                amount=float(data['amount']),
                fee=float(data.get('fee', 0.01))
            )
            
            # Para testnet, no requerimos firma
            # En producción esto sería obligatorio
            
            # Agregar a pending transactions
            self.blockchain.add_transaction(transaction)
            
            return jsonify({
                'success': True,
                'transactionId': transaction.calculate_hash(),
                'status': 'pending',
                'message': 'Transacción creada exitosamente'
            }), 201
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_transaction(self, tx_hash: str):
        """Obtiene información de una transacción"""
        try:
            # Buscar en bloques confirmados
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if tx.calculate_hash() == tx_hash:
                        return jsonify({
                            'success': True,
                            'transaction': tx.to_dict(),
                            'block_index': block.index,
                            'confirmations': len(self.blockchain.chain) - block.index,
                            'status': 'confirmed'
                        })
            
            # Buscar en transacciones pendientes
            for tx in self.blockchain.pending_transactions:
                if tx.calculate_hash() == tx_hash:
                    return jsonify({
                        'success': True,
                        'transaction': tx.to_dict(),
                        'status': 'pending'
                    })
            
            return jsonify({'error': 'Transacción no encontrada'}), 404
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_transaction_history(self, address: str):
        """Obtiene el historial de transacciones de una dirección"""
        try:
            transactions = []
            
            # Buscar en todos los bloques
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if tx.from_address == address or tx.to_address == address:
                        transactions.append({
                            'transaction': tx.to_dict(),
                            'block_index': block.index,
                            'timestamp': block.timestamp,
                            'confirmations': len(self.blockchain.chain) - block.index
                        })
            
            # Ordenar por timestamp descendente
            transactions.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Paginación
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            start = (page - 1) * per_page
            end = start + per_page
            
            return jsonify({
                'success': True,
                'address': address,
                'transactions': transactions[start:end],
                'total': len(transactions),
                'page': page,
                'per_page': per_page
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def testnet_faucet(self):
        """Faucet de testnet para obtener tokens de prueba"""
        data = request.get_json()
        
        if not data or 'address' not in data:
            return jsonify({'error': 'Dirección requerida'}), 400
        
        address = data['address']
        amount = float(data.get('amount', 1000))  # Default 1000 PRGLD
        
        try:
            # Crear transacción de faucet
            faucet_transaction = Transaction(
                from_address=None,  # Faucet address
                to_address=address,
                amount=amount,
                fee=0.0
            )
            
            # Agregar a transacciones pendientes
            self.blockchain.add_transaction(faucet_transaction)
            
            # Simular minado inmediato para testnet
            block = self.blockchain.mine_pending_transactions('faucet_miner')
            
            return jsonify({
                'success': True,
                'transactionId': faucet_transaction.calculate_hash(),
                'amount': amount,
                'address': address,
                'block_index': block.index,
                'message': f'Faucet: {amount} PRGLD enviados a {address}'
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=18080, debug=False):
        """Inicia el servidor API"""
        self.app.run(host=host, port=port, debug=debug)