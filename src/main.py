"""
PlayerGold Main Application Entry Point
Initializes the distributed AI nodes architecture
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

from config.config import get_config, PlayerGoldConfig
from src.utils.logging import setup_logging, get_logger


class PlayerGoldApp:
    """Main application class for PlayerGold"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Load configuration
        self.config = get_config()
        
        # Setup logging
        setup_logging(
            log_level=self.config.logging.log_level,
            log_file=self.config.logging.log_file
        )
        
        self.logger = get_logger("main")
        self.running = False
        
        # Initialize components (will be implemented in later tasks)
        self.blockchain = None
        self.ai_node = None
        self.p2p_network = None
        self.api_server = None
        
    async def start(self):
        """Start the PlayerGold application"""
        self.logger.info("Starting PlayerGold application", 
                        environment=self.config.environment,
                        debug=self.config.debug)
        
        try:
            # Create necessary directories
            self._create_directories()
            
            # Initialize components (placeholders for now)
            await self._initialize_components()
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            self.running = True
            self.logger.info("PlayerGold application started successfully")
            
            # Main application loop
            await self._run_main_loop()
            
        except Exception as e:
            self.logger.error("Failed to start PlayerGold application", error=str(e))
            raise
    
    async def stop(self):
        """Stop the PlayerGold application"""
        self.logger.info("Stopping PlayerGold application")
        self.running = False
        
        # Cleanup components (will be implemented in later tasks)
        await self._cleanup_components()
        
        self.logger.info("PlayerGold application stopped")
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.config.blockchain.data_dir,
            self.config.wallet.wallet_dir,
            self.config.ai.models_dir,
            Path(self.config.logging.log_file).parent if self.config.logging.log_file else None
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
                self.logger.debug("Created directory", path=str(directory))
    
    async def _initialize_components(self):
        """Initialize application components"""
        self.logger.info("Initializing components")
        
        # TODO: Initialize blockchain core (Task 4)
        # self.blockchain = BlockchainCore(self.config.blockchain)
        
        # TODO: Initialize AI node (Task 2)
        # self.ai_node = AINode(self.config.ai)
        
        # TODO: Initialize P2P network (Task 5)
        # self.p2p_network = P2PNetwork(self.config.network)
        
        # TODO: Initialize API server (Task 9)
        # self.api_server = APIServer(self.config.network)
        
        self.logger.info("Components initialized (placeholders)")
    
    async def _cleanup_components(self):
        """Cleanup application components"""
        self.logger.info("Cleaning up components")
        
        # TODO: Cleanup components in reverse order
        # if self.api_server:
        #     await self.api_server.stop()
        # if self.p2p_network:
        #     await self.p2p_network.stop()
        # if self.ai_node:
        #     await self.ai_node.stop()
        # if self.blockchain:
        #     await self.blockchain.stop()
        
        self.logger.info("Components cleaned up")
    
    async def _run_main_loop(self):
        """Main application loop"""
        self.logger.info("Entering main application loop")
        
        while self.running:
            try:
                # Main application logic will be implemented in later tasks
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                self.logger.info("Main loop cancelled")
                break
            except Exception as e:
                self.logger.error("Error in main loop", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info("Received signal", signal=signum)
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    app = PlayerGoldApp()
    
    try:
        await app.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Application failed: {e}")
        sys.exit(1)
    finally:
        await app.stop()


if __name__ == "__main__":
    # Check if CLI arguments are provided
    if len(sys.argv) > 1:
        from src.cli import cli
        cli()
    else:
        asyncio.run(main())