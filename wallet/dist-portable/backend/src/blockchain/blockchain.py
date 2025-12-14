"""
Blockchain principal para PlayerGold
"""

from typing import List, Dict, Optional
from .block import Block, create_genesis_block
from .transaction import Transaction
import time


class Blockchain:
    """Blockchain principal de PlayerGold"""
    
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.difficulty = 1
        self.mining_reward = 10.0
        self.balances: Dict[str, float] = {}
        
        # Crear bloque genesis
        genesis_block = create_genesis_block()
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        """Obtiene el último bloque de la cadena"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction):
        """Agrega una transacción a las pendientes"""
        if transaction.is_valid():
            self.pending_transactions.append(transaction)
        else:
            raise ValueError("Transacción inválida")
    
    def get_balance(self, address: str) -> float:
        """Obtiene el balance de una dirección"""
        balance = 0.0
        
        # Recorrer todos los bloques
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.from_address == address:
                    balance -= transaction.amount + transaction.fee
                if transaction.to_address == address:
                    balance += transaction.amount
        
        # Incluir transacciones pendientes
        for transaction in self.pending_transactions:
            if transaction.from_address == address:
                balance -= transaction.amount + transaction.fee
            if transaction.to_address == address:
                balance += transaction.amount
        
        return balance
    
    def mine_pending_transactions(self, mining_reward_address: str) -> Block:
        """Mina las transacciones pendientes"""
        # Crear transacción de recompensa
        reward_transaction = Transaction(
            from_address=None,  # Recompensa de minería
            to_address=mining_reward_address,
            amount=self.mining_reward,
            fee=0.0
        )
        
        self.pending_transactions.append(reward_transaction)
        
        # Crear nuevo bloque
        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash
        )
        
        # Minar el bloque (simplificado)
        block.mine_block(self.difficulty)
        
        # Agregar a la cadena
        self.chain.append(block)
        
        # Limpiar transacciones pendientes
        self.pending_transactions = []
        
        return block
    
    def is_chain_valid(self) -> bool:
        """Valida la integridad de la cadena"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if not current_block.has_valid_transactions():
                return False
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True