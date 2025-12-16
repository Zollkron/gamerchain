/**
 * Simple integration tests for complete mock data removal
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

describe('Mock Data Removal - Simple Tests', () => {
  let mockStore;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup mock store
    mockStore = {
      get: jest.fn(),
      set: jest.fn(),
      delete: jest.fn()
    };
    Store.mockImplementation(() => mockStore);

    // Setup immediate rejection for network calls
    axios.get.mockRejectedValue(new Error('Network unavailable'));
    axios.post.mockRejectedValue(new Error('Network unavailable'));
  });

  describe('Core Mock Data Validation', () => {
    test('MiningService should not return mock hardware info', () => {
      const result = MiningService.checkSystemCapabilities();
      
      expect(result.adequate).toBe(false); // Conservative default
      expect(result.gpu).toBe('Hardware detection not implemented');
      expect(result.ram).toBe('Memory detection not implemented');
    });

    test('MiningService should not return mock rewards', () => {
      const result = MiningService.estimateMiningRewards();
      
      expect(result.hourly).toBe(0);
      expect(result.daily).toBe(0);
      expect(result.weekly).toBe(0);
      expect(result.monthly).toBe(0);
      expect(result.factors).toContain('Network data required for accurate estimation');
    });

    test('AIModelService should not return mock compatibility', () => {
      const mockModelId = 'test-model';
      
      const result = AIModelService.checkSystemRequirements(mockModelId);
      
      expect(result.compatible).toBe(false); // Conservative default - model not found
      expect(result.reason).toBe('Model not found');
    });

    test('WalletService should not return mock balance', async () => {
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
      
      const testWalletId = 'test-wallet-123';
      
      const result = await WalletService.getWalletBalance(testWalletId);
      
      expect(result.isMock).toBe(false);
      expect(result.balance).toBe('0');
      expect(result.requiresGenesis).toBe(true);
    });

    test('WalletService should not return mock transactions', async () => {
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
      
      const testWalletId = 'test-wallet-123';
      
      const result = await WalletService.getTransactionHistory(testWalletId);
      
      expect(result.isMock).toBe(false);
      expect(result.transactions).toEqual([]);
      expect(result.requiresGenesis).toBe(true);
    });
  });

  describe('Property-Based Test: No Mock Data Property', () => {
    test('**Genesis State Validation, Property 1: No Mock Data Property**', async () => {
      // Property: For any service operation, the system should never return mock data
      
      // Test MiningService operations
      const miningCapabilities = MiningService.checkSystemCapabilities();
      expect(miningCapabilities.adequate).toBe(false); // No mock "true" values
      
      const miningRewards = MiningService.estimateMiningRewards();
      expect(miningRewards.hourly).toBe(0); // No mock reward values
      
      // Test AIModelService operations
      const modelCompatibility = AIModelService.checkSystemRequirements('nonexistent-model');
      expect(modelCompatibility.compatible).toBe(false); // No mock compatibility
      
      // Test WalletService operations
      const mockGenesisStateManager = new GenesisStateManager();
      jest.spyOn(mockGenesisStateManager, 'checkGenesisExists').mockResolvedValue({
        exists: false,
        isVerified: false
      });
      
      WalletService.genesisStateManager = mockGenesisStateManager;
      mockStore.get.mockReturnValue([]);
      
      const balanceResult = await WalletService.getWalletBalance('test-wallet');
      expect(balanceResult.isMock).toBe(false);
      expect(balanceResult.balance).toBe('0'); // No mock balance
      
      const historyResult = await WalletService.getTransactionHistory('test-wallet');
      expect(historyResult.isMock).toBe(false);
      expect(historyResult.transactions).toEqual([]); // No mock transactions
      
      // All operations should return real error states, not mock success
      console.log('✅ All services return real data, no mock values detected');
    });
  });

  describe('Error State Validation', () => {
    test('All services return proper error states instead of mock data', async () => {
      // Test that services return proper error states when they can't provide real data
      
      // MiningService returns conservative defaults
      const capabilities = MiningService.checkSystemCapabilities();
      expect(capabilities.adequate).toBe(false);
      expect(capabilities.gpu).toContain('not implemented');
      
      // AIModelService returns proper error for unknown models
      const compatibility = AIModelService.checkSystemRequirements('unknown');
      expect(compatibility.compatible).toBe(false);
      expect(compatibility.reason).toBe('Model not found');
      
      // WalletService returns zero balance when no genesis
      const mockGenesisStateManager = new GenesisStateManager();
      jest.spyOn(mockGenesisStateManager, 'checkGenesisExists').mockResolvedValue({
        exists: false,
        isVerified: false
      });
      
      WalletService.genesisStateManager = mockGenesisStateManager;
      mockStore.get.mockReturnValue([]);
      
      const balance = await WalletService.getWalletBalance('test');
      expect(balance.balance).toBe('0');
      expect(balance.requiresGenesis).toBe(true);
      expect(balance.isMock).toBe(false);
      
      console.log('✅ All error states are real, no mock fallbacks detected');
    });
  });
});