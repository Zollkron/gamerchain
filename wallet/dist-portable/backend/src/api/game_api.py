"""
API REST para integración con juegos
Proporciona endpoints para transacciones, consulta de saldos y estado de red
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import jwt
import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import secrets

from ..blockchain.transaction import Transaction
from ..blockchain.block import Block


class GameAPI:
    """API REST para integración con juegos"""
    
    def __init__(self, blockchain, secret_key: str = None):
        self.app = Flask(__name__)
        self.blockchain = blockchain
        self.secret_key = secret_key or secrets.token_hex(32)
        self.app.config['SECRET_KEY'] = self.secret_key
        
        # Rate limiting para protección contra DDoS
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["100 per minute", "1000 per hour"],
            storage_uri="memory://"
        )
        
        # Almacenamiento de API keys (en producción usar base de datos)
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API"""
        
        # Endpoints públicos
        self.app.route('/api/v1/health', methods=['GET'])(self.health_check)
        self.app.route('/api/v1/network/status', methods=['GET'])(
            self.limiter.limit("30 per minute")(self.get_network_status)
        )
        
        # Endpoints de autenticación
        self.app.route('/api/v1/auth/register', methods=['POST'])(
            self.limiter.limit("5 per hour")(self.register_developer)
        )
        self.app.route('/api/v1/auth/token', methods=['POST'])(
            self.limiter.limit("10 per minute")(self.get_auth_token)
        )
        
        # Endpoints protegidos (públicos en testnet)
        self.app.route('/api/v1/balance/<address>', methods=['GET'])(
            self.limiter.limit("60 per minute")(self.get_balance)
        )
        self.app.route('/api/v1/transaction', methods=['POST'])(
            self.limiter.limit("30 per minute")(self.create_transaction)
        )
        self.app.route('/api/v1/transaction/<tx_hash>', methods=['GET'])(
            self.limiter.limit("60 per minute")(self.get_transaction)
        )
        self.app.route('/api/v1/transactions/history/<address>', methods=['GET'])(
            self.limiter.limit("30 per minute")(self.get_transaction_history)
        )
        self.app.route('/api/v1/block/<int:block_index>', methods=['GET'])(
            self.limiter.limit("60 per minute")(self.require_auth(self.get_block))
        )
        self.app.route('/api/v1/faucet', methods=['POST'])(
            self.limiter.limit("10 per hour")(self.testnet_faucet)
        )
    
    def require_auth(self, f):
        """Decorador para requerir autenticación"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            
            if not token:
                return jsonify({'error': 'Token de autenticación requerido'}), 401
            
            if token.startswith('Bearer '):
                token = token[7:]
            
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                api_key = payload.get('api_key')
                
                if api_key not in self.api_keys:
                    return jsonify({'error': 'API key inválida'}), 401
                
                # Verificar que la API key no esté revocada
                if self.api_keys[api_key].get('revoked', False):
                    return jsonify({'error': 'API key revocada'}), 401
                
                request.api_key = api_key
                request.developer_info = self.api_keys[api_key]
                
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expirado'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Token inválido'}), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def health_check(self):
        """Endpoint de health check"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    def register_developer(self):
        """Registra un nuevo desarrollador y genera API key"""
        data = request.get_json()
        
        if not data or 'email' not in data or 'game_name' not in data:
            return jsonify({'error': 'Email y nombre del juego requeridos'}), 400
        
        # Generar API key única
        api_key = secrets.token_urlsafe(32)
        
        # Almacenar información del desarrollador
        self.api_keys[api_key] = {
            'email': data['email'],
            'game_name': data['game_name'],
            'created_at': datetime.utcnow().isoformat(),
            'revoked': False,
            'rate_limit_tier': data.get('tier', 'standard')
        }
        
        return jsonify({
            'api_key': api_key,
            'message': 'Desarrollador registrado exitosamente'
        }), 201
    
    def get_auth_token(self):
        """Genera un JWT token para autenticación"""
        data = request.get_json()
        
        if not data or 'api_key' not in data:
            return jsonify({'error': 'API key requerida'}), 400
        
        api_key = data['api_key']
        
        if api_key not in self.api_keys:
            return jsonify({'error': 'API key inválida'}), 401
        
        if self.api_keys[api_key].get('revoked', False):
            return jsonify({'error': 'API key revocada'}), 401
        
        # Generar JWT token con expiración de 24 horas
        payload = {
            'api_key': api_key,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        return jsonify({
            'token': token,
            'expires_in': 86400  # 24 horas en segundos
        })
    
    def get_network_status(self):
        """Obtiene el estado actual de la red"""
        try:
            chain_length = len(self.blockchain.chain)
            last_block = self.blockchain.chain[-1] if chain_length > 0 else None
            
            return jsonify({
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
                'address': address,
                'balance': float(balance),
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def create_transaction(self):
        """Crea una nueva transacción"""
        data = request.get_json()
        
        required_fields = ['from_address', 'to_address', 'amount', 'private_key']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Campos requeridos: from_address, to_address, amount, private_key'}), 400
        
        try:
            # Crear transacción
            transaction = Transaction(
                from_address=data['from_address'],
                to_address=data['to_address'],
                amount=float(data['amount']),
                fee=float(data.get('fee', 0.01))
            )
            
            # Firmar transacción
            transaction.sign_transaction(data['private_key'])
            
            # Validar y agregar a pending transactions
            if transaction.is_valid():
                self.blockchain.add_transaction(transaction)
                
                return jsonify({
                    'transaction_hash': transaction.calculate_hash(),
                    'status': 'pending',
                    'message': 'Transacción creada exitosamente'
                }), 201
            else:
                return jsonify({'error': 'Transacción inválida'}), 400
                
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
                            'transaction': tx.to_dict(),
                            'block_index': block.index,
                            'confirmations': len(self.blockchain.chain) - block.index,
                            'status': 'confirmed'
                        })
            
            # Buscar en transacciones pendientes
            for tx in self.blockchain.pending_transactions:
                if tx.calculate_hash() == tx_hash:
                    return jsonify({
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
                'address': address,
                'transactions': transactions[start:end],
                'total': len(transactions),
                'page': page,
                'per_page': per_page
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_block(self, block_index: int):
        """Obtiene información de un bloque"""
        try:
            if block_index < 0 or block_index >= len(self.blockchain.chain):
                return jsonify({'error': 'Índice de bloque inválido'}), 404
            
            block = self.blockchain.chain[block_index]
            
            return jsonify({
                'block': block.to_dict(),
                'confirmations': len(self.blockchain.chain) - block_index
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
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Inicia el servidor API"""
        self.app.run(host=host, port=port, debug=debug)
