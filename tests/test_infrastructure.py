"""
Test infrastructure setup and basic functionality
"""

import pytest
import tempfile
import os
from pathlib import Path

from config.config import PlayerGoldConfig, load_config
from src.utils.logging import setup_logging, get_logger


class TestInfrastructure:
    """Test basic infrastructure components"""
    
    def test_config_loading(self):
        """Test configuration loading"""
        config = PlayerGoldConfig()
        
        # Test default values
        assert config.environment == "development"
        assert config.network.p2p_port == 8333
        assert config.ai.challenge_timeout == 0.1
        assert config.blockchain.reward_distribution["ai_nodes"] == 0.9
        assert config.blockchain.fee_distribution["burn"] == 0.8
    
    def test_config_from_file(self):
        """Test loading configuration from YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
environment: "test"
debug: true
network:
  p2p_port: 9999
  api_port: 8888
ai:
  challenge_timeout: 0.2
""")
            config_file = f.name
        
        try:
            config = load_config(config_file)
            assert config.environment == "test"
            assert config.debug == True
            assert config.network.p2p_port == 9999
            assert config.network.api_port == 8888
            assert config.ai.challenge_timeout == 0.2
        finally:
            os.unlink(config_file)
    
    def test_logging_setup(self):
        """Test logging system setup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            # Setup logging
            logger_instance = setup_logging(log_level="DEBUG", log_file=log_file)
            assert logger_instance is not None
            
            # Get logger and test logging
            logger = get_logger("test")
            logger.info("Test message", test_param="test_value")
            
            # Verify log file was created
            assert Path(log_file).exists()
            
            # Close logging handlers to release file locks on Windows
            import logging
            for handler in logging.getLogger().handlers[:]:
                handler.close()
                logging.getLogger().removeHandler(handler)
    
    def test_directory_structure(self):
        """Test that all required directories exist"""
        required_dirs = [
            "src",
            "src/blockchain",
            "src/ai_nodes", 
            "src/wallet",
            "src/p2p",
            "src/api",
            "src/utils",
            "config",
            "tests",
            "web"
        ]
        
        for dir_path in required_dirs:
            assert Path(dir_path).exists(), f"Directory {dir_path} should exist"
            assert Path(dir_path).is_dir(), f"{dir_path} should be a directory"
    
    def test_package_imports(self):
        """Test that all packages can be imported"""
        # Test configuration import
        from config.config import PlayerGoldConfig, get_config
        
        # Test logging import
        from src.utils.logging import setup_logging, get_logger
        
        # Test package imports
        import src.blockchain
        import src.ai_nodes
        import src.wallet
        import src.p2p
        import src.api
        import src.utils
        
        # All imports should succeed without errors
        assert True
    
    def test_requirements_file(self):
        """Test that requirements.txt exists and has required dependencies"""
        requirements_file = Path("requirements.txt")
        assert requirements_file.exists(), "requirements.txt should exist"
        
        content = requirements_file.read_text()
        
        # Check for key dependencies
        required_deps = [
            "torch",
            "transformers", 
            "cryptography",
            "fastapi",
            "structlog",
            "pydantic",
            "pyyaml"
        ]
        
        for dep in required_deps:
            assert dep in content, f"Dependency {dep} should be in requirements.txt"
    
    def test_config_environment_variables(self):
        """Test configuration with environment variables"""
        # Set environment variables
        os.environ["ENVIRONMENT"] = "test_env"
        os.environ["NETWORK__P2P_PORT"] = "7777"
        os.environ["DEBUG"] = "true"
        
        try:
            config = PlayerGoldConfig()
            assert config.environment == "test_env"
            assert config.network.p2p_port == 7777
            assert config.debug == True
        finally:
            # Clean up environment variables
            del os.environ["ENVIRONMENT"]
            del os.environ["NETWORK__P2P_PORT"] 
            del os.environ["DEBUG"]