"""
Example: Complete Monitoring Integration for PlayerGold
Demonstrates how to use the alert system, immutable logger, and block explorer together
"""

import time
from decimal import Decimal

# Import monitoring components
from src.monitoring import (
    create_alert_system, create_immutable_logger,
    AlertType, AlertSeverity, LogCategory, LogLevel,
    ConsoleAlertHandler, FileAlertHandler, PatternAnalyzer
)

# Import blockchain components (mock for example)
from src.blockchain.block import Block
from src.blockchain.transaction import Transaction


class MonitoredBlockchain:
    """
    Example blockchain with integrated monitoring
    """
    
    def __init__(self):
        # Initialize monitoring systems
        self.alert_system = create_alert_system([
            ConsoleAlertHandler(),
            FileAlertHandler('alerts.log')
        ])
        
        self.logger = create_immutable_logger('logs')
        
        # Blockchain state
        self.chain = []
        self.pending_transactions = []
        
        # Log system initialization
        self.logger.info(LogCategory.SYSTEM, "Blockchain initialized", {
            'timestamp': time.time()
        })
    
    def add_transaction(self, transaction: Transaction):
        """Add transaction with monitoring"""
        try:
            # Log transaction
            self.logger.info(LogCategory.TRANSACTION, "Transaction received", {
                'from': transaction.from_address,
                'to': transaction.to_address,
                'amount': float(transaction.amount),
                'fee': float(transaction.fee)
            })
            
            # Validate transaction
            if transaction.amount <= 0:
                self.logger.error(LogCategory.TRANSACTION, "Invalid amount", {
                    'amount': float(transaction.amount)
                })
                raise ValueError("Invalid transaction amount")
            
            self.pending_transactions.append(transaction)
            
            # Check for transaction spike
            if len(self.pending_transactions) > 100:
                self.alert_system.create_alert(
                    AlertType.TRANSACTION_SPIKE,
                    AlertSeverity.WARNING,
                    f"High pending transactions: {len(self.pending_transactions)}",
                    {'count': len(self.pending_transactions)}
                )
            
            return True
            
        except Exception as e:
            self.logger.error(LogCategory.TRANSACTION, "Transaction failed", {
                'error': str(e)
            })
            raise
    
    def mine_block(self, miner_address: str):
        """Mine a new block with monitoring"""
        start_time = time.time()
        
        try:
            # Create block
            block = Block(
                index=len(self.chain),
                previous_hash=self.chain[-1].hash if self.chain else "0" * 64,
                timestamp=time.time(),
                transactions=self.pending_transactions[:10],  # Take first 10
                merkle_root="merkle_root_placeholder"
            )
            
            # Simulate validation
            validation_time = (time.time() - start_time) * 1000  # ms
            
            # Log block creation
            self.logger.info(LogCategory.BLOCK, "Block mined", {
                'height': block.index,
                'transactions': len(block.transactions),
                'validation_time_ms': validation_time,
                'miner': miner_address
            })
            
            # Check validation time
            if validation_time > 100:
                self.alert_system.create_alert(
                    AlertType.BLOCK_VALIDATION_TIMEOUT,
                    AlertSeverity.WARNING,
                    f"Slow block validation: {validation_time:.2f}ms",
                    {'validation_time': validation_time, 'block_height': block.index}
                )
            
            # Add to chain
            self.chain.append(block)
            self.pending_transactions = self.pending_transactions[10:]
            
            return block
            
        except Exception as e:
            self.logger.critical(LogCategory.BLOCK, "Block mining failed", {
                'error': str(e),
                'height': len(self.chain)
            })
            
            self.alert_system.create_alert(
                AlertType.CONSENSUS_FAILURE,
                AlertSeverity.CRITICAL,
                "Failed to mine block",
                {'error': str(e)}
            )
            raise
    
    def validate_node(self, node_id: str, model_hash: str, expected_hash: str):
        """Validate AI node with monitoring"""
        try:
            if model_hash != expected_hash:
                # Log security issue
                self.logger.critical(LogCategory.SECURITY, "Invalid model hash detected", {
                    'node_id': node_id,
                    'expected_hash': expected_hash,
                    'actual_hash': model_hash
                })
                
                # Create critical alert
                self.alert_system.create_alert(
                    AlertType.INVALID_MODEL_HASH,
                    AlertSeverity.CRITICAL,
                    f"Node {node_id} has invalid model hash",
                    {
                        'node_id': node_id,
                        'expected': expected_hash,
                        'actual': model_hash
                    }
                )
                
                return False
            
            # Log successful validation
            self.logger.info(LogCategory.NODE, "Node validated successfully", {
                'node_id': node_id,
                'model_hash': model_hash
            })
            
            return True
            
        except Exception as e:
            self.logger.error(LogCategory.NODE, "Node validation error", {
                'node_id': node_id,
                'error': str(e)
            })
            raise
    
    def check_network_health(self):
        """Check network health and create alerts if needed"""
        # Calculate metrics
        tps = len(self.pending_transactions) / 60.0  # Rough estimate
        latency = 50  # Placeholder
        active_nodes = 10  # Placeholder
        
        metrics = {
            'tps': tps,
            'latency': latency,
            'active_nodes': active_nodes,
            'block_height': len(self.chain)
        }
        
        # Log metrics
        self.logger.debug(LogCategory.NETWORK, "Network health check", metrics)
        
        # Check with alert system
        self.alert_system.check_network_health(metrics)
        
        return metrics
    
    def get_monitoring_report(self):
        """Generate comprehensive monitoring report"""
        # Alert statistics
        alert_stats = self.alert_system.get_statistics()
        
        # Log statistics
        log_stats = self.logger.get_statistics()
        
        # Pattern analysis
        analyzer = PatternAnalyzer(self.logger)
        error_patterns = analyzer.analyze_error_patterns(hours=24)
        
        report = {
            'alerts': alert_stats,
            'logs': log_stats,
            'error_patterns': error_patterns,
            'blockchain': {
                'height': len(self.chain),
                'pending_transactions': len(self.pending_transactions)
            }
        }
        
        return report


def main():
    """Main example demonstrating monitoring integration"""
    print("=" * 80)
    print("PlayerGold Monitoring Integration Example")
    print("=" * 80)
    print()
    
    # Create monitored blockchain
    blockchain = MonitoredBlockchain()
    
    print("1. Adding transactions...")
    for i in range(5):
        tx = Transaction(
            from_address=f"address_{i}",
            to_address=f"address_{i+1}",
            amount=Decimal(f"{10 + i}"),
            fee=Decimal("0.1")
        )
        blockchain.add_transaction(tx)
    print(f"   ✓ Added 5 transactions")
    print()
    
    print("2. Mining block...")
    block = blockchain.mine_block("miner_address_1")
    print(f"   ✓ Mined block #{block.index}")
    print()
    
    print("3. Validating AI nodes...")
    # Valid node
    blockchain.validate_node("node1", "abc123", "abc123")
    print("   ✓ Node 1 validated (valid hash)")
    
    # Invalid node (will create alert)
    blockchain.validate_node("node2", "wrong_hash", "abc123")
    print("   ✗ Node 2 validation failed (invalid hash)")
    print()
    
    print("4. Checking network health...")
    metrics = blockchain.check_network_health()
    print(f"   TPS: {metrics['tps']:.2f}")
    print(f"   Latency: {metrics['latency']}ms")
    print(f"   Active Nodes: {metrics['active_nodes']}")
    print()
    
    print("5. Generating monitoring report...")
    report = blockchain.get_monitoring_report()
    print(f"   Total Alerts: {report['alerts']['total_alerts']}")
    print(f"   Active Alerts: {report['alerts']['active_alerts']}")
    print(f"   Total Logs: {report['logs']['total_logs']}")
    print(f"   Integrity Verified: {report['logs']['integrity_verified']}")
    print()
    
    print("6. Querying logs...")
    # Get critical logs
    critical_logs = blockchain.logger.get_critical_logs(hours=1)
    print(f"   Critical logs: {len(critical_logs)}")
    for log in critical_logs:
        print(f"   - {log.message}")
    print()
    
    print("7. Querying alerts...")
    # Get active alerts
    active_alerts = blockchain.alert_system.get_active_alerts()
    print(f"   Active alerts: {len(active_alerts)}")
    for alert in active_alerts:
        print(f"   - [{alert.severity.value.upper()}] {alert.message}")
    print()
    
    print("8. Verifying log integrity...")
    integrity = blockchain.logger.verify_integrity()
    print(f"   Log chain integrity: {'✓ VALID' if integrity else '✗ COMPROMISED'}")
    print()
    
    print("9. Analyzing patterns...")
    analyzer = PatternAnalyzer(blockchain.logger)
    error_patterns = analyzer.analyze_error_patterns(hours=1)
    print(f"   Total errors: {error_patterns['total_errors']}")
    if error_patterns['repeated_messages']:
        print("   Repeated error messages:")
        for msg, count in error_patterns['repeated_messages'].items():
            print(f"   - {msg}: {count} times")
    print()
    
    print("=" * 80)
    print("Example completed successfully!")
    print("=" * 80)
    print()
    print("Files created:")
    print("  - logs/master.log (immutable log chain)")
    print("  - logs/security.log (security events)")
    print("  - logs/transaction.log (transaction events)")
    print("  - alerts.log (alert history)")
    print()


if __name__ == "__main__":
    main()
