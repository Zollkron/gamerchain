#!/bin/bash

# Update Network Coordinator with full endpoints
# This script updates the coordinator on the server to include all endpoints

echo "============================================================================"
echo "PlayerGold Network Coordinator - Update Full Endpoints"
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

log "Updating Network Coordinator with full endpoints..."

# Stop current coordinator service
log "Stopping current coordinator service..."
systemctl stop playergold-coordinator 2>/dev/null || true

# Backup current installation
log "Creating backup of current installation..."
if [ -d "/opt/playergold" ]; then
    cp -r /opt/playergold /opt/playergold.backup.$(date +%Y%m%d_%H%M%S)
    success "Backup created"
fi

# Update coordinator files
log "Updating coordinator source files..."

# Create directory structure
mkdir -p /opt/playergold/src/network_coordinator
mkdir -p /opt/playergold/scripts
mkdir -p /opt/playergold/logs
mkdir -p /opt/playergold/data

# Copy updated source files (assuming they're in the current directory)
if [ -f "src/network_coordinator/server.py" ]; then
    cp src/network_coordinator/*.py /opt/playergold/src/network_coordinator/
    success "Source files updated"
else
    error "Source files not found. Run this script from the project root directory."
    exit 1
fi

# Copy startup script
if [ -f "scripts/start_network_coordinator.py" ]; then
    cp scripts/start_network_coordinator.py /opt/playergold/scripts/
    success "Startup script updated"
fi

# Set proper ownership
chown -R playergold:playergold /opt/playergold/

# Install Python dependencies
log "Installing/updating Python dependencies..."
sudo -u playergold /opt/playergold/venv/bin/pip install fastapi uvicorn aiofiles cryptography pydantic

# Update systemd service to use the full coordinator
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
Environment=PATH=/opt/playergold/venv/bin
Environment=PYTHONPATH=/opt/playergold
ExecStart=/opt/playergold/venv/bin/python scripts/start_network_coordinator.py --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10
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

# Reload systemd and start service
log "Reloading systemd and starting coordinator..."
systemctl daemon-reload
systemctl enable playergold-coordinator
systemctl start playergold-coordinator

# Wait for service to start
sleep 5

# Check service status
if systemctl is-active --quiet playergold-coordinator; then
    success "Coordinator service is running"
else
    error "Coordinator service failed to start"
    log "Checking service logs..."
    journalctl -u playergold-coordinator --no-pager -n 20
    exit 1
fi

# Test endpoints
log "Testing coordinator endpoints..."

# Test health endpoint
if curl -s -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost:8000/api/v1/health | grep -q "healthy"; then
    success "Health endpoint working"
else
    warning "Health endpoint not responding correctly"
fi

# Test registration endpoint
log "Testing registration endpoint..."
REGISTER_RESPONSE=$(curl -s -X POST \
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

if echo "$REGISTER_RESPONSE" | grep -q "success"; then
    success "Registration endpoint working"
else
    warning "Registration endpoint not working correctly"
    echo "Response: $REGISTER_RESPONSE"
fi

# Test network map endpoint
log "Testing network map endpoint..."
MAP_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "User-Agent: PlayerGold-Wallet/1.0.0" \
    -d '{
        "requester_latitude": 40.4168,
        "requester_longitude": -3.7038
    }' \
    http://localhost:8000/api/v1/network-map)

if echo "$MAP_RESPONSE" | grep -q "encrypted_data"; then
    success "Network map endpoint working"
else
    warning "Network map endpoint not working correctly"
    echo "Response: $MAP_RESPONSE"
fi

# Update Apache configuration to proxy all endpoints
log "Updating Apache configuration..."
cat > /etc/apache2/sites-available/playergold-coordinator.conf << 'EOF'
<VirtualHost *:443>
    ServerName playergold.es
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/playergold.es/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/playergold.es/privkey.pem
    
    # Security Headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    
    # User-Agent validation for all API endpoints
    <LocationMatch "^/api/">
        RewriteEngine On
        RewriteCond %{HTTP_USER_AGENT} !^PlayerGold-Wallet/
        RewriteRule .* - [F,L]
        
        # Rate limiting
        <RequireAll>
            Require all granted
        </RequireAll>
    </LocationMatch>
    
    # Proxy all API requests to coordinator
    ProxyPreserveHost On
    ProxyPass /api/ http://127.0.0.1:8000/api/
    ProxyPassReverse /api/ http://127.0.0.1:8000/api/
    
    # Default page
    DocumentRoot /var/www/html
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/playergold_error.log
    CustomLog ${APACHE_LOG_DIR}/playergold_access.log combined
</VirtualHost>

# Redirect HTTP to HTTPS
<VirtualHost *:80>
    ServerName playergold.es
    Redirect permanent / https://playergold.es/
</VirtualHost>
EOF

# Enable site and restart Apache
a2ensite playergold-coordinator
systemctl reload apache2

# Final verification
log "Final verification..."
sleep 2

# Test through Apache (HTTPS)
if curl -k -s -H "User-Agent: PlayerGold-Wallet/1.0.0" https://playergold.es/api/v1/health | grep -q "healthy"; then
    success "HTTPS health endpoint working through Apache"
else
    warning "HTTPS health endpoint not working through Apache"
fi

echo
echo "============================================================================"
echo "                    🎉 COORDINATOR UPDATE COMPLETED"
echo "============================================================================"
echo
success "Network Coordinator updated with full endpoints"
echo
echo "📋 Available endpoints:"
echo "   • GET  /api/v1/health      - Health check"
echo "   • POST /api/v1/register    - Node registration"
echo "   • POST /api/v1/network-map - Get network map"
echo "   • POST /api/v1/keepalive   - Node keepalive"
echo "   • GET  /api/v1/stats       - Network statistics"
echo
echo "🌐 Access URLs:"
echo "   • Health: https://playergold.es/api/v1/health"
echo "   • All endpoints require User-Agent: PlayerGold-Wallet/1.0.0"
echo
echo "🔧 Management commands:"
echo "   • Status: systemctl status playergold-coordinator"
echo "   • Logs:   journalctl -u playergold-coordinator -f"
echo "   • Restart: systemctl restart playergold-coordinator"
echo
success "Coordinator is ready for production use!"