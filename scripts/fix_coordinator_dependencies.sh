#!/bin/bash

# Fix Network Coordinator Dependencies and Restart Service
# This script fixes the missing aiohttp dependency and ensures all endpoints work

echo "============================================================================"
echo "PlayerGold Network Coordinator - Fix Dependencies & Restart"
echo "============================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
   exit 1
fi

log "Fixing Network Coordinator dependencies and restarting service..."

# Step 1: Stop current coordinator service
log "Stopping current coordinator service..."
systemctl stop playergold-coordinator 2>/dev/null || true
sleep 2

# Step 2: Check service status
log "Checking service status..."
if systemctl is-active --quiet playergold-coordinator; then
    warning "Service still running, force stopping..."
    systemctl kill playergold-coordinator
    sleep 3
fi

# Step 3: Install missing dependencies
log "Installing missing Python dependencies..."
sudo -u playergold /opt/playergold/venv/bin/pip install --upgrade pip
sudo -u playergold /opt/playergold/venv/bin/pip install aiohttp aiofiles
sudo -u playergold /opt/playergold/venv/bin/pip install fastapi uvicorn cryptography pydantic
sudo -u playergold /opt/playergold/venv/bin/pip install sqlalchemy sqlite3

# Step 4: Verify dependencies are installed
log "Verifying dependencies..."
MISSING_DEPS=0

if ! sudo -u playergold /opt/playergold/venv/bin/python -c "import aiohttp" 2>/dev/null; then
    error "aiohttp still missing"
    MISSING_DEPS=1
fi

if ! sudo -u playergold /opt/playergold/venv/bin/python -c "import fastapi" 2>/dev/null; then
    error "fastapi still missing"
    MISSING_DEPS=1
fi

if ! sudo -u playergold /opt/playergold/venv/bin/python -c "import uvicorn" 2>/dev/null; then
    error "uvicorn still missing"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    error "Some dependencies are still missing. Attempting alternative installation..."
    
    # Try system-wide installation as fallback
    apt update
    apt install -y python3-aiohttp python3-fastapi python3-uvicorn
    
    # Try pip3 system installation
    pip3 install aiohttp fastapi uvicorn cryptography pydantic
fi

# Step 5: Ensure coordinator source files are present
log "Checking coordinator source files..."
if [ ! -f "/opt/playergold/src/network_coordinator/server.py" ]; then
    error "Coordinator source files missing. Copying from current directory..."
    
    if [ -f "src/network_coordinator/server.py" ]; then
        mkdir -p /opt/playergold/src/network_coordinator
        cp -r src/network_coordinator/* /opt/playergold/src/network_coordinator/
        chown -R playergold:playergold /opt/playergold/src/
        success "Source files copied"
    else
        error "Source files not found in current directory. Run from project root."
        exit 1
    fi
fi

# Step 6: Create startup script if missing
log "Ensuring startup script exists..."
if [ ! -f "/opt/playergold/scripts/start_network_coordinator.py" ]; then
    mkdir -p /opt/playergold/scripts
    cat > /opt/playergold/scripts/start_network_coordinator.py << 'EOF'
#!/usr/bin/env python3
"""
Network Coordinator Startup Script
"""

import sys
import os
import argparse

# Add the project root to Python path
sys.path.insert(0, '/opt/playergold')

def main():
    parser = argparse.ArgumentParser(description='Start PlayerGold Network Coordinator')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    try:
        from src.network_coordinator.server import run_server
        print(f"Starting Network Coordinator on {args.host}:{args.port}")
        run_server(host=args.host, port=args.port, debug=args.debug)
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
    
    chmod +x /opt/playergold/scripts/start_network_coordinator.py
    chown playergold:playergold /opt/playergold/scripts/start_network_coordinator.py
    success "Startup script created"
fi

# Step 7: Update systemd service with better configuration
log "Updating systemd service configuration..."
cat > /etc/systemd/system/playergold-coordinator.service << 'EOF'
[Unit]
Description=PlayerGold Network Coordinator
After=network.target
Wants=network.target

[Service]
Type=simple
User=playergold
Group=playergold
WorkingDirectory=/opt/playergold
Environment=PATH=/opt/playergold/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/playergold
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/playergold/venv/bin/python /opt/playergold/scripts/start_network_coordinator.py --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=playergold-coordinator

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/playergold/data /opt/playergold/logs

[Install]
WantedBy=multi-user.target
EOF

# Step 8: Reload systemd and start service
log "Reloading systemd daemon..."
systemctl daemon-reload

log "Enabling coordinator service..."
systemctl enable playergold-coordinator

log "Starting coordinator service..."
systemctl start playergold-coordinator

# Step 9: Wait for service to start and check status
log "Waiting for service to start..."
sleep 5

# Check if service is running
if systemctl is-active --quiet playergold-coordinator; then
    success "Coordinator service is running!"
else
    error "Coordinator service failed to start"
    log "Checking service logs..."
    journalctl -u playergold-coordinator --no-pager -n 20
    
    # Try to start manually for debugging
    log "Attempting manual start for debugging..."
    sudo -u playergold /opt/playergold/venv/bin/python /opt/playergold/scripts/start_network_coordinator.py --host 127.0.0.1 --port 8000 &
    MANUAL_PID=$!
    sleep 3
    
    if kill -0 $MANUAL_PID 2>/dev/null; then
        success "Manual start successful, killing and restarting service..."
        kill $MANUAL_PID
        systemctl restart playergold-coordinator
        sleep 3
    else
        error "Manual start also failed"
        exit 1
    fi
fi

# Step 10: Test local endpoints
log "Testing local endpoints..."

# Test health endpoint locally
if curl -s -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost:8000/api/v1/health | grep -q "healthy"; then
    success "✅ Health endpoint working locally"
else
    warning "❌ Health endpoint not working locally"
    
    # Show service logs for debugging
    log "Service logs:"
    journalctl -u playergold-coordinator --no-pager -n 10
fi

# Test registration endpoint locally
REGISTER_TEST=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "User-Agent: PlayerGold-Wallet/1.0.0" \
    -d '{
        "node_id": "PGtest123456789",
        "public_ip": "127.0.0.1",
        "port": 18333,
        "latitude": 40.4168,
        "longitude": -3.7038,
        "os_info": "test",
        "node_type": "regular",
        "public_key": "test_key",
        "signature": "test_signature"
    }' \
    http://localhost:8000/api/v1/register)

if echo "$REGISTER_TEST" | grep -q "success"; then
    success "✅ Registration endpoint working locally"
else
    warning "❌ Registration endpoint not working locally"
    echo "Response: $REGISTER_TEST"
fi

# Step 11: Restart Apache to ensure proxy is working
log "Restarting Apache to ensure proxy configuration is active..."
systemctl restart apache2
sleep 2

# Step 12: Test through Apache proxy
log "Testing endpoints through Apache proxy..."

# Test health through Apache
if curl -k -s -H "User-Agent: PlayerGold-Wallet/1.0.0" https://playergold.es/api/v1/health | grep -q "healthy"; then
    success "✅ Health endpoint working through Apache HTTPS"
else
    warning "❌ Health endpoint not working through Apache HTTPS"
    
    # Check Apache error logs
    log "Apache error logs:"
    tail -n 5 /var/log/apache2/playergold_error.log 2>/dev/null || echo "No Apache error logs found"
fi

# Step 13: Final status report
echo
echo "============================================================================"
echo "                    🎉 COORDINATOR DEPENDENCY FIX COMPLETED"
echo "============================================================================"
echo

# Service status
if systemctl is-active --quiet playergold-coordinator; then
    success "✅ Coordinator service is running"
    
    # Show service info
    log "Service status:"
    systemctl status playergold-coordinator --no-pager -l
else
    error "❌ Coordinator service is not running"
fi

echo
echo "🔧 Next steps:"
echo "   1. Test all endpoints: node test_coordinator_endpoints_final.js"
echo "   2. Check service logs: journalctl -u playergold-coordinator -f"
echo "   3. Test wallet connection"
echo
echo "🌐 Coordinator should now be available at:"
echo "   • https://playergold.es/api/v1/health"
echo "   • https://playergold.es/api/v1/register"
echo "   • https://playergold.es/api/v1/network-map"
echo "   • https://playergold.es/api/v1/keepalive"
echo "   • https://playergold.es/api/v1/stats"
echo
success "Coordinator dependency fix completed!"