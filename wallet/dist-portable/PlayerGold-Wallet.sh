#!/bin/bash
echo "==============================================="
echo "   PlayerGold Wallet - Starting..."
echo "   Hecho por gamers para gamers"
echo "==============================================="
echo

# Automatic Environment Detection and Configuration
echo "🔍 Detecting system environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8 or higher."
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "   macOS: brew install python3"
    echo "   Or download from: https://www.python.org/downloads/"
    echo
    echo "💡 After installing Python, run this script again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js."
    echo "   Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "   CentOS/RHEL: curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash - && sudo yum install -y nodejs"
    echo "   macOS: brew install node"
    echo "   Or download from: https://nodejs.org/"
    echo
    echo "💡 After installing Node.js, run this script again."
    exit 1
fi

echo "✅ System requirements verified successfully."
echo

# Automatic Environment Configuration
echo "⚙️ Configuring environment automatically..."

# Install Python dependencies if needed
if [ ! -d "backend/venv" ]; then
    echo "🐍 Setting up Python environment for the first time..."
    echo "   This may take a few minutes..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error installing Python dependencies."
        echo "   Please check your internet connection and try again."
        exit 1
    fi
    cd ..
    echo "✅ Python environment configured successfully."
fi

# Create comprehensive data directory structure
echo "📁 Creating directory structure..."
mkdir -p data/wallets
mkdir -p data/blockchain
mkdir -p data/logs
mkdir -p data/models
mkdir -p data/temp

# Pioneer Mode Initialization for New Installations
if [ ! -f "data/bootstrap-state.json" ]; then
    echo "🚀 First installation detected - Initializing pioneer mode..."
    echo "{\"mode\":\"pioneer\",\"initialized\":true,\"timestamp\":\"$(date)\",\"version\":\"1.0.0\",\"portable\":true}" > data/bootstrap-state.json
    echo "✅ Pioneer mode initialized. Ready to create the network!"
    echo
    echo "🎮 What does this mean?"
    echo "   - You are a PlayerGold pioneer user"
    echo "   - Your wallet will automatically search for other users"
    echo "   - When it finds other pioneers, you'll create the network together"
    echo "   - You don't need to do anything technical!"
    echo
fi

# Set environment variables for portable mode
export PLAYERGOLD_PORTABLE=true
export PLAYERGOLD_DATA_DIR="$(pwd)/data"
export PLAYERGOLD_BOOTSTRAP_MODE=auto
export NODE_ENV=production

# Final system check
echo "🔧 Final system verification..."
python3 --version 2>/dev/null
node --version 2>/dev/null
echo

# Start the wallet with enhanced portable mode support
echo "🚀 Starting PlayerGold Wallet in portable mode..."
echo "   Mode: Automatic Pioneer"
echo "   Data directory: $(pwd)/data"
echo
cd wallet
electron . --portable --pioneer-mode --no-sandbox

if [ $? -ne 0 ]; then
    echo
    echo "❌ Error starting the wallet."
    echo "💡 Possible solutions:"
    echo "   1. Restart your computer and try again"
    echo "   2. Run with sudo if needed"
    echo "   3. Check that no antivirus is blocking the application"
    echo
fi
