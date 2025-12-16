/**
 * Peer Discovery Manager for Auto-Bootstrap P2P Network
 * 
 * Handles P2P network scanning and peer identification in both testnet and mainnet modes.
 * Implements IP range scanning for testnet (local networks) and public IP discovery for mainnet.
 */

const EventEmitter = require('events');
const { BootstrapLogger } = require('./BootstrapLogger');

/**
 * Network modes for peer discovery
 */
const NetworkMode = {
  TESTNET: 'testnet',
  MAINNET: 'mainnet'
};

/**
 * Peer information structure
 */
class PeerInfo {
  constructor(id, address, port, walletAddress, networkMode, isReady = false, capabilities = []) {
    this.id = id;
    this.address = address;
    this.port = port;
    this.walletAddress = walletAddress;
    this.networkMode = networkMode;
    this.isReady = isReady;
    this.capabilities = capabilities;
    this.lastSeen = Date.now();
  }
}

/**
 * Network connection wrapper
 */
class Connection {
  constructor(socket, peer) {
    this.socket = socket;
    this.peer = peer;
    this.isConnected = true;
    this.lastActivity = Date.now();
  }

  close() {
    if (this.socket && this.isConnected) {
      this.socket.destroy();
      this.isConnected = false;
    }
  }
}

class PeerDiscoveryManager extends EventEmitter {
  constructor(networkMode = NetworkMode.TESTNET) {
    super();
    
    this.networkMode = networkMode;
    this.logger = new BootstrapLogger('PeerDiscoveryManager');
    
    // Discovery configuration
    this.config = {
      scanTimeout: 5000, // 5 seconds per IP
      connectionTimeout: 10000, // 10 seconds for connection establishment
      maxConcurrentScans: 10,
      retryAttempts: 3,
      retryDelay: 1000,
      
      // Testnet configuration
      testnetPorts: [8000, 8001, 8002, 8080, 9000],
      localIpRanges: [
        '192.168.0.0/16',
        '10.0.0.0/8', 
        '172.16.0.0/12',
        '127.0.0.0/8'
      ],
      
      // Mainnet configuration
      mainnetPorts: [8000, 443, 80],
      publicIpServices: [
        'https://api.ipify.org?format=json',
        'https://httpbin.org/ip',
        'https://icanhazip.com'
      ]
    };
    
    // State
    this.discoveredPeers = new Map();
    this.activeConnections = new Map();
    this.isScanning = false;
    this.ownWalletAddress = null;
    
    this.logger.info(`PeerDiscoveryManager initialized for ${networkMode} mode`);
  }

  /**
   * Detect network mode (testnet vs mainnet)
   * @returns {string} NetworkMode.TESTNET or NetworkMode.MAINNET
   */
  detectNetworkMode() {
    // For now, return the configured mode
    // In production, this could detect based on environment, configuration, etc.
    return this.networkMode;
  }

  /**
   * Validate IP address based on network mode
   * @param {string} ipAddress - IP address to validate
   * @returns {boolean} True if valid for current network mode
   */
  validateIpAddress(ipAddress) {
    if (!ipAddress || typeof ipAddress !== 'string') {
      return false;
    }

    // Basic IP format validation
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(ipAddress)) {
      return false;
    }

    const parts = ipAddress.split('.').map(Number);
    if (parts.some(part => part < 0 || part > 255)) {
      return false;
    }

    // Skip reserved IP addresses in both modes
    if (this.isReservedIpAddress(ipAddress)) {
      return false;
    }

    if (this.networkMode === NetworkMode.TESTNET) {
      // Testnet accepts both local/private AND public IP addresses
      return true;
    } else {
      // Mainnet only accepts public IP addresses
      return this.isPublicIpAddress(ipAddress);
    }
  }

  /**
   * Check if IP address is a local/private address
   * @param {string} ipAddress - IP address to check
   * @returns {boolean} True if local/private
   */
  isLocalIpAddress(ipAddress) {
    const parts = ipAddress.split('.').map(Number);
    
    // 127.x.x.x (localhost)
    if (parts[0] === 127) return true;
    
    // 10.x.x.x (Class A private)
    if (parts[0] === 10) return true;
    
    // 172.16.x.x - 172.31.x.x (Class B private)
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;
    
    // 192.168.x.x (Class C private)
    if (parts[0] === 192 && parts[1] === 168) return true;
    
    return false;
  }

  /**
   * Check if IP address is a public address
   * @param {string} ipAddress - IP address to check
   * @returns {boolean} True if public
   */
  isPublicIpAddress(ipAddress) {
    return !this.isLocalIpAddress(ipAddress) && !this.isReservedIpAddress(ipAddress);
  }

  /**
   * Check if IP address is reserved (multicast, broadcast, etc.)
   * @param {string} ipAddress - IP address to check
   * @returns {boolean} True if reserved
   */
  isReservedIpAddress(ipAddress) {
    const parts = ipAddress.split('.').map(Number);
    
    // 0.x.x.x (reserved)
    if (parts[0] === 0) return true;
    
    // 224.x.x.x - 255.x.x.x (multicast and reserved)
    if (parts[0] >= 224) return true;
    
    // 169.254.x.x (link-local)
    if (parts[0] === 169 && parts[1] === 254) return true;
    
    return false;
  }

  /**
   * Generate IP addresses to scan based on network mode
   * @returns {Array<string>} Array of IP addresses to scan
   */
  generateScanTargets() {
    if (this.networkMode === NetworkMode.TESTNET) {
      return this.generateLocalNetworkTargets();
    } else {
      // For mainnet, we would typically use bootstrap nodes or DHT
      // For now, return empty array as mainnet discovery is more complex
      return [];
    }
  }

  /**
   * Generate local network IP addresses for testnet scanning
   * @returns {Array<string>} Array of local IP addresses
   */
  generateLocalNetworkTargets() {
    const targets = [];
    
    // Common local network ranges
    const ranges = [
      { base: '192.168.1', start: 1, end: 254 },
      { base: '192.168.0', start: 1, end: 254 },
      { base: '10.0.0', start: 1, end: 254 },
      { base: '127.0.0', start: 1, end: 10 } // localhost range
    ];
    
    for (const range of ranges) {
      for (let i = range.start; i <= range.end; i++) {
        targets.push(`${range.base}.${i}`);
      }
    }
    
    return targets;
  }

  /**
   * Scan for peers on the network using P2P protocols
   * @param {string} networkMode - Network mode (testnet/mainnet)
   * @returns {Promise<Array<PeerInfo>>} Array of discovered peers
   */
  async scanForPeers(networkMode = this.networkMode) {
    if (this.isScanning) {
      this.logger.warn('Peer scanning already in progress');
      return Array.from(this.discoveredPeers.values());
    }

    this.isScanning = true;
    this.logger.info(`Starting P2P peer scan in ${networkMode} mode`);

    try {
      const scanTargets = this.generateScanTargets();
      const ports = networkMode === NetworkMode.TESTNET ? 
        this.config.testnetPorts : this.config.mainnetPorts;

      this.logger.info(`Scanning ${scanTargets.length} IP addresses on ${ports.length} ports`);

      const discoveredPeers = [];
      const scanPromises = [];

      // Limit concurrent scans
      for (let i = 0; i < scanTargets.length; i += this.config.maxConcurrentScans) {
        const batch = scanTargets.slice(i, i + this.config.maxConcurrentScans);
        
        for (const ip of batch) {
          for (const port of ports) {
            scanPromises.push(this.scanSingleTargetWithRetry(ip, port));
          }
        }

        // Wait for current batch to complete before starting next
        const batchResults = await Promise.allSettled(scanPromises.splice(0, batch.length * ports.length));
        
        for (const result of batchResults) {
          if (result.status === 'fulfilled' && result.value) {
            discoveredPeers.push(result.value);
            this.discoveredPeers.set(result.value.id, result.value);
            
            // Emit peer discovered event for P2P protocol
            this.emit('peerDiscovered', result.value);
          }
        }
      }

      this.logger.info(`P2P peer scan completed. Found ${discoveredPeers.length} peers`);
      
      // Check if we have enough peers for network formation
      this.checkNetworkFormationTrigger(discoveredPeers);
      
      return discoveredPeers;

    } catch (error) {
      this.logger.error('Error during P2P peer scanning:', error);
      throw error;
    } finally {
      this.isScanning = false;
    }
  }

  /**
   * Check if network formation should be triggered
   * @param {Array<PeerInfo>} peers - Discovered peers
   */
  checkNetworkFormationTrigger(peers) {
    const readyPeers = peers.filter(peer => 
      peer.isReady && 
      peer.capabilities.includes('genesis-creation')
    );

    if (readyPeers.length >= 2) {
      this.logger.info(`Network formation trigger: ${readyPeers.length} ready peers found`);
      this.emit('networkFormationTriggered', readyPeers);
    }
  }

  /**
   * Scan a single target with retry and timeout handling
   * @param {string} ip - IP address to scan
   * @param {number} port - Port to scan
   * @returns {Promise<PeerInfo|null>} Discovered peer or null
   */
  async scanSingleTargetWithRetry(ip, port) {
    let lastError = null;
    
    for (let attempt = 0; attempt < this.config.retryAttempts; attempt++) {
      try {
        const result = await this.scanSingleTarget(ip, port);
        if (result) {
          return result;
        }
      } catch (error) {
        lastError = error;
        
        // Apply exponential backoff for retries
        if (attempt < this.config.retryAttempts - 1) {
          const backoffDelay = this.config.retryDelay * Math.pow(2, attempt);
          this.logger.debug(`Retry attempt ${attempt + 1} for ${ip}:${port} after ${backoffDelay}ms`);
          await this.sleep(backoffDelay);
        }
      }
    }
    
    if (lastError) {
      this.logger.debug(`Failed to scan ${ip}:${port} after ${this.config.retryAttempts} attempts: ${lastError.message}`);
    }
    
    return null;
  }

  /**
   * Sleep utility for backoff delays
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise<void>}
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Scan a single IP:port combination for peers
   * @param {string} ip - IP address to scan
   * @param {number} port - Port to scan
   * @returns {Promise<PeerInfo|null>} Discovered peer or null
   */
  async scanSingleTarget(ip, port) {
    // Skip invalid IPs for current network mode
    if (!this.validateIpAddress(ip)) {
      return null;
    }

    try {
      const net = require('net');
      
      return new Promise((resolve) => {
        const socket = new net.Socket();
        let resolved = false;

        const cleanup = () => {
          if (!resolved) {
            resolved = true;
            socket.destroy();
          }
        };

        socket.setTimeout(this.config.scanTimeout);

        socket.on('connect', async () => {
          try {
            // Attempt to perform handshake
            const peerInfo = await this.performHandshake(socket, ip, port);
            cleanup();
            resolve(peerInfo);
          } catch (error) {
            cleanup();
            resolve(null);
          }
        });

        socket.on('error', () => {
          cleanup();
          resolve(null);
        });

        socket.on('timeout', () => {
          cleanup();
          resolve(null);
        });

        socket.connect(port, ip);
      });

    } catch (error) {
      return null;
    }
  }

  /**
   * Perform P2P handshake with discovered peer
   * @param {Socket} socket - Connected socket
   * @param {string} ip - Peer IP address
   * @param {number} port - Peer port
   * @returns {Promise<PeerInfo|null>} Peer information or null
   */
  async performHandshake(socket, ip, port) {
    try {
      // Send P2P handshake request with protocol identification
      const handshakeRequest = {
        type: 'p2p_handshake',
        protocol: 'auto-bootstrap-p2p',
        version: '1.0.0',
        nodeId: `discovery-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        networkMode: this.networkMode,
        capabilities: ['p2p-discovery', 'genesis-creation'],
        walletAddress: this.ownWalletAddress,
        timestamp: Date.now()
      };

      const message = JSON.stringify(handshakeRequest);
      const messageBuffer = Buffer.from(message);
      const lengthBuffer = Buffer.alloc(4);
      lengthBuffer.writeUInt32BE(messageBuffer.length, 0);
      
      socket.write(Buffer.concat([lengthBuffer, messageBuffer]));

      // Wait for P2P response
      return new Promise((resolve, reject) => {
        let buffer = Buffer.alloc(0);
        let expectedLength = null;
        
        const timeout = setTimeout(() => {
          reject(new Error('P2P handshake timeout'));
        }, 5000);

        socket.on('data', (data) => {
          buffer = Buffer.concat([buffer, data]);
          
          try {
            // Read message length if not yet determined
            if (expectedLength === null && buffer.length >= 4) {
              expectedLength = buffer.readUInt32BE(0);
              buffer = buffer.slice(4);
            }
            
            // Check if we have the complete message
            if (expectedLength !== null && buffer.length >= expectedLength) {
              const messageData = buffer.slice(0, expectedLength);
              const response = JSON.parse(messageData.toString());
              
              if (response.type === 'p2p_handshake_response' && 
                  response.protocol === 'auto-bootstrap-p2p' &&
                  response.nodeId) {
                
                clearTimeout(timeout);
                
                const peerInfo = new PeerInfo(
                  response.nodeId,
                  ip,
                  port,
                  response.walletAddress || '',
                  response.networkMode || this.networkMode,
                  response.isReady || false,
                  response.capabilities || ['p2p-discovery']
                );
                
                this.logger.debug(`P2P handshake successful with peer ${response.nodeId} at ${ip}:${port}`);
                resolve(peerInfo);
              } else {
                reject(new Error('Invalid P2P handshake response'));
              }
            }
          } catch (error) {
            clearTimeout(timeout);
            reject(new Error(`P2P handshake parse error: ${error.message}`));
          }
        });

        socket.on('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });

    } catch (error) {
      throw new Error(`P2P handshake failed: ${error.message}`);
    }
  }

  /**
   * Broadcast availability to the network
   * @param {string} walletAddress - Wallet address to broadcast
   */
  broadcastAvailability(walletAddress) {
    this.ownWalletAddress = walletAddress;
    this.logger.info(`Broadcasting availability for wallet: ${walletAddress}`);
    
    // In a real implementation, this would broadcast to known peers
    // For now, we'll emit an event
    this.emit('availabilityBroadcast', {
      walletAddress,
      networkMode: this.networkMode,
      timestamp: Date.now()
    });
  }

  /**
   * Validate peer connection
   * @param {PeerInfo} peer - Peer to validate
   * @returns {Promise<boolean>} True if connection is valid
   */
  async validatePeerConnection(peer) {
    if (!peer || !peer.address || !peer.port) {
      return false;
    }

    // Validate IP address for network mode
    if (!this.validateIpAddress(peer.address)) {
      this.logger.warn(`Invalid IP address for ${this.networkMode}: ${peer.address}`);
      return false;
    }

    // Check network mode compatibility
    if (peer.networkMode && peer.networkMode !== this.networkMode) {
      this.logger.warn(`Network mode mismatch: peer=${peer.networkMode}, local=${this.networkMode}`);
      return false;
    }

    return true;
  }

  /**
   * Establish connection to a peer
   * @param {PeerInfo} peer - Peer to connect to
   * @returns {Promise<Connection>} Established connection
   */
  async establishConnection(peer) {
    if (!await this.validatePeerConnection(peer)) {
      throw new Error(`Invalid peer connection: ${peer.address}:${peer.port}`);
    }

    try {
      const net = require('net');
      const socket = new net.Socket();

      return new Promise((resolve, reject) => {
        socket.setTimeout(this.config.connectionTimeout);

        socket.on('connect', () => {
          const connection = new Connection(socket, peer);
          this.activeConnections.set(peer.id, connection);
          
          this.logger.info(`Established connection to peer ${peer.id} at ${peer.address}:${peer.port}`);
          resolve(connection);
        });

        socket.on('error', (error) => {
          reject(new Error(`Failed to connect to ${peer.address}:${peer.port}: ${error.message}`));
        });

        socket.on('timeout', () => {
          socket.destroy();
          reject(new Error(`Connection timeout to ${peer.address}:${peer.port}`));
        });

        socket.connect(peer.port, peer.address);
      });

    } catch (error) {
      throw new Error(`Connection establishment failed: ${error.message}`);
    }
  }

  /**
   * Get discovered peers
   * @returns {Array<PeerInfo>} Array of discovered peers
   */
  getDiscoveredPeers() {
    return Array.from(this.discoveredPeers.values());
  }

  /**
   * Get active connections
   * @returns {Array<Connection>} Array of active connections
   */
  getActiveConnections() {
    return Array.from(this.activeConnections.values());
  }

  /**
   * Close all connections and cleanup
   */
  cleanup() {
    this.logger.info('Cleaning up peer discovery manager');
    
    // Close all active connections
    for (const connection of this.activeConnections.values()) {
      connection.close();
    }
    
    this.activeConnections.clear();
    this.discoveredPeers.clear();
    this.isScanning = false;
  }
}

module.exports = {
  PeerDiscoveryManager,
  PeerInfo,
  Connection,
  NetworkMode
};