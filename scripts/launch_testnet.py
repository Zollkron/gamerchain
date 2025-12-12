#!/usr/bin/env python3
"""
PlayerGold Testnet Launcher

Easy launcher for starting multiple testnet nodes for development and testing.
Creates the initial 2 pioneer nodes needed for genesis block creation.

Usage:
    python scripts/launch_testnet.py [--nodes N] [--start-port PORT]
"""

import asyncio
import sys
import logging
import argparse
import subprocess
import time
import signal
import os
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestnetLauncher:
    """
    Launcher for PlayerGold testnet nodes
    """
    
    def __init__(self, num_nodes: int = 2, start_port: int = 18080):
        self.num_nodes = num_nodes
        self.start_port = start_port
        self.processes: List[subprocess.Popen] = []
        self.running = False
        
        logger.info(f"Testnet Launcher initialized")
        logger.info(f"Nodes to launch: {num_nodes}")
        logger.info(f"Starting port: {start_port}")
    
    def launch_nodes(self):
        """Launch all testnet nodes"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 LAUNCHING PLAYERGOLD TESTNET")
            logger.info("=" * 60)
            
            script_path = Path(__file__).parent / "start_multinode_network.py"
            
            for i in range(self.num_nodes):
                node_id = f"testnet_pioneer_{i+1}"
                port = self.start_port + i
                
                logger.info(f"🚀 Launching node {i+1}/{self.num_nodes}: {node_id}")
                logger.info(f"   P2P Port: {port}")
                logger.info(f"   API Port: {port + 1000}")
                
                # Launch node process
                cmd = [
                    sys.executable,
                    str(script_path),
                    "--node-id", node_id,
                    "--port", str(port),
                    "--network", "testnet",
                    "--log-level", "INFO"
                ]
                
                # Add bootstrap nodes for peer discovery
                if i == 0:
                    # First node connects to second node
                    cmd.extend(["--bootstrap", f"127.0.0.1:{self.start_port + 1}"])
                else:
                    # Second node connects to first node
                    cmd.extend(["--bootstrap", f"127.0.0.1:{self.start_port}"])
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                self.processes.append(process)
                
                # Small delay between launches
                time.sleep(2)
            
            self.running = True
            
            logger.info("✅ All nodes launched successfully!")
            logger.info("=" * 60)
            logger.info("📊 TESTNET INFORMATION")
            logger.info("=" * 60)
            
            for i in range(self.num_nodes):
                node_id = f"testnet_pioneer_{i+1}"
                port = self.start_port + i
                api_port = port + 1000
                
                logger.info(f"Node {i+1}: {node_id}")
                logger.info(f"  P2P: 127.0.0.1:{port}")
                logger.info(f"  API: http://127.0.0.1:{api_port}")
                logger.info(f"  Health: http://127.0.0.1:{api_port}/api/v1/health")
                logger.info(f"  Status: http://127.0.0.1:{api_port}/api/v1/network/status")
                logger.info("")
            
            logger.info("🏗️  Genesis block will be created automatically when 2 pioneer nodes connect")
            logger.info("⏳ Monitor the logs to see genesis block creation...")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Error launching nodes: {e}")
            self.stop_all_nodes()
            raise
    
    def monitor_nodes(self):
        """Monitor running nodes and display their output"""
        try:
            while self.running and any(p.poll() is None for p in self.processes):
                for i, process in enumerate(self.processes):
                    if process.poll() is None:  # Process is still running
                        # Read output line by line
                        try:
                            line = process.stdout.readline()
                            if line:
                                node_id = f"testnet_pioneer_{i+1}"
                                print(f"[{node_id}] {line.strip()}")
                        except:
                            pass
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping nodes...")
            self.stop_all_nodes()
    
    def stop_all_nodes(self):
        """Stop all running nodes"""
        logger.info("🛑 Stopping all testnet nodes...")
        
        self.running = False
        
        for i, process in enumerate(self.processes):
            if process.poll() is None:  # Process is still running
                node_id = f"testnet_pioneer_{i+1}"
                logger.info(f"Stopping {node_id}...")
                
                try:
                    process.terminate()
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {node_id}...")
                    process.kill()
                    process.wait()
                except Exception as e:
                    logger.error(f"Error stopping {node_id}: {e}")
        
        self.processes.clear()
        logger.info("✅ All nodes stopped")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down testnet...")
        self.stop_all_nodes()
        sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PlayerGold Testnet Launcher')
    parser.add_argument('--nodes', type=int, default=2, help='Number of nodes to launch (default: 2)')
    parser.add_argument('--start-port', type=int, default=18080, help='Starting P2P port (default: 18080)')
    
    args = parser.parse_args()
    
    if args.nodes < 2:
        logger.error("❌ Minimum 2 nodes required for genesis block creation")
        sys.exit(1)
    
    # Create launcher
    launcher = TestnetLauncher(
        num_nodes=args.nodes,
        start_port=args.start_port
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, launcher.handle_signal)
    signal.signal(signal.SIGTERM, launcher.handle_signal)
    
    try:
        # Launch nodes
        launcher.launch_nodes()
        
        # Monitor nodes
        launcher.monitor_nodes()
        
    except KeyboardInterrupt:
        logger.info("Testnet launcher interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        launcher.stop_all_nodes()


if __name__ == "__main__":
    main()