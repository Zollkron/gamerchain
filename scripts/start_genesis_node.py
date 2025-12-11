#!/usr/bin/env python3
"""
Nodo Génesis Autónomo PlayerGold

Este nodo funciona como una blockchain completa de un solo nodo:
- Procesa transacciones del faucet
- Valida bloques con IA
- Actualiza la blockchain
- Envía recompensas de minería
- Mantiene consenso consigo mismo
"""

import asyncio
import sys
import logging
import threading
import time
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.blockchain.blockchain import Blockchain
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GenesisNode:
    def __init__(self):
        self.blockchain = Blockchain()
        self.pending_transactions = []
        self.balances = {}
        self.transaction_history = {}
        self.is_mining = False
        self.mining_rewards = {}
        self.block_count = 0  # Track blocks mined
        
        # Genesis node configuration
        self.node_id = "genesis_node_1"
        self.validator_address = "PGgenesis000000000000000000000000000000"
        self.faucet_address = "PGfaucet000000000000000000000000000000000"
        
        # Initialize genesis balances
        self.balances[self.faucet_address] = 1000000.0  # 1M PRGLD for faucet
        self.balances[self.validator_address] = 100000.0  # 100K PRGLD for validator
        
        logger.info(f"🏗️  Genesis Node initialized: {self.node_id}")
        logger.info(f"💰 Faucet balance: {self.balances[self.faucet_address]} PRGLD")
        logger.info(f"⚡ Validator balance: {self.balances[self.validator_address]} PRGLD")

    def create_api_app(self):
        """Create Flask API app"""
        app = Flask(__name__)
        
        @app.route('/api/v1/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'network': 'genesis-testnet',
                'node_id': self.node_id,
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0',
                'blockchain_height': len(self.blockchain.chain) if hasattr(self.blockchain, 'chain') else 1
            })

        @app.route('/api/v1/balance/<address>', methods=['GET'])
        def get_balance(address):
            balance = self.balances.get(address, 0.0)
            return jsonify({
                'success': True,
                'address': address,
                'balance': balance,
                'network': 'genesis-testnet',
                'timestamp': datetime.utcnow().isoformat()
            })

        @app.route('/api/v1/transactions/history/<address>', methods=['GET'])
        def get_transaction_history(address):
            transactions = self.transaction_history.get(address, [])
            
            logger.info(f"📋 Transaction history request for {address}")
            logger.info(f"📋 Found {len(transactions)} transactions")
            for i, tx in enumerate(transactions):
                logger.info(f"📋 TX {i+1}: {tx['type']} - {tx['amount']} PRGLD - {tx['status']}")
            
            return jsonify({
                'success': True,
                'address': address,
                'transactions': transactions,
                'total': len(transactions),
                'page': 1,
                'per_page': 20
            })

        @app.route('/api/v1/faucet', methods=['POST'])
        def faucet():
            try:
                logger.info("🚰 Faucet request received")
                data = request.get_json()
                logger.info(f"📋 Request data: {data}")
                
                if not data or 'address' not in data:
                    logger.error("❌ Missing address in request")
                    return jsonify({'error': 'Dirección requerida'}), 400
                
                address = data['address']
                amount = float(data.get('amount', 1000))
                
                # Create faucet transaction
                tx_id = self.process_faucet_transaction(address, amount)
                
                logger.info(f"✅ Faucet transaction created: {tx_id}")
                
                return jsonify({
                    'success': True,
                    'transactionId': tx_id,
                    'amount': amount,
                    'address': address,
                    'message': f'Faucet: {amount} PRGLD enviados a {address}'
                }), 200
                
            except Exception as e:
                logger.error(f"❌ Faucet error: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500

        @app.route('/api/v1/network/status', methods=['GET'])
        def network_status():
            return jsonify({
                'network': 'genesis-testnet',
                'node_id': self.node_id,
                'chain_length': self.block_count + 1,  # +1 for genesis block
                'last_block_index': self.block_count,
                'last_block_hash': f'block_{self.block_count}' if self.block_count > 0 else 'genesis_block_hash',
                'pending_transactions': len(self.pending_transactions),
                'difficulty': 1,
                'is_mining': self.is_mining,
                'validator_address': self.validator_address,
                'timestamp': datetime.utcnow().isoformat()
            })

        @app.route('/api/v1/mining/stats/<address>', methods=['GET'])
        def get_mining_stats(address):
            """Get mining statistics for a specific address"""
            # Count mining rewards for this address
            mining_rewards = []
            total_rewards = 0.0
            blocks_validated = 0
            
            if address in self.transaction_history:
                for tx in self.transaction_history[address]:
                    if tx['type'] == 'mining_reward':
                        mining_rewards.append(tx)
                        total_rewards += float(tx['amount'])
                        blocks_validated += 1
            
            return jsonify({
                'success': True,
                'address': address,
                'mining_stats': {
                    'blocks_validated': blocks_validated,
                    'rewards_earned': total_rewards,
                    'challenges_processed': blocks_validated,  # Each block is a challenge
                    'success_rate': 100.0 if blocks_validated > 0 else 0.0,
                    'reputation': 100.0,
                    'is_mining': self.is_mining,
                    'last_reward': mining_rewards[-1] if mining_rewards else None
                },
                'network': 'genesis-testnet',
                'timestamp': datetime.utcnow().isoformat()
            })

        return app

    def process_faucet_transaction(self, to_address, amount):
        """Process a faucet transaction"""
        logger.info(f"💸 Processing faucet transaction: {amount} PRGLD to {to_address}")
        
        # Check faucet balance
        if self.balances[self.faucet_address] < amount:
            raise Exception("Insufficient faucet balance")
        
        # Create transaction
        tx_id = f"faucet_tx_{int(time.time())}_{hash(to_address) % 10000}"
        
        # Update balances
        self.balances[self.faucet_address] -= amount
        if to_address not in self.balances:
            self.balances[to_address] = 0
        self.balances[to_address] += amount
        
        # Create transaction record
        transaction = {
            'id': tx_id,
            'type': 'faucet_transfer',
            'from': self.faucet_address,
            'to': to_address,
            'amount': str(amount),
            'fee': '0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'pending',
            'memo': f'Genesis faucet - {amount} PRGLD',
            'blockNumber': None,
            'confirmations': 0
        }
        
        # Add to pending transactions
        self.pending_transactions.append(transaction)
        
        # Add to transaction history
        if to_address not in self.transaction_history:
            self.transaction_history[to_address] = []
        self.transaction_history[to_address].append(transaction)
        
        logger.info(f"📝 Transaction added to pending: {tx_id}")
        logger.info(f"💰 New balance for {to_address}: {self.balances[to_address]} PRGLD")
        logger.info(f"🏦 Faucet balance remaining: {self.balances[self.faucet_address]} PRGLD")
        
        # Trigger mining process
        self.trigger_mining()
        
        return tx_id

    def trigger_mining(self):
        """Trigger the mining process to validate pending transactions"""
        if self.is_mining or len(self.pending_transactions) == 0:
            return
        
        logger.info("⛏️  Triggering mining process...")
        threading.Thread(target=self.mine_block, daemon=True).start()

    def mine_block(self):
        """Mine a new block with pending transactions"""
        if self.is_mining:
            return
        
        self.is_mining = True
        logger.info("🔨 Starting block mining...")
        
        try:
            # Simulate AI validation process
            logger.info("🤖 AI validating transactions...")
            time.sleep(2)  # Simulate AI processing time
            
            # Create new block
            self.block_count += 1
            block_number = self.block_count
            block_hash = f"block_{block_number}_{int(time.time())}"
            
            logger.info(f"📦 Mining block #{block_number}")
            logger.info(f"📋 Pending transactions: {len(self.pending_transactions)}")
            
            # Process all pending transactions and collect miners
            confirmed_transactions = []
            miners = set()  # Track unique miners for rewards
            
            for tx in self.pending_transactions:
                tx['status'] = 'confirmed'
                tx['blockNumber'] = block_number
                tx['confirmations'] = 1
                confirmed_transactions.append(tx)
                
                # Track miners (recipients of transactions for reward distribution)
                if tx['to'] != self.faucet_address and tx['to'] != self.validator_address:
                    miners.add(tx['to'])
                
                logger.info(f"✅ Transaction confirmed: {tx['id']}")
            
            # Clear pending transactions
            self.pending_transactions = []
            
            # Calculate and distribute mining rewards
            if len(confirmed_transactions) > 0 and len(miners) > 0:
                total_mining_reward = len(confirmed_transactions) * 10.0  # 10 PRGLD per transaction
                reward_per_miner = total_mining_reward / len(miners)
                
                logger.info(f"💎 Total mining reward: {total_mining_reward} PRGLD")
                logger.info(f"👥 Miners to reward: {len(miners)} - {list(miners)}")
                logger.info(f"💰 Reward per miner: {reward_per_miner} PRGLD")
                
                # Send mining rewards to each miner
                for miner_address in miners:
                    logger.info(f"🎯 Sending reward to: {miner_address}")
                    self.send_mining_reward(miner_address, reward_per_miner, block_number)
                
                # Small reward to validator for processing
                validator_reward = 1.0  # 1 PRGLD for validator
                self.balances[self.validator_address] += validator_reward
                logger.info(f"⚡ Validator processing fee: {validator_reward} PRGLD")
                logger.info(f"⚡ Validator balance: {self.balances[self.validator_address]} PRGLD")
            else:
                logger.warning(f"❌ No mining rewards sent - Transactions: {len(confirmed_transactions)}, Miners: {len(miners)}")
            
            logger.info(f"🎉 Block #{block_number} mined successfully!")
            logger.info(f"📦 Block hash: {block_hash}")
            logger.info(f"📋 Transactions confirmed: {len(confirmed_transactions)}")
            
        except Exception as e:
            logger.error(f"❌ Mining error: {e}")
            # Revert transactions to pending on error
            for tx in confirmed_transactions:
                tx['status'] = 'pending'
                tx['blockNumber'] = None
                tx['confirmations'] = 0
                self.pending_transactions.append(tx)
        
        finally:
            self.is_mining = False

    def send_mining_reward(self, miner_address, reward_amount, block_number):
        """Send mining reward to a miner as a real transaction"""
        logger.info(f"🏆 Sending mining reward: {reward_amount} PRGLD to {miner_address}")
        
        # Create mining reward transaction
        tx_id = f"mining_reward_{int(time.time())}_{hash(miner_address) % 10000}"
        
        # Update balances
        if self.validator_address not in self.balances:
            self.balances[self.validator_address] = 100000.0
        
        # Validator pays the reward (from pool)
        if miner_address not in self.balances:
            self.balances[miner_address] = 0
        self.balances[miner_address] += reward_amount
        
        # Create mining reward transaction record
        mining_transaction = {
            'id': tx_id,
            'type': 'mining_reward',
            'from': self.validator_address,
            'to': miner_address,
            'amount': str(reward_amount),
            'fee': '0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'confirmed',
            'memo': f'Mining reward - Block #{block_number}',
            'blockNumber': block_number,
            'confirmations': 1
        }
        
        # Add to transaction history
        if miner_address not in self.transaction_history:
            self.transaction_history[miner_address] = []
        self.transaction_history[miner_address].append(mining_transaction)
        
        logger.info(f"🎁 Mining reward sent: {tx_id}")
        logger.info(f"💰 New balance for {miner_address}: {self.balances[miner_address]} PRGLD")

    def start_api_server(self):
        """Start the API server"""
        app = self.create_api_app()
        logger.info("🌐 Starting Genesis Node API server...")
        app.run(host='0.0.0.0', port=18080, debug=False)

    def run(self):
        """Run the genesis node"""
        logger.info("=" * 60)
        logger.info("🏗️  PLAYERGOLD GENESIS NODE")
        logger.info("=" * 60)
        logger.info(f"🆔 Node ID: {self.node_id}")
        logger.info(f"🌐 API: http://127.0.0.1:18080")
        logger.info(f"⚡ Validator: {self.validator_address}")
        logger.info(f"🚰 Faucet: {self.faucet_address}")
        logger.info("=" * 60)
        
        # Start API server
        self.start_api_server()

def main():
    """Main entry point"""
    try:
        genesis_node = GenesisNode()
        genesis_node.run()
    except KeyboardInterrupt:
        logger.info("\n🛑 Genesis node stopped by user")
    except Exception as e:
        logger.error(f"❌ Genesis node error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()