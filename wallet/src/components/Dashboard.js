import React, { useState, useEffect } from 'react';
import BlockchainNodeStatus from './BlockchainNodeStatus';
import PioneerNodeStatus from './PioneerNodeStatus';

const Dashboard = ({ wallet, wallets, onWalletChange, onWalletsUpdate }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [balance, setBalance] = useState('0.00');
  const [transactions, setTransactions] = useState([]);
  const [networkStatus, setNetworkStatus] = useState({ connected: false, synced: false });
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [errorInfo, setErrorInfo] = useState(null);
  const [bootstrapService, setBootstrapService] = useState(null);
  const [bootstrapState, setBootstrapState] = useState({ mode: 'network' });
  
  // Genesis state management
  const [genesisStateManager, setGenesisStateManager] = useState(null);
  const [walletStateProvider, setWalletStateProvider] = useState(null);
  const [genesisState, setGenesisState] = useState({ exists: false });
  const [walletDisplayState, setWalletDisplayState] = useState(null);
  
  // Send transaction form state
  const [sendForm, setSendForm] = useState({
    toAddress: '',
    amount: '',
    memo: ''
  });
  
  // Mining state
  const [miningStatus, setMiningStatus] = useState({
    isActive: false,
    selectedModel: '',
    currentModel: null,
    stats: {
      blocksValidated: 0,
      rewardsEarned: 0,
      challengesProcessed: 0,
      successRate: 100,
      uptime: 0,
      reputation: 100
    }
  });
  
  const [availableModels, setAvailableModels] = useState([]);
  const [downloadProgress, setDownloadProgress] = useState({});
  const [miningRewards, setMiningRewards] = useState(null);

  // Initialize genesis state management
  useEffect(() => {
    const initializeStateManagement = async () => {
      try {
        if (window.electronAPI && window.electronAPI.getGenesisStateManager) {
          const gsm = await window.electronAPI.getGenesisStateManager();
          setGenesisStateManager(gsm);
          
          // Check initial genesis state
          const initialGenesisState = await gsm.checkGenesisExists();
          setGenesisState(initialGenesisState);
          
          // Setup comprehensive genesis state listeners
          gsm.on('genesisStateChanged', (newGenesisState) => {
            setGenesisState(newGenesisState);
            
            // Refresh wallet data when genesis state changes
            if (newGenesisState.exists && wallet) {
              setTimeout(() => loadWalletData(), 500);
            }
          });
          
          gsm.on('networkStateChanged', (newState, previousState) => {
            console.log(`Network state changed: ${previousState} -> ${newState}`);
            
            // Update network status based on state change
            setNetworkStatus(prev => ({
              ...prev,
              connected: newState === 'active',
              synced: newState === 'active'
            }));
            
            // Refresh wallet data on significant state changes
            if (newState === 'active' && wallet) {
              setTimeout(() => loadWalletData(), 500);
            }
          });
          
          gsm.on('cachedDataCleared', () => {
            console.log('Cached data cleared - refreshing wallet data');
            if (wallet) {
              loadWalletData();
            }
          });
          
          gsm.on('networkActivated', (data) => {
            console.log('Network activated:', data);
            if (wallet) {
              setTimeout(() => loadWalletData(), 1000);
            }
          });
        }
        
        if (window.electronAPI && window.electronAPI.getWalletStateProvider) {
          const wsp = await window.electronAPI.getWalletStateProvider();
          setWalletStateProvider(wsp);
          
          // Setup comprehensive wallet state provider listeners
          wsp.on('walletStateUpdated', (walletId, displayState) => {
            if (wallet && walletId === wallet.id) {
              setWalletDisplayState(displayState);
              
              // Update UI state based on display state
              setBalance(displayState.balance);
              setTransactions(displayState.transactions);
              setNetworkStatus({
                connected: displayState.networkState === 'active',
                synced: displayState.networkState === 'active'
              });
            }
          });
          
          wsp.on('bootstrapStateChanged', (bootstrapState) => {
            console.log('Bootstrap state changed in wallet state provider:', bootstrapState.mode);
            setBootstrapState(bootstrapState);
          });
          
          wsp.on('bootstrapCompleted', (data) => {
            console.log('Bootstrap completed:', data);
            if (wallet) {
              setTimeout(() => loadWalletData(), 1000);
            }
          });
          
          wsp.on('bootstrapPhaseChanged', (phase) => {
            console.log('Bootstrap phase changed:', phase);
            // Could update UI to show bootstrap progress
          });
          
          wsp.on('blockchainOperationsEnabled', (data) => {
            console.log('Blockchain operations enabled:', data.availableFeatures);
            if (wallet) {
              setTimeout(() => loadWalletData(), 500);
            }
          });
        }
      } catch (error) {
        console.error('Error initializing state management:', error);
      }
    };
    
    initializeStateManagement();
  }, []);

  // Load wallet data on mount and wallet change
  useEffect(() => {
    if (wallet) {
      loadWalletData();
      loadMiningData();
    }
  }, [wallet]);

  // Initialize bootstrap service
  useEffect(() => {
    const initBootstrapService = async () => {
      try {
        if (window.electronAPI && window.electronAPI.getBootstrapService) {
          const service = await window.electronAPI.getBootstrapService();
          setBootstrapService(service);
          
          // Get initial state
          const state = service.getState();
          setBootstrapState(state);
          
          // Setup comprehensive bootstrap listeners
          const handleStateChange = (newState) => {
            setBootstrapState(newState);
            
            // Update UI based on bootstrap state
            if (newState.mode === 'network') {
              // Bootstrap completed - refresh wallet data
              loadWalletData();
            }
          };
          
          const handleGenesisCreated = (genesisResult) => {
            console.log('Genesis block created:', genesisResult);
            // Refresh wallet data after genesis creation
            setTimeout(() => loadWalletData(), 1000);
          };
          
          const handleNetworkModeActivated = () => {
            console.log('Network mode activated');
            // Clear any cached data and refresh
            setTimeout(() => loadWalletData(), 1000);
          };
          
          const handleBootstrapError = (error) => {
            console.error('Bootstrap error:', error);
            // Could show error notification to user
          };
          
          // Set up all bootstrap listeners
          service.on('stateChanged', handleStateChange);
          service.on('genesisCreated', handleGenesisCreated);
          service.on('networkModeActivated', handleNetworkModeActivated);
          service.on('error', handleBootstrapError);
          
          // Integrate with genesis state manager if available
          if (genesisStateManager && service) {
            try {
              await genesisStateManager.synchronizeWithBootstrap();
            } catch (error) {
              console.warn('Could not synchronize with bootstrap:', error);
            }
          }
          
          // Integrate with wallet state provider if available
          if (walletStateProvider && service) {
            try {
              await walletStateProvider.synchronizeWithBootstrap();
            } catch (error) {
              console.warn('Could not synchronize wallet state provider with bootstrap:', error);
            }
          }
          
          return () => {
            service.removeListener('stateChanged', handleStateChange);
            service.removeListener('genesisCreated', handleGenesisCreated);
            service.removeListener('networkModeActivated', handleNetworkModeActivated);
            service.removeListener('error', handleBootstrapError);
          };
        }
      } catch (error) {
        console.error('Error initializing bootstrap service:', error);
      }
    };
    
    initBootstrapService();
  }, [genesisStateManager, walletStateProvider]);

  // Set up mining status listeners
  useEffect(() => {
    if (!window.electronAPI) return;

    const handleMiningStatusChange = (status) => {
      // Only log if status is valid
      if (status && typeof status === 'object' && Object.keys(status).length > 0) {
        console.log('Mining status change:', status);
        loadMiningData(); // Refresh mining data
      }
    };

    const handleModelDownloadProgress = (progress) => {
      setDownloadProgress(prev => ({
        ...prev,
        [progress.modelId]: progress
      }));
    };

    // Set up listeners
    const unsubscribeMining = window.electronAPI.onMiningStatusChange?.(handleMiningStatusChange);
    const unsubscribeDownload = window.electronAPI.onModelDownloadProgress?.(handleModelDownloadProgress);

    return () => {
      if (unsubscribeMining) unsubscribeMining();
      if (unsubscribeDownload) unsubscribeDownload();
    };
  }, []);

  const loadWalletData = async () => {
    if (!wallet || !window.electronAPI) return;
    
    setIsLoading(true);
    setErrorInfo(null);
    
    // Set loading message based on current network state
    const currentNetworkState = genesisStateManager ? genesisStateManager.getCurrentNetworkState() : 'disconnected';
    setLoadingMessage(getLoadingMessage('wallet_data', currentNetworkState));
    
    try {
      // Use WalletStateProvider if available for honest state display
      if (walletStateProvider) {
        const displayState = await walletStateProvider.getWalletDisplayState(wallet.id);
        setWalletDisplayState(displayState);
        setBalance(displayState.balance);
        setTransactions(displayState.transactions);
        setNetworkStatus({
          connected: displayState.networkState === 'active',
          synced: displayState.networkState === 'active'
        });
        
        // Handle error information from display state
        if (displayState.error) {
          setErrorInfo({
            message: displayState.error,
            type: 'wallet_state_error',
            canRetry: true
          });
        }
      } else {
        // Fallback to direct API calls
        setLoadingMessage(getLoadingMessage('balance_query', currentNetworkState));
        
        // Load balance - but check genesis state first
        const balanceResult = await window.electronAPI.getWalletBalance(wallet.id);
        if (balanceResult.success && !balanceResult.requiresGenesis) {
          setBalance(balanceResult.balance);
        } else {
          // Show zero balance when genesis doesn't exist
          setBalance('0.00');
          
          // Handle balance errors
          if (balanceResult.errorInfo) {
            setErrorInfo({
              message: balanceResult.errorInfo.message,
              explanation: balanceResult.errorInfo.explanation,
              type: balanceResult.errorType,
              canRetry: balanceResult.errorInfo.canRetry
            });
          }
        }
        
        setLoadingMessage(getLoadingMessage('transaction_history', currentNetworkState));
        
        // Load transaction history - but check genesis state first
        const historyResult = await window.electronAPI.getTransactionHistory(wallet.id, 20, 0);
        if (historyResult.success && !historyResult.requiresGenesis) {
          setTransactions(historyResult.transactions);
        } else {
          // Show empty transactions when genesis doesn't exist
          setTransactions([]);
          
          // Handle history errors (only if no balance error)
          if (historyResult.errorInfo && !errorInfo) {
            setErrorInfo({
              message: historyResult.errorInfo.message,
              explanation: historyResult.errorInfo.explanation,
              type: historyResult.errorType,
              canRetry: historyResult.errorInfo.canRetry
            });
          }
        }
        
        setLoadingMessage(getLoadingMessage('network_status', currentNetworkState));
        
        // Get network status
        const statusResult = await window.electronAPI.getNetworkStatus();
        if (statusResult.success) {
          setNetworkStatus({
            connected: true,
            synced: statusResult.status.syncStatus === 'synced'
          });
        } else {
          setNetworkStatus({ connected: false, synced: false });
          
          // Handle network status errors (only if no other errors)
          if (statusResult.errorInfo && !errorInfo) {
            setErrorInfo({
              message: statusResult.errorInfo.message,
              explanation: statusResult.errorInfo.explanation,
              type: statusResult.errorType,
              canRetry: statusResult.errorInfo.canRetry
            });
          }
        }
      }
    } catch (error) {
      console.error('Error loading wallet data:', error);
      
      // On error, show honest empty state
      setBalance('0.00');
      setTransactions([]);
      setNetworkStatus({ connected: false, synced: false });
      
      // Set generic error info
      setErrorInfo({
        message: 'Error inesperado al cargar datos de la cartera',
        explanation: 'Ha ocurrido un error no esperado. Por favor, intenta nuevamente.',
        type: 'unknown_error',
        canRetry: true
      });
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  /**
   * Get loading message for current operation and network state
   * @param {string} operation - Current operation
   * @param {string} networkState - Current network state
   * @returns {string} Loading message
   */
  const getLoadingMessage = (operation, networkState) => {
    const messages = {
      'wallet_data': 'Cargando datos de la cartera',
      'balance_query': 'Consultando balance',
      'transaction_history': 'Cargando historial de transacciones',
      'network_status': 'Verificando estado de la red'
    };
    
    const baseMessage = messages[operation] || 'Procesando';
    
    if (networkState === 'connecting') {
      return `${baseMessage} (conectando a la red)...`;
    } else if (networkState.startsWith('bootstrap_')) {
      return `${baseMessage} (estableciendo red)...`;
    } else {
      return `${baseMessage}...`;
    }
  };

  const handleSendTransaction = async (e) => {
    e.preventDefault();
    if (!window.electronAPI || !wallet) return;
    
    // Check if send transaction operation is allowed based on genesis state
    const canSendTransactions = walletDisplayState?.canSendTransactions ?? 
      (genesisStateManager ? genesisStateManager.isOperationAllowed('send_transaction') : false);
    
    if (!canSendTransactions) {
      setErrorInfo({
        message: 'Envío de transacciones no disponible',
        explanation: 'Las transacciones requieren que la blockchain esté completamente activa. Actualmente la red está en proceso de inicialización.',
        type: 'operation_not_allowed',
        canRetry: false
      });
      return;
    }
    
    setIsLoading(true);
    setErrorInfo(null);
    setLoadingMessage('Enviando transacción...');
    
    try {
      const result = await window.electronAPI.sendTransaction(wallet.id, {
        toAddress: sendForm.toAddress,
        amount: parseFloat(sendForm.amount),
        memo: sendForm.memo
      });
      
      if (result.success) {
        alert(`Transacción enviada exitosamente!\nID: ${result.transactionId}`);
        setSendForm({ toAddress: '', amount: '', memo: '' });
        loadWalletData(); // Refresh data
      } else {
        // Handle transaction error with detailed information
        if (result.errorInfo) {
          setErrorInfo({
            message: result.errorInfo.message,
            explanation: result.errorInfo.explanation,
            type: result.errorType,
            canRetry: result.errorInfo.canRetry
          });
        } else {
          alert(`Error al enviar transacción: ${result.error}`);
        }
      }
    } catch (error) {
      setErrorInfo({
        message: 'Error inesperado al enviar transacción',
        explanation: 'Ha ocurrido un error no esperado durante el envío. Por favor, verifica los datos e intenta nuevamente.',
        type: 'unknown_error',
        canRetry: true
      });
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  const handleRequestFaucet = async () => {
    if (!window.electronAPI || !wallet) return;
    
    // Check if faucet operation is allowed based on genesis state
    const canRequestFaucet = walletDisplayState?.canRequestFaucet ?? 
      (genesisStateManager ? genesisStateManager.isOperationAllowed('faucet') : false);
    
    if (!canRequestFaucet) {
      setErrorInfo({
        message: 'Faucet no disponible',
        explanation: 'El faucet de testnet requiere que la blockchain esté completamente activa. Actualmente la red está en proceso de inicialización.',
        type: 'operation_not_allowed',
        canRetry: false
      });
      return;
    }
    
    setIsLoading(true);
    setErrorInfo(null);
    setLoadingMessage('Solicitando tokens del faucet...');
    
    try {
      const result = await window.electronAPI.requestFaucetTokens(wallet.id, 1000);
      if (result.success) {
        alert(`¡Tokens solicitados exitosamente!\nCantidad: ${result.amount} PRGLD\nID: ${result.transactionId}`);
        setTimeout(() => loadWalletData(), 3000); // Refresh after 3 seconds
      } else {
        // Handle faucet error with detailed information
        if (result.errorInfo) {
          setErrorInfo({
            message: result.errorInfo.message,
            explanation: result.errorInfo.explanation,
            type: result.errorType,
            canRetry: result.errorInfo.canRetry
          });
        } else {
          alert(`Error al solicitar tokens: ${result.error}`);
        }
      }
    } catch (error) {
      setErrorInfo({
        message: 'Error inesperado al solicitar tokens',
        explanation: 'Ha ocurrido un error no esperado durante la solicitud del faucet. Por favor, intenta nuevamente.',
        type: 'unknown_error',
        canRetry: true
      });
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  const loadMiningData = async () => {
    if (!window.electronAPI) return;
    
    try {
      // Load mining status
      const statusResult = await window.electronAPI.getMiningStatus();
      if (statusResult.success) {
        setMiningStatus({
          isActive: statusResult.status.isMining,
          selectedModel: statusResult.status.currentModel?.id || '',
          currentModel: statusResult.status.currentModel,
          stats: statusResult.status.stats
        });
      }
      
      // Load available models
      const modelsResult = await window.electronAPI.getCertifiedModels();
      if (modelsResult.success) {
        setAvailableModels(modelsResult.models);
      }
      
      // Load mining rewards estimation
      const rewardsResult = await window.electronAPI.estimateMiningRewards();
      if (rewardsResult.success) {
        setMiningRewards(rewardsResult.rewards);
      }
    } catch (error) {
      console.error('Error loading mining data:', error);
    }
  };

  const handleDownloadModel = async (modelId) => {
    if (!window.electronAPI) return;
    
    try {
      const result = await window.electronAPI.downloadModel(modelId);
      if (result.success) {
        alert(`¡Modelo descargado exitosamente!\n${result.message}`);
        loadMiningData(); // Refresh mining data
      } else {
        alert(`Error al descargar modelo: ${result.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const handleStartMining = async () => {
    if (!window.electronAPI || !wallet || !miningStatus.selectedModel) return;
    
    setIsLoading(true);
    try {
      // If in bootstrap mode, notify bootstrap service about mining readiness
      if (bootstrapService && bootstrapState.mode === 'pioneer') {
        await bootstrapService.onWalletAddressCreated(wallet.address);
        await bootstrapService.onMiningReadiness(miningStatus.selectedModel, {
          id: miningStatus.selectedModel,
          name: miningStatus.currentModel?.name || 'Selected Model'
        });
        
        // Start peer discovery
        await bootstrapService.startPeerDiscovery();
        
        alert('¡Bootstrap P2P iniciado!\nBuscando otros usuarios pioneros en la red...');
      } else {
        // Normal mining start
        const result = await window.electronAPI.startMining(miningStatus.selectedModel, wallet.address);
        if (result.success) {
          alert(`¡Minería iniciada exitosamente!\nModelo: ${result.model.name}`);
          loadMiningData(); // Refresh mining data
        } else {
          alert(`Error al iniciar minería: ${result.error}`);
        }
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopMining = async () => {
    if (!window.electronAPI) return;
    
    setIsLoading(true);
    try {
      const result = await window.electronAPI.stopMining();
      if (result.success) {
        alert(`Minería detenida exitosamente!`);
        loadMiningData(); // Refresh mining data
      } else {
        alert(`Error al detener minería: ${result.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const navigationItems = [
    { id: 'overview', label: 'Resumen', icon: '🏠' },
    { id: 'send', label: 'Enviar', icon: '📤' },
    { id: 'receive', label: 'Recibir', icon: '📥' },
    { id: 'history', label: 'Historial', icon: '📋' },
    { id: 'mining', label: 'Minería', icon: '⛏️' },
    { id: 'wallets', label: 'Carteras', icon: '👛' },
    { id: 'addressbook', label: 'Libreta', icon: '📇' },
    { id: 'privacy', label: 'Privacidad', icon: '🔒' },
    { id: 'security', label: 'Seguridad', icon: '🛡️' }
  ];

  const handleTransactionSent = (result) => {
    // Refresh wallet data after successful transaction
    if (onWalletsUpdate) {
      onWalletsUpdate();
    }
  };

  const renderContent = () => {
    if (!wallet) {
      return (
        <div className="no-wallet-selected">
          <h3>No hay cartera seleccionada</h3>
          <p>Selecciona una cartera desde el menú de carteras para continuar.</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return (
          <div className="tab-content">
            {/* Pioneer Node Status - Always show for network validation */}
            <PioneerNodeStatus />
            
            {/* Bootstrap Status Card */}
            {bootstrapState.mode !== 'network' && (
              <div className="bootstrap-status-card">
                <h3>🚀 Estado del Bootstrap P2P</h3>
                <div className="bootstrap-mode">
                  <span className="mode-indicator">
                    {bootstrapState.mode === 'pioneer' ? '🏴‍☠️' :
                     bootstrapState.mode === 'discovery' ? '🔍' :
                     bootstrapState.mode === 'genesis' ? '⚡' : '✅'}
                  </span>
                  <div className="mode-info">
                    <strong>
                      {bootstrapState.mode === 'pioneer' ? 'Modo Pionero' :
                       bootstrapState.mode === 'discovery' ? 'Descubrimiento P2P' :
                       bootstrapState.mode === 'genesis' ? 'Creación del Génesis' : 'Red Activa'}
                    </strong>
                    <p>
                      {bootstrapState.mode === 'pioneer' ? 'Crea tu cartera y selecciona un modelo IA para comenzar' :
                       bootstrapState.mode === 'discovery' ? 'Buscando otros usuarios pioneros en la red' :
                       bootstrapState.mode === 'genesis' ? 'Coordinando con peers para crear el bloque génesis' : 'Red establecida'}
                    </p>
                  </div>
                </div>
                
                {bootstrapState.mode === 'pioneer' && (
                  <div className="bootstrap-instructions">
                    <h4>Próximos pasos:</h4>
                    <ol>
                      <li>✅ Cartera creada: {wallet ? wallet.address.substring(0, 10) + '...' : 'Pendiente'}</li>
                      <li>{bootstrapState.selectedModel ? '✅' : '⏳'} Ve a "Minería" y selecciona un modelo IA</li>
                      <li>{bootstrapState.isReady ? '✅' : '⏳'} Haz clic en "Iniciar Minería" para comenzar</li>
                    </ol>
                  </div>
                )}
                
                {bootstrapState.mode === 'discovery' && (
                  <div className="discovery-status">
                    <p><strong>Peers encontrados:</strong> {bootstrapState.discoveredPeers.length}</p>
                    <p><strong>Estado:</strong> Buscando más usuarios pioneros...</p>
                    <div className="discovery-animation">
                      <div className="scanning-dots">
                        <span>●</span><span>●</span><span>●</span>
                      </div>
                    </div>
                  </div>
                )}
                
                {bootstrapState.mode === 'genesis' && (
                  <div className="genesis-status">
                    <p><strong>Participantes:</strong> {bootstrapState.discoveredPeers.length}</p>
                    <p><strong>Estado:</strong> Creando bloque génesis...</p>
                    <div className="genesis-animation">
                      <div className="creating-spinner"></div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Error Display */}
            {errorInfo && (
              <div className="error-card">
                <div className="error-header">
                  <span className="error-icon">⚠️</span>
                  <h4>{errorInfo.message}</h4>
                </div>
                {errorInfo.explanation && (
                  <p className="error-explanation">{errorInfo.explanation}</p>
                )}
                {errorInfo.canRetry && (
                  <button 
                    className="retry-button"
                    onClick={() => {
                      setErrorInfo(null);
                      loadWalletData();
                    }}
                    disabled={isLoading}
                  >
                    🔄 Reintentar
                  </button>
                )}
                <button 
                  className="dismiss-error-button"
                  onClick={() => setErrorInfo(null)}
                >
                  ✕ Cerrar
                </button>
              </div>
            )}

            <div className="balance-card">
              <h3>Balance Total</h3>
              <div className="balance-amount">
                {isLoading ? (loadingMessage || 'Cargando...') : `${balance} PRGLD`}
              </div>
              {/* Genesis state indicator */}
              {!genesisState.exists && (
                <div className="genesis-warning">
                  ⚠️ Blockchain no inicializada - Balance real: 0 PRGLD
                </div>
              )}
              <button 
                className="faucet-button" 
                onClick={handleRequestFaucet}
                disabled={
                  isLoading || 
                  !genesisState.exists ||
                  !(walletDisplayState?.canRequestFaucet ?? (genesisStateManager ? genesisStateManager.isOperationAllowed('faucet') : false))
                }
                title={
                  bootstrapState.mode !== 'network' ? 'Disponible después del bootstrap' :
                  !genesisState.exists ? 'Requiere blockchain activa' :
                  ''
                }
              >
                🚰 Solicitar Tokens Testnet
              </button>
            </div>
            
            <div className="wallet-info-card">
              <h3>Información de la Cartera</h3>
              <div className="info-row">
                <span>Nombre:</span>
                <span>{wallet.name || 'Sin nombre'}</span>
              </div>
              <div className="info-row">
                <span>Dirección:</span>
                <span className="address">{wallet.address || 'No disponible'}</span>
              </div>
              <div className="info-row">
                <span>Creada:</span>
                <span>{wallet.createdAt ? new Date(wallet.createdAt).toLocaleDateString() : 'N/A'}</span>
              </div>
            </div>

            <div className="recent-transactions">
              <h3>Transacciones Recientes</h3>
              {!genesisState.exists ? (
                <div className="no-genesis-message">
                  <p>📋 No hay transacciones disponibles</p>
                  <p>Las transacciones aparecerán una vez que se inicialice la blockchain</p>
                </div>
              ) : transactions.length === 0 ? (
                <p>No hay transacciones recientes</p>
              ) : (
                <div className="transactions-list">
                  {transactions.slice(0, 5).map((tx, index) => (
                    <div key={index} className="transaction-item">
                      <div className="tx-icon">
                        {tx.direction === 'sent' ? '📤' : '📥'}
                      </div>
                      <div className="tx-details">
                        <div className="tx-amount">
                          {tx.direction === 'sent' ? '-' : '+'}{tx.amount} PRGLD
                        </div>
                        <div className="tx-address">
                          {tx.direction === 'sent' ? `Para: ${tx.to}` : `De: ${tx.from}`}
                        </div>
                        <div className="tx-date">
                          {new Date(tx.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <div className="tx-status">
                        {tx.status === 'confirmed' ? '✅' : '⏳'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      case 'wallets':
        return (
          <div className="tab-content">
            <h2>Gestión de Carteras</h2>
            <p>Carteras disponibles: {wallets.length}</p>
            <div className="wallets-list">
              {wallets.map((w, index) => (
                <div key={index} className={`wallet-item ${w === wallet ? 'active' : ''}`}>
                  <p><strong>{w.name || `Cartera ${index + 1}`}</strong></p>
                  <p>{w.address}</p>
                  {w !== wallet && (
                    <button onClick={() => onWalletChange(w)}>Seleccionar</button>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      case 'send':
        return (
          <div className="tab-content">
            <div className="send-form-container">
              <h3>Enviar PRGLD</h3>
              <form onSubmit={handleSendTransaction} className="send-form">
                <div className="form-group">
                  <label>Dirección de destino:</label>
                  <input
                    type="text"
                    value={sendForm.toAddress}
                    onChange={(e) => setSendForm({...sendForm, toAddress: e.target.value})}
                    placeholder="PG..."
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>Cantidad:</label>
                  <input
                    type="number"
                    step="0.00000001"
                    min="0"
                    value={sendForm.amount}
                    onChange={(e) => setSendForm({...sendForm, amount: e.target.value})}
                    placeholder="0.00"
                    required
                  />
                  <small>Balance disponible: {balance} PRGLD</small>
                </div>
                
                <div className="form-group">
                  <label>Memo (opcional):</label>
                  <input
                    type="text"
                    value={sendForm.memo}
                    onChange={(e) => setSendForm({...sendForm, memo: e.target.value})}
                    placeholder="Descripción de la transacción"
                  />
                </div>
                
                <button 
                  type="submit" 
                  className="send-button"
                  disabled={
                    isLoading || 
                    !sendForm.toAddress || 
                    !sendForm.amount ||
                    !genesisState.exists ||
                    !(walletDisplayState?.canSendTransactions ?? (genesisStateManager ? genesisStateManager.isOperationAllowed('send_transaction') : false))
                  }
                  title={!genesisState.exists ? 'Requiere blockchain activa' : ''}
                >
                  {isLoading ? (loadingMessage || 'Enviando...') : 'Enviar Transacción'}
                </button>
                
                {!genesisState.exists && (
                  <div style={{ marginTop: '10px', fontSize: '12px', color: '#dc3545' }}>
                    ⚠️ Las transacciones requieren que la blockchain esté inicializada
                  </div>
                )}
              </form>
            </div>
          </div>
        );
      case 'receive':
        return (
          <div className="tab-content">
            <div className="receive-container">
              <h3>Recibir PRGLD</h3>
              <p>Comparte esta dirección para recibir tokens:</p>
              
              <div className="address-display">
                <div className="address-text">{wallet.address}</div>
                <button 
                  onClick={() => navigator.clipboard.writeText(wallet.address)}
                  className="copy-button"
                >
                  📋 Copiar
                </button>
              </div>
              
              <div className="qr-placeholder">
                <div className="qr-code">
                  <p>📱 Código QR</p>
                  <p>(Próximamente)</p>
                </div>
              </div>
              
              <div className="receive-instructions">
                <h4>Instrucciones:</h4>
                <ul>
                  <li>Comparte tu dirección con quien te va a enviar tokens</li>
                  <li>Las transacciones aparecerán automáticamente en tu historial</li>
                  <li>No necesitas estar conectado para recibir tokens</li>
                </ul>
              </div>
            </div>
          </div>
        );
      case 'history':
        return (
          <div className="tab-content">
            <div className="history-container">
              <h3>Historial de Transacciones</h3>
              
              {isLoading ? (
                <p>Cargando transacciones...</p>
              ) : transactions.length === 0 ? (
                <div className="no-transactions">
                  <p>No hay transacciones aún</p>
                  <p>Las transacciones aparecerán aquí una vez que envíes o recibas tokens</p>
                </div>
              ) : (
                <div className="transactions-table">
                  <div className="table-header">
                    <span>Tipo</span>
                    <span>Cantidad</span>
                    <span>Dirección</span>
                    <span>Fecha</span>
                    <span>Estado</span>
                  </div>
                  
                  {transactions.map((tx, index) => (
                    <div key={index} className="table-row">
                      <span className="tx-type">
                        {tx.direction === 'sent' ? '📤 Enviado' : '📥 Recibido'}
                      </span>
                      <span className={`tx-amount ${tx.direction}`}>
                        {tx.direction === 'sent' ? '-' : '+'}{tx.amount} PRGLD
                      </span>
                      <span className="tx-address">
                        {tx.direction === 'sent' ? tx.to : tx.from}
                      </span>
                      <span className="tx-date">
                        {new Date(tx.timestamp).toLocaleString()}
                      </span>
                      <span className="tx-status">
                        {tx.status === 'confirmed' ? '✅ Confirmado' : '⏳ Pendiente'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              
              <button 
                onClick={loadWalletData}
                className="refresh-button"
                disabled={isLoading}
              >
                🔄 Actualizar
              </button>
            </div>
          </div>
        );
      case 'mining':
        return (
          <div className="tab-content">
            <div className="mining-container">
              <h3>Minería PoAIP (Proof-of-AI-Participation)</h3>
              
              <div className="mining-status">
                <div className="status-indicator">
                  <span className={`status-dot ${miningStatus.isActive ? 'active' : 'inactive'}`}></span>
                  <span>{miningStatus.isActive ? 'Minando Activo' : 'Minado Inactivo'}</span>
                  {miningStatus.currentModel && (
                    <span className="current-model">con {miningStatus.currentModel.name}</span>
                  )}
                </div>
              </div>
              
              <div className="mining-info">
                <h4>¿Qué es la Minería PoAIP?</h4>
                <ul>
                  <li>Solo las IAs pueden participar en el consenso</li>
                  <li>Recompensas equitativas independientes del poder económico</li>
                  <li>Requiere hardware gaming: 4GB VRAM, 4 cores CPU, 8GB RAM</li>
                  <li>Modelos IA certificados: Gemma 3 4B, Mistral 3B, Qwen 3 4B</li>
                </ul>
                
                {bootstrapState.mode !== 'network' && (
                  <div className="bootstrap-mining-info">
                    <h5>🚀 Modo Bootstrap P2P</h5>
                    <p>
                      {bootstrapState.mode === 'pioneer' ? 
                        'Selecciona un modelo e inicia la minería para comenzar el descubrimiento P2P automático.' :
                        'El sistema está estableciendo la red blockchain automáticamente.'
                      }
                    </p>
                  </div>
                )}
              </div>
              
              <div className="models-section">
                <h4>Modelos IA Disponibles</h4>
                <div className="models-grid">
                  {availableModels.map(model => (
                    <div key={model.id} className="model-card">
                      <div className="model-header">
                        <h5>{model.name}</h5>
                        <span className={`model-status ${model.isInstalled ? 'installed' : 'not-installed'}`}>
                          {model.isInstalled ? '✅ Instalado' : '📥 No instalado'}
                        </span>
                      </div>
                      <p className="model-description">{model.description}</p>
                      <div className="model-specs">
                        <small>Tamaño: {model.size} | VRAM: {model.requirements.vram}</small>
                      </div>
                      
                      {downloadProgress[model.id] && (
                        <div className="download-progress">
                          <div className="progress-bar">
                            <div 
                              className="progress-fill" 
                              style={{width: `${downloadProgress[model.id].progress}%`}}
                            ></div>
                          </div>
                          <small>{downloadProgress[model.id].progress}% descargado</small>
                        </div>
                      )}
                      
                      <div className="model-actions">
                        {!model.isInstalled ? (
                          <button 
                            className="download-model-button"
                            onClick={() => handleDownloadModel(model.id)}
                            disabled={downloadProgress[model.id]?.status === 'downloading'}
                          >
                            {downloadProgress[model.id]?.status === 'downloading' ? 'Descargando...' : '📥 Descargar'}
                          </button>
                        ) : (
                          <button 
                            className={`select-model-button ${miningStatus.selectedModel === model.id ? 'selected' : ''}`}
                            onClick={() => setMiningStatus({...miningStatus, selectedModel: model.id})}
                            disabled={miningStatus.isActive}
                          >
                            {miningStatus.selectedModel === model.id ? '✅ Seleccionado' : 'Seleccionar'}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="mining-controls">
                {!miningStatus.isActive ? (
                  <button 
                    className="start-mining-button"
                    disabled={!miningStatus.selectedModel || isLoading}
                    onClick={handleStartMining}
                  >
                    {isLoading ? 'Iniciando...' : 
                     bootstrapState.mode === 'pioneer' ? '🚀 Iniciar Bootstrap P2P' : 
                     '🚀 Iniciar Minería'}
                  </button>
                ) : (
                  <button 
                    className="stop-mining-button"
                    onClick={handleStopMining}
                    disabled={isLoading || (bootstrapState.mode !== 'network' && bootstrapState.mode !== 'pioneer')}
                  >
                    {isLoading ? 'Deteniendo...' : '⏹️ Detener Minería'}
                  </button>
                )}
                
                {bootstrapState.mode !== 'network' && bootstrapState.mode !== 'pioneer' && (
                  <div className="bootstrap-mining-notice">
                    <p>⏳ Minería disponible después de establecer la red blockchain</p>
                  </div>
                )}
              </div>
              
              <div className="mining-stats">
                <h4>Estadísticas de Minería</h4>
                <div className="stats-grid">
                  <div className="stat-item">
                    <span>Bloques Validados:</span>
                    <span>{miningStatus.stats.blocksValidated}</span>
                  </div>
                  <div className="stat-item">
                    <span>Recompensas Ganadas:</span>
                    <span>{miningStatus.stats.rewardsEarned.toFixed(2)} PRGLD</span>
                  </div>
                  <div className="stat-item">
                    <span>Challenges Procesados:</span>
                    <span>{miningStatus.stats.challengesProcessed}</span>
                  </div>
                  <div className="stat-item">
                    <span>Tasa de Éxito:</span>
                    <span>{miningStatus.stats.successRate.toFixed(1)}%</span>
                  </div>
                  <div className="stat-item">
                    <span>Tiempo Activo:</span>
                    <span>{miningStatus.stats.uptimeFormatted || '00:00:00'}</span>
                  </div>
                  <div className="stat-item">
                    <span>Reputación:</span>
                    <span>{miningStatus.stats.reputation}%</span>
                  </div>
                </div>
              </div>
              
              {miningRewards && (
                <div className="mining-rewards">
                  <h4>Estimación de Recompensas</h4>
                  <div className="rewards-grid">
                    <div className="reward-item">
                      <span>Por Hora:</span>
                      <span>{miningRewards.hourly} PRGLD</span>
                    </div>
                    <div className="reward-item">
                      <span>Por Día:</span>
                      <span>{miningRewards.daily} PRGLD</span>
                    </div>
                    <div className="reward-item">
                      <span>Por Semana:</span>
                      <span>{miningRewards.weekly} PRGLD</span>
                    </div>
                    <div className="reward-item">
                      <span>Por Mes:</span>
                      <span>{miningRewards.monthly} PRGLD</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      case 'addressbook':
        return (
          <div className="tab-content">
            <h2>Libreta de Direcciones</h2>
            <p>Libreta de direcciones - Próximamente</p>
          </div>
        );
      case 'privacy':
        return (
          <div className="tab-content">
            <h2>Configuración de Privacidad</h2>
            <p>Configuración de privacidad - Próximamente</p>
          </div>
        );
      case 'security':
        return (
          <div className="tab-content">
            <h2>Configuración de Seguridad</h2>
            <p>Configuración de seguridad - Próximamente</p>
          </div>
        );
      default:
        return (
          <div className="tab-content">
            <h2>Resumen de la Cartera</h2>
            <p>Contenido por defecto</p>
          </div>
        );
    }
  };

  return (
    <div className="dashboard">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>PlayerGold</h2>
          <p>Wallet Desktop v1.0</p>
        </div>
        
        <nav className="sidebar-nav">
          {navigationItems.map(item => (
            <div
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <span className="icon">{item.icon}</span>
              {item.label}
            </div>
          ))}
        </nav>
        
        <div style={{ padding: '20px', borderTop: '1px solid #e9ecef', fontSize: '12px', color: '#666' }}>
          <p>Hecho por gamers para gamers</p>
          <p>Consenso PoAIP - Gestionado por IA</p>
        </div>
      </div>

      <div className="main-content">
        <div className="content-header">
          <h1>{navigationItems.find(item => item.id === activeTab)?.label || 'Dashboard'}</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            {/* Bootstrap Status Indicator */}
            {bootstrapState.mode !== 'network' && (
              <div style={{ fontSize: '12px', color: '#e74c3c', fontWeight: '600' }}>
                Bootstrap: <span style={{ color: '#f39c12' }}>●</span> {
                  bootstrapState.mode === 'pioneer' ? 'Modo Pionero' :
                  bootstrapState.mode === 'discovery' ? 'Descubriendo Peers' :
                  bootstrapState.mode === 'genesis' ? 'Creando Génesis' : 'Activo'
                }
              </div>
            )}
            
            {/* Genesis State Indicator */}
            <div style={{ fontSize: '12px', color: '#666' }}>
              Génesis: <span style={{ color: genesisState.exists ? '#28a745' : '#dc3545' }}>●</span> 
              {genesisState.exists ? 'Activo' : 'No inicializado'}
            </div>
            
            <div style={{ fontSize: '12px', color: '#666' }}>
              Red: <span style={{ color: (bootstrapState.mode === 'network' && genesisState.exists) ? '#28a745' : '#f39c12' }}>●</span> 
              {(bootstrapState.mode === 'network' && genesisState.exists) ? 'Conectado' : 'Estableciendo'}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              Sincronización: {(bootstrapState.mode === 'network' && genesisState.exists) ? '100%' : 'En progreso'}
            </div>
            
            {/* Status Message from WalletStateProvider */}
            {walletDisplayState?.statusMessage && (
              <div style={{ fontSize: '11px', color: '#666', fontStyle: 'italic' }}>
                {walletDisplayState.statusMessage}
              </div>
            )}
          </div>
        </div>
        
        <div className="content-body">
          {/* Blockchain Node Status - Always visible */}
          <BlockchainNodeStatus />
          
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;