import React, { useState, useEffect } from 'react';

const BootstrapStatus = ({ bootstrapService, onBootstrapComplete }) => {
  const [bootstrapState, setBootstrapState] = useState({
    mode: 'pioneer',
    walletAddress: null,
    selectedModel: null,
    discoveredPeers: [],
    genesisBlock: null,
    networkConfig: null,
    lastError: null,
    isReady: false
  });
  
  const [peerDiscoveryStatus, setPeerDiscoveryStatus] = useState({
    phase: 'idle',
    peers: [],
    elapsed: 0,
    message: ''
  });
  
  const [genesisProgress, setGenesisProgress] = useState({
    phase: 'idle',
    percentage: 0,
    message: '',
    participants: []
  });
  
  const [statusMessages, setStatusMessages] = useState([]);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (!bootstrapService) return;

    // Set up comprehensive event listeners for bootstrap service
    const handleStateChanged = (state) => {
      setBootstrapState(state);
      
      // Show bootstrap UI when not in network mode
      setIsVisible(state.mode !== 'network');
      
      // Notify parent when bootstrap is complete
      if (state.mode === 'network' && onBootstrapComplete) {
        onBootstrapComplete();
      }
    };

    const handlePeerDiscoveryStatus = (status) => {
      setPeerDiscoveryStatus(status);
      addStatusMessage('info', status.message);
    };

    const handleGenesisProgress = (progress) => {
      setGenesisProgress(progress);
      addStatusMessage('info', progress.message);
    };

    const handleError = (error) => {
      addStatusMessage('error', error.message);
    };

    const handleSuccess = (message) => {
      addStatusMessage('success', message);
    };

    // Additional bootstrap integration listeners
    const handlePeerDiscoveryStarted = () => {
      addStatusMessage('info', 'Iniciando descubrimiento de peers P2P...');
      setPeerDiscoveryStatus(prev => ({
        ...prev,
        phase: 'discovering',
        message: 'Buscando peers en la red...'
      }));
    };

    const handlePeersDiscovered = (peers) => {
      addStatusMessage('success', `${peers.length} peers descubiertos`);
      setPeerDiscoveryStatus(prev => ({
        ...prev,
        peers: peers,
        message: `${peers.length} peers encontrados`
      }));
    };

    const handleGenesisCoordinationStarted = () => {
      addStatusMessage('info', 'Iniciando coordinación del bloque génesis...');
      setGenesisProgress(prev => ({
        ...prev,
        phase: 'negotiating',
        percentage: 10,
        message: 'Negociando parámetros del génesis...'
      }));
    };

    const handleGenesisCreated = (genesisResult) => {
      addStatusMessage('success', '¡Bloque génesis creado exitosamente!');
      setGenesisProgress(prev => ({
        ...prev,
        phase: 'completed',
        percentage: 100,
        message: 'Génesis completado'
      }));
    };

    const handleNetworkModeActivated = () => {
      addStatusMessage('success', '¡Red blockchain establecida exitosamente!');
      // Hide bootstrap UI after a short delay
      setTimeout(() => {
        setIsVisible(false);
        if (onBootstrapComplete) {
          onBootstrapComplete();
        }
      }, 2000);
    };

    const handleModeChanged = (newMode, previousMode) => {
      addStatusMessage('info', `Transición: ${previousMode} → ${newMode}`);
    };

    // Set up all listeners
    bootstrapService.on('stateChanged', handleStateChanged);
    bootstrapService.on('peerDiscoveryStatus', handlePeerDiscoveryStatus);
    bootstrapService.on('genesisProgress', handleGenesisProgress);
    bootstrapService.on('error', handleError);
    bootstrapService.on('success', handleSuccess);
    
    // Additional integration listeners
    bootstrapService.on('peerDiscoveryStarted', handlePeerDiscoveryStarted);
    bootstrapService.on('peersDiscovered', handlePeersDiscovered);
    bootstrapService.on('genesisCoordinationStarted', handleGenesisCoordinationStarted);
    bootstrapService.on('genesisCreated', handleGenesisCreated);
    bootstrapService.on('networkModeActivated', handleNetworkModeActivated);
    bootstrapService.on('modeChanged', handleModeChanged);

    // Get initial state and setup
    const initialState = bootstrapService.getState();
    setBootstrapState(initialState);
    setIsVisible(initialState.mode !== 'network');

    // Initialize peer discovery status if in discovery mode
    if (initialState.mode === 'discovery') {
      setPeerDiscoveryStatus({
        phase: 'discovering',
        peers: initialState.discoveredPeers || [],
        elapsed: 0,
        message: 'Buscando peers en la red...'
      });
    }

    // Initialize genesis progress if in genesis mode
    if (initialState.mode === 'genesis') {
      setGenesisProgress({
        phase: 'negotiating',
        percentage: 20,
        message: 'Coordinando creación del génesis...',
        participants: initialState.discoveredPeers?.map(p => p.walletAddress) || []
      });
    }

    // Cleanup listeners
    return () => {
      bootstrapService.removeListener('stateChanged', handleStateChanged);
      bootstrapService.removeListener('peerDiscoveryStatus', handlePeerDiscoveryStatus);
      bootstrapService.removeListener('genesisProgress', handleGenesisProgress);
      bootstrapService.removeListener('error', handleError);
      bootstrapService.removeListener('success', handleSuccess);
      bootstrapService.removeListener('peerDiscoveryStarted', handlePeerDiscoveryStarted);
      bootstrapService.removeListener('peersDiscovered', handlePeersDiscovered);
      bootstrapService.removeListener('genesisCoordinationStarted', handleGenesisCoordinationStarted);
      bootstrapService.removeListener('genesisCreated', handleGenesisCreated);
      bootstrapService.removeListener('networkModeActivated', handleNetworkModeActivated);
      bootstrapService.removeListener('modeChanged', handleModeChanged);
    };
  }, [bootstrapService, onBootstrapComplete]);

  const addStatusMessage = (type, message) => {
    const newMessage = {
      id: Date.now(),
      type,
      message,
      timestamp: new Date().toLocaleTimeString()
    };
    
    setStatusMessages(prev => [...prev.slice(-9), newMessage]); // Keep last 10 messages
  };

  const getModeDisplayName = (mode) => {
    const modeNames = {
      pioneer: 'Modo Pionero',
      discovery: 'Descubrimiento P2P',
      genesis: 'Creación del Génesis',
      network: 'Red Activa'
    };
    return modeNames[mode] || mode;
  };

  const getModeDescription = (mode) => {
    const descriptions = {
      pioneer: 'Esperando que crees tu cartera y selecciones un modelo IA para comenzar',
      discovery: 'Buscando otros usuarios pioneros en la red para formar la blockchain',
      genesis: 'Coordinando con otros peers para crear el bloque génesis',
      network: 'Red blockchain establecida - todas las funciones disponibles'
    };
    return descriptions[mode] || '';
  };

  const getInstructions = (mode) => {
    switch (mode) {
      case 'pioneer':
        return [
          '1. Crea tu dirección de cartera usando el botón "Crear Nueva Cartera"',
          '2. Ve a la pestaña "Minería" y selecciona un modelo IA',
          '3. Haz clic en "Iniciar Minería" para comenzar el descubrimiento P2P'
        ];
      case 'discovery':
        return [
          '1. Buscando otros usuarios pioneros en la red local...',
          '2. Asegúrate de que otros dispositivos estén ejecutando la aplicación',
          '3. El proceso puede tomar unos minutos - mantén la aplicación abierta'
        ];
      case 'genesis':
        return [
          '1. Coordinando con peers encontrados para crear el bloque génesis',
          '2. Negociando parámetros de la red blockchain',
          '3. Este proceso es automático - no cierres la aplicación'
        ];
      case 'network':
        return [
          '¡Red blockchain establecida exitosamente!',
          'Todas las funciones están ahora disponibles',
          'Puedes enviar transacciones, minar y participar en el consenso'
        ];
      default:
        return [];
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="bootstrap-overlay">
      <div className="bootstrap-container">
        <div className="bootstrap-header">
          <h2>🚀 Auto-Bootstrap P2P Network</h2>
          <p>Estableciendo red blockchain automáticamente</p>
        </div>

        <div className="bootstrap-status">
          <div className="status-indicator">
            <div className={`status-dot ${bootstrapState.mode === 'network' ? 'success' : 'active'}`}></div>
            <div className="status-info">
              <h3>{getModeDisplayName(bootstrapState.mode)}</h3>
              <p>{getModeDescription(bootstrapState.mode)}</p>
            </div>
          </div>
        </div>

        {/* Peer Discovery Progress */}
        {bootstrapState.mode === 'discovery' && (
          <div className="discovery-section">
            <h4>🔍 Descubrimiento de Peers</h4>
            <div className="discovery-info">
              <div className="peer-count">
                <span>Peers encontrados: {peerDiscoveryStatus.peers.length}</span>
                <span>Tiempo transcurrido: {Math.floor(peerDiscoveryStatus.elapsed / 1000)}s</span>
              </div>
              <div className="discovery-message">
                {peerDiscoveryStatus.message}
              </div>
            </div>
            
            {peerDiscoveryStatus.peers.length > 0 && (
              <div className="discovered-peers">
                <h5>Peers Descubiertos:</h5>
                <div className="peers-list">
                  {peerDiscoveryStatus.peers.map((peer, index) => (
                    <div key={peer.id || index} className="peer-item">
                      <span className="peer-address">{peer.address}:{peer.port}</span>
                      <span className="peer-status">{peer.isReady ? '✅ Listo' : '⏳ Preparando'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Genesis Creation Progress */}
        {bootstrapState.mode === 'genesis' && (
          <div className="genesis-section">
            <h4>⚡ Creación del Bloque Génesis</h4>
            <div className="genesis-progress">
              <div className="progress-info">
                <span>{genesisProgress.message}</span>
                <span>{genesisProgress.percentage}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${genesisProgress.percentage}%` }}
                ></div>
              </div>
            </div>
            
            {genesisProgress.participants.length > 0 && (
              <div className="genesis-participants">
                <h5>Participantes del Génesis:</h5>
                <div className="participants-list">
                  {genesisProgress.participants.map((address, index) => (
                    <div key={index} className="participant-item">
                      <span className="participant-address">{address}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Instructions */}
        <div className="bootstrap-instructions">
          <h4>📋 Instrucciones</h4>
          <div className="instructions-list">
            {getInstructions(bootstrapState.mode).map((instruction, index) => (
              <div key={index} className="instruction-item">
                {instruction}
              </div>
            ))}
          </div>
        </div>

        {/* Status Messages */}
        {statusMessages.length > 0 && (
          <div className="status-messages">
            <h4>📝 Estado del Sistema</h4>
            <div className="messages-container">
              {statusMessages.map((message) => (
                <div key={message.id} className={`status-message ${message.type}`}>
                  <span className="message-icon">
                    {message.type === 'error' ? '❌' : 
                     message.type === 'success' ? '✅' : 
                     message.type === 'warning' ? '⚠️' : 'ℹ️'}
                  </span>
                  <span className="message-text">{message.message}</span>
                  <span className="message-time">{message.timestamp}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Display */}
        {bootstrapState.lastError && (
          <div className="bootstrap-error">
            <h4>⚠️ Error</h4>
            <div className="error-details">
              <p><strong>Tipo:</strong> {bootstrapState.lastError.type}</p>
              <p><strong>Mensaje:</strong> {bootstrapState.lastError.message}</p>
              <p><strong>Hora:</strong> {new Date(bootstrapState.lastError.timestamp).toLocaleString()}</p>
              {bootstrapState.lastError.canRetry && (
                <p className="retry-info">🔄 El sistema reintentará automáticamente</p>
              )}
            </div>
          </div>
        )}

        {/* Loading Animation */}
        {(bootstrapState.mode === 'discovery' || bootstrapState.mode === 'genesis') && (
          <div className="loading-animation">
            <div className="spinner"></div>
            <p>Procesando... Por favor mantén la aplicación abierta</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BootstrapStatus;