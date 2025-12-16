import React, { useState, useEffect } from 'react';
import SecurityService from '../services/SecurityService';

const SecuritySettings = () => {
  const [pinConfigured, setPinConfigured] = useState(false);
  const [twoFAEnabled, setTwoFAEnabled] = useState(false);
  const [showPinSetup, setShowPinSetup] = useState(false);
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [twoFACode, setTwoFACode] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [recentActivities, setRecentActivities] = useState([]);
  const [suspiciousActivity, setSuspiciousActivity] = useState(null);

  useEffect(() => {
    loadSecurityStatus();
    loadRecentActivities();
    checkSuspiciousActivity();
  }, []);

  const loadSecurityStatus = () => {
    setPinConfigured(SecurityService.isPINConfigured());
    setTwoFAEnabled(SecurityService.is2FAEnabled());
  };

  const loadRecentActivities = () => {
    const activities = SecurityService.getRecentActivities(10);
    setRecentActivities(activities);
  };

  const checkSuspiciousActivity = () => {
    const analysis = SecurityService.detectSuspiciousActivity();
    setSuspiciousActivity(analysis);
  };

  const showMessage = (text, type = 'info') => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
  };

  const handleSetupPIN = async () => {
    if (pin !== confirmPin) {
      showMessage('Los PINs no coinciden', 'error');
      return;
    }

    if (pin.length < 4 || pin.length > 6) {
      showMessage('El PIN debe tener entre 4 y 6 dígitos', 'error');
      return;
    }

    setLoading(true);
    const result = await SecurityService.setupPIN(pin);
    setLoading(false);

    if (result.success) {
      showMessage('PIN configurado exitosamente', 'success');
      setShowPinSetup(false);
      setPin('');
      setConfirmPin('');
      loadSecurityStatus();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleSetup2FA = async () => {
    setLoading(true);
    const result = await SecurityService.setup2FA();
    setLoading(false);

    if (result.success) {
      setQrCode(result.qrCode);
      setShow2FASetup(true);
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleVerify2FA = async () => {
    if (!twoFACode || twoFACode.length !== 6) {
      showMessage('Ingresa un código de 6 dígitos', 'error');
      return;
    }

    setLoading(true);
    const result = await SecurityService.verify2FA(twoFACode);
    setLoading(false);

    if (result.success) {
      showMessage('2FA habilitado exitosamente', 'success');
      setBackupCodes(result.backupCodes);
      setShow2FASetup(false);
      setTwoFACode('');
      loadSecurityStatus();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleDisable2FA = async () => {
    const code = prompt('Ingresa tu código 2FA para deshabilitar:');
    if (!code) return;

    setLoading(true);
    const result = await SecurityService.disable2FA(code);
    setLoading(false);

    if (result.success) {
      showMessage('2FA deshabilitado', 'success');
      loadSecurityStatus();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const getActivityIcon = (action) => {
    const icons = {
      'PIN_VERIFIED': '✅',
      'PIN_FAILED': '❌',
      '2FA_VERIFIED': '🔐',
      '2FA_FAILED': '🚫',
      '2FA_ENABLED': '🔒',
      '2FA_DISABLED': '🔓',
      'WALLET_LOCKED': '🔒',
      'WALLET_UNLOCKED': '🔓',
      'TRANSACTION_SENT': '💸'
    };
    return icons[action] || '📝';
  };

  const getActivityDescription = (action) => {
    const descriptions = {
      'PIN_VERIFIED': 'PIN verificado correctamente',
      'PIN_FAILED': 'Intento de PIN fallido',
      '2FA_VERIFIED': '2FA verificado correctamente',
      '2FA_FAILED': 'Código 2FA incorrecto',
      '2FA_ENABLED': '2FA habilitado',
      '2FA_DISABLED': '2FA deshabilitado',
      'WALLET_LOCKED': 'Wallet bloqueado por seguridad',
      'WALLET_UNLOCKED': 'Wallet desbloqueado',
      'TRANSACTION_SENT': 'Transacción enviada'
    };
    return descriptions[action] || action;
  };

  const getRiskLevelColor = (level) => {
    const colors = {
      'low': '#28a745',
      'medium': '#ffc107',
      'high': '#dc3545'
    };
    return colors[level] || '#6c757d';
  };

  return (
    <div className="security-settings">
      <div className="settings-header">
        <h2>Configuración de Seguridad</h2>
        <p>Protege tu wallet con autenticación adicional</p>
      </div>

      {message && (
        <div className={`message ${messageType}`}>
          {message}
        </div>
      )}

      {/* Security Status Overview */}
      <div className="security-overview">
        <h3>Estado de Seguridad</h3>
        <div className="security-items">
          <div className="security-item">
            <div className="item-info">
              <span className="icon">📱</span>
              <div>
                <h4>PIN de Acceso</h4>
                <p>Protege el acceso a tu wallet</p>
              </div>
            </div>
            <div className="item-status">
              {pinConfigured ? (
                <span className="status enabled">✅ Configurado</span>
              ) : (
                <button 
                  className="btn-setup"
                  onClick={() => setShowPinSetup(true)}
                >
                  Configurar PIN
                </button>
              )}
            </div>
          </div>

          <div className="security-item">
            <div className="item-info">
              <span className="icon">🔐</span>
              <div>
                <h4>Autenticación de Dos Factores (2FA)</h4>
                <p>Capa adicional de seguridad con app autenticadora</p>
              </div>
            </div>
            <div className="item-status">
              {twoFAEnabled ? (
                <div>
                  <span className="status enabled">✅ Habilitado</span>
                  <button 
                    className="btn-danger small"
                    onClick={handleDisable2FA}
                  >
                    Deshabilitar
                  </button>
                </div>
              ) : (
                <button 
                  className="btn-setup"
                  onClick={handleSetup2FA}
                >
                  Habilitar 2FA
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Suspicious Activity Alert */}
      {suspiciousActivity && suspiciousActivity.isSuspicious && (
        <div className="suspicious-activity-alert">
          <h3>⚠️ Actividad Sospechosa Detectada</h3>
          <div className="risk-level" style={{ color: getRiskLevelColor(suspiciousActivity.riskLevel) }}>
            Nivel de Riesgo: {suspiciousActivity.riskLevel.toUpperCase()}
          </div>
          <div className="patterns">
            {suspiciousActivity.patterns.multipleFailedPINs > 0 && (
              <p>• {suspiciousActivity.patterns.multipleFailedPINs} intentos de PIN fallidos</p>
            )}
            {suspiciousActivity.patterns.multipleFailed2FA > 0 && (
              <p>• {suspiciousActivity.patterns.multipleFailed2FA} códigos 2FA incorrectos</p>
            )}
            {suspiciousActivity.patterns.rapidTransactions > 0 && (
              <p>• {suspiciousActivity.patterns.rapidTransactions} transacciones rápidas</p>
            )}
            {suspiciousActivity.patterns.unusualTiming && (
              <p>• Actividad en horario inusual</p>
            )}
          </div>
        </div>
      )}

      {/* Recent Security Activities */}
      <div className="recent-activities">
        <h3>Actividad Reciente</h3>
        <div className="activities-list">
          {recentActivities.length > 0 ? (
            recentActivities.map((activity, index) => (
              <div key={index} className="activity-item">
                <span className="activity-icon">
                  {getActivityIcon(activity.action)}
                </span>
                <div className="activity-details">
                  <div className="activity-description">
                    {getActivityDescription(activity.action)}
                  </div>
                  <div className="activity-time">
                    {new Date(activity.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p>No hay actividad reciente</p>
          )}
        </div>
      </div>

      {/* PIN Setup Modal */}
      {showPinSetup && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Configurar PIN de Acceso</h3>
              <button 
                className="close-btn"
                onClick={() => setShowPinSetup(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>PIN (4-6 dígitos)</label>
                <input
                  type="password"
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  placeholder="Ingresa tu PIN"
                  maxLength="6"
                />
              </div>
              <div className="form-group">
                <label>Confirmar PIN</label>
                <input
                  type="password"
                  value={confirmPin}
                  onChange={(e) => setConfirmPin(e.target.value)}
                  placeholder="Confirma tu PIN"
                  maxLength="6"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setShowPinSetup(false)}
              >
                Cancelar
              </button>
              <button 
                className="btn-primary"
                onClick={handleSetupPIN}
                disabled={loading}
              >
                {loading ? 'Configurando...' : 'Configurar PIN'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2FA Setup Modal */}
      {show2FASetup && (
        <div className="modal-overlay">
          <div className="modal large">
            <div className="modal-header">
              <h3>Configurar Autenticación de Dos Factores</h3>
              <button 
                className="close-btn"
                onClick={() => setShow2FASetup(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="setup-steps">
                <div className="step">
                  <h4>1. Escanea el código QR</h4>
                  <p>Usa una app autenticadora como Google Authenticator o Authy</p>
                  {qrCode && (
                    <div className="qr-code">
                      <img src={qrCode} alt="QR Code para 2FA" />
                    </div>
                  )}
                </div>
                <div className="step">
                  <h4>2. Ingresa el código de verificación</h4>
                  <div className="form-group">
                    <input
                      type="text"
                      value={twoFACode}
                      onChange={(e) => setTwoFACode(e.target.value)}
                      placeholder="Código de 6 dígitos"
                      maxLength="6"
                    />
                  </div>
                </div>
              </div>
              
              {backupCodes.length > 0 && (
                <div className="backup-codes">
                  <h4>Códigos de Respaldo</h4>
                  <p>Guarda estos códigos en un lugar seguro. Puedes usarlos si pierdes acceso a tu app autenticadora.</p>
                  <div className="codes-grid">
                    {backupCodes.map((code, index) => (
                      <div key={index} className="backup-code">
                        {code}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setShow2FASetup(false)}
              >
                Cancelar
              </button>
              <button 
                className="btn-primary"
                onClick={handleVerify2FA}
                disabled={loading || twoFACode.length !== 6}
              >
                {loading ? 'Verificando...' : 'Verificar y Habilitar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SecuritySettings;