"""
Tests for Alert System
"""

import pytest
import time
from src.monitoring.alert_system import (
    AlertSystem, AlertType, AlertSeverity,
    ConsoleAlertHandler, FileAlertHandler,
    AnomalyDetector, create_alert_system
)
import tempfile
import os


@pytest.fixture
def alert_system():
    return AlertSystem()


@pytest.fixture
def anomaly_detector():
    return AnomalyDetector(window_size=20)


def test_create_alert(alert_system):
    """Test creating an alert"""
    alert = alert_system.create_alert(
        AlertType.HIGH_LATENCY,
        AlertSeverity.WARNING,
        "Test alert message",
        {'latency': 2500}
    )
    
    assert alert.alert_type == AlertType.HIGH_LATENCY
    assert alert.severity == AlertSeverity.WARNING
    assert alert.message == "Test alert message"
    assert alert.details['latency'] == 2500
    assert not alert.resolved
    assert alert.alert_id.startswith("ALERT-")


def test_resolve_alert(alert_system):
    """Test resolving an alert"""
    alert = alert_system.create_alert(
        AlertType.NODE_FAILURE,
        AlertSeverity.CRITICAL,
        "Node failed"
    )
    
    assert not alert.resolved
    
    success = alert_system.resolve_alert(alert.alert_id)
    assert success
    assert alert.resolved
    assert alert.resolved_at is not None


def test_get_active_alerts(alert_system):
    """Test getting active alerts"""
    alert1 = alert_system.create_alert(
        AlertType.HIGH_LATENCY,
        AlertSeverity.WARNING,
        "Alert 1"
    )
    
    alert2 = alert_system.create_alert(
        AlertType.LOW_TPS,
        AlertSeverity.ERROR,
        "Alert 2"
    )
    
    active = alert_system.get_active_alerts()
    assert len(active) == 2
    
    # Resolve one
    alert_system.resolve_alert(alert1.alert_id)
    
    active = alert_system.get_active_alerts()
    assert len(active) == 1
    assert active[0].alert_id == alert2.alert_id


def test_get_active_alerts_by_severity(alert_system):
    """Test filtering active alerts by severity"""
    alert_system.create_alert(
        AlertType.HIGH_LATENCY,
        AlertSeverity.WARNING,
        "Warning alert"
    )
    
    alert_system.create_alert(
        AlertType.NODE_FAILURE,
        AlertSeverity.CRITICAL,
        "Critical alert"
    )
    
    warnings = alert_system.get_active_alerts(AlertSeverity.WARNING)
    assert len(warnings) == 1
    assert warnings[0].severity == AlertSeverity.WARNING
    
    critical = alert_system.get_active_alerts(AlertSeverity.CRITICAL)
    assert len(critical) == 1
    assert critical[0].severity == AlertSeverity.CRITICAL


def test_get_recent_alerts(alert_system):
    """Test getting recent alerts"""
    alert_system.create_alert(
        AlertType.HIGH_LATENCY,
        AlertSeverity.WARNING,
        "Recent alert"
    )
    
    recent = alert_system.get_recent_alerts(hours=1)
    assert len(recent) == 1


def test_console_alert_handler(alert_system, capsys):
    """Test console alert handler"""
    handler = ConsoleAlertHandler()
    alert_system.add_handler(handler)
    
    alert_system.create_alert(
        AlertType.HIGH_LATENCY,
        AlertSeverity.WARNING,
        "Test console alert"
    )
    
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "Test console alert" in captured.out


def test_file_alert_handler(alert_system):
    """Test file alert handler"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        filepath = f.name
    
    try:
        handler = FileAlertHandler(filepath)
        alert_system.add_handler(handler)
        
        alert_system.create_alert(
            AlertType.NODE_FAILURE,
            AlertSeverity.CRITICAL,
            "Test file alert"
        )
        
        # Read the file
        with open(filepath, 'r') as f:
            content = f.read()
            assert "Test file alert" in content
            assert "node_failure" in content
    finally:
        os.unlink(filepath)


def test_anomaly_detector_tps(anomaly_detector):
    """Test TPS anomaly detection"""
    # Add normal samples
    for i in range(15):
        anomaly_detector.add_sample(tps=100.0, latency=50, node_count=10)
    
    # No anomaly yet
    anomaly = anomaly_detector.detect_tps_anomaly()
    assert anomaly is None
    
    # Add anomalous sample
    anomaly_detector.add_sample(tps=500.0, latency=50, node_count=10)
    
    anomaly = anomaly_detector.detect_tps_anomaly()
    assert anomaly is not None
    assert anomaly['current'] == 500.0
    assert anomaly['deviation'] > 2.0


def test_anomaly_detector_latency(anomaly_detector):
    """Test latency anomaly detection"""
    # Add normal samples
    for i in range(10):
        anomaly_detector.add_sample(tps=100.0, latency=50, node_count=10)
    
    # No anomaly
    anomaly = anomaly_detector.detect_latency_anomaly(threshold_ms=2000)
    assert anomaly is None
    
    # Add high latency
    anomaly_detector.add_sample(tps=100.0, latency=3000, node_count=10)
    
    anomaly = anomaly_detector.detect_latency_anomaly(threshold_ms=2000)
    assert anomaly is not None
    assert anomaly['current'] == 3000
    assert anomaly['threshold'] == 2000


def test_anomaly_detector_node_failure(anomaly_detector):
    """Test node failure detection"""
    # Add samples with 10 nodes
    for i in range(15):
        anomaly_detector.add_sample(tps=100.0, latency=50, node_count=10)
    
    # No failure
    failure = anomaly_detector.detect_node_failure(threshold_drop=0.3)
    assert failure is None
    
    # Drop to 5 nodes (50% drop)
    anomaly_detector.add_sample(tps=100.0, latency=50, node_count=5)
    
    failure = anomaly_detector.detect_node_failure(threshold_drop=0.3)
    assert failure is not None
    assert failure['current'] == 5
    assert failure['drop_percentage'] > 30


def test_check_network_health(alert_system):
    """Test network health checking"""
    metrics = {
        'tps': 5,  # Below threshold
        'latency': 2500,  # Above threshold
        'active_nodes': 10
    }
    
    alert_system.check_network_health(metrics)
    
    active = alert_system.get_active_alerts()
    assert len(active) >= 2  # Should have low TPS and high latency alerts
    
    # Check alert types
    alert_types = [a.alert_type for a in active]
    assert AlertType.LOW_TPS in alert_types
    assert AlertType.HIGH_LATENCY in alert_types


def test_check_node_behavior(alert_system):
    """Test node behavior checking"""
    behavior_data = {
        'invalid_hash': True,
        'expected_hash': 'abc123',
        'actual_hash': 'def456'
    }
    
    alert_system.check_node_behavior('node1', behavior_data)
    
    active = alert_system.get_active_alerts()
    assert len(active) == 1
    assert active[0].alert_type == AlertType.INVALID_MODEL_HASH


def test_check_consensus_health(alert_system):
    """Test consensus health checking"""
    consensus_data = {
        'failed': True,
        'reason': 'Insufficient validators'
    }
    
    alert_system.check_consensus_health(consensus_data)
    
    active = alert_system.get_active_alerts()
    assert len(active) == 1
    assert active[0].alert_type == AlertType.CONSENSUS_FAILURE
    assert active[0].severity == AlertSeverity.CRITICAL


def test_get_statistics(alert_system):
    """Test getting alert statistics"""
    alert_system.create_alert(AlertType.HIGH_LATENCY, AlertSeverity.WARNING, "Alert 1")
    alert_system.create_alert(AlertType.LOW_TPS, AlertSeverity.ERROR, "Alert 2")
    alert_system.create_alert(AlertType.NODE_FAILURE, AlertSeverity.CRITICAL, "Alert 3")
    
    stats = alert_system.get_statistics()
    
    assert stats['total_alerts'] == 3
    assert stats['active_alerts'] == 3
    assert stats['resolved_alerts'] == 0
    assert 'by_severity' in stats
    assert 'by_type' in stats


def test_create_alert_system_factory():
    """Test factory function"""
    system = create_alert_system()
    assert isinstance(system, AlertSystem)
    assert len(system.handlers) == 1  # Default console handler


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
