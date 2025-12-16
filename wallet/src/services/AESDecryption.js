/**
 * AES Decryption Utility for Network Map
 * 
 * Handles decryption of network maps using AES certificates
 * installed by the coordinator setup process.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class AESDecryption {
    constructor() {
        this.certificatePath = path.join(process.cwd(), '.AES_certificate');
        this.masterKey = null;
        this.certificateInfo = null;
        
        this.loadCertificate();
    }
    
    /**
     * Load AES certificate from disk
     */
    loadCertificate() {
        try {
            // Load certificate info
            const certInfoPath = path.join(this.certificatePath, 'certificate_info.json');
            if (fs.existsSync(certInfoPath)) {
                this.certificateInfo = JSON.parse(fs.readFileSync(certInfoPath, 'utf8'));
                console.log('✅ AES certificate info loaded');
            } else {
                console.warn('⚠️ AES certificate info not found');
                return;
            }
            
            // Load master key
            const masterKeyPath = path.join(this.certificatePath, 'master_key.bin');
            if (fs.existsSync(masterKeyPath)) {
                this.masterKey = fs.readFileSync(masterKeyPath);
                console.log('✅ AES master key loaded');
            } else {
                console.warn('⚠️ AES master key not found');
                return;
            }
            
            console.log('🔐 AES decryption ready');
            
        } catch (error) {
            console.error('❌ Failed to load AES certificate:', error.message);
        }
    }
    
    /**
     * Check if AES decryption is available
     */
    isAvailable() {
        return this.masterKey !== null && this.certificateInfo !== null;
    }
    
    /**
     * Decrypt network map data
     * @param {string} encryptedData - Hex-encoded encrypted data
     * @param {string} salt - Hex-encoded salt
     * @returns {Object|null} Decrypted network map data or null
     */
    decryptNetworkMap(encryptedData, salt) {
        if (!this.isAvailable()) {
            console.warn('⚠️ AES decryption not available - certificates not loaded');
            return null;
        }
        
        try {
            console.log('🔓 Attempting to decrypt network map...');
            
            // Convert base64 strings to buffers (server sends base64, not hex)
            const encryptedBuffer = Buffer.from(encryptedData, 'base64');
            const saltBuffer = salt ? Buffer.from(salt, 'base64') : null;
            
            // For AES-256-GCM, we need to extract the IV and auth tag
            // Assuming format: IV (12 bytes) + encrypted data + auth tag (16 bytes)
            const ivLength = 12;
            const tagLength = 16;
            
            if (encryptedBuffer.length < ivLength + tagLength) {
                throw new Error('Encrypted data too short');
            }
            
            const iv = encryptedBuffer.slice(0, ivLength);
            const tag = encryptedBuffer.slice(-tagLength);
            const ciphertext = encryptedBuffer.slice(ivLength, -tagLength);
            
            // Create decipher
            const decipher = crypto.createDecipheriv('aes-256-gcm', this.masterKey, iv);
            decipher.setAuthTag(tag);
            
            // Decrypt
            let decrypted = decipher.update(ciphertext, null, 'utf8');
            decrypted += decipher.final('utf8');
            
            // Parse JSON
            const networkData = JSON.parse(decrypted);
            
            console.log('✅ Network map decrypted successfully');
            console.log(`📊 Decrypted data contains ${networkData.nodes ? networkData.nodes.length : 0} nodes`);
            
            return networkData;
            
        } catch (error) {
            console.error('❌ Network map decryption failed:', error.message);
            
            // Try alternative decryption method (simple AES-256-CBC)
            return this.tryAlternativeDecryption(encryptedData, salt);
        }
    }
    
    /**
     * Try alternative decryption method (AES-256-CBC)
     * @param {string} encryptedData - Hex-encoded encrypted data
     * @param {string} salt - Hex-encoded salt
     * @returns {Object|null} Decrypted network map data or null
     */
    tryAlternativeDecryption(encryptedData, salt) {
        try {
            console.log('🔄 Trying alternative decryption method (AES-256-CBC)...');
            
            const encryptedBuffer = Buffer.from(encryptedData, 'base64');
            const saltBuffer = salt ? Buffer.from(salt, 'base64') : null;
            
            // Assume IV is first 16 bytes for CBC
            const ivLength = 16;
            
            if (encryptedBuffer.length < ivLength) {
                throw new Error('Encrypted data too short for CBC');
            }
            
            const iv = encryptedBuffer.slice(0, ivLength);
            const ciphertext = encryptedBuffer.slice(ivLength);
            
            // Create decipher
            const decipher = crypto.createDecipheriv('aes-256-cbc', this.masterKey, iv);
            
            // Decrypt
            let decrypted = decipher.update(ciphertext, null, 'utf8');
            decrypted += decipher.final('utf8');
            
            // Parse JSON
            const networkData = JSON.parse(decrypted);
            
            console.log('✅ Network map decrypted with alternative method');
            console.log(`📊 Decrypted data contains ${networkData.nodes ? networkData.nodes.length : 0} nodes`);
            
            return networkData;
            
        } catch (error) {
            console.error('❌ Alternative decryption also failed:', error.message);
            return null;
        }
    }
    
    /**
     * Create mock decrypted network data for development
     * @param {number} activeNodes - Number of active nodes from network map
     * @returns {Object} Mock network data
     */
    createMockNetworkData(activeNodes = 2) {
        console.log('🔧 Creating mock network data for development');
        
        const nodes = [];
        
        // Create mock nodes based on active node count
        for (let i = 0; i < activeNodes; i++) {
            nodes.push({
                node_id: `mock_node_${i + 1}`,
                public_ip: i === 0 ? '127.0.0.1' : '127.0.0.1', // Both on localhost for testing
                port: 18080 + i, // Different ports
                node_type: 'GENESIS',
                is_genesis: true,
                status: 'ACTIVE',
                latitude: 40.4168 + (i * 0.001),
                longitude: -3.7038 + (i * 0.001),
                last_seen: new Date().toISOString()
            });
        }
        
        return {
            nodes: nodes,
            total_nodes: activeNodes,
            active_nodes: activeNodes,
            genesis_nodes: activeNodes,
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = AESDecryption;