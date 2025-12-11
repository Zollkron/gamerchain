import React, { useState, useEffect } from 'react';

const SyncProgress = ({ onSyncComplete, onError }) => {
  const [syncStatus, setSyncStatus] = useState({
    isConnected: false,
    isSyncing: false,
    currentBlock: 0,
    targetBlock: 0,
    syncProgress: 0,
    peers: 0,
    lastUpdate: null
  });
  
  const [statusMessages, setStatusMessages] = useState([]);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    initializeServices();
    
    // Cleanup on unmount
    return () => {
      window.electronAPI.stopBlockchainServices();
    };
  }, []);

  const initializeServices = async () => {
    try {
      setIsInitializing(true);
      
      // Listen for status updates
      window.electronAPI.onSyncStatus((status) => {
        addStatusMessage(status);
      });
      
      // Listen for sync status updates
      window.electronAPI.onSyncStatusUpdate((status) => {
        setSyncStatus(status);
      });
      
      // Listen for ready event
      window.electronAPI.onSyncReady(() => {
        setIsInitializing(false);
        if (onSyncComplete) {
          onSyncComplete();
        }
      });
      
      // Listen for errors
      window.electronAPI.onSyncError((error) => {
        addStatusMessage({ type: 'error', message: error.message });
        if (onError) {
          onError(error);
        }
      });
      
      // Start initialization
      await window.electronAPI.initializeBlockchainServices();
      
    } catch (error) {
      console.error('Error initializing services:', error);
      addStatusMessage({ type: 'error', message: error.message });
      if (onError) {
        onError(error);
      }
    }
  };

  const addStatusMessage = (status) => {
    const timestamp = new Date().toLocaleTimeString();
    const message = {
      ...status,
      timestamp,
      id: Date.now() + Math.random()
    };
    
    setStatusMessages(prev => [...prev.slice(-9), message]); // Keep last 10 messages
  };

  const getStatusIcon = (type) => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      default: return 'ℹ️';
    }
  };

  const getConnectionStatus = () => {
    if (!syncStatus.isConnected) {
      return { text: 'Desconectado', color: '#ff6b6b', icon: '🔴' };
    }
    if (syncStatus.isSyncing) {
      return { text: 'Sincronizando', color: '#ffd93d', icon: '🔄' };
    }
    return { text: 'Conectado', color: '#6bcf7f', icon: '🟢' };
  };

  const connectionStatus = getConnectionStatus();

  if (!isInitializing && syncStatus.syncProgress === 100 && !syncStatus.isSyncing) {
    return null; // Hide component when sync is complete
  }

  return (
    <div className="sync-progress-overlay">
      <div className="sync-progress-container">
        <div className="sync-header">
          <h2>🔗 Inicializando PlayerGold</h2>
          <p>Conectando a la red blockchain...</p>
        </div>

        {/* Connection Status */}
        <div className="connection-status">
          <div className="status-item">
            <span className="status-icon">{connectionStatus.icon}</span>
            <span className="status-text" style={{ color: connectionStatus.color }}>
              {connectionStatus.text}
            </span>
            {syncStatus.peers > 0 && (
              <span className="peer-count">({syncStatus.peers} peers)</span>
            )}
          </div>
        </div>

        {/* Sync Progress */}
        {syncStatus.isSyncing && (
          <div className="sync-progress-section">
            <div className="progress-info">
              <span>Sincronizando blockchain</span>
              <span>{syncStatus.syncProgress}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${syncStatus.syncProgress}%` }}
              ></div>
            </div>
            <div className="block-info">
              <span>Bloque {syncStatus.currentBlock} de {syncStatus.targetBlock}</span>
            </div>
          </div>
        )}

        {/* Status Messages */}
        <div className="status-messages">
          <h3>Estado del sistema:</h3>
          <div className="messages-container">
            {statusMessages.map((message) => (
              <div key={message.id} className={`status-message ${message.type}`}>
                <span className="message-icon">{getStatusIcon(message.type)}</span>
                <span className="message-text">{message.message}</span>
                <span className="message-time">{message.timestamp}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Loading Animation */}
        {isInitializing && (
          <div className="loading-animation">
            <div className="spinner"></div>
            <p>Iniciando servicios...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SyncProgress;