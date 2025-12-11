const NetworkService = require('./NetworkService');
const crypto = require('crypto');

class TransactionService {
  constructor() {
    this.pendingTransactions = new Map();
  }

  /**
   * Send a transaction
   * @param {Object} txParams - Transaction parameters
   * @returns {Object} Transaction result
   */
  async sendTransaction(txParams) {
    try {
      const {
        fromAddress,
        toAddress,
        amount,
        privateKey,
        transactionType = 'transfer',
        memo = ''
      } = txParams;

      // Validate parameters
      if (!fromAddress || !toAddress || !amount || !privateKey) {
        throw new Error('Missing required transaction parameters');
      }

      if (!NetworkService.isValidAddress(fromAddress) || !NetworkService.isValidAddress(toAddress)) {
        throw new Error('Invalid address format');
      }

      const amountNum = parseFloat(amount);
      if (isNaN(amountNum) || amountNum <= 0) {
        throw new Error('Invalid amount');
      }

      // Create transaction object
      const transaction = {
        type: transactionType,
        from: fromAddress,
        to: toAddress,
        amount: amountNum.toString(),
        memo: memo,
        timestamp: new Date().toISOString(),
        nonce: this._generateNonce(),
        networkId: NetworkService.getNetworkInfo().networkId
      };

      // Calculate fee (simplified)
      transaction.fee = this._calculateFee(transaction);

      // Sign transaction
      transaction.signature = this._signTransaction(transaction, privateKey);

      // Calculate transaction ID
      transaction.id = this._calculateTransactionId(transaction);

      // Add to pending transactions
      this.pendingTransactions.set(transaction.id, {
        ...transaction,
        status: 'pending',
        createdAt: Date.now()
      });

      // Send to network
      const result = await NetworkService.sendTransaction(transaction);

      if (result.success) {
        // Update pending transaction
        if (this.pendingTransactions.has(transaction.id)) {
          this.pendingTransactions.get(transaction.id).status = 'sent';
          this.pendingTransactions.get(transaction.id).networkTxId = result.transactionId;
        }

        return {
          success: true,
          transactionId: transaction.id,
          networkTransactionId: result.transactionId,
          hash: result.hash,
          amount: transaction.amount,
          fee: transaction.fee,
          from: transaction.from,
          to: transaction.to,
          memo: transaction.memo,
          timestamp: transaction.timestamp
        };
      } else {
        // Mark as failed
        if (this.pendingTransactions.has(transaction.id)) {
          this.pendingTransactions.get(transaction.id).status = 'failed';
          this.pendingTransactions.get(transaction.id).error = result.error;
        }

        return {
          success: false,
          error: result.error,
          transactionId: transaction.id
        };
      }

    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get transaction history for an address
   * @param {string} address - Address to get history for
   * @param {number} limit - Number of transactions
   * @param {number} offset - Pagination offset
   * @returns {Object} Transaction history
   */
  async getTransactionHistory(address, limit = 50, offset = 0) {
    try {
      const result = await NetworkService.getTransactionHistory(address, limit, offset);
      
      if (result.success) {
        // Process and format transactions
        const transactions = result.transactions.map(tx => ({
          id: tx.id,
          type: tx.type,
          from: tx.from,
          to: tx.to,
          amount: tx.amount,
          fee: tx.fee || '0',
          status: tx.status || 'confirmed',
          timestamp: tx.timestamp,
          memo: tx.memo || '',
          blockNumber: tx.blockNumber,
          confirmations: tx.confirmations || 0,
          direction: this._getTransactionDirection(tx, address)
        }));

        return {
          success: true,
          transactions: transactions,
          total: result.total,
          address: address
        };
      } else {
        return result;
      }

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
   * @param {string} address - Address to check
   * @returns {Array} Pending transactions
   */
  getPendingTransactions(address) {
    const pending = [];
    
    for (const [txId, tx] of this.pendingTransactions.entries()) {
      if (tx.from === address || tx.to === address) {
        pending.push({
          id: txId,
          type: tx.type,
          from: tx.from,
          to: tx.to,
          amount: tx.amount,
          fee: tx.fee,
          status: tx.status,
          timestamp: tx.timestamp,
          memo: tx.memo,
          direction: this._getTransactionDirection(tx, address),
          createdAt: tx.createdAt
        });
      }
    }

    // Sort by creation time (newest first)
    return pending.sort((a, b) => b.createdAt - a.createdAt);
  }

  /**
   * Get transaction by ID
   * @param {string} txId - Transaction ID
   * @returns {Object|null} Transaction or null if not found
   */
  getTransaction(txId) {
    return this.pendingTransactions.get(txId) || null;
  }

  /**
   * Clear old pending transactions
   * @param {number} maxAge - Maximum age in milliseconds (default 1 hour)
   */
  clearOldPendingTransactions(maxAge = 3600000) {
    const now = Date.now();
    
    for (const [txId, tx] of this.pendingTransactions.entries()) {
      if (now - tx.createdAt > maxAge) {
        this.pendingTransactions.delete(txId);
      }
    }
  }

  /**
   * Generate transaction nonce
   * @returns {number} Nonce
   */
  _generateNonce() {
    return Date.now() * 1000 + Math.floor(Math.random() * 1000);
  }

  /**
   * Calculate transaction fee
   * @param {Object} transaction - Transaction object
   * @returns {string} Fee amount
   */
  _calculateFee(transaction) {
    // Simple fee calculation: base fee + amount-based fee
    const baseFee = 0.01; // 0.01 PRGLD base fee
    const amountFee = parseFloat(transaction.amount) * 0.001; // 0.1% of amount
    const totalFee = baseFee + amountFee;
    
    // Minimum fee of 0.01 PRGLD
    return Math.max(totalFee, 0.01).toFixed(8);
  }

  /**
   * Sign transaction (simplified)
   * @param {Object} transaction - Transaction to sign
   * @param {string} privateKey - Private key for signing
   * @returns {string} Signature
   */
  _signTransaction(transaction, privateKey) {
    // Create transaction string for signing
    const txString = JSON.stringify({
      type: transaction.type,
      from: transaction.from,
      to: transaction.to,
      amount: transaction.amount,
      memo: transaction.memo,
      timestamp: transaction.timestamp,
      nonce: transaction.nonce,
      fee: transaction.fee
    }, Object.keys(transaction).sort());

    // Create signature using HMAC-SHA256 (simplified)
    const signature = crypto
      .createHmac('sha256', privateKey)
      .update(txString)
      .digest('hex');

    return signature;
  }

  /**
   * Calculate transaction ID
   * @param {Object} transaction - Transaction object
   * @returns {string} Transaction ID
   */
  _calculateTransactionId(transaction) {
    const txString = JSON.stringify({
      type: transaction.type,
      from: transaction.from,
      to: transaction.to,
      amount: transaction.amount,
      memo: transaction.memo,
      timestamp: transaction.timestamp,
      nonce: transaction.nonce,
      signature: transaction.signature
    }, Object.keys(transaction).sort());

    return crypto
      .createHash('sha256')
      .update(txString)
      .digest('hex');
  }

  /**
   * Determine transaction direction relative to an address
   * @param {Object} transaction - Transaction object
   * @param {string} address - Reference address
   * @returns {string} 'sent', 'received', or 'self'
   */
  _getTransactionDirection(transaction, address) {
    if (transaction.from === address && transaction.to === address) {
      return 'self';
    } else if (transaction.from === address) {
      return 'sent';
    } else if (transaction.to === address) {
      return 'received';
    }
    return 'unknown';
  }

  /**
   * Validate transaction parameters
   * @param {Object} txParams - Transaction parameters
   * @returns {Object} Validation result
   */
  validateTransactionParams(txParams) {
    const errors = [];

    if (!txParams.fromAddress) {
      errors.push('From address is required');
    } else if (!NetworkService.isValidAddress(txParams.fromAddress)) {
      errors.push('Invalid from address format');
    }

    if (!txParams.toAddress) {
      errors.push('To address is required');
    } else if (!NetworkService.isValidAddress(txParams.toAddress)) {
      errors.push('Invalid to address format');
    }

    if (!txParams.amount) {
      errors.push('Amount is required');
    } else {
      const amount = parseFloat(txParams.amount);
      if (isNaN(amount) || amount <= 0) {
        errors.push('Amount must be a positive number');
      }
    }

    if (!txParams.privateKey) {
      errors.push('Private key is required for signing');
    }

    return {
      isValid: errors.length === 0,
      errors: errors
    };
  }

  /**
   * Estimate transaction fee
   * @param {Object} txParams - Transaction parameters
   * @returns {string} Estimated fee
   */
  estimateFee(txParams) {
    if (!txParams.amount) return '0.01';
    
    const amount = parseFloat(txParams.amount);
    if (isNaN(amount)) return '0.01';
    
    return this._calculateFee({ amount: amount.toString() });
  }

  /**
   * Get network statistics
   * @returns {Object} Network stats
   */
  async getNetworkStats() {
    try {
      const status = await NetworkService.getNetworkStatus();
      return status;
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

module.exports = new TransactionService();