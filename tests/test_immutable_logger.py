"""
Tests for Immutable Logger
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from src.monitoring.immutable_logger import (
    ImmutableLogger, LogLevel, LogCategory,
    PatternAnalyzer, create_immutable_logger
)


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def logger(temp_log_dir):
    return ImmutableLogger(temp_log_dir)


def test_create_log_entry(logger):
    """Test creating a log entry"""
    entry = logger.info(
        LogCategory.CONSENSUS,
        "Test log message",
        {'key': 'value'}
    )
    
    assert entry.log_id == 1
    assert entry.level == LogLevel.INFO
    assert entry.category == LogCategory.CONSENSUS
    assert entry.message == "Test log message"
    assert entry.data['key'] == 'value'
    assert entry.hash != ""
    assert entry.previous_hash == "0" * 64  # First entry


def test_log_chain_integrity(logger):
    """Test that log chain maintains integrity"""
    entry1 = logger.info(LogCategory.SYSTEM, "First log")
    entry2 = logger.info(LogCategory.SYSTEM, "Second log")
    entry3 = logger.info(LogCategory.SYSTEM, "Third log")
    
    # Check chain linkage
    assert entry2.previous_hash == entry1.hash
    assert entry3.previous_hash == entry2.hash
    
    # Verify integrity
    assert logger.verify_integrity()


def test_verify_integrity_detects_tampering(logger):
    """Test that integrity verification detects tampering"""
    logger.info(LogCategory.SYSTEM, "Log 1")
    logger.info(LogCategory.SYSTEM, "Log 2")
    logger.info(LogCategory.SYSTEM, "Log 3")
    
    # Tamper with a log entry
    logger.log_chain[1].message = "Tampered message"
    
    # Integrity check should fail
    assert not logger.verify_integrity()


def test_log_levels(logger):
    """Test different log levels"""
    logger.debug(LogCategory.SYSTEM, "Debug message")
    logger.info(LogCategory.SYSTEM, "Info message")
    logger.warning(LogCategory.SYSTEM, "Warning message")
    logger.error(LogCategory.SYSTEM, "Error message")
    logger.critical(LogCategory.SYSTEM, "Critical message")
    
    assert len(logger.log_chain) == 5
    assert logger.log_chain[0].level == LogLevel.DEBUG
    assert logger.log_chain[1].level == LogLevel.INFO
    assert logger.log_chain[2].level == LogLevel.WARNING
    assert logger.log_chain[3].level == LogLevel.ERROR
    assert logger.log_chain[4].level == LogLevel.CRITICAL


def test_log_categories(logger):
    """Test different log categories"""
    logger.info(LogCategory.CONSENSUS, "Consensus log")
    logger.info(LogCategory.TRANSACTION, "Transaction log")
    logger.info(LogCategory.BLOCK, "Block log")
    logger.info(LogCategory.NODE, "Node log")
    
    assert len(logger.log_chain) == 4
    assert logger.log_chain[0].category == LogCategory.CONSENSUS
    assert logger.log_chain[1].category == LogCategory.TRANSACTION


def test_get_logs_by_category(logger):
    """Test filtering logs by category"""
    logger.info(LogCategory.CONSENSUS, "Consensus 1")
    logger.info(LogCategory.TRANSACTION, "Transaction 1")
    logger.info(LogCategory.CONSENSUS, "Consensus 2")
    
    consensus_logs = logger.get_logs(category=LogCategory.CONSENSUS)
    assert len(consensus_logs) == 2
    assert all(l.category == LogCategory.CONSENSUS for l in consensus_logs)


def test_get_logs_by_level(logger):
    """Test filtering logs by level"""
    logger.info(LogCategory.SYSTEM, "Info 1")
    logger.error(LogCategory.SYSTEM, "Error 1")
    logger.info(LogCategory.SYSTEM, "Info 2")
    logger.error(LogCategory.SYSTEM, "Error 2")
    
    errors = logger.get_logs(level=LogLevel.ERROR)
    assert len(errors) == 2
    assert all(l.level == LogLevel.ERROR for l in errors)


def test_get_logs_by_time_range(logger):
    """Test filtering logs by time range"""
    start_time = time.time()
    
    logger.info(LogCategory.SYSTEM, "Log 1")
    time.sleep(0.1)
    mid_time = time.time()
    time.sleep(0.1)
    logger.info(LogCategory.SYSTEM, "Log 2")
    
    end_time = time.time()
    
    # Get logs after mid_time
    recent_logs = logger.get_logs(start_time=mid_time)
    assert len(recent_logs) == 1
    assert recent_logs[0].message == "Log 2"


def test_get_logs_with_limit(logger):
    """Test limiting number of returned logs"""
    for i in range(10):
        logger.info(LogCategory.SYSTEM, f"Log {i}")
    
    limited = logger.get_logs(limit=5)
    assert len(limited) == 5
    # Should return last 5
    assert limited[-1].message == "Log 9"


def test_get_recent_logs(logger):
    """Test getting recent logs"""
    logger.info(LogCategory.SYSTEM, "Recent log")
    
    recent = logger.get_recent_logs(hours=1)
    assert len(recent) == 1


def test_get_critical_logs(logger):
    """Test getting critical logs"""
    logger.info(LogCategory.SYSTEM, "Info log")
    logger.critical(LogCategory.SECURITY, "Critical log 1")
    logger.error(LogCategory.SYSTEM, "Error log")
    logger.critical(LogCategory.SECURITY, "Critical log 2")
    
    critical = logger.get_critical_logs(hours=1)
    assert len(critical) == 2
    assert all(l.level == LogLevel.CRITICAL for l in critical)


def test_search_logs(logger):
    """Test searching logs by message"""
    logger.info(LogCategory.SYSTEM, "Node validation successful")
    logger.info(LogCategory.SYSTEM, "Transaction processed")
    logger.info(LogCategory.SYSTEM, "Node connection failed")
    
    results = logger.search_logs("node")
    assert len(results) == 2
    assert "Node" in results[0].message or "node" in results[0].message


def test_get_statistics(logger):
    """Test getting log statistics"""
    logger.info(LogCategory.SYSTEM, "Info 1")
    logger.error(LogCategory.SECURITY, "Error 1")
    logger.warning(LogCategory.CONSENSUS, "Warning 1")
    logger.critical(LogCategory.SECURITY, "Critical 1")
    
    stats = logger.get_statistics()
    
    assert stats['total_logs'] == 4
    assert stats['by_level'][LogLevel.INFO.value] == 1
    assert stats['by_level'][LogLevel.ERROR.value] == 1
    assert stats['by_category'][LogCategory.SECURITY.value] == 2
    assert stats['integrity_verified'] == True


def test_export_logs(logger, temp_log_dir):
    """Test exporting logs to file"""
    logger.info(LogCategory.SYSTEM, "Log 1")
    logger.info(LogCategory.SYSTEM, "Log 2")
    logger.info(LogCategory.CONSENSUS, "Log 3")
    
    export_path = Path(temp_log_dir) / "export.log"
    logger.export_logs(str(export_path), category=LogCategory.SYSTEM)
    
    # Read exported file
    with open(export_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2  # Only SYSTEM category


def test_persistence(temp_log_dir):
    """Test that logs persist across logger instances"""
    # Create logger and add logs
    logger1 = ImmutableLogger(temp_log_dir)
    logger1.info(LogCategory.SYSTEM, "Persistent log 1")
    logger1.info(LogCategory.SYSTEM, "Persistent log 2")
    
    # Create new logger instance with same directory
    logger2 = ImmutableLogger(temp_log_dir)
    
    # Should load existing logs
    assert len(logger2.log_chain) == 2
    assert logger2.log_chain[0].message == "Persistent log 1"
    assert logger2.verify_integrity()


def test_pattern_analyzer_error_patterns(logger):
    """Test analyzing error patterns"""
    logger.error(LogCategory.CONSENSUS, "Consensus failed")
    logger.error(LogCategory.CONSENSUS, "Consensus failed")
    logger.error(LogCategory.NETWORK, "Network timeout")
    logger.info(LogCategory.SYSTEM, "Normal operation")
    
    analyzer = PatternAnalyzer(logger)
    patterns = analyzer.analyze_error_patterns(hours=1)
    
    assert patterns['total_errors'] == 3
    assert patterns['by_category'][LogCategory.CONSENSUS.value] == 2
    assert "Consensus failed" in patterns['repeated_messages']
    assert patterns['repeated_messages']["Consensus failed"] == 2


def test_pattern_analyzer_anomalous_activity(logger):
    """Test detecting anomalous activity"""
    # Create burst of logs
    for i in range(150):
        logger.info(LogCategory.SYSTEM, f"Burst log {i}")
    
    analyzer = PatternAnalyzer(logger)
    anomalies = analyzer.detect_anomalous_activity(threshold=100)
    
    assert len(anomalies) > 0
    assert anomalies[0]['log_count'] > 100


def test_pattern_analyzer_node_behavior(logger):
    """Test analyzing node behavior"""
    node_id = "node123"
    
    logger.info(LogCategory.NODE, f"Node {node_id} started", {'node_id': node_id})
    logger.error(LogCategory.NODE, f"Node {node_id} validation failed", {'node_id': node_id})
    logger.warning(LogCategory.NODE, f"Node {node_id} slow response", {'node_id': node_id})
    logger.info(LogCategory.SYSTEM, "Other log")
    
    analyzer = PatternAnalyzer(logger)
    behavior = analyzer.analyze_node_behavior(node_id, hours=1)
    
    assert behavior['node_id'] == node_id
    assert behavior['total_logs'] == 3
    assert behavior['errors'] == 1
    assert behavior['warnings'] == 1


def test_create_immutable_logger_factory(temp_log_dir):
    """Test factory function"""
    logger = create_immutable_logger(temp_log_dir)
    assert isinstance(logger, ImmutableLogger)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
