import React, { useState, useEffect } from 'react';
import PrivacyService from '../services/PrivacyService';

const PrivacySettings = ({ wallet }) => {
  const [mixingSessions, setMixingSessions] = useState([]);
  const [showMixingForm, setShowMixingForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [privacyStats, setPrivacyStats] = useState({});
  
  const [mixingForm, setMixingForm] = useState({
    toAddress: '',
    amount: '',
    mixingLevel: 'medium'
  });

  const mixingLevels = [
    {
      value: 'low',
      label: 'Bajo',
      description: '2 direcciones intermedias, completado en ~6 minutos',
      feeMultiplier: '1.1x'
    },
    {
      value: 'medium',
      label: 'Medio',
      description: '4 direcciones intermedias, completado en ~20 minutos',
      feeMultiplier: '1.25x'
    },
    {
      value: 'high',
      label: 'Alto',
      description: '8 direcciones intermedias, completado en ~60 minutos',
      feeMultiplier: '1.5x'
    }
  ];

  useEffect(() => {
    loadMixingSessions();
    loadPrivacyStats();
  }, []);

  const loadMixingSessions = async () => {
    const result = await PrivacyService.getMixingSessions();
    if (result.success) {
      setMixingSessions(result.sessions);
    }
  };

  const loadPrivacyStats = () => {
    const stats = PrivacyService.getPrivacyStatistics();
    setPrivacyStats(stats);
  };

  const showMessage = (text, type = 'info') => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
  };

  const handleCreateMixedTransaction = async () => {
    if (!mixingForm.toAddress || !mixingForm.amount) {
      showMessage('Dirección de destino y cantidad son requeridas', 'error');
      return;
    }

    if (!wallet) {
      showMessage('No hay wallet seleccionado', 'error');
      return;
    }

    const amount = parseFloat(mixingForm.amount);
    if (isNaN(amount) || amount <= 0) {
      showMessage('Cantidad inválida', 'error');
      return;
    }

    setLoading(true);
    
    const transactionData = {
      fromAddress: wallet.address,
      toAddress: mixingForm.toAddress,
      amount: mixingForm.amount,
      privateKey: 'dummy-key', // This would come from wallet service
      mixingLevel: mixingForm.mixingLevel
    };

    const result = await PrivacyService.createMixedTransaction(transactionData);
    setLoading(false);

    if (result.success) {
      showMessage(
        `Transacción de mixing creada. Fee estimado: ${result.estimatedFee} PRGLD, Tiempo: ${result.estimatedTime} min`,
        'success'
      );
      setShowMixingForm(false);
      setMixingForm({ toAddress: '', amount: '', mixingLevel: 'medium' });
      loadMixingSessions();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleExecuteMixing = async (sessionId) => {
    if (!confirm('¿Ejecutar la transacción de mixing? Este proceso no se puede cancelar una vez iniciado.')) {
      return;
    }

    setLoading(true);
    const result = await PrivacyService.executeMixingTransaction(sessionId);
    setLoading(false);

    if (result.success) {
      showMessage('Transacción de mixing ejecutada exitosamente', 'success');
      loadMixingSessions();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleCancelMixing = async (sessionId) => {
    if (!confirm('¿Cancelar esta sesión de mixing?')) {
      return;
    }

    const result = await PrivacyService.cancelMixingSession(sessionId);
    
    if (result.success) {
      showMessage('Sesión de mixing cancelada', 'success');
      loadMixingSessions();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': '#ffc107',
      'executing': '#17a2b8',
      'completed': '#28a745',
      'failed': '#dc3545',
      'cancelled': '#6c757d'
    };
    return colors[status] || '#6c757d';
  };

  const getStatusLabel = (status) => {
    const labels = {
      'pending': 'Pendiente',
      'executing': 'Ejecutando',
      'completed': 'Completado',
      'failed': 'Fallido',
      'cancelled': 'Cancelado'
    };
    return labels[status] || status;
  };

  const formatAmount = (amount) => {
    return parseFloat(amount).toFixed(4);
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime || !endTime) return 'N/A';
    
    const duration = new Date(endTime) - new Date(startTime);
    const minutes = Math.round(duration / 1000 / 60);
    return `${minutes} min`;
  };

  return (
    <div className="privacy-settings">
      <div className="privacy-header">
        <h2>Configuración de Privacidad</h2>
        <p>Mejora la privacidad de tus transacciones con mixing opcional</p>
      </div>

      {message && (
        <div className={`message ${messageType}`}>
          {message}
        </div>
      )}

      {/* Privacy Overview */}
      <div className="privacy-overview">
        <h3>Estadísticas de Privacidad</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-value">{privacyStats.totalSessions || 0}</div>
            <div className="stat-label">Sesiones Totales</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{privacyStats.completedSessions || 0}</div>
            <div className="stat-label">Completadas</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{formatAmount(privacyStats.totalMixedAmount || 0)} PRGLD</div>
            <div className="stat-label">Cantidad Mezclada</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{privacyStats.averageMixingTime || 0} min</div>
            <div className="stat-label">Tiempo Promedio</div>
          </div>
        </div>
      </div>

      {/* Create New Mixed Transaction */}
      <div className="mixing-section">
        <div className="section-header">
          <h3>Transacciones Privadas</h3>
          <button 
            className="btn-primary"
            onClick={() => setShowMixingForm(true)}
            disabled={!wallet}
          >
            + Nueva Transacción Privada
          </button>
        </div>

        {!wallet && (
          <div className="warning">
            Selecciona un wallet para crear transacciones privadas
          </div>
        )}
      </div>

      {/* Mixing Sessions List */}
      <div className="mixing-sessions">
        <h3>Sesiones de Mixing</h3>
        {mixingSessions.length > 0 ? (
          <div className="sessions-list">
            {mixingSessions.map(session => (
              <div key={session.id} className="session-item">
                <div className="session-header">
                  <div className="session-info">
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(session.status) }}
                    >
                      {getStatusLabel(session.status)}
                    </span>
                    <span className="session-amount">
                      {formatAmount(session.originalTransaction.amount)} PRGLD
                    </span>
                    <span className="mixing-level">
                      Nivel: {session.mixingLevel}
                    </span>
                  </div>
                  <div className="session-actions">
                    {session.status === 'pending' && (
                      <>
                        <button
                          className="btn-action success"
                          onClick={() => handleExecuteMixing(session.id)}
                          disabled={loading}
                        >
                          ▶️ Ejecutar
                        </button>
                        <button
                          className="btn-action danger"
                          onClick={() => handleCancelMixing(session.id)}
                        >
                          ❌ Cancelar
                        </button>
                      </>
                    )}
                  </div>
                </div>
                
                <div className="session-details">
                  <div className="detail-row">
                    <span>Desde:</span>
                    <span className="address">{session.originalTransaction.from}</span>
                  </div>
                  <div className="detail-row">
                    <span>Hacia:</span>
                    <span className="address">{session.originalTransaction.to}</span>
                  </div>
                  <div className="detail-row">
                    <span>Fee de Mixing:</span>
                    <span>{formatAmount(session.mixingFee)} PRGLD</span>
                  </div>
                  <div className="detail-row">
                    <span>Creado:</span>
                    <span>{new Date(session.createdAt).toLocaleString()}</span>
                  </div>
                  
                  {session.status === 'executing' && session.progress && (
                    <div className="progress-bar">
                      <div 
                        className="progress-fill"
                        style={{ width: `${session.progress}%` }}
                      />
                      <span className="progress-text">{session.progress}%</span>
                    </div>
                  )}
                  
                  {session.status === 'completed' && (
                    <div className="detail-row">
                      <span>Duración:</span>
                      <span>{formatDuration(session.startedAt, session.completedAt)}</span>
                    </div>
                  )}
                  
                  {session.status === 'failed' && session.error && (
                    <div className="error-message">
                      Error: {session.error}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No hay sesiones de mixing</p>
            <p>Las transacciones privadas mejoran tu privacidad mediante mixing de tokens</p>
          </div>
        )}
      </div>

      {/* Create Mixing Transaction Modal */}
      {showMixingForm && (
        <div className="modal-overlay">
          <div className="modal large">
            <div className="modal-header">
              <h3>Crear Transacción Privada</h3>
              <button 
                className="close-btn"
                onClick={() => setShowMixingForm(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Dirección de Destino</label>
                <input
                  type="text"
                  value={mixingForm.toAddress}
                  onChange={(e) => setMixingForm({...mixingForm, toAddress: e.target.value})}
                  placeholder="PG..."
                />
              </div>
              
              <div className="form-group">
                <label>Cantidad (PRGLD)</label>
                <input
                  type="number"
                  step="0.0001"
                  value={mixingForm.amount}
                  onChange={(e) => setMixingForm({...mixingForm, amount: e.target.value})}
                  placeholder="0.0000"
                />
              </div>
              
              <div className="form-group">
                <label>Nivel de Privacidad</label>
                <div className="mixing-levels">
                  {mixingLevels.map(level => (
                    <div 
                      key={level.value}
                      className={`mixing-level ${mixingForm.mixingLevel === level.value ? 'selected' : ''}`}
                      onClick={() => setMixingForm({...mixingForm, mixingLevel: level.value})}
                    >
                      <div className="level-header">
                        <span className="level-name">{level.label}</span>
                        <span className="level-fee">Fee: {level.feeMultiplier}</span>
                      </div>
                      <div className="level-description">
                        {level.description}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="mixing-info">
                <h4>ℹ️ Información sobre Mixing</h4>
                <ul>
                  <li>El mixing mejora la privacidad dividiendo tu transacción en múltiples pasos</li>
                  <li>Los tokens pasan por direcciones intermedias antes de llegar al destino</li>
                  <li>Mayor nivel = más privacidad pero más tiempo y fees</li>
                  <li>El proceso no se puede cancelar una vez iniciado</li>
                </ul>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={() => setShowMixingForm(false)}
              >
                Cancelar
              </button>
              <button 
                className="btn-primary"
                onClick={handleCreateMixedTransaction}
                disabled={loading || !mixingForm.toAddress || !mixingForm.amount}
              >
                {loading ? 'Creando...' : 'Crear Transacción Privada'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrivacySettings;