/**
 * Integration tests for complete mock data removal
 * Validates Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 * 
 * These tests verify that no mock data is returned in any scenario
 * and that all error paths return real errors instead of fake data.
 */

const NetworkService = require('../NetworkService');
const WalletService = require('../WalletService');
const { GenesisStateManager } = require('../GenesisStateManager');
const MiningService = require('../MiningService');
const AIModelService = require('../AIModelService');

// Mock external dependencies to simulate network failures
jest.mock('axios');
jest.mock('electron-store');

const axios = require('axios');
const Store = require('electron-store');

describe('Mock Data Removal Integration Tests', () => {
  let mockStore;

  // Increase timeout for integration tests
  jest.setTimeout(30000);

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup mock store
    mockStore = {
      get: jest.fn(),
      set: jest.fn(),
      delete: jest.fn()
    };
    Store.mockImplementation(() => mockStore);

    // Setup default mock responses for network failures with faster timeout
    axios.get.mockRejectedValue(new Error('Network unavailable'));
    axios.post.mockRejectedValue(new Error('Network unavailable'));
    
    // Increase test timeout for network operations
    jest.setTimeout(10000);
  });

  describe('NetworkService - No Mock Data', () => {
    test('getBalance should never return mock data', async () => {
      const testAddress = 'PG' + 'a'.repeat(38);
      
      const result = await NetworkService.getBalance(testAddress);
      
      expect(result.isMock).toBe(false);
      expect(result.success).toBe(false);
      expect(result.balance).toBe('0');
      expect(result.error).toBeDefined();
      expect(result.requiresGenesis).toBe(true);
    });

    test('getTransactionHistory should never return mock transactions', async () => {
      const testAddress = 'PG' + 'a'.repeat(38);
      
      const result = await NetworkService.getTransactionHistory(testAddress);
      
      expect(result.isMock).toBe(false);
      expect(result.success).toBe(false);
      expect(result.transactions).toEqual([]);
      expect(result.error).toBeDefined();
      expect(result.requiresGenesis).toBe(true);
    });

    test('getNetworkStatus should never return mock status', async () => {
      const result = await NetworkService.getNetworkStatus();
      
      expect(result.isMock).toBe(false);
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.requiresGenesis).toBe(true);
    });

    test('requestFaucetTokens should never return mock success', async () => {
      const testAddress = 'PG' + 'a'.repeat(38);
      
      const result = await NetworkService.requestFaucetTokens(testAddress, 1000);
      
      expect(result.isMock).toBe(false);
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.requiresGenesis).toBe(true);
    });

    test('getMiningChallenge should never return mock challenges', async () => {
      const result = await NetworkService.getMiningChallenge();
      
      expect(result.isMock).toBe(false);
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.requiresGenesis).toBe(true);
    });
  });

  describe('WalletService - No Mock Data', () => {
    beforeEach(() => {
      // Mock no genesis exists
      const mockGenesisStateManager = new GenesisStateManager();
      jest.spyOn(mockGenesisStateManager, 'checkGenesisExists').mockResolvedValue({
        exists: false,
        isVerified: false
      });
      
      // Setup wallet service with genesis state manager
      WalletService.genesisStateManager = mockGenesisStateManager;
      
      // Mock empty wallet store
      mockStore.get.mockReturnValue([]);
    });

    test('getWalletBalance should never return mock balance', async () => {
      const testWalletId = 'test-wallet-123';
      
      const result = await WalletService.getWalletBalance(testWalletId);
      
      expect(result.isMock).toBe(false);
      expect(result.balance).toBe('0');
      expect(result.requiresGenesis).toBe(true);
    });

    test('getTransactionHistory should never return mock transactions', async () => {
      const testWalletId = 'test-wallet-123';
      
      const result = await WalletService.getTransactionHistory(testWalletId);
      
      expect(result.isMock).toBe(false);
      expect(result.transactions).toEqual([]);
      expect(result.requiresGenesis).toBe(true);
    });

    test('syncWallet should never return mock sync data', async () => {
      const testWalletId = 'test-wallet-123';
      
      const result = await WalletService.syncWallet(testWalletId);
      
      expect(result.isMock).toBe(false);
      expect(result.requiresGenesis).toBe(true);
    });
  });

  describe('MiningService - No Mock Data', () => {
    test('checkSystemCapabilities should not return mock hardware info', () => {
      const result = MiningService.checkSystemCapabilities();
      
      expect(result.adequate).toBe(false); // Conservative default
      expect(result.gpu).toBe('Hardware detection not implemented');
      expect(result.ram).toBe('Memory detection not implemented');
    });

    test('estimateMiningRewards should not return mock rewards', () => {
      const result = MiningService.estimateMiningRewards();
      
      expect(result.hourly).toBe(0);
      expect(result.daily).toBe(0);
      expect(result.weekly).toBe(0);
      expect(result.monthly).toBe(0);
      expect(result.factors).toContain('Network data required for accurate estimation');
    });
  });

  describe('AIModelService - No Mock Data', () => {
    test('checkSystemRequirements should not return mock compatibility', () => {
      const mockModelId = 'test-model';
      
      const result = AIModelService.checkSystemRequirements(mockModelId);
      
      expect(result.compatible).toBe(false); // Conservative default - model not found
      expect(result.reason).toBe('Model not found');
    });
  });

  describe('End-to-End Mock Data Validation', () => {
    test('complete wallet flow should never return mock data', async () => {
      // Create a test wallet
      const testWallet = {
        id: 'test-wallet-e2e',
        name: 'Test Wallet',
        address: 'PG' + 'a'.repeat(38),
        createdAt: new Date().toISOString()
      };
      
      mockStore.get.mockReturnValue([testWallet]);
      
      // Test balance retrieval
      const balanceResult = await WalletService.getWalletBalance(testWallet.id);
      expect(balanceResult.isMock).toBe(false);
      expect(balanceResult.balance).toBe('0');
      
      // Test transaction history
      const historyResult = await WalletService.getTransactionHistory(testWallet.id);
      expect(historyResult.isMock).toBe(false);
      expect(historyResult.transactions).toEqual([]);
      
      // Test network status
      const networkResult = await NetworkService.getNetworkStatus();
      expect(networkResult.isMock).toBe(false);
      expect(networkResult.success).toBe(false);
      
      // Test faucet request
      const faucetResult = await NetworkService.requestFaucetTokens(testWallet.address, 1000);
      expect(faucetResult.isMock).toBe(false);
      expect(faucetResult.success).toBe(false);
    });

    test('UI behavior with real empty states', async () => {
      // Mock genesis state manager to return no genesis
      const mockGenesisStateManager = new GenesisStateManager();
      jest.spyOn(mockGenesisStateManager, 'checkGenesisExists').mockResolvedValue({
        exists: false,
        isVerified: false
      });
      
      WalletService.genesisStateManager = mockGenesisStateManager;
      
      // Mock empty wallet
      const testWallet = {
        id: 'test-wallet-ui',
        name: 'UI Test Wallet',
        address: 'PG' + 'b'.repeat(38),
        createdAt: new Date().toISOString()
      };
      
      mockStore.get.mockReturnValue([testWallet]);
      
      // Get wallet display state
      const balanceResult = await WalletService.getWalletBalance(testWallet.id);
      const historyResult = await WalletService.getTransactionHistory(testWallet.id);
      
      // Verify UI would show real empty states
      expect(balanceResult.balance).toBe('0');
      expect(balanceResult.requiresGenesis).toBe(true);
      expect(balanceResult.isMock).toBe(false);
      
      expect(historyResult.transactions).toEqual([]);
      expect(historyResult.requiresGenesis).toBe(true);
      expect(historyResult.isMock).toBe(false);
      
      // Verify error messages are informative (if message exists)
      if (historyResult.message) {
        expect(historyResult.message).toContain('blockchain not initialized');
      }
    });

    test('all error paths return real errors', async () => {
      const testAddress = 'PG' + 'c'.repeat(38);
      
      // Test various error scenarios
      const errorScenarios = [
        () => NetworkService.getBalance(testAddress),
        () => NetworkService.getTransactionHistory(testAddress),
        () => NetworkService.getNetworkStatus(),
        () => NetworkService.requestFaucetTokens(testAddress, 1000),
        () => NetworkService.getMiningChallenge()
      ];
      
      for (const scenario of errorScenarios) {
        const result = await scenario();
        
        // Every error result should be real, not mock
        expect(result.isMock).toBe(false);
        expect(result.success).toBe(false);
        expect(result.error).toBeDefined();
        expect(typeof result.error).toBe('string');
        expect(result.error.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Property-Based Test: No Mock Data Property', () => {
    test('**Genesis State Validation, Property 1: No Mock Data Property**', async () => {
      // Property: For any wallet operation, the system should never return mock data
      const testCases = [
        { address: 'PG' + 'a'.repeat(38), operation: 'getBalance' },
        { address: 'PG' + 'b'.repeat(38), operation: 'getTransactionHistory' },
        { address: 'PG' + 'c'.repeat(38), operation: 'requestFaucetTokens' },
        { address: 'PG' + 'd'.repeat(38), operation: 'getNetworkStatus' },
        { address: 'PG' + 'e'.repeat(38), operation: 'getMiningChallenge' }
      ];
      
      for (const testCase of testCases) {
        let result;
        
        switch (testCase.operation) {
          case 'getBalance':
            result = await NetworkService.getBalance(testCase.address);
            break;
          case 'getTransactionHistory':
            result = await NetworkService.getTransactionHistory(testCase.address);
            break;
          case 'requestFaucetTokens':
            result = await NetworkService.requestFaucetTokens(testCase.address, 1000);
            break;
          case 'getNetworkStatus':
            result = await NetworkService.getNetworkStatus();
            break;
          case 'getMiningChallenge':
            result = await NetworkService.getMiningChallenge();
            break;
        }
        
        // Assert: Never return mock data
        expect(result.isMock).toBe(false);
        if (!result.success) {
          expect(result.error).toBeDefined();
          expect(typeof result.error).toBe('string');
        }
      }
    });
  });
});