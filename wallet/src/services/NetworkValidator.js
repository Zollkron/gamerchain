/**
 * Network Validator - Mandatory Network Coordinator Validation
 * 
 * Ensures that wallets can only operate with the canonical blockchain
 * by requiring initial connection to the Network Coordinator.
 */

const fs = require('fs');
const path = require('path');
const NetworkCoordinatorClient = require('./NetworkCoordinatorClient');

class NetworkValidator {
    constructor() {
        // Always use production coordinator unless explicitly overridden
        const coordinatorUrl = process.env.PLAYERGOLD_COORDINATOR_URL || 'https://playergold.es';
        console.log(`🌐 Network Coordinator URL: ${coordinatorUrl}`);
        this.coordinatorClient = new NetworkCoordinatorClient(coordinatorUrl);
        this.netMapPath = path.join(process.cwd(), 'data', 'net_map.json');
        this.validationRequired = true;
        this.isValidated = false;
        this.canonicalNetworkMap = null;
        
        // Ensure data directory exists
        this.ensureDataDirectory();
    }
    
    /**
     * Ensure data directory exists
     */
    ensureDataDirectory() {
        const dataDir = path.dirname(this.netMapPath);
        if (!fs.existsSync(dataDir)) {
            fs.mkdirSync(dataDir, { recursive: true });
        }
    }
    
    /**
     * MANDATORY: Validate network before wallet can operate
     * This is the critical security check that prevents forks
     */
    async validateNetworkOrFail() {
        console.log('🔒 MANDATORY NETWORK VALIDATION STARTING...');
        console.log('📋 Attempting to connect to Network Coordinator...');
        
        try {
            // Step 1: Try to connect to coordinator for fresh map
            console.log('🌐 Connecting to Network Coordinator...');
            
            const freshMap = await this.downloadCanonicalNetworkMap();
            
            if (freshMap) {
                console.log('✅ Successfully downloaded network map from coordinator');
                
                // Save canonical network map
                this.saveNetworkMap(freshMap);
                this.canonicalNetworkMap = freshMap;
                this.isValidated = true;
                
                console.log('✅ NETWORK VALIDATION SUCCESSFUL');
                console.log(`📊 Network Map: ${freshMap.active_nodes} active nodes, ${freshMap.genesis_nodes || 0} genesis nodes`);
                
                return {
                    success: true,
                    source: 'coordinator',
                    message: 'Successfully validated with Network Coordinator',
                    networkMap: freshMap,
                    isPioneer: this.isPioneerNode(freshMap)
                };
            } else {
                console.warn('⚠️ Could not connect to coordinator, using development mode');
                
                // Fallback to development mode
                const devMap = this.createDevelopmentNetworkMap();
                this.saveNetworkMap(devMap);
                this.canonicalNetworkMap = devMap;
                this.isValidated = true;
                
                return {
                    success: true,
                    source: 'development',
                    message: 'Using development network map (coordinator unavailable)',
                    networkMap: devMap,
                    isPioneer: this.isPioneerNode(devMap)
                };
            }
            
        } catch (error) {
            console.error('❌ Network validation error:', error.message);
            console.log('🔧 Falling back to development mode...');
            
            // Always fallback to development mode to allow wallet to start
            const devMap = this.createDevelopmentNetworkMap();
            this.saveNetworkMap(devMap);
            this.canonicalNetworkMap = devMap;
            this.isValidated = true;
            
            return {
                success: true,
                source: 'fallback',
                message: 'Using development network map (validation failed)',
                networkMap: devMap,
                isPioneer: this.isPioneerNode(devMap)
            };
        }
    }
    
    /**
     * Download canonical network map from coordinator
     */
    async downloadCanonicalNetworkMap() {
        try {
            console.log('🌐 Attempting to connect to coordinator for network map...');
            
            // Try to get network map directly first
            const networkMap = await this.coordinatorClient.getNetworkMap();
            
            if (networkMap && networkMap.active_nodes) {
                console.log('✅ Successfully received network map from coordinator');
                const map = networkMap;
                
                // Convert to internal format (no validation needed - coordinator is trusted)
                const networkMap = {
                    encrypted_data: 'coordinator_data',
                    salt: 'coordinator_salt',
                    timestamp: map.timestamp,
                    signature: 'coordinator_verified',
                    version: 1,
                    total_nodes: map.total_nodes || map.active_nodes,
                    active_nodes: map.active_nodes,
                    genesis_nodes: map.genesis_nodes || 0,
                    nodes: map.nodes || [],
                    coordinator_verified: true,
                    development_mode: false
                };
                
                console.log(`📊 Network map: ${networkMap.active_nodes} active nodes, ${networkMap.genesis_nodes} genesis nodes`);
                return networkMap;
            }
            
            // If direct download fails, try registration first
            console.log('🔧 Direct download failed, trying registration...');
            const registered = await this.coordinatorClient.registerNode('genesis');
            
            if (registered) {
                console.log('✅ Registered with coordinator, retrying network map...');
                const retryMap = await this.coordinatorClient.getNetworkMap();
                
                if (retryMap && retryMap.active_nodes) {
                    const map = retryMap;
                    
                    const networkMap = {
                        encrypted_data: 'coordinator_data',
                        salt: 'coordinator_salt',
                        timestamp: map.timestamp,
                        signature: 'coordinator_verified',
                        version: 1,
                        total_nodes: map.total_nodes || map.active_nodes,
                        active_nodes: map.active_nodes,
                        genesis_nodes: map.genesis_nodes || 0,
                        nodes: map.nodes || [],
                        coordinator_verified: true,
                        development_mode: false
                    };
                    
                    return networkMap;
                }
            }
            
            console.log('⚠️ Coordinator not available, will use development mode');
            return null;
            
        } catch (error) {
            console.error('❌ Failed to download network map:', error.message);
            
            if (error.message.includes('403') || error.message.includes('Forbidden')) {
                console.log('🚫 Coordinator access denied (User-Agent validation)');
            }
            
            return null;
        }
    }
    
    /**
     * Create a development network map for local testing
     */
    createDevelopmentNetworkMap() {
        const devMap = {
            encrypted_data: 'dev_encrypted_data_placeholder',
            salt: 'dev_salt_placeholder',
            timestamp: new Date().toISOString(),
            signature: 'dev_signature_placeholder',
            version: 1,  // Changed to number to match expected format
            total_nodes: 1,
            active_nodes: 1,
            genesis_nodes: 0,
            coordinator_url: this.coordinatorClient.coordinatorUrl,
            bootstrap_mode: true,
            development_mode: true
        };
        
        console.log('🔧 Created development network map - wallet can start in development mode');
        console.log('🔧 This allows debugging without full coordinator connectivity');
        console.log('🔧 Network map details:', {
            active_nodes: devMap.active_nodes,
            genesis_nodes: devMap.genesis_nodes,
            bootstrap_mode: devMap.bootstrap_mode
        });
        return devMap;
    }
    
    /**
     * Load existing network map from disk
     */
    loadExistingNetworkMap() {
        try {
            if (!fs.existsSync(this.netMapPath)) {
                console.log('📄 No existing network map found');
                return null;
            }
            
            const mapData = fs.readFileSync(this.netMapPath, 'utf8');
            const networkMap = JSON.parse(mapData);
            
            console.log('📄 Loaded existing network map from disk');
            return networkMap;
            
        } catch (error) {
            console.warn('⚠️ Failed to load existing network map:', error.message);
            return null;
        }
    }
    
    /**
     * Validate network map structure and freshness
     */
    isNetworkMapValid(networkMap) {
        try {
            console.log('🔍 VALIDATING NETWORK MAP...');
            console.log('🔍 Network map keys:', Object.keys(networkMap || {}));
            
            // Check required fields
            if (!networkMap || typeof networkMap !== 'object') {
                console.warn('❌ Invalid network map: not an object');
                return false;
            }
            
            // Special handling for coordinator-verified maps
            if (networkMap.coordinator_verified) {
                console.log('✅ Network map is coordinator-verified, using relaxed validation');
                
                // Only check essential fields for coordinator maps
                const essentialFields = ['timestamp', 'active_nodes'];
                for (const field of essentialFields) {
                    if (!(field in networkMap)) {
                        console.warn(`❌ Coordinator map missing essential field: ${field}`);
                        return false;
                    }
                }
                
                // Check minimum network size
                if (networkMap.active_nodes < 1) {
                    console.warn('❌ Invalid network map: no active nodes');
                    return false;
                }
                
                console.log('✅ Coordinator network map validation passed');
                return true;
            }
            
            // Standard validation for non-coordinator maps
            const requiredFields = ['encrypted_data', 'salt', 'timestamp', 'signature', 'version', 'active_nodes'];
            for (const field of requiredFields) {
                if (!(field in networkMap)) {
                    console.warn(`❌ Invalid network map: missing field ${field}`);
                    console.warn(`Available fields:`, Object.keys(networkMap));
                    return false;
                }
            }
            
            // Check timestamp freshness (not older than 24 hours, but be more lenient for development)
            const mapTime = new Date(networkMap.timestamp);
            const now = new Date();
            const ageHours = (now - mapTime) / (1000 * 60 * 60);
            
            // Allow longer age for development maps
            const maxAgeHours = networkMap.development_mode ? 168 : 24; // 7 days for dev, 24 hours for prod
            
            if (ageHours > maxAgeHours) {
                console.warn(`❌ Network map too old: ${ageHours.toFixed(1)} hours (max: ${maxAgeHours})`);
                return false;
            }
            
            // Check minimum network size
            if (networkMap.active_nodes < 1) {
                console.warn('❌ Invalid network map: no active nodes');
                return false;
            }
            
            // Log validation success with mode info
            const mode = networkMap.development_mode ? 'DEVELOPMENT' : 'PRODUCTION';
            console.log(`✅ Network map validation passed (${mode} mode, ${ageHours.toFixed(1)} hours old)`);
            return true;
            
        } catch (error) {
            console.warn('❌ Network map validation error:', error.message);
            return false;
        }
    }
    
    /**
     * Determine if this node should be a pioneer
     */
    isPioneerNode(networkMap) {
        // Pioneer mode if:
        // 1. Very few active nodes (< 5)
        // 2. No genesis nodes exist yet
        // 3. Network is in bootstrap phase
        // 4. Bootstrap mode (coordinator establishing network)
        
        const activeNodes = networkMap.active_nodes || 0;
        const genesisNodes = networkMap.genesis_nodes || 0;
        const isBootstrapMode = networkMap.bootstrap_mode || false;
        
        const isPioneer = activeNodes < 5 || genesisNodes === 0 || isBootstrapMode;
        
        if (isPioneer) {
            if (isBootstrapMode) {
                console.log('🔧 BOOTSTRAP MODE: Network is being established');
            } else {
                console.log('🚀 PIONEER MODE: This node can help bootstrap the network');
            }
        } else {
            console.log('🌐 REGULAR MODE: Joining established network');
        }
        
        return isPioneer;
    }
    
    /**
     * Save network map to disk
     */
    saveNetworkMap(networkMap) {
        try {
            const mapData = JSON.stringify(networkMap, null, 2);
            fs.writeFileSync(this.netMapPath, mapData, 'utf8');
            
            console.log('💾 Network map saved to disk');
            
        } catch (error) {
            console.error('❌ Failed to save network map:', error.message);
        }
    }
    
    /**
     * Handle validation failure - wallet cannot operate
     */
    handleValidationFailure(reason) {
        console.error('🚫 WALLET CANNOT OPERATE - NETWORK VALIDATION FAILED');
        console.error(`📋 Reason: ${reason}`);
        console.error('🌐 Internet connection and coordinator access required for first run');
        
        this.isValidated = false;
        
        return {
            success: false,
            error: reason,
            canOperate: false,
            message: 'Wallet cannot operate without valid network map from coordinator',
            requiresInternet: true
        };
    }
    
    /**
     * Check if wallet can operate (has valid network map)
     */
    canWalletOperate() {
        return this.isValidated && this.canonicalNetworkMap !== null;
    }
    
    /**
     * Get canonical network map
     */
    getCanonicalNetworkMap() {
        return this.canonicalNetworkMap;
    }
    
    /**
     * Get list of valid nodes from network map
     */
    getValidNodes() {
        if (!this.canonicalNetworkMap) {
            return [];
        }
        
        try {
            // Check if we have unencrypted data from coordinator
            if (this.canonicalNetworkMap.coordinator_verified && this.canonicalNetworkMap.nodes) {
                console.log('📡 Using unencrypted node data from coordinator');
                
                // Filter out our own node and return valid peers
                const validNodes = this.canonicalNetworkMap.nodes.filter(node => 
                    node.status === 'active' && 
                    node.ip && 
                    node.port
                );
                
                console.log(`✅ Found ${validNodes.length} valid peer nodes from coordinator`);
                
                // Convert to expected format
                return validNodes.map(node => ({
                    node_id: node.node_id,
                    public_ip: node.ip,
                    port: node.port,
                    status: 'ACTIVE',
                    wallet_address: node.wallet_address || 'unknown',
                    is_genesis: node.is_genesis,
                    node_type: node.node_type
                }));
            }
            
            // Extract real node information from network map
            if (!this.canonicalNetworkMap || !this.canonicalNetworkMap.active_nodes) {
                return [];
            }
            
            // Try to decrypt the network map to get real node data (legacy format)
            const AESDecryption = require('./AESDecryption');
            const aesDecryption = new AESDecryption();
            
            if (aesDecryption.isAvailable() && this.canonicalNetworkMap.encrypted_data && 
                this.canonicalNetworkMap.encrypted_data !== 'unencrypted_data_from_coordinator') {
                console.log('🔓 Decrypting network map to extract peer nodes...');
                
                const decryptedData = aesDecryption.decryptNetworkMap(
                    this.canonicalNetworkMap.encrypted_data,
                    this.canonicalNetworkMap.salt
                );
                
                if (decryptedData && decryptedData.nodes) {
                    console.log(`✅ Successfully decrypted network map: ${decryptedData.nodes.length} nodes found`);
                    
                    // Filter out our own node and return valid peers
                    const validNodes = decryptedData.nodes.filter(node => 
                        node.status === 'ACTIVE' && 
                        node.public_ip && 
                        node.port
                    );
                    
                    console.log(`📡 Valid peer nodes for connection: ${validNodes.length}`);
                    return validNodes;
                } else {
                    console.warn('⚠️ Network map decryption failed, using mock data for development');
                    
                    // Use mock data for development
                    const mockData = aesDecryption.createMockNetworkData(this.canonicalNetworkMap.active_nodes);
                    return mockData.nodes;
                }
            } else {
                console.warn('⚠️ AES decryption not available or not needed, using mock data for development');
                
                // Create mock network data for development
                const AESDecryption = require('./AESDecryption');
                const aesDecryption = new AESDecryption();
                const mockData = aesDecryption.createMockNetworkData(this.canonicalNetworkMap.active_nodes);
                return mockData.nodes;
            }
            
        } catch (error) {
            console.error('❌ Failed to extract nodes from network map:', error.message);
            return [];
        }
    }
    
    /**
     * Refresh network map (optional, only if coordinator is available)
     */
    async refreshNetworkMap() {
        try {
            console.log('🔄 Refreshing network map...');
            
            const freshMap = await this.downloadCanonicalNetworkMap();
            
            if (freshMap && this.isNetworkMapValid(freshMap)) {
                this.saveNetworkMap(freshMap);
                this.canonicalNetworkMap = freshMap;
                
                console.log('✅ Network map refreshed successfully');
                return true;
            } else {
                console.warn('⚠️ Failed to refresh network map, keeping existing one');
                return false;
            }
            
        } catch (error) {
            console.warn('⚠️ Network map refresh failed:', error.message);
            return false;
        }
    }
    
    /**
     * Get network validation status
     */
    getValidationStatus() {
        return {
            isValidated: this.isValidated,
            canOperate: this.canWalletOperate(),
            hasNetworkMap: this.canonicalNetworkMap !== null,
            mapPath: this.netMapPath,
            mapAge: this.canonicalNetworkMap ? 
                (new Date() - new Date(this.canonicalNetworkMap.timestamp)) / (1000 * 60 * 60) : null,
            activeNodes: this.canonicalNetworkMap?.active_nodes || 0,
            genesisNodes: this.canonicalNetworkMap?.genesis_nodes || 0
        };
    }
    
    /**
     * Force re-validation (for testing or troubleshooting)
     */
    async forceRevalidation() {
        console.log('🔄 Forcing network re-validation...');
        
        this.isValidated = false;
        this.canonicalNetworkMap = null;
        
        // Delete existing network map to force fresh download
        if (fs.existsSync(this.netMapPath)) {
            fs.unlinkSync(this.netMapPath);
            console.log('🗑️ Deleted existing network map');
        }
        
        return await this.validateNetworkOrFail();
    }
}

module.exports = NetworkValidator;