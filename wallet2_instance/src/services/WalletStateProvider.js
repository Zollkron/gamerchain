/**
 * Wallet State Provider
 * 
 * Provides consolidated state management for UI components.
 * Integrates with GenesisStateManager and BootstrapService to provide
 * accurate wallet display state across all network conditions.
 */

const EventEmitter = require('events');
const { GenesisStateManager, NetworkState } = require('./GenesisStateManager');
const { ErrorHandlingService } = require('./ErrorHandlingService');

/**
 * Wallet display state for UI components
 */
class WalletDisplayState {
  constructor({
    balance = '0',
    transactions = [],
    canSendTransactions = false,
    canRequestFaucet = false,
    networkState = NetworkState.DISCONNECTED,
    genesisState = null,
    statusMessage = '',
    lastUpdated = new Date(),
    isLoading = false,
    error = null
  } = {}) {
    this.balance = balance;
    this.transactions = transactions;
    this.canSendTransactions = canSendTransactions;
    this.canRequestFaucet = canRequestFaucet;
    this.networkState = networkState;
    this.genesisState = genesisState;
    this.statusMessage = statusMessage;
    this.lastUpdated = lastUpdated;
    this.isLoading = isLoading;
    this.error = error;
  }

  /**
   * Convert to plain object for serialization
   */
  toDict() {
    return {
      balance: this.balance,
      transactions: this.transactions,
      canSendTransactions: this.canSendTransactions,
      canRequestFaucet: this.canRequestFaucet,
      networkState: this.networkState,
      genesisState: this.genesisState ? this.genesisState.toDict() : null,
      statusMessage: this.statusMessage,
      lastUpdated: this.lastUpdated.toISOString(),
      isLoading: this.isLoading,
      error: this.error
    };
  }
}

class WalletStateProvider extends EventEmitter {
  constructor() {
    super();
    
    // State cache for wallets
    this.walletStates = new Map();
    
    // Service dependencies
    this.genesisStateManager = null;
    this.bootstrapService = null;
    this.walletService = null;
    this.networkService = null;
    
    // Error handling service
    this.errorHandler = new ErrorHandlingService();
    
    // Configuration
    this.config = {
      stateRefreshInterval: 10000, // 10 seconds
      maxCacheAge: 30000, // 30 seconds
      enableAutoRefresh: true
    };
    
    // Auto-refresh timer
    this.refreshTimer = null;
    
    console.log('WalletStateProvider initialized');
  }

  /**
   * Initialize the wallet state provider with required services
   * @param {Object} services - Service dependencies
   * @param {GenesisStateManager} services.genesisStateManager - Genesis state manager
   * @param {Object} services.bootstrapService - Bootstrap service (optional)
   * @param {Object} services.walletService - Wallet service
   * @param {Object} services.networkService - Network service
   */
  initialize(services) {
    const { genesisStateManager, bootstrapService, walletService, networkService } = services;
    
    if (!genesisStateManager) {
      throw new Error('GenesisStateManager is required for WalletStateProvider initialization');
    }
    if (!walletService) {
      throw new Error('WalletService is required for WalletStateProvider initialization');
    }
    if (!networkService) {
      throw new Error('NetworkService is required for WalletStateProvider initialization');
    }
    
    this.genesisStateManager = genesisStateManager;
    this.bootstrapService = bootstrapService;
    this.walletService = walletService;
    this.networkService = networkService;
    
    // Setup event listeners
    this.setupGenesisStateListeners();
    if (this.bootstrapService) {
      this.setupBootstrapListeners();
    }
    
    // Start auto-refresh if enabled
    if (this.config.enableAutoRefresh) {
      this.startAutoRefresh();
    }
    
    console.log('WalletStateProvider initialized with services');
  }

  /**
   * Get consolidated wallet display state for UI components
   * @param {string} walletId - Wallet ID
   * @returns {Promise<WalletDisplayState>} Wallet display state
   */
  async getWalletDisplayState(walletId) {
    try {
      if (!walletId) {
        throw new Error('Wallet ID is required');
      }

      // Check cache first
      const cachedState = this.getCachedState(walletId);
      if (cachedState && !this.isCacheExpired(cachedState)) {
        return cachedState.state;
      }

      // Get current genesis and network state
      const genesisState = await this.genesisStateManager.checkGenesisExists();
      const networkState = this.genesisStateManager.getCurrentNetworkState();
      
      // Get wallet data
      const walletBalance = await this.walletService.getWalletBalance(walletId);
      const transactionHistory = await this.walletService.getTransactionHistory(walletId, 10, 0);
      
      // Determine operation availability
      const canSendTransactions = this.genesisStateManager.isOperationAllowed('send_transaction');
      const canRequestFaucet = this.genesisStateManager.isOperationAllowed('faucet');
      
      // Generate status message
      const statusMessage = this.generateStatusMessage(networkState, genesisState, walletBalance, transactionHistory);
      
      // Create display state
      const displayState = new WalletDisplayState({
        balance: walletBalance.balance || '0',
        transactions: transactionHistory.transactions || [],
        canSendTransactions,
        canRequestFaucet,
        networkState,
        genesisState,
        statusMessage,
        lastUpdated: new Date(),
        isLoading: false,
        error: walletBalance.error || transactionHistory.error || null
      });

      // Cache the state
      this.cacheState(walletId, displayState);
      
      // Emit state update event
      this.emit('walletStateUpdated', walletId, displayState);
      
      return displayState;
      
    } catch (error) {
      console.error(`Error getting wallet display state for ${walletId}:`, error);
      
      // Return error state
      const errorState = new WalletDisplayState({
        balance: '0',
        transactions: [],
        canSendTransactions: false,
        canRequestFaucet: false,
        networkState: NetworkState.DISCONNECTED,
        genesisState: { exists: false },
        statusMessage: `Error: ${error.message}`,
        lastUpdated: new Date(),
        isLoading: false,
        error: error.message
      });
      
      this.emit('walletStateError', walletId, error);
      return errorState;
    }
  }

  /**
   * Handle genesis block creation event
   * @param {Object} genesisResult - Genesis creation result
   */
  onGenesisCreated(genesisResult) {
    console.log('WalletStateProvider: Genesis block created, refreshing all wallet states');
    
    // Clear all cached states to force refresh
    this.walletStates.clear();
    
    // Emit genesis created event
    this.emit('genesisCreated', genesisResult);
    
    // Refresh all active wallet states
    this.refreshAllWalletStates();
  }

  /**
   * Handle network state change event
   * @param {string} newState - New network state
   * @param {string} previousState - Previous network state
   */
  onNetworkStateChange(newState, previousState) {
    console.log(`WalletStateProvider: Network state changed from ${previousState} to ${newState}`);
    
    // Clear cached states for significant state changes
    if (this.isSignificantStateChange(previousState, newState)) {
      this.walletStates.clear();
    }
    
    // Emit network state change event
    this.emit('networkStateChanged', newState, previousState);
    
    // Refresh all active wallet states
    this.refreshAllWalletStates();
  }

  /**
   * Generate appropriate status message based on current state
   * @param {string} networkState - Current network state
   * @param {Object} genesisState - Genesis state information
   * @param {Object} balanceResult - Balance query result
   * @param {Object} historyResult - Transaction history result
   * @returns {string} Status message
   */
  generateStatusMessage(networkState, genesisState, balanceResult, historyResult) {
    // Handle error states first using ErrorHandlingService
    if (balanceResult.errorInfo) {
      return this.errorHandler.getStatusMessage(networkState, genesisState, {
        type: balanceResult.errorType,
        originalError: new Error(balanceResult.error),
        context: { operation: 'balance_query' }
      });
    }
    
    if (historyResult.errorInfo) {
      return this.errorHandler.getStatusMessage(networkState, genesisState, {
        type: historyResult.errorType,
        originalError: new Error(historyResult.error),
        context: { operation: 'transaction_history' }
      });
    }

    // Use ErrorHandlingService for consistent status messages
    return this.errorHandler.getStatusMessage(networkState, genesisState);
  }

  /**
   * Check if a state change is significant enough to clear cache
   * @param {string} previousState - Previous network state
   * @param {string} newState - New network state
   * @returns {boolean} True if significant change
   */
  isSignificantStateChange(previousState, newState) {
    const significantTransitions = [
      // Transitions to/from ACTIVE state
      [NetworkState.ACTIVE, NetworkState.DISCONNECTED],
      [NetworkState.DISCONNECTED, NetworkState.ACTIVE],
      [NetworkState.CONNECTING, NetworkState.ACTIVE],
      [NetworkState.ACTIVE, NetworkState.CONNECTING],
      
      // Bootstrap completion
      [NetworkState.BOOTSTRAP_GENESIS, NetworkState.ACTIVE],
      [NetworkState.BOOTSTRAP_DISCOVERY, NetworkState.BOOTSTRAP_GENESIS],
      
      // Network failures
      [NetworkState.ACTIVE, NetworkState.BOOTSTRAP_PIONEER],
      [NetworkState.ACTIVE, NetworkState.BOOTSTRAP_DISCOVERY]
    ];
    
    return significantTransitions.some(([from, to]) => 
      (previousState === from && newState === to) ||
      (previousState === to && newState === from)
    );
  }

  /**
   * Setup event listeners for genesis state manager
   */
  setupGenesisStateListeners() {
    if (!this.genesisStateManager) return;
    
    this.genesisStateManager.on('genesisStateChanged', (genesisState) => {
      if (genesisState.exists) {
        this.onGenesisCreated({ genesisState });
      }
    });
    
    this.genesisStateManager.on('networkStateChanged', (newState, previousState) => {
      this.onNetworkStateChange(newState, previousState);
    });
  }

  /**
   * Setup event listeners for bootstrap service
   */
  setupBootstrapListeners() {
    if (!this.bootstrapService) return;
    
    console.log('Setting up bootstrap service listeners in WalletStateProvider');
    
    this.bootstrapService.on('genesisCreated', (genesisResult) => {
      this.onGenesisCreated(genesisResult);
    });
    
    this.bootstrapService.on('networkModeActivated', () => {
      this.onNetworkStateChange(NetworkState.ACTIVE, this.genesisStateManager.getCurrentNetworkState());
    });
    
    this.bootstrapService.on('stateChanged', (bootstrapState) => {
      // Map bootstrap state to network state if needed
      const networkState = this.mapBootstrapToNetworkState(bootstrapState.mode);
      if (networkState !== this.genesisStateManager.getCurrentNetworkState()) {
        this.onNetworkStateChange(networkState, this.genesisStateManager.getCurrentNetworkState());
      }
      
      // Handle bootstrap-specific state changes
      this.handleBootstrapStateChange(bootstrapState);
    });
    
    this.bootstrapService.on('modeChanged', (newMode, previousMode) => {
      this.handleBootstrapModeTransition(newMode, previousMode);
    });
    
    this.bootstrapService.on('peerDiscoveryStarted', () => {
      this.clearCache(); // Clear cache when starting peer discovery
      this.emit('bootstrapPhaseChanged', 'peer_discovery');
    });
    
    this.bootstrapService.on('genesisCoordinationStarted', () => {
      this.clearCache(); // Clear cache when starting genesis coordination
      this.emit('bootstrapPhaseChanged', 'genesis_coordination');
    });
    
    this.bootstrapService.on('allBlockchainOperationsEnabled', (data) => {
      this.handleBlockchainOperationsEnabled(data);
    });
  }

  /**
   * Map bootstrap mode to network state
   * @param {string} bootstrapMode - Bootstrap mode
   * @returns {string} Network state
   */
  mapBootstrapToNetworkState(bootstrapMode) {
    const modeMap = {
      'pioneer': NetworkState.BOOTSTRAP_PIONEER,
      'discovery': NetworkState.BOOTSTRAP_DISCOVERY,
      'genesis': NetworkState.BOOTSTRAP_GENESIS,
      'network': NetworkState.ACTIVE
    };
    
    return modeMap[bootstrapMode] || NetworkState.DISCONNECTED;
  }

  /**
   * Cache wallet state
   * @param {string} walletId - Wallet ID
   * @param {WalletDisplayState} state - State to cache
   */
  cacheState(walletId, state) {
    this.walletStates.set(walletId, {
      state,
      cachedAt: new Date(),
      accessCount: (this.walletStates.get(walletId)?.accessCount || 0) + 1
    });
  }

  /**
   * Get cached state if available and not expired
   * @param {string} walletId - Wallet ID
   * @returns {Object|null} Cached state or null
   */
  getCachedState(walletId) {
    const cached = this.walletStates.get(walletId);
    if (!cached) return null;
    
    // Update access count
    cached.accessCount++;
    
    return cached;
  }

  /**
   * Check if cached state is expired
   * @param {Object} cachedState - Cached state object
   * @returns {boolean} True if expired
   */
  isCacheExpired(cachedState) {
    const age = Date.now() - cachedState.cachedAt.getTime();
    return age > this.config.maxCacheAge;
  }

  /**
   * Refresh all cached wallet states
   */
  async refreshAllWalletStates() {
    const walletIds = Array.from(this.walletStates.keys());
    
    for (const walletId of walletIds) {
      try {
        // Force refresh by clearing cache entry
        this.walletStates.delete(walletId);
        await this.getWalletDisplayState(walletId);
      } catch (error) {
        console.error(`Error refreshing wallet state for ${walletId}:`, error);
      }
    }
  }

  /**
   * Start automatic state refresh
   */
  startAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
    
    this.refreshTimer = setInterval(() => {
      this.refreshAllWalletStates();
    }, this.config.stateRefreshInterval);
    
    console.log(`Started auto-refresh every ${this.config.stateRefreshInterval}ms`);
  }

  /**
   * Stop automatic state refresh
   */
  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
      console.log('Stopped auto-refresh');
    }
  }

  /**
   * Clear all cached states
   */
  clearCache() {
    this.walletStates.clear();
    console.log('Wallet state cache cleared');
    this.emit('cacheCleared');
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  getCacheStats() {
    const stats = {
      totalEntries: this.walletStates.size,
      entries: []
    };
    
    for (const [walletId, cached] of this.walletStates.entries()) {
      stats.entries.push({
        walletId,
        cachedAt: cached.cachedAt,
        accessCount: cached.accessCount,
        age: Date.now() - cached.cachedAt.getTime(),
        expired: this.isCacheExpired(cached)
      });
    }
    
    return stats;
  }

  /**
   * Handle bootstrap state changes
   * @param {Object} bootstrapState - Current bootstrap state
   */
  handleBootstrapStateChange(bootstrapState) {
    console.log('Handling bootstrap state change:', bootstrapState.mode);
    
    // Clear cached data during bootstrap transitions
    if (bootstrapState.mode !== 'network') {
      this.clearCache();
    }
    
    // Emit bootstrap state change for UI components
    this.emit('bootstrapStateChanged', bootstrapState);
  }

  /**
   * Handle bootstrap mode transitions
   * @param {string} newMode - New bootstrap mode
   * @param {string} previousMode - Previous bootstrap mode
   */
  handleBootstrapModeTransition(newMode, previousMode) {
    console.log(`Handling bootstrap mode transition: ${previousMode} -> ${newMode}`);
    
    // Clear cache on any mode transition
    this.clearCache();
    
    // Handle specific transitions
    if (newMode === 'network' && previousMode !== 'network') {
      // Transitioning to active network - refresh all states
      this.refreshAllWalletStates();
      this.emit('bootstrapCompleted', { newMode, previousMode });
    } else if (previousMode === 'network' && newMode !== 'network') {
      // Transitioning away from active network - clear states
      this.clearCache();
      this.emit('bootstrapRestarted', { newMode, previousMode });
    }
    
    this.emit('bootstrapModeChanged', newMode, previousMode);
  }

  /**
   * Handle blockchain operations being enabled
   * @param {Object} data - Operations enabled data
   */
  handleBlockchainOperationsEnabled(data) {
    console.log('Blockchain operations enabled:', data.availableFeatures);
    
    // Clear cache to force refresh with new operation availability
    this.clearCache();
    
    // Refresh all wallet states to reflect new operation availability
    this.refreshAllWalletStates();
    
    this.emit('blockchainOperationsEnabled', data);
  }

  /**
   * Get bootstrap integration status
   * @returns {Object} Bootstrap integration status
   */
  getBootstrapIntegrationStatus() {
    return {
      hasBootstrapService: this.bootstrapService !== null,
      bootstrapMode: this.bootstrapService ? this.bootstrapService.getCurrentMode() : null,
      isBootstrapping: this.bootstrapService ? this.bootstrapService.getCurrentMode() !== 'network' : false,
      cachedWallets: this.walletStates.size,
      autoRefreshEnabled: this.refreshTimer !== null
    };
  }

  /**
   * Force synchronization with bootstrap service
   */
  async synchronizeWithBootstrap() {
    if (!this.bootstrapService) {
      console.warn('Cannot synchronize - no bootstrap service available');
      return;
    }
    
    try {
      console.log('Synchronizing WalletStateProvider with bootstrap service');
      
      const bootstrapState = this.bootstrapService.getState();
      
      // Handle the current bootstrap state
      this.handleBootstrapStateChange(bootstrapState);
      
      // Map and update network state
      const networkState = this.mapBootstrapToNetworkState(bootstrapState.mode);
      if (networkState !== this.genesisStateManager.getCurrentNetworkState()) {
        this.onNetworkStateChange(networkState, this.genesisStateManager.getCurrentNetworkState());
      }
      
      console.log('WalletStateProvider synchronized with bootstrap service');
    } catch (error) {
      console.error('Error synchronizing with bootstrap service:', error);
    }
  }

  /**
   * Update wallet display state for bootstrap progress
   * @param {string} walletId - Wallet ID
   * @param {Object} bootstrapProgress - Bootstrap progress information
   * @returns {WalletDisplayState} Updated display state
   */
  updateStateForBootstrapProgress(walletId, bootstrapProgress) {
    const cachedState = this.getCachedState(walletId);
    const currentState = cachedState ? cachedState.state : new WalletDisplayState();
    
    // Update status message based on bootstrap progress
    let statusMessage = currentState.statusMessage;
    
    if (bootstrapProgress.phase) {
      switch (bootstrapProgress.phase) {
        case 'peer_discovery':
          statusMessage = `Discovering peers... (${bootstrapProgress.peersFound || 0} found)`;
          break;
        case 'genesis_coordination':
          statusMessage = `Creating genesis block... (${bootstrapProgress.percentage || 0}% complete)`;
          break;
        case 'network_formation':
          statusMessage = 'Finalizing network formation...';
          break;
        default:
          statusMessage = `Bootstrap phase: ${bootstrapProgress.phase}`;
          break;
      }
    }
    
    // Create updated state
    const updatedState = new WalletDisplayState({
      ...currentState,
      statusMessage,
      isLoading: bootstrapProgress.isActive || false,
      lastUpdated: new Date()
    });
    
    // Cache and emit the updated state
    this.cacheState(walletId, updatedState);
    this.emit('walletStateUpdated', walletId, updatedState);
    
    return updatedState;
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    this.stopAutoRefresh();
    this.clearCache();
    this.removeAllListeners();
    
    console.log('WalletStateProvider cleaned up');
  }
}

module.exports = {
  WalletStateProvider,
  WalletDisplayState
};