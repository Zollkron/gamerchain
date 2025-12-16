const axios = require('axios');
const EventEmitter = require('events');

class BlockchainService extends EventEmitter {
  constructor() {
    super();
    this.localBlockchain = {
      blocks: [],
      height: 0,
      lastBlockHash: null
    };
    this.peers = [];
    this.isConnected = false;
    this.isSyncing = false;
  }

  /**
   * Initialize blockchain service
   */
  async initialize() {
    try {
      // Load local blockchain
      await this.loadLocalBlockchain();
      
      // Connect to network
      await this.connectToNetwork();
      
      // Sync with network
      await this.syncWithNetwork();
      
      this.emit('ready');
      
    } catch (error) {
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Load local blockchain from storage
   */
  async loadLocalBlockchain() {
    try {
      // In a real implementation, this would load from a local database
      // For now, we'll simulate having a genesis block
      this.localBlockchain = {
        blocks: [
          {
            index: 0,
            hash: '8ae3ac88603b190b85301eff394d0258909711fcc556473bf5f3608b96aca7cc',
            previousHash: '0',
            timestamp: Date.now() - 86400000, // 1 day ago
            transactions: [],
            nonce: 0
          }
        ],
        height: 1,
        lastBlockHash: '8ae3ac88603b190b85301eff394d0258909711fcc556473bf5f3608b96aca7cc'
      };
      
      this.emit('status', { 
        type: 'info', 
        message: `Blockchain local cargado (${this.localBlockchain.height} bloques)` 
      });
      
    } catch (error) {
      throw new Error(`Error loading local blockchain: ${error.message}`);
    }
  }

  /**
   * Connect to P2P network
   */
  async connectToNetwork() {
    try {
      this.emit('status', { type: 'info', message: 'Conectando a la red P2P...' });
      
      // Simulate network connection
      await this.sleep(2000);
      
      // In a real implementation, this would connect to actual P2P nodes
      this.peers = [
        { id: 'node1', address: '192.168.1.129:18333', height: 150 },
        { id: 'node2', address: '192.168.1.132:18333', height: 150 }
      ];
      
      this.isConnected = true;
      
      this.emit('status', { 
        type: 'success', 
        message: `Conectado a ${this.peers.length} peers` 
      });
      
      this.emit('syncStatusUpdate', {
        isConnected: true,
        peers: this.peers.length,
        currentBlock: this.localBlockchain.height,
        targetBlock: Math.max(...this.peers.map(p => p.height)),
        isSyncing: false,
        syncProgress: 0
      });
      
    } catch (error) {
      throw new Error(`Error connecting to network: ${error.message}`);
    }
  }

  /**
   * Sync blockchain with network
   */
  async syncWithNetwork() {
    try {
      if (!this.isConnected || this.peers.length === 0) {
        throw new Error('Not connected to network');
      }

      // Get the highest block height from peers
      const targetHeight = Math.max(...this.peers.map(p => p.height));
      const currentHeight = this.localBlockchain.height;
      
      if (targetHeight <= currentHeight) {
        this.emit('status', { 
          type: 'success', 
          message: 'Blockchain ya está sincronizado' 
        });
        return;
      }

      this.isSyncing = true;
      const blocksToSync = targetHeight - currentHeight;
      
      this.emit('status', { 
        type: 'info', 
        message: `Sincronizando ${blocksToSync} bloques...` 
      });

      // Sync blocks one by one
      for (let height = currentHeight; height < targetHeight; height++) {
        await this.downloadBlock(height + 1);
        
        const progress = Math.round(((height - currentHeight + 1) / blocksToSync) * 100);
        
        this.emit('syncStatusUpdate', {
          isConnected: true,
          peers: this.peers.length,
          currentBlock: height + 1,
          targetBlock: targetHeight,
          isSyncing: true,
          syncProgress: progress
        });
        
        this.emit('status', { 
          type: 'info', 
          message: `Descargando bloque ${height + 1}/${targetHeight} (${progress}%)` 
        });
        
        // Small delay to simulate network download
        await this.sleep(50);
      }

      this.isSyncing = false;
      
      this.emit('status', { 
        type: 'success', 
        message: 'Blockchain sincronizado correctamente' 
      });
      
      this.emit('syncStatusUpdate', {
        isConnected: true,
        peers: this.peers.length,
        currentBlock: targetHeight,
        targetBlock: targetHeight,
        isSyncing: false,
        syncProgress: 100
      });
      
    } catch (error) {
      this.isSyncing = false;
      throw new Error(`Error syncing blockchain: ${error.message}`);
    }
  }

  /**
   * Download a specific block from the network
   */
  async downloadBlock(height) {
    try {
      // In a real implementation, this would request the block from peers
      // For now, we'll simulate creating a block
      const block = {
        index: height,
        hash: this.generateBlockHash(height),
        previousHash: this.localBlockchain.lastBlockHash,
        timestamp: Date.now() - (86400000 - (height * 600000)), // Simulate 10 min intervals
        transactions: this.generateMockTransactions(height),
        nonce: Math.floor(Math.random() * 1000000)
      };
      
      // Validate block (simplified)
      if (!this.validateBlock(block)) {
        throw new Error(`Invalid block at height ${height}`);
      }
      
      // Add to local blockchain
      this.localBlockchain.blocks.push(block);
      this.localBlockchain.height = height;
      this.localBlockchain.lastBlockHash = block.hash;
      
      // In a real implementation, this would save to local database
      await this.saveBlockToStorage(block);
      
    } catch (error) {
      throw new Error(`Error downloading block ${height}: ${error.message}`);
    }
  }

  /**
   * Generate a mock block hash
   */
  generateBlockHash(height) {
    const crypto = require('crypto');
    return crypto.createHash('sha256')
      .update(`block_${height}_${Date.now()}`)
      .digest('hex');
  }

  /**
   * Generate mock transactions for a block
   */
  generateMockTransactions(height) {
    const transactions = [];
    
    // Add mining reward transaction
    transactions.push({
      id: `mining_reward_${height}`,
      from: null,
      to: 'PGminer' + height.toString().padStart(34, '0'),
      amount: 10.0,
      fee: 0.0,
      type: 'mining_reward',
      timestamp: Date.now()
    });
    
    // Add some random transactions
    const numTx = Math.floor(Math.random() * 5) + 1;
    for (let i = 0; i < numTx; i++) {
      transactions.push({
        id: `tx_${height}_${i}`,
        from: 'PG' + Math.random().toString(36).substring(2, 40),
        to: 'PG' + Math.random().toString(36).substring(2, 40),
        amount: Math.random() * 100,
        fee: 0.01,
        type: 'transfer',
        timestamp: Date.now() - Math.random() * 600000
      });
    }
    
    return transactions;
  }

  /**
   * Validate a block (simplified)
   */
  validateBlock(block) {
    // Basic validation
    if (!block.hash || !block.previousHash || block.index < 0) {
      return false;
    }
    
    // Check if previous hash matches
    if (block.index > 0 && block.previousHash !== this.localBlockchain.lastBlockHash) {
      return false;
    }
    
    return true;
  }

  /**
   * Save block to local storage
   */
  async saveBlockToStorage(block) {
    // In a real implementation, this would save to a database like LevelDB
    // For now, we'll just simulate the save
    await this.sleep(10);
  }

  /**
   * Get blockchain info
   */
  getBlockchainInfo() {
    return {
      height: this.localBlockchain.height,
      lastBlockHash: this.localBlockchain.lastBlockHash,
      totalBlocks: this.localBlockchain.blocks.length,
      isConnected: this.isConnected,
      peers: this.peers.length,
      isSyncing: this.isSyncing
    };
  }

  /**
   * Get balance for an address
   */
  async getBalance(address) {
    try {
      let balance = 0;
      
      // Calculate balance from all blocks
      for (const block of this.localBlockchain.blocks) {
        for (const tx of block.transactions) {
          if (tx.to === address) {
            balance += tx.amount;
          }
          if (tx.from === address) {
            balance -= (tx.amount + tx.fee);
          }
        }
      }
      
      return balance;
      
    } catch (error) {
      throw new Error(`Error getting balance: ${error.message}`);
    }
  }

  /**
   * Get transaction history for an address
   */
  async getTransactionHistory(address, limit = 50) {
    try {
      const transactions = [];
      
      // Search through all blocks
      for (const block of this.localBlockchain.blocks) {
        for (const tx of block.transactions) {
          if (tx.from === address || tx.to === address) {
            transactions.push({
              ...tx,
              blockIndex: block.index,
              blockHash: block.hash,
              confirmations: this.localBlockchain.height - block.index
            });
          }
        }
      }
      
      // Sort by timestamp (newest first) and limit
      return transactions
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, limit);
      
    } catch (error) {
      throw new Error(`Error getting transaction history: ${error.message}`);
    }
  }

  /**
   * Broadcast a transaction to the network
   */
  async broadcastTransaction(transaction) {
    try {
      if (!this.isConnected) {
        throw new Error('Not connected to network');
      }
      
      // In a real implementation, this would broadcast to P2P network
      // For now, we'll simulate adding to pending transactions
      
      this.emit('status', { 
        type: 'success', 
        message: `Transacción ${transaction.id} enviada a la red` 
      });
      
      return {
        success: true,
        transactionId: transaction.id,
        message: 'Transaction broadcasted successfully'
      };
      
    } catch (error) {
      throw new Error(`Error broadcasting transaction: ${error.message}`);
    }
  }

  /**
   * Utility function to sleep
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = new BlockchainService();