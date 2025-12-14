#!/bin/bash

# Fix Network Coordinator Permissions and Database Issues
# This script fixes the specific permission and database problems found

echo "============================================================================"
echo "PlayerGold Network Coordinator - Fix Permissions & Database"
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

log "Fixing coordinator permissions and database issues..."

# Step 1: Stop service
log "Stopping coordinator service..."
systemctl stop playergold-coordinator 2>/dev/null || true
sleep 2

# Step 2: Create and fix directory permissions
log "Creating and fixing directory permissions..."

# Create all necessary directories
mkdir -p /opt/playergold/data
mkdir -p /opt/playergold/logs
mkdir -p /opt/playergold/src/network_coordinator
mkdir -p /opt/playergold/scripts

# Set proper ownership for all directories
chown -R playergold:playergold /opt/playergold/
chmod -R 755 /opt/playergold/

# Ensure data and logs directories are writable
chmod 775 /opt/playergold/data
chmod 775 /opt/playergold/logs

success "Directory permissions fixed"

# Step 3: Initialize database properly
log "Initializing database..."

# Create database file with proper permissions
DB_PATH="/opt/playergold/data/network_nodes.db"
touch "$DB_PATH"
chown playergold:playergold "$DB_PATH"
chmod 664 "$DB_PATH"

success "Database file created with proper permissions"

# Step 4: Update startup script to handle permissions
log "Updating startup script..."
cat > /opt/playergold/scripts/start_network_coordinator.py << 'EOF'
#!/usr/bin/env python3
"""
Network Coordinator Startup Script - Fixed Version
"""

import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='Start PlayerGold Network Coordinator')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Change to the correct working directory
    os.chdir('/opt/playergold')
    
    # Add the project root to Python path
    sys.path.insert(0, '/opt/playergold')
    
    # Ensure data and logs directories exist
    os.makedirs('/opt/playergold/data', exist_ok=True)
    os.makedirs('/opt/playergold/logs', exist_ok=True)
    
    try:
        from src.network_coordinator.server import run_server
        print(f"Starting Network Coordinator on {args.host}:{args.port}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Database path: /opt/playergold/data/network_nodes.db")
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

success "Startup script updated"

# Step 5: Update registry.py to use absolute paths
log "Updating registry.py to use absolute database path..."

# Backup original registry.py
cp /opt/playergold/src/network_coordinator/registry.py /opt/playergold/src/network_coordinator/registry.py.backup

# Update registry.py to use absolute path
sed -i 's|self.db_path = "network_nodes.db"|self.db_path = "/opt/playergold/data/network_nodes.db"|g' /opt/playergold/src/network_coordinator/registry.py

success "Registry updated to use absolute database path"

# Step 6: Test database creation manually
log "Testing database creation..."
sudo -u playergold python3 -c "
import sqlite3
import os
os.chdir('/opt/playergold')
db_path = '/opt/playergold/data/network_nodes.db'
print(f'Testing database at: {db_path}')
try:
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER)')
    conn.close()
    print('✅ Database creation successful')
except Exception as e:
    print(f'❌ Database creation failed: {e}')
"

# Step 7: Update systemd service
log "Updating systemd service..."
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

# Security settings (relaxed for database access)
NoNewPrivileges=true
PrivateTmp=false
ProtectSystem=false
ProtectHome=false
ReadWritePaths=/opt/playergold

[Install]
WantedBy=multi-user.target
EOF

# Step 8: Reload and start service
log "Reloading systemd and starting service..."
systemctl daemon-reload
systemctl enable playergold-coordinator

# Step 9: Test manual start first
log "Testing manual start..."
sudo -u playergold /opt/playergold/venv/bin/python /opt/playergold/scripts/start_network_coordinator.py --host 127.0.0.1 --port 8000 &
MANUAL_PID=$!
sleep 5

if kill -0 $MANUAL_PID 2>/dev/null; then
    success "Manual start successful!"
    kill $MANUAL_PID
    sleep 2
    
    # Now start the service
    log "Starting systemd service..."
    systemctl start playergold-coordinator
    sleep 3
    
    if systemctl is-active --quiet playergold-coordinator; then
        success "✅ Coordinator service is running!"
    else
        error "Service failed to start, checking logs..."
        journalctl -u playergold-coordinator --no-pager -n 10
    fi
else
    error "Manual start failed"
    exit 1
fi

# Step 10: Test endpoints
log "Testing endpoints..."

# Wait a bit for service to fully start
sleep 3

# Test health endpoint
if curl -s -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost:8000/api/v1/health | grep -q "healthy"; then
    success "✅ Health endpoint working!"
else
    warning "Health endpoint not responding yet, checking service..."
    systemctl status playergold-coordinator --no-pager
fi

echo
echo "============================================================================"
echo "                    🎉 COORDINATOR PERMISSIONS FIXED"
echo "============================================================================"
echo

if systemctl is-active --quiet playergold-coordinator; then
    success "✅ Coordinator service is running"
    echo
    echo "🧪 Test the endpoints now:"
    echo "   node test_coordinator_endpoints_final.js"
    echo
    echo "🔧 Monitor logs:"
    echo "   journalctl -u playergold-coordinator -f"
else
    error "❌ Service still not running"
    echo "Check logs: journalctl -u playergold-coordinator -n 20"
fi

success "Permission and database fix completed!"