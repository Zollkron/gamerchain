const crypto = require('crypto');
const bip39 = require('bip39');
const HDKey = require('hdkey');
const secp256k1 = require('secp256k1');
const Store = require('electron-store');
const CryptoJS = require('crypto-js');
const NetworkService = require('./NetworkService');
const TransactionService = require('./TransactionService');

class WalletService {
  constructor() {
    this.store = new Store({
      name: 'playergold-wallets',
      encryptionKey: 'playergold-secure-key'
    });
  }

  /**
   * Generate a new wallet with mnemonic phrase
   * @returns {Object} Wallet data with address, mnemonic, and encrypted private key
   */
  async generateWallet() {
    try {
      // Generate 12-word mnemonic phrase
      const mnemonic = bip39.generateMnemonic(128);
      
      // Generate seed from mnemonic
      const seed = await bip39.mnemonicToSeed(mnemonic);
      
      // Create HD wallet
      const hdkey = HDKey.fromMasterSeed(seed);
      
      // Derive key using BIP44 path for PlayerGold (m/44'/60'/0'/0/0)
      const derivedKey = hdkey.derive("m/44'/60'/0'/0/0");
      
      // Get private and public keys
      const privateKey = derivedKey.privateKey;
      const publicKey = secp256k1.publicKeyCreate(privateKey);
      
      // Generate address from public key (simplified - using hash of public key)
      const address = this.generateAddress(publicKey);
      
      // Create wallet object
      const wallet = {
        id: crypto.randomUUID(),
        name: `Wallet ${Date.now()}`,
        address: address,
        mnemonic: mnemonic,
        privateKey: privateKey.toString('hex'),
        publicKey: publicKey.toString('hex'),
        createdAt: new Date().toISOString(),
        balance: '0'
      };

      // Store encrypted wallet
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
      imported: wallet.imported
    };

    // Get existing wallets and add new one
    const wallets = this.store.get('wallets', []);
    wallets.push(secureWallet);
    this.store.set('wallets', wallets);
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

      const balanceResult = await NetworkService.getBalance(wallet.address);
      
      if (balanceResult.success) {
        // Update cached balance
        wallet.balance = balanceResult.balance;
        this.store.set('wallets', wallets);
      }

      return balanceResult;
    } catch (error) {
      return {
        success: false,
        error: error.message,
        balance: '0'
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
      
      return result;
    } catch (error) {
      return {
        success: false,
        error: error.message
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

      const result = await TransactionService.getTransactionHistory(
        wallet.address, 
        limit, 
        offset
      );
      
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
      // Get fresh balance
      const balanceResult = await this.getWalletBalance(walletId);
      
      // Get recent transactions
      const historyResult = await this.getTransactionHistory(walletId, 10, 0);
      
      return {
        success: true,
        balance: balanceResult.balance || '0',
        recentTransactions: historyResult.transactions || [],
        syncedAt: new Date().toISOString()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
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

      const result = await NetworkService.requestFaucetTokens(wallet.address, amount);
      
      if (result.success) {
        // Refresh balance after faucet request
        setTimeout(() => {
          this.getWalletBalance(walletId);
        }, 5000); // Wait 5 seconds then refresh
      }
      
      return result;
    } catch (error) {
      return {
        success: false,
        error: error.message
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
}

module.exports = new WalletService();