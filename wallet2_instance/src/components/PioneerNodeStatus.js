import React, { useState, useEffect } from 'react';
import './PioneerNodeStatus.css';

const PioneerNodeStatus = () => {
  const [pioneerStatus, setPioneerStatus] = useState({
    isPioneer: false,
    isRegistered: false,
    waitingForSecondPioneer: false,
    networkMap: null,
    coordinatorConnected: false,
    lastUpdate: null,
    error: null
  });

  const [validationStatus, setValidationStatus] = useState({
    isValidated: false,
    canOperate: false,
    hasNetworkMap: false,
    activeNodes: 0,
    genesisNodes: 0
  });

  useEffect(() => {
    // Get initial network validation status
    const checkValidationStatus = async () => {
      try {
        const result = await window.electronAPI.getNetworkValidationStatus();
        if (result.success) {
          setValidationStatus(result.status);
          
          // Check if this is a pioneer node
          if (result.validationResult && result.validationResult.isPioneer) {
            setPioneerStatus(prev => ({
              ...prev,
              isPioneer: true,
              coordinatorConnected: true,
              networkMap: result.validationResult.networkMap,
              lastUpdate: new Date().toISOString()
            }));
          }
        }
      } catch (error) {
        console.error('Error checking validation status:', error);
        setPioneerStatus(prev => ({
          ...prev,
          error: error.message
        }));
      }
    };

    checkValidationStatus();

    // Set up periodic status updates
    const interval = setInterval(checkValidationStatus, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleRefreshStatus = async () => {
    try {
      const result = await window.electronAPI.refreshNetworkValidation();
      if (result.success) {
        console.log('Network validation refreshed successfully');
        // Trigger status update
        const statusResult = await window.electronAPI.getNetworkValidationStatus();
        if (statusResult.success) {
          setValidationStatus(statusResult.status);
        }
      } else {
        setPioneerStatus(prev => ({
          ...prev,
          error: result.error || 'Failed to refresh network validation'
        }));
      }
    } catch (error) {
      console.error('Error refreshing status:', error);
      setPioneerStatus(prev => ({
        ...prev,
        error: error.message
      }));
    }
  };

  const handleForceRevalidation = async () => {
    try {
      const result = await window.electronAPI.forceNetworkRevalidation();
      if (result.success) {
        console.log('Network revalidation completed successfully');
        // Update status
        const statusResult = await window.electronAPI.getNetworkValidationStatus();
        if (statusResult.success) {
          setValidationStatus(statusResult.status);
        }
      } else {
        setPioneerStatus(prev => ({
          ...prev,
          error: result.error || 'Network revalidation failed'
        }));
      }
    } catch (error) {
      console.error('Error forcing revalidation:', error);
      setPioneerStatus(prev => ({
        ...prev,
        error: error.message
      }));
    }
  };

  const getStatusIcon = () => {
    if (pioneerStatus.error) return '❌';
    if (!validationStatus.isValidated) return '🔄';
    if (pioneerStatus.isPioneer && validationStatus.activeNodes < 2) return '🚀';
    if (pioneerStatus.isPioneer && validationStatus.activeNodes >= 2) return '🌐';
    return '✅';
  };

  const getStatusMessage = () => {
    if (pioneerStatus.error) {
      return `Error: ${pioneerStatus.error}`;
    }
    
    if (!validationStatus.isValidated) {
      return 'Validando conexión con coordinador...';
    }
    
    if (!validationStatus.canOperate) {
      return 'No se puede operar - validación de red requerida';
    }
    
    if (pioneerStatus.isPioneer) {
      if (validationStatus.activeNodes < 2) {
        return `Nodo Pionero - Esperando segundo nodo (${validationStatus.activeNodes}/2 nodos activos)`;
      } else {
        return `Nodo Pionero - Red activa con ${validationStatus.activeNodes} nodos`;
      }
    }
    
    return `Conectado a red con ${validationStatus.activeNodes} nodos activos`;
  };

  const getStatusClass = () => {
    if (pioneerStatus.error) return 'error';
    if (!validationStatus.isValidated) return 'validating';
    if (pioneerStatus.isPioneer && validationStatus.activeNodes < 2) return 'waiting';
    return 'connected';
  };

  return (
    <div className="pioneer-node-status">
      <div className="status-header">
        <h3>
          <span className="status-icon">{getStatusIcon()}</span>
          Estado del Nodo
        </h3>
        <div className="status-actions">
          <button 
            onClick={handleRefreshStatus}
            className="btn-refresh"
            title="Actualizar estado"
          >
            🔄
          </button>
          <button 
            onClick={handleForceRevalidation}
            className="btn-revalidate"
            title="Forzar revalidación"
          >
            🔍
          </button>
        </div>
      </div>

      <div className={`status-card ${getStatusClass()}`}>
        <div className="status-message">
          {getStatusMessage()}
        </div>
        
        {validationStatus.lastUpdate && (
          <div className="last-update">
            Última actualización: {new Date(validationStatus.lastUpdate).toLocaleTimeString()}
          </div>
        )}
      </div>

      <div className="network-info">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Coordinador:</span>
            <span className={`info-value ${validationStatus.isValidated ? 'connected' : 'disconnected'}`}>
              {validationStatus.isValidated ? '🟢 Conectado' : '🔴 Desconectado'}
            </span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Nodos Activos:</span>
            <span className="info-value">{validationStatus.activeNodes}</span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Nodos Génesis:</span>
            <span className="info-value">{validationStatus.genesisNodes}</span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Puede Operar:</span>
            <span className={`info-value ${validationStatus.canOperate ? 'yes' : 'no'}`}>
              {validationStatus.canOperate ? '✅ Sí' : '❌ No'}
            </span>
          </div>
        </div>
      </div>

      {pioneerStatus.isPioneer && validationStatus.activeNodes < 2 && (
        <div className="pioneer-waiting">
          <div className="waiting-animation">
            <div className="pulse"></div>
          </div>
          <div className="waiting-message">
            <h4>🚀 Modo Pionero Activo</h4>
            <p>
              Este es el primer nodo de la red PlayerGold. 
              La red se activará automáticamente cuando se conecte el segundo nodo pionero.
            </p>
            <div className="waiting-details">
              <div>• Nodo registrado en el coordinador ✅</div>
              <div>• Esperando segundo nodo pionero ⏳</div>
              <div>• La wallet funcionará normalmente una vez que la red esté activa 🌐</div>
            </div>
          </div>
        </div>
      )}

      {pioneerStatus.isPioneer && validationStatus.activeNodes >= 2 && (
        <div className="pioneer-active">
          <div className="success-icon">🎉</div>
          <div className="success-message">
            <h4>🌐 Red PlayerGold Activa</h4>
            <p>
              ¡Felicitaciones! La red PlayerGold está ahora activa con {validationStatus.activeNodes} nodos.
              Tu nodo pionero ha ayudado a inicializar la red exitosamente.
            </p>
          </div>
        </div>
      )}

      {pioneerStatus.error && (
        <div className="error-details">
          <h4>❌ Error de Conexión</h4>
          <p>{pioneerStatus.error}</p>
          <div className="error-actions">
            <button onClick={handleForceRevalidation} className="btn-retry">
              Reintentar Conexión
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PioneerNodeStatus;