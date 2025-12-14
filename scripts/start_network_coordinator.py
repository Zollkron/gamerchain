#!/usr/bin/env python3
"""
Start Network Coordinator Server

This script starts the PlayerGold Network Coordinator server that maintains
a centralized registry of network nodes with distributed backup capabilities.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.network_coordinator.server import run_server

def setup_logging(debug: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/network_coordinator.log', mode='a')
        ]
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PlayerGold Network Coordinator')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--db-path', default='data/network_nodes.db', help='Database path')
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Setup logging
    setup_logging(args.debug)
    
    logger = logging.getLogger(__name__)
    
    logger.info("Starting PlayerGold Network Coordinator")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Debug: {args.debug}")
    logger.info(f"Database: {args.db_path}")
    
    try:
        # Set database path environment variable
        os.environ['NETWORK_COORDINATOR_DB_PATH'] = args.db_path
        
        # Run the server
        run_server(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        logger.info("Shutting down Network Coordinator...")
    except Exception as e:
        logger.error(f"Network Coordinator failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()