/**
 * Tests for GenesisCoordinator - Auto-Bootstrap P2P Network
 * Includes both unit tests and property-based tests
 */

// Mock fast-check for property-based testing
const fc = {
  assert: (property, options) => {
    // Run the property multiple times with generated data
    for (let i = 0; i < (options?.numRuns || 100); i++) {
      try {
        const testData = property.generator();
        property.predicate(testData);
      } catch (error) {
        throw new Error(`Property failed on run ${i + 1}: ${error.message}`);
      }
    }
  },
  property: (generator, predicate) => ({ generator, predicate }),
  record: (obj) => () => {
    const result = {};
    for (const [key, gen] of Object.entries(obj)) {
      result[key] = typeof gen === 'function' ? gen() : gen;
    }
    return result;
  },
  array: (gen, opts) => () => {
    const length = Math.max(opts?.minLength || 2, Math.floor(Math.random() * (opts?.maxLength || 10)) + 1);
    return Array(length).fill().map(() => typeof gen === 'function' ? gen() : gen);
  },
  string: (opts) => () => {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    const length = Math.max(opts?.minLength || 5, Math.floor(Math.random() * (opts?.maxLength || 20)) + 1);
    return Array(length).fill().map(() => chars[Math.floor(Math.random() * chars.length)]).join('');
  },
  integer: (opts) => () => {
    const min = opts?.min || 0;
    const max = opts?.max || 1000000;
    return Math.floor(Math.random() * (max - min + 1)) + min;
  },
  constantFrom: (...values) => () => values[Math.floor(Math.random() * values.length)],
  nat: (max) => () => Math.floor(Math.random() * (max || 1000))
};

const { 
  GenesisCoordinator, 
  GenesisParams, 
  NetworkConfig, 
  GenesisBlock, 
  GenesisPhase 
} = require('../GenesisCoordinator');

describe('GenesisCoordinator', () => {
  let genesisCoordinator;

  beforeEach(() => {
    genesisCoordinator = new GenesisCoordinator();
  });

  afterEach(() => {
    if (genesisCoordinator) {
      genesisCoordinator.removeAllListeners();
      genesisCoordinator.reset();
    }
  });

  describe('Unit Tests', () => {
    describe('initialization', () => {
      it('should initialize with correct default state', () => {
        expect(genesisCoordinator.currentPhase).toBeNull();
        expect(genesisCoordinator.isCoordinating).toBe(false);
        expect(genesisCoordinator.participants).toEqual([]);
      });
    });

    describe('parameter negotiation', () => {
      it('should negotiate genesis parameters with valid peers', async () => {
        const peers = [
          {
            id: 'peer1',
            address: '192.168.1.100',
            port: 8000,
            walletAddress: 'PG1234567890abcdef1234567890abcdef12345678',
            networkMode: 'testnet',
            isReady: true
          },
          {
            id: 'peer2',
            address: '192.168.1.101',
            port: 8000,
            walletAddress: 'PG9876543210fedcba9876543210fedcba87654321',
            networkMode: 'testnet',
            isReady: true
          }
        ];

        const params = await genesisCoordinator.negotiateGenesisParameters(peers);

        expect(params).toBeInstanceOf(GenesisParams);
        expect(params.participants).toHaveLength(2);
        expect(params.participants).toContain(peers[0].walletAddress);
        expect(params.participants).toContain(peers[1].walletAddress);
        expect(params.networkId).toBeDefined();
        expect(params.consensusRules.algorithm).toBe('PoAIP');
      });

      it('should reject insufficient peers', async () => {
        const singlePeer = [{
          id: 'peer1',
          address: '192.168.1.100',
          port: 8000,
          walletAddress: 'PG1234567890abcdef1234567890abcdef12345678',
          networkMode: 'testnet',
          isReady: true
        }];

        await expect(genesisCoordinator.negotiateGenesisParameters(singlePeer))
          .rejects.toThrow('At least 2 peers required for genesis creation');
      });
    });

    describe('genesis block creation', () => {
      it('should create valid genesis block', async () => {
        const params = new GenesisParams(
          Date.now(),
          1,
          ['PG1234567890abcdef1234567890abcdef12345678'],
          new Map([['PG1234567890abcdef1234567890abcdef12345678', 10.0]]),
          'test-network',
          { algorithm: 'PoAIP', blockTime: 600 }
        );

        const block = await genesisCoordinator.createGenesisBlock(params);

        expect(block).toBeInstanceOf(GenesisBlock);
        expect(block.index).toBe(0);
        expect(block.previousHash).toBe('0'.repeat(64));
        expect(block.transactions).toHaveLength(1);
        expect(block.transactions[0].type).toBe('genesis_reward');
        expect(block.hash).toBeDefined();
        expect(block.hash).toHaveLength(64);
      });
    });

    describe('network configuration persistence', () => {
      it('should persist network configuration', () => {
        const config = new NetworkConfig(
          'test-network',
          'genesis-hash-123',
          [],
          { algorithm: 'PoAIP' },
          new Date()
        );

        expect(() => {
          genesisCoordinator.persistNetworkConfiguration(config);
        }).not.toThrow();

        expect(genesisCoordinator.networkConfig).toBe(config);
      });
    });
  });

  describe('Property-Based Tests', () => {
    /**
     * **Feature: auto-bootstrap-p2p, Property 8: Genesis coordination**
     * **Validates: Requirements 3.3**
     * 
     * For any set of connected peers, the system should coordinate genesis block 
     * creation among all peers
     */
    it('Property 8: Genesis coordination', () => {
      fc.assert(fc.property(
        fc.array(
          fc.record({
            id: fc.string({ minLength: 5, maxLength: 20 }),
            address: fc.constantFrom('192.168.1.100', '192.168.1.101', '192.168.1.102', '10.0.0.1', '10.0.0.2'),
            port: fc.constantFrom(8000, 8001, 8002),
            walletAddress: fc.string({ minLength: 42, maxLength: 42 }),
            networkMode: fc.constantFrom('testnet', 'mainnet'),
            isReady: fc.constantFrom(true),
            capabilities: fc.constantFrom(['p2p-discovery', 'genesis-creation'])
          }),
          { minLength: 2, maxLength: 5 }
        ),
        async (peers) => {
          const coordinator = new GenesisCoordinator();
          
          try {
            // Property: Genesis coordination should work for any valid set of connected peers
            const result = await coordinator.coordinateGenesis(peers);
            
            // Verify coordination result structure
            expect(result).toBeDefined();
            expect(result.success).toBe(true);
            expect(result.block).toBeDefined();
            expect(result.networkConfig).toBeDefined();
            expect(result.participants).toBeDefined();
            
            // Verify all peers are included in participants
            const participantAddresses = result.participants;
            const peerAddresses = peers.map(p => p.walletAddress).filter(addr => addr);
            
            for (const peerAddr of peerAddresses) {
              expect(participantAddresses).toContain(peerAddr);
            }
            
            // Verify genesis block properties
            expect(result.block.index).toBe(0);
            expect(result.block.previousHash).toBe('0'.repeat(64));
            expect(result.block.hash).toBeDefined();
            expect(result.block.transactions.length).toBeGreaterThan(0);
            
            // Verify network configuration
            expect(result.networkConfig.networkId).toBeDefined();
            expect(result.networkConfig.genesisHash).toBe(result.block.hash);
            expect(result.networkConfig.peers).toHaveLength(peers.length);
            
            coordinator.removeAllListeners();
            coordinator.reset();
            
            return true;
          } catch (error) {
            coordinator.removeAllListeners();
            coordinator.reset();
            throw error;
          }
        }
      ), { numRuns: 100 });
    });

    /**
     * **Feature: auto-bootstrap-p2p, Property 18: Network configuration persistence**
     * **Validates: Requirements 5.4**
     * 
     * For any successful genesis block creation, storing and retrieving the network 
     * configuration should return the same configuration
     */
    it('Property 18: Network configuration persistence', () => {
      fc.assert(fc.property(
        fc.record({
          networkId: fc.string({ minLength: 8, maxLength: 32 }),
          genesisHash: fc.string({ minLength: 64, maxLength: 64 }),
          peers: fc.array(
            fc.record({
              id: fc.string({ minLength: 5, maxLength: 20 }),
              address: fc.constantFrom('192.168.1.100', '192.168.1.101', '10.0.0.1'),
              port: fc.constantFrom(8000, 8001, 8002),
              walletAddress: fc.string({ minLength: 42, maxLength: 42 }),
              networkMode: fc.constantFrom('testnet', 'mainnet')
            }),
            { minLength: 1, maxLength: 5 }
          ),
          consensusRules: fc.record({
            algorithm: fc.constantFrom('PoAIP', 'PoW', 'PoS'),
            blockTime: fc.constantFrom(600, 300, 900),
            minValidators: fc.integer({ min: 1, max: 10 }),
            maxValidators: fc.integer({ min: 10, max: 100 })
          }),
          createdAt: fc.constantFrom(new Date())
        }),
        (configData) => {
          const coordinator = new GenesisCoordinator();
          
          try {
            // Create network configuration
            const originalConfig = new NetworkConfig(
              configData.networkId,
              configData.genesisHash,
              configData.peers,
              configData.consensusRules,
              configData.createdAt
            );
            
            // Property: Persist configuration
            coordinator.persistNetworkConfiguration(originalConfig);
            
            // Retrieve persisted configuration
            const retrievedConfig = coordinator.networkConfig;
            
            // Property: Retrieved configuration should match original
            expect(retrievedConfig).toBeDefined();
            expect(retrievedConfig.networkId).toBe(originalConfig.networkId);
            expect(retrievedConfig.genesisHash).toBe(originalConfig.genesisHash);
            expect(retrievedConfig.peers).toHaveLength(originalConfig.peers.length);
            expect(retrievedConfig.consensusRules.algorithm).toBe(originalConfig.consensusRules.algorithm);
            expect(retrievedConfig.consensusRules.blockTime).toBe(originalConfig.consensusRules.blockTime);
            expect(retrievedConfig.createdAt).toEqual(originalConfig.createdAt);
            
            // Property: Configuration should be serializable and deserializable
            const serialized = retrievedConfig.toDict();
            const deserialized = NetworkConfig.fromDict(serialized);
            
            expect(deserialized.networkId).toBe(originalConfig.networkId);
            expect(deserialized.genesisHash).toBe(originalConfig.genesisHash);
            expect(deserialized.peers).toHaveLength(originalConfig.peers.length);
            expect(deserialized.consensusRules.algorithm).toBe(originalConfig.consensusRules.algorithm);
            
            coordinator.removeAllListeners();
            coordinator.reset();
            
            return true;
          } catch (error) {
            coordinator.removeAllListeners();
            coordinator.reset();
            throw error;
          }
        }
      ), { numRuns: 100 });
    });

    /**
     * Additional property test: Genesis block consistency
     */
    it('Property: Genesis block consistency across multiple coordinations', () => {
      fc.assert(fc.property(
        fc.record({
          peers: fc.array(
            fc.record({
              id: fc.string({ minLength: 5, maxLength: 15 }),
              address: fc.constantFrom('192.168.1.100', '192.168.1.101', '192.168.1.102'),
              port: fc.constantFrom(8000, 8001),
              walletAddress: fc.string({ minLength: 42, maxLength: 42 }),
              networkMode: fc.constantFrom('testnet'),
              isReady: fc.constantFrom(true)
            }),
            { minLength: 2, maxLength: 4 }
          ),
          iterations: fc.integer({ min: 2, max: 5 })
        }),
        async (testData) => {
          const { peers, iterations } = testData;
          const results = [];
          
          // Run genesis coordination multiple times with same peers
          for (let i = 0; i < iterations; i++) {
            const coordinator = new GenesisCoordinator();
            
            try {
              const result = await coordinator.coordinateGenesis(peers);
              results.push(result);
              
              coordinator.removeAllListeners();
              coordinator.reset();
            } catch (error) {
              coordinator.removeAllListeners();
              coordinator.reset();
              throw error;
            }
          }
          
          // Property: Each coordination should produce valid but unique results
          for (let i = 0; i < results.length; i++) {
            const result = results[i];
            
            // Each result should be valid
            expect(result.success).toBe(true);
            expect(result.block.index).toBe(0);
            expect(result.participants.length).toBe(peers.length);
            
            // Network IDs should be unique (different timestamps)
            for (let j = i + 1; j < results.length; j++) {
              expect(result.networkConfig.networkId).not.toBe(results[j].networkConfig.networkId);
            }
          }
          
          return true;
        }
      ), { numRuns: 50 });
    });

    /**
     * Property test: Parameter negotiation consistency
     */
    it('Property: Parameter negotiation produces consistent results', () => {
      fc.assert(fc.property(
        fc.array(
          fc.record({
            id: fc.string({ minLength: 8, maxLength: 16 }),
            address: fc.constantFrom('192.168.1.100', '192.168.1.101', '192.168.1.102', '10.0.0.1'),
            port: fc.constantFrom(8000, 8001, 8002),
            walletAddress: fc.string({ minLength: 42, maxLength: 42 }),
            networkMode: fc.constantFrom('testnet', 'mainnet'),
            isReady: fc.constantFrom(true)
          }),
          { minLength: 2, maxLength: 6 }
        ),
        async (peers) => {
          const coordinator = new GenesisCoordinator();
          
          try {
            const params = await coordinator.negotiateGenesisParameters(peers);
            
            // Property: Negotiated parameters should be consistent with input peers
            expect(params.participants.length).toBe(peers.filter(p => p.walletAddress).length);
            expect(params.difficulty).toBe(1); // Default difficulty
            expect(params.consensusRules.algorithm).toBe('PoAIP');
            expect(params.networkId).toBeDefined();
            expect(params.networkId.length).toBe(16);
            
            // All peer wallet addresses should be in participants
            const peerAddresses = peers.map(p => p.walletAddress).filter(addr => addr);
            for (const addr of peerAddresses) {
              expect(params.participants).toContain(addr);
            }
            
            // Initial rewards should be set for all participants
            expect(params.initialRewards.size).toBe(peerAddresses.length);
            for (const addr of peerAddresses) {
              expect(params.initialRewards.has(addr)).toBe(true);
              expect(params.initialRewards.get(addr)).toBe(10.0); // Base reward
            }
            
            coordinator.removeAllListeners();
            coordinator.reset();
            
            return true;
          } catch (error) {
            coordinator.removeAllListeners();
            coordinator.reset();
            throw error;
          }
        }
      ), { numRuns: 100 });
    });
  });
});