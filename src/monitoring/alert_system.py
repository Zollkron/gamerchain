"""
Alert System for PlayerGold Network
Detects anomalies and sends automatic alerts for critical events
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Callable, Optional
from datetime import datetime, timedelta
import time
import threading
import json
from collections import deque


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    NODE_FAILURE = "node_failure"
    HIGH_LATENCY = "high_latency"
    LOW_TPS = "low_tps"
    CONSENSUS_FAILURE = "consensus_failure"
    NETWORK_PARTITION = "network_partition"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    INVALID_MODEL_HASH = "invalid_model_hash"
    REPUTATION_DROP = "reputation_drop"
    TRANSACTION_SPIKE = "transaction_spike"
    BLOCK_VALIDATION_TIMEOUT = "block_validation_timeout"


@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: float
    details: Dict
    resolved: bool = False
    resolved_at: Optional[float] = None


class AlertHandler:
    """Base class for alert handlers"""
    
    def handle(self, alert: Alert):
        """Handle an alert"""
        raise NotImplementedError


class ConsoleAlertHandler(AlertHandler):
    """Print alerts to console"""
    
    def handle(self, alert: Alert):
        severity_colors = {
            AlertSeverity.INFO: '\033[94m',      # Blue
            AlertSeverity.WARNING: '\033[93m',   # Yellow
            AlertSeverity.ERROR: '\033[91m',     # Red
            AlertSeverity.CRITICAL: '\033[95m'   # Magenta
        }
        reset_color = '\033[0m'
        
        color = severity_colors.get(alert.severity, '')
        timestamp = datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"{color}[{alert.severity.value.upper()}] {timestamp} - {alert.alert_type.value}{reset_color}")
        print(f"  {alert.message}")
        if alert.details:
            print(f"  Details: {json.dumps(alert.details, indent=2)}")


class FileAlertHandler(AlertHandler):
    """Write alerts to file"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
    
    def handle(self, alert: Alert):
        with open(self.filepath, 'a') as f:
            alert_data = {
                'alert_id': alert.alert_id,
                'type': alert.alert_type.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp,
                'details': alert.details,
                'resolved': alert.resolved
            }
            f.write(json.dumps(alert_data) + '\n')


class WebhookAlertHandler(AlertHandler):
    """Send alerts to webhook endpoint"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def handle(self, alert: Alert):
        import requests
        
        payload = {
            'alert_id': alert.alert_id,
            'type': alert.alert_type.value,
            'severity': alert.severity.value,
            'message': alert.message,
            'timestamp': alert.timestamp,
            'details': alert.details
        }
        
        try:
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")


class AnomalyDetector:
    """Detects anomalies in network behavior"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.tps_history = deque(maxlen=window_size)
        self.latency_history = deque(maxlen=window_size)
        self.node_count_history = deque(maxlen=window_size)
    
    def add_sample(self, tps: float, latency: float, node_count: int):
        """Add a sample to the history"""
        self.tps_history.append(tps)
        self.latency_history.append(latency)
        self.node_count_history.append(node_count)
    
    def detect_tps_anomaly(self, threshold_std: float = 2.0) -> Optional[Dict]:
        """Detect TPS anomalies using standard deviation"""
        if len(self.tps_history) < 10:
            return None
        
        import statistics
        mean = statistics.mean(self.tps_history)
        stdev = statistics.stdev(self.tps_history)
        current = self.tps_history[-1]
        
        if abs(current - mean) > threshold_std * stdev:
            return {
                'current': current,
                'mean': mean,
                'stdev': stdev,
                'deviation': abs(current - mean) / stdev if stdev > 0 else 0
            }
        return None
    
    def detect_latency_anomaly(self, threshold_ms: int = 2000) -> Optional[Dict]:
        """Detect high latency"""
        if not self.latency_history:
            return None
        
        current = self.latency_history[-1]
        if current > threshold_ms:
            import statistics
            avg = statistics.mean(self.latency_history)
            return {
                'current': current,
                'average': avg,
                'threshold': threshold_ms
            }
        return None
    
    def detect_node_failure(self, threshold_drop: float = 0.3) -> Optional[Dict]:
        """Detect significant drop in active nodes"""
        if len(self.node_count_history) < 10:
            return None
        
        recent_avg = sum(list(self.node_count_history)[-10:]) / 10
        current = self.node_count_history[-1]
        
        if recent_avg > 0 and (recent_avg - current) / recent_avg > threshold_drop:
            return {
                'current': current,
                'recent_average': recent_avg,
                'drop_percentage': ((recent_avg - current) / recent_avg) * 100
            }
        return None


class AlertSystem:
    """Main alert system for network monitoring"""
    
    def __init__(self):
        self.handlers: List[AlertHandler] = []
        self.alerts: List[Alert] = []
        self.alert_counter = 0
        self.anomaly_detector = AnomalyDetector()
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Alert rules
        self.rules = {
            'high_latency_threshold': 2000,  # ms
            'low_tps_threshold': 10,
            'node_failure_threshold': 0.3,  # 30% drop
            'reputation_drop_threshold': 20  # points
        }
    
    def add_handler(self, handler: AlertHandler):
        """Add an alert handler"""
        self.handlers.append(handler)
    
    def create_alert(self, alert_type: AlertType, severity: AlertSeverity,
                    message: str, details: Dict = None) -> Alert:
        """Create and dispatch an alert"""
        self.alert_counter += 1
        alert = Alert(
            alert_id=f"ALERT-{self.alert_counter:06d}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=time.time(),
            details=details or {}
        )
        
        self.alerts.append(alert)
        self._dispatch_alert(alert)
        
        return alert
    
    def _dispatch_alert(self, alert: Alert):
        """Dispatch alert to all handlers"""
        for handler in self.handlers:
            try:
                handler.handle(alert)
            except Exception as e:
                print(f"Error in alert handler: {e}")
    
    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved"""
        for alert in self.alerts:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = time.time()
                return True
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        active = [a for a in self.alerts if not a.resolved]
        if severity:
            active = [a for a in active if a.severity == severity]
        return active
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours"""
        cutoff = time.time() - (hours * 3600)
        return [a for a in self.alerts if a.timestamp >= cutoff]
    
    def check_network_health(self, metrics: Dict):
        """Check network health and create alerts if needed"""
        # Add sample to anomaly detector
        self.anomaly_detector.add_sample(
            metrics.get('tps', 0),
            metrics.get('latency', 0),
            metrics.get('active_nodes', 0)
        )
        
        # Check for high latency
        if metrics.get('latency', 0) > self.rules['high_latency_threshold']:
            self.create_alert(
                AlertType.HIGH_LATENCY,
                AlertSeverity.WARNING,
                f"High latency detected: {metrics['latency']}ms",
                {'latency': metrics['latency'], 'threshold': self.rules['high_latency_threshold']}
            )
        
        # Check for low TPS
        if metrics.get('tps', 0) < self.rules['low_tps_threshold']:
            self.create_alert(
                AlertType.LOW_TPS,
                AlertSeverity.WARNING,
                f"Low TPS detected: {metrics['tps']:.2f}",
                {'tps': metrics['tps'], 'threshold': self.rules['low_tps_threshold']}
            )
        
        # Check for TPS anomalies
        tps_anomaly = self.anomaly_detector.detect_tps_anomaly()
        if tps_anomaly:
            self.create_alert(
                AlertType.TRANSACTION_SPIKE,
                AlertSeverity.INFO,
                f"TPS anomaly detected: {tps_anomaly['deviation']:.2f} standard deviations",
                tps_anomaly
            )
        
        # Check for latency anomalies
        latency_anomaly = self.anomaly_detector.detect_latency_anomaly()
        if latency_anomaly:
            self.create_alert(
                AlertType.HIGH_LATENCY,
                AlertSeverity.ERROR,
                f"Latency spike: {latency_anomaly['current']}ms",
                latency_anomaly
            )
        
        # Check for node failures
        node_failure = self.anomaly_detector.detect_node_failure()
        if node_failure:
            self.create_alert(
                AlertType.NODE_FAILURE,
                AlertSeverity.CRITICAL,
                f"Significant node drop: {node_failure['drop_percentage']:.1f}%",
                node_failure
            )
    
    def check_node_behavior(self, node_id: str, behavior_data: Dict):
        """Check individual node behavior for anomalies"""
        # Check for invalid model hash
        if behavior_data.get('invalid_hash'):
            self.create_alert(
                AlertType.INVALID_MODEL_HASH,
                AlertSeverity.CRITICAL,
                f"Node {node_id} has invalid model hash",
                {'node_id': node_id, 'expected_hash': behavior_data.get('expected_hash'),
                 'actual_hash': behavior_data.get('actual_hash')}
            )
        
        # Check for reputation drop
        if behavior_data.get('reputation_drop', 0) > self.rules['reputation_drop_threshold']:
            self.create_alert(
                AlertType.REPUTATION_DROP,
                AlertSeverity.WARNING,
                f"Node {node_id} reputation dropped by {behavior_data['reputation_drop']} points",
                {'node_id': node_id, 'drop': behavior_data['reputation_drop']}
            )
        
        # Check for suspicious activity
        if behavior_data.get('suspicious'):
            self.create_alert(
                AlertType.SUSPICIOUS_ACTIVITY,
                AlertSeverity.ERROR,
                f"Suspicious activity detected on node {node_id}",
                {'node_id': node_id, 'reason': behavior_data.get('reason')}
            )
    
    def check_consensus_health(self, consensus_data: Dict):
        """Check consensus mechanism health"""
        # Check for consensus failures
        if consensus_data.get('failed'):
            self.create_alert(
                AlertType.CONSENSUS_FAILURE,
                AlertSeverity.CRITICAL,
                "Consensus validation failed",
                consensus_data
            )
        
        # Check for validation timeouts
        if consensus_data.get('timeout'):
            self.create_alert(
                AlertType.BLOCK_VALIDATION_TIMEOUT,
                AlertSeverity.ERROR,
                f"Block validation timeout: {consensus_data.get('duration')}ms",
                consensus_data
            )
    
    def start_monitoring(self, check_interval: int = 30):
        """Start background monitoring thread"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                # Monitoring logic would go here
                # This would be called by the main application
                time.sleep(check_interval)
        
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def get_statistics(self) -> Dict:
        """Get alert statistics"""
        total = len(self.alerts)
        active = len(self.get_active_alerts())
        resolved = total - active
        
        by_severity = {}
        for severity in AlertSeverity:
            by_severity[severity.value] = len([a for a in self.alerts 
                                               if a.severity == severity])
        
        by_type = {}
        for alert_type in AlertType:
            by_type[alert_type.value] = len([a for a in self.alerts 
                                             if a.alert_type == alert_type])
        
        return {
            'total_alerts': total,
            'active_alerts': active,
            'resolved_alerts': resolved,
            'by_severity': by_severity,
            'by_type': by_type
        }


def create_alert_system(handlers: List[AlertHandler] = None) -> AlertSystem:
    """Factory function to create AlertSystem with default handlers"""
    system = AlertSystem()
    
    if handlers:
        for handler in handlers:
            system.add_handler(handler)
    else:
        # Add default console handler
        system.add_handler(ConsoleAlertHandler())
    
    return system
