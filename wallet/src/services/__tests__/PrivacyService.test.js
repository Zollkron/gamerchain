import { PrivacyService } from '../PrivacyService';

// Mock electron-store
jest.mock('electron-store', () => {
  const mockStore = {
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
    clear: jest.fn()
  };
  
  return jest.fn(() => mockStore);
});

// Mock NetworkService
jest.mock('../NetworkService', () => ({
  NetworkService: {
    sendTransaction: jest.fn(() => Promise.resolve({ 
      success: true, 
      transactionHash: 'mock-hash' 
    }))
  }
}));

describe('PrivacyService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    PrivacyService.store.clear();
  });

  describe('Mixed Transaction Creation', () => {
    test('should create mixed transaction successfully', async () => {
      PrivacyService.store.get.mockReturnValue([]);
      
      const transactionData = {
        fromAddress: 'PG1111111111111111111111111111111111111111',
        toAddress: 'PG2222222222222222222222222222222222222222',
        amount: '10.0',
        privateKey: 'mock-private-key',
        mixingLevel: 'medium'
      };
      
      const result = await PrivacyService.createMixedTransaction(transactionData);
      
      expect(result.success).toBe(true);
      expect(result.mixingSession).toMatchObject({
        id: expect.any(String),
        originalTransaction: {
          from: transactionData.fromAddress,
          to: transactionData.toAddress,
          amount: transactionData.amount
        },
        mixingLevel: 'medium',
        status: 'pending',
        createdAt: expect.any(String)
      });
      
      expect(PrivacyService.store.set).toHaveBeenCalledWith('mixingSessions', 
        expect.arrayContaining([result.mixingSession])
      );
    });

    test('should reject invalid mixing level', async () => {
      const transactionData = {
        fromAddress: 'PG1111111111111111111111111111111111111111',
        toAddress: 'PG2222222222222222222222222222222222222222',
        amount: '10.0',
        privateKey: 'mock-private-key',
        mixingLevel: 'invalid'
      };
      
      const result = await PrivacyService.createMixedTransaction(transactionData);
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Nivel de mixing inválido');
    });

    test('should calculate mixing fee correctly for different levels', () => {
      const amount = '100.0';
      
      const lowFee = PrivacyService.calculateMixingFee(amount, 'low');
      const mediumFee = PrivacyService.calculateMixingFee(amount, 'medium');
      const highFee = PrivacyService.calculateMixingFee(amount, 'high');
      
      expect(lowFee).toBe(0.11); // 100 * 0.001 * 1.1
      expect(mediumFee).toBe(0.125); // 100 * 0.001 * 1.25
      expect(highFee).toBe(0.15); // 100 * 0.001 * 1.5
    });

    test('should enforce minimum fee', () => {
      const smallAmount = '0.001';
      
      const fee = PrivacyService.calculateMixingFee(smallAmount, 'low');
      
      expect(fee).toBe(0.01); // Minimum fee
    });
  });

  describe('Mixing Parameters', () => {
    test('should return correct parameters for each level', () => {
      const lowParams = PrivacyService.getMixingParameters('low');
      const mediumParams = PrivacyService.getMixingParameters('medium');
      const highParams = PrivacyService.getMixingParameters('high');
      
      expect(lowParams).toEqual({
        intermediateCount: 2,
        delayRange: [1, 3],
        feeMultiplier: 1.1
      });
      
      expect(mediumParams).toEqual({
        intermediateCount: 4,
        delayRange: [2, 8],
        feeMultiplier: 1.25
      });
      
      expect(highParams).toEqual({
        intermediateCount: 8,
        delayRange: [5, 15],
        feeMultiplier: 1.5
      });
    });
  });

  describe('Intermediate Address Generation', () => {
    test('should generate correct number of intermediate addresses', async () => {
      const addresses = await PrivacyService.generateIntermediateAddresses(3);
      
      expect(addresses).toHaveLength(3);
      addresses.forEach(addr => {
        expect(addr).toMatchObject({
          address: expect.stringMatching(/^PG[0-9a-f]{38}$/),
          privateKey: expect.any(String),
          temporary: true
        });
      });
    });
  });

  describe('Amount Splitting', () => {
    test('should split amount into correct number of chunks', () => {
      const totalAmount = 100;
      const chunkCount = 4;
      
      const chunks = PrivacyService.splitAmountRandomly(totalAmount, chunkCount);
      
      expect(chunks).toHaveLength(chunkCount);
      
      // Sum should equal original amount (with small floating point tolerance)
      const sum = chunks.reduce((acc, chunk) => acc + chunk, 0);
      expect(Math.abs(sum - totalAmount)).toBeLessThan(0.0001);
      
      // Each chunk should be positive
      chunks.forEach(chunk => {
        expect(chunk).toBeGreaterThan(0);
      });
    });
  });

  describe('Mixing Chain Creation', () => {
    test('should create proper mixing chain', async () => {
      const params = {
        fromAddress: 'PG1111111111111111111111111111111111111111',
        toAddress: 'PG9999999999999999999999999999999999999999',
        amount: 100,
        intermediateAddresses: [
          { address: 'PG2222222222222222222222222222222222222222', privateKey: 'key1' },
          { address: 'PG3333333333333333333333333333333333333333', privateKey: 'key2' }
        ],
        mixingParams: {
          delayRange: [1, 3],
          intermediateCount: 2
        },
        privateKey: 'original-key'
      };
      
      const chain = await PrivacyService.createMixingChain(params);
      
      // Should have transactions for: split (2) + shuffle (1) + final (1) = 4
      expect(chain.length).toBeGreaterThan(0);
      
      // First transactions should be splits from original address
      const splitTransactions = chain.filter(tx => tx.transactionType === 'mixing_split');
      expect(splitTransactions.length).toBe(2);
      splitTransactions.forEach(tx => {
        expect(tx.fromAddress).toBe(params.fromAddress);
        expect(tx.privateKey).toBe(params.privateKey);
      });
      
      // Should have final transaction to destination
      const finalTransaction = chain.find(tx => tx.transactionType === 'mixing_final');
      expect(finalTransaction).toBeDefined();
      expect(finalTransaction.toAddress).toBe(params.toAddress);
    });
  });

  describe('Mixing Execution', () => {
    test('should execute mixing transaction successfully', async () => {
      const mockSession = {
        id: 'test-session',
        status: 'pending',
        mixingChain: [
          {
            fromAddress: 'PG1111111111111111111111111111111111111111',
            toAddress: 'PG2222222222222222222222222222222222222222',
            amount: '50.0',
            privateKey: 'key1',
            transactionType: 'mixing_split'
          }
        ]
      };
      
      PrivacyService.store.get.mockReturnValue([mockSession]);
      
      const result = await PrivacyService.executeMixingTransaction('test-session');
      
      expect(result.success).toBe(true);
      expect(result.transactionHashes).toEqual(['mock-hash']);
      
      // Should update session status to completed
      expect(PrivacyService.store.set).toHaveBeenCalledWith('mixingSessions', 
        expect.arrayContaining([
          expect.objectContaining({
            id: 'test-session',
            status: 'completed',
            completedAt: expect.any(String)
          })
        ])
      );
    });

    test('should handle transaction failure during execution', async () => {
      const { NetworkService } = require('../NetworkService');
      NetworkService.sendTransaction.mockResolvedValueOnce({ 
        success: false, 
        error: 'Transaction failed' 
      });
      
      const mockSession = {
        id: 'test-session',
        status: 'pending',
        mixingChain: [
          {
            fromAddress: 'PG1111111111111111111111111111111111111111',
            toAddress: 'PG2222222222222222222222222222222222222222',
            amount: '50.0',
            privateKey: 'key1'
          }
        ]
      };
      
      PrivacyService.store.get.mockReturnValue([mockSession]);
      
      const result = await PrivacyService.executeMixingTransaction('test-session');
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('Transacción de mixing falló');
      
      // Should mark session as failed
      expect(PrivacyService.store.set).toHaveBeenCalledWith('mixingSessions', 
        expect.arrayContaining([
          expect.objectContaining({
            id: 'test-session',
            status: 'failed',
            error: 'Transaction failed'
          })
        ])
      );
    });

    test('should reject execution of non-pending session', async () => {
      const mockSession = {
        id: 'test-session',
        status: 'completed', // Not pending
        mixingChain: []
      };
      
      PrivacyService.store.get.mockReturnValue([mockSession]);
      
      const result = await PrivacyService.executeMixingTransaction('test-session');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('La sesión ya fue procesada');
    });
  });

  describe('Session Management', () => {
    test('should get mixing session status', async () => {
      const mockSession = {
        id: 'test-session',
        status: 'pending',
        originalTransaction: { amount: '100.0' }
      };
      
      PrivacyService.store.get.mockReturnValue([mockSession]);
      
      const result = await PrivacyService.getMixingSessionStatus('test-session');
      
      expect(result.success).toBe(true);
      expect(result.session).toEqual(mockSession);
    });

    test('should get all mixing sessions', async () => {
      const mockSessions = [
        { id: '1', status: 'completed', createdAt: '2023-01-02T00:00:00.000Z' },
        { id: '2', status: 'pending', createdAt: '2023-01-01T00:00:00.000Z' }
      ];
      
      PrivacyService.store.get.mockReturnValue(mockSessions);
      
      const result = await PrivacyService.getMixingSessions();
      
      expect(result.success).toBe(true);
      // Should be sorted by creation date (newest first)
      expect(result.sessions[0].id).toBe('1');
      expect(result.sessions[1].id).toBe('2');
    });

    test('should filter sessions by status', async () => {
      const mockSessions = [
        { id: '1', status: 'completed' },
        { id: '2', status: 'pending' },
        { id: '3', status: 'completed' }
      ];
      
      PrivacyService.store.get.mockReturnValue(mockSessions);
      
      const result = await PrivacyService.getMixingSessions('completed');
      
      expect(result.success).toBe(true);
      expect(result.sessions).toHaveLength(2);
      expect(result.sessions.every(s => s.status === 'completed')).toBe(true);
    });

    test('should cancel pending mixing session', async () => {
      const mockSessions = [{
        id: 'test-session',
        status: 'pending'
      }];
      
      PrivacyService.store.get.mockReturnValue(mockSessions);
      
      const result = await PrivacyService.cancelMixingSession('test-session');
      
      expect(result.success).toBe(true);
      expect(PrivacyService.store.set).toHaveBeenCalledWith('mixingSessions', 
        expect.arrayContaining([
          expect.objectContaining({
            id: 'test-session',
            status: 'cancelled',
            cancelledAt: expect.any(String)
          })
        ])
      );
    });

    test('should reject cancelling non-pending session', async () => {
      const mockSessions = [{
        id: 'test-session',
        status: 'executing'
      }];
      
      PrivacyService.store.get.mockReturnValue(mockSessions);
      
      const result = await PrivacyService.cancelMixingSession('test-session');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Solo se pueden cancelar sesiones pendientes');
    });
  });

  describe('Time Estimation', () => {
    test('should estimate completion time correctly', () => {
      const lowTime = PrivacyService.estimateCompletionTime('low');
      const mediumTime = PrivacyService.estimateCompletionTime('medium');
      const highTime = PrivacyService.estimateCompletionTime('high');
      
      // Low: 2 intermediate * 2 + 1 = 5 transactions, avg delay 2 minutes
      expect(lowTime).toBe(10); // 5 * 2
      
      // Medium: 4 intermediate * 2 + 1 = 9 transactions, avg delay 5 minutes
      expect(mediumTime).toBe(45); // 9 * 5
      
      // High: 8 intermediate * 2 + 1 = 17 transactions, avg delay 10 minutes
      expect(highTime).toBe(170); // 17 * 10
    });
  });

  describe('Privacy Statistics', () => {
    test('should calculate privacy statistics correctly', () => {
      const mockSessions = [
        {
          status: 'completed',
          originalTransaction: { amount: '100.0' },
          startedAt: '2023-01-01T00:00:00.000Z',
          completedAt: '2023-01-01T00:30:00.000Z'
        },
        {
          status: 'completed',
          originalTransaction: { amount: '50.0' },
          startedAt: '2023-01-01T01:00:00.000Z',
          completedAt: '2023-01-01T01:15:00.000Z'
        },
        {
          status: 'pending',
          originalTransaction: { amount: '25.0' }
        },
        {
          status: 'failed',
          originalTransaction: { amount: '75.0' }
        }
      ];
      
      PrivacyService.store.get.mockReturnValue(mockSessions);
      
      const stats = PrivacyService.getPrivacyStatistics();
      
      expect(stats.totalSessions).toBe(4);
      expect(stats.completedSessions).toBe(2);
      expect(stats.pendingSessions).toBe(1);
      expect(stats.failedSessions).toBe(1);
      expect(stats.totalMixedAmount).toBe(150.0); // 100 + 50
      expect(stats.averageMixingTime).toBe(22); // (30 + 15) / 2 minutes
    });
  });

  describe('Cleanup', () => {
    test('should cleanup old sessions', () => {
      const now = new Date();
      const oldDate = new Date(now.getTime() - 35 * 24 * 60 * 60 * 1000); // 35 days ago
      const recentDate = new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000); // 10 days ago
      
      const mockSessions = [
        { id: '1', createdAt: oldDate.toISOString() }, // Should be removed
        { id: '2', createdAt: recentDate.toISOString() }, // Should be kept
        { id: '3', createdAt: now.toISOString() } // Should be kept
      ];
      
      PrivacyService.store.get.mockReturnValue(mockSessions);
      
      const result = PrivacyService.cleanupOldSessions();
      
      expect(result.success).toBe(true);
      expect(result.removedSessions).toBe(1);
      
      expect(PrivacyService.store.set).toHaveBeenCalledWith('mixingSessions', 
        expect.arrayContaining([
          expect.objectContaining({ id: '2' }),
          expect.objectContaining({ id: '3' })
        ])
      );
    });
  });

  describe('Address Generation', () => {
    test('should generate valid PlayerGold address from private key', () => {
      const privateKey = Buffer.from('test-private-key');
      
      const address = PrivacyService.generateAddressFromPrivateKey(privateKey);
      
      expect(address).toMatch(/^PG[0-9a-f]{38}$/);
    });
  });
});