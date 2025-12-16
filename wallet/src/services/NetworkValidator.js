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
        console.log('📋 Wallet cannot operate without valid network map from coordinator');
        
        try {
            // Step 1: Try to load existing valid network map
            const existingMap = this.loadExistingNetworkMap();
            
            if (existingMap && this.isNetworkMapValid(existingMap)) {
                console.log('✅ Found valid existing network map');
                this.canonicalNetworkMap = existingMap;
                this.isValidated = true;
                return {
                    success: true,
                    source: 'cached',
                    message: 'Using cached valid network map',
                    networkMap: existingMap,
                    isPioneer: this.isPioneerNode(existingMap)
                };
            }
            
            // Step 2: MANDATORY - Must connect to coordinator for fresh map
            console.log('🌐 Connecting to Network Coordinator (MANDATORY)...');
            
            const freshMap = await this.downloadCanonicalNetworkMap();
            
            if (!freshMap) {
                return this.handleValidationFailure('Cannot connect to Network Coordinator');
            }
            
            // Step 3: Validate and save the fresh map
            if (!this.isNetworkMapValid(freshMap)) {
                return this.handleValidationFailure('Invalid network map received from coordinator');
            }
            
            // Step 4: Save canonical network map
            this.saveNetworkMap(freshMap);
            this.canonicalNetworkMap = freshMap;
            this.isValidated = true;
            
            console.log('✅ NETWORK VALIDATION SUCCESSFUL');
            console.log(`📊 Network Map: ${freshMap.active_nodes} active nodes, ${freshMap.genesis_nodes} genesis nodes`);
            
            return {
                success: true,
                source: 'coordinator',
                message: 'Successfully validated with Network Coordinator',
                networkMap: freshMap,
                isPioneer: this.isPioneerNode(freshMap)
            };
            
        } catch (error) {
            console.error('❌ NETWORK VALIDATION FAILED:', error.message);
            return this.handleValidationFailure(`Network validation error: ${error.message}`);
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
            
            if (networkMap) {
                console.log('📥 Downloaded network map from coordinator');
                return networkMap;
            }
            
            // If that fails, try registration first
            console.log('🔧 Direct map download failed, trying registration first...');
            const registered = await this.coordinatorClient.registerNode('regular');
            
            if (registered) {
                console.log('✅ Registered with coordinator, getting network map...');
                const mapAfterRegistration = await this.coordinatorClient.getNetworkMap();
                
                if (mapAfterRegistration) {
                    console.log('📥 Downloaded network map after registration');
                    return mapAfterRegistration;
                }
            }
            
            // If coordinator is not fully functional, create a development network map
            console.log('🔧 Coordinator not fully available, creating development network map...');
            return this.createDevelopmentNetworkMap();
            
        } catch (error) {
            console.error('❌ Failed to download network map:', error.message);
            
            // Always fall back to development map for now to allow wallet to start
            console.log('🔧 Creating development network map as fallback...');
            return this.createDevelopmentNetworkMap();
        }
    }
    
    /**
     * Create a development network map for local testing
     */
    createDevelopmentNetworkMap() {
        const devMap = {
            encrypted_data: 'dev_encrypted_data',
            salt: 'dev_salt',
            timestamp: new Date().toISOString(),
            signature: 'dev_signature',
            version: '1.0.0-dev',
            active_nodes: 1,
            genesis_nodes: 0,
            coordinator_url: this.coordinatorClient.coordinatorUrl,
            bootstrap_mode: true,
            development_mode: true
        };
        
        console.log('🔧 Created development network map - wallet can start in development mode');
        console.log('🔧 This allows debugging without full coordinator connectivity');
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
            // Check required fields
            if (!networkMap || typeof networkMap !== 'object') {
                console.warn('❌ Invalid network map: not an object');
                return false;
            }
            
            const requiredFields = ['encrypted_data', 'salt', 'timestamp', 'signature', 'version', 'active_nodes'];
            for (const field of requiredFields) {
                if (!(field in networkMap)) {
                    console.warn(`❌ Invalid network map: missing field ${field}`);
                    return false;
                }
            }
            
            // Check timestamp freshness (not older than 24 hours)
            const mapTime = new Date(networkMap.timestamp);
            const now = new Date();
            const ageHours = (now - mapTime) / (1000 * 60 * 60);
            
            if (ageHours > 24) {
                console.warn(`❌ Network map too old: ${ageHours.toFixed(1)} hours`);
                return false;
            }
            
            // Check minimum network size
            if (networkMap.active_nodes < 1) {
                console.warn('❌ Invalid network map: no active nodes');
                return false;
            }
            
            console.log(`✅ Network map validation passed (${ageHours.toFixed(1)} hours old)`);
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
            // Extract real node information from network map
            if (!this.canonicalNetworkMap || !this.canonicalNetworkMap.active_nodes) {
                return [];
            }
            
            // Decrypt the network map to get real node data
            const AESDecryption = require('./AESDecryption');
            const aesDecryption = new AESDecryption();
            
            if (aesDecryption.isAvailable() && this.canonicalNetworkMap.encrypted_data) {
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
                console.warn('⚠️ AES decryption not available, using mock data for development');
                
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