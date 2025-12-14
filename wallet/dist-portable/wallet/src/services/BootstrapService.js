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
const { GenesisCoordinator } = require('./GenesisCoordinator');

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
    
    // Genesis coordinator for distributed block creation
    this.genesisCoordinator = new GenesisCoordinator();
    this.setupGenesisCoordinatorListeners();
    
    // Discovery timing
    this.discoveryStartTime = null;
    
    // Initialize data preservation
    this.implementDataPreservation();
    
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
      
      // Use GenesisCoordinator to handle the complete genesis process with peer disconnection handling
      const genesisResult = await this.coordinateGenesisWithResilience(this.state.discoveredPeers);
      
      // Handle successful genesis creation
      this.onGenesisCreated(genesisResult);
      
    } catch (error) {
      this.handleError(BootstrapErrorType.GENESIS_FAILURE, 'Failed to coordinate genesis creation', error, {
        autoRetry: true
      });
      throw error;
    }
  }

  /**
   * Coordinate genesis creation with peer disconnection resilience
   * @param {Array} initialPeers - Initial set of peers
   * @returns {Promise<Object>} Genesis result
   */
  async coordinateGenesisWithResilience(initialPeers) {
    let activePeers = [...initialPeers];
    let attempt = 0;
    const maxAttempts = 3;

    while (attempt < maxAttempts) {
      try {
        this.logger.info(`Genesis coordination attempt ${attempt + 1}/${maxAttempts} with ${activePeers.length} peers`);
        
        // Check if we still have enough peers
        if (activePeers.length < this.config.minPeersForGenesis) {
          throw new Error(`Insufficient peers for genesis creation: ${activePeers.length} < ${this.config.minPeersForGenesis}`);
        }

        // Attempt genesis coordination
        const result = await this.genesisCoordinator.coordinateGenesis(activePeers);
        
        this.logger.info(`Genesis coordination successful with ${activePeers.length} peers`);
        return result;

      } catch (error) {
        attempt++;
        
        if (error.message.includes('peer disconnected') || error.message.includes('connection lost')) {
          // Handle peer disconnection gracefully
          this.logger.warn(`Peer disconnection detected during genesis creation: ${error.message}`);
          
          // Remove disconnected peers and continue with remaining ones
          activePeers = await this.filterActivePeers(activePeers);
          
          this.feedbackManager.displayErrorMessage({
            type: BootstrapErrorType.PEER_DISCONNECTION,
            message: `Peer desconectado durante creación del génesis. Continuando con ${activePeers.length} peers restantes.`,
            timestamp: new Date().toISOString(),
            state: this.state.mode,
            canRetry: true
          });

          // Update state with remaining peers
          this.setState({
            discoveredPeers: activePeers
          });

          // If we still have enough peers, continue
          if (activePeers.length >= this.config.minPeersForGenesis && attempt < maxAttempts) {
            this.logger.info(`Retrying genesis coordination with ${activePeers.length} remaining peers`);
            continue;
          }
        }
        
        // If this was the last attempt or we don't have enough peers, throw the error
        if (attempt >= maxAttempts || activePeers.length < this.config.minPeersForGenesis) {
          throw error;
        }
      }
    }

    throw new Error(`Genesis coordination failed after ${maxAttempts} attempts`);
  }

  /**
   * Filter out disconnected peers and return only active ones
   * @param {Array} peers - Peers to filter
   * @returns {Promise<Array>} Active peers
   */
  async filterActivePeers(peers) {
    const activePeers = [];
    
    for (const peer of peers) {
      try {
        // Check if peer is still reachable
        const isActive = await this.peerDiscoveryManager.validatePeerConnection(peer);
        if (isActive) {
          activePeers.push(peer);
        } else {
          this.logger.info(`Removing disconnected peer: ${peer.id} at ${peer.address}:${peer.port}`);
        }
      } catch (error) {
        this.logger.warn(`Failed to validate peer ${peer.id}: ${error.message}`);
        // Don't include this peer in active list
      }
    }
    
    return activePeers;
  }

  /**
   * Handle insufficient peers scenario with status updates
   */
  handleInsufficientPeers() {
    const currentPeerCount = this.state.discoveredPeers.length;
    const requiredPeers = this.config.minPeersForGenesis;
    
    this.logger.info(`Insufficient peers for genesis creation: ${currentPeerCount}/${requiredPeers}`);
    
    // Update user with status
    this.feedbackManager.displayPeerDiscoveryStatus({
      phase: 'waiting',
      peers: this.state.discoveredPeers,
      elapsed: Date.now() - (this.discoveryStartTime || Date.now()),
      message: `Esperando más peers... (${currentPeerCount}/${requiredPeers} encontrados)`
    });
    
    // Continue peer discovery
    this.continuePeerDiscovery();
  }

  /**
   * Continue peer discovery when insufficient peers are found
   */
  async continuePeerDiscovery() {
    try {
      this.logger.info('Continuing peer discovery due to insufficient peers');
      
      // Wait a bit before retrying
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      // Restart peer discovery
      const newPeers = await this.peerDiscoveryManager.scanForPeers(this.config.networkMode);
      
      // Merge with existing peers (avoid duplicates)
      const allPeers = [...this.state.discoveredPeers];
      for (const newPeer of newPeers) {
        if (!allPeers.find(p => p.id === newPeer.id)) {
          allPeers.push(newPeer);
        }
      }
      
      this.setState({
        discoveredPeers: allPeers
      });
      
      // Check if we now have enough peers
      if (allPeers.length >= this.config.minPeersForGenesis) {
        this.logger.info(`Sufficient peers found: ${allPeers.length}/${this.config.minPeersForGenesis}`);
        await this.coordinateGenesisCreation();
      } else {
        // Still not enough, continue waiting
        this.handleInsufficientPeers();
      }
      
    } catch (error) {
      this.logger.error('Error during continued peer discovery:', error);
      this.handleError(BootstrapErrorType.INSUFFICIENT_PEERS, 'Failed to find sufficient peers', error, {
        autoRetry: true
      });
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
      
      // Enable all blockchain operations
      this.enableAllBlockchainOperations();
      
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
   * @param {Object} options - Additional error handling options
   */
  handleError(type, message, error, options = {}) {
    const bootstrapError = {
      type,
      message,
      originalError: error,
      timestamp: new Date().toISOString(),
      state: this.state.mode,
      retryCount: options.retryCount || 0,
      canRetry: this.canRetryError(type),
      nextRetryDelay: options.nextRetryDelay || null
    };
    
    this.setState({
      lastError: bootstrapError
    });
    
    // Display error through feedback manager
    this.feedbackManager.displayErrorMessage(bootstrapError);
    
    // Log detailed error information for troubleshooting
    this.logger.error(`Bootstrap error [${type}]: ${message}`, {
      error: error.message,
      stack: error.stack,
      state: this.state.mode,
      retryCount: bootstrapError.retryCount,
      canRetry: bootstrapError.canRetry
    });
    
    this.emit('error', bootstrapError);
    
    // Attempt automatic retry if appropriate
    if (bootstrapError.canRetry && options.autoRetry !== false) {
      this.scheduleRetry(type, options);
    }
  }

  /**
   * Check if error type can be retried
   * @param {string} errorType - Error type
   * @returns {boolean} True if retryable
   */
  canRetryError(errorType) {
    const retryableErrors = [
      BootstrapErrorType.NETWORK_TIMEOUT,
      BootstrapErrorType.PEER_DISCONNECTION,
      BootstrapErrorType.INSUFFICIENT_PEERS
    ];
    return retryableErrors.includes(errorType);
  }

  /**
   * Schedule retry with exponential backoff
   * @param {string} errorType - Type of error to retry
   * @param {Object} options - Retry options
   */
  scheduleRetry(errorType, options = {}) {
    const retryCount = (options.retryCount || 0) + 1;
    
    // Don't retry if we've exceeded max attempts
    if (retryCount > this.config.maxRetries) {
      this.logger.warn(`Max retry attempts (${this.config.maxRetries}) exceeded for error type: ${errorType}`);
      this.feedbackManager.displayErrorMessage({
        type: BootstrapErrorType.GENESIS_FAILURE,
        message: `Operación fallida después de ${this.config.maxRetries} intentos. Por favor, revise su conexión de red.`,
        timestamp: new Date().toISOString(),
        state: this.state.mode,
        canRetry: false
      });
      return;
    }

    // Calculate exponential backoff delay
    const baseDelay = this.config.retryBackoffMs;
    const backoffDelay = baseDelay * Math.pow(2, retryCount - 1);
    const jitter = Math.random() * 0.1 * backoffDelay; // Add 10% jitter
    const totalDelay = Math.min(backoffDelay + jitter, 30000); // Cap at 30 seconds

    this.logger.info(`Scheduling retry ${retryCount}/${this.config.maxRetries} for ${errorType} in ${Math.round(totalDelay)}ms`);
    
    // Show retry status to user
    this.feedbackManager.addStatusMessage({
      type: 'info',
      message: `Reintentando operación en ${Math.round(totalDelay / 1000)} segundos... (${retryCount}/${this.config.maxRetries})`,
      timestamp: new Date().toISOString(),
      retryCount: retryCount
    });

    // Schedule the retry
    setTimeout(() => {
      this.executeRetry(errorType, { ...options, retryCount });
    }, totalDelay);
  }

  /**
   * Execute retry operation based on error type
   * @param {string} errorType - Type of error to retry
   * @param {Object} options - Retry options
   */
  async executeRetry(errorType, options = {}) {
    try {
      this.logger.info(`Executing retry ${options.retryCount}/${this.config.maxRetries} for error type: ${errorType}`);
      
      switch (errorType) {
        case BootstrapErrorType.NETWORK_TIMEOUT:
          // Retry peer discovery
          if (this.state.walletAddress && this.state.selectedModel) {
            await this.startPeerDiscovery();
          }
          break;
          
        case BootstrapErrorType.PEER_DISCONNECTION:
          // Retry genesis coordination with remaining peers
          if (this.state.discoveredPeers.length >= this.config.minPeersForGenesis) {
            await this.coordinateGenesisCreation();
          } else {
            // Not enough peers, retry discovery
            await this.startPeerDiscovery();
          }
          break;
          
        case BootstrapErrorType.INSUFFICIENT_PEERS:
          // Retry peer discovery
          await this.startPeerDiscovery();
          break;
          
        default:
          this.logger.warn(`No retry handler for error type: ${errorType}`);
          break;
      }
    } catch (retryError) {
      this.logger.error(`Retry attempt ${options.retryCount} failed:`, retryError);
      this.handleError(errorType, `Retry attempt failed: ${retryError.message}`, retryError, {
        ...options,
        autoRetry: true
      });
    }
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
   * Integrate with existing wallet functionality during bootstrap
   * Ensures wallet operations remain available and data is preserved
   * @param {Object} walletService - WalletService instance
   */
  integrateWithWalletService(walletService) {
    if (!walletService) {
      throw new Error('WalletService instance required for integration');
    }

    this.logger.info('Integrating bootstrap service with wallet functionality');

    // Preserve existing wallet data during bootstrap
    this.on('stateChanged', async (state) => {
      try {
        // Ensure wallet addresses are preserved for genesis block rewards
        if (state.walletAddress && state.mode !== BootstrapMode.NETWORK) {
          await this.preserveWalletDataForGenesis(walletService, state.walletAddress);
        }
      } catch (error) {
        this.logger.error('Error preserving wallet data during bootstrap:', error);
      }
    });

    // Enable wallet operations after network formation
    this.on('networkModeActivated', async () => {
      try {
        await this.enableWalletOperationsAfterBootstrap(walletService);
      } catch (error) {
        this.logger.error('Error enabling wallet operations after bootstrap:', error);
      }
    });

    this.logger.info('Wallet service integration completed');
  }

  /**
   * Preserve wallet data for genesis block rewards
   * @param {Object} walletService - WalletService instance
   * @param {string} walletAddress - Wallet address to preserve
   */
  async preserveWalletDataForGenesis(walletService, walletAddress) {
    try {
      // Ensure address is eligible for genesis rewards
      const genesisAddresses = walletService.getGenesisEligibleAddresses();
      const existingEntry = genesisAddresses.find(entry => entry.address === walletAddress);
      
      if (!existingEntry) {
        // Add address to genesis eligibility list
        await walletService.persistAddressForGenesis(walletAddress, `bootstrap-${Date.now()}`);
        this.logger.info(`Preserved wallet address for genesis rewards: ${walletAddress}`);
      }
    } catch (error) {
      this.logger.error('Error preserving wallet data for genesis:', error);
    }
  }

  /**
   * Enable wallet operations after bootstrap completion
   * @param {Object} walletService - WalletService instance
   */
  async enableWalletOperationsAfterBootstrap(walletService) {
    try {
      // Refresh wallet balances after network formation
      const walletsResult = await walletService.getWallets();
      if (walletsResult.success) {
        for (const wallet of walletsResult.wallets) {
          try {
            await walletService.getWalletBalance(wallet.id);
          } catch (error) {
            this.logger.warn(`Could not refresh balance for wallet ${wallet.id}:`, error.message);
          }
        }
      }

      this.logger.info('Wallet operations enabled after bootstrap completion');
    } catch (error) {
      this.logger.error('Error enabling wallet operations:', error);
    }
  }

  /**
   * Integrate with mining and consensus mechanisms after network formation
   * @param {Object} miningService - MiningService instance
   * @param {Object} blockchainService - BlockchainService instance
   */
  integrateWithMiningAndConsensus(miningService, blockchainService) {
    if (!miningService) {
      throw new Error('MiningService instance required for integration');
    }

    this.logger.info('Integrating bootstrap service with mining and consensus mechanisms');

    // Enable mining operations after network formation
    this.on('networkModeActivated', async () => {
      try {
        await this.enableMiningAfterNetworkFormation(miningService, blockchainService);
      } catch (error) {
        this.logger.error('Error enabling mining after network formation:', error);
      }
    });

    // Preserve mining state during transitions
    this.on('stateChanged', (state) => {
      try {
        this.preserveMiningStateAcrossTransitions(miningService, state);
      } catch (error) {
        this.logger.error('Error preserving mining state:', error);
      }
    });

    this.logger.info('Mining and consensus integration completed');
  }

  /**
   * Enable mining operations after network formation
   * @param {Object} miningService - MiningService instance
   * @param {Object} blockchainService - BlockchainService instance (optional)
   */
  async enableMiningAfterNetworkFormation(miningService, blockchainService) {
    try {
      // Check if mining requirements are met
      const requirements = await miningService.checkMiningRequirements();
      
      if (requirements.canMine) {
        this.logger.info('Mining requirements satisfied - mining operations enabled');
        
        // If blockchain service is available, ensure it's ready
        if (blockchainService) {
          try {
            await blockchainService.initialize();
            this.logger.info('Blockchain service initialized for mining operations');
          } catch (error) {
            this.logger.warn('Blockchain service initialization failed:', error.message);
          }
        }
        
        // Notify that mining is ready to start
        this.emit('miningOperationsEnabled', {
          canMine: requirements.canMine,
          installedModels: requirements.installedModels,
          blockchainNodeAvailable: requirements.blockchainNodeAvailable
        });
      } else {
        this.logger.warn('Mining requirements not met after network formation:', requirements);
      }
    } catch (error) {
      this.logger.error('Error enabling mining operations:', error);
    }
  }

  /**
   * Preserve mining state across bootstrap transitions
   * @param {Object} miningService - MiningService instance
   * @param {Object} state - Current bootstrap state
   */
  preserveMiningStateAcrossTransitions(miningService, state) {
    try {
      // Preserve mining configuration during transitions
      if (state.selectedModel && state.modelInfo) {
        // Store mining configuration for restoration after network formation
        this.miningConfiguration = {
          selectedModel: state.selectedModel,
          modelInfo: state.modelInfo,
          walletAddress: state.walletAddress,
          preservedAt: new Date().toISOString()
        };
      }

      // Restore mining configuration in network mode
      if (state.mode === BootstrapMode.NETWORK && this.miningConfiguration) {
        this.logger.info('Restoring mining configuration after network formation');
        
        // Mining configuration is preserved and available for use
        this.emit('miningConfigurationRestored', this.miningConfiguration);
      }
    } catch (error) {
      this.logger.error('Error preserving mining state:', error);
    }
  }

  /**
   * Implement comprehensive data preservation across bootstrap transitions
   * Ensures all user data and wallet state is maintained
   */
  implementDataPreservation() {
    this.logger.info('Implementing comprehensive data preservation');

    // Store original state for preservation
    this.preservedData = {
      userPreferences: {},
      walletData: {},
      miningConfiguration: {},
      customData: {}
    };

    // Preserve data on state changes
    this.on('stateChanged', (state) => {
      this.preserveUserData(state);
    });

    // Restore data after transitions
    this.on('modeChanged', (newMode, previousMode) => {
      this.restoreUserDataAfterTransition(newMode, previousMode);
    });

    this.logger.info('Data preservation implementation completed');
  }

  /**
   * Preserve user data during state transitions
   * @param {Object} state - Current state
   */
  preserveUserData(state) {
    try {
      // Preserve core bootstrap data
      if (state.walletAddress) {
        this.preservedData.walletData.address = state.walletAddress;
      }
      
      if (state.selectedModel) {
        this.preservedData.miningConfiguration.selectedModel = state.selectedModel;
      }
      
      if (state.modelInfo) {
        this.preservedData.miningConfiguration.modelInfo = { ...state.modelInfo };
      }
      
      if (state.discoveredPeers) {
        this.preservedData.networkData = {
          discoveredPeers: [...state.discoveredPeers],
          preservedAt: new Date().toISOString()
        };
      }

      // Preserve any custom data
      if (state.customData) {
        this.preservedData.customData = { ...state.customData };
      }

    } catch (error) {
      this.logger.error('Error preserving user data:', error);
    }
  }

  /**
   * Restore user data after mode transitions
   * @param {string} newMode - New bootstrap mode
   * @param {string} previousMode - Previous bootstrap mode
   */
  restoreUserDataAfterTransition(newMode, previousMode) {
    try {
      this.logger.info(`Restoring user data after transition: ${previousMode} -> ${newMode}`);

      // Restore preserved data in the new mode
      const restoredState = {};

      if (this.preservedData.walletData.address) {
        restoredState.walletAddress = this.preservedData.walletData.address;
      }

      if (this.preservedData.miningConfiguration.selectedModel) {
        restoredState.selectedModel = this.preservedData.miningConfiguration.selectedModel;
      }

      if (this.preservedData.miningConfiguration.modelInfo) {
        restoredState.modelInfo = { ...this.preservedData.miningConfiguration.modelInfo };
      }

      if (this.preservedData.networkData && newMode !== BootstrapMode.PIONEER) {
        restoredState.discoveredPeers = [...this.preservedData.networkData.discoveredPeers];
      }

      if (this.preservedData.customData) {
        restoredState.customData = { ...this.preservedData.customData };
      }

      // Apply restored state
      if (Object.keys(restoredState).length > 0) {
        this.setState(restoredState);
        this.logger.info('User data restored successfully after transition');
      }

    } catch (error) {
      this.logger.error('Error restoring user data after transition:', error);
    }
  }

  /**
   * Enable all standard blockchain operations after bootstrap completion
   */
  enableAllBlockchainOperations() {
    try {
      this.logger.info('Enabling all standard blockchain operations');

      // Clear all restricted features
      this.restrictedFeatures.clear();

      // Emit event for external services to enable their operations
      this.emit('allBlockchainOperationsEnabled', {
        mode: this.state.mode,
        timestamp: new Date().toISOString(),
        availableFeatures: [
          'send_transaction',
          'mining_operations',
          'consensus_participation',
          'block_validation',
          'peer_communication',
          'network_synchronization'
        ]
      });

      this.logger.info('All blockchain operations enabled successfully');
    } catch (error) {
      this.logger.error('Error enabling blockchain operations:', error);
    }
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
   * Setup event listeners for genesis coordinator
   */
  setupGenesisCoordinatorListeners() {
    this.genesisCoordinator.on('phaseChanged', (phase) => {
      this.logger.info(`Genesis coordination phase changed to: ${phase}`);
      
      // Update user feedback based on phase
      const phaseMessages = {
        'negotiating': 'Negociando parámetros del bloque génesis...',
        'creating': 'Creando bloque génesis...',
        'distributing': 'Distribuyendo bloque génesis a peers...',
        'validating': 'Validando consenso entre peers...',
        'completed': 'Bloque génesis creado exitosamente',
        'failed': 'Error en la creación del bloque génesis'
      };
      
      const phasePercentages = {
        'negotiating': 20,
        'creating': 40,
        'distributing': 60,
        'validating': 80,
        'completed': 100,
        'failed': 0
      };
      
      this.feedbackManager.showGenesisCreationProgress({
        phase: phase,
        percentage: phasePercentages[phase] || 0,
        message: phaseMessages[phase] || `Fase de génesis: ${phase}`,
        participants: this.state.discoveredPeers.map(p => p.walletAddress)
      });
    });

    this.genesisCoordinator.on('parametersNegotiated', (params) => {
      this.logger.info(`Genesis parameters negotiated for network: ${params.networkId}`);
    });

    this.genesisCoordinator.on('blockCreated', (block) => {
      this.logger.info(`Genesis block created with hash: ${block.hash}`);
    });

    this.genesisCoordinator.on('consensusAchieved', (result) => {
      this.logger.info(`Genesis consensus achieved: ${result.validPeers}/${result.total} peers`);
    });

    this.genesisCoordinator.on('genesisFailed', (error) => {
      this.logger.error('Genesis coordination failed:', error);
      this.handleError(BootstrapErrorType.GENESIS_FAILURE, 'Genesis coordination failed', error);
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
    
    // Cleanup genesis coordinator
    if (this.genesisCoordinator) {
      this.genesisCoordinator.reset();
      this.genesisCoordinator.removeAllListeners();
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