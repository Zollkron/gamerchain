/**
 * Genesis State Manager
 * 
 * Manages genesis block detection and network state validation.
 * Provides centralized state management for determining when blockchain operations are available.
 */

const EventEmitter = require('events');
const axios = require('axios');

/**
 * Network states for the blockchain
 */
const NetworkState = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting', 
  BOOTSTRAP_PIONEER: 'bootstrap_pioneer',
  BOOTSTRAP_DISCOVERY: 'bootstrap_discovery',
  BOOTSTRAP_GENESIS: 'bootstrap_genesis',
  ACTIVE: 'active'
};

/**
 * Genesis state information
 */
class GenesisState {
  constructor(exists = false, blockHash = null, createdAt = null, isVerified = false) {
    this.exists = exists;
    this.blockHash = blockHash;
    this.createdAt = createdAt;
    this.isVerified = isVerified;
  }

  toDict() {
    return {
      exists: this.exists,
      blockHash: this.blockHash,
      createdAt: this.createdAt ? this.createdAt.toISOString() : null,
      isVerified: this.isVerified
    };
  }

  static fromDict(data) {
    return new GenesisState(
      data.exists || false,
      data.blockHash || null,
      data.createdAt ? new Date(data.createdAt) : null,
      data.isVerified || false
    );
  }
}

class GenesisStateManager extends EventEmitter {
  constructor() {
    super();
    
    // Current state
    this.currentNetworkState = NetworkState.DISCONNECTED;
    this.genesisState = new GenesisState();
    this.lastStateCheck = null;
    
    // Configuration
    this.config = {
      stateCheckInterval: 30000, // 30 seconds
      genesisVerificationTimeout: 10000, // 10 seconds
      maxRetries: 3,
      retryBackoffMs: 2000
    };
    
    // Services (injected dependencies)
    this.networkService = null;
    this.bootstrapService = null;
    
    // State check timer
    this.stateCheckTimer = null;
    
    console.log('GenesisStateManager initialized');
  }

  /**
   * Check for local genesis block file
   * @returns {Promise<GenesisState|null>} Genesis state if found locally, null otherwise
   */
  async checkLocalGenesisBlock() {
    try {
      const fs = require('fs');
      const path = require('path');
      
      // Check multiple possible locations for genesis block
      const possiblePaths = [
        path.join(process.cwd(), 'data', 'genesis_block.json'),
        path.join(__dirname, '../../../data/genesis_block.json'),
        path.join(process.resourcesPath || process.cwd(), 'data', 'genesis_block.json')
      ];
      
      for (const genesisPath of possiblePaths) {
        if (fs.existsSync(genesisPath)) {
          try {
            const genesisData = JSON.parse(fs.readFileSync(genesisPath, 'utf8'));
            
            if (genesisData.index === 0 && genesisData.hash) {
              console.log(`✅ Local genesis block found at: ${genesisPath}`);
              
              return new GenesisState(
                true,
                genesisData.hash,
                new Date(genesisData.timestamp),
                true
              );
            }
          } catch (parseError) {
            console.warn(`⚠️ Invalid genesis block at ${genesisPath}:`, parseError.message);
          }
        }
      }
      
      return null;
      
    } catch (error) {
      console.error('❌ Error checking local genesis block:', error);
      return null;
    }
  }

  /**
   * Initialize the genesis state manager with required services
   * @param {Object} networkService - NetworkService instance
   * @param {Object} bootstrapService - BootstrapService instance (optional)
   */
  initialize(networkService, bootstrapService = null) {
    if (!networkService) {
      throw new Error('NetworkService is required for GenesisStateManager initialization');
    }
    
    this.networkService = networkService;
    this.bootstrapService = bootstrapService;
    
    // Set initial state based on bootstrap service if available
    if (this.bootstrapService) {
      try {
        const bootstrapState = this.bootstrapService.getState();
        
        if (bootstrapState && bootstrapState.mode) {
          switch (bootstrapState.mode) {
            case 'pioneer':
              this.currentNetworkState = NetworkState.BOOTSTRAP_PIONEER;
              break;
            case 'discovery':
              this.currentNetworkState = NetworkState.BOOTSTRAP_DISCOVERY;
              break;
            case 'genesis':
              this.currentNetworkState = NetworkState.BOOTSTRAP_GENESIS;
              break;
            case 'network':
              this.currentNetworkState = NetworkState.ACTIVE;
              break;
            default:
              this.currentNetworkState = NetworkState.DISCONNECTED;
              break;
          }
        }
        
        this.setupBootstrapListeners();
      } catch (error) {
        console.warn('Failed to get bootstrap state during initialization:', error.message);
      }
    }
    
    console.log('GenesisStateManager initialized with services');
    
    // Start periodic state checking
    this.startPeriodicStateCheck();
  }

  /**
   * Check if genesis block exists on the blockchain
   * @returns {Promise<GenesisState>} Genesis state information
   */
  async checkGenesisExists() {
    try {
      console.log('Checking genesis block existence...');
      
      // First, check for local genesis block file
      const localGenesis = await this.checkLocalGenesisBlock();
      if (localGenesis) {
        this.genesisState = localGenesis;
        console.log(`✅ Genesis block found locally: ${this.genesisState.blockHash}`);
        
        // If we have a local genesis block and we're not in bootstrap mode, activate the network
        if (this.currentNetworkState === NetworkState.DISCONNECTED || 
            this.currentNetworkState === NetworkState.CONNECTING) {
          console.log('🌐 Local genesis found - activating network state');
          this.updateNetworkState(NetworkState.ACTIVE);
        }
        
        this.emit('genesisStateChanged', this.genesisState);
        return this.genesisState;
      }
      
      // If we're in bootstrap mode, check bootstrap service
      if (this.bootstrapService) {
        const bootstrapState = this.bootstrapService.getState();
        
        if (bootstrapState.genesisBlock) {
          // Genesis block exists in bootstrap service
          this.genesisState = new GenesisState(
            true,
            bootstrapState.genesisBlock.hash,
            new Date(bootstrapState.genesisBlock.timestamp),
            true
          );
          
          console.log(`Genesis block found in bootstrap service: ${this.genesisState.blockHash}`);
          this.emit('genesisStateChanged', this.genesisState);
          return this.genesisState;
        }
      }
      
      // Check via network service
      if (this.networkService) {
        try {
          // Try to get network status to check if genesis exists
          const networkStatus = await this.networkService.getNetworkStatus();
          
          if (networkStatus.success && networkStatus.status) {
            // If network is active, genesis must exist
            if (networkStatus.status.blockchain_height > 0) {
              this.genesisState = new GenesisState(
                true,
                networkStatus.status.genesis_hash || 'unknown',
                networkStatus.status.genesis_timestamp ? new Date(networkStatus.status.genesis_timestamp) : null,
                true
              );
              
              console.log('Genesis block confirmed via network status');
              this.emit('genesisStateChanged', this.genesisState);
              return this.genesisState;
            }
          }
        } catch (error) {
          console.warn('Network status check failed:', error.message);
        }
        
        // Try to get actual genesis block information
        try {
          const apiUrl = this.networkService.getBestApiUrl();
          const response = await axios.get(`${apiUrl}/api/v1/block/0`, {
            timeout: 5000
          });
          
          if (response.data && response.data.block && response.data.block.height === 0) {
            // Real genesis block found
            this.genesisState = new GenesisState(true, response.data.block, null, true);
            console.log('✅ Real genesis block confirmed:', response.data.block.hash);
            this.emit('genesisStateChanged', this.genesisState);
            return this.genesisState;
          }
        } catch (error) {
          console.log('🔍 No genesis block found - this is expected for bootstrap mode');
        }
      }
      
      // No genesis block found
      this.genesisState = new GenesisState(false);
      console.log('No genesis block found');
      this.emit('genesisStateChanged', this.genesisState);
      
      this.lastStateCheck = new Date();
      return this.genesisState;
      
    } catch (error) {
      console.error('Error checking genesis existence:', error);
      
      // On error, assume no genesis and return state gracefully
      this.genesisState = new GenesisState(false);
      this.emit('genesisStateChanged', this.genesisState);
      this.lastStateCheck = new Date();
      return this.genesisState;
    }
  }

  /**
   * Get current network state
   * @returns {string} Current network state from NetworkState enum
   */
  getCurrentNetworkState() {
    // Always return the current state if it was explicitly set
    // This ensures reset() works properly and explicit state changes are respected
    return this.currentNetworkState;
  }

  /**
   * Check if a specific operation is allowed in current state
   * @param {string} operation - Operation to check ('send_transaction', 'mining', 'faucet', etc.)
   * @returns {boolean} True if operation is allowed
   */
  isOperationAllowed(operation) {
    const currentState = this.getCurrentNetworkState();
    
    // Define operation requirements
    const operationRequirements = {
      'send_transaction': [NetworkState.ACTIVE],
      'receive_transaction': [NetworkState.ACTIVE],
      'mining': [NetworkState.ACTIVE],
      'faucet': [NetworkState.ACTIVE],
      'balance_query': [NetworkState.ACTIVE],
      'transaction_history': [NetworkState.ACTIVE],
      'network_status': [NetworkState.CONNECTING, NetworkState.ACTIVE, NetworkState.BOOTSTRAP_GENESIS],
      'wallet_creation': [NetworkState.DISCONNECTED, NetworkState.CONNECTING, NetworkState.BOOTSTRAP_PIONEER, NetworkState.BOOTSTRAP_DISCOVERY, NetworkState.BOOTSTRAP_GENESIS, NetworkState.ACTIVE],
      'peer_discovery': [NetworkState.BOOTSTRAP_PIONEER, NetworkState.BOOTSTRAP_DISCOVERY],
      'genesis_creation': [NetworkState.BOOTSTRAP_GENESIS]
    };
    
    const allowedStates = operationRequirements[operation];
    if (!allowedStates) {
      console.warn(`Unknown operation: ${operation}`);
      return false;
    }
    
    const isAllowed = allowedStates.includes(currentState);
    
    console.log(`Operation '${operation}' ${isAllowed ? 'allowed' : 'blocked'} in state '${currentState}'`);
    return isAllowed;
  }

  /**
   * Update network state based on external events
   * @param {string} newState - New network state
   */
  updateNetworkState(newState) {
    if (!Object.values(NetworkState).includes(newState)) {
      throw new Error(`Invalid network state: ${newState}`);
    }
    
    const previousState = this.currentNetworkState;
    this.currentNetworkState = newState;
    
    console.log(`Network state changed: ${previousState} -> ${newState}`);
    this.emit('networkStateChanged', newState, previousState);
  }

  /**
   * Get comprehensive state information
   * @returns {Object} Complete state information
   */
  getStateInfo() {
    return {
      networkState: this.getCurrentNetworkState(),
      genesisState: this.genesisState.toDict(),
      lastStateCheck: this.lastStateCheck,
      isBootstrapping: this.bootstrapService ? this.bootstrapService.isCoordinating : false,
      availableOperations: this.getAvailableOperations()
    };
  }

  /**
   * Get list of currently available operations
   * @returns {Array<string>} List of available operations
   */
  getAvailableOperations() {
    const allOperations = [
      'send_transaction',
      'receive_transaction', 
      'mining',
      'faucet',
      'balance_query',
      'transaction_history',
      'network_status',
      'wallet_creation',
      'peer_discovery',
      'genesis_creation'
    ];
    
    return allOperations.filter(op => this.isOperationAllowed(op));
  }

  /**
   * Setup listeners for bootstrap service events
   */
  setupBootstrapListeners() {
    if (!this.bootstrapService) return;
    
    console.log('Setting up bootstrap service listeners');
    
    this.bootstrapService.on('stateChanged', (state) => {
      // Update network state based on bootstrap state
      let newNetworkState = this.currentNetworkState;
      
      if (state.mode) {
        switch (state.mode) {
          case 'pioneer':
            newNetworkState = NetworkState.BOOTSTRAP_PIONEER;
            break;
          case 'discovery':
            newNetworkState = NetworkState.BOOTSTRAP_DISCOVERY;
            break;
          case 'genesis':
            newNetworkState = NetworkState.BOOTSTRAP_GENESIS;
            break;
          case 'network':
            newNetworkState = NetworkState.ACTIVE;
            break;
          default:
            newNetworkState = NetworkState.DISCONNECTED;
            break;
        }
      }
      
      if (newNetworkState !== this.currentNetworkState) {
        this.updateNetworkState(newNetworkState);
      }
      
      // Clear cached data during bootstrap transitions
      if (state.mode !== 'network') {
        this.clearCachedData();
      }
    });
    
    this.bootstrapService.on('genesisCreated', (genesisResult) => {
      // Update genesis state when genesis is created
      if (genesisResult.block) {
        this.genesisState = new GenesisState(
          true,
          genesisResult.block.hash,
          new Date(genesisResult.block.timestamp),
          true
        );
        
        console.log('Genesis state updated from bootstrap service');
        this.emit('genesisStateChanged', this.genesisState);
        
        // Trigger state refresh after genesis creation
        this.refreshStateAfterGenesis();
      }
    });
    
    this.bootstrapService.on('networkModeActivated', () => {
      // Network is now active
      this.updateNetworkState(NetworkState.ACTIVE);
      
      // Clear any cached data and refresh state
      this.clearCachedData();
      this.refreshStateAfterNetworkActivation();
    });
    
    this.bootstrapService.on('modeChanged', (newMode, previousMode) => {
      console.log(`Bootstrap mode changed: ${previousMode} -> ${newMode}`);
      
      // Handle state transitions
      this.handleBootstrapModeTransition(newMode, previousMode);
    });
    
    this.bootstrapService.on('peerDiscoveryStarted', () => {
      this.updateNetworkState(NetworkState.BOOTSTRAP_DISCOVERY);
    });
    
    this.bootstrapService.on('genesisCoordinationStarted', () => {
      this.updateNetworkState(NetworkState.BOOTSTRAP_GENESIS);
    });
  }

  /**
   * Start periodic state checking
   */
  startPeriodicStateCheck() {
    if (this.stateCheckTimer) {
      clearInterval(this.stateCheckTimer);
    }
    
    this.stateCheckTimer = setInterval(async () => {
      try {
        await this.checkGenesisExists();
        await this.updateNetworkConnectivity();
      } catch (error) {
        console.warn('Periodic state check failed:', error.message);
      }
    }, this.config.stateCheckInterval);
    
    console.log(`Started periodic state checking every ${this.config.stateCheckInterval}ms`);
  }

  /**
   * Update network connectivity state
   */
  async updateNetworkConnectivity() {
    if (!this.networkService) return;
    
    try {
      const networkStatus = await this.networkService.getNetworkStatus();
      
      if (networkStatus.success) {
        // Network is reachable
        if (this.currentNetworkState === NetworkState.DISCONNECTED) {
          this.updateNetworkState(NetworkState.CONNECTING);
        }
      } else {
        // Network is not reachable
        if (this.currentNetworkState === NetworkState.CONNECTING || this.currentNetworkState === NetworkState.ACTIVE) {
          this.updateNetworkState(NetworkState.DISCONNECTED);
        }
      }
    } catch (error) {
      // Network error - update to disconnected if not already
      if (this.currentNetworkState !== NetworkState.DISCONNECTED && !this.currentNetworkState.startsWith('bootstrap_')) {
        this.updateNetworkState(NetworkState.DISCONNECTED);
      }
    }
  }

  /**
   * Stop periodic state checking
   */
  stopPeriodicStateCheck() {
    if (this.stateCheckTimer) {
      clearInterval(this.stateCheckTimer);
      this.stateCheckTimer = null;
      console.log('Stopped periodic state checking');
    }
  }

  /**
   * Reset state manager to initial state
   */
  reset() {
    this.stopPeriodicStateCheck();
    
    this.currentNetworkState = NetworkState.DISCONNECTED;
    this.genesisState = new GenesisState();
    this.lastStateCheck = null;
    
    console.log('GenesisStateManager reset to initial state');
    this.emit('reset');
  }

  /**
   * Clear cached data during bootstrap transitions
   */
  clearCachedData() {
    console.log('Clearing cached data during bootstrap transition');
    
    // Reset last state check to force fresh data
    this.lastStateCheck = null;
    
    // Emit event for other services to clear their cached data
    this.emit('cachedDataCleared');
  }

  /**
   * Handle bootstrap mode transitions
   * @param {string} newMode - New bootstrap mode
   * @param {string} previousMode - Previous bootstrap mode
   */
  handleBootstrapModeTransition(newMode, previousMode) {
    console.log(`Handling bootstrap mode transition: ${previousMode} -> ${newMode}`);
    
    // Clear cached data on any mode transition
    this.clearCachedData();
    
    // Handle specific transitions
    if (newMode === 'network' && previousMode !== 'network') {
      // Transitioning to active network - refresh all state
      this.refreshStateAfterNetworkActivation();
    } else if (previousMode === 'network' && newMode !== 'network') {
      // Transitioning away from active network - reset genesis state
      this.genesisState = new GenesisState(false);
      this.emit('genesisStateChanged', this.genesisState);
    }
  }

  /**
   * Refresh state after genesis creation
   */
  async refreshStateAfterGenesis() {
    console.log('Refreshing state after genesis creation');
    
    try {
      // Force a fresh genesis check
      await this.checkGenesisExists();
      
      // Update network connectivity
      await this.updateNetworkConnectivity();
      
      console.log('State refreshed successfully after genesis creation');
    } catch (error) {
      console.error('Error refreshing state after genesis creation:', error);
    }
  }

  /**
   * Refresh state after network activation
   */
  async refreshStateAfterNetworkActivation() {
    console.log('Refreshing state after network activation');
    
    try {
      // Clear cached data first
      this.clearCachedData();
      
      // Force fresh state checks
      await this.checkGenesisExists();
      await this.updateNetworkConnectivity();
      
      // Emit event for UI components to refresh
      this.emit('networkActivated', {
        networkState: this.currentNetworkState,
        genesisState: this.genesisState.toDict(),
        timestamp: new Date().toISOString()
      });
      
      console.log('State refreshed successfully after network activation');
    } catch (error) {
      console.error('Error refreshing state after network activation:', error);
    }
  }

  /**
   * Get bootstrap integration status
   * @returns {Object} Integration status
   */
  getBootstrapIntegrationStatus() {
    return {
      hasBootstrapService: this.bootstrapService !== null,
      bootstrapMode: this.bootstrapService ? this.bootstrapService.getCurrentMode() : null,
      networkState: this.currentNetworkState,
      genesisExists: this.genesisState.exists,
      lastStateCheck: this.lastStateCheck,
      isIntegrated: this.bootstrapService !== null
    };
  }

  /**
   * Force state synchronization with bootstrap service
   */
  async synchronizeWithBootstrap() {
    if (!this.bootstrapService) {
      console.warn('Cannot synchronize - no bootstrap service available');
      return;
    }
    
    try {
      console.log('Synchronizing state with bootstrap service');
      
      const bootstrapState = this.bootstrapService.getState();
      
      // Update network state based on bootstrap mode
      let newNetworkState = this.currentNetworkState;
      
      if (bootstrapState.mode) {
        switch (bootstrapState.mode) {
          case 'pioneer':
            newNetworkState = NetworkState.BOOTSTRAP_PIONEER;
            break;
          case 'discovery':
            newNetworkState = NetworkState.BOOTSTRAP_DISCOVERY;
            break;
          case 'genesis':
            newNetworkState = NetworkState.BOOTSTRAP_GENESIS;
            break;
          case 'network':
            newNetworkState = NetworkState.ACTIVE;
            break;
          default:
            newNetworkState = NetworkState.DISCONNECTED;
            break;
        }
      }
      
      if (newNetworkState !== this.currentNetworkState) {
        this.updateNetworkState(newNetworkState);
      }
      
      // Update genesis state if available
      if (bootstrapState.genesisBlock) {
        this.genesisState = new GenesisState(
          true,
          bootstrapState.genesisBlock.hash,
          new Date(bootstrapState.genesisBlock.timestamp),
          true
        );
        this.emit('genesisStateChanged', this.genesisState);
      }
      
      console.log('State synchronized with bootstrap service');
    } catch (error) {
      console.error('Error synchronizing with bootstrap service:', error);
    }
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    this.stopPeriodicStateCheck();
    this.removeAllListeners();
    
    console.log('GenesisStateManager cleaned up');
  }
}

module.exports = {
  GenesisStateManager,
  GenesisState,
  NetworkState
};