/**
 * Auto-Bootstrap P2P Network Service
 * 
 * Manages the automatic bootstrap process for establishing a P2P blockchain network.
 * Handles state transitions from pioneer mode through peer discovery to network formation.
 */

const EventEmitter = require('events');
const { BootstrapLogger, BootstrapErrorHandler } = require('./BootstrapLogger');
const { UserFeedbackManager } = require('./UserFeedbackManager');
const { PeerDiscoveryManager, NetworkMode: PeerNetworkMode } = require('./PeerDiscoveryManager');

/**
 * Bootstrap state machine modes
 */
const BootstrapMode = {
  PIONEER: 'pioneer',
  DISCOVERY: 'discovery', 
  GENESIS: 'genesis',
  NETWORK: 'network'
};

/**
 * Network modes for peer discovery
 */
const NetworkMode = {
  TESTNET: 'testnet',
  MAINNET: 'mainnet'
};

/**
 * Bootstrap error types
 */
const BootstrapErrorType = {
  NETWORK_TIMEOUT: 'network_timeout',
  PEER_DISCONNECTION: 'peer_disconnection',
  GENESIS_FAILURE: 'genesis_failure',
  INVALID_PEER: 'invalid_peer',
  INSUFFICIENT_PEERS: 'insufficient_peers'
};

class BootstrapService extends EventEmitter {
  constructor() {
    super();
    
    // Initialize bootstrap state
    this.state = {
      mode: BootstrapMode.PIONEER,
      walletAddress: null,
      selectedModel: null,
      discoveredPeers: [],
      genesisBlock: null,
      networkConfig: null,
      lastError: null,
      isReady: false
    };
    
    // Configuration
    this.config = {
      peerDiscoveryTimeout: 30000, // 30 seconds
      genesisCreationTimeout: 60000, // 60 seconds
      maxRetries: 3,
      retryBackoffMs: 1000,
      minPeersForGenesis: 2,
      networkMode: NetworkMode.TESTNET
    };
    
    // Feature availability during bootstrap
    this.restrictedFeatures = new Set([
      'send_transaction',
      'mining_operations',
      'consensus_participation',
      'block_validation'
    ]);
    
    // Logging and error handling
    this.logger = new BootstrapLogger('BootstrapService');
    this.errorHandler = new BootstrapErrorHandler(this.logger);
    
    // User feedback manager
    this.feedbackManager = new UserFeedbackManager();
    
    // P2P peer discovery manager
    this.peerDiscoveryManager = new PeerDiscoveryManager(this.config.networkMode);
    this.setupPeerDiscoveryListeners();
    
    // Discovery timing
    this.discoveryStartTime = null;
    
    this.logger.info('BootstrapService initialized in pioneer mode');
  }
  
  /**
   * Initialize pioneer mode - entry point for new installations
   */
  async initializePioneerMode() {
    try {
      this.logger.info('Initializing pioneer mode...');
      
      this.setState({
        mode: BootstrapMode.PIONEER,
        isReady: false,
        lastError: null
      });
      
      this.emit('stateChanged', this.state);
      this.emit('pioneerModeInitialized');
      
      this.logger.info('Pioneer mode initialized successfully');
      
    } catch (error) {
      this.handleError(BootstrapErrorType.GENESIS_FAILURE, 'Failed to initialize pioneer mode', error);
      throw error;
    }
  }
  
  /**
   * Handle wallet address creation
   * @param {string} address - The created wallet address
   */
  onWalletAddressCreated(address) {
    if (!address || typeof address !== 'string') {
      throw new Error('Invalid wallet address provided');
    }
    
    this.logger.info(`Wallet address created: ${address}`);
    
    this.setState({
      walletAddress: address
    });
    
    this.emit('walletAddressCreated', address);
    this.checkReadinessForDiscovery();
  }
  
  /**
   * Handle mining readiness (AI model selected and prepared)
   * @param {string} modelPath - Path to the prepared AI model
   * @param {Object} modelInfo - Additional model information
   */
  onMiningReadiness(modelPath, modelInfo = {}) {
    if (!modelPath || typeof modelPath !== 'string') {
      throw new Error('Invalid model path provided');
    }
    
    this.logger.info(`Mining readiness achieved with model: ${modelPath}`);
    
    this.setState({
      selectedModel: modelPath,
      modelInfo: {
        path: modelPath,
        id: modelInfo.id || 'unknown',
        name: modelInfo.name || 'Unknown Model',
        preparedAt: new Date().toISOString(),
        ...modelInfo
      },
      isReady: true
    });
    
    this.emit('miningReadiness', {
      modelPath,
      modelInfo: this.state.modelInfo
    });
    
    this.checkReadinessForDiscovery();
  }
  
  /**
   * Check if ready to start peer discovery
   */
  checkReadinessForDiscovery() {
    if (this.state.walletAddress && this.state.selectedModel && this.state.isReady) {
      this.logger.info('All prerequisites met, ready for peer discovery');
      this.emit('readyForDiscovery');
      
      // Trigger network availability broadcasting
      this.broadcastAvailability(this.state.walletAddress);
    }
  }
  
  /**
   * Broadcast availability to the P2P network
   * @param {string} walletAddress - Wallet address to broadcast
   */
  broadcastAvailability(walletAddress) {
    if (!walletAddress) {
      throw new Error('Wallet address required for broadcasting');
    }
    
    this.logger.info(`Broadcasting P2P availability for wallet: ${walletAddress}`);
    
    // Use PeerDiscoveryManager to broadcast availability
    this.peerDiscoveryManager.broadcastAvailability(walletAddress);
    
    this.emit('broadcastingAvailability', {
      walletAddress,
      modelPath: this.state.selectedModel,
      timestamp: new Date().toISOString()
    });
  }
  
  /**
   * Start P2P peer discovery process
   */
  async startPeerDiscovery() {
    if (!this.state.walletAddress || !this.state.selectedModel) {
      throw new Error('Cannot start peer discovery: wallet address and model selection required');
    }
    
    try {
      this.logger.info('Starting P2P peer discovery...');
      
      this.setState({
        mode: BootstrapMode.DISCOVERY,
        discoveredPeers: []
      });
      
      // Show initial discovery status
      this.feedbackManager.displayPeerDiscoveryStatus({
        phase: 'initializing',
        peers: [],
        elapsed: 0,
        message: 'Iniciando búsqueda P2P de peers...'
      });
      
      this.emit('stateChanged', this.state);
      this.emit('peerDiscoveryStarted');
      
      // Track discovery start time
      this.discoveryStartTime = Date.now();
      
      // Start P2P peer discovery with timeout handling
      const discoveredPeers = await this.peerDiscoveryManager.scanForPeers(this.config.networkMode);
      this.onPeersDiscovered(discoveredPeers);
      
    } catch (error) {
      this.handleError(BootstrapErrorType.NETWORK_TIMEOUT, 'Failed to start P2P peer discovery', error);
      throw error;
    }
  }
  
  /**
   * Handle discovered peers
   * @param {Array} peers - Array of PeerInfo objects
   */
  onPeersDiscovered(peers) {
    if (!Array.isArray(peers)) {
      throw new Error('Peers must be an array');
    }
    
    this.logger.info(`Discovered ${peers.length} peers`);
    
    // Validate peer information
    const validPeers = peers.filter(peer => this.validatePeerInfo(peer));
    
    this.setState({
      discoveredPeers: validPeers
    });
    
    this.emit('peersDiscovered', validPeers);
    
    // Check if we have enough peers for genesis creation
    if (validPeers.length >= this.config.minPeersForGenesis) {
      this.logger.info(`Sufficient peers found (${validPeers.length}), initiating genesis coordination`);
      this.coordinateGenesisCreation();
    }
  }
  
  /**
   * Coordinate genesis block creation among discovered peers
   */
  async coordinateGenesisCreation() {
    try {
      this.logger.info('Coordinating genesis block creation...');
      
      this.setState({
        mode: BootstrapMode.GENESIS
      });
      
      // Show genesis creation progress
      this.feedbackManager.showGenesisCreationProgress({
        phase: 'negotiating',
        percentage: 10,
        message: 'Negociando parámetros del bloque génesis...',
        participants: this.state.discoveredPeers.map(p => p.walletAddress)
      });
      
      this.emit('stateChanged', this.state);
      this.emit('genesisCoordinationStarted');
      
      // Genesis coordination will be handled by GenesisCoordinator
      // This method will be called when genesis is complete
      
    } catch (error) {
      this.handleError(BootstrapErrorType.GENESIS_FAILURE, 'Failed to coordinate genesis creation', error);
      throw error;
    }
  }
  
  /**
   * Handle successful genesis block creation
   * @param {Object} genesisResult - Genesis creation result
   */
  onGenesisCreated(genesisResult) {
    if (!genesisResult || !genesisResult.block) {
      throw new Error('Invalid genesis result provided');
    }
    
    this.logger.info('Genesis block created successfully');
    
    this.setState({
      genesisBlock: genesisResult.block,
      networkConfig: genesisResult.networkConfig
    });
    
    this.emit('genesisCreated', genesisResult);
    this.transitionToNetworkMode();
  }
  
  /**
   * Transition to active network mode
   */
  transitionToNetworkMode() {
    try {
      this.logger.info('Transitioning to network mode...');
      
      this.setState({
        mode: BootstrapMode.NETWORK
      });
      
      // Enable all features
      this.restrictedFeatures.clear();
      
      // Show success message
      this.feedbackManager.showSuccessMessage(
        '¡Red blockchain establecida exitosamente! Todas las funciones están ahora disponibles.'
      );
      
      this.emit('stateChanged', this.state);
      this.emit('networkModeActivated');
      
      this.logger.info('Successfully transitioned to network mode - all features enabled');
      
    } catch (error) {
      this.handleError(BootstrapErrorType.GENESIS_FAILURE, 'Failed to transition to network mode', error);
      throw error;
    }
  }
  
  /**
   * Check if a feature is available during current bootstrap state
   * @param {string} feature - Feature identifier
   * @returns {boolean} True if feature is available
   */
  isFeatureAvailable(feature) {
    return !this.restrictedFeatures.has(feature);
  }
  
  /**
   * Get list of currently restricted features
   * @returns {Array} Array of restricted feature names
   */
  getRestrictedFeatures() {
    return Array.from(this.restrictedFeatures);
  }
  
  /**
   * Validate peer information structure
   * @param {Object} peer - PeerInfo object to validate
   * @returns {boolean} True if valid
   */
  validatePeerInfo(peer) {
    if (!peer || typeof peer !== 'object') {
      return false;
    }
    
    const required = ['id', 'address', 'port', 'walletAddress', 'networkMode', 'isReady'];
    return required.every(field => peer.hasOwnProperty(field));
  }
  
  /**
   * Handle errors with proper logging and user feedback
   * @param {string} type - Error type from BootstrapErrorType
   * @param {string} message - User-friendly error message
   * @param {Error} error - Original error object
   */
  handleError(type, message, error) {
    const bootstrapError = {
      type,
      message,
      originalError: error,
      timestamp: new Date().toISOString(),
      state: this.state.mode
    };
    
    this.setState({
      lastError: bootstrapError
    });
    
    // Display error through feedback manager
    this.feedbackManager.displayErrorMessage(bootstrapError);
    
    this.logger.error(`Bootstrap error [${type}]: ${message}`, error);
    this.emit('error', bootstrapError);
  }
  
  /**
   * Update internal state and emit change events
   * @param {Object} updates - State updates to apply
   */
  setState(updates) {
    const previousState = { ...this.state };
    this.state = { ...this.state, ...updates };
    
    // Emit specific events for mode changes
    if (updates.mode && updates.mode !== previousState.mode) {
      this.emit('modeChanged', updates.mode, previousState.mode);
    }
    
    this.emit('stateChanged', this.state);
  }
  
  /**
   * Get current bootstrap state
   * @returns {Object} Current state object
   */
  getState() {
    return { ...this.state };
  }
  
  /**
   * Get current bootstrap mode
   * @returns {string} Current mode
   */
  getCurrentMode() {
    return this.state.mode;
  }
  
  /**
   * Get user feedback manager instance
   * @returns {UserFeedbackManager} Feedback manager
   */
  getFeedbackManager() {
    return this.feedbackManager;
  }
  
  /**
   * Setup event listeners for peer discovery manager
   */
  setupPeerDiscoveryListeners() {
    this.peerDiscoveryManager.on('peerDiscovered', (peer) => {
      this.logger.info(`P2P peer discovered: ${peer.id} at ${peer.address}:${peer.port}`);
      
      // Update feedback with discovered peer
      this.feedbackManager.displayPeerDiscoveryStatus({
        phase: 'discovering',
        peers: this.peerDiscoveryManager.getDiscoveredPeers(),
        elapsed: Date.now() - this.discoveryStartTime,
        message: `Peer encontrado: ${peer.address}:${peer.port}`
      });
    });

    this.peerDiscoveryManager.on('networkFormationTriggered', (readyPeers) => {
      this.logger.info(`Network formation triggered with ${readyPeers.length} ready peers`);
      
      // Update state with ready peers
      this.setState({
        discoveredPeers: readyPeers
      });
      
      // Automatically start genesis coordination
      this.coordinateGenesisCreation();
    });

    this.peerDiscoveryManager.on('availabilityBroadcast', (data) => {
      this.logger.info(`Broadcasting availability: ${data.walletAddress}`);
      this.emit('broadcastingAvailability', data);
    });
  }

  /**
   * Reset bootstrap service to initial state
   */
  reset() {
    this.logger.info('Resetting bootstrap service to initial state');
    
    // Cleanup peer discovery manager
    if (this.peerDiscoveryManager) {
      this.peerDiscoveryManager.cleanup();
      this.peerDiscoveryManager.removeAllListeners();
    }
    
    this.state = {
      mode: BootstrapMode.PIONEER,
      walletAddress: null,
      selectedModel: null,
      discoveredPeers: [],
      genesisBlock: null,
      networkConfig: null,
      lastError: null,
      isReady: false
    };
    
    // Restore restricted features
    this.restrictedFeatures = new Set([
      'send_transaction',
      'mining_operations',
      'consensus_participation',
      'block_validation'
    ]);
    
    this.emit('stateChanged', this.state);
    this.emit('reset');
  }
}

// Export constants and class
module.exports = {
  BootstrapService,
  BootstrapMode,
  NetworkMode,
  BootstrapErrorType
};