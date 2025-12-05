"""
Immutable Logging System for PlayerGold
All critical operations are logged with cryptographic verification
"""

import hashlib
import json
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import threading
from pathlib import Path


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(Enum):
    """Categories of logs"""
    CONSENSUS = "consensus"
    TRANSACTION = "transaction"
    BLOCK = "block"
    NODE = "node"
    NETWORK = "network"
    SECURITY = "security"
    REPUTATION = "reputation"
    SYSTEM = "system"


@dataclass
class LogEntry:
    """Immutable log entry"""
    log_id: int
    timestamp: float
    level: LogLevel
    category: LogCategory
    message: str
    data: Dict
    previous_hash: str
    hash: str
    
    def calculate_hash(self) -> str:
        """Calculate hash of this log entry"""
        content = {
            'log_id': self.log_id,
            'timestamp': self.timestamp,
            'level': self.level.value,
            'category': self.category.value,
            'message': self.message,
            'data': self.data,
            'previous_hash': self.previous_hash
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()


class ImmutableLogger:
    """
    Immutable logging system with cryptographic chain
    Each log entry is linked to the previous one via hash
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.log_chain: List[LogEntry] = []
        self.log_counter = 0
        self.lock = threading.Lock()
        
        # Separate files for different categories
        self.log_files = {}
        for category in LogCategory:
            filepath = self.log_dir / f"{category.value}.log"
            self.log_files[category] = filepath
        
        # Master log file with all entries
        self.master_log = self.log_dir / "master.log"
        
        # Load existing logs
        self._load_existing_logs()
    
    def _load_existing_logs(self):
        """Load existing logs from master log file"""
        if not self.master_log.exists():
            return
        
        try:
            with open(self.master_log, 'r') as f:
                for line in f:
                    if line.strip():
                        entry_data = json.loads(line)
                        entry = LogEntry(
                            log_id=entry_data['log_id'],
                            timestamp=entry_data['timestamp'],
                            level=LogLevel(entry_data['level']),
                            category=LogCategory(entry_data['category']),
                            message=entry_data['message'],
                            data=entry_data['data'],
                            previous_hash=entry_data['previous_hash'],
                            hash=entry_data['hash']
                        )
                        self.log_chain.append(entry)
                        self.log_counter = max(self.log_counter, entry.log_id)
        except Exception as e:
            print(f"Error loading existing logs: {e}")
    
    def log(self, level: LogLevel, category: LogCategory, 
            message: str, data: Dict = None) -> LogEntry:
        """Create an immutable log entry"""
        with self.lock:
            self.log_counter += 1
            
            # Get previous hash
            previous_hash = self.log_chain[-1].hash if self.log_chain else "0" * 64
            
            # Create entry
            entry = LogEntry(
                log_id=self.log_counter,
                timestamp=time.time(),
                level=level,
                category=category,
                message=message,
                data=data or {},
                previous_hash=previous_hash,
                hash=""  # Will be calculated
            )
            
            # Calculate hash
            entry.hash = entry.calculate_hash()
            
            # Add to chain
            self.log_chain.append(entry)
            
            # Write to files
            self._write_to_files(entry)
            
            return entry
    
    def _write_to_files(self, entry: LogEntry):
        """Write log entry to files"""
        entry_dict = asdict(entry)
        entry_dict['level'] = entry.level.value
        entry_dict['category'] = entry.category.value
        entry_json = json.dumps(entry_dict)
        
        # Write to master log
        with open(self.master_log, 'a') as f:
            f.write(entry_json + '\n')
        
        # Write to category-specific log
        category_file = self.log_files[entry.category]
        with open(category_file, 'a') as f:
            f.write(entry_json + '\n')
    
    def debug(self, category: LogCategory, message: str, data: Dict = None):
        """Log debug message"""
        return self.log(LogLevel.DEBUG, category, message, data)
    
    def info(self, category: LogCategory, message: str, data: Dict = None):
        """Log info message"""
        return self.log(LogLevel.INFO, category, message, data)
    
    def warning(self, category: LogCategory, message: str, data: Dict = None):
        """Log warning message"""
        return self.log(LogLevel.WARNING, category, message, data)
    
    def error(self, category: LogCategory, message: str, data: Dict = None):
        """Log error message"""
        return self.log(LogLevel.ERROR, category, message, data)
    
    def critical(self, category: LogCategory, message: str, data: Dict = None):
        """Log critical message"""
        return self.log(LogLevel.CRITICAL, category, message, data)
    
    def verify_integrity(self) -> bool:
        """Verify the integrity of the log chain"""
        if not self.log_chain:
            return True
        
        # Check first entry
        if self.log_chain[0].previous_hash != "0" * 64:
            return False
        
        # Check each entry's hash
        for i, entry in enumerate(self.log_chain):
            # Verify hash is correct
            if entry.hash != entry.calculate_hash():
                print(f"Hash mismatch at log {entry.log_id}")
                return False
            
            # Verify chain linkage
            if i > 0:
                if entry.previous_hash != self.log_chain[i-1].hash:
                    print(f"Chain broken at log {entry.log_id}")
                    return False
        
        return True
    
    def get_logs(self, category: Optional[LogCategory] = None,
                 level: Optional[LogLevel] = None,
                 start_time: Optional[float] = None,
                 end_time: Optional[float] = None,
                 limit: Optional[int] = None) -> List[LogEntry]:
        """Query logs with filters"""
        logs = self.log_chain.copy()
        
        if category:
            logs = [l for l in logs if l.category == category]
        
        if level:
            logs = [l for l in logs if l.level == level]
        
        if start_time:
            logs = [l for l in logs if l.timestamp >= start_time]
        
        if end_time:
            logs = [l for l in logs if l.timestamp <= end_time]
        
        if limit:
            logs = logs[-limit:]
        
        return logs
    
    def get_recent_logs(self, hours: int = 24, 
                       category: Optional[LogCategory] = None) -> List[LogEntry]:
        """Get logs from the last N hours"""
        cutoff = time.time() - (hours * 3600)
        return self.get_logs(category=category, start_time=cutoff)
    
    def get_critical_logs(self, hours: int = 24) -> List[LogEntry]:
        """Get critical logs from the last N hours"""
        cutoff = time.time() - (hours * 3600)
        return self.get_logs(level=LogLevel.CRITICAL, start_time=cutoff)
    
    def search_logs(self, query: str, category: Optional[LogCategory] = None) -> List[LogEntry]:
        """Search logs by message content"""
        logs = self.log_chain if not category else [l for l in self.log_chain if l.category == category]
        return [l for l in logs if query.lower() in l.message.lower()]
    
    def get_statistics(self) -> Dict:
        """Get logging statistics"""
        total = len(self.log_chain)
        
        by_level = {}
        for level in LogLevel:
            by_level[level.value] = len([l for l in self.log_chain if l.level == level])
        
        by_category = {}
        for category in LogCategory:
            by_category[category.value] = len([l for l in self.log_chain if l.category == category])
        
        # Recent activity (last hour)
        one_hour_ago = time.time() - 3600
        recent = len([l for l in self.log_chain if l.timestamp >= one_hour_ago])
        
        return {
            'total_logs': total,
            'by_level': by_level,
            'by_category': by_category,
            'recent_hour': recent,
            'integrity_verified': self.verify_integrity()
        }
    
    def export_logs(self, filepath: str, category: Optional[LogCategory] = None,
                   start_time: Optional[float] = None, end_time: Optional[float] = None):
        """Export logs to a file"""
        logs = self.get_logs(category=category, start_time=start_time, end_time=end_time)
        
        with open(filepath, 'w') as f:
            for entry in logs:
                entry_dict = asdict(entry)
                entry_dict['level'] = entry.level.value
                entry_dict['category'] = entry.category.value
                f.write(json.dumps(entry_dict) + '\n')


class PatternAnalyzer:
    """Analyzes log patterns to detect unusual behavior"""
    
    def __init__(self, logger: ImmutableLogger):
        self.logger = logger
    
    def analyze_error_patterns(self, hours: int = 24) -> Dict:
        """Analyze error patterns in recent logs"""
        errors = self.logger.get_logs(
            level=LogLevel.ERROR,
            start_time=time.time() - (hours * 3600)
        )
        
        # Count by category
        by_category = {}
        for error in errors:
            cat = error.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        
        # Find repeated messages
        message_counts = {}
        for error in errors:
            msg = error.message
            message_counts[msg] = message_counts.get(msg, 0) + 1
        
        repeated = {msg: count for msg, count in message_counts.items() if count > 1}
        
        return {
            'total_errors': len(errors),
            'by_category': by_category,
            'repeated_messages': repeated,
            'time_range_hours': hours
        }
    
    def detect_anomalous_activity(self, threshold: int = 100) -> List[Dict]:
        """Detect periods of anomalously high activity"""
        anomalies = []
        
        # Group logs by 5-minute windows
        window_size = 300  # 5 minutes
        current_time = time.time()
        
        for i in range(24):  # Last 24 hours
            window_start = current_time - ((i + 1) * window_size)
            window_end = current_time - (i * window_size)
            
            logs_in_window = self.logger.get_logs(
                start_time=window_start,
                end_time=window_end
            )
            
            if len(logs_in_window) > threshold:
                anomalies.append({
                    'window_start': window_start,
                    'window_end': window_end,
                    'log_count': len(logs_in_window),
                    'threshold': threshold
                })
        
        return anomalies
    
    def analyze_node_behavior(self, node_id: str, hours: int = 24) -> Dict:
        """Analyze behavior of a specific node"""
        cutoff = time.time() - (hours * 3600)
        
        # Find all logs mentioning this node
        node_logs = [l for l in self.logger.log_chain 
                    if l.timestamp >= cutoff and 
                    (node_id in l.message or 
                     l.data.get('node_id') == node_id)]
        
        errors = [l for l in node_logs if l.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        warnings = [l for l in node_logs if l.level == LogLevel.WARNING]
        
        return {
            'node_id': node_id,
            'total_logs': len(node_logs),
            'errors': len(errors),
            'warnings': len(warnings),
            'error_rate': len(errors) / len(node_logs) if node_logs else 0,
            'recent_errors': [l.message for l in errors[-5:]]
        }


def create_immutable_logger(log_dir: str = "logs") -> ImmutableLogger:
    """Factory function to create ImmutableLogger"""
    return ImmutableLogger(log_dir)
