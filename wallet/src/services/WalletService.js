const crypto = require('crypto');
const bip39 = require('bip39');
const HDKey = require('hdkey');
const secp256k1 = require('secp256k1');
const Store = require('electron-store');
const CryptoJS = require('crypto-js');
const NetworkService = require('./NetworkService');
const TransactionService = require('./TransactionService');
const { GenesisStateManager } = require('./GenesisStateManager');

class WalletService {
  constructor() {
    this.store = new Store({
      name: 'playergold-wallets',
      encryptionKey: 'playergold-secure-key'
    });
    
    // Initialize GenesisStateManager
    this.genesisStateManager = new GenesisStateManager();
    this.genesisStateManager.initialize(NetworkService);
  }

  /**
   * Generate a new wallet with mnemonic phrase
   * Works independently of network connectivity
   * @returns {Object} Wallet data with address, mnemonic, and encrypted private key
   */
  async generateWallet() {
    try {
      // Generate 12-word mnemonic phrase (purely local operation)
      const mnemonic = bip39.generateMnemonic(128);
      
      // Generate seed from mnemonic (purely local operation)
      const seed = await bip39.mnemonicToSeed(mnemonic);
      
      // Create HD wallet (purely local operation)
      const hdkey = HDKey.fromMasterSeed(seed);
      
      // Derive key using BIP44 path for PlayerGold (m/44'/60'/0'/0/0)
      const derivedKey = hdkey.derive("m/44'/60'/0'/0/0");
      
      // Get private and public keys (purely local operation)
      const privateKey = derivedKey.privateKey;
      const publicKey = secp256k1.publicKeyCreate(privateKey);
      
      // Generate address from public key (purely local operation)
      const address = this.generateAddress(publicKey);
      
      // Validate generated address locally
      if (!this.isValidAddress(address)) {
        throw new Error('Generated address failed validation');
      }
      
      // Create wallet object
      const wallet = {
        id: crypto.randomUUID(),
        name: `Wallet ${Date.now()}`,
        address: address,
        mnemonic: mnemonic,
        privateKey: privateKey.toString('hex'),
        publicKey: publicKey.toString('hex'),
        createdAt: new Date().toISOString(),
        balance: '0',
        networkIndependent: true // Flag to indicate this wallet was created without network
      };

      // Store encrypted wallet (local storage operation)
      await this.storeWallet(wallet);
      
      // Return wallet without private key for security
      const { privateKey: _, ...safeWallet } = wallet;
      return {
        success: true,
        wallet: safeWallet
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Import wallet from mnemonic phrase
   * @param {string} mnemonic - 12-word mnemonic phrase
   * @returns {Object} Imported wallet data
   */
  async importWallet(mnemonic) {
    try {
      // Validate mnemonic
      if (!bip39.validateMnemonic(mnemonic)) {
        throw new Error('Invalid mnemonic phrase');
      }

      // Generate seed from mnemonic
      const seed = await bip39.mnemonicToSeed(mnemonic);
      
      // Create HD wallet
      const hdkey = HDKey.fromMasterSeed(seed);
      
      // Derive key using BIP44 path
      const derivedKey = hdkey.derive("m/44'/60'/0'/0/0");
      
      // Get keys and address
      const privateKey = derivedKey.privateKey;
      const publicKey = secp256k1.publicKeyCreate(privateKey);
      const address = this.generateAddress(publicKey);

      // Check if wallet already exists
      const existingWallets = this.store.get('wallets', []);
      const existingWallet = existingWallets.find(w => w.address === address);
      
      if (existingWallet) {
        throw new Error('Wallet already exists');
      }

      // Create wallet object
      const wallet = {
        id: crypto.randomUUID(),
        name: `Imported Wallet ${Date.now()}`,
        address: address,
        mnemonic: mnemonic,
        privateKey: privateKey.toString('hex'),
        publicKey: publicKey.toString('hex'),
        createdAt: new Date().toISOString(),
        balance: '0',
        imported: true
      };

      // Store encrypted wallet
      await this.storeWallet(wallet);
      
      // Return wallet without private key
      const { privateKey: _, ...safeWallet } = wallet;
      return {
        success: true,
        wallet: safeWallet
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Export wallet mnemonic phrase
   * @param {string} walletId - Wallet ID to export
   * @returns {Object} Wallet mnemonic phrase
   */
  async exportWallet(walletId) {
    try {
      const wallets = this.store.get('wallets', []);
      const wallet = wallets.find(w => w.id === walletId);
      
      if (!wallet) {
        throw new Error('Wallet not found');
      }

      // Decrypt mnemonic
      const decryptedMnemonic = CryptoJS.AES.decrypt(wallet.encryptedMnemonic, 'playergold-wallet-key').toString(CryptoJS.enc.Utf8);
      
      return {
        success: true,
        mnemonic: decryptedMnemonic,
        address: wallet.address
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get all stored wallets
   * @returns {Array} List of wallets (without private keys)
   */
  async getWallets() {
    try {
      const wallets = this.store.get('wallets', []);
      
      // Return wallets without sensitive data
      const safeWallets = wallets.map(wallet => ({
        id: wallet.id,
        name: wallet.name,
        address: wallet.address,
        balance: wallet.balance || '0',
        createdAt: wallet.createdAt,
        imported: wallet.imported || false
      }));

      return {
        success: true,
        wallets: safeWallets
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        wallets: []
      };
    }
  }

  /**
   * Store wallet securely with encryption
   * @param {Object} wallet - Wallet object to store
   */
  async storeWallet(wallet) {
    // Encrypt sensitive data
    const encryptedMnemonic = CryptoJS.AES.encrypt(wallet.mnemonic, 'playergold-wallet-key').toString();
    const encryptedPrivateKey = CryptoJS.AES.encrypt(wallet.privateKey, 'playergold-wallet-key').toString();

    // Create secure wallet object for storage
    const secureWallet = {
      id: wallet.id,
      name: wallet.name,
      address: wallet.address,
      publicKey: wallet.publicKey,
      encryptedMnemonic: encryptedMnemonic,
      encryptedPrivateKey: encryptedPrivateKey,
      createdAt: wallet.createdAt,
      balance: wallet.balance,
      imported: wallet.imported,
      networkIndependent: wallet.networkIndependent || false
    };

    // Get existing wallets and add new one
    const wallets = this.store.get('wallets', []);
    wallets.push(secureWallet);
    this.store.set('wallets', wallets);
    
    // Also persist address separately for genesis block rewards
    await this.persistAddressForGenesis(wallet.address, wallet.id);
  }

  /**
   * Persist wallet address for genesis block rewards
   * @param {string} address - Wallet address
   * @param {string} walletId - Wallet ID
   */
  async persistAddressForGenesis(address, walletId) {
    const genesisAddresses = this.store.get('genesis_addresses', []);
    
    // Check if address already exists
    const existingEntry = genesisAddresses.find(entry => entry.address === address);
    if (!existingEntry) {
      genesisAddresses.push({
        address: address,
        walletId: walletId,
        createdAt: new Date().toISOString(),
        eligibleForGenesis: true
      });
      this.store.set('genesis_addresses', genesisAddresses);
    }
  }

  /**
   * Get addresses eligible for genesis block rewards
   * @returns {Array} List of addresses eligible for genesis rewards
   */
  getGenesisEligibleAddresses() {
    return this.store.get('genesis_addresses', []);
  }

  /**
   * Generate wallet in offline mode (explicitly network-independent)
   * @returns {Object} Wallet data created without any network dependency
   */
  async generateOfflineWallet() {
    // This method is identical to generateWallet but explicitly documented as offline
    return await this.generateWallet();
  }

  static async generateOfflineWallet() {
    // Generate 12-word mnemonic phrase (purely local operation)
    const mnemonic = bip39.generateMnemonic(128);
    
    // Generate seed from mnemonic (purely local operation)
    const seed = await bip39.mnemonicToSeed(mnemonic);
    
    // Create HD wallet (purely local operation)
    const hdkey = HDKey.fromMasterSeed(seed);
    
    // Derive key using BIP44 path for PlayerGold (m/44'/60'/0'/0/0)
    const derivedKey = hdkey.derive("m/44'/60'/0'/0/0");
    
    // Get private and public keys (purely local operation)
    const privateKey = derivedKey.privateKey;
    const publicKey = secp256k1.publicKeyCreate(privateKey);
    
    // Generate address from public key (purely local operation)
    const address = WalletService.generateAddress(publicKey);
    
    // Validate generated address locally
    if (!WalletService.isValidAddress(address)) {
      throw new Error('Generated address failed validation');
    }
    
    // Create wallet object (without storing it)
    const wallet = {
      id: crypto.randomUUID(),
      name: `Wallet ${Date.now()}`,
      address: address,
      mnemonic: mnemonic,
      privateKey: privateKey.toString('hex'),
      publicKey: publicKey.toString('hex'),
      createdAt: new Date().toISOString(),
      balance: '0',
      networkIndependent: true
    };

    return {
      id: wallet.id,
      name: wallet.name,
      address: wallet.address,
      mnemonic: wallet.mnemonic,
      createdAt: wallet.createdAt,
      balance: wallet.balance
    };
  }

  /**
   * Generate address from public key
   * @param {Buffer} publicKey - Public key buffer
   * @returns {string} Generated address
   */
  generateAddress(publicKey) {
    // Simple address generation (in production, use proper address format)
    const hash = crypto.createHash('sha256').update(publicKey).digest();
    const address = 'PG' + hash.toString('hex').substring(0, 38);
    return address;
  }

  static generateAddress(publicKey) {
    // Simple address generation (in production, use proper address format)
    const hash = crypto.createHash('sha256').update(publicKey).digest();
    const address = 'PG' + hash.toString('hex').substring(0, 38);
    return address;
  }

  /**
   * Validate address format locally
   * @param {string} address - Address to validate
   * @returns {boolean} True if valid
   */
  isValidAddress(address) {
    // PlayerGold addresses start with 'PG' and are 40 characters total
    return /^PG[a-fA-F0-9]{38}$/.test(address);
  }

  static isValidAddress(address) {
    // PlayerGold addresses start with 'PG' and are 40 characters total
    return /^PG[a-fA-F0-9]{38}$/.test(address);
  }

  /**
   * Update wallet name
   * @param {string} walletId - Wallet ID
   * @param {string} newName - New wallet name
   */
  async updateWalletName(walletId, newName) {
    try {
      const wallets = this.store.get('wallets', []);
      const walletIndex = wallets.findIndex(w => w.id === walletId);
      
      if (walletIndex === -1) {
        throw new Error('Wallet not found');
      }

      wallets[walletIndex].name = newName;
      this.store.set('wallets', wallets);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Delete wallet
   * @param {string} walletId - Wallet ID to delete
   */
  async deleteWallet(walletId) {
    try {
      const wallets = this.store.get('wallets', []);
      const filteredWallets = wallets.filter(w => w.id !== walletId);
      
      if (wallets.length === filteredWallets.length) {
        throw new Error('Wallet not found');
      }

      this.store.set('wallets', filteredWallets);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get wallet balance from network
   * @param {string} walletId - Wallet ID
   * @returns {Object} Balance information
   */
  async getWalletBalance(walletId) {
    try {
      const wallets = this.store.get('wallets', []);
      const wallet = wallets.find(w => w.id === walletId);
      
      if (!wallet) {
        throw new Error('Wallet not found');
      }

      // Check genesis state first
      const genesisState = await this.genesisStateManager.checkGenesisExists();
      
      if (!genesisState.exists) {
        // No genesis block exists - return zero balance with clear message
        return {
          success: true,
          balance: '0',
          requiresGenesis: true,
          message: 'Blockchain not initialized - genesis block required',
          address: wallet.address
        };
      }

      // Check if balance query operation is allowed
      if (!this.genesisStateManager.isOperationAllowed('balance_query')) {
        const networkState = this.genesisStateManager.getCurrentNetworkState();
        return {
          success: false,
          balance: '0',
          error: `Balance query not available in current network state: ${networkState}`,
          requiresGenesis: !genesisState.exists,
          address: wallet.address
        };
      }

      // Genesis exists and operation is allowed - get real balance
      const balanceResult = await NetworkService.getBalance(wallet.address);
      
      if (balanceResult.success) {
        // Update cached balance only if we got real data
        wallet.balance = balanceResult.balance;
        this.store.set('wallets', wallets);
        
        // Ensure no mock data is returned
        return {
          ...balanceResult,
          requiresGenesis: false,
          isMock: false
        };
      } else {
        // Network error - return error state with zero balance
        return {
          success: false,
          error: balanceResult.error || 'Failed to fetch balance from network',
          balance: '0',
          requiresGenesis: false,
          isMock: false,
          address: wallet.address
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        balance: '0',
        requiresGenesis: true,
        isMock: false
      };
    }
  }

  /**
   * Send transaction from wallet
   * @param {string} walletId - Wallet ID
   * @param {Object} transactionData - Transaction details
   * @returns {Object} Transaction result
   */
  async sendTransaction(walletId, transactionData) {
    try {
      const wallets = this.store.get('wallets', []);
      const wallet = wallets.find(w => w.id === walletId);
      
      if (!wallet) {
        throw new Error('Wallet not found');
      }

      // Check genesis state first
      const genesisState = await this.genesisStateManager.checkGenesisExists();
      
      if (!genesisState.exists) {
        return {
          success: false,
          error: 'Cannot send transactions - blockchain not initialized (genesis block required)',
          requiresGenesis: true,
          operationBlocked: true
        };
      }

      // Check if send transaction operation is allowed
      if (!this.genesisStateManager.isOperationAllowed('send_transaction')) {
        const networkState = this.genesisStateManager.getCurrentNetworkState();
        return {
          success: false,
          error: `Transaction sending not available in current network state: ${networkState}`,
          requiresGenesis: !genesisState.exists,
          operationBlocked: true
        };
      }

      // Decrypt private key
      const decryptedPrivateKey = CryptoJS.AES.decrypt(
        wallet.encryptedPrivateKey, 
        'playergold-wallet-key'
      ).toString(CryptoJS.enc.Utf8);

      // Prepare transaction parameters
      const txParams = {
        fromAddress: wallet.address,
        toAddress: transactionData.toAddress,
        amount: transactionData.amount,
        privateKey: decryptedPrivateKey,
        transactionType: transactionData.transactionType || 'transfer',
        memo: transactionData.memo || ''
      };

      // Send transaction through TransactionService
      const result = await TransactionService.sendTransaction(txParams);
      
      return {
        ...result,
        requiresGenesis: false,
        operationBlocked: false
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        requiresGenesis: true,
        operationBlocked: false
      };
    }
  }

  /**
   * Get transaction history for wallet
   * @param {string} walletId - Wallet ID
   * @param {number} limit - Number of transactions
   * @param {number} offset - Pagination offset
   * @returns {Object} Transaction history
   */
  async getTransactionHistory(walletId, limit = 50, offset = 0) {
    try {
      const wallets = this.store.get('wallets', []);
      const wallet = wallets.find(w => w.id === walletId);
      
      if (!wallet) {
        throw new Error('Wallet not found');
      }

      // Check genesis state first
      const genesisState = await this.genesisStateManager.checkGenesisExists();
      
      if (!genesisState.exists) {
        // No genesis block exists - return empty history with clear message
        return {
          success: true,
          transactions: [],
          requiresGenesis: true,
          message: 'No transaction history available - blockchain not initialized',
          address: wallet.address,
          isMock: false
        };
      }

      // Check if transaction history operation is allowed
      if (!this.genesisStateManager.isOperationAllowed('transaction_history')) {
        const networkState = this.genesisStateManager.getCurrentNetworkState();
        return {
          success: false,
          transactions: [],
          error: `Transaction history not available in current network state: ${networkState}`,
          requiresGenesis: !genesisState.exists,
          address: wallet.address,
          isMock: false
        };
      }

      // Genesis exists and operation is allowed - get real transaction history
      const result = await TransactionService.getTransactionHistory(
        wallet.address, 
        limit, 
        offset
      );
      
      // Ensure no mock data is returned
      return {
        ...result,
        requiresGenesis: false,
        isMock: false
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        transactions: [],
        requiresGenesis: true,
        isMock: false
      };
    }
  }

  /**
   * Get pending transactions for wallet
   * @param {string} walletId - Wallet ID
   * @returns {Array} Pending transactions
   */
  getPendingTransactions(walletId) {
    try {
      const wallets = this.store.get('wallets', []);
      const wallet = wallets.find(w => w.id === walletId);
      
      if (!wallet) {
        return [];
      }

      return TransactionService.getPendingTransactions(wallet.address);
    } catch (error) {
      return [];
    }
  }

  /**
   * Sync wallet with network
   * @param {string} walletId - Wallet ID
   * @returns {Object} Sync result
   */
  async syncWallet(walletId) {
    try {
      // Clear any cached mock data first
      const wallets = this.store.get('wallets', []);
      const wallet = wallets.find(w => w.id === walletId);
      
      if (wallet) {
        // Reset cached balance to ensure fresh data
        wallet.balance = '0';
        this.store.set('wallets', wallets);
      }

      // Get fresh balance (will check genesis state)
      const balanceResult = await this.getWalletBalance(walletId);
      
      // Get recent transactions (will check genesis state)
      const historyResult = await this.getTransactionHistory(walletId, 10, 0);
      
      return {
        success: true,
        balance: balanceResult.balance || '0',
        recentTransactions: historyResult.transactions || [],
        requiresGenesis: balanceResult.requiresGenesis || historyResult.requiresGenesis || false,
        networkState: this.genesisStateManager.getCurrentNetworkState(),
        genesisExists: (await this.genesisStateManager.checkGenesisExists()).exists,
        syncedAt: new Date().toISOString(),
        isMock: false
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        balance: '0',
        recentTransactions: [],
        requiresGenesis: true,
        isMock: false
      };
    }
  }

  /**
   * Request tokens from testnet faucet
   * @param {string} walletId - Wallet ID
   * @param {number} amount - Amount to request (default 1000)
   * @returns {Object} Faucet result
   */
  async requestFaucetTokens(walletId, amount = 1000) {
    try {
      const wallets = this.store.get('wallets', []);
      const wallet = wallets.find(w => w.id === walletId);
      
      if (!wallet) {
        throw new Error('Wallet not found');
      }

      // Check genesis state first
      const genesisState = await this.genesisStateManager.checkGenesisExists();
      
      if (!genesisState.exists) {
        return {
          success: false,
          error: 'Cannot request faucet tokens - blockchain not initialized (genesis block required)',
          requiresGenesis: true,
          operationBlocked: true
        };
      }

      // Check if faucet operation is allowed
      if (!this.genesisStateManager.isOperationAllowed('faucet')) {
        const networkState = this.genesisStateManager.getCurrentNetworkState();
        return {
          success: false,
          error: `Faucet requests not available in current network state: ${networkState}`,
          requiresGenesis: !genesisState.exists,
          operationBlocked: true
        };
      }

      const result = await NetworkService.requestFaucetTokens(wallet.address, amount);
      
      if (result.success) {
        // Refresh balance after faucet request
        setTimeout(() => {
          this.getWalletBalance(walletId);
        }, 5000); // Wait 5 seconds then refresh
      }
      
      return {
        ...result,
        requiresGenesis: false,
        operationBlocked: false
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        requiresGenesis: true,
        operationBlocked: false
      };
    }
  }

  /**
   * Get network information
   * @returns {Object} Network info
   */
  getNetworkInfo() {
    return NetworkService.getNetworkInfo();
  }

  /**
   * Switch network (testnet/mainnet)
   * @param {string} network - 'testnet' or 'mainnet'
   * @returns {Object} Switch result
   */
  switchNetwork(network) {
    try {
      NetworkService.switchNetwork(network);
      return {
        success: true,
        network: network,
        networkInfo: NetworkService.getNetworkInfo()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get genesis state manager instance (for testing)
   * @returns {GenesisStateManager} Genesis state manager instance
   */
  getGenesisStateManager() {
    return this.genesisStateManager;
  }

  /**
   * Check if operation is allowed in current state
   * @param {string} operation - Operation to check
   * @returns {boolean} True if operation is allowed
   */
  isOperationAllowed(operation) {
    return this.genesisStateManager.isOperationAllowed(operation);
  }

  /**
   * Get current network state
   * @returns {string} Current network state
   */
  getCurrentNetworkState() {
    return this.genesisStateManager.getCurrentNetworkState();
  }
}

const walletServiceInstance = new WalletService();

// Add static methods to the instance for backward compatibility with tests
walletServiceInstance.isValidAddress = WalletService.isValidAddress;
walletServiceInstance.generateAddress = WalletService.generateAddress;
walletServiceInstance.generateOfflineWallet = WalletService.generateOfflineWallet;

module.exports = walletServiceInstance;