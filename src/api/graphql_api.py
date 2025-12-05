"""
API GraphQL para integración con juegos
Proporciona una interfaz GraphQL flexible para consultas y mutaciones
"""

import graphene
from graphene import ObjectType, String, Float, Int, List, Field, Mutation, Schema
from flask import Flask, request
from flask_graphql import GraphQLView
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
from datetime import datetime, timedelta
from typing import Optional

from ..blockchain.transaction import Transaction as BlockchainTransaction
from ..blockchain.block import Block as BlockchainBlock


# Tipos GraphQL
class TransactionType(ObjectType):
    """Tipo GraphQL para transacciones"""
    from_address = String()
    to_address = String()
    amount = Float()
    fee = Float()
    timestamp = Float()
    signature = String()
    transaction_hash = String()
    
    def resolve_transaction_hash(self, info):
        return self.calculate_hash() if hasattr(self, 'calculate_hash') else None


class BlockType(ObjectType):
    """Tipo GraphQL para bloques"""
    index = Int()
    previous_hash = String()
    timestamp = Float()
    transactions = List(TransactionType)
    merkle_root = String()
    hash = String()
    ai_validators = List(String)


class BalanceType(ObjectType):
    """Tipo GraphQL para saldos"""
    address = String()
    balance = Float()
    timestamp = String()


class NetworkStatusType(ObjectType):
    """Tipo GraphQL para estado de red"""
    chain_length = Int()
    last_block_index = Int()
    last_block_hash = String()
    pending_transactions = Int()
    difficulty = Int()
    timestamp = String()


class TransactionHistoryType(ObjectType):
    """Tipo GraphQL para historial de transacciones"""
    address = String()
    transactions = List(TransactionType)
    total = Int()


# Mutaciones
class CreateTransaction(Mutation):
    """Mutación para crear transacciones"""
    
    class Arguments:
        from_address = String(required=True)
        to_address = String(required=True)
        amount = Float(required=True)
        fee = Float(default_value=0.01)
        private_key = String(required=True)
    
    transaction_hash = String()
    status = String()
    message = String()
    
    def mutate(self, info, from_address, to_address, amount, fee, private_key):
        try:
            blockchain = info.context.get('blockchain')
            
            # Crear transacción
            transaction = BlockchainTransaction(
                from_address=from_address,
                to_address=to_address,
                amount=amount,
                fee=fee
            )
            
            # Firmar transacción
            transaction.sign_transaction(private_key)
            
            # Validar y agregar
            if transaction.is_valid():
                blockchain.add_transaction(transaction)
                return CreateTransaction(
                    transaction_hash=transaction.calculate_hash(),
                    status='pending',
                    message='Transacción creada exitosamente'
                )
            else:
                return CreateTransaction(
                    transaction_hash=None,
                    status='error',
                    message='Transacción inválida'
                )
                
        except Exception as e:
            return CreateTransaction(
                transaction_hash=None,
                status='error',
                message=str(e)
            )


class Mutations(ObjectType):
    """Mutaciones disponibles"""
    create_transaction = CreateTransaction.Field()


# Queries
class Query(ObjectType):
    """Queries disponibles en la API GraphQL"""
    
    # Consultas de red
    network_status = Field(NetworkStatusType)
    
    # Consultas de saldos
    balance = Field(
        BalanceType,
        address=String(required=True)
    )
    
    # Consultas de transacciones
    transaction = Field(
        TransactionType,
        tx_hash=String(required=True)
    )
    
    transaction_history = Field(
        TransactionHistoryType,
        address=String(required=True),
        limit=Int(default_value=20)
    )
    
    # Consultas de bloques
    block = Field(
        BlockType,
        index=Int(required=True)
    )
    
    latest_blocks = List(
        BlockType,
        limit=Int(default_value=10)
    )
    
    def resolve_network_status(self, info):
        """Resuelve el estado de la red"""
        blockchain = info.context.get('blockchain')
        
        chain_length = len(blockchain.chain)
        last_block = blockchain.chain[-1] if chain_length > 0 else None
        
        return NetworkStatusType(
            chain_length=chain_length,
            last_block_index=last_block.index if last_block else 0,
            last_block_hash=last_block.hash if last_block else None,
            pending_transactions=len(blockchain.pending_transactions),
            difficulty=getattr(blockchain, 'difficulty', 1),
            timestamp=datetime.utcnow().isoformat()
        )
    
    def resolve_balance(self, info, address):
        """Resuelve el saldo de una dirección"""
        blockchain = info.context.get('blockchain')
        balance = blockchain.get_balance(address)
        
        return BalanceType(
            address=address,
            balance=float(balance),
            timestamp=datetime.utcnow().isoformat()
        )
    
    def resolve_transaction(self, info, tx_hash):
        """Resuelve una transacción por hash"""
        blockchain = info.context.get('blockchain')
        
        # Buscar en bloques confirmados
        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.calculate_hash() == tx_hash:
                    return tx
        
        # Buscar en transacciones pendientes
        for tx in blockchain.pending_transactions:
            if tx.calculate_hash() == tx_hash:
                return tx
        
        return None
    
    def resolve_transaction_history(self, info, address, limit):
        """Resuelve el historial de transacciones"""
        blockchain = info.context.get('blockchain')
        transactions = []
        
        # Buscar en todos los bloques
        for block in blockchain.chain:
            for tx in block.transactions:
                if tx.from_address == address or tx.to_address == address:
                    transactions.append(tx)
        
        # Limitar resultados
        transactions = transactions[-limit:]
        
        return TransactionHistoryType(
            address=address,
            transactions=transactions,
            total=len(transactions)
        )
    
    def resolve_block(self, info, index):
        """Resuelve un bloque por índice"""
        blockchain = info.context.get('blockchain')
        
        if 0 <= index < len(blockchain.chain):
            return blockchain.chain[index]
        
        return None
    
    def resolve_latest_blocks(self, info, limit):
        """Resuelve los últimos bloques"""
        blockchain = info.context.get('blockchain')
        
        return blockchain.chain[-limit:] if len(blockchain.chain) > 0 else []


class GraphQLGameAPI:
    """API GraphQL para integración con juegos"""
    
    def __init__(self, blockchain, secret_key: str = None):
        self.app = Flask(__name__)
        self.blockchain = blockchain
        self.secret_key = secret_key
        
        # Rate limiting
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["100 per minute", "1000 per hour"],
            storage_uri="memory://"
        )
        
        # Crear schema GraphQL
        self.schema = Schema(query=Query, mutation=Mutations)
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas GraphQL"""
        
        # Endpoint GraphQL con autenticación
        self.app.add_url_rule(
            '/graphql',
            view_func=self.limiter.limit("60 per minute")(
                GraphQLView.as_view(
                    'graphql',
                    schema=self.schema,
                    graphiql=True,  # Habilitar GraphiQL en desarrollo
                    get_context=self._get_context
                )
            )
        )
    
    def _get_context(self):
        """Obtiene el contexto para las queries GraphQL"""
        # Verificar autenticación
        token = request.headers.get('Authorization')
        
        context = {
            'blockchain': self.blockchain,
            'authenticated': False
        }
        
        if token and token.startswith('Bearer '):
            token = token[7:]
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                context['authenticated'] = True
                context['api_key'] = payload.get('api_key')
            except:
                pass
        
        return context
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Inicia el servidor GraphQL"""
        self.app.run(host=host, port=port, debug=debug)
