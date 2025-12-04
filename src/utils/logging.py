"""
Centralized logging system for PlayerGold
Provides structured logging with different levels and outputs
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import structlog
from structlog.stdlib import LoggerFactory


class PlayerGoldLogger:
    """Centralized logging configuration for PlayerGold"""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.log_level = log_level.upper()
        self.log_file = log_file
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure structured logging with appropriate processors"""
        
        # Configure structlog processors
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]
        
        # Add JSON formatter for file output, console formatter for terminal
        if self.log_file:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer(colors=True))
        
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, self.log_level),
        )
        
        # Add file handler if specified
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(getattr(logging, self.log_level))
            
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
    
    @staticmethod
    def get_logger(name: str) -> structlog.BoundLogger:
        """Get a logger instance for a specific module"""
        return structlog.get_logger(name)


# Global logger instance
_logger_instance: Optional[PlayerGoldLogger] = None


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> PlayerGoldLogger:
    """Setup global logging configuration"""
    global _logger_instance
    _logger_instance = PlayerGoldLogger(log_level, log_file)
    return _logger_instance


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger for the specified module"""
    if _logger_instance is None:
        setup_logging()
    return PlayerGoldLogger.get_logger(name)


# Module-specific loggers
blockchain_logger = get_logger("blockchain")
ai_nodes_logger = get_logger("ai_nodes")
p2p_logger = get_logger("p2p")
wallet_logger = get_logger("wallet")
api_logger = get_logger("api")