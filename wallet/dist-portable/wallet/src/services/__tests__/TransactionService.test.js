const { TransactionService } = require('../TransactionService');

// Mock NetworkService
jest.mock('../NetworkService', () => ({
  NetworkService: {
    getBalance: jest.fn(),
    estimateFee: jest.fn(),
    sendTransaction: jest.fn(),
    getTransactionHistory: jest.fn(),
    getTransaction: jest.fn(),
    on: jest.fn(),
    off: jest.fn()
  }
}));

const { NetworkService } = require('../NetworkService');

describe('TransactionService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('validateTransactionInputs', () => {
    test('should validate correct transaction inputs', () => {
      const params = {
        fromAddress: 'PG1234567890abcdef1234567890abcdef12345678',
        toAddress: 'PGabcdef1234567890abcdef1234567890abcdef12',
        amount: '10.5',
        privateKey: 'test-private-key'
      };

      const result = TransactionService.validateTransactionInputs(params);
      expect(result.valid).toBe(true);
    });

    test('should reject missing parameters', () => {
      const params = {
        fromAddress: 'PG1234567890abcdef1234567890abcdef12345678',
        toAddress: '',
        amount: '10.5',
        privateKey: 'test-private-key'
      };

      const result = TransactionService.validateTransactionInputs(params);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Missing required');
    });

    test('should reject same from and to addresses', () => {
      const address = 'PG1234567890abcdef1234567890abcdef12345678';
      const params = {
        fromAddress: address,
        toAddress: address,
        amount: '10.5',
        privateKey: 'test-private-key'
      };

      const result = TransactionService.validateTransactionInputs(params);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Cannot send to the same address');
    });

    test('should reject invalid amount', () => {
      const params = {
        fromAddress: 'PG1234567890abcdef1234567890abcdef12345678',
        toAddress: 'PGabcdef1234567890abcdef1234567890abcdef12',
        amount: '-5',
        privateKey: 'test-private-key'
      };

      const result = TransactionService.validateTransactionInputs(params);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid amount');
    });

    test('should reject invalid address format', () => {
      const params = {
        fromAddress: 'invalid-address',
        toAddress: 'PGabcdef1234567890abcdef1234567890abcdef12',
        amount: '10.5',
        privateKey: 'test-private-key'
      };

      const result = TransactionService.validateTransactionInputs(params);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid address format');
    });
  });

  describe('isValidAddress', () => {
    test('should validate correct PlayerGold address', () => {
      const address = 'PG1234567890abcdef1234567890abcdef12345678';
      expect(TransactionService.isValidAddress(address)).toBe(true);
    });

    test('should reject address without PG prefix', () => {
      const address = '1234567890abcdef1234567890abcdef12345678ab';
      expect(TransactionService.isValidAddress(address)).toBe(false);
    });

    test('should reject address with wrong length', () => {
      const address = 'PG1234567890abcdef';
      expect(TransactionService.isValidAddress(address)).toBe(false);
    });

    test('should reject address with invalid characters', () => {
      const address = 'PG1234567890abcdef1234567890abcdef1234567g';
      expect(TransactionService.isValidAddress(address)).toBe(false);
    });
  });

  describe('sendTransaction', () => {
    test('should send transaction successfully', async () => {
      const params = {
        fromAddress: 'PG1234567890abcdef1234567890abcdef12345678',
        toAddress: 'PGabcdef1234567890abcdef1234567890abcdef12',
        amount: '10.5',
        privateKey: 'test-private-key'
      };

      // Mock network responses
      NetworkService.getBalance.mockResolvedValue({
        success: true,
        balance: '100.0'
      });

      NetworkService.estimateFee.mockResolvedValue({
        success: true,
        fee: '0.01'
      });

      NetworkService.sendTransaction.mockResolvedValue({
        success: true,
        transactionHash: 'test-hash-123',
        estimatedConfirmationTime: 30
      });

      const result = await TransactionService.sendTransaction(params);

      expect(result.success).toBe(true);
      expect(result.transactionHash).toBe('test-hash-123');
      expect(NetworkService.getBalance).toHaveBeenCalledWith(params.fromAddress);
      expect(NetworkService.estimateFee).toHaveBeenCalled();
      expect(NetworkService.sendTransaction).toHaveBeenCalled();
    });

    test('should fail with insufficient balance', async () => {
      const params = {
        fromAddress: 'PG1234567890abcdef1234567890abcdef12345678',
        toAddress: 'PGabcdef1234567890abcdef1234567890abcdef12',
        amount: '10.5',
        privateKey: 'test-private-key'
      };

      NetworkService.getBalance.mockResolvedValue({
        success: true,
        balance: '5.0'
      });

      NetworkService.estimateFee.mockResolvedValue({
        success: true,
        fee: '0.01'
      });

      const result = await TransactionService.sendTransaction(params);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Insufficient balance');
    });

    test('should fail when balance check fails', async () => {
      const params = {
        fromAddress: 'PG1234567890abcdef1234567890abcdef12345678',
        toAddress: 'PGabcdef1234567890abcdef1234567890abcdef12',
        amount: '10.5',
        privateKey: 'test-private-key'
      };

      NetworkService.getBalance.mockResolvedValue({
        success: false,
        error: 'Network error'
      });

      const result = await TransactionService.sendTransaction(params);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Failed to verify balance');
    });
  });

  describe('calculateTransactionHash', () => {
    test('should calculate consistent hash for same transaction', () => {
      const transaction = {
        from_address: 'PG1234567890abcdef1234567890abcdef12345678',
        to_address: 'PGabcdef1234567890abcdef1234567890abcdef12',
        amount: '10.5',
        fee: '0.01',
        timestamp: 1234567890,
        transaction_type: 'transfer',
        nonce: 12345
      };

      const hash1 = TransactionService.calculateTransactionHash(transaction);
      const hash2 = TransactionService.calculateTransactionHash(transaction);

      expect(hash1).toBe(hash2);
      expect(hash1).toMatch(/^[a-f0-9]{64}$/); // SHA-256 hex format
    });

    test('should calculate different hash for different transactions', () => {
      const transaction1 = {
        from_address: 'PG1234567890abcdef1234567890abcdef12345678',
        to_address: 'PGabcdef1234567890abcdef1234567890abcdef12',
        amount: '10.5',
        fee: '0.01',
        timestamp: 1234567890,
        transaction_type: 'transfer',
        nonce: 12345
      };

      const transaction2 = {
        ...transaction1,
        amount: '20.5'
      };

      const hash1 = TransactionService.calculateTransactionHash(transaction1);
      const hash2 = TransactionService.calculateTransactionHash(transaction2);

      expect(hash1).not.toBe(hash2);
    });
  });

  describe('formatAmount', () => {
    test('should format amounts correctly', () => {
      expect(TransactionService.formatAmount('1234.56789')).toBe('1,234.56789000');
      expect(TransactionService.formatAmount('0.00000001')).toBe('0.00000001');
      expect(TransactionService.formatAmount('1000000')).toBe('1,000,000.00000000');
      expect(TransactionService.formatAmount('invalid')).toBe('0.00');
    });
  });

  describe('getTransactionStatusText', () => {
    test('should return correct status text', () => {
      expect(TransactionService.getTransactionStatusText({ status: 'pending' })).toBe('Pendiente');
      expect(TransactionService.getTransactionStatusText({ status: 'confirmed' })).toBe('Confirmada');
      expect(TransactionService.getTransactionStatusText({ status: 'failed' })).toBe('Fallida');
      expect(TransactionService.getTransactionStatusText({ status: 'unknown' })).toBe('Desconocido');
    });
  });

  describe('getTransactionHistory', () => {
    test('should fetch and cache transaction history', async () => {
      const address = 'PG1234567890abcdef1234567890abcdef12345678';
      const mockTransactions = [
        {
          hash: 'tx1',
          from_address: address,
          to_address: 'PGother',
          amount: '10.0',
          timestamp: 1234567890
        }
      ];

      NetworkService.getTransactionHistory.mockResolvedValue({
        success: true,
        transactions: mockTransactions,
        total: 1,
        hasMore: false
      });

      const result = await TransactionService.getTransactionHistory(address, 10, 0);

      expect(result.success).toBe(true);
      expect(result.transactions).toEqual(mockTransactions);
      expect(NetworkService.getTransactionHistory).toHaveBeenCalledWith(address, 10, 0);
    });
  });
});