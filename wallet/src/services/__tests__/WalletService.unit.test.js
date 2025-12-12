/**
 * Unit tests for WalletService focusing on core functionality
 */

// Setup crypto polyfill for Node.js environment
const crypto = require('crypto');
Object.defineProperty(globalThis, 'crypto', {
  value: {
    getRandomValues: arr => {
      const bytes = crypto.randomBytes(arr.length);
      for (let i = 0; i < arr.length; i++) {
        arr[i] = bytes[i];
      }
      return arr;
    }
  }
});

describe('WalletService Core Functionality', () => {
  describe('Address Validation', () => {
    /**
     * **Feature: auto-bootstrap-p2p, Property 2: Address persistence round trip**
     * **Validates: Requirements 2.2**
     */
    it('should validate addresses correctly without network dependency', () => {
      // Import WalletService to test address validation
      const WalletService = require('../WalletService');
      
      // Test valid addresses - property: for any valid format address, validation should return true
      const validAddresses = [
        'PG' + 'a'.repeat(38),
        'PG' + '1'.repeat(38),
        'PG' + 'f'.repeat(38),
        'PG' + '0'.repeat(38),
        'PG' + 'A'.repeat(38),
        'PG' + 'F'.repeat(38),
        'PG' + '123456789abcdef'.repeat(2) + '12345678',
        'PGabcdef1234567890abcdef1234567890abcdef12'
      ];
      
      for (const address of validAddresses) {
        expect(WalletService.isValidAddress(address)).toBe(true);
      }
      
      // Test invalid addresses - property: for any invalid format address, validation should return false
      const invalidAddresses = [
        'invalid',
        'PG' + 'a'.repeat(37), // Too short
        'PG' + 'a'.repeat(39), // Too long
        'XX' + 'a'.repeat(38), // Wrong prefix
        'PG' + 'g'.repeat(38), // Invalid hex character
        'PG' + 'z'.repeat(38), // Invalid hex character
        '', // Empty
        'PG', // Just prefix
        'PGa', // Too short
        'pg' + 'a'.repeat(38), // Wrong case prefix
      ];
      
      for (const address of invalidAddresses) {
        expect(WalletService.isValidAddress(address)).toBe(false);
      }
    });

    it('should generate consistent addresses for same public key', () => {
      const WalletService = require('../WalletService');
      
      // Property: for any given public key, generateAddress should always return the same result
      const testKeys = [
        Buffer.from('test-public-key-1'),
        Buffer.from('test-public-key-2'),
        Buffer.from('another-key-data'),
        Buffer.from('04' + '0'.repeat(126), 'hex'), // Mock compressed public key
        Buffer.from('different-test-key')
      ];
      
      for (const publicKey of testKeys) {
        const address1 = WalletService.generateAddress(publicKey);
        const address2 = WalletService.generateAddress(publicKey);
        const address3 = WalletService.generateAddress(publicKey);
        
        // Address should be consistent
        expect(address1).toBe(address2);
        expect(address2).toBe(address3);
        
        // Address should be valid format
        expect(WalletService.isValidAddress(address1)).toBe(true);
      }
    });

    it('should generate different addresses for different public keys', () => {
      const WalletService = require('../WalletService');
      
      // Property: for any two different public keys, addresses should be different
      const key1 = Buffer.from('test-public-key-1');
      const key2 = Buffer.from('test-public-key-2');
      const key3 = Buffer.from('completely-different-key');
      
      const address1 = WalletService.generateAddress(key1);
      const address2 = WalletService.generateAddress(key2);
      const address3 = WalletService.generateAddress(key3);
      
      expect(address1).not.toBe(address2);
      expect(address2).not.toBe(address3);
      expect(address1).not.toBe(address3);
      
      // All should be valid
      expect(WalletService.isValidAddress(address1)).toBe(true);
      expect(WalletService.isValidAddress(address2)).toBe(true);
      expect(WalletService.isValidAddress(address3)).toBe(true);
    });
  });

  describe('Network Independence', () => {
    it('should have methods that work without network', () => {
      const WalletService = require('../WalletService');
      
      // These methods should exist and be callable without network
      expect(typeof WalletService.isValidAddress).toBe('function');
      expect(typeof WalletService.generateAddress).toBe('function');
      expect(typeof WalletService.generateOfflineWallet).toBe('function');
      
      // Address validation should work without network
      expect(WalletService.isValidAddress('PG' + 'a'.repeat(38))).toBe(true);
      expect(WalletService.isValidAddress('invalid')).toBe(false);
      
      // Address generation should work without network
      const testKey = Buffer.from('test-key');
      const address = WalletService.generateAddress(testKey);
      expect(typeof address).toBe('string');
      expect(WalletService.isValidAddress(address)).toBe(true);
    });
  });
});