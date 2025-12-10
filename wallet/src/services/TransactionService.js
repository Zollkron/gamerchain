import crypto from 'crypto';
import CryptoJS from 'crypto-js';
import NetworkService from './NetworkService';

/**
 * TransactionService handles transaction creation, signing, and management
 * Integrates with NetworkService for blockchain communication
 */
class TransactionService {
  constructor() {
    this.pendingTransactions = new Map();
    this.transactionHistory = new Map();
    
    // Listen to network events
    NetworkService.on('transactionSent', (txData) => {
      this.handleTransactionSent(txData);
    });
  }

  /**
   * Create and send a transaction
   * @param {Object} params - Transaction parameters
   * @returns {Object} Transaction result
   */
  async sendTransaction(params) {
    const {
      fromAddress,
      toAddress,
      amount,
      privateKey,
      transactionType = 'transfer',
      memo = ''
    } = params;

    try {
      // Validate inputs
      const validation = this.validateTransactionInputs(params);
      if (!validation.valid) {
        return {
          success: false,
          error: validation.error
        };
      }

      // Get current balance
      const balanceResult = await NetworkService.getBalance(fromAddress);
      if (!balanceResult.success) {
        return {
          success: false,
          error: 'Failed to verify balance'
        };
      }

      // Estimate fee
      const feeEstimate = await NetworkService.estimateFee({
        from: fromAddress,
        to: toAddress,
        amount: amount,
        type: transactionType
      });

      if (!feeEstimate.success) {
        return {
          success: false,
          error: 'Failed to estimate transaction fee'
        };
      }

      const fee = feeEstimate.fee;
      const totalRequired = parseFloat(amount) + parseFloat(fee);

      // Check sufficient balance
      if (parseFloat(balanceResult.balance) < totalRequired) {
        return {
          success: false,
          error: `Insufficient balance. Required: ${totalRequired} PRGLD, Available: ${balanceResult.balance} PRGLD`
        };
      }

      // Create transaction object
      const transaction = {
        from_address: fromAddress,
        to_address: toAddress,
        amount: amount.toString(),
        fee: fee.toString(),
        timestamp: Date.now() / 1000,
        transaction_type: transactionType,
        nonce: await this.getNonce(fromAddress),
        memo: memo
      };

      // Calculate transaction hash
      transaction.hash = this.calculateTransactionHash(transaction);

      // Sign transaction
      const signature = this.signTransaction(transaction, privateKey);
      transaction.signature = signature;

      // Send to network
      const sendResult = await NetworkService.sendTransaction(transaction);
      
      if (sendResult.success) {
        // Store as pending transaction
        this.addPendingTransaction({
          ...transaction,
          status: 'pending',
          confirmations: 0,
          sentAt: Date.now()
        });

        return {
          success: true,
          transactionHash: sendResult.transactionHash,
          fee: fee,
          estimatedConfirmationTime: sendResult.estimatedConfirmationTime
        };
      }

      return sendResult;

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
   * @param {number} limit - Number of transactions to fetch
   * @param {number} offset - Pagination offset
   * @returns {Object} Transaction history
   */
  async getTransactionHistory(address, limit = 50, offset = 0) {
    try {
      const result = await NetworkService.getTransactionHistory(address, limit, offset);
      
      if (result.success) {
        // Process and cache transactions
        result.transactions.forEach(tx => {
          this.cacheTransaction(address, tx);
        });
      }

      return result;
    } catch (error) {
      return {
        success: false,
        error: error.message,
        transactions: []
      };
    }
  }

  /**
   * Get pending transactions for an address
   * @param {string} address - Wallet address
   * @returns {Array} Pending transactions
   */
  getPendingTransactions(address) {
    const pending = [];
    
    for (const [hash, tx] of this.pendingTransactions) {
      if (tx.from_address === address || tx.to_address === address) {
        pending.push(tx);
      }
    }
    
    return pending.sort((a, b) => b.sentAt - a.sentAt);
  }

  /**
   * Get transaction details by hash
   * @param {string} hash - Transaction hash
   * @returns {Object} Transaction details
   */
  async getTransactionDetails(hash) {
    try {
      // Check if it's a pending transaction first
      if (this.pendingTransactions.has(hash)) {
        return {
          success: true,
          transaction: this.pendingTransactions.get(hash)
        };
      }

      // Fetch from network
      const result = await NetworkService.getTransaction(hash);
      return result;
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Validate transaction inputs
   * @param {Object} params - Transaction parameters
   * @returns {Object} Validation result
   */
  validateTransactionInputs(params) {
    const { fromAddress, toAddress, amount, privateKey } = params;

    if (!fromAddress || !toAddress || !amount || !privateKey) {
      return {
        valid: false,
        error: 'Missing required transaction parameters'
      };
    }

    if (fromAddress === toAddress) {
      return {
        valid: false,
        error: 'Cannot send to the same address'
      };
    }

    const amountNum = parseFloat(amount);
    if (isNaN(amountNum) || amountNum <= 0) {
      return {
        valid: false,
        error: 'Invalid amount'
      };
    }

    if (!this.isValidAddress(fromAddress) || !this.isValidAddress(toAddress)) {
      return {
        valid: false,
        error: 'Invalid address format'
      };
    }

    return { valid: true };
  }

  /**
   * Validate PlayerGold address format
   * @param {string} address - Address to validate
   * @returns {boolean} Is valid address
   */
  isValidAddress(address) {
    // PlayerGold addresses start with 'PG' followed by 38 hex characters
    const addressRegex = /^PG[0-9a-fA-F]{38}$/;
    return addressRegex.test(address);
  }

  /**
   * Calculate transaction hash
   * @param {Object} transaction - Transaction object
   * @returns {string} Transaction hash
   */
  calculateTransactionHash(transaction) {
    const txData = {
      from_address: transaction.from_address,
      to_address: transaction.to_address,
      amount: transaction.amount,
      fee: transaction.fee,
      timestamp: transaction.timestamp,
      transaction_type: transaction.transaction_type,
      nonce: transaction.nonce
    };

    const txString = JSON.stringify(txData, Object.keys(txData).sort());
    return crypto.createHash('sha256').update(txString).digest('hex');
  }

  /**
   * Sign transaction with private key
   * @param {Object} transaction - Transaction to sign
   * @param {string} privateKey - Private key for signing
   * @returns {string} Transaction signature
   */
  signTransaction(transaction, privateKey) {
    // Simplified signing - in production, use proper Ed25519 signing
    const message = transaction.hash;
    const signature = CryptoJS.HmacSHA256(message, privateKey).toString();
    return signature;
  }

  /**
   * Get next nonce for an address
   * @param {string} address - Wallet address
   * @returns {number} Next nonce
   */
  async getNonce(address) {
    try {
      // In a real implementation, this would fetch from the network
      // For now, use timestamp-based nonce
      return Date.now();
    } catch (error) {
      return Date.now();
    }
  }

  /**
   * Add pending transaction
   * @param {Object} transaction - Transaction to add
   */
  addPendingTransaction(transaction) {
    this.pendingTransactions.set(transaction.hash, transaction);
    
    // Auto-remove after 10 minutes if not confirmed
    setTimeout(() => {
      if (this.pendingTransactions.has(transaction.hash)) {
        const tx = this.pendingTransactions.get(transaction.hash);
        if (tx.status === 'pending') {
          tx.status = 'timeout';
        }
      }
    }, 10 * 60 * 1000);
  }

  /**
   * Handle transaction sent event from network
   * @param {Object} txData - Transaction data from network
   */
  handleTransactionSent(txData) {
    if (this.pendingTransactions.has(txData.hash)) {
      const tx = this.pendingTransactions.get(txData.hash);
      tx.status = 'broadcast';
      tx.broadcastAt = Date.now();
    }
  }

  /**
   * Update transaction confirmation status
   * @param {string} hash - Transaction hash
   * @param {number} confirmations - Number of confirmations
   */
  updateTransactionConfirmations(hash, confirmations) {
    if (this.pendingTransactions.has(hash)) {
      const tx = this.pendingTransactions.get(hash);
      tx.confirmations = confirmations;
      
      if (confirmations >= 6) { // Consider confirmed after 6 blocks
        tx.status = 'confirmed';
        tx.confirmedAt = Date.now();
        
        // Move to history after confirmation
        setTimeout(() => {
          this.pendingTransactions.delete(hash);
        }, 5000);
      }
    }
  }

  /**
   * Cache transaction in local history
   * @param {string} address - Wallet address
   * @param {Object} transaction - Transaction to cache
   */
  cacheTransaction(address, transaction) {
    if (!this.transactionHistory.has(address)) {
      this.transactionHistory.set(address, []);
    }
    
    const history = this.transactionHistory.get(address);
    const existingIndex = history.findIndex(tx => tx.hash === transaction.hash);
    
    if (existingIndex >= 0) {
      history[existingIndex] = transaction;
    } else {
      history.unshift(transaction);
      
      // Keep only last 100 transactions in cache
      if (history.length > 100) {
        history.splice(100);
      }
    }
  }

  /**
   * Get cached transaction history
   * @param {string} address - Wallet address
   * @returns {Array} Cached transactions
   */
  getCachedHistory(address) {
    return this.transactionHistory.get(address) || [];
  }

  /**
   * Clear transaction cache
   * @param {string} address - Wallet address (optional)
   */
  clearCache(address = null) {
    if (address) {
      this.transactionHistory.delete(address);
    } else {
      this.transactionHistory.clear();
    }
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
   * Get transaction status display text
   * @param {Object} transaction - Transaction object
   * @returns {string} Status text
   */
  getTransactionStatusText(transaction) {
    switch (transaction.status) {
      case 'pending':
        return 'Pendiente';
      case 'broadcast':
        return 'Transmitida';
      case 'confirmed':
        return 'Confirmada';
      case 'failed':
        return 'Fallida';
      case 'timeout':
        return 'Tiempo agotado';
      default:
        return 'Desconocido';
    }
  }
}

export default new TransactionService();