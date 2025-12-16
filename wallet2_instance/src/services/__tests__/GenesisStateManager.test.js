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
  asyncProperty: (gen1, gen2, gen3, gen4, predicate) => ({ 
    generator: () => [gen1(), gen2(), gen3(), gen4()], 
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
  constant: (value) => () => value
};

const { GenesisStateManager, GenesisState, NetworkState } = require('../GenesisStateManager');

// Mock NetworkService
const mockNetworkService = {
  getNetworkStatus: jest.fn(),
  getBalance: jest.fn()
};

// Mock BootstrapService
const mockBootstrapService = {
  getState: jest.fn(),
  isCoordinating: false,
  on: jest.fn(),
  emit: jest.fn()
};

describe('GenesisStateManager', () => {
  let genesisStateManager;

  beforeEach(() => {
    jest.clearAllMocks();
    genesisStateManager = new GenesisStateManager();
  });

  afterEach(() => {
    if (genesisStateManager) {
      genesisStateManager.cleanup();
    }
  });

  describe('**Genesis State Validation, Property 2: Genesis State Consistency**', () => {
    test('should maintain consistency between genesis existence and wallet operations', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.boolean(), // genesisExists
          fc.boolean(), // networkAvailable
          fc.string({ minLength: 40, maxLength: 40 }), // walletAddress
          fc.oneof(
            fc.constant('getBalance'),
            fc.constant('getTransactionHistory'),
            fc.constant('sendTransaction'),
            fc.constant('requestFaucetTokens')
          ), // operation
          async (genesisExists, networkAvailable, walletAddress, operation) => {
            // Setup: Initialize GenesisStateManager with mocked services
            // Reset mocks for each iteration
            jest.clearAllMocks();
            
            // Setup bootstrap service mock
            if (genesisExists) {
              mockBootstrapService.getState.mockReturnValue({
                mode: 'network',
                genesisBlock: {
                  hash: 'genesis_hash_123',
                  timestamp: Date.now()
                }
              });
            } else {
              mockBootstrapService.getState.mockReturnValue({
                mode: 'pioneer',
                genesisBlock: null
              });
            }
            
            genesisStateManager.initialize(mockNetworkService, mockBootstrapService);

            // Mock network service responses based on genesis existence
            if (genesisExists) {
              // Genesis exists - network operations should succeed
              mockNetworkService.getNetworkStatus.mockResolvedValue({
                success: true,
                status: {
                  blockchain_height: 1,
                  genesis_hash: 'genesis_hash_123',
                  genesis_timestamp: Date.now()
                }
              });
              
              mockNetworkService.getBalance.mockResolvedValue({
                success: true,
                balance: '0',
                requiresGenesis: false
              });
              
              mockBootstrapService.getState.mockReturnValue({
                mode: 'network',
                genesisBlock: {
                  hash: 'genesis_hash_123',
                  timestamp: Date.now()
                }
              });
            } else {
              // No genesis - network operations should fail with requiresGenesis
              mockNetworkService.getNetworkStatus.mockResolvedValue({
                success: false,
                error: 'No genesis block found',
                requiresGenesis: true
              });
              
              mockNetworkService.getBalance.mockResolvedValue({
                success: false,
                balance: '0',
                error: 'Genesis block required',
                requiresGenesis: true
              });
              
              mockBootstrapService.getState.mockReturnValue({
                mode: 'pioneer',
                genesisBlock: null
              });
            }

            // Action: Check genesis state
            const genesisState = await genesisStateManager.checkGenesisExists();

            // Assert: Genesis state consistency
            expect(genesisState.exists).toBe(genesisExists);

            // If no genesis exists, balance should be zero and transactions empty
            if (!genesisExists) {
              // Check that operations are properly restricted
              expect(genesisStateManager.isOperationAllowed('send_transaction')).toBe(false);
              expect(genesisStateManager.isOperationAllowed('faucet')).toBe(false);
              expect(genesisStateManager.isOperationAllowed('balance_query')).toBe(false);
              expect(genesisStateManager.isOperationAllowed('transaction_history')).toBe(false);
              
              // Wallet creation should still be allowed
              expect(genesisStateManager.isOperationAllowed('wallet_creation')).toBe(true);
              
              // Network state should not be ACTIVE
              const networkState = genesisStateManager.getCurrentNetworkState();
              expect(networkState).not.toBe(NetworkState.ACTIVE);
            } else {
              // Genesis exists - blockchain operations should be allowed
              expect(genesisStateManager.isOperationAllowed('send_transaction')).toBe(true);
              expect(genesisStateManager.isOperationAllowed('faucet')).toBe(true);
              expect(genesisStateManager.isOperationAllowed('balance_query')).toBe(true);
              expect(genesisStateManager.isOperationAllowed('transaction_history')).toBe(true);
              
              // Network state should be ACTIVE
              const networkState = genesisStateManager.getCurrentNetworkState();
              expect(networkState).toBe(NetworkState.ACTIVE);
            }

            // State info should be consistent
            const stateInfo = genesisStateManager.getStateInfo();
            expect(stateInfo.genesisState.exists).toBe(genesisExists);
            
            // Available operations should match genesis state
            const availableOps = stateInfo.availableOperations;
            if (genesisExists) {
              expect(availableOps).toContain('send_transaction');
              expect(availableOps).toContain('balance_query');
            } else {
              expect(availableOps).not.toContain('send_transaction');
              expect(availableOps).not.toContain('balance_query');
              expect(availableOps).toContain('wallet_creation');
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('Genesis State Detection', () => {
    beforeEach(() => {
      // Mock bootstrap service to return a valid state
      mockBootstrapService.getState.mockReturnValue({
        mode: 'pioneer'
      });
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
    });

    test('should detect genesis from bootstrap service', async () => {
      const genesisBlock = {
        hash: 'test_genesis_hash',
        timestamp: Date.now()
      };

      mockBootstrapService.getState.mockReturnValue({
        mode: 'network',
        genesisBlock: genesisBlock
      });

      const genesisState = await genesisStateManager.checkGenesisExists();

      expect(genesisState.exists).toBe(true);
      expect(genesisState.blockHash).toBe(genesisBlock.hash);
      expect(genesisState.isVerified).toBe(true);
    });

    test('should detect genesis from network status', async () => {
      mockBootstrapService.getState.mockReturnValue({
        mode: 'pioneer',
        genesisBlock: null
      });

      mockNetworkService.getNetworkStatus.mockResolvedValue({
        success: true,
        status: {
          blockchain_height: 5,
          genesis_hash: 'network_genesis_hash',
          genesis_timestamp: Date.now()
        }
      });

      const genesisState = await genesisStateManager.checkGenesisExists();

      expect(genesisState.exists).toBe(true);
      expect(genesisState.blockHash).toBe('network_genesis_hash');
      expect(genesisState.isVerified).toBe(true);
    });

    test('should detect no genesis when blockchain is empty', async () => {
      mockBootstrapService.getState.mockReturnValue({
        mode: 'pioneer',
        genesisBlock: null
      });

      mockNetworkService.getNetworkStatus.mockResolvedValue({
        success: false,
        error: 'No blockchain found',
        requiresGenesis: true
      });

      mockNetworkService.getBalance.mockResolvedValue({
        success: false,
        balance: '0',
        error: 'Genesis required',
        requiresGenesis: true
      });

      const genesisState = await genesisStateManager.checkGenesisExists();

      expect(genesisState.exists).toBe(false);
      expect(genesisState.blockHash).toBeNull();
      expect(genesisState.isVerified).toBe(false);
    });
  });

  describe('Network State Management', () => {
    beforeEach(() => {
      // Mock bootstrap service to return a valid state
      mockBootstrapService.getState.mockReturnValue({
        mode: 'pioneer'
      });
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
    });

    test('should derive network state from bootstrap service', () => {
      const testCases = [
        { bootstrapMode: 'pioneer', expectedState: NetworkState.BOOTSTRAP_PIONEER },
        { bootstrapMode: 'discovery', expectedState: NetworkState.BOOTSTRAP_DISCOVERY },
        { bootstrapMode: 'genesis', expectedState: NetworkState.BOOTSTRAP_GENESIS },
        { bootstrapMode: 'network', expectedState: NetworkState.ACTIVE }
      ];

      testCases.forEach(({ bootstrapMode, expectedState }) => {
        // Create a new instance for each test case to ensure clean state
        const testManager = new GenesisStateManager();
        
        mockBootstrapService.getState.mockReturnValue({
          mode: bootstrapMode
        });

        testManager.initialize(mockNetworkService, mockBootstrapService);
        
        const networkState = testManager.getCurrentNetworkState();
        expect(networkState).toBe(expectedState);
        
        testManager.cleanup();
      });
    });

    test('should update network state correctly', () => {
      const stateChanges = [];
      genesisStateManager.on('networkStateChanged', (newState, oldState) => {
        stateChanges.push({ newState, oldState });
      });

      genesisStateManager.updateNetworkState(NetworkState.CONNECTING);
      genesisStateManager.updateNetworkState(NetworkState.ACTIVE);

      expect(stateChanges).toHaveLength(2);
      expect(stateChanges[0].newState).toBe(NetworkState.CONNECTING);
      expect(stateChanges[1].newState).toBe(NetworkState.ACTIVE);
    });
  });

  describe('Operation Permissions', () => {
    beforeEach(() => {
      // Mock bootstrap service to return a valid state
      mockBootstrapService.getState.mockReturnValue({
        mode: 'pioneer'
      });
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
    });

    test('should allow wallet creation in all states', () => {
      const allStates = Object.values(NetworkState);
      
      allStates.forEach(state => {
        genesisStateManager.updateNetworkState(state);
        expect(genesisStateManager.isOperationAllowed('wallet_creation')).toBe(true);
      });
    });

    test('should only allow blockchain operations in ACTIVE state', () => {
      const blockchainOps = ['send_transaction', 'mining', 'faucet', 'balance_query'];
      
      // Test in ACTIVE state
      genesisStateManager.updateNetworkState(NetworkState.ACTIVE);
      blockchainOps.forEach(op => {
        expect(genesisStateManager.isOperationAllowed(op)).toBe(true);
      });

      // Test in non-ACTIVE states
      const nonActiveStates = [
        NetworkState.DISCONNECTED,
        NetworkState.CONNECTING,
        NetworkState.BOOTSTRAP_PIONEER,
        NetworkState.BOOTSTRAP_DISCOVERY,
        NetworkState.BOOTSTRAP_GENESIS
      ];

      nonActiveStates.forEach(state => {
        genesisStateManager.updateNetworkState(state);
        blockchainOps.forEach(op => {
          expect(genesisStateManager.isOperationAllowed(op)).toBe(false);
        });
      });
    });

    test('should handle unknown operations gracefully', () => {
      genesisStateManager.updateNetworkState(NetworkState.ACTIVE);
      expect(genesisStateManager.isOperationAllowed('unknown_operation')).toBe(false);
    });
  });

  describe('State Information', () => {
    beforeEach(() => {
      // Mock bootstrap service to return a valid state
      mockBootstrapService.getState.mockReturnValue({
        mode: 'network'
      });
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
    });

    test('should provide comprehensive state information', () => {
      genesisStateManager.updateNetworkState(NetworkState.ACTIVE);
      genesisStateManager.genesisState = new GenesisState(true, 'test_hash', new Date(), true);

      const stateInfo = genesisStateManager.getStateInfo();

      expect(stateInfo).toHaveProperty('networkState');
      expect(stateInfo).toHaveProperty('genesisState');
      expect(stateInfo).toHaveProperty('availableOperations');
      expect(stateInfo.networkState).toBe(NetworkState.ACTIVE);
      expect(stateInfo.genesisState.exists).toBe(true);
      expect(Array.isArray(stateInfo.availableOperations)).toBe(true);
    });

    test('should list correct available operations', () => {
      // Test ACTIVE state
      genesisStateManager.updateNetworkState(NetworkState.ACTIVE);
      const activeOps = genesisStateManager.getAvailableOperations();
      expect(activeOps).toContain('send_transaction');
      expect(activeOps).toContain('wallet_creation');

      // Test PIONEER state
      genesisStateManager.updateNetworkState(NetworkState.BOOTSTRAP_PIONEER);
      const pioneerOps = genesisStateManager.getAvailableOperations();
      expect(pioneerOps).not.toContain('send_transaction');
      expect(pioneerOps).toContain('wallet_creation');
      expect(pioneerOps).toContain('peer_discovery');
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      mockBootstrapService.getState.mockReturnValue({
        mode: 'pioneer',
        genesisBlock: null
      });
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
    });

    test('should handle network service errors gracefully', async () => {
      mockNetworkService.getNetworkStatus.mockRejectedValue(new Error('Network error'));
      mockNetworkService.getBalance.mockRejectedValue(new Error('Balance error'));

      // The method should handle errors gracefully and return a state, not throw
      const genesisState = await genesisStateManager.checkGenesisExists();
      
      // Should still have a valid genesis state (false) even with errors
      expect(genesisState.exists).toBe(false);
      expect(genesisStateManager.genesisState.exists).toBe(false);
    });

    test('should handle invalid network state updates', () => {
      expect(() => {
        genesisStateManager.updateNetworkState('invalid_state');
      }).toThrow('Invalid network state: invalid_state');
    });
  });

  describe('Cleanup and Reset', () => {
    beforeEach(() => {
      mockBootstrapService.getState.mockReturnValue({
        mode: 'network'
      });
      genesisStateManager.initialize(mockNetworkService, mockBootstrapService);
    });

    test('should reset to initial state', () => {
      genesisStateManager.updateNetworkState(NetworkState.ACTIVE);
      genesisStateManager.genesisState = new GenesisState(true, 'test', new Date(), true);

      genesisStateManager.reset();

      expect(genesisStateManager.getCurrentNetworkState()).toBe(NetworkState.DISCONNECTED);
      expect(genesisStateManager.genesisState.exists).toBe(false);
    });

    test('should cleanup resources properly', () => {
      const stopSpy = jest.spyOn(genesisStateManager, 'stopPeriodicStateCheck');
      const removeListenersSpy = jest.spyOn(genesisStateManager, 'removeAllListeners');

      genesisStateManager.cleanup();

      expect(stopSpy).toHaveBeenCalled();
      expect(removeListenersSpy).toHaveBeenCalled();
    });
  });
});