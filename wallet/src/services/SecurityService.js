import crypto from 'crypto';
import Store from 'electron-store';
import CryptoJS from 'crypto-js';
import speakeasy from 'speakeasy';
import QRCode from 'qrcode';

class SecurityService {
  constructor() {
    this.store = new Store({
      name: 'playergold-security',
      encryptionKey: 'playergold-security-key'
    });
    this.activityStore = new Store({
      name: 'playergold-activity',
      encryptionKey: 'playergold-activity-key'
    });
  }

  /**
   * Set up PIN for wallet access
   * @param {string} pin - 4-6 digit PIN
   * @returns {Object} Setup result
   */
  async setupPIN(pin) {
    try {
      if (!pin || pin.length < 4 || pin.length > 6) {
        throw new Error('PIN debe tener entre 4 y 6 dígitos');
      }

      if (!/^\d+$/.test(pin)) {
        throw new Error('PIN solo puede contener números');
      }

      // Hash the PIN with salt
      const salt = crypto.randomBytes(32).toString('hex');
      const hashedPIN = crypto.pbkdf2Sync(pin, salt, 10000, 64, 'sha512').toString('hex');

      this.store.set('pin', {
        hash: hashedPIN,
        salt: salt,
        createdAt: new Date().toISOString(),
        attempts: 0,
        lockedUntil: null
      });

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Verify PIN for wallet access
   * @param {string} pin - PIN to verify
   * @returns {Object} Verification result
   */
  async verifyPIN(pin) {
    try {
      const pinData = this.store.get('pin');
      
      if (!pinData) {
        throw new Error('PIN no configurado');
      }

      // Check if wallet is locked
      if (pinData.lockedUntil && new Date() < new Date(pinData.lockedUntil)) {
        const lockTime = Math.ceil((new Date(pinData.lockedUntil) - new Date()) / 1000 / 60);
        throw new Error(`Wallet bloqueado por ${lockTime} minutos más`);
      }

      // Hash provided PIN
      const hashedPIN = crypto.pbkdf2Sync(pin, pinData.salt, 10000, 64, 'sha512').toString('hex');

      if (hashedPIN !== pinData.hash) {
        // Increment failed attempts
        const attempts = (pinData.attempts || 0) + 1;
        let lockedUntil = null;

        // Lock wallet after 3 failed attempts
        if (attempts >= 3) {
          lockedUntil = new Date(Date.now() + 15 * 60 * 1000).toISOString(); // 15 minutes
        }

        this.store.set('pin', {
          ...pinData,
          attempts: attempts,
          lockedUntil: lockedUntil
        });

        if (lockedUntil) {
          throw new Error('Demasiados intentos fallidos. Wallet bloqueado por 15 minutos.');
        } else {
          throw new Error(`PIN incorrecto. ${3 - attempts} intentos restantes.`);
        }
      }

      // Reset attempts on successful verification
      this.store.set('pin', {
        ...pinData,
        attempts: 0,
        lockedUntil: null,
        lastAccess: new Date().toISOString()
      });

      // Log successful access
      this.logActivity('PIN_VERIFIED', { timestamp: new Date().toISOString() });

      return { success: true };
    } catch (error) {
      // Log failed access attempt
      this.logActivity('PIN_FAILED', { 
        timestamp: new Date().toISOString(),
        error: error.message 
      });

      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Check if PIN is configured
   * @returns {boolean} PIN configuration status
   */
  isPINConfigured() {
    return !!this.store.get('pin');
  }

  /**
   * Setup 2FA (Two-Factor Authentication)
   * @param {string} appName - Application name for 2FA
   * @returns {Object} 2FA setup data including QR code
   */
  async setup2FA(appName = 'PlayerGold Wallet') {
    try {
      // Generate secret
      const secret = speakeasy.generateSecret({
        name: appName,
        issuer: 'PlayerGold'
      });

      // Generate QR code
      const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url);

      // Store secret (encrypted)
      const encryptedSecret = CryptoJS.AES.encrypt(secret.base32, 'playergold-2fa-key').toString();
      
      this.store.set('2fa', {
        secret: encryptedSecret,
        enabled: false,
        backupCodes: this.generateBackupCodes(),
        createdAt: new Date().toISOString()
      });

      return {
        success: true,
        secret: secret.base32,
        qrCode: qrCodeUrl,
        manualEntryKey: secret.base32
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Verify 2FA token and enable 2FA
   * @param {string} token - 6-digit token from authenticator app
   * @returns {Object} Verification result
   */
  async verify2FA(token) {
    try {
      const twoFAData = this.store.get('2fa');
      
      if (!twoFAData) {
        throw new Error('2FA no configurado');
      }

      // Decrypt secret
      const decryptedSecret = CryptoJS.AES.decrypt(twoFAData.secret, 'playergold-2fa-key').toString(CryptoJS.enc.Utf8);

      // Verify token
      const verified = speakeasy.totp.verify({
        secret: decryptedSecret,
        encoding: 'base32',
        token: token,
        window: 2 // Allow 2 time steps (60 seconds) tolerance
      });

      if (!verified) {
        throw new Error('Código 2FA inválido');
      }

      // Enable 2FA
      this.store.set('2fa', {
        ...twoFAData,
        enabled: true,
        enabledAt: new Date().toISOString()
      });

      this.logActivity('2FA_ENABLED', { timestamp: new Date().toISOString() });

      return { 
        success: true,
        backupCodes: twoFAData.backupCodes
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Verify 2FA token for authentication
   * @param {string} token - 6-digit token or backup code
   * @returns {Object} Verification result
   */
  async authenticate2FA(token) {
    try {
      const twoFAData = this.store.get('2fa');
      
      if (!twoFAData || !twoFAData.enabled) {
        return { success: true }; // 2FA not enabled
      }

      // Check if it's a backup code
      if (twoFAData.backupCodes && twoFAData.backupCodes.includes(token)) {
        // Remove used backup code
        const updatedBackupCodes = twoFAData.backupCodes.filter(code => code !== token);
        this.store.set('2fa', {
          ...twoFAData,
          backupCodes: updatedBackupCodes
        });

        this.logActivity('2FA_BACKUP_USED', { timestamp: new Date().toISOString() });
        return { success: true, usedBackupCode: true };
      }

      // Decrypt secret and verify TOTP
      const decryptedSecret = CryptoJS.AES.decrypt(twoFAData.secret, 'playergold-2fa-key').toString(CryptoJS.enc.Utf8);

      const verified = speakeasy.totp.verify({
        secret: decryptedSecret,
        encoding: 'base32',
        token: token,
        window: 2
      });

      if (!verified) {
        this.logActivity('2FA_FAILED', { timestamp: new Date().toISOString() });
        throw new Error('Código 2FA inválido');
      }

      this.logActivity('2FA_VERIFIED', { timestamp: new Date().toISOString() });
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Check if 2FA is enabled
   * @returns {boolean} 2FA status
   */
  is2FAEnabled() {
    const twoFAData = this.store.get('2fa');
    return twoFAData && twoFAData.enabled;
  }

  /**
   * Disable 2FA
   * @param {string} token - 2FA token for verification
   * @returns {Object} Disable result
   */
  async disable2FA(token) {
    try {
      const authResult = await this.authenticate2FA(token);
      
      if (!authResult.success) {
        throw new Error('Verificación 2FA fallida');
      }

      this.store.delete('2fa');
      this.logActivity('2FA_DISABLED', { timestamp: new Date().toISOString() });

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Generate backup codes for 2FA
   * @returns {Array} Array of backup codes
   */
  generateBackupCodes() {
    const codes = [];
    for (let i = 0; i < 10; i++) {
      codes.push(crypto.randomBytes(4).toString('hex').toUpperCase());
    }
    return codes;
  }

  /**
   * Log security activity
   * @param {string} action - Action type
   * @param {Object} details - Activity details
   */
  logActivity(action, details = {}) {
    const activities = this.activityStore.get('activities', []);
    
    activities.push({
      id: crypto.randomUUID(),
      action: action,
      timestamp: new Date().toISOString(),
      ip: this.getLocalIP(),
      userAgent: process.platform,
      details: details
    });

    // Keep only last 1000 activities
    if (activities.length > 1000) {
      activities.splice(0, activities.length - 1000);
    }

    this.activityStore.set('activities', activities);
  }

  /**
   * Detect suspicious activity
   * @returns {Object} Suspicious activity analysis
   */
  detectSuspiciousActivity() {
    const activities = this.activityStore.get('activities', []);
    const now = new Date();
    const oneHour = 60 * 60 * 1000;
    const recentActivities = activities.filter(
      activity => (now - new Date(activity.timestamp)) < oneHour
    );

    const suspiciousPatterns = {
      multipleFailedPINs: 0,
      multipleFailed2FA: 0,
      rapidTransactions: 0,
      unusualTiming: false
    };

    // Count failed attempts in last hour
    recentActivities.forEach(activity => {
      if (activity.action === 'PIN_FAILED') {
        suspiciousPatterns.multipleFailedPINs++;
      }
      if (activity.action === '2FA_FAILED') {
        suspiciousPatterns.multipleFailed2FA++;
      }
      if (activity.action === 'TRANSACTION_SENT') {
        suspiciousPatterns.rapidTransactions++;
      }
    });

    // Check for unusual timing (activity between 2 AM and 6 AM)
    const currentHour = now.getHours();
    if (currentHour >= 2 && currentHour <= 6) {
      suspiciousPatterns.unusualTiming = true;
    }

    const isSuspicious = 
      suspiciousPatterns.multipleFailedPINs >= 5 ||
      suspiciousPatterns.multipleFailed2FA >= 3 ||
      suspiciousPatterns.rapidTransactions >= 10;

    return {
      isSuspicious,
      patterns: suspiciousPatterns,
      riskLevel: this.calculateRiskLevel(suspiciousPatterns)
    };
  }

  /**
   * Calculate risk level based on suspicious patterns
   * @param {Object} patterns - Suspicious patterns
   * @returns {string} Risk level (low, medium, high)
   */
  calculateRiskLevel(patterns) {
    let score = 0;
    
    if (patterns.multipleFailedPINs >= 3) score += 3;
    if (patterns.multipleFailed2FA >= 2) score += 4;
    if (patterns.rapidTransactions >= 5) score += 2;
    if (patterns.unusualTiming) score += 1;

    if (score >= 6) return 'high';
    if (score >= 3) return 'medium';
    return 'low';
  }

  /**
   * Lock wallet temporarily due to suspicious activity
   * @param {number} minutes - Lock duration in minutes
   * @returns {Object} Lock result
   */
  lockWallet(minutes = 30) {
    const lockUntil = new Date(Date.now() + minutes * 60 * 1000).toISOString();
    
    this.store.set('walletLock', {
      lockedAt: new Date().toISOString(),
      lockedUntil: lockUntil,
      reason: 'suspicious_activity'
    });

    this.logActivity('WALLET_LOCKED', { 
      timestamp: new Date().toISOString(),
      duration: minutes,
      reason: 'suspicious_activity'
    });

    return { success: true, lockedUntil: lockUntil };
  }

  /**
   * Check if wallet is locked
   * @returns {Object} Lock status
   */
  isWalletLocked() {
    const lockData = this.store.get('walletLock');
    
    if (!lockData) {
      return { locked: false };
    }

    const now = new Date();
    const lockUntil = new Date(lockData.lockedUntil);

    if (now < lockUntil) {
      const remainingMinutes = Math.ceil((lockUntil - now) / 1000 / 60);
      return {
        locked: true,
        lockedUntil: lockData.lockedUntil,
        remainingMinutes: remainingMinutes,
        reason: lockData.reason
      };
    }

    // Lock expired, remove it
    this.store.delete('walletLock');
    return { locked: false };
  }

  /**
   * Unlock wallet manually (admin override)
   * @returns {Object} Unlock result
   */
  unlockWallet() {
    this.store.delete('walletLock');
    this.logActivity('WALLET_UNLOCKED', { timestamp: new Date().toISOString() });
    return { success: true };
  }

  /**
   * Get recent security activities
   * @param {number} limit - Number of activities to return
   * @returns {Array} Recent activities
   */
  getRecentActivities(limit = 50) {
    const activities = this.activityStore.get('activities', []);
    return activities.slice(-limit).reverse();
  }

  /**
   * Get local IP address (simplified)
   * @returns {string} Local IP
   */
  getLocalIP() {
    // Simplified IP detection for logging purposes
    return '127.0.0.1';
  }

  /**
   * Clear all security data (for testing/reset)
   * @returns {Object} Clear result
   */
  clearSecurityData() {
    this.store.clear();
    this.activityStore.clear();
    return { success: true };
  }
}

export const SecurityService = new SecurityService();