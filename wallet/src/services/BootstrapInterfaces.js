/**
 * TypeScript-style interfaces for Auto-Bootstrap P2P Network system
 * Implemented as JSDoc type definitions for JavaScript compatibility
 */

/**
 * @typedef {Object} PeerInfo
 * @property {string} id - Unique peer identifier
 * @property {string} address - IP address of the peer
 * @property {number} port - Port number for peer communication
 * @property {string} walletAddress - Wallet address of the peer
 * @property {string} networkMode - Network mode ('testnet' or 'mainnet')
 * @property {boolean} isReady - Whether peer is ready for network formation
 * @property {Date} lastSeen - Last time peer was seen/contacted
 * @property {string[]} capabilities - List of peer capabilities
 */

/**
 * @typedef {Object} GenesisParams
 * @property {number} timestamp - Genesis block timestamp
 * @property {number} difficulty - Initial mining difficulty
 * @property {string[]} participants - List of participating wallet addresses
 * @property {Map<string, number>} initialRewards - Initial reward distribution
 * @property {string} networkId - Unique network identifier
 * @property {ConsensusRules} consensusRules - Consensus mechanism rules
 */

/**
 * @typedef {Object} BootstrapState
 * @property {string} mode - Current bootstrap mode ('pioneer'|'discovery'|'genesis'|'network')
 * @property {string|null} walletAddress - Created wallet address
 * @property {string|null} selectedModel - Path to selected AI model
 * @property {PeerInfo[]} discoveredPeers - Array of discovered peers
 * @property {Object|null} genesisBlock - Genesis block object
 * @property {NetworkConfig|null} networkConfig - Network configuration
 * @property {BootstrapError|null} lastError - Last error that occurred
 * @property {boolean} isReady - Whether system is ready for next step
 */

/**
 * @typedef {Object} NetworkConfig
 * @property {string} networkId - Unique network identifier
 * @property {string} genesisHash - Hash of the genesis block
 * @property {PeerInfo[]} peers - List of network peers
 * @property {ConsensusRules} consensusRules - Network consensus rules
 * @property {Date} createdAt - Network creation timestamp
 */

/**
 * @typedef {Object} ConsensusRules
 * @property {string} algorithm - Consensus algorithm name
 * @property {number} blockTime - Target block time in seconds
 * @property {number} minValidators - Minimum number of validators
 * @property {number} maxValidators - Maximum number of validators
 * @property {Object} rewards - Reward structure configuration
 */

/**
 * @typedef {Object} BootstrapError
 * @property {string} type - Error type from BootstrapErrorType
 * @property {string} message - User-friendly error message
 * @property {Error} originalError - Original error object
 * @property {string} timestamp - ISO timestamp when error occurred
 * @property {string} state - Bootstrap state when error occurred
 */

/**
 * @typedef {Object} GenesisResult
 * @property {Object} block - The created genesis block
 * @property {NetworkConfig} networkConfig - Network configuration
 * @property {string[]} participants - List of participating addresses
 * @property {boolean} success - Whether genesis creation succeeded
 */

/**
 * @typedef {Object} ScanProgress
 * @property {number} percentage - Completion percentage (0-100)
 * @property {string} currentRange - Current IP range being scanned
 * @property {number} peersFound - Number of peers found so far
 * @property {string} status - Current status message
 */

/**
 * @typedef {Object} DiscoveryStatus
 * @property {string} phase - Current discovery phase
 * @property {PeerInfo[]} peers - Currently discovered peers
 * @property {number} elapsed - Elapsed time in milliseconds
 * @property {string} message - Status message
 */

/**
 * @typedef {Object} GenesisProgress
 * @property {string} phase - Current genesis creation phase
 * @property {number} percentage - Completion percentage (0-100)
 * @property {string} message - Progress message
 * @property {string[]} participants - Participating peer addresses
 */

/**
 * @typedef {Object} Connection
 * @property {string} peerId - Connected peer ID
 * @property {string} address - Peer address
 * @property {number} port - Connection port
 * @property {boolean} isActive - Whether connection is active
 * @property {Date} establishedAt - When connection was established
 */

/**
 * Interface definitions for service classes
 */

/**
 * @interface BootstrapServiceInterface
 * @description Main bootstrap orchestration service
 */
class BootstrapServiceInterface {
  /**
   * Initialize pioneer mode for new installations
   * @returns {Promise<void>}
   */
  async initializePioneerMode() {}
  
  /**
   * Handle wallet address creation
   * @param {string} address - The created wallet address
   */
  onWalletAddressCreated(address) {}
  
  /**
   * Handle mining readiness (model prepared)
   * @param {string} modelPath - Path to prepared AI model
   */
  onMiningReadiness(modelPath) {}
  
  /**
   * Start peer discovery process
   * @returns {Promise<void>}
   */
  async startPeerDiscovery() {}
  
  /**
   * Handle discovered peers
   * @param {PeerInfo[]} peers - Array of discovered peers
   */
  onPeersDiscovered(peers) {}
  
  /**
   * Coordinate genesis block creation
   * @returns {Promise<GenesisResult>}
   */
  async coordinateGenesisCreation() {}
  
  /**
   * Transition to active network mode
   */
  transitionToNetworkMode() {}
  
  /**
   * Check if feature is available during bootstrap
   * @param {string} feature - Feature identifier
   * @returns {boolean}
   */
  isFeatureAvailable(feature) {}
}

/**
 * @interface PeerDiscoveryManagerInterface
 * @description Handles P2P network scanning and peer identification
 */
class PeerDiscoveryManagerInterface {
  /**
   * Detect network mode (testnet vs mainnet)
   * @returns {string} Network mode
   */
  detectNetworkMode() {}
  
  /**
   * Scan for peers in specified network mode
   * @param {string} mode - Network mode
   * @returns {Promise<PeerInfo[]>}
   */
  async scanForPeers(mode) {}
  
  /**
   * Broadcast availability to network
   * @param {string} walletAddress - Local wallet address
   */
  broadcastAvailability(walletAddress) {}
  
  /**
   * Validate peer connection
   * @param {PeerInfo} peer - Peer to validate
   * @returns {Promise<boolean>}
   */
  async validatePeerConnection(peer) {}
  
  /**
   * Establish connection to peer
   * @param {PeerInfo} peer - Peer to connect to
   * @returns {Promise<Connection>}
   */
  async establishConnection(peer) {}
}

/**
 * @interface GenesisCoordinatorInterface
 * @description Manages collaborative genesis block creation
 */
class GenesisCoordinatorInterface {
  /**
   * Negotiate genesis parameters with peers
   * @param {PeerInfo[]} peers - Participating peers
   * @returns {Promise<GenesisParams>}
   */
  async negotiateGenesisParameters(peers) {}
  
  /**
   * Create genesis block with parameters
   * @param {GenesisParams} params - Genesis parameters
   * @returns {Promise<Object>}
   */
  async createGenesisBlock(params) {}
  
  /**
   * Distribute genesis block to peers
   * @param {Object} block - Genesis block
   * @param {PeerInfo[]} peers - Target peers
   * @returns {Promise<void>}
   */
  async distributeGenesisBlock(block, peers) {}
  
  /**
   * Persist network configuration
   * @param {NetworkConfig} config - Network configuration
   */
  persistNetworkConfiguration(config) {}
  
  /**
   * Validate genesis consensus among peers
   * @param {PeerInfo[]} peers - Participating peers
   * @returns {Promise<boolean>}
   */
  async validateGenesisConsensus(peers) {}
}

/**
 * @interface UserFeedbackManagerInterface
 * @description Provides real-time status updates to users
 */
class UserFeedbackManagerInterface {
  /**
   * Show scanning progress
   * @param {ScanProgress} progress - Scan progress information
   */
  showScanningProgress(progress) {}
  
  /**
   * Display peer discovery status
   * @param {DiscoveryStatus} status - Discovery status
   */
  displayPeerDiscoveryStatus(status) {}
  
  /**
   * Show genesis creation progress
   * @param {GenesisProgress} progress - Genesis progress
   */
  showGenesisCreationProgress(progress) {}
  
  /**
   * Display error message
   * @param {BootstrapError} error - Error information
   */
  displayErrorMessage(error) {}
  
  /**
   * Show success message
   * @param {string} message - Success message
   */
  showSuccessMessage(message) {}
}

// Export UserFeedbackManager implementation
const { UserFeedbackManager } = require('./UserFeedbackManager');

module.exports = {
  // Interface classes (for documentation)
  BootstrapServiceInterface,
  PeerDiscoveryManagerInterface,
  GenesisCoordinatorInterface,
  UserFeedbackManagerInterface,
  // Implementation classes
  UserFeedbackManager
};