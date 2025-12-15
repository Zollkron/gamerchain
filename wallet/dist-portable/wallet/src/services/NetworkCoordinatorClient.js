/**
 * Network Coordinator Client
 * 
 * Handles communication with the PlayerGold Network Coordinator
 * for node registration, keepalive, and network map retrieval.
 */

const axios = require('axios');
const crypto = require('crypto');

class NetworkCoordinatorClient {
    constructor(coordinatorUrl = 'https://playergold.es', backupUrls = []) {
        this.coordinatorUrl = coordinatorUrl;
        this.backupUrls = backupUrls;
        this.nodeId = null;
        this.publicKey = null;
        this.privateKey = null;
        this.keepaliveInterval = null;
        this.networkMap = null;
        this.lastMapUpdate = null;
        
        // Load or generate node keypair
        this.loadOrGenerateNodeKeys();
    }
    
    /**
     * Load existing node keys or generate new ones
     */
    loadOrGenerateNodeKeys() {
        const fs = require('fs');
        const path = require('path');
        
        try {
            // Create data directory if it doesn't exist
            const dataDir = path.join(process.cwd(), 'data');
            if (!fs.existsSync(dataDir)) {
                fs.mkdirSync(dataDir, { recursive: true });
            }
            
            const keysFile = path.join(dataDir, 'node_keys.json');
            
            // Try to load existing keys
            if (fs.existsSync(keysFile)) {
                const keysData = JSON.parse(fs.readFileSync(keysFile, 'utf8'));
                this.nodeId = keysData.nodeId;
                this.publicKey = keysData.publicKey;
                this.privateKey = keysData.privateKey;
                
                console.log(`📂 Loaded existing node ID: ${this.nodeId}`);
                return;
            }
            
            // Generate new keys if none exist
            this.generateNewNodeKeys();
            
            // Save keys for future use
            const keysData = {
                nodeId: this.nodeId,
                publicKey: this.publicKey,
                privateKey: this.privateKey,
                createdAt: new Date().toISOString()
            };
            
            fs.writeFileSync(keysFile, JSON.stringify(keysData, null, 2));
            console.log(`💾 Saved new node keys to: ${keysFile}`);
            
        } catch (error) {
            console.error('Failed to load/generate node keys:', error);
            // Fallback to in-memory keys
            this.generateNewNodeKeys();
        }
    }
    
    /**
     * Generate new keypair for node authentication
     */
    generateNewNodeKeys() {
        try {
            // Use RSA as fallback since Ed25519 might not be supported
            const keyPair = crypto.generateKeyPairSync('rsa', {
                modulusLength: 2048,
                publicKeyEncoding: { type: 'spki', format: 'pem' },
                privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
            });
            
            this.publicKey = keyPair.publicKey;
            this.privateKey = keyPair.privateKey;
            
            // Generate node ID from public key hash
            const publicKeyHash = crypto.createHash('sha256')
                .update(this.publicKey)
                .digest('hex');
            this.nodeId = `PG${publicKeyHash.substring(0, 40)}`;
            
            console.log(`🔑 Generated new node ID: ${this.nodeId}`);
            
        } catch (error) {
            console.error('Failed to generate node keys:', error);
            // Fallback to random node ID
            this.nodeId = `PG${crypto.randomBytes(20).toString('hex')}`;
            this.publicKey = 'dummy_public_key';
            this.privateKey = 'dummy_private_key';
        }
    }
    
    /**
     * Sign a message with the node's private key
     */
    signMessage(message) {
        try {
            if (this.privateKey === 'dummy_private_key') {
                return 'dummy_signature';
            }
            
            const sign = crypto.createSign('SHA256');
            sign.update(message);
            sign.end();
            return sign.sign(this.privateKey, 'base64');
        } catch (error) {
            console.error('Failed to sign message:', error);
            return 'dummy_signature'; // Fallback for development
        }
    }
    
    /**
     * Get current location (placeholder implementation)
     */
    async getCurrentLocation() {
        // In a real implementation, this would:
        // 1. Try to get GPS coordinates if available
        // 2. Fall back to IP geolocation
        // 3. Use cached location if available
        
        try {
            // Try IP geolocation as fallback
            const response = await axios.get('http://ip-api.com/json/', { timeout: 5000 });
            if (response.data && response.data.status === 'success') {
                return {
                    latitude: response.data.lat,
                    longitude: response.data.lon
                };
            }
        } catch (error) {
            console.warn('IP geolocation failed:', error.message);
        }
        
        // Default location (Madrid, Spain) if geolocation fails
        return {
            latitude: 40.4168,
            longitude: -3.7038
        };
    }
    
    /**
     * Register this node with the network coordinator
     */
    async registerNode(nodeType = 'regular', port = 18333) {
        try {
            const location = await this.getCurrentLocation();
            const osInfo = `${process.platform} ${process.arch}`;
            
            // Get public IP (placeholder)
            let publicIp = '127.0.0.1';
            try {
                const ipResponse = await axios.get('https://api.ipify.org?format=json', { timeout: 5000 });
                publicIp = ipResponse.data.ip;
            } catch (error) {
                console.warn('Failed to get public IP, using localhost');
            }
            
            const registrationData = {
                node_id: this.nodeId,
                public_ip: publicIp,
                port: port,
                latitude: location.latitude,
                longitude: location.longitude,
                os_info: osInfo,
                node_type: nodeType,
                public_key: Buffer.from(this.publicKey).toString('base64'),
                signature: this.signMessage(`${this.nodeId}:${publicIp}:${port}`)
            };
            
            const response = await this.makeRequest('POST', '/api/v1/register', registrationData);
            
            if (response.status === 'success') {
                console.log('✅ Node registered successfully with network coordinator');
                
                // Start keepalive
                this.startKeepalive();
                
                return true;
            } else {
                console.error('❌ Node registration failed:', response.message);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Node registration error:', error.message);
            return false;
        }
    }
    
    /**
     * Send keepalive message to coordinator
     */
    async sendKeepalive(blockchainHeight = 0, connectedPeers = 0, aiModelLoaded = false, miningActive = false) {
        try {
            const keepaliveData = {
                node_id: this.nodeId,
                blockchain_height: blockchainHeight,
                connected_peers: connectedPeers,
                cpu_usage: process.cpuUsage ? this.getCpuUsage() : 0,
                memory_usage: this.getMemoryUsage(),
                network_latency: 0, // Placeholder
                ai_model_loaded: aiModelLoaded,
                mining_active: miningActive,
                signature: this.signMessage(`${this.nodeId}:${Date.now()}`)
            };
            
            const response = await this.makeRequest('POST', '/api/v1/keepalive', keepaliveData);
            
            if (response.status === 'success') {
                console.log('📡 KeepAlive sent successfully');
                return true;
            } else {
                console.warn('⚠️ KeepAlive failed:', response.message);
                return false;
            }
            
        } catch (error) {
            console.warn('⚠️ KeepAlive error:', error.message);
            return false;
        }
    }
    
    /**
     * Start automatic keepalive sending
     */
    startKeepalive() {
        if (this.keepaliveInterval) {
            clearInterval(this.keepaliveInterval);
        }
        
        // Send keepalive every 60 seconds
        this.keepaliveInterval = setInterval(() => {
            this.sendKeepalive();
        }, 60000);
        
        // Send initial keepalive
        setTimeout(() => this.sendKeepalive(), 1000);
    }
    
    /**
     * Stop automatic keepalive
     */
    stopKeepalive() {
        if (this.keepaliveInterval) {
            clearInterval(this.keepaliveInterval);
            this.keepaliveInterval = null;
        }
    }
    
    /**
     * Get network map from coordinator
     */
    async getNetworkMap(maxDistanceKm = null, limit = null) {
        try {
            const location = await this.getCurrentLocation();
            
            const requestData = {
                requester_latitude: location.latitude,
                requester_longitude: location.longitude
            };
            
            if (maxDistanceKm !== null) {
                requestData.max_distance_km = maxDistanceKm;
            }
            
            if (limit !== null) {
                requestData.limit = limit;
            }
            
            const response = await this.makeRequest('POST', '/api/v1/network-map', requestData);
            
            if (response.status === 'success' && response.map) {
                this.networkMap = response.map;
                this.lastMapUpdate = new Date();
                
                console.log(`📊 Network map updated: ${response.map.active_nodes} active nodes`);
                return response.map;
            } else {
                console.warn('⚠️ Failed to get network map:', response.message);
                return null;
            }
            
        } catch (error) {
            console.warn('⚠️ Network map error:', error.message);
            
            // Try backup nodes if main coordinator fails
            return await this.getNetworkMapFromBackup();
        }
    }
    
    /**
     * Get network map from backup nodes
     */
    async getNetworkMapFromBackup() {
        for (const backupUrl of this.backupUrls) {
            try {
                console.log(`🔄 Trying backup coordinator: ${backupUrl}`);
                
                const response = await axios.get(`${backupUrl}/api/backup/latest`, {
                    timeout: 10000
                });
                
                if (response.data && response.data.encrypted_map) {
                    console.log('✅ Got network map from backup node');
                    return response.data.encrypted_map;
                }
                
            } catch (error) {
                console.warn(`⚠️ Backup ${backupUrl} failed:`, error.message);
            }
        }
        
        console.error('❌ All coordinators (main + backups) are unavailable');
        return null;
    }
    
    /**
     * Get network statistics
     */
    async getNetworkStats() {
        try {
            const response = await this.makeRequest('GET', '/api/v1/stats');
            return response;
            
        } catch (error) {
            console.warn('⚠️ Failed to get network stats:', error.message);
            return null;
        }
    }
    
    /**
     * Make HTTP request to coordinator with fallback to backups
     */
    async makeRequest(method, endpoint, data = null) {
        const urls = [this.coordinatorUrl, ...this.backupUrls];
        
        for (const url of urls) {
            try {
                const config = {
                    method: method,
                    url: `${url}${endpoint}`,
                    timeout: 15000,
                    headers: {
                        'Content-Type': 'application/json',
                        'User-Agent': 'PlayerGold-Wallet/1.0.0'
                    },
                    // Handle SSL issues in development/testing
                    httpsAgent: new (require('https').Agent)({
                        rejectUnauthorized: false // Allow self-signed certificates for testing
                    })
                };
                
                if (data) {
                    config.data = data;
                }
                
                console.log(`🌐 Making request to: ${config.url}`);
                const response = await axios(config);
                console.log(`✅ Request successful: ${response.status}`);
                return response.data;
                
            } catch (error) {
                console.warn(`⚠️ Request to ${url} failed:`, error.message);
                
                // Try with native https module as fallback
                if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
                    try {
                        console.log(`🔄 Trying native HTTPS for ${url}...`);
                        const result = await this.makeNativeHttpsRequest(url, endpoint, method, data);
                        return result;
                    } catch (nativeError) {
                        console.warn(`⚠️ Native HTTPS also failed:`, nativeError.message);
                    }
                }
                
                if (url === urls[urls.length - 1]) {
                    // Last URL, re-throw error
                    throw error;
                }
            }
        }
    }
    
    /**
     * Fallback HTTP request using native Node.js modules
     */
    async makeNativeHttpsRequest(baseUrl, endpoint, method = 'GET', data = null) {
        return new Promise((resolve, reject) => {
            const https = require('https');
            const url = require('url');
            
            const fullUrl = `${baseUrl}${endpoint}`;
            const parsedUrl = url.parse(fullUrl);
            
            const options = {
                hostname: parsedUrl.hostname,
                port: parsedUrl.port || 443,
                path: parsedUrl.path,
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'PlayerGold-Wallet/1.0.0'
                },
                rejectUnauthorized: false // Allow self-signed certificates
            };
            
            const req = https.request(options, (res) => {
                let responseData = '';
                
                res.on('data', (chunk) => {
                    responseData += chunk;
                });
                
                res.on('end', () => {
                    try {
                        const jsonData = JSON.parse(responseData);
                        resolve(jsonData);
                    } catch (parseError) {
                        reject(new Error(`Failed to parse response: ${parseError.message}`));
                    }
                });
            });
            
            req.on('error', (error) => {
                reject(error);
            });
            
            req.setTimeout(15000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });
            
            if (data && (method === 'POST' || method === 'PUT')) {
                req.write(JSON.stringify(data));
            }
            
            req.end();
        });
    }
    
    /**
     * Get CPU usage percentage (placeholder)
     */
    getCpuUsage() {
        // Placeholder implementation
        return Math.random() * 100;
    }
    
    /**
     * Get memory usage percentage
     */
    getMemoryUsage() {
        const used = process.memoryUsage();
        const total = require('os').totalmem();
        return (used.heapUsed / total) * 100;
    }
    
    /**
     * Calculate distance between two coordinates
     */
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in kilometers
        const dLat = this.toRadians(lat2 - lat1);
        const dLon = this.toRadians(lon2 - lon1);
        
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }
    
    toRadians(degrees) {
        return degrees * (Math.PI / 180);
    }
    
    /**
     * Clean shutdown
     */
    shutdown() {
        console.log('🔄 Shutting down Network Coordinator client...');
        this.stopKeepalive();
        
        // Send disconnection notification (optional)
        // In a real implementation, we might want to notify the coordinator
        // that we're disconnecting cleanly
    }
}

module.exports = NetworkCoordinatorClient;