/**
 * Guided Bootstrap Manager
 * 
 * Implements intelligent bootstrap using Network Coordinator data.
 * Prioritizes connections to known active nodes from the network map
 * before falling back to expensive network scanning.
 */

const EventEmitter = require('events');
const { BootstrapLogger } = require('./BootstrapLogger');

/**
 * Bootstrap strategy types
 */
const BootstrapStrategy = {
  COORDINATOR_GUIDED: 'coordinator_guided',
  NETWORK_SCAN: 'network_scan',
  HYBRID: 'hybrid'
};

/**
 * Connection attempt result
 */
class ConnectionAttempt {
  constructor(nodeId, address, port, success = false, error = null, latency = null) {
    this.nodeId = nodeId;
    this.address = address;
    this.port = port;
    this.success = success;
    this.error = error;
    this.latency = latency;
    this.timestamp = Date.now();
  }
}

class GuidedBootstrapManager extends EventEmitter {
  constructor(networkCoordinatorClient, peerDiscoveryManager) {
    super();
    
    this.networkCoordinatorClient = networkCoordinatorClient;
    this.peerDiscoveryManager = peerDiscoveryManager;
    this.logger = new BootstrapLogger('GuidedBootstrapManager');
    
    // Configuration
    this.config = {
      maxCoordinatorNodes: 10,
      connectionTimeout: 8000,
      maxConcurrentConnections: 5,
      coordinatorRetryDelay: 2000,
      fallbackToScanDelay: 15000,
      proximityWeight: 0.7, // Weight for geographic proximity
      latencyWeight: 0.3,   // Weight for network latency
      maxDistanceKm: 1000   // Maximum distance for coordinator nodes
    };
    
    // State
    this.currentStrategy = BootstrapStrategy.COORDINATOR_GUIDED;
    this.networkMap = null;
    this.lastMapUpdate = null;
    this.connectionAttempts = [];
    this.connectedNodes = new Map();
    this.isBootstrapping = false;
    
    this.logger.info('GuidedBootstrapManager initialized');
  }
  
  /**
   * Start guided bootstrap process
   * @param {string} walletAddress - Local wallet address
   * @param {Object} options - Bootstrap options
   * @returns {Promise<Array>} Connected peers
   */
  async startGuidedBootstrap(walletAddress, options = {}) {
    if (this.isBootstrapping) {
      this.logger.warn('Bootstrap already in progress');
      return Array.from(this.connectedNodes.values());
    }
    
    this.isBootstrapping = true;
    this.logger.info('Starting guided bootstrap process');
    
    try {
      // Step 1: Get fresh network map from coordinator
      this.emit('bootstrapPhaseChanged', 'fetching_network_map');
      const networkMap = await this.fetchNetworkMap();
      
      if (networkMap && networkMap.nodes && networkMap.nodes.length > 0) {
        this.logger.info(`Network map contains ${networkMap.nodes.length} active nodes`);
        
        // Step 2: Try coordinator-guided connections first
        this.emit('bootstrapPhaseChanged', 'coordinator_guided');
        const coordinatorPeers = await this.attemptCoordinatorGuidedConnections(networkMap, walletAddress);
        
        if (coordinatorPeers.length > 0) {
          this.logger.info(`Successfully connected to ${coordinatorPeers.length} nodes via coordinator guidance`);
          this.emit('bootstrapCompleted', coordinatorPeers, BootstrapStrategy.COORDINATOR_GUIDED);
          return coordinatorPeers;
        }
      }
      
      // Step 3: Fallback to network scanning if coordinator guidance fails
      this.logger.info('Coordinator guidance failed, falling back to network scanning');
      this.emit('bootstrapPhaseChanged', 'network_scan_fallback');
      
      const scanPeers = await this.fallbackToNetworkScan(walletAddress);
      
      this.emit('bootstrapCompleted', scanPeers, BootstrapStrategy.NETWORK_SCAN);
      return scanPeers;
      
    } catch (error) {
      this.logger.error('Guided bootstrap failed:', error);
      this.emit('bootstrapFailed', error);
      throw error;
    } finally {
      this.isBootstrapping = false;
    }
  }
  
  /**
   * Fetch network map from coordinator
   * @returns {Promise<Object|null>} Network map or null
   */
  async fetchNetworkMap() {
    try {
      this.logger.info('Fetching network map from coordinator');
      
      const networkMap = await this.networkCoordinatorClient.getNetworkMap(
        this.config.maxDistanceKm,
        this.config.maxCoordinatorNodes
      );
      
      if (networkMap) {
        this.networkMap = networkMap;
        this.lastMapUpdate = new Date();
        
        this.logger.info(`Network map updated: ${networkMap.active_nodes} active nodes`);
        this.emit('networkMapUpdated', networkMap);
        
        return networkMap;
      } else {
        this.logger.warn('Failed to fetch network map from coordinator');
        return null;
      }
      
    } catch (error) {
      this.logger.error('Error fetching network map:', error);
      return null;
    }
  }
  
  /**
   * Attempt connections to nodes from coordinator network map
   * @param {Object} networkMap - Network map from coordinator
   * @param {string} walletAddress - Local wallet address
   * @returns {Promise<Array>} Successfully connected peers
   */
  async attemptCoordinatorGuidedConnections(networkMap, walletAddress) {
    const connectedPeers = [];
    
    try {
      // Sort nodes by proximity and reliability
      const sortedNodes = this.sortNodesByPriority(networkMap.nodes);
      
      this.logger.info(`Attempting connections to ${sortedNodes.length} coordinator nodes`);
      
      // Attempt connections in batches
      for (let i = 0; i < sortedNodes.length; i += this.config.maxConcurrentConnections) {
        const batch = sortedNodes.slice(i, i + this.config.maxConcurrentConnections);
        
        const batchPromises = batch.map(node => 
          this.attemptNodeConnection(node, walletAddress)
        );
        
        const batchResults = await Promise.allSettled(batchPromises);
        
        for (let j = 0; j < batchResults.length; j++) {
          const result = batchResults[j];
          const node = batch[j];
          
          if (result.status === 'fulfilled' && result.value) {
            connectedPeers.push(result.value);
            this.connectedNodes.set(node.node_id, result.value);
            
            this.logger.info(`Successfully connected to coordinator node: ${node.node_id} at ${node.public_ip}:${node.port}`);
            this.emit('nodeConnected', result.value, 'coordinator');
          } else {
            const error = result.reason || new Error('Connection failed');
            this.recordConnectionAttempt(node.node_id, node.public_ip, node.port, false, error);
            
            this.logger.debug(`Failed to connect to coordinator node ${node.node_id}: ${error.message}`);
          }
        }
        
        // If we have enough connections, we can stop
        if (connectedPeers.length >= 2) {
          this.logger.info(`Sufficient connections established (${connectedPeers.length}), stopping coordinator guidance`);
          break;
        }
        
        // Small delay between batches
        if (i + this.config.maxConcurrentConnections < sortedNodes.length) {
          await this.sleep(500);
        }
      }
      
      return connectedPeers;
      
    } catch (error) {
      this.logger.error('Error during coordinator-guided connections:', error);
      return connectedPeers;
    }
  }
  
  /**
   * Sort nodes by priority (proximity, latency, reliability)
   * @param {Array} nodes - Nodes from network map
   * @returns {Array} Sorted nodes
   */
  sortNodesByPriority(nodes) {
    if (!nodes || !Array.isArray(nodes)) {
      return [];
    }
    
    // Get our current location for proximity calculation
    const ourLocation = this.getCurrentLocation();
    
    return nodes
      .filter(node => this.isValidCoordinatorNode(node))
      .map(node => ({
        ...node,
        priority: this.calculateNodePriority(node, ourLocation)
      }))
      .sort((a, b) => b.priority - a.priority); // Higher priority first
  }
  
  /**
   * Calculate node priority based on proximity and other factors
   * @param {Object} node - Node from network map
   * @param {Object} ourLocation - Our current location
   * @returns {number} Priority score (higher is better)
   */
  calculateNodePriority(node, ourLocation) {
    let priority = 0;
    
    // Proximity score (closer is better)
    if (node.latitude && node.longitude && ourLocation.latitude && ourLocation.longitude) {
      const distance = this.calculateDistance(
        ourLocation.latitude, ourLocation.longitude,
        node.latitude, node.longitude
      );
      
      // Normalize distance to 0-1 scale (closer = higher score)
      const maxDistance = this.config.maxDistanceKm;
      const proximityScore = Math.max(0, 1 - (distance / maxDistance));
      priority += proximityScore * this.config.proximityWeight;
    }
    
    // Latency score (lower latency is better)
    if (node.network_latency !== undefined) {
      // Normalize latency (assume max 500ms, lower = higher score)
      const latencyScore = Math.max(0, 1 - (node.network_latency / 500));
      priority += latencyScore * this.config.latencyWeight;
    }
    
    // Reliability factors
    if (node.uptime_percentage) {
      priority += (node.uptime_percentage / 100) * 0.2;
    }
    
    if (node.connected_peers) {
      // Nodes with more peers are more valuable
      priority += Math.min(node.connected_peers / 10, 0.5) * 0.1;
    }
    
    // Prefer nodes that are actively mining
    if (node.mining_active) {
      priority += 0.1;
    }
    
    return priority;
  }
  
  /**
   * Check if coordinator node is valid for connection
   * @param {Object} node - Node from network map
   * @returns {boolean} True if valid
   */
  isValidCoordinatorNode(node) {
    if (!node || !node.node_id || !node.public_ip || !node.port) {
      return false;
    }
    
    // Skip our own node
    if (node.node_id === this.networkCoordinatorClient.nodeId) {
      return false;
    }
    
    // Validate IP address
    if (!this.isValidIpAddress(node.public_ip)) {
      return false;
    }
    
    // Check if node is recently active
    if (node.last_seen) {
      const lastSeenTime = new Date(node.last_seen);
      const timeDiff = Date.now() - lastSeenTime.getTime();
      const maxAge = 30 * 60 * 1000; // 30 minutes
      
      if (timeDiff > maxAge) {
        return false;
      }
    }
    
    return true;
  }
  
  /**
   * Attempt connection to a specific coordinator node
   * @param {Object} node - Node from network map
   * @param {string} walletAddress - Local wallet address
   * @returns {Promise<Object|null>} Connected peer info or null
   */
  async attemptNodeConnection(node, walletAddress) {
    const startTime = Date.now();
    
    try {
      this.logger.debug(`Attempting connection to coordinator node: ${node.node_id} at ${node.public_ip}:${node.port}`);
      
      // Create peer info from coordinator node data
      const peerInfo = {
        id: node.node_id,
        address: node.public_ip,
        port: node.port,
        walletAddress: node.wallet_address || '',
        networkMode: node.network_mode || 'testnet',
        isReady: node.mining_active || false,
        capabilities: ['p2p-discovery', 'genesis-creation'],
        coordinatorNode: true,
        lastSeen: node.last_seen,
        connectedPeers: node.connected_peers || 0
      };
      
      // Validate the peer connection
      const isValid = await this.peerDiscoveryManager.validatePeerConnection(peerInfo);
      if (!isValid) {
        throw new Error('Peer validation failed');
      }
      
      // Establish connection
      const connection = await this.peerDiscoveryManager.establishConnection(peerInfo);
      
      const latency = Date.now() - startTime;
      this.recordConnectionAttempt(node.node_id, node.public_ip, node.port, true, null, latency);
      
      this.logger.info(`Connected to coordinator node ${node.node_id} (latency: ${latency}ms)`);
      
      return peerInfo;
      
    } catch (error) {
      const latency = Date.now() - startTime;
      this.recordConnectionAttempt(node.node_id, node.public_ip, node.port, false, error, latency);
      
      this.logger.debug(`Failed to connect to coordinator node ${node.node_id}: ${error.message}`);
      return null;
    }
  }
  
  /**
   * Fallback to traditional network scanning
   * @param {string} walletAddress - Local wallet address
   * @returns {Promise<Array>} Discovered peers
   */
  async fallbackToNetworkScan(walletAddress) {
    try {
      this.logger.info('Starting fallback network scan');
      
      // Add delay before scanning to avoid overwhelming the network
      await this.sleep(this.config.fallbackToScanDelay);
      
      // Use existing peer discovery manager for scanning
      const discoveredPeers = await this.peerDiscoveryManager.scanForPeers();
      
      this.logger.info(`Network scan completed: ${discoveredPeers.length} peers discovered`);
      
      return discoveredPeers;
      
    } catch (error) {
      this.logger.error('Network scan fallback failed:', error);
      return [];
    }
  }
  
  /**
   * Record connection attempt for analytics
   * @param {string} nodeId - Node ID
   * @param {string} address - IP address
   * @param {number} port - Port number
   * @param {boolean} success - Whether connection succeeded
   * @param {Error|null} error - Error if failed
   * @param {number|null} latency - Connection latency
   */
  recordConnectionAttempt(nodeId, address, port, success, error, latency) {
    const attempt = new ConnectionAttempt(nodeId, address, port, success, error, latency);
    this.connectionAttempts.push(attempt);
    
    // Keep only last 100 attempts
    if (this.connectionAttempts.length > 100) {
      this.connectionAttempts = this.connectionAttempts.slice(-100);
    }
    
    this.emit('connectionAttempt', attempt);
  }
  
  /**
   * Get current location (placeholder - should integrate with NetworkCoordinatorClient)
   * @returns {Object} Current location
   */
  getCurrentLocation() {
    // This should integrate with NetworkCoordinatorClient.getCurrentLocation()
    // For now, return a default location
    return {
      latitude: 40.4168,
      longitude: -3.7038
    };
  }
  
  /**
   * Calculate distance between two coordinates
   * @param {number} lat1 - Latitude 1
   * @param {number} lon1 - Longitude 1
   * @param {number} lat2 - Latitude 2
   * @param {number} lon2 - Longitude 2
   * @returns {number} Distance in kilometers
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
  
  /**
   * Convert degrees to radians
   * @param {number} degrees - Degrees
   * @returns {number} Radians
   */
  toRadians(degrees) {
    return degrees * (Math.PI / 180);
  }
  
  /**
   * Validate IP address format
   * @param {string} ip - IP address
   * @returns {boolean} True if valid
   */
  isValidIpAddress(ip) {
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(ip)) {
      return false;
    }
    
    const parts = ip.split('.').map(Number);
    return parts.every(part => part >= 0 && part <= 255);
  }
  
  /**
   * Sleep utility
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise<void>}
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  /**
   * Get bootstrap statistics
   * @returns {Object} Bootstrap statistics
   */
  getBootstrapStats() {
    const totalAttempts = this.connectionAttempts.length;
    const successfulAttempts = this.connectionAttempts.filter(a => a.success).length;
    const averageLatency = this.connectionAttempts
      .filter(a => a.success && a.latency)
      .reduce((sum, a, _, arr) => sum + a.latency / arr.length, 0);
    
    return {
      strategy: this.currentStrategy,
      totalConnectionAttempts: totalAttempts,
      successfulConnections: successfulAttempts,
      successRate: totalAttempts > 0 ? (successfulAttempts / totalAttempts) : 0,
      averageLatency: Math.round(averageLatency),
      connectedNodes: this.connectedNodes.size,
      lastMapUpdate: this.lastMapUpdate,
      networkMapNodes: this.networkMap ? this.networkMap.active_nodes : 0
    };
  }
  
  /**
   * Reset the guided bootstrap manager
   */
  reset() {
    this.logger.info('Resetting guided bootstrap manager');
    
    this.isBootstrapping = false;
    this.connectionAttempts = [];
    this.connectedNodes.clear();
    this.networkMap = null;
    this.lastMapUpdate = null;
    
    this.emit('reset');
  }
  
  /**
   * Cleanup resources
   */
  cleanup() {
    this.logger.info('Cleaning up guided bootstrap manager');
    
    this.reset();
    this.removeAllListeners();
  }
}

module.exports = {
  GuidedBootstrapManager,
  BootstrapStrategy,
  ConnectionAttempt
};