/**
 * Tests for Bootstrap Integration
 * Tests the integration between GenesisStateManager, BootstrapService, and WalletStateProvider
 */

const { GenesisStateManager, GenesisState, NetworkState } = require('../GenesisStateManager');
const { WalletStateProvider, WalletDisplayState } = require('../WalletStateProvider');

// Mock BootstrapService
const mockBootstrapService = {
  getState: jest.fn(),
  getCurrentMode: jest.fn(),
  on: jest.fn(),
  emit: jest.fn(),
  removeListener: jest.fn(),
  removeAllListeners: jest.fn()
};

// Mock NetworkService
const mockNetworkService = {
  getNetworkStatus: jest.fn(),
  getBalance: jest.fn()
};

// Mock WalletService
const mockWalletService = {
  getWalletBalance: jest.fn(),
  getTransactionHistory: jest.fn()
};

describe('Bootstrap Integration Tests', () => {
  let genesisStateManager;
  let walletStateProvider;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset mock implementations
    mockBootstrapService.getState.mockReturnValue({
      mode: 'pioneer',
      walletAddress: null,
      selectedModel: null,
      discoveredPeers: [],
      genesisBlock: null,
      networkConfig: null,
      lastError: null,
      isReady: false
    });
    
    mockBootstrapService.getCurrentMode.mockReturnValue('pioneer');
    
    mockNetworkService.getNetworkStatus.mockResolvedValue({
      success: false,
      error: 'Network not available'
    });
    
    mockNetworkService.getBalance.mockResolvedValue({
      success: false,
      error: 'Balance not available',
      requiresGenesis: true
    });
    
    mockWalletService.getWalletBalance.mockResolvedValue({
      success: false,
      balance: '0',
      error: 'Genesis block required',
      requiresGenesis: true
    });
    
    mockWalletService.getTransactionHistory.mockResolvedValue({
      success: false,
      transactions: [],
      error: 'Genesis block required',
      requiresGenesis: true
    });

    // Create fresh instances
    genesisStateManager = new GenesisStateManager();
    walletStateProvider = new WalletStateProvider();
  });

  afterEach(() => {
    if (genesisStateManager) {
      genesisStateManager.cleanup();
    }
    if (walletStateProvider) {
      walletStateProvider.cleanup();
    }
  });

  describe('GenesisStateManager Bootstrap Integration', () => {
    test('should initialize with bootstrap service', () => {
      // Initialize with bootstrap service
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      
      expect(genesisStateManager.bootstrapService).toBe(mockBootstrapService);
      expect(mockBootstrapService.on).toHaveBeenCalledWith('stateChanged', expect.any(Function));
      expect(mockBootstrapService.on).toHaveBeenCalledWith('genesisCreated', expect.any(Function));
      expect(mockBootstrapService.on).toHaveBeenCalledWith('networkModeActivated', expect.any(Function));
    });

    test('should update network state based on bootstrap mode transitions', () => {
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      
      // Get the stateChanged listener
      const stateChangedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'stateChanged')[1];
      
      // Test pioneer mode
      stateChangedListener({ mode: 'pioneer' });
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.BOOTSTRAP_PIONEER);
      
      // Test discovery mode
      stateChangedListener({ mode: 'discovery' });
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.BOOTSTRAP_DISCOVERY);
      
      // Test genesis mode
      stateChangedListener({ mode: 'genesis' });
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.BOOTSTRAP_GENESIS);
      
      // Test network mode
      stateChangedListener({ mode: 'network' });
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.ACTIVE);
    });

    test('should clear cached data during bootstrap transitions', () => {
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      
      const clearDataSpy = jest.spyOn(genesisStateManager, 'clearCachedData');
      const stateChangedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'stateChanged')[1];
      
      // Transition to discovery mode should clear cached data
      stateChangedListener({ mode: 'discovery' });
      expect(clearDataSpy).toHaveBeenCalled();
    });

    test('should update genesis state when genesis is created', () => {
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      
      const genesisCreatedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'genesisCreated')[1];
      
      const mockGenesisResult = {
        block: {
          hash: 'test-genesis-hash',
          timestamp: new Date().toISOString()
        }
      };
      
      genesisCreatedListener(mockGenesisResult);
      
      expect(genesisStateManager.genesisState.exists).toBe(true);
      expect(genesisStateManager.genesisState.blockHash).toBe('test-genesis-hash');
      expect(genesisStateManager.genesisState.isVerified).toBe(true);
    });

    test('should handle network mode activation', () => {
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      
      const networkModeListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'networkModeActivated')[1];
      
      networkModeListener();
      
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.ACTIVE);
    });

    test('should synchronize with bootstrap service', async () => {
      mockBootstrapService.getState.mockReturnValue({
        mode: 'genesis',
        genesisBlock: {
          hash: 'sync-test-hash',
          timestamp: new Date().toISOString()
        }
      });
      
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      
      await genesisStateManager.synchronizeWithBootstrap();
      
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.BOOTSTRAP_GENESIS);
      expect(genesisStateManager.genesisState.exists).toBe(true);
      expect(genesisStateManager.genesisState.blockHash).toBe('sync-test-hash');
    });
  });

  describe('WalletStateProvider Bootstrap Integration', () => {
    test('should initialize with bootstrap service', () => {
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      expect(walletStateProvider.bootstrapService).toBe(mockBootstrapService);
      expect(mockBootstrapService.on).toHaveBeenCalledWith('genesisCreated', expect.any(Function));
      expect(mockBootstrapService.on).toHaveBeenCalledWith('networkModeActivated', expect.any(Function));
      expect(mockBootstrapService.on).toHaveBeenCalledWith('stateChanged', expect.any(Function));
    });

    test('should handle bootstrap state changes', () => {
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      const stateChangedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'stateChanged')[1];
      
      const clearCacheSpy = jest.spyOn(walletStateProvider, 'clearCache');
      
      // Bootstrap state change should clear cache
      stateChangedListener({ mode: 'discovery' });
      expect(clearCacheSpy).toHaveBeenCalled();
    });

    test('should handle genesis creation', () => {
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      const genesisCreatedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'genesisCreated')[1];
      
      const onGenesisCreatedSpy = jest.spyOn(walletStateProvider, 'onGenesisCreated');
      
      genesisCreatedListener({ genesisState: { exists: true } });
      
      expect(onGenesisCreatedSpy).toHaveBeenCalledWith({ genesisState: { exists: true } });
    });

    test('should handle network mode activation', () => {
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      const networkModeListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'networkModeActivated')[1];
      
      const onNetworkStateChangeSpy = jest.spyOn(walletStateProvider, 'onNetworkStateChange');
      
      networkModeListener();
      
      expect(onNetworkStateChangeSpy).toHaveBeenCalledWith(
        NetworkState.ACTIVE, 
        expect.any(String)
      );
    });

    test('should map bootstrap modes to network states correctly', () => {
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      expect(walletStateProvider.mapBootstrapToNetworkState('pioneer')).toBe(NetworkState.BOOTSTRAP_PIONEER);
      expect(walletStateProvider.mapBootstrapToNetworkState('discovery')).toBe(NetworkState.BOOTSTRAP_DISCOVERY);
      expect(walletStateProvider.mapBootstrapToNetworkState('genesis')).toBe(NetworkState.BOOTSTRAP_GENESIS);
      expect(walletStateProvider.mapBootstrapToNetworkState('network')).toBe(NetworkState.ACTIVE);
      expect(walletStateProvider.mapBootstrapToNetworkState('unknown')).toBe(NetworkState.DISCONNECTED);
    });

    test('should synchronize with bootstrap service', async () => {
      mockBootstrapService.getState.mockReturnValue({
        mode: 'discovery'
      });
      
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      const handleBootstrapStateChangeSpy = jest.spyOn(walletStateProvider, 'handleBootstrapStateChange');
      
      await walletStateProvider.synchronizeWithBootstrap();
      
      expect(handleBootstrapStateChangeSpy).toHaveBeenCalledWith({ mode: 'discovery' });
    });
  });

  describe('End-to-End Bootstrap Integration', () => {
    test('should handle complete bootstrap flow from pioneer to network', async () => {
      // Initialize both services
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      // Get listeners
      const genesisStateChangedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'stateChanged' && call[1].toString().includes('GenesisStateManager'))?.[1] ||
        mockBootstrapService.on.mock.calls.find(call => call[0] === 'stateChanged')[1];
      
      const walletStateChangedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'stateChanged' && call[1].toString().includes('WalletStateProvider'))?.[1] ||
        mockBootstrapService.on.mock.calls.find(call => call[0] === 'stateChanged')[1];
      
      // Test pioneer mode
      genesisStateChangedListener({ mode: 'pioneer' });
      walletStateChangedListener({ mode: 'pioneer' });
      
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.BOOTSTRAP_PIONEER);
      
      // Test discovery mode
      genesisStateChangedListener({ mode: 'discovery' });
      walletStateChangedListener({ mode: 'discovery' });
      
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.BOOTSTRAP_DISCOVERY);
      
      // Test genesis mode
      genesisStateChangedListener({ mode: 'genesis' });
      walletStateChangedListener({ mode: 'genesis' });
      
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.BOOTSTRAP_GENESIS);
      
      // Test network mode activation
      const genesisResult = {
        block: {
          hash: 'final-genesis-hash',
          timestamp: new Date().toISOString()
        }
      };
      
      // Trigger genesis creation
      const genesisCreatedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'genesisCreated')[1];
      genesisCreatedListener(genesisResult);
      
      // Trigger network mode activation
      const networkModeListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'networkModeActivated')[1];
      networkModeListener();
      
      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.ACTIVE);
      expect(genesisStateManager.genesisState.exists).toBe(true);
      expect(genesisStateManager.genesisState.blockHash).toBe('final-genesis-hash');
    });

    test('should handle data clearing during transitions', () => {
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      const genesisClearSpy = jest.spyOn(genesisStateManager, 'clearCachedData');
      
      // Get the genesis state manager's stateChanged listener
      const genesisStateChangedListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'stateChanged' && call[1].toString().includes('clearCachedData'))?.[1] ||
        mockBootstrapService.on.mock.calls.find(call => call[0] === 'stateChanged')[1];
      
      // Transition should clear cached data
      genesisStateChangedListener({ mode: 'discovery' });
      
      expect(genesisClearSpy).toHaveBeenCalled();
    });

    test('should handle bootstrap errors gracefully', () => {
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      // Simulate bootstrap error
      const errorListener = mockBootstrapService.on.mock.calls
        .find(call => call[0] === 'error')?.[1];
      
      if (errorListener) {
        const mockError = {
          type: 'network_timeout',
          message: 'Network timeout during peer discovery',
          timestamp: new Date().toISOString()
        };
        
        // Should not throw
        expect(() => errorListener(mockError)).not.toThrow();
      }
    });
  });

  describe('Bootstrap Integration Status', () => {
    test('should provide integration status from GenesisStateManager', () => {
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
      
      const status = genesisStateManager.getBootstrapIntegrationStatus();
      
      expect(status).toEqual({
        hasBootstrapService: true,
        bootstrapMode: 'pioneer',
        networkState: expect.any(String),
        genesisExists: false,
        lastStateCheck: null,
        isIntegrated: true
      });
    });

    test('should provide integration status from WalletStateProvider', () => {
      walletStateProvider.initialize({
        genesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
      
      const status = walletStateProvider.getBootstrapIntegrationStatus();
      
      expect(status).toEqual({
        hasBootstrapService: true,
        bootstrapMode: 'pioneer',
        isBootstrapping: true,
        cachedWallets: 0,
        autoRefreshEnabled: expect.any(Boolean)
      });
    });
  });
});