/**
 * Service Integration Manager
 * 
 * Manages the initialization and integration of all wallet services,
 * ensuring proper dependency injection and service coordination.
 */

const { BootstrapService } = require('./BootstrapService');
const NetworkService = require('./NetworkService');
const { GenesisStateManager } = require('./GenesisStateManager');
const { WalletStateProvider } = require('./WalletStateProvider');
const WalletService = require('./WalletService');
const MiningService = require('./MiningService');

class ServiceIntegrationManager {
  constructor() {
    this.services = {};
    this.initialized = false;
    
    console.log('ServiceIntegrationManager initialized');
  }
  
  /**
   * Initialize all services with proper dependency injection
   * @returns {Promise<Object>} Initialized services
   */
  async initializeServices() {
    if (this.initialized) {
      return this.services;
    }
    
    try {
      console.log('🔧 Initializing wallet services with dependency injection...');
      
      // Step 1: Initialize core network services first
      this.services.networkService = NetworkService; // NetworkService is a singleton
      const coordinatorClient = this.services.networkService.getCoordinatorClient();
      
      // Step 2: Initialize Genesis State Manager
      this.services.genesisStateManager = new GenesisStateManager();
      
      // Step 3: Initialize Bootstrap Service with coordinator client
      this.services.bootstrapService = new BootstrapService(coordinatorClient);
      
      // Step 4: Initialize Wallet State Provider
      this.services.walletStateProvider = new WalletStateProvider(
        this.services.genesisStateManager,
        this.services.networkService
      );
      
      // Step 5: Initialize other services
      this.services.walletService = WalletService;
      this.services.miningService = MiningService;
      
      // Step 6: Set up service integrations
      await this.setupServiceIntegrations();
      
      // Step 7: Auto-initialize pioneer mode if in bootstrap mode
      await this.autoInitializePioneerMode();
      
      this.initialized = true;
      console.log('✅ All wallet services initialized successfully');
      
      return this.services;
      
    } catch (error) {
      console.error('❌ Failed to initialize wallet services:', error);
      throw error;
    }
  }
  
  /**
   * Set up integrations between services
   */
  async setupServiceIntegrations() {
    try {
      // Integrate Bootstrap Service with Wallet Service
      if (this.services.bootstrapService && this.services.walletService) {
        this.services.bootstrapService.integrateWithWalletService(this.services.walletService);
      }
      
      // Integrate Bootstrap Service with Mining Service
      if (this.services.bootstrapService && this.services.miningService) {
        this.services.bootstrapService.integrateWithMiningAndConsensus(
          this.services.miningService,
          null // BlockchainService not yet available
        );
      }
      
      // Genesis State Manager is already initialized with required dependencies
      
      console.log('🔗 Service integrations completed');
      
    } catch (error) {
      console.error('❌ Failed to set up service integrations:', error);
      throw error;
    }
  }
  
  /**
   * Get a specific service
   * @param {string} serviceName - Name of the service
   * @returns {Object|null} Service instance or null
   */
  getService(serviceName) {
    return this.services[serviceName] || null;
  }
  
  /**
   * Get all services
   * @returns {Object} All initialized services
   */
  getAllServices() {
    return { ...this.services };
  }
  
  /**
   * Check if services are initialized
   * @returns {boolean} True if initialized
   */
  isInitialized() {
    return this.initialized;
  }
  
  /**
   * Get bootstrap service specifically (commonly used)
   * @returns {BootstrapService|null} Bootstrap service
   */
  getBootstrapService() {
    return this.services.bootstrapService || null;
  }
  
  /**
   * Get network coordinator client
   * @returns {NetworkCoordinatorClient|null} Coordinator client
   */
  getNetworkCoordinatorClient() {
    return this.services.networkService ? 
      this.services.networkService.getCoordinatorClient() : null;
  }
  
  /**
   * Get guided bootstrap manager
   * @returns {GuidedBootstrapManager|null} Guided bootstrap manager
   */
  getGuidedBootstrapManager() {
    const bootstrapService = this.getBootstrapService();
    return bootstrapService ? bootstrapService.guidedBootstrapManager : null;
  }
  
  /**
   * Get bootstrap statistics from all relevant services
   * @returns {Object} Comprehensive bootstrap statistics
   */
  getBootstrapStats() {
    const stats = {
      servicesInitialized: this.initialized,
      availableServices: Object.keys(this.services),
      timestamp: new Date().toISOString()
    };
    
    // Add bootstrap service stats
    const bootstrapService = this.getBootstrapService();
    if (bootstrapService) {
      stats.bootstrap = bootstrapService.getBootstrapStats();
    }
    
    // Add network coordinator stats
    const coordinatorClient = this.getNetworkCoordinatorClient();
    if (coordinatorClient) {
      stats.networkCoordinator = {
        nodeId: coordinatorClient.nodeId,
        coordinatorUrl: coordinatorClient.coordinatorUrl,
        lastMapUpdate: coordinatorClient.lastMapUpdate,
        networkMap: coordinatorClient.networkMap
      };
    }
    
    return stats;
  }
  
  /**
   * Auto-initialize pioneer mode if conditions are met
   */
  async autoInitializePioneerMode() {
    try {
      if (!this.services.bootstrapService) {
        return;
      }
      
      // Check if we should auto-initialize pioneer mode
      const shouldInitialize = await this.shouldAutoInitializePioneerMode();
      
      if (shouldInitialize) {
        console.log('🚀 Auto-initializing pioneer mode for bootstrap...');
        await this.services.bootstrapService.initializePioneerMode();
        console.log('✅ Pioneer mode auto-initialization completed');
      }
      
    } catch (error) {
      console.error('❌ Error during pioneer mode auto-initialization:', error);
    }
  }
  
  /**
   * Check if we should auto-initialize pioneer mode
   */
  async shouldAutoInitializePioneerMode() {
    try {
      // Check if network validator indicates pioneer mode
      if (this.services.networkService && this.services.networkService.networkValidator) {
        const networkMap = this.services.networkService.networkValidator.getCanonicalNetworkMap();
        if (networkMap) {
          const isPioneer = this.services.networkService.networkValidator.isPioneerNode(networkMap);
          if (isPioneer) {
            console.log('🔍 Network validator indicates pioneer mode - auto-initializing');
            return true;
          }
        }
      }
      
      // Check environment variables
      const isPioneerMode = process.env.PLAYERGOLD_BOOTSTRAP_MODE === 'auto' || process.argv.includes('--pioneer-mode');
      if (isPioneerMode) {
        console.log('🔍 Environment indicates pioneer mode - auto-initializing');
        return true;
      }
      
      // Check if no genesis block exists (bootstrap condition)
      // This would indicate we need to bootstrap the network
      return false;
      
    } catch (error) {
      console.error('Error checking pioneer mode conditions:', error);
      return false;
    }
  }
  
  /**
   * Cleanup all services
   */
  async cleanup() {
    try {
      console.log('🧹 Cleaning up wallet services...');
      
      // Cleanup services in reverse order
      if (this.services.bootstrapService) {
        this.services.bootstrapService.reset();
      }
      
      if (this.services.networkService && this.services.networkService.coordinatorClient) {
        this.services.networkService.coordinatorClient.shutdown();
      }
      
      this.services = {};
      this.initialized = false;
      
      console.log('✅ Service cleanup completed');
      
    } catch (error) {
      console.error('❌ Error during service cleanup:', error);
    }
  }
}

// Create singleton instance
const serviceIntegrationManager = new ServiceIntegrationManager();

module.exports = serviceIntegrationManager;