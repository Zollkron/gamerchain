import React, { useState, useEffect } from 'react';
import { aiModelService } from '../services/AIModelService';
import { miningService } from '../services/MiningService';

const MiningTab = ({ wallet }) => {
  const [miningStatus, setMiningStatus] = useState('stopped'); // stopped, downloading, starting, running, stopping
  const [selectedModel, setSelectedModel] = useState('');
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [nodeStatus, setNodeStatus] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [installedModels, setInstalledModels] = useState([]);
  const [systemRequirements, setSystemRequirements] = useState(null);

  // Get certified AI models from service
  const [certifiedModels, setCertifiedModels] = useState([]);

  useEffect(() => {
    // Initialize component
    initializeComponent();
    
    // Set up mining service listeners
    const handleStatusChange = (status, data) => {
      setMiningStatus(status);
      
      if (status === 'metrics' && data) {
        setNodeStatus(data);
      } else if (status === 'running') {
        addNotification('success', 'Nodo IA iniciado correctamente - Participando en consenso');
      } else if (status === 'stopped') {
        setNodeStatus(null);
        addNotification('success', 'Nodo IA detenido correctamente');
      } else if (status === 'error') {
        addNotification('error', data.error || 'Error en el nodo IA');
      }
    };

    miningService.addStatusListener(handleStatusChange);
    
    return () => {
      miningService.removeStatusListener(handleStatusChange);
    };
  }, []);

  const initializeComponent = async () => {
    try {
      // Load certified models
      const models = aiModelService.getCertifiedModels();
      setCertifiedModels(models);
      
      // Check system requirements
      await checkSystemRequirements();
      
      // Load installed models
      await loadInstalledModels();
      
      // Get current mining status
      const status = miningService.getMiningStatus();
      setMiningStatus(status.status);
      if (status.model) {
        setSelectedModel(status.model.modelId);
        setNodeStatus(miningService.generateMiningMetrics());
      }
    } catch (error) {
      console.error('Error initializing mining tab:', error);
      addNotification('error', 'Error inicializando la pestaña de minería');
    }
  };

  const checkSystemRequirements = async () => {
    try {
      const requirements = await aiModelService.checkSystemRequirements();
      setSystemRequirements(requirements);
    } catch (error) {
      console.error('Error checking system requirements:', error);
      addNotification('error', 'Error verificando requisitos del sistema');
    }
  };

  const loadInstalledModels = async () => {
    try {
      const installed = await aiModelService.getInstalledModels();
      setInstalledModels(installed.map(m => m.id));
    } catch (error) {
      console.error('Error loading installed models:', error);
      addNotification('error', 'Error cargando modelos instalados');
    }
  };



  const addNotification = (type, message) => {
    const notification = {
      id: Date.now(),
      type, // success, error, warning, info
      message,
      timestamp: new Date()
    };
    
    setNotifications(prev => [notification, ...prev.slice(0, 4)]); // Keep last 5
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const handleModelDownload = async (modelId) => {
    const model = certifiedModels.find(m => m.id === modelId);
    if (!model) return;

    try {
      setMiningStatus('downloading');
      setDownloadProgress(0);
      
      addNotification('info', `Iniciando descarga de ${model.name}...`);

      // Download model with progress tracking
      const result = await aiModelService.downloadModel(modelId, (progress) => {
        setDownloadProgress(progress);
      });

      // Verify model hash
      addNotification('info', `Verificando integridad de ${model.name}...`);
      await aiModelService.verifyModelHash(modelId, result.path);

      // Mark as installed
      await aiModelService.markModelInstalled(modelId, result.path, result.hash);
      
      // Update installed models list
      await loadInstalledModels();
      
      addNotification('success', `${model.name} descargado y verificado correctamente`);
      setMiningStatus('stopped');
      setDownloadProgress(0);

    } catch (error) {
      console.error('Error downloading model:', error);
      addNotification('error', error.message);
      setMiningStatus('stopped');
      setDownloadProgress(0);
    }
  };

  const startMining = async () => {
    if (!selectedModel) {
      addNotification('warning', 'Selecciona un modelo IA para comenzar la minería');
      return;
    }

    const model = certifiedModels.find(m => m.id === selectedModel);
    if (!installedModels.includes(selectedModel)) {
      await handleModelDownload(selectedModel);
      return;
    }

    try {
      addNotification('info', `Iniciando nodo IA con ${model.name}...`);
      
      // Start mining through service
      await miningService.startMining(selectedModel, wallet.address);
      
    } catch (error) {
      console.error('Error starting mining:', error);
      addNotification('error', error.message);
    }
  };

  const stopMining = async () => {
    try {
      addNotification('info', 'Deteniendo nodo IA...');
      await miningService.stopMining();
    } catch (error) {
      console.error('Error stopping mining:', error);
      addNotification('error', error.message);
    }
  };

  const uninstallModel = async (modelId) => {
    const model = certifiedModels.find(m => m.id === modelId);
    if (!model) return;

    if (miningStatus === 'running' && selectedModel === modelId) {
      addNotification('warning', 'Detén la minería antes de desinstalar el modelo');
      return;
    }

    try {
      await aiModelService.uninstallModel(modelId);
      await loadInstalledModels();
      addNotification('success', `${model.name} desinstalado correctamente`);
    } catch (error) {
      console.error('Error uninstalling model:', error);
      addNotification('error', error.message);
    }
  };

  const getModelStatus = (modelId) => {
    if (installedModels.includes(modelId)) {
      return 'installed';
    }
    return 'not-installed';
  };

  const canStartMining = () => {
    return miningStatus === 'stopped' && selectedModel && systemRequirements?.compatible;
  };

  const renderSystemRequirements = () => (
    <div className="system-requirements">
      <h3>Requisitos del Sistema</h3>
      {systemRequirements ? (
        <div className="requirements-grid">
          <div className="requirement-item">
            <span className="label">GPU:</span>
            <span className="value">{systemRequirements.gpu}</span>
            <span className={`status ${systemRequirements.compatible ? 'compatible' : 'incompatible'}`}>
              {systemRequirements.compatible ? '✓' : '✗'}
            </span>
          </div>
          <div className="requirement-item">
            <span className="label">VRAM:</span>
            <span className="value">{systemRequirements.vram} GB</span>
            <span className="status compatible">✓</span>
          </div>
          <div className="requirement-item">
            <span className="label">RAM:</span>
            <span className="value">{systemRequirements.ram} GB</span>
            <span className="status compatible">✓</span>
          </div>
          <div className="requirement-item">
            <span className="label">CPU Cores:</span>
            <span className="value">{systemRequirements.cores}</span>
            <span className="status compatible">✓</span>
          </div>
        </div>
      ) : (
        <div className="loading-requirements">
          <div className="loading-spinner"></div>
          <span>Verificando sistema...</span>
        </div>
      )}
    </div>
  );

  const renderModelSelector = () => (
    <div className="model-selector">
      <h3>Modelos IA Certificados</h3>
      <div className="model-dropdown">
        <select 
          value={selectedModel} 
          onChange={(e) => setSelectedModel(e.target.value)}
          disabled={miningStatus === 'running'}
        >
          <option value="">Selecciona un modelo IA...</option>
          {certifiedModels.map(model => (
            <option key={model.id} value={model.id}>
              {model.name} ({model.sizeFormatted})
            </option>
          ))}
        </select>
      </div>
      
      {selectedModel && (
        <div className="selected-model-info">
          {(() => {
            const model = certifiedModels.find(m => m.id === selectedModel);
            const status = getModelStatus(selectedModel);
            
            return (
              <div className="model-card">
                <div className="model-header">
                  <h4>{model.name}</h4>
                  <span className={`model-status ${status}`}>
                    {status === 'installed' ? 'Instalado' : 'No instalado'}
                  </span>
                </div>
                <p className="model-description">{model.description}</p>
                <div className="model-details">
                  <div className="detail">
                    <span>Tamaño:</span>
                    <span>{model.sizeFormatted}</span>
                  </div>
                  <div className="detail">
                    <span>VRAM requerida:</span>
                    <span>{model.requirements.vram} GB</span>
                  </div>
                  <div className="detail">
                    <span>RAM requerida:</span>
                    <span>{model.requirements.ram} GB</span>
                  </div>
                </div>
                
                {status === 'installed' && (
                  <div className="model-actions">
                    <button 
                      className="uninstall-button"
                      onClick={() => uninstallModel(selectedModel)}
                      disabled={miningStatus === 'running'}
                    >
                      Desinstalar
                    </button>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );

  const renderMiningControls = () => (
    <div className="mining-controls">
      <h3>Control de Minería</h3>
      
      {miningStatus === 'downloading' && (
        <div className="download-progress">
          <div className="progress-header">
            <span>Descargando modelo...</span>
            <span>{Math.round(downloadProgress)}%</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${downloadProgress}%` }}
            ></div>
          </div>
        </div>
      )}
      
      <div className="control-buttons">
        {miningStatus === 'stopped' && (
          <button 
            className="start-mining-button"
            onClick={startMining}
            disabled={!canStartMining()}
          >
            {selectedModel && !installedModels.includes(selectedModel) 
              ? 'Descargar e Iniciar Minería' 
              : 'Iniciar Minería'
            }
          </button>
        )}
        
        {(miningStatus === 'starting' || miningStatus === 'downloading') && (
          <button className="mining-button loading" disabled>
            <div className="loading-spinner"></div>
            {miningStatus === 'downloading' ? 'Descargando...' : 'Iniciando...'}
          </button>
        )}
        
        {miningStatus === 'running' && (
          <button 
            className="stop-mining-button"
            onClick={stopMining}
          >
            Detener Minería
          </button>
        )}
        
        {miningStatus === 'stopping' && (
          <button className="mining-button loading" disabled>
            <div className="loading-spinner"></div>
            Deteniendo...
          </button>
        )}
      </div>
    </div>
  );

  const renderNodeStatus = () => {
    if (!nodeStatus) return null;

    return (
      <div className="node-status">
        <h3>Estado del Nodo IA</h3>
        <div className="status-grid">
          <div className="status-card">
            <div className="status-icon">⚡</div>
            <div className="status-info">
              <div className="status-label">Estado</div>
              <div className="status-value">Validando</div>
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-icon">🔗</div>
            <div className="status-info">
              <div className="status-label">Peers Conectados</div>
              <div className="status-value">{nodeStatus.peersConnected}</div>
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-icon">✅</div>
            <div className="status-info">
              <div className="status-label">Validaciones</div>
              <div className="status-value">{nodeStatus.validationsCount}</div>
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-icon">⭐</div>
            <div className="status-info">
              <div className="status-label">Reputación</div>
              <div className="status-value">{nodeStatus.reputationScore.toFixed(1)}</div>
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-icon">💰</div>
            <div className="status-info">
              <div className="status-label">Ganado Hoy</div>
              <div className="status-value">{nodeStatus.earnings.today.toFixed(2)} PRGLD</div>
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-icon">🏆</div>
            <div className="status-info">
              <div className="status-label">Total Ganado</div>
              <div className="status-value">{nodeStatus.earnings.total.toFixed(2)} PRGLD</div>
            </div>
          </div>
        </div>
        
        <div className="last-activity">
          <span>Último challenge: {nodeStatus.lastChallenge.toLocaleTimeString()}</span>
        </div>
      </div>
    );
  };

  const renderNotifications = () => {
    if (notifications.length === 0) return null;

    return (
      <div className="notifications">
        {notifications.map(notification => (
          <div key={notification.id} className={`notification ${notification.type}`}>
            <div className="notification-content">
              <span className="notification-message">{notification.message}</span>
              <span className="notification-time">
                {notification.timestamp.toLocaleTimeString()}
              </span>
            </div>
            <button 
              className="notification-close"
              onClick={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    );
  };

  if (!wallet) {
    return (
      <div className="mining-tab">
        <div className="no-wallet-message">
          <h3>Cartera requerida</h3>
          <p>Necesitas tener una cartera activa para participar en la minería con IA.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mining-tab">
      {renderNotifications()}
      
      <div className="mining-header">
        <h2>Minería con IA - Consenso PoAIP</h2>
        <p>Convierte tu wallet en un nodo validador ejecutando una IA local certificada</p>
      </div>

      <div className="mining-content">
        <div className="mining-left">
          {renderSystemRequirements()}
          {renderModelSelector()}
          {renderMiningControls()}
        </div>
        
        <div className="mining-right">
          {renderNodeStatus()}
          
          <div className="mining-info">
            <h3>Información de Minería</h3>
            <div className="info-list">
              <div className="info-item">
                <span className="info-icon">🤖</span>
                <div className="info-text">
                  <strong>Solo IAs pueden minar:</strong> Los challenges matemáticos son imposibles de resolver por humanos en menos de 100ms
                </div>
              </div>
              <div className="info-item">
                <span className="info-icon">⚖️</span>
                <div className="info-text">
                  <strong>Recompensas equitativas:</strong> Todas las IAs validadoras reciben la misma recompensa, sin importar el hardware
                </div>
              </div>
              <div className="info-item">
                <span className="info-icon">🔒</span>
                <div className="info-text">
                  <strong>Verificación de modelos:</strong> Todos los modelos son verificados por hash SHA-256 para garantizar integridad
                </div>
              </div>
              <div className="info-item">
                <span className="info-icon">🌐</span>
                <div className="info-text">
                  <strong>Consenso distribuido:</strong> Validación cruzada entre múltiples IAs para máxima seguridad
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MiningTab;