import axios from 'axios';
import { EventEmitter } from 'events';

/**
 * NetworkService handles communication with PlayerGold blockchain network
 * Manages balance synchronization, transaction broadcasting, and network status
 */
class NetworkService extends EventEmitter {
  constructor() {
    super();
    
    // Default network configuration
    this.config = {
      apiUrl: 'http://localhost:8545', // Default local node
      timeout: 10000,
      retryAttempts: 3,
      retryDelay: 1000
    };
    
    this.isConnected = false;
    this.syncProgress = 0;
    this.networkStats = {
      blockHeight: 0,
      tps: 0,
      pendingTransactions: 0,
      connectedPeers: 0
    };
    
    // Start connection monitoring
    this.startConnectionMonitoring();
  }

  /**
   * Initialize connection to PlayerGold network
   */
  async connect() {
    try {
      const response = await this.makeRequest('/api/network/status');
      
      if (response.success) {
        this.isConnected = true;
        this.networkStats = response.data;
        this.emit('connected', this.networkStats);
        return { success: true };
      }
      
      throw new Error(response.error || 'Failed to connect to network');
    } catch (error) {
      this.isConnected = false;
      this.emit('disconnected', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get balance for a specific address
   * @param {string} address - Wallet address
   * @returns {Object} Balance information
   */
  async getBalance(address) {
    try {
      const response = await this.makeRequest(`/api/wallet/${address}/balance`);
      
      if (response.success) {
        return {
          success: true,
          balance: response.data.balance,
          confirmed: response.data.confirmed,
          pending: response.data.pending
        };
      }
      
      throw new Error(response.error || 'Failed to get balance');
    } catch (error) {
      return {
        success: false,
        error: error.message,
        balance: '0'
      };
    }
  }

  /**
   * Send transaction to the network
   * @param {Object} transactionData - Transaction details
   * @returns {Object} Transaction result
   */
  async sendTransaction(transactionData) {
    try {
      const response = await this.makeRequest('/api/transactions/send', 'POST', transactionData);
      
      if (response.success) {
        this.emit('transactionSent', response.data);
        return {
          success: true,
          transactionHash: response.data.hash,
          estimatedConfirmationTime: response.data.estimatedTime || 30
        };
      }
      
      throw new Error(response.error || 'Failed to send transaction');
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get transaction history for an address
   * @param {string} address - Wallet address
   * @param {number} limit - Maximum number of transactions
   * @param {number} offset - Pagination offset
   * @returns {Object} Transaction history
   */
  async getTransactionHistory(address, limit = 50, offset = 0) {
    try {
      const response = await this.makeRequest(
        `/api/wallet/${address}/transactions?limit=${limit}&offset=${offset}`
      );
      
      if (response.success) {
        return {
          success: true,
          transactions: response.data.transactions,
          total: response.data.total,
          hasMore: response.data.hasMore
        };
      }
      
      throw new Error(response.error || 'Failed to get transaction history');
    } catch (error) {
      return {
        success: false,
        error: error.message,
        transactions: []
      };
    }
  }

  /**
   * Get transaction details by hash
   * @param {string} hash - Transaction hash
   * @returns {Object} Transaction details
   */
  async getTransaction(hash) {
    try {
      const response = await this.makeRequest(`/api/transactions/${hash}`);
      
      if (response.success) {
        return {
          success: true,
          transaction: response.data
        };
      }
      
      throw new Error(response.error || 'Transaction not found');
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Estimate transaction fee
   * @param {Object} transactionData - Transaction details for estimation
   * @returns {Object} Fee estimation
   */
  async estimateFee(transactionData) {
    try {
      const response = await this.makeRequest('/api/transactions/estimate-fee', 'POST', transactionData);
      
      if (response.success) {
        return {
          success: true,
          fee: response.data.fee,
          congestionLevel: response.data.congestionLevel,
          estimatedTime: response.data.estimatedTime
        };
      }
      
      throw new Error(response.error || 'Failed to estimate fee');
    } catch (error) {
      return {
        success: false,
        error: error.message,
        fee: '0.01' // Default fallback fee
      };
    }
  }

  /**
   * Get network statistics
   * @returns {Object} Network stats
   */
  async getNetworkStats() {
    try {
      const response = await this.makeRequest('/api/network/stats');
      
      if (response.success) {
        this.networkStats = response.data;
        this.emit('statsUpdated', this.networkStats);
        return {
          success: true,
          stats: response.data
        };
      }
      
      throw new Error(response.error || 'Failed to get network stats');
    } catch (error) {
      return {
        success: false,
        error: error.message,
        stats: this.networkStats
      };
    }
  }

  /**
   * Make HTTP request to blockchain API with retry logic
   * @param {string} endpoint - API endpoint
   * @param {string} method - HTTP method
   * @param {Object} data - Request data
   * @returns {Object} Response data
   */
  async makeRequest(endpoint, method = 'GET', data = null) {
    let lastError;
    
    for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
      try {
        const config = {
          method,
          url: `${this.config.apiUrl}${endpoint}`,
          timeout: this.config.timeout,
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'PlayerGold-Wallet/1.0.0'
          }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
          config.data = data;
        }
        
        const response = await axios(config);
        return response.data;
        
      } catch (error) {
        lastError = error;
        
        if (attempt < this.config.retryAttempts) {
          await this.delay(this.config.retryDelay * attempt);
        }
      }
    }
    
    throw lastError;
  }

  /**
   * Start monitoring network connection
   */
  startConnectionMonitoring() {
    // Check connection every 30 seconds
    setInterval(async () => {
      const wasConnected = this.isConnected;
      const result = await this.connect();
      
      if (wasConnected && !result.success) {
        this.emit('connectionLost');
      } else if (!wasConnected && result.success) {
        this.emit('connectionRestored');
      }
    }, 30000);
    
    // Update network stats every 10 seconds
    setInterval(async () => {
      if (this.isConnected) {
        await this.getNetworkStats();
      }
    }, 10000);
  }

  /**
   * Utility function for delays
   * @param {number} ms - Milliseconds to delay
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get current connection status
   * @returns {Object} Connection status
   */
  getConnectionStatus() {
    return {
      connected: this.isConnected,
      syncProgress: this.syncProgress,
      networkStats: this.networkStats
    };
  }

  /**
   * Update network configuration
   * @param {Object} newConfig - New configuration
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
  }
}

export default new NetworkService();