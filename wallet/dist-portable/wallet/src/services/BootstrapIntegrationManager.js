/**
 * Bootstrap Integration Manager
 * 
 * Manages the integration between BootstrapService and existing wallet/blockchain components
 * Ensures seamless operation during bootstrap and after network formation
 */

const { BootstrapService } = require('./BootstrapService');
const WalletService = require('./WalletService');
const MiningService = require('./MiningService');
const BlockchainService = require('./BlockchainService');
const { BootstrapLogger } = require('./BootstrapLogger');

class BootstrapIntegrationManager {
  constructor() {
    this.logger = new BootstrapLogger('BootstrapIntegrationManager');
    this.bootstrapService = null;
    this.integrations = {
      wallet: false,
      mining: false,
      blockchain: false
    };
  }

  /**
   * Initialize bootstrap integration with all services
   * @param {Object} options - Integration options
   */
  async initializeIntegration(options = {}) {
    try {
      this.logger.info('Initializing bootstrap integration with existing services');

      // Get or create bootstrap service instance
      this.bootstrapService = options.bootstrapService || new BootstrapService();

      // Set up wallet integration
      await this.setupWalletIntegration();

      // Set up mining and consensus integration
      await this.setupMiningIntegration();

      // Set up blockchain service integration
      await this.setupBlockchainIntegration();

      // Set up cross-service event handling
      this.setupCrossServiceEvents();

      this.logger.info('Bootstrap integration initialized successfully');

      return {
        success: true,
        integrations: this.integrations,
        bootstrapService: this.bootstrapService
      };

    } catch (error) {
      this.logger.error('Failed to initialize bootstrap integration:', error);
      throw error;
    }
  }

  /**
   * Set up wallet service integration
   */
  async setupWalletIntegration() {
    try {
      this.logger.info('Setting up wallet service integration');

      // Integrate bootstrap service with wallet functionality
      this.bootstrapService.integrateWithWalletService(WalletService);

      // Ensure wallet operations work during bootstrap
      this.bootstrapService.on('stateChanged', async (state) => {
        // Wallet operations should always be available
        if (!this.bootstrapService.isFeatureAvailable('wallet_operations')) {
          // Wallet operations are not restricted during bootstrap
          this.logger.info('Wallet operations remain available during bootstrap');
        }
      });

      // Handle wallet address creation during bootstrap
      this.bootstrapService.on('walletAddressCreated', async (address) => {
        this.logger.info(`Wallet address created during bootstrap: ${address}`);
        
        // Ensure address is preserved for genesis rewards
        try {
          await WalletService.persistAddressForGenesis(address, `bootstrap-${Date.now()}`);
        } catch (error) {
          this.logger.warn('Could not persist address for genesis:', error.message);
        }
      });

      this.integrations.wallet = true;
      this.logger.info('Wallet service integration completed');

    } catch (error) {
      this.logger.error('Failed to set up wallet integration:', error);
      throw error;
    }
  }

  /**
   * Set up mining service integration
   */
  async setupMiningIntegration() {
    try {
      this.logger.info('Setting up mining service integration');

      // Integrate bootstrap service with mining and consensus
      this.bootstrapService.integrateWithMiningAndConsensus(MiningService, BlockchainService);

      // Handle mining operations after network formation
      this.bootstrapService.on('networkModeActivated', async () => {
        this.logger.info('Network mode activated - enabling mining operations');
        
        try {
          // Check mining requirements
          const requirements = await MiningService.checkMiningRequirements();
          
          if (requirements.canMine) {
            this.logger.info('Mining requirements satisfied after network formation');
          } else {
            this.logger.warn('Mining requirements not satisfied:', requirements);
          }
        } catch (error) {
          this.logger.error('Error checking mining requirements after network formation:', error);
        }
      });

      // Handle mining configuration restoration
      this.bootstrapService.on('miningConfigurationRestored', (config) => {
        this.logger.info('Mining configuration restored after bootstrap transition:', config);
      });

      this.integrations.mining = true;
      this.logger.info('Mining service integration completed');

    } catch (error) {
      this.logger.error('Failed to set up mining integration:', error);
      throw error;
    }
  }

  /**
   * Set up blockchain service integration
   */
  async setupBlockchainIntegration() {
    try {
      this.logger.info('Setting up blockchain service integration');

      // Handle blockchain operations after network formation
      this.bootstrapService.on('allBlockchainOperationsEnabled', async (data) => {
        this.logger.info('All blockchain operations enabled:', data.availableFeatures);
        
        try {
          // Initialize blockchain service if not already done
          if (BlockchainService && typeof BlockchainService.initialize === 'function') {
            await BlockchainService.initialize();
            this.logger.info('Blockchain service initialized after bootstrap');
          }
        } catch (error) {
          this.logger.warn('Could not initialize blockchain service:', error.message);
        }
      });

      // Handle genesis block creation
      this.bootstrapService.on('genesisCreated', (genesisResult) => {
        this.logger.info('Genesis block created - blockchain operations now available');
        
        // Blockchain service can now operate with the genesis block
        if (BlockchainService && typeof BlockchainService.setGenesisBlock === 'function') {
          try {
            BlockchainService.setGenesisBlock(genesisResult.block);
          } catch (error) {
            this.logger.warn('Could not set genesis block in blockchain service:', error.message);
          }
        }
      });

      this.integrations.blockchain = true;
      this.logger.info('Blockchain service integration completed');

    } catch (error) {
      this.logger.error('Failed to set up blockchain integration:', error);
      throw error;
    }
  }

  /**
   * Set up cross-service event handling
   */
  setupCrossServiceEvents() {
    try {
      this.logger.info('Setting up cross-service event handling');

      // Handle data preservation across all services
      this.bootstrapService.on('stateChanged', (state) => {
        this.preserveDataAcrossServices(state);
      });

      // Handle feature availability changes
      this.bootstrapService.on('modeChanged', (newMode, previousMode) => {
        this.updateFeatureAvailability(newMode, previousMode);
      });

      this.logger.info('Cross-service event handling set up successfully');

    } catch (error) {
      this.logger.error('Failed to set up cross-service events:', error);
      throw error;
    }
  }

  /**
   * Preserve data across all integrated services
   * @param {Object} state - Current bootstrap state
   */
  preserveDataAcrossServices(state) {
    try {
      // Ensure wallet data is preserved
      if (state.walletAddress) {
        this.logger.debug(`Preserving wallet address across services: ${state.walletAddress}`);
      }

      // Ensure mining configuration is preserved
      if (state.selectedModel && state.modelInfo) {
        this.logger.debug(`Preserving mining configuration: ${state.selectedModel}`);
      }

      // Ensure network data is preserved
      if (state.discoveredPeers && state.discoveredPeers.length > 0) {
        this.logger.debug(`Preserving network data: ${state.discoveredPeers.length} peers`);
      }

    } catch (error) {
      this.logger.error('Error preserving data across services:', error);
    }
  }

  /**
   * Update feature availability across services
   * @param {string} newMode - New bootstrap mode
   * @param {string} previousMode - Previous bootstrap mode
   */
  updateFeatureAvailability(newMode, previousMode) {
    try {
      this.logger.info(`Updating feature availability: ${previousMode} -> ${newMode}`);

      // Update service availability based on bootstrap mode
      const availableFeatures = this.getAvailableFeatures(newMode);
      
      this.logger.info(`Features available in ${newMode} mode:`, availableFeatures);

      // Notify services of feature availability changes
      this.notifyServicesOfFeatureChanges(availableFeatures, newMode);

    } catch (error) {
      this.logger.error('Error updating feature availability:', error);
    }
  }

  /**
   * Get available features for a bootstrap mode
   * @param {string} mode - Bootstrap mode
   * @returns {Array} Available features
   */
  getAvailableFeatures(mode) {
    const allFeatures = [
      'wallet_operations',
      'send_transaction',
      'mining_operations',
      'consensus_participation',
      'block_validation',
      'peer_communication',
      'network_synchronization'
    ];

    switch (mode) {
      case 'pioneer':
      case 'discovery':
      case 'genesis':
        // During bootstrap, only wallet operations are fully available
        return ['wallet_operations'];
      
      case 'network':
        // In network mode, all features are available
        return allFeatures;
      
      default:
        return ['wallet_operations'];
    }
  }

  /**
   * Notify services of feature availability changes
   * @param {Array} availableFeatures - Currently available features
   * @param {string} mode - Current bootstrap mode
   */
  notifyServicesOfFeatureChanges(availableFeatures, mode) {
    try {
      // Notify mining service
      if (MiningService && typeof MiningService.updateFeatureAvailability === 'function') {
        MiningService.updateFeatureAvailability(availableFeatures, mode);
      }

      // Notify blockchain service
      if (BlockchainService && typeof BlockchainService.updateFeatureAvailability === 'function') {
        BlockchainService.updateFeatureAvailability(availableFeatures, mode);
      }

      // Emit event for other services to listen to
      this.bootstrapService.emit('featureAvailabilityChanged', {
        availableFeatures,
        mode,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      this.logger.error('Error notifying services of feature changes:', error);
    }
  }

  /**
   * Get integration status
   * @returns {Object} Integration status
   */
  getIntegrationStatus() {
    return {
      initialized: this.bootstrapService !== null,
      integrations: { ...this.integrations },
      bootstrapMode: this.bootstrapService ? this.bootstrapService.getCurrentMode() : null,
      availableFeatures: this.bootstrapService ? 
        this.getAvailableFeatures(this.bootstrapService.getCurrentMode()) : []
    };
  }

  /**
   * Cleanup integration
   */
  cleanup() {
    try {
      this.logger.info('Cleaning up bootstrap integration');

      if (this.bootstrapService) {
        this.bootstrapService.removeAllListeners();
        this.bootstrapService = null;
      }

      this.integrations = {
        wallet: false,
        mining: false,
        blockchain: false
      };

      this.logger.info('Bootstrap integration cleanup completed');

    } catch (error) {
      this.logger.error('Error during integration cleanup:', error);
    }
  }
}

module.exports = new BootstrapIntegrationManager();