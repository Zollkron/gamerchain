"""
Block Explorer API for PlayerGold
Provides real-time metrics, block/transaction data, and network statistics
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading

from src.blockchain.block import Block
from src.blockchain.transaction import Transaction
from src.reputation.node_reputation import NodeReputationManager
from src.p2p.network import P2PNetwork


class ExplorerAPI:
    """API for block explorer with real-time metrics and monitoring"""
    
    def __init__(self, blockchain, p2p_network: P2PNetwork, 
                 reputation_manager: NodeReputationManager):
        self.app = Flask(__name__)
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.blockchain = blockchain
        self.p2p_network = p2p_network
        self.reputation_manager = reputation_manager
        
        # Metrics tracking
        self.metrics_history = []
        self.tps_window = []
        self.latency_samples = []
        
        self.setup_routes()
        self.setup_websocket_handlers()
        self.start_metrics_collector()
    
    def setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/api/network/metrics', methods=['GET'])
        def get_network_metrics():
            """Get current network metrics"""
            metrics = self.calculate_network_metrics()
            return jsonify(metrics)
        
        @self.app.route('/api/blocks/recent', methods=['GET'])
        def get_recent_blocks():
            """Get recent blocks"""
            limit = int(request.args.get('limit', 10))
            blocks = self.get_recent_blocks(limit)
            return jsonify(blocks)
        
        @self.app.route('/api/blocks/<block_hash>', methods=['GET'])
        def get_block(block_hash):
            """Get block by hash"""
            block = self.find_block_by_hash(block_hash)
            if block:
                return jsonify(self.serialize_block(block))
            return jsonify({'error': 'Block not found'}), 404
        
        @self.app.route('/api/transactions/recent', methods=['GET'])
        def get_recent_transactions():
            """Get recent transactions"""
            limit = int(request.args.get('limit', 10))
            transactions = self.get_recent_transactions(limit)
            return jsonify(transactions)
        
        @self.app.route('/api/transactions/<tx_hash>', methods=['GET'])
        def get_transaction(tx_hash):
            """Get transaction by hash"""
            tx = self.find_transaction_by_hash(tx_hash)
            if tx:
                return jsonify(self.serialize_transaction(tx))
            return jsonify({'error': 'Transaction not found'}), 404
        
        @self.app.route('/api/address/<address>', methods=['GET'])
        def get_address_info(address):
            """Get address information"""
            info = self.get_address_details(address)
            return jsonify(info)
        
        @self.app.route('/api/nodes/distribution', methods=['GET'])
        def get_node_distribution():
            """Get AI node distribution and statistics"""
            distribution = self.get_node_distribution_stats()
            return jsonify(distribution)
        
        @self.app.route('/api/search', methods=['GET'])
        def search():
            """Search for block, transaction, or address"""
            query = request.args.get('q', '')
            result = self.perform_search(query)
            return jsonify(result)
        
        @self.app.route('/api/stats/tps', methods=['GET'])
        def get_tps_history():
            """Get TPS history"""
            hours = int(request.args.get('hours', 1))
            history = self.get_tps_history(hours)
            return jsonify(history)
        
        @self.app.route('/api/stats/latency', methods=['GET'])
        def get_latency_history():
            """Get latency history"""
            hours = int(request.args.get('hours', 1))
            history = self.get_latency_history(hours)
            return jsonify(history)
    
    def setup_websocket_handlers(self):
        """Setup WebSocket handlers for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected to explorer WebSocket')
            emit('connected', {'status': 'connected'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected from explorer WebSocket')
        
        @self.socketio.on('subscribe_metrics')
        def handle_subscribe_metrics():
            """Subscribe to real-time metrics updates"""
            emit('subscribed', {'channel': 'metrics'})
    
    def calculate_network_metrics(self) -> Dict:
        """Calculate current network metrics"""
        # Calculate TPS (transactions per second)
        tps = self.calculate_tps()
        
        # Calculate average latency
        latency = self.calculate_average_latency()
        
        # Get active nodes count
        active_nodes = len(self.p2p_network.get_active_peers())
        
        # Get current block height
        block_height = len(self.blockchain.chain)
        
        # Get total supply and circulating supply
        total_supply = self.blockchain.get_total_supply()
        circulating_supply = self.blockchain.get_circulating_supply()
        
        return {
            'tps': tps,
            'latency': latency,
            'active_nodes': active_nodes,
            'block_height': block_height,
            'total_supply': total_supply,
            'circulating_supply': circulating_supply,
            'timestamp': time.time()
        }
    
    def calculate_tps(self) -> float:
        """Calculate transactions per second over last minute"""
        now = time.time()
        one_minute_ago = now - 60
        
        # Count transactions in last minute
        tx_count = 0
        for block in reversed(self.blockchain.chain):
            if block.timestamp < one_minute_ago:
                break
            tx_count += len(block.transactions)
        
        return tx_count / 60.0
    
    def calculate_average_latency(self) -> int:
        """Calculate average block validation latency in milliseconds"""
        if not self.latency_samples:
            return 0
        
        # Average of last 10 samples
        recent_samples = self.latency_samples[-10:]
        return int(sum(recent_samples) / len(recent_samples))
    
    def get_recent_blocks(self, limit: int = 10) -> List[Dict]:
        """Get most recent blocks"""
        recent_blocks = self.blockchain.chain[-limit:]
        return [self.serialize_block(block) for block in reversed(recent_blocks)]
    
    def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """Get most recent transactions"""
        transactions = []
        
        for block in reversed(self.blockchain.chain):
            for tx in block.transactions:
                transactions.append(self.serialize_transaction(tx, 'confirmed'))
                if len(transactions) >= limit:
                    return transactions
        
        return transactions
    
    def find_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Find block by hash"""
        for block in self.blockchain.chain:
            if block.hash == block_hash:
                return block
        return None
    
    def find_transaction_by_hash(self, tx_hash: str) -> Optional[tuple]:
        """Find transaction by hash, returns (transaction, status)"""
        # Search in blockchain
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.calculate_hash() == tx_hash:
                    return (tx, 'confirmed')
        
        # Search in pending transactions
        if hasattr(self.blockchain, 'pending_transactions'):
            for tx in self.blockchain.pending_transactions:
                if tx.calculate_hash() == tx_hash:
                    return (tx, 'pending')
        
        return None
    
    def get_address_details(self, address: str) -> Dict:
        """Get detailed information about an address"""
        balance = self.blockchain.get_balance(address)
        
        # Count transactions
        tx_count = 0
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.from_address == address or tx.to_address == address:
                    tx_count += 1
        
        # Get reputation if available
        reputation = 0
        if hasattr(self.reputation_manager, 'user_reputation'):
            reputation = self.reputation_manager.user_reputation.get_reputation(address)
        
        return {
            'address': address,
            'balance': float(balance),
            'transaction_count': tx_count,
            'reputation': reputation
        }
    
    def get_node_distribution_stats(self) -> Dict:
        """Get AI node distribution statistics"""
        nodes = self.p2p_network.get_active_peers()
        
        # Count by model type
        model_distribution = {}
        node_details = []
        
        for node in nodes:
            node_info = self.p2p_network.get_peer_info(node)
            if node_info and 'model_name' in node_info:
                model_name = node_info['model_name']
                model_distribution[model_name] = model_distribution.get(model_name, 0) + 1
                
                # Get reputation
                reputation = self.reputation_manager.get_reputation(node)
                
                node_details.append({
                    'node_id': node,
                    'model_name': model_name,
                    'model_hash': node_info.get('model_hash', ''),
                    'total_validations': reputation.get('total_validations', 0),
                    'last_validation': reputation.get('last_validation', 0),
                    'reputation_score': reputation.get('score', 0)
                })
        
        models = [{'name': name, 'count': count} 
                  for name, count in model_distribution.items()]
        
        return {
            'models': models,
            'nodes': node_details,
            'total_nodes': len(nodes)
        }
    
    def perform_search(self, query: str) -> Dict:
        """Search for block, transaction, or address"""
        query = query.strip()
        
        # Try to find as block hash
        block = self.find_block_by_hash(query)
        if block:
            return {
                'type': 'block',
                'data': self.serialize_block(block)
            }
        
        # Try to find as transaction hash
        tx_result = self.find_transaction_by_hash(query)
        if tx_result:
            tx, status = tx_result
            return {
                'type': 'transaction',
                'data': self.serialize_transaction(tx, status)
            }
        
        # Try as address
        if len(query) == 64:  # Assuming address length
            address_info = self.get_address_details(query)
            if address_info['transaction_count'] > 0:
                return {
                    'type': 'address',
                    'data': address_info
                }
        
        return {'type': 'not_found', 'data': None}
    
    def get_tps_history(self, hours: int) -> List[Dict]:
        """Get TPS history for specified hours"""
        cutoff_time = time.time() - (hours * 3600)
        return [m for m in self.metrics_history 
                if m['timestamp'] >= cutoff_time and 'tps' in m]
    
    def get_latency_history(self, hours: int) -> List[Dict]:
        """Get latency history for specified hours"""
        cutoff_time = time.time() - (hours * 3600)
        return [m for m in self.metrics_history 
                if m['timestamp'] >= cutoff_time and 'latency' in m]
    
    def serialize_block(self, block: Block) -> Dict:
        """Serialize block to JSON-compatible dict"""
        return {
            'index': block.index,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'timestamp': block.timestamp,
            'transactions': [self.serialize_transaction(tx, 'confirmed') 
                           for tx in block.transactions],
            'merkle_root': block.merkle_root,
            'ai_validators': block.ai_validators if hasattr(block, 'ai_validators') else []
        }
    
    def serialize_transaction(self, tx: Transaction, status: str = 'confirmed') -> Dict:
        """Serialize transaction to JSON-compatible dict"""
        return {
            'hash': tx.calculate_hash(),
            'from_address': tx.from_address,
            'to_address': tx.to_address,
            'amount': float(tx.amount),
            'fee': float(tx.fee),
            'timestamp': tx.timestamp,
            'status': status,
            'transaction_type': tx.transaction_type.value if hasattr(tx, 'transaction_type') else 'TRANSFER'
        }
    
    def broadcast_new_block(self, block: Block):
        """Broadcast new block to connected clients"""
        self.socketio.emit('new_block', {
            'type': 'new_block',
            'block': self.serialize_block(block)
        })
    
    def broadcast_new_transaction(self, tx: Transaction):
        """Broadcast new transaction to connected clients"""
        self.socketio.emit('new_transaction', {
            'type': 'new_transaction',
            'transaction': self.serialize_transaction(tx, 'pending')
        })
    
    def broadcast_metrics_update(self, metrics: Dict):
        """Broadcast metrics update to connected clients"""
        self.socketio.emit('metrics_update', {
            'type': 'metrics_update',
            'metrics': metrics
        })
    
    def start_metrics_collector(self):
        """Start background thread to collect metrics"""
        def collect_metrics():
            while True:
                metrics = self.calculate_network_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours
                cutoff = time.time() - (24 * 3600)
                self.metrics_history = [m for m in self.metrics_history 
                                       if m['timestamp'] >= cutoff]
                
                # Broadcast to connected clients
                self.broadcast_metrics_update(metrics)
                
                time.sleep(5)  # Collect every 5 seconds
        
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
    
    def record_block_latency(self, latency_ms: int):
        """Record block validation latency"""
        self.latency_samples.append(latency_ms)
        if len(self.latency_samples) > 100:
            self.latency_samples.pop(0)
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the explorer API server"""
        self.socketio.run(self.app, host=host, port=port, debug=debug)


def create_explorer_api(blockchain, p2p_network, reputation_manager):
    """Factory function to create ExplorerAPI instance"""
    return ExplorerAPI(blockchain, p2p_network, reputation_manager)
