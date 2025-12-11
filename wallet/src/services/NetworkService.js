const axios = require('axios');

class NetworkService {
  constructor() {
    // Testnet configuration
    this.testnetConfig = {
      apiUrl: 'http://127.0.0.1:18080',  // Local testnet API (IPv4 explicit)
      networkId: 'playergold-testnet-genesis',
      explorerUrl: 'http://127.0.0.1:18080/explorer'
    };
    
    // Mainnet configuration (for future use)
    this.mainnetConfig = {
      apiUrl: 'https://api.playergold.es',
      networkId: 'playergold-mainnet',
      explorerUrl: 'https://explorer.playergold.es'
    };
    
    // Current network (default to testnet)
    this.currentNetwork = 'testnet';
    this.config = this.testnetConfig;
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
    try {
      const response = await axios.get(`${this.config.apiUrl}/api/v1/balance/${address}`, {
        timeout: 10000
      });
      
      return {
        success: true,
        balance: response.data.balance || '0',
        address: address,
        network: this.currentNetwork
      };
    } catch (error) {
      console.error('Error getting balance:', error.message);
      
      // Return mock balance for development
      if (this.currentNetwork === 'testnet') {
        return {
          success: true,
          balance: '1000.0', // Mock testnet balance
          address: address,
          network: this.currentNetwork,
          mock: true
        };
      }
      
      return {
        success: false,
        error: error.message,
        balance: '0'
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
      
      // Return mock transaction for development
      if (this.currentNetwork === 'testnet') {
        const mockTxId = 'mock_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
        return {
          success: true,
          transactionId: mockTxId,
          hash: mockTxId,
          network: this.currentNetwork,
          mock: true
        };
      }
      
      return {
        success: false,
        error: error.message
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
    try {
      const response = await axios.get(`${this.config.apiUrl}/api/v1/transactions/history/${address}`, {
        params: { limit, offset },
        timeout: 10000
      });
      
      return {
        success: true,
        transactions: response.data.transactions || [],
        total: response.data.total || 0,
        address: address,
        network: this.currentNetwork
      };
    } catch (error) {
      console.error('Error getting transaction history:', error.message);
      
      // Return mock transactions for development
      if (this.currentNetwork === 'testnet') {
        const mockTransactions = [
          {
            id: 'faucet_tx_initial',
            type: 'faucet_transfer',
            from: 'PGfaucet000000000000000000000000000000000',
            to: address,
            amount: '1000.0',
            fee: '0.0',
            timestamp: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
            status: 'confirmed',
            memo: 'Testnet faucet - Initial 1000 PRGLD',
            blockNumber: 1,
            confirmations: 1
          }
        ];
        
        return {
          success: true,
          transactions: mockTransactions,
          total: mockTransactions.length,
          address: address,
          network: this.currentNetwork,
          mock: true
        };
      }
      
      return {
        success: false,
        error: error.message,
        transactions: []
      };
    }
  }

  /**
   * Get network status
   * @returns {Object} Network status
   */
  async getNetworkStatus() {
    try {
      const response = await axios.get(`${this.config.apiUrl}/api/v1/network/status`, {
        timeout: 5000
      });
      
      return {
        success: true,
        status: response.data,
        network: this.currentNetwork
      };
    } catch (error) {
      console.error('Error getting network status:', error.message);
      
      // Return mock status for development
      if (this.currentNetwork === 'testnet') {
        return {
          success: true,
          status: {
            network: this.currentNetwork,
            networkId: this.config.networkId,
            blockHeight: 150,
            connectedPeers: 2,
            isValidator: false,
            syncStatus: 'synced'
          },
          network: this.currentNetwork,
          mock: true
        };
      }
      
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Request tokens from testnet faucet
   * @param {string} address - Address to send tokens to
   * @param {number} amount - Amount to request (default 1000)
   * @returns {Object} Faucet result
   */
  async requestFaucetTokens(address, amount = 1000) {
    if (this.currentNetwork !== 'testnet') {
      return {
        success: false,
        error: 'Faucet is only available on testnet'
      };
    }

    try {
      console.log(`🚰 Requesting faucet tokens: ${amount} PRGLD to ${address}`);
      console.log(`🌐 API URL: ${this.config.apiUrl}/api/v1/faucet`);
      
      const response = await axios.post(`${this.config.apiUrl}/api/v1/faucet`, {
        address: address,
        amount: amount
      }, {
        timeout: 10000,
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
        message: `Requested ${amount} PRGLD from testnet faucet`
      };
    } catch (error) {
      console.error('❌ Error requesting faucet tokens:', error.message);
      console.error('❌ Error details:', error.response?.data || error);
      
      // For now, let's propagate the error instead of returning mock
      return {
        success: false,
        error: `Faucet request failed: ${error.message}`,
        details: error.response?.data || error.message
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
      
      // Return mock stats for development
      if (this.currentNetwork === 'testnet') {
        return {
          success: true,
          mining_stats: {
            blocks_validated: 0,
            rewards_earned: 0,
            challenges_processed: 0,
            success_rate: 100.0,
            reputation: 100.0,
            is_mining: false,
            last_reward: null
          },
          network: this.currentNetwork,
          mock: true
        };
      }
      
      return {
        success: false,
        error: error.message
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
}

module.exports = new NetworkService();