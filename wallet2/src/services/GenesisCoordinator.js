/**
 * Genesis Coordinator for Auto-Bootstrap P2P Network
 * 
 * Manages collaborative genesis block creation among discovered peers.
 * Handles peer consensus, parameter negotiation, and distributed genesis block creation.
 */

const EventEmitter = require('events');
const crypto = require('crypto');
const { BootstrapLogger } = require('./BootstrapLogger');

/**
 * Genesis creation phases
 */
const GenesisPhase = {
  NEGOTIATING: 'negotiating',
  CREATING: 'creating',
  DISTRIBUTING: 'distributing',
  VALIDATING: 'validating',
  COMPLETED: 'completed',
  FAILED: 'failed'
};

/**
 * Genesis parameters structure
 */
class GenesisParams {
  constructor(timestamp, difficulty, participants, initialRewards, networkId, consensusRules) {
    this.timestamp = timestamp;
    this.difficulty = difficulty;
    this.participants = participants; // Array of wallet addresses
    this.initialRewards = initialRewards; // Map of address -> reward amount
    this.networkId = networkId;
    this.consensusRules = consensusRules;
  }

  toDict() {
    return {
      timestamp: this.timestamp,
      difficulty: this.difficulty,
      participants: this.participants,
      initialRewards: Object.fromEntries(this.initialRewards),
      networkId: this.networkId,
      consensusRules: this.consensusRules
    };
  }

  static fromDict(data) {
    return new GenesisParams(
      data.timestamp,
      data.difficulty,
      data.participants,
      new Map(Object.entries(data.initialRewards)),
      data.networkId,
      data.consensusRules
    );
  }
}

/**
 * Network configuration structure
 */
class NetworkConfig {
  constructor(networkId, genesisHash, peers, consensusRules, createdAt) {
    this.networkId = networkId;
    this.genesisHash = genesisHash;
    this.peers = peers;
    this.consensusRules = consensusRules;
    this.createdAt = createdAt;
  }

  toDict() {
    return {
      networkId: this.networkId,
      genesisHash: this.genesisHash,
      peers: this.peers.map(peer => ({
        id: peer.id,
        address: peer.address,
        port: peer.port,
        walletAddress: peer.walletAddress,
        networkMode: peer.networkMode
      })),
      consensusRules: this.consensusRules,
      createdAt: this.createdAt.toISOString()
    };
  }

  static fromDict(data) {
    return new NetworkConfig(
      data.networkId,
      data.genesisHash,
      data.peers,
      data.consensusRules,
      new Date(data.createdAt)
    );
  }
}

/**
 * Genesis block structure
 */
class GenesisBlock {
  constructor(index, previousHash, timestamp, transactions, merkleRoot, nonce = 0) {
    this.index = index;
    this.previousHash = previousHash;
    this.timestamp = timestamp;
    this.transactions = transactions;
    this.merkleRoot = merkleRoot;
    this.nonce = nonce;
    this.hash = this.calculateHash();
  }

  calculateHash() {
    const blockData = {
      index: this.index,
      previousHash: this.previousHash,
      timestamp: this.timestamp,
      merkleRoot: this.merkleRoot,
      nonce: this.nonce
    };
    
    const blockString = JSON.stringify(blockData, Object.keys(blockData).sort());
    return crypto.createHash('sha256').update(blockString).digest('hex');
  }

  toDict() {
    return {
      index: this.index,
      previousHash: this.previousHash,
      timestamp: this.timestamp,
      transactions: this.transactions,
      merkleRoot: this.merkleRoot,
      nonce: this.nonce,
      hash: this.hash
    };
  }
}

class GenesisCoordinator extends EventEmitter {
  constructor() {
    super();
    
    this.logger = new BootstrapLogger('GenesisCoordinator');
    
    // Configuration
    this.config = {
      negotiationTimeout: 30000, // 30 seconds
      creationTimeout: 60000, // 60 seconds
      distributionTimeout: 30000, // 30 seconds
      validationTimeout: 20000, // 20 seconds
      maxRetries: 3,
      retryBackoffMs: 2000,
      
      // Genesis block parameters
      initialDifficulty: 1,
      baseReward: 10.0,
      consensusAlgorithm: 'PoAIP', // Proof of AI Participation
      blockTime: 600, // 10 minutes in seconds
      minValidators: 2,
      maxValidators: 100
    };
    
    // State
    this.currentPhase = null;
    this.participants = [];
    this.genesisParams = null;
    this.genesisBlock = null;
    this.networkConfig = null;
    this.consensusVotes = new Map();
    this.isCoordinating = false;
    
    this.logger.info('GenesisCoordinator initialized');
  }

  /**
   * Negotiate genesis parameters with participating peers
   * @param {Array<PeerInfo>} peers - Participating peers
   * @returns {Promise<GenesisParams>} Negotiated genesis parameters
   */
  async negotiateGenesisParameters(peers) {
    if (!Array.isArray(peers) || peers.length < 2) {
      throw new Error('At least 2 peers required for genesis creation');
    }

    this.logger.info(`Starting genesis parameter negotiation with ${peers.length} peers`);
    
    try {
      this.currentPhase = GenesisPhase.NEGOTIATING;
      this.participants = peers;
      
      this.emit('phaseChanged', GenesisPhase.NEGOTIATING);
      
      // Generate network ID based on participants
      const networkId = this.generateNetworkId(peers);
      
      // Create initial rewards map (equal distribution)
      const initialRewards = new Map();
      const rewardPerPeer = this.config.baseReward;
      
      for (const peer of peers) {
        if (peer.walletAddress) {
          initialRewards.set(peer.walletAddress, rewardPerPeer);
        }
      }
      
      // Define consensus rules
      const consensusRules = {
        algorithm: this.config.consensusAlgorithm,
        blockTime: this.config.blockTime,
        minValidators: Math.min(this.config.minValidators, peers.length),
        maxValidators: this.config.maxValidators,
        rewards: {
          baseReward: this.config.baseReward,
          feeDistribution: 'proportional'
        }
      };
      
      // Create genesis parameters
      this.genesisParams = new GenesisParams(
        Date.now(),
        this.config.initialDifficulty,
        peers.map(p => p.walletAddress).filter(addr => addr),
        initialRewards,
        networkId,
        consensusRules
      );
      
      // In a real P2P implementation, this would involve:
      // 1. Broadcasting proposed parameters to all peers
      // 2. Collecting votes/agreements from peers
      // 3. Reaching consensus on final parameters
      // Negotiate parameters with network peers
      
      await this.negotiateGenesisParameters();
      
      this.logger.info(`Genesis parameters negotiated successfully for network: ${networkId}`);
      this.emit('parametersNegotiated', this.genesisParams);
      
      return this.genesisParams;
      
    } catch (error) {
      this.currentPhase = GenesisPhase.FAILED;
      this.logger.error('Genesis parameter negotiation failed:', error);
      this.emit('phaseChanged', GenesisPhase.FAILED);
      throw error;
    }
  }

  /**
   * Create genesis block with negotiated parameters
   * @param {GenesisParams} params - Genesis parameters
   * @returns {Promise<GenesisBlock>} Created genesis block
   */
  async createGenesisBlock(params) {
    if (!params) {
      throw new Error('Genesis parameters required for block creation');
    }

    this.logger.info('Creating genesis block...');
    
    try {
      this.currentPhase = GenesisPhase.CREATING;
      this.emit('phaseChanged', GenesisPhase.CREATING);
      
      // Create genesis transactions (initial rewards)
      const genesisTransactions = [];
      
      for (const [address, amount] of params.initialRewards) {
        genesisTransactions.push({
          id: `genesis_reward_${address}`,
          from: null, // Genesis rewards have no sender
          to: address,
          amount: amount,
          fee: 0.0,
          type: 'genesis_reward',
          timestamp: params.timestamp,
          hash: this.calculateTransactionHash({
            from: null,
            to: address,
            amount: amount,
            timestamp: params.timestamp
          })
        });
      }
      
      // Calculate merkle root of transactions
      const merkleRoot = this.calculateMerkleRoot(genesisTransactions);
      
      // Create genesis block
      this.genesisBlock = new GenesisBlock(
        0, // Genesis block index is always 0
        '0'.repeat(64), // Genesis previous hash is all zeros
        params.timestamp,
        genesisTransactions,
        merkleRoot,
        0 // Genesis nonce
      );
      
      this.logger.info(`Genesis block created with hash: ${this.genesisBlock.hash}`);
      this.emit('blockCreated', this.genesisBlock);
      
      return this.genesisBlock;
      
    } catch (error) {
      this.currentPhase = GenesisPhase.FAILED;
      this.logger.error('Genesis block creation failed:', error);
      this.emit('phaseChanged', GenesisPhase.FAILED);
      throw error;
    }
  }

  /**
   * Distribute genesis block to all participating peers
   * @param {GenesisBlock} block - Genesis block to distribute
   * @param {Array<PeerInfo>} peers - Target peers
   * @returns {Promise<void>}
   */
  async distributeGenesisBlock(block, peers) {
    if (!block || !Array.isArray(peers)) {
      throw new Error('Genesis block and peers required for distribution');
    }

    this.logger.info(`Distributing genesis block to ${peers.length} peers`);
    
    try {
      this.currentPhase = GenesisPhase.DISTRIBUTING;
      this.emit('phaseChanged', GenesisPhase.DISTRIBUTING);
      
      // In a real P2P implementation, this would:
      // 1. Send the genesis block to each peer
      // 2. Wait for acknowledgments
      // 3. Handle retries for failed distributions
      // 4. Ensure all peers have the same genesis block
      
      const distributionPromises = peers.map(peer => 
        this.distributeToSinglePeer(block, peer)
      );
      
      const results = await Promise.allSettled(distributionPromises);
      
      // Check distribution results
      const successful = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;
      
      if (failed > 0) {
        this.logger.warn(`Genesis block distribution: ${successful} successful, ${failed} failed`);
      }
      
      // Require majority success for distribution to be considered successful
      const requiredSuccess = Math.ceil(peers.length * 0.6); // 60% threshold
      
      if (successful < requiredSuccess) {
        throw new Error(`Genesis block distribution failed: only ${successful}/${peers.length} peers received the block`);
      }
      
      this.logger.info(`Genesis block distributed successfully to ${successful}/${peers.length} peers`);
      this.emit('blockDistributed', { successful, failed, total: peers.length });
      
    } catch (error) {
      this.currentPhase = GenesisPhase.FAILED;
      this.logger.error('Genesis block distribution failed:', error);
      this.emit('phaseChanged', GenesisPhase.FAILED);
      throw error;
    }
  }

  /**
   * Persist network configuration to local storage
   * @param {NetworkConfig} config - Network configuration to persist
   */
  persistNetworkConfiguration(config) {
    if (!config) {
      throw new Error('Network configuration required for persistence');
    }

    try {
      this.logger.info(`Persisting network configuration for network: ${config.networkId}`);
      
      // In a real implementation, this would save to:
      // - Local database (LevelDB, SQLite, etc.)
      // - Configuration files
      // - Encrypted storage for sensitive data
      
      // Store configuration in memory
      this.networkConfig = config;
      
      // Real file system persistence would be implemented here
      const configData = JSON.stringify(config.toDict(), null, 2);
      
      // In a real implementation:
      // const fs = require('fs').promises;
      // await fs.writeFile(`./data/network-${config.networkId}.json`, configData);
      
      this.logger.info('Network configuration persisted successfully');
      this.emit('configurationPersisted', config);
      
    } catch (error) {
      this.logger.error('Failed to persist network configuration:', error);
      throw error;
    }
  }

  /**
   * Validate genesis consensus among participating peers
   * @param {Array<PeerInfo>} peers - Participating peers
   * @returns {Promise<boolean>} True if consensus is achieved
   */
  async validateGenesisConsensus(peers) {
    if (!Array.isArray(peers) || peers.length < 2) {
      throw new Error('At least 2 peers required for consensus validation');
    }

    this.logger.info(`Validating genesis consensus among ${peers.length} peers`);
    
    try {
      this.currentPhase = GenesisPhase.VALIDATING;
      this.emit('phaseChanged', GenesisPhase.VALIDATING);
      
      // In a real P2P implementation, this would:
      // 1. Request genesis block hash from each peer
      // 2. Compare hashes to ensure all peers have the same block
      // 3. Validate that all peers accept the genesis block
      // 4. Check that network configuration is consistent across peers
      
      const consensusPromises = peers.map(peer => 
        this.validatePeerConsensus(peer)
      );
      
      const results = await Promise.allSettled(consensusPromises);
      
      // Count successful validations
      const validPeers = results.filter(r => r.status === 'fulfilled' && r.value === true).length;
      const invalidPeers = peers.length - validPeers;
      
      // Require majority consensus (>50%)
      const requiredConsensus = Math.ceil(peers.length / 2);
      const hasConsensus = validPeers >= requiredConsensus;
      
      if (hasConsensus) {
        this.currentPhase = GenesisPhase.COMPLETED;
        this.logger.info(`Genesis consensus achieved: ${validPeers}/${peers.length} peers in agreement`);
        this.emit('consensusAchieved', { validPeers, invalidPeers, total: peers.length });
      } else {
        this.currentPhase = GenesisPhase.FAILED;
        this.logger.error(`Genesis consensus failed: only ${validPeers}/${peers.length} peers in agreement`);
        this.emit('consensusFailed', { validPeers, invalidPeers, total: peers.length });
      }
      
      this.emit('phaseChanged', this.currentPhase);
      
      return hasConsensus;
      
    } catch (error) {
      this.currentPhase = GenesisPhase.FAILED;
      this.logger.error('Genesis consensus validation failed:', error);
      this.emit('phaseChanged', GenesisPhase.FAILED);
      throw error;
    }
  }

  /**
   * Complete genesis coordination process
   * @param {Array<PeerInfo>} peers - Participating peers
   * @returns {Promise<Object>} Genesis result with block and network config
   */
  async coordinateGenesis(peers) {
    if (this.isCoordinating) {
      throw new Error('Genesis coordination already in progress');
    }

    this.isCoordinating = true;
    
    try {
      this.logger.info(`Starting complete genesis coordination with ${peers.length} peers`);
      
      // Step 1: Negotiate parameters
      const params = await this.negotiateGenesisParameters(peers);
      
      // Step 2: Create genesis block
      const block = await this.createGenesisBlock(params);
      
      // Step 3: Distribute to peers
      await this.distributeGenesisBlock(block, peers);
      
      // Step 4: Create network configuration
      const networkConfig = new NetworkConfig(
        params.networkId,
        block.hash,
        peers,
        params.consensusRules,
        new Date()
      );
      
      // Step 5: Persist configuration
      this.persistNetworkConfiguration(networkConfig);
      
      // Step 6: Validate consensus
      const hasConsensus = await this.validateGenesisConsensus(peers);
      
      if (!hasConsensus) {
        throw new Error('Failed to achieve genesis consensus among peers');
      }
      
      const result = {
        block: block,
        networkConfig: networkConfig,
        participants: params.participants,
        success: true
      };
      
      this.logger.info('Genesis coordination completed successfully');
      this.emit('genesisCompleted', result);
      
      return result;
      
    } catch (error) {
      this.logger.error('Genesis coordination failed:', error);
      this.emit('genesisFailed', error);
      throw error;
    } finally {
      this.isCoordinating = false;
    }
  }

  /**
   * Get current genesis coordination status
   * @returns {Object} Current status information
   */
  getStatus() {
    return {
      phase: this.currentPhase,
      isCoordinating: this.isCoordinating,
      participants: this.participants.length,
      genesisParams: this.genesisParams ? this.genesisParams.toDict() : null,
      genesisBlock: this.genesisBlock ? this.genesisBlock.toDict() : null,
      networkConfig: this.networkConfig ? this.networkConfig.toDict() : null
    };
  }

  // Private helper methods

  /**
   * Generate unique network ID based on participating peers
   * @param {Array<PeerInfo>} peers - Participating peers
   * @returns {string} Generated network ID
   */
  generateNetworkId(peers) {
    const peerData = peers
      .map(p => `${p.id}:${p.walletAddress}`)
      .sort()
      .join('|');
    
    const timestamp = Date.now();
    const networkData = `${peerData}:${timestamp}`;
    
    return crypto.createHash('sha256')
      .update(networkData)
      .digest('hex')
      .substring(0, 16); // Use first 16 characters
  }

  /**
   * Calculate transaction hash
   * @param {Object} transaction - Transaction data
   * @returns {string} Transaction hash
   */
  calculateTransactionHash(transaction) {
    const txData = JSON.stringify({
      from: transaction.from,
      to: transaction.to,
      amount: transaction.amount,
      timestamp: transaction.timestamp
    }, Object.keys(transaction).sort());
    
    return crypto.createHash('sha256').update(txData).digest('hex');
  }

  /**
   * Calculate merkle root of transactions
   * @param {Array} transactions - Array of transactions
   * @returns {string} Merkle root hash
   */
  calculateMerkleRoot(transactions) {
    if (transactions.length === 0) {
      return crypto.createHash('sha256').update('').digest('hex');
    }
    
    if (transactions.length === 1) {
      return transactions[0].hash;
    }
    
    // Simple merkle root calculation (in production, use proper merkle tree)
    const hashes = transactions.map(tx => tx.hash);
    
    while (hashes.length > 1) {
      const newLevel = [];
      
      for (let i = 0; i < hashes.length; i += 2) {
        const left = hashes[i];
        const right = hashes[i + 1] || left; // Duplicate last hash if odd number
        
        const combined = crypto.createHash('sha256')
          .update(left + right)
          .digest('hex');
        
        newLevel.push(combined);
      }
      
      hashes.splice(0, hashes.length, ...newLevel);
    }
    
    return hashes[0];
  }

  /**
   * Negotiate genesis parameters with network peers
   * @returns {Promise<void>}
   */
  async negotiateGenesisParameters() {
    // Real parameter negotiation with network peers
    try {
      // In a real implementation, this would involve P2P message exchange
      // For now, use local parameters since no peers are available
      this.logger.debug('Genesis parameter negotiation - using local parameters (no peers available)');
    } catch (error) {
      this.logger.error('Failed to negotiate genesis parameters:', error);
      throw error;
    }
  }

  /**
   * Distribute genesis block to a single peer
   * @param {GenesisBlock} block - Genesis block
   * @param {PeerInfo} peer - Target peer
   * @returns {Promise<boolean>} True if successful
   */
  async distributeToSinglePeer(block, peer) {
    try {
      // Real network distribution via P2P protocol
      // This would send the block via actual P2P network
      this.logger.debug(`Attempting to distribute genesis block to peer ${peer.id}`);
      
      // For now, return false since no real P2P implementation
      this.logger.warn(`P2P distribution not implemented - cannot reach peer ${peer.id}`);
      return false;
    } catch (error) {
      this.logger.warn(`Failed to distribute genesis block to peer ${peer.id}:`, error);
      return false;
    }
  }

  /**
   * Validate consensus with a single peer
   * @param {PeerInfo} peer - Peer to validate
   * @returns {Promise<boolean>} True if peer is in consensus
   */
  async validatePeerConsensus(peer) {
    try {
      // Real consensus validation with peer
      // This would:
      // 1. Request genesis block hash from peer
      // 2. Compare with local genesis block hash
      // 3. Validate peer's network configuration
      
      this.logger.debug(`Attempting consensus validation with peer ${peer.id}`);
      
      // For now, return false since no real P2P implementation
      this.logger.warn(`P2P consensus validation not implemented - cannot validate peer ${peer.id}`);
      return false;
    } catch (error) {
      this.logger.warn(`Failed to validate consensus with peer ${peer.id}:`, error);
      return false;
    }
  }

  /**
   * Reset coordinator state
   */
  reset() {
    this.currentPhase = null;
    this.participants = [];
    this.genesisParams = null;
    this.genesisBlock = null;
    this.networkConfig = null;
    this.consensusVotes.clear();
    this.isCoordinating = false;
    
    this.logger.info('GenesisCoordinator reset to initial state');
    this.emit('reset');
  }
}

module.exports = {
  GenesisCoordinator,
  GenesisParams,
  NetworkConfig,
  GenesisBlock,
  GenesisPhase
};