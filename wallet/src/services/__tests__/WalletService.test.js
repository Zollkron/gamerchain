/**
 * Tests for WalletService
 * Note: These are basic tests. In a real implementation, you would need to mock electron-store
 */

const bip39 = require('bip39');

describe('WalletService', () => {
  // Mock electron-store
  const mockStore = {
    get: jest.fn(() => []),
    set: jest.fn()
  };

  // Mock the WalletService with mocked dependencies
  const createMockWalletService = () => {
    const WalletService = require('../WalletService').WalletService;
    WalletService.store = mockStore;
    return WalletService;
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('generateWallet', () => {
    it('should generate a valid wallet with mnemonic', async () => {
      const walletService = createMockWalletService();
      const result = await walletService.generateWallet();

      expect(result.success).toBe(true);
      expect(result.wallet).toBeDefined();
      expect(result.wallet.address).toMatch(/^PG[a-f0-9]{38}$/);
      expect(result.wallet.mnemonic).toBeDefined();
      
      // Verify mnemonic is valid
      const words = result.wallet.mnemonic.split(' ');
      expect(words).toHaveLength(12);
      expect(bip39.validateMnemonic(result.wallet.mnemonic)).toBe(true);
    });

    it('should not return private key in response', async () => {
      const walletService = createMockWalletService();
      const result = await walletService.generateWallet();

      expect(result.wallet.privateKey).toBeUndefined();
    });
  });

  describe('importWallet', () => {
    it('should import wallet from valid mnemonic', async () => {
      const walletService = createMockWalletService();
      const validMnemonic = bip39.generateMnemonic(128);
      
      const result = await walletService.importWallet(validMnemonic);

      expect(result.success).toBe(true);
      expect(result.wallet).toBeDefined();
      expect(result.wallet.address).toMatch(/^PG[a-f0-9]{38}$/);
      expect(result.wallet.imported).toBe(true);
    });

    it('should reject invalid mnemonic', async () => {
      const walletService = createMockWalletService();
      const invalidMnemonic = 'invalid mnemonic phrase with wrong words count';
      
      const result = await walletService.importWallet(invalidMnemonic);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('generateAddress', () => {
    it('should generate consistent addresses for same public key', () => {
      const walletService = createMockWalletService();
      const publicKey = Buffer.from('test-public-key');
      
      const address1 = walletService.generateAddress(publicKey);
      const address2 = walletService.generateAddress(publicKey);
      
      expect(address1).toBe(address2);
      expect(address1).toMatch(/^PG[a-f0-9]{38}$/);
    });
  });
});

// Mock modules for testing
jest.mock('electron-store', () => {
  return jest.fn().mockImplementation(() => ({
    get: jest.fn(() => []),
    set: jest.fn()
  }));
});

jest.mock('crypto-js', () => ({
  AES: {
    encrypt: jest.fn((text) => ({ toString: () => 'encrypted-' + text })),
    decrypt: jest.fn((encrypted) => ({ toString: () => encrypted.replace('encrypted-', '') }))
  },
  enc: {
    Utf8: {}
  }
}));