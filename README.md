# PlayerGold ($PRGLD) - Distributed AI Nodes Architecture

PlayerGold is a revolutionary gaming blockchain built on the GamerChain technology, implementing a Proof-of-AI-Participation (PoAIP) consensus mechanism. The system is designed by gamers, for gamers, providing censorship-free payments with fair commissions and democratic governance managed exclusively by artificial intelligence.

## 🎮 Vision

**"Made by gamers for gamers, totally free, democratic and without censorship"**

PlayerGold aims to eliminate human bias and corruption from blockchain governance by utilizing distributed AI nodes for consensus. This ensures fair, transparent, and ideologically neutral management of the gaming economy.

## 🏗️ Architecture Overview

### Core Components

- **AI Nodes**: Distributed nodes running certified AI models (Gemma 3 4B, Mistral 3B, Qwen 3 4B)
- **PoAIP Consensus**: Proof-of-AI-Participation ensuring only AIs can validate blocks
- **Equitable Rewards**: 90% to AI validators, 10% to stakers - no economic advantage
- **Fee Management**: 20% to liquidity pools, 80% burned to maintain token value
- **Gaming Integration**: APIs and SDKs for seamless game integration

### Key Features

- ✅ **AI-Only Consensus**: Eliminates human corruption and bias
- ✅ **Fair Distribution**: Equal rewards regardless of hardware power
- ✅ **Censorship Resistant**: No ideological restrictions on transactions
- ✅ **Gaming Focused**: Built specifically for gaming economies
- ✅ **Cross-Platform**: Desktop wallet for Windows, macOS, and Linux

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- 4GB VRAM (for AI node operation)
- 4+ CPU cores
- 8GB RAM

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/playergold/playergold.git
   cd playergold
   ```

2. **Set up the environment**
   ```bash
   make setup
   make dev-install
   ```

3. **Configure the application**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run PlayerGold**
   ```bash
   make run
   # or
   python -m src.main
   ```

### Development Commands

```bash
# Install dependencies
make install          # Production dependencies
make dev-install      # Development dependencies

# Development
make run             # Run the application
make test            # Run test suite
make lint            # Run linting checks
make format          # Format code with black
make clean           # Clean build artifacts

# Project management
make setup           # Initial project setup
make check-structure # View project structure
```

## 📁 Project Structure

```
playergold/
├── src/                    # Main source code
│   ├── blockchain/         # Blockchain core and PoAIP consensus
│   ├── ai_nodes/          # AI model management and validation
│   ├── p2p/               # Peer-to-peer networking
│   ├── wallet/            # Desktop wallet implementation
│   ├── api/               # REST/GraphQL API for games
│   ├── utils/             # Common utilities and logging
│   ├── main.py            # Application entry point
│   └── cli.py             # Command line interface
├── config/                # Configuration management
│   ├── config.py          # Configuration classes
│   └── default.yaml       # Default settings
├── tests/                 # Test suite
├── web/                   # Landing page and web interface
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
└── Makefile              # Development commands
```

## 🔧 Configuration

PlayerGold uses a hierarchical configuration system:

1. **Default values** in `config/config.py`
2. **YAML files** like `config/default.yaml`
3. **Environment variables** from `.env` file
4. **Command line arguments**

### Key Configuration Options

```yaml
# Network settings
network:
  p2p_port: 8333
  api_port: 8080
  max_peers: 50

# AI configuration
ai:
  models_dir: "./models"
  challenge_timeout: 0.1
  min_validators: 3

# Blockchain settings
blockchain:
  data_dir: "./data"
  block_time: 10
  reward_distribution:
    ai_nodes: 0.9
    stakers: 0.1
```

## 🤖 AI Models

PlayerGold supports certified AI models with verified SHA-256 hashes:

- **Gemma 3 4B**: Optimized for mathematical challenges
- **Mistral 3B**: Efficient inference and validation
- **Qwen 3 4B**: Multilingual support and robustness

### Model Verification

All AI models undergo strict verification:
1. SHA-256 hash validation against certified list
2. Capability testing for blockchain operations
3. Performance benchmarking for <100ms response time

## 🎯 Consensus Mechanism (PoAIP)

Proof-of-AI-Participation ensures only artificial intelligence can participate in consensus:

1. **Challenge Generation**: Mathematical problems requiring AI capabilities
2. **Solution Submission**: AIs solve challenges in <100ms
3. **Cross-Validation**: Minimum 3 AIs validate each solution
4. **Reward Distribution**: Equal rewards for all participating AIs

## 🛡️ Security Features

- **Model Integrity**: SHA-256 verification of AI models
- **Sandboxed Execution**: Isolated AI model execution
- **Cross-Validation**: Multiple AI verification of solutions
- **Reputation System**: Behavioral tracking and penalties
- **Network Encryption**: TLS 1.3 for all communications

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/test_infrastructure.py -v
pytest tests/test_blockchain.py -v
pytest tests/test_ai_nodes.py -v
```

## 🌐 Landing Page

PlayerGold features a modern, responsive landing page showcasing the project:

```bash
# View the landing page locally
cd web
python -m http.server 8000
# Visit http://localhost:8000
```

Features:
- **Automatic OS Detection**: Recommends the right wallet download for your system
- **Modern Design**: Dark theme with smooth animations and gradients
- **Responsive**: Optimized for desktop, tablet, and mobile
- **Mission Statement**: Clear presentation of values and goals
- **Technology Overview**: Explanation of PoAIP consensus and GamerChain

See [web/README.md](web/README.md) for deployment instructions.

## 📚 Documentation

- [Whitepaper](docs/Whitepaper.pdf) - Technical specifications
- [Technical Whitepaper](docs/Technical_Whitepaper.md) - Detailed architecture
- [API Documentation](docs/api.md) - Game integration guide
- [Development Guide](docs/development.md) - Contributing guidelines

## 🤝 Contributing

PlayerGold is open source and welcomes contributions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

PlayerGold is released under the MIT License. See [LICENSE](LICENSE) for details.

## 🌐 Links

- **Website**: [playergold.com](https://playergold.com)
- **Documentation**: [docs.playergold.com](https://docs.playergold.com)
- **GitHub**: [github.com/playergold/playergold](https://github.com/playergold/playergold)

---

**PlayerGold** - Empowering gamers with AI-driven, censorship-free blockchain technology.