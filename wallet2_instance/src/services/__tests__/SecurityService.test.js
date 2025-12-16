import { SecurityService } from '../SecurityService';

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

// Mock speakeasy
jest.mock('speakeasy', () => ({
  generateSecret: jest.fn(() => ({
    base32: 'JBSWY3DPEHPK3PXP',
    otpauth_url: 'otpauth://totp/PlayerGold?secret=JBSWY3DPEHPK3PXP&issuer=PlayerGold'
  })),
  totp: {
    verify: jest.fn(() => true)
  }
}));

// Mock qrcode
jest.mock('qrcode', () => ({
  toDataURL: jest.fn(() => Promise.resolve('data:image/png;base64,mockqrcode'))
}));

describe('SecurityService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset the service state
    SecurityService.store.clear();
    SecurityService.activityStore.clear();
  });

  describe('PIN Management', () => {
    test('should setup PIN successfully', async () => {
      const result = await SecurityService.setupPIN('1234');
      
      expect(result.success).toBe(true);
      expect(SecurityService.store.set).toHaveBeenCalledWith('pin', expect.objectContaining({
        hash: expect.any(String),
        salt: expect.any(String),
        createdAt: expect.any(String),
        attempts: 0,
        lockedUntil: null
      }));
    });

    test('should reject invalid PIN length', async () => {
      const result = await SecurityService.setupPIN('12');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('PIN debe tener entre 4 y 6 dígitos');
    });

    test('should reject non-numeric PIN', async () => {
      const result = await SecurityService.setupPIN('12ab');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('PIN solo puede contener números');
    });

    test('should verify correct PIN', async () => {
      // First setup a PIN
      await SecurityService.setupPIN('1234');
      
      // Mock the stored PIN data
      const mockPinData = {
        hash: 'mockhash',
        salt: 'mocksalt',
        attempts: 0,
        lockedUntil: null
      };
      SecurityService.store.get.mockReturnValue(mockPinData);
      
      // Mock crypto.pbkdf2Sync to return the same hash
      const crypto = require('crypto');
      jest.spyOn(crypto, 'pbkdf2Sync').mockReturnValue(Buffer.from('mockhash', 'hex'));
      
      const result = await SecurityService.verifyPIN('1234');
      
      expect(result.success).toBe(true);
    });

    test('should increment attempts on wrong PIN', async () => {
      const mockPinData = {
        hash: 'correcthash',
        salt: 'mocksalt',
        attempts: 0,
        lockedUntil: null
      };
      SecurityService.store.get.mockReturnValue(mockPinData);
      
      // Mock crypto.pbkdf2Sync to return different hash
      const crypto = require('crypto');
      jest.spyOn(crypto, 'pbkdf2Sync').mockReturnValue(Buffer.from('wronghash', 'hex'));
      
      const result = await SecurityService.verifyPIN('9999');
      
      expect(result.success).toBe(false);
      expect(SecurityService.store.set).toHaveBeenCalledWith('pin', expect.objectContaining({
        attempts: 1
      }));
    });

    test('should lock wallet after 3 failed attempts', async () => {
      const mockPinData = {
        hash: 'correcthash',
        salt: 'mocksalt',
        attempts: 2, // Already 2 failed attempts
        lockedUntil: null
      };
      SecurityService.store.get.mockReturnValue(mockPinData);
      
      const crypto = require('crypto');
      jest.spyOn(crypto, 'pbkdf2Sync').mockReturnValue(Buffer.from('wronghash', 'hex'));
      
      const result = await SecurityService.verifyPIN('9999');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Demasiados intentos fallidos. Wallet bloqueado por 15 minutos.');
      expect(SecurityService.store.set).toHaveBeenCalledWith('pin', expect.objectContaining({
        attempts: 3,
        lockedUntil: expect.any(String)
      }));
    });
  });

  describe('2FA Management', () => {
    test('should setup 2FA successfully', async () => {
      const result = await SecurityService.setup2FA();
      
      expect(result.success).toBe(true);
      expect(result.secret).toBe('JBSWY3DPEHPK3PXP');
      expect(result.qrCode).toBe('data:image/png;base64,mockqrcode');
      expect(SecurityService.store.set).toHaveBeenCalledWith('2fa', expect.objectContaining({
        secret: expect.any(String),
        enabled: false,
        backupCodes: expect.any(Array),
        createdAt: expect.any(String)
      }));
    });

    test('should verify 2FA token and enable 2FA', async () => {
      const mock2FAData = {
        secret: 'encryptedsecret',
        enabled: false,
        backupCodes: ['CODE1', 'CODE2']
      };
      SecurityService.store.get.mockReturnValue(mock2FAData);
      
      // Mock CryptoJS decrypt
      const CryptoJS = require('crypto-js');
      jest.spyOn(CryptoJS.AES, 'decrypt').mockReturnValue({
        toString: jest.fn(() => 'JBSWY3DPEHPK3PXP')
      });
      
      const result = await SecurityService.verify2FA('123456');
      
      expect(result.success).toBe(true);
      expect(result.backupCodes).toEqual(['CODE1', 'CODE2']);
      expect(SecurityService.store.set).toHaveBeenCalledWith('2fa', expect.objectContaining({
        enabled: true,
        enabledAt: expect.any(String)
      }));
    });

    test('should authenticate with backup code', async () => {
      const mock2FAData = {
        secret: 'encryptedsecret',
        enabled: true,
        backupCodes: ['BACKUP1', 'BACKUP2']
      };
      SecurityService.store.get.mockReturnValue(mock2FAData);
      
      const result = await SecurityService.authenticate2FA('BACKUP1');
      
      expect(result.success).toBe(true);
      expect(result.usedBackupCode).toBe(true);
      expect(SecurityService.store.set).toHaveBeenCalledWith('2fa', expect.objectContaining({
        backupCodes: ['BACKUP2'] // BACKUP1 should be removed
      }));
    });
  });

  describe('Activity Logging', () => {
    test('should log security activity', () => {
      SecurityService.logActivity('PIN_VERIFIED', { test: 'data' });
      
      expect(SecurityService.activityStore.set).toHaveBeenCalledWith('activities', expect.arrayContaining([
        expect.objectContaining({
          id: expect.any(String),
          action: 'PIN_VERIFIED',
          timestamp: expect.any(String),
          details: { test: 'data' }
        })
      ]));
    });

    test('should limit activities to 1000 entries', () => {
      // Mock existing activities (1000 entries)
      const existingActivities = Array(1000).fill().map((_, i) => ({
        id: `id${i}`,
        action: 'TEST',
        timestamp: new Date().toISOString()
      }));
      SecurityService.activityStore.get.mockReturnValue(existingActivities);
      
      SecurityService.logActivity('NEW_ACTIVITY');
      
      expect(SecurityService.activityStore.set).toHaveBeenCalledWith('activities', 
        expect.arrayContaining([
          expect.objectContaining({ action: 'NEW_ACTIVITY' })
        ])
      );
      
      // Should have called set with exactly 1000 activities (removed oldest, added newest)
      const setCall = SecurityService.activityStore.set.mock.calls[0];
      expect(setCall[1]).toHaveLength(1000);
    });
  });

  describe('Suspicious Activity Detection', () => {
    test('should detect multiple failed PINs as suspicious', () => {
      const recentActivities = [
        { action: 'PIN_FAILED', timestamp: new Date().toISOString() },
        { action: 'PIN_FAILED', timestamp: new Date().toISOString() },
        { action: 'PIN_FAILED', timestamp: new Date().toISOString() },
        { action: 'PIN_FAILED', timestamp: new Date().toISOString() },
        { action: 'PIN_FAILED', timestamp: new Date().toISOString() }
      ];
      SecurityService.activityStore.get.mockReturnValue(recentActivities);
      
      const analysis = SecurityService.detectSuspiciousActivity();
      
      expect(analysis.isSuspicious).toBe(true);
      expect(analysis.patterns.multipleFailedPINs).toBe(5);
      expect(analysis.riskLevel).toBe('high');
    });

    test('should detect unusual timing as suspicious pattern', () => {
      // Mock current time to be 3 AM
      const mockDate = new Date();
      mockDate.setHours(3, 0, 0, 0);
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate);
      
      SecurityService.activityStore.get.mockReturnValue([]);
      
      const analysis = SecurityService.detectSuspiciousActivity();
      
      expect(analysis.patterns.unusualTiming).toBe(true);
      
      // Restore Date
      global.Date.mockRestore();
    });

    test('should calculate risk level correctly', () => {
      const patterns = {
        multipleFailedPINs: 3,
        multipleFailed2FA: 2,
        rapidTransactions: 5,
        unusualTiming: true
      };
      
      const riskLevel = SecurityService.calculateRiskLevel(patterns);
      
      // Score: 3 + 4 + 2 + 1 = 10 (high risk)
      expect(riskLevel).toBe('high');
    });
  });

  describe('Wallet Locking', () => {
    test('should lock wallet for suspicious activity', () => {
      const result = SecurityService.lockWallet(30);
      
      expect(result.success).toBe(true);
      expect(SecurityService.store.set).toHaveBeenCalledWith('walletLock', expect.objectContaining({
        lockedAt: expect.any(String),
        lockedUntil: expect.any(String),
        reason: 'suspicious_activity'
      }));
    });

    test('should check if wallet is locked', () => {
      const futureTime = new Date(Date.now() + 30 * 60 * 1000).toISOString();
      const lockData = {
        lockedAt: new Date().toISOString(),
        lockedUntil: futureTime,
        reason: 'suspicious_activity'
      };
      SecurityService.store.get.mockReturnValue(lockData);
      
      const lockStatus = SecurityService.isWalletLocked();
      
      expect(lockStatus.locked).toBe(true);
      expect(lockStatus.remainingMinutes).toBeGreaterThan(0);
    });

    test('should unlock expired wallet lock', () => {
      const pastTime = new Date(Date.now() - 30 * 60 * 1000).toISOString();
      const lockData = {
        lockedAt: new Date().toISOString(),
        lockedUntil: pastTime,
        reason: 'suspicious_activity'
      };
      SecurityService.store.get.mockReturnValue(lockData);
      
      const lockStatus = SecurityService.isWalletLocked();
      
      expect(lockStatus.locked).toBe(false);
      expect(SecurityService.store.delete).toHaveBeenCalledWith('walletLock');
    });
  });

  describe('Utility Functions', () => {
    test('should check if PIN is configured', () => {
      SecurityService.store.get.mockReturnValue({ hash: 'somehash' });
      
      const isConfigured = SecurityService.isPINConfigured();
      
      expect(isConfigured).toBe(true);
    });

    test('should check if 2FA is enabled', () => {
      SecurityService.store.get.mockReturnValue({ enabled: true });
      
      const isEnabled = SecurityService.is2FAEnabled();
      
      expect(isEnabled).toBe(true);
    });

    test('should generate backup codes', () => {
      const codes = SecurityService.generateBackupCodes();
      
      expect(codes).toHaveLength(10);
      codes.forEach(code => {
        expect(code).toMatch(/^[0-9A-F]{8}$/);
      });
    });

    test('should get recent activities', () => {
      const mockActivities = [
        { action: 'PIN_VERIFIED', timestamp: '2023-01-01T00:00:00.000Z' },
        { action: '2FA_VERIFIED', timestamp: '2023-01-01T00:01:00.000Z' }
      ];
      SecurityService.activityStore.get.mockReturnValue(mockActivities);
      
      const activities = SecurityService.getRecentActivities(10);
      
      expect(activities).toEqual(mockActivities.reverse()); // Should be reversed (newest first)
    });

    test('should clear security data', () => {
      const result = SecurityService.clearSecurityData();
      
      expect(result.success).toBe(true);
      expect(SecurityService.store.clear).toHaveBeenCalled();
      expect(SecurityService.activityStore.clear).toHaveBeenCalled();
    });
  });
});