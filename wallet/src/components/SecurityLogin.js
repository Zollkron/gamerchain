import React, { useState, useEffect } from 'react';
import SecurityService from '../services/SecurityService';

const SecurityLogin = ({ onAuthenticated }) => {
  const [step, setStep] = useState('pin'); // 'pin', '2fa', 'locked'
  const [pin, setPin] = useState('');
  const [twoFACode, setTwoFACode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lockInfo, setLockInfo] = useState(null);
  const [showBackupCode, setShowBackupCode] = useState(false);

  useEffect(() => {
    checkInitialState();
  }, []);

  const checkInitialState = () => {
    // Check if wallet is locked
    const lockStatus = SecurityService.isWalletLocked();
    if (lockStatus.locked) {
      setLockInfo(lockStatus);
      setStep('locked');
      return;
    }

    // Check if PIN is configured
    if (!SecurityService.isPINConfigured()) {
      // No PIN configured, allow access
      onAuthenticated();
      return;
    }

    // Start with PIN verification
    setStep('pin');
  };

  const handlePINSubmit = async (e) => {
    e.preventDefault();
    
    if (!pin) {
      setError('Ingresa tu PIN');
      return;
    }

    setLoading(true);
    setError('');

    const result = await SecurityService.verifyPIN(pin);
    setLoading(false);

    if (result.success) {
      // PIN verified, check if 2FA is enabled
      if (SecurityService.is2FAEnabled()) {
        setStep('2fa');
        setPin(''); // Clear PIN for security
      } else {
        // No 2FA, authentication complete
        onAuthenticated();
      }
    } else {
      setError(result.error);
      setPin('');
      
      // Check if wallet got locked after failed attempt
      const lockStatus = SecurityService.isWalletLocked();
      if (lockStatus.locked) {
        setLockInfo(lockStatus);
        setStep('locked');
      }
    }
  };

  const handle2FASubmit = async (e) => {
    e.preventDefault();
    
    if (!twoFACode) {
      setError('Ingresa el código 2FA');
      return;
    }

    setLoading(true);
    setError('');

    const result = await SecurityService.authenticate2FA(twoFACode);
    setLoading(false);

    if (result.success) {
      // Authentication complete
      onAuthenticated();
      
      if (result.usedBackupCode) {
        alert('Has usado un código de respaldo. Considera regenerar tus códigos de respaldo.');
      }
    } else {
      setError(result.error);
      setTwoFACode('');
    }
  };

  const handleUnlock = () => {
    // In a real implementation, this might require admin privileges
    // For now, we'll just check if the lock has expired
    checkInitialState();
  };

  const formatTimeRemaining = (minutes) => {
    if (minutes < 60) {
      return `${minutes} minutos`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  if (step === 'locked') {
    return (
      <div className="security-login locked">
        <div className="lock-container">
          <div className="lock-icon">🔒</div>
          <h2>Wallet Bloqueado</h2>
          <p>Tu wallet ha sido bloqueado temporalmente por seguridad.</p>
          
          <div className="lock-details">
            <div className="lock-reason">
              Razón: {lockInfo?.reason === 'suspicious_activity' ? 'Actividad sospechosa detectada' : 'Múltiples intentos fallidos'}
            </div>
            <div className="lock-time">
              Tiempo restante: {formatTimeRemaining(lockInfo?.remainingMinutes || 0)}
            </div>
          </div>
          
          <div className="lock-actions">
            <button 
              className="btn-secondary"
              onClick={handleUnlock}
            >
              Verificar Estado
            </button>
          </div>
          
          <div className="lock-help">
            <p>Si crees que esto es un error, espera a que expire el bloqueo o contacta soporte.</p>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'pin') {
    return (
      <div className="security-login pin">
        <div className="login-container">
          <div className="login-header">
            <h2>Acceso Seguro</h2>
            <p>Ingresa tu PIN para acceder al wallet</p>
          </div>
          
          <form onSubmit={handlePINSubmit}>
            <div className="pin-input-container">
              <input
                type="password"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                placeholder="PIN"
                maxLength="6"
                className="pin-input"
                autoFocus
              />
            </div>
            
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
            
            <button 
              type="submit"
              className="btn-primary full-width"
              disabled={loading || !pin}
            >
              {loading ? 'Verificando...' : 'Acceder'}
            </button>
          </form>
          
          <div className="login-help">
            <p>¿Olvidaste tu PIN? Necesitarás restaurar tu wallet con la frase de recuperación.</p>
          </div>
        </div>
      </div>
    );
  }

  if (step === '2fa') {
    return (
      <div className="security-login twofa">
        <div className="login-container">
          <div className="login-header">
            <h2>Verificación 2FA</h2>
            <p>Ingresa el código de tu app autenticadora</p>
          </div>
          
          <form onSubmit={handle2FASubmit}>
            <div className="twofa-input-container">
              <input
                type="text"
                value={twoFACode}
                onChange={(e) => setTwoFACode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength="6"
                className="twofa-input"
                autoFocus
              />
            </div>
            
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
            
            <button 
              type="submit"
              className="btn-primary full-width"
              disabled={loading || twoFACode.length !== 6}
            >
              {loading ? 'Verificando...' : 'Verificar'}
            </button>
          </form>
          
          <div className="backup-code-section">
            <button 
              type="button"
              className="btn-link"
              onClick={() => setShowBackupCode(!showBackupCode)}
            >
              ¿No tienes acceso a tu app? Usar código de respaldo
            </button>
            
            {showBackupCode && (
              <div className="backup-code-input">
                <input
                  type="text"
                  value={twoFACode}
                  onChange={(e) => setTwoFACode(e.target.value.toUpperCase().slice(0, 8))}
                  placeholder="Código de respaldo"
                  maxLength="8"
                />
                <p className="backup-help">
                  Ingresa uno de tus códigos de respaldo de 8 caracteres
                </p>
              </div>
            )}
          </div>
          
          <div className="login-actions">
            <button 
              type="button"
              className="btn-secondary"
              onClick={() => setStep('pin')}
            >
              ← Volver al PIN
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default SecurityLogin;