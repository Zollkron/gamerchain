/**
 * Property-Based Tests for WalletStateProvider State Transitions
 * **Feature: genesis-state-validation, Property 4: State Transition Integrity**
 * **Validates: Requirements 3.3, 3.5**
 */

// Mock fast-check for property-based testing
const fc = {
  assert: async (property, options) => {
    // Run the property multiple times with generated data
    for (let i = 0; i < (options?.numRuns || 100); i++) {
      try {
        const testData = property.generator();
        await property.predicate(...testData);
      } catch (error) {
        throw new Error(`Property failed on run ${i + 1}: ${error.message}`);
      }
    }
  },
  asyncProperty: (gen1, gen2, gen3, predicate) => ({ 
    generator: () => [gen1(), gen2(), gen3()], 
    predicate 
  }),
  string: (opts = {}) => () => {
    const length = opts.minLength || opts.maxLength || 40;
    return 'PG' + Array.from({length: length - 2}, () => Math.random().toString(36)[2] || '0').join('');
  },
  boolean: () => () => Math.random() < 0.5,
  oneof: (...generators) => () => {
    const randomIndex = Math.floor(Math.random() * generators.length);
    return generators[randomIndex]();
  },
  constant: (value) => () => value,
  array: (generator, opts = {}) => () => {
    const length = opts.minLength || opts.maxLength || Math.floor(Math.random() * 5);
    return Array.from({length}, () => generator());
  }
};

const { WalletStateProvider, WalletDisplayState } = require('../WalletStateProvider');
const { NetworkState } = require('../GenesisStateManager');

// Mock services
const mockGenesisStateManager = {
  checkGenesisExists: jest.fn(),
  getCurrentNetworkState: jest.fn(),
  isOperationAllowed: jest.fn(),
  on: jest.fn(),
  emit: jest.fn()
};

const mockBootstrapService = {
  getState: jest.fn(),
  on: jest.fn(),
  emit: jest.fn()
};

const mockWalletService = {
  getWalletBalance: jest.fn(),
  getTransactionHistory: jest.fn()
};

const mockNetworkService = {
  getNetworkStatus: jest.fn(),
  getBalance: jest.fn()
};

describe('WalletStateProvider Property Tests', () => {
  let walletStateProvider;

  beforeEach(() => {
    jest.clearAllMocks();
    walletStateProvider = new WalletStateProvider();
  });

  afterEach(() => {
    if (walletStateProvider) {
      walletStateProvider.cleanup();
    }
  });

  describe('**Genesis State Validation, Property 4: State Transition Integrity**', () => {
    test('should maintain state transition integrity across bootstrap to active network transitions', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 40, maxLength: 40 }), // walletId
          fc.boolean(), // networkAvailable
          fc.oneof(
            fc.constant(NetworkState.BOOTSTRAP_PIONEER),
            fc.constant(NetworkState.BOOTSTRAP_DISCOVERY),
            fc.constant(NetworkState.BOOTSTRAP_GENESIS),
            fc.constant(NetworkState.ACTIVE)
          ), // initialNetworkState
          async (walletId, networkAvailable, initialNetworkState) => {
            // Setup: Initialize WalletStateProvider with mocked services
            walletStateProvider.initialize({
              genesisStateManager: mockGenesisStateManager,
              bootstrapService: mockBootstrapService,
              walletService: mockWalletService,
              networkService: mockNetworkService
            });

            // Setup initial state - before genesis creation
            const initialGenesisState = {
              exists: false,
              blockHash: null,
              createdAt: null,
              isVerified: false
            };

            mockGenesisStateManager.checkGenesisExists.mockResolvedValue(initialGenesisState);
            mockGenesisStateManager.getCurrentNetworkState.mockReturnValue(initialNetworkState);
            mockGenesisStateManager.isOperationAllowed.mockImplementation((operation) => {
              // Only wallet creation allowed before genesis
              return operation === 'wallet_creation';
            });

            // Setup initial wallet service responses - should always be correct (no mock data)
            // The WalletStateProvider should ensure no mock data is ever returned
            mockWalletService.getWalletBalance.mockResolvedValue({
              success: true,
              balance: '0',
              requiresGenesis: true,
              message: 'Blockchain not initialized - genesis block required',
              isMock: false
            });
            
            mockWalletService.getTransactionHistory.mockResolvedValue({
              success: true,
              transactions: [],
              requiresGenesis: true,
              message: 'No transaction history available - blockchain not initialized',
              isMock: false
            });

            // Action 1: Get initial wallet state (before genesis)
            const initialState = await walletStateProvider.getWalletDisplayState(walletId);

            // Assert: Initial state should never contain mock data
            expect(initialState.balance).toBe('0'); // Should always be zero before genesis
            expect(initialState.transactions).toEqual([]); // Should always be empty before genesis
            expect(initialState.canSendTransactions).toBe(false);
            expect(initialState.canRequestFaucet).toBe(false);
            // Status message should indicate the current state appropriately
            expect(initialState.statusMessage.toLowerCase()).toMatch(/(blockchain|pioneer|discovery|genesis|network|pionero|génesis|red|creando|bloque)/); // Should mention network state

            // Action 2: Simulate genesis creation
            const genesisResult = {
              block: {
                hash: 'genesis-hash-' + Math.random().toString(36).substring(7),
                timestamp: Date.now()
              },
              networkConfig: {
                networkId: 'test-network'
              }
            };

            // Update mocks to reflect genesis creation
            const postGenesisState = {
              exists: true,
              blockHash: genesisResult.block.hash,
              createdAt: new Date(genesisResult.block.timestamp),
              isVerified: true
            };

            mockGenesisStateManager.checkGenesisExists.mockResolvedValue(postGenesisState);
            mockGenesisStateManager.getCurrentNetworkState.mockReturnValue(NetworkState.ACTIVE);
            mockGenesisStateManager.isOperationAllowed.mockReturnValue(true);

            // Update wallet service to return real data (no mock flags)
            mockWalletService.getWalletBalance.mockResolvedValue({
              success: true,
              balance: '0', // Real zero balance (no genesis rewards yet)
              requiresGenesis: false,
              isMock: false
            });
            
            mockWalletService.getTransactionHistory.mockResolvedValue({
              success: true,
              transactions: [], // Real empty history
              requiresGenesis: false,
              isMock: false
            });

            // Action 3: Trigger genesis creation event
            walletStateProvider.onGenesisCreated(genesisResult);

            // Action 4: Get wallet state after genesis creation
            const postGenesisWalletState = await walletStateProvider.getWalletDisplayState(walletId);

            // Assert: State transition integrity
            // 1. All cached mock data should be cleared
            expect(postGenesisWalletState.balance).toBe('0'); // Real zero, not mock data
            expect(postGenesisWalletState.transactions).toEqual([]); // Real empty, not mock data
            
            // 2. Operations should now be available
            expect(postGenesisWalletState.canSendTransactions).toBe(true);
            expect(postGenesisWalletState.canRequestFaucet).toBe(true);
            
            // 3. Network state should be active
            expect(postGenesisWalletState.networkState).toBe(NetworkState.ACTIVE);
            
            // 4. Genesis state should be properly set
            expect(postGenesisWalletState.genesisState.exists).toBe(true);
            expect(postGenesisWalletState.genesisState.blockHash).toBe(genesisResult.block.hash);
            
            // 5. Status message should reflect active state
            expect(postGenesisWalletState.statusMessage.toLowerCase()).toContain('activa');
            
            // 6. No error should be present
            expect(postGenesisWalletState.error).toBeNull();
            
            // 7. State should be recently updated
            const timeDiff = Date.now() - postGenesisWalletState.lastUpdated.getTime();
            expect(timeDiff).toBeLessThan(5000); // Updated within last 5 seconds

            // Action 5: Verify cache was cleared during transition
            const cacheStats = walletStateProvider.getCacheStats();
            
            // The cache should contain the fresh state, not the old mock data
            const cachedEntry = cacheStats.entries.find(entry => entry.walletId === walletId);
            if (cachedEntry) {
              // Cache entry should be recent (created after genesis event)
              expect(cachedEntry.age).toBeLessThan(5000);
            }

            // Action 6: Test network state change handling
            const previousNetworkState = postGenesisWalletState.networkState;
            
            // Update mock to return the new network state
            mockGenesisStateManager.getCurrentNetworkState.mockReturnValue(NetworkState.CONNECTING);
            
            walletStateProvider.onNetworkStateChange(NetworkState.CONNECTING, previousNetworkState);
            
            // Get state after network change
            const postNetworkChangeState = await walletStateProvider.getWalletDisplayState(walletId);
            
            // Assert: Network state change should update state appropriately
            expect(postNetworkChangeState.networkState).toBe(NetworkState.CONNECTING);
            expect(postNetworkChangeState.statusMessage.toLowerCase()).toContain('conectando');
            
            // But genesis state should remain (it doesn't disappear)
            expect(postNetworkChangeState.genesisState.exists).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('WalletStateProvider Core Functionality', () => {
    beforeEach(() => {
      walletStateProvider.initialize({
        genesisStateManager: mockGenesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
    });

    test('should initialize with required services', () => {
      expect(walletStateProvider.genesisStateManager).toBe(mockGenesisStateManager);
      expect(walletStateProvider.walletService).toBe(mockWalletService);
      expect(walletStateProvider.networkService).toBe(mockNetworkService);
    });

    test('should throw error when required services are missing', () => {
      const newProvider = new WalletStateProvider();
      
      expect(() => {
        newProvider.initialize({});
      }).toThrow('GenesisStateManager is required');
      
      expect(() => {
        newProvider.initialize({ genesisStateManager: mockGenesisStateManager });
      }).toThrow('WalletService is required');
    });

    test('should generate appropriate status messages', () => {
      const testCases = [
        {
          networkState: NetworkState.BOOTSTRAP_PIONEER,
          genesisExists: false,
          expected: 'modo pionero'
        },
        {
          networkState: NetworkState.BOOTSTRAP_DISCOVERY,
          genesisExists: false,
          expected: 'descubriendo peers'
        },
        {
          networkState: NetworkState.BOOTSTRAP_GENESIS,
          genesisExists: false,
          expected: 'creando bloque génesis'
        },
        {
          networkState: NetworkState.ACTIVE,
          genesisExists: true,
          expected: 'Blockchain activa'
        },
        {
          networkState: NetworkState.DISCONNECTED,
          genesisExists: false,
          expected: 'blockchain no inicializada'
        }
      ];

      testCases.forEach(({ networkState, genesisExists, expected }) => {
        const genesisState = { exists: genesisExists };
        const balanceResult = { success: true, balance: '0' };
        const historyResult = { success: true, transactions: [] };
        
        const message = walletStateProvider.generateStatusMessage(
          networkState, 
          genesisState, 
          balanceResult, 
          historyResult
        );
        
        expect(message.toLowerCase()).toContain(expected.toLowerCase());
      });
    });

    test('should handle error states gracefully', async () => {
      const walletId = 'test-wallet-error';
      
      // Mock services to throw errors
      mockGenesisStateManager.checkGenesisExists.mockRejectedValue(new Error('Genesis check failed'));
      
      const errorState = await walletStateProvider.getWalletDisplayState(walletId);
      
      expect(errorState.balance).toBe('0');
      expect(errorState.transactions).toEqual([]);
      expect(errorState.canSendTransactions).toBe(false);
      expect(errorState.canRequestFaucet).toBe(false);
      expect(errorState.error).toContain('Genesis check failed');
      expect(errorState.statusMessage).toContain('Error');
    });

    test('should cache and retrieve wallet states', async () => {
      const walletId = 'test-wallet-cache';
      
      // Setup successful mocks
      mockGenesisStateManager.checkGenesisExists.mockResolvedValue({
        exists: true,
        blockHash: 'test-hash',
        isVerified: true
      });
      mockGenesisStateManager.getCurrentNetworkState.mockReturnValue(NetworkState.ACTIVE);
      mockGenesisStateManager.isOperationAllowed.mockReturnValue(true);
      mockWalletService.getWalletBalance.mockResolvedValue({
        success: true,
        balance: '100.0'
      });
      mockWalletService.getTransactionHistory.mockResolvedValue({
        success: true,
        transactions: []
      });

      // First call should fetch from services
      const state1 = await walletStateProvider.getWalletDisplayState(walletId);
      expect(mockWalletService.getWalletBalance).toHaveBeenCalledTimes(1);

      // Second call should use cache
      const state2 = await walletStateProvider.getWalletDisplayState(walletId);
      expect(mockWalletService.getWalletBalance).toHaveBeenCalledTimes(1); // Still 1, not 2
      
      expect(state1.balance).toBe(state2.balance);
    });

    test('should clear cache on significant state changes', () => {
      const walletId = 'test-wallet-clear';
      
      // Add something to cache
      const testState = new WalletDisplayState({ balance: '100' });
      walletStateProvider.cacheState(walletId, testState);
      
      expect(walletStateProvider.walletStates.size).toBe(1);
      
      // Trigger significant state change
      walletStateProvider.onNetworkStateChange(NetworkState.ACTIVE, NetworkState.DISCONNECTED);
      
      expect(walletStateProvider.walletStates.size).toBe(0);
    });

    test('should provide cache statistics', () => {
      const walletId1 = 'wallet-1';
      const walletId2 = 'wallet-2';
      
      walletStateProvider.cacheState(walletId1, new WalletDisplayState());
      walletStateProvider.cacheState(walletId2, new WalletDisplayState());
      
      const stats = walletStateProvider.getCacheStats();
      
      expect(stats.totalEntries).toBe(2);
      expect(stats.entries).toHaveLength(2);
      expect(stats.entries[0]).toHaveProperty('walletId');
      expect(stats.entries[0]).toHaveProperty('cachedAt');
      expect(stats.entries[0]).toHaveProperty('accessCount');
    });
  });

  describe('Event Handling', () => {
    beforeEach(() => {
      walletStateProvider.initialize({
        genesisStateManager: mockGenesisStateManager,
        bootstrapService: mockBootstrapService,
        walletService: mockWalletService,
        networkService: mockNetworkService
      });
    });

    test('should emit events on state updates', async () => {
      const walletId = 'test-wallet-events';
      const stateUpdates = [];
      
      walletStateProvider.on('walletStateUpdated', (id, state) => {
        stateUpdates.push({ id, state });
      });

      // Setup mocks
      mockGenesisStateManager.checkGenesisExists.mockResolvedValue({
        exists: true,
        blockHash: 'test-hash',
        isVerified: true
      });
      mockGenesisStateManager.getCurrentNetworkState.mockReturnValue(NetworkState.ACTIVE);
      mockGenesisStateManager.isOperationAllowed.mockReturnValue(true);
      mockWalletService.getWalletBalance.mockResolvedValue({
        success: true,
        balance: '50.0'
      });
      mockWalletService.getTransactionHistory.mockResolvedValue({
        success: true,
        transactions: []
      });

      await walletStateProvider.getWalletDisplayState(walletId);
      
      expect(stateUpdates).toHaveLength(1);
      expect(stateUpdates[0].id).toBe(walletId);
      expect(stateUpdates[0].state.balance).toBe('50.0');
    });

    test('should emit events on genesis creation', () => {
      const genesisEvents = [];
      
      walletStateProvider.on('genesisCreated', (result) => {
        genesisEvents.push(result);
      });

      const genesisResult = {
        block: { hash: 'genesis-123', timestamp: Date.now() }
      };
      
      walletStateProvider.onGenesisCreated(genesisResult);
      
      expect(genesisEvents).toHaveLength(1);
      expect(genesisEvents[0]).toBe(genesisResult);
    });

    test('should emit events on network state changes', () => {
      const networkEvents = [];
      
      walletStateProvider.on('networkStateChanged', (newState, previousState) => {
        networkEvents.push({ newState, previousState });
      });

      walletStateProvider.onNetworkStateChange(NetworkState.ACTIVE, NetworkState.CONNECTING);
      
      expect(networkEvents).toHaveLength(1);
      expect(networkEvents[0].newState).toBe(NetworkState.ACTIVE);
      expect(networkEvents[0].previousState).toBe(NetworkState.CONNECTING);
    });
  });
});