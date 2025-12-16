const axios = require('axios');
const NetworkCoordinatorClient = require('./NetworkCoordinatorClient');
const { ErrorHandlingService } = require('./ErrorHandlingService');

class NetworkService {
  constructor() {
    // Remote-only configuration for gamers scenario
    this.remoteConfig = {
      apiUrl: 'https://playergold.es',  // Remote coordinator only
      networkId: 'playergold-remote-network',
      explorerUrl: 'https://playergold.es/explorer'
    };
    
    // Current network (remote only)
    this.currentNetwork = 'remote';
    this.config = this.remoteConfig;
    
    // Local blockchain node service (lazy loaded to avoid circular dependency)
    this._blockchainNodeService = null;
    
    // Network Coordinator client
    this.coordinatorClient = new NetworkCoordinatorClient(
      'https://playergold.es',  // Main coordinator
      [
        'https://backup1.playergold.es',  // Backup coordinators
        'https://backup2.playergold.es'
      ]
    );
    
    // Error handling service
    this.errorHandler = new ErrorHandlingService();
    
    // Auto-register with coordinator when service starts
    this.initializeCoordinator();
  }
  
  /**
   * Get Network Coordinator client instance
   * @returns {NetworkCoordinatorClient} Coordinator client
   */
  getCoordinatorClient() {
    return this.coordinatorClient;
  }

  /**
   * Initialize Network Coordinator integration
   */
  async initializeCoordinator() {
    try {
      console.log('🌐 Initializing Network Coordinator integration...');
      
      // Register node with coordinator
      const nodeType = this.isGenesisNode() ? 'genesis' : 'regular';
      const success = await this.coordinatorClient.registerNode(nodeType);
      
      if (success) {
        console.log('✅ Successfully registered with Network Coordinator');
        
        // Get initial network map
        await this.updateNetworkMap();
      } else {
        console.warn('⚠️ Failed to register with Network Coordinator, continuing without it');
      }
      
    } catch (error) {
      console.warn('⚠️ Network Coordinator initialization failed:', error.message);
    }
  }
  
  /**
   * Check if this node should be a genesis node
   */
  isGenesisNode() {
    // In a real implementation, this would check configuration or capabilities
    // For now, we'll make it configurable via environment variable
    return process.env.PLAYERGOLD_GENESIS_NODE === 'true';
  }
  
  /**
   * Update network map from coordinator
   */
  async updateNetworkMap() {
    try {
      const networkMap = await this.coordinatorClient.getNetworkMap(1000, 50); // 1000km radius, max 50 nodes
      
      if (networkMap) {
        console.log(`📊 Network map updated: ${networkMap.active_nodes} active nodes`);
        
        // Store network map for use by other services
        this.networkMap = networkMap;
        
        // Emit event for other components
        if (typeof window !== 'undefined' && window.electronAPI) {
          window.electronAPI.emit('network-map-updated', networkMap);
        }
        
        return networkMap;
      }
      
    } catch (error) {
      console.warn('⚠️ Failed to update network map:', error.message);
    }
    
    return null;
  }
  
  /**
   * Get blockchain node service (lazy loaded)
   */
  getBlockchainNodeService() {
    if (!this._blockchainNodeService) {
      try {
        this._blockchainNodeService = require('./BlockchainNodeService');
      } catch (error) {
        console.warn('BlockchainNodeService not available:', error.message);
      }
    }
    return this._blockchainNodeService;
  }
  
  /**
   * Get the best available API URL (local node first, then fallback)
   */
  getBestApiUrl() {
    const nodeService = this.getBlockchainNodeService();
    
    // Try local node first if available
    if (nodeService && nodeService.isRunning) {
      const localUrl = nodeService.getApiUrl();
      if (localUrl) {
        return localUrl;
      }
    }
    
    // Fallback to configured URL
    return this.config.apiUrl;
  }

  /**
   * Switch between testnet and mainnet
   * @param {string} network - 'testnet' or 'mainnet'
   */
  switchNetwork(network) {
    if (network === 'testnet') {
      this.currentNetwork = 'testnet';
      this.config = this.testnetConfig;
    } else if (network === 'mainnet') {
      this.currentNetwork = 'mainnet';
      this.config = this.mainnetConfig;
    } else {
      throw new Error('Invalid network. Use "testnet" or "mainnet"');
    }
  }

  /**
   * Get current network info
   */
  getNetworkInfo() {
    return {
      network: this.currentNetwork,
      networkId: this.config.networkId,
      apiUrl: this.config.apiUrl,
      explorerUrl: this.config.explorerUrl
    };
  }

  /**
   * Get balance for an address
   * @param {string} address - Wallet address
   * @returns {Object} Balance information
   */
  async getBalance(address) {
    const context = { operation: 'balance_query', address };
    
    // Try local blockchain node first
    const nodeService = this.getBlockchainNodeService();
    if (nodeService && nodeService.isRunning) {
      try {
        const localResult = await nodeService.getBalance(address);
        if (localResult.success) {
          return {
            ...localResult,
            source: 'local_node',
            isMock: false
          };
        }
      } catch (error) {
        console.warn('Local node balance query failed:', error.message);
      }
    }
    
    // Fallback to remote API with retry mechanism
    try {
      const operation = async () => {
        const apiUrl = this.getBestApiUrl();
        const response = await axios.get(`${apiUrl}/api/v1/balance/${address}`, {
          timeout: this.errorHandler.config.networkTimeout
        });
        
        return {
          success: true,
          balance: response.data.balance || '0',
          address: address,
          network: this.currentNetwork,
          source: 'remote_api',
          isMock: false
        };
      };
      
      return await this.errorHandler.retryOperation('network_timeout', operation, context);
      
    } catch (error) {
      console.error('Error getting balance:', error.message);
      
      // Determine error type
      let errorType = 'network_disconnected';
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorType = 'network_timeout';
      } else if (error.response?.status >= 500) {
        errorType = 'api_unavailable';
      }
      
      const errorInfo = this.errorHandler.handleError(errorType, error, context);
      
      return {
        success: false,
        error: errorInfo.message,
        errorType: errorType,
        errorInfo: errorInfo,
        balance: '0',
        address: address,
        network: this.currentNetwork,
        requiresGenesis: true,
        isMock: false
      };
    }
  }

  /**
   * Send a transaction
   * @param {Object} transaction - Transaction data
   * @returns {Object} Transaction result
   */
  async sendTransaction(transaction) {
    try {
      // Convert transaction format to match API expectations
      const apiTransaction = {
        from_address: transaction.from,
        to_address: transaction.to,
        amount: transaction.amount,
        fee: transaction.fee || 0.01,
        memo: transaction.memo || '',
        timestamp: transaction.timestamp
      };

      const response = await axios.post(`${this.config.apiUrl}/api/v1/transaction`, apiTransaction, {
        timeout: 15000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      return {
        success: true,
        transactionId: response.data.transactionId,
        hash: response.data.hash || response.data.transactionId,
        network: this.currentNetwork
      };
    } catch (error) {
      console.error('Error sending transaction:', error.message);
      
      return {
        success: false,
        error: error.message,
        requiresGenesis: true
      };
    }
  }

  /**
   * Get transaction history for an address
   * @param {string} address - Wallet address
   * @param {number} limit - Number of transactions to fetch
   * @param {number} offset - Pagination offset
   * @returns {Object} Transaction history
   */
  async getTransactionHistory(address, limit = 50, offset = 0) {
    const context = { operation: 'transaction_history', address, limit, offset };
    
    try {
      const operation = async () => {
        const response = await axios.get(`${this.config.apiUrl}/api/v1/transactions/history/${address}`, {
          params: { limit, offset },
          timeout: this.errorHandler.config.networkTimeout
        });
        
        return {
          success: true,
          transactions: response.data.transactions || [],
          total: response.data.total || 0,
          address: address,
          network: this.currentNetwork,
          isMock: false
        };
      };
      
      return await this.errorHandler.retryOperation('network_timeout', operation, context);
      
    } catch (error) {
      console.error('Error getting transaction history:', error.message);
      
      // Determine error type
      let errorType = 'network_disconnected';
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorType = 'network_timeout';
      } else if (error.response?.status >= 500) {
        errorType = 'api_unavailable';
      }
      
      const errorInfo = this.errorHandler.handleError(errorType, error, context);
      
      return {
        success: false,
        error: errorInfo.message,
        errorType: errorType,
        errorInfo: errorInfo,
        transactions: [],
        total: 0,
        address: address,
        network: this.currentNetwork,
        requiresGenesis: true,
        isMock: false
      };
    }
  }

  /**
   * Get network status - For remote gamer scenario, we assume network is ready
   * @returns {Object} Network status
   */
  async getNetworkStatus() {
    // For remote gamer scenario, we don't need to check local blockchain status
    // The network coordination happens through the Network Coordinator
    return {
      success: true,
      status: {
        network: this.currentNetwork,
        mode: 'remote_coordination',
        ready: true,
        message: 'Network coordination through remote coordinator'
      },
      network: this.currentNetwork,
      requiresGenesis: false, // Genesis will be handled by peer discovery
      isMock: false
    };
  }

  /**
   * Request tokens from testnet faucet
   * @param {string} address - Address to send tokens to
   * @param {number} amount - Amount to request (default 1000)
   * @returns {Object} Faucet result
   */
  async requestFaucetTokens(address, amount = 1000) {
    const context = { operation: 'faucet_request', address, amount };
    
    if (this.currentNetwork !== 'testnet') {
      const errorInfo = this.errorHandler.handleError('operation_not_allowed', 
        new Error('Faucet is only available on testnet'), context);
      
      return {
        success: false,
        error: errorInfo.message,
        errorType: 'operation_not_allowed',
        errorInfo: errorInfo,
        network: this.currentNetwork,
        requiresGenesis: true,
        isMock: false
      };
    }

    // Try local blockchain node first
    const nodeService = this.getBlockchainNodeService();
    if (nodeService && nodeService.isRunning) {
      try {
        console.log(`🚰 Requesting faucet tokens from local node: ${amount} PRGLD to ${address}`);
        const localResult = await nodeService.requestFaucetTokens(address, amount);
        if (localResult.success) {
          return {
            ...localResult,
            source: 'local_node',
            isMock: false
          };
        }
      } catch (error) {
        console.warn('Local node faucet request failed:', error.message);
      }
    }

    // Fallback to remote faucet with retry mechanism
    try {
      const operation = async () => {
        console.log(`🚰 Requesting faucet tokens from remote: ${amount} PRGLD to ${address}`);
        const apiUrl = this.getBestApiUrl();
        console.log(`🌐 API URL: ${apiUrl}/api/v1/faucet`);
        
        const response = await axios.post(`${apiUrl}/api/v1/faucet`, {
          address: address,
          amount: amount
        }, {
          timeout: this.errorHandler.config.networkTimeout,
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log(`✅ Faucet response:`, response.data);
        
        return {
          success: true,
          transactionId: response.data.transactionId,
          amount: amount,
          address: address,
          message: `Requested ${amount} PRGLD from testnet faucet`,
          network: this.currentNetwork,
          source: 'remote_api',
          isMock: false
        };
      };
      
      return await this.errorHandler.retryOperation('network_timeout', operation, context);
      
    } catch (error) {
      console.error('❌ Error requesting faucet tokens:', error.message);
      console.error('❌ Error details:', error.response?.data || error);
      
      // Determine error type
      let errorType = 'network_disconnected';
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorType = 'network_timeout';
      } else if (error.response?.status >= 500) {
        errorType = 'api_unavailable';
      } else if (error.response?.status === 429) {
        errorType = 'operation_not_allowed'; // Rate limited
      }
      
      const errorInfo = this.errorHandler.handleError(errorType, error, context);
      
      return {
        success: false,
        error: errorInfo.message,
        errorType: errorType,
        errorInfo: errorInfo,
        details: error.response?.data || error.message,
        network: this.currentNetwork,
        requiresGenesis: true,
        isMock: false
      };
    }
  }

  /**
   * Get mining challenge from network
   * @returns {Promise<Object>} Challenge response
   */
  async getMiningChallenge() {
    try {
      // For now, return a simple challenge since we're in bootstrap mode
      // This will be improved when the full mining system is integrated
      return {
        success: true,
        challenge: {
          difficulty: 1,
          target: '0x00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
          timestamp: Date.now()
        },
        network: this.currentNetwork,
        source: 'bootstrap_mode',
        isMock: false
      };
    } catch (error) {
      console.error('Failed to get mining challenge:', error);
      return {
        success: false,
        error: error.message,
        details: error.response?.data || error.message,
        network: this.currentNetwork,
        requiresGenesis: true,
        isMock: false
      };
    }
  }

  /**
   * Validate address format
   * @param {string} address - Address to validate
   * @returns {boolean} True if valid
   */
  isValidAddress(address) {
    // PlayerGold addresses start with 'PG' and are 40 characters total
    return /^PG[a-fA-F0-9]{38}$/.test(address);
  }

  /**
   * Format amount for display
   * @param {string|number} amount - Amount to format
   * @returns {string} Formatted amount
   */
  formatAmount(amount) {
    const num = parseFloat(amount);
    if (isNaN(num)) return '0.00';
    
    return num.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 8
    });
  }

  /**
   * Get explorer URL for transaction
   * @param {string} txId - Transaction ID
   * @returns {string} Explorer URL
   */
  getTransactionUrl(txId) {
    return `${this.config.explorerUrl}/tx/${txId}`;
  }

  /**
   * Get mining statistics for an address
   * @param {string} address - Address to get mining stats for
   * @returns {Object} Mining statistics
   */
  async getMiningStats(address) {
    try {
      console.log(`📊 Getting mining stats for: ${address}`);
      
      const response = await axios.get(`${this.config.apiUrl}/api/v1/mining/stats/${address}`, {
        timeout: 5000
      });
      
      console.log(`✅ Mining stats response:`, response.data);
      
      return {
        success: true,
        mining_stats: response.data.mining_stats,
        network: this.currentNetwork
      };
    } catch (error) {
      console.error('❌ Error getting mining stats:', error.message);
      
      return {
        success: false,
        error: error.message,
        network: this.currentNetwork,
        requiresGenesis: true
      };
    }
  }

  /**
   * Get explorer URL for address
   * @param {string} address - Address
   * @returns {string} Explorer URL
   */
  getAddressUrl(address) {
    return `${this.config.explorerUrl}/address/${address}`;
  }

  // ========================================
  // Network Coordinator Methods
  // ========================================

  /**
   * Get network statistics from coordinator
   */
  async getNetworkCoordinatorStats() {
    try {
      const stats = await this.coordinatorClient.getNetworkStats();
      return {
        success: true,
        stats: stats
      };
    } catch (error) {
      console.warn('⚠️ Failed to get coordinator stats:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get current network map
   */
  getNetworkMap() {
    return this.networkMap;
  }

  /**
   * Force refresh network map
   */
  async refreshNetworkMap() {
    return await this.updateNetworkMap();
  }

  /**
   * Get nearby nodes based on current location
   */
  async getNearbyNodes(maxDistanceKm = 500, limit = 20) {
    try {
      const networkMap = await this.coordinatorClient.getNetworkMap(maxDistanceKm, limit);
      return {
        success: true,
        nodes: networkMap ? networkMap.active_nodes : 0,
        map: networkMap
      };
    } catch (error) {
      console.warn('⚠️ Failed to get nearby nodes:', error.message);
      return {
        success: false,
        error: error.message,
        nodes: 0
      };
    }
  }

  /**
   * Update node status for coordinator
   */
  async updateNodeStatus(blockchainHeight, connectedPeers, aiModelLoaded = false, miningActive = false) {
    try {
      const success = await this.coordinatorClient.sendKeepalive(
        blockchainHeight,
        connectedPeers,
        aiModelLoaded,
        miningActive
      );
      
      return {
        success: success,
        message: success ? 'Node status updated' : 'Failed to update node status'
      };
    } catch (error) {
      console.warn('⚠️ Failed to update node status:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get coordinator connection status
   */
  getCoordinatorStatus() {
    return {
      nodeId: this.coordinatorClient.nodeId,
      isRegistered: this.coordinatorClient.keepaliveInterval !== null,
      lastMapUpdate: this.coordinatorClient.lastMapUpdate,
      coordinatorUrl: this.coordinatorClient.coordinatorUrl,
      backupUrls: this.coordinatorClient.backupUrls
    };
  }

  /**
   * Shutdown coordinator client
   */
  shutdownCoordinator() {
    if (this.coordinatorClient) {
      this.coordinatorClient.shutdown();
    }
  }
}

module.exports = new NetworkService();