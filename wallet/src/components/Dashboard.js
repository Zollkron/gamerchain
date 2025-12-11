import React, { useState, useEffect } from 'react';

const Dashboard = ({ wallet, wallets, onWalletChange, onWalletsUpdate }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [balance, setBalance] = useState('0.00');
  const [transactions, setTransactions] = useState([]);
  const [networkStatus, setNetworkStatus] = useState({ connected: false, synced: false });
  const [isLoading, setIsLoading] = useState(false);
  
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
    downloadProgress: 0,
    isDownloading: false
  });

  // Load wallet data on mount and wallet change
  useEffect(() => {
    if (wallet) {
      loadWalletData();
    }
  }, [wallet]);

  const loadWalletData = async () => {
    if (!wallet || !window.electronAPI) return;
    
    setIsLoading(true);
    try {
      // Load balance
      const balanceResult = await window.electronAPI.getWalletBalance(wallet.id);
      if (balanceResult.success) {
        setBalance(balanceResult.balance);
      }
      
      // Load transaction history
      const historyResult = await window.electronAPI.getTransactionHistory(wallet.id, 20, 0);
      if (historyResult.success) {
        setTransactions(historyResult.transactions);
      }
      
      // Get network status
      const statusResult = await window.electronAPI.getNetworkStatus();
      if (statusResult.success) {
        setNetworkStatus({
          connected: true,
          synced: statusResult.status.syncStatus === 'synced'
        });
      }
    } catch (error) {
      console.error('Error loading wallet data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendTransaction = async (e) => {
    e.preventDefault();
    if (!window.electronAPI || !wallet) return;
    
    setIsLoading(true);
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
        alert(`Error al enviar transacción: ${result.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestFaucet = async () => {
    if (!window.electronAPI || !wallet) return;
    
    setIsLoading(true);
    try {
      const result = await window.electronAPI.requestFaucetTokens(wallet.id, 1000);
      if (result.success) {
        alert(`¡Tokens solicitados exitosamente!\nCantidad: ${result.amount} PRGLD\nID: ${result.transactionId}`);
        setTimeout(() => loadWalletData(), 3000); // Refresh after 3 seconds
      } else {
        alert(`Error al solicitar tokens: ${result.error}`);
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
            <div className="balance-card">
              <h3>Balance Total</h3>
              <div className="balance-amount">
                {isLoading ? 'Cargando...' : `${balance} PRGLD`}
              </div>
              <button 
                className="faucet-button" 
                onClick={handleRequestFaucet}
                disabled={isLoading}
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
              {transactions.length === 0 ? (
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
                  disabled={isLoading || !sendForm.toAddress || !sendForm.amount}
                >
                  {isLoading ? 'Enviando...' : 'Enviar Transacción'}
                </button>
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
              </div>
              
              <div className="model-selection">
                <h4>Seleccionar Modelo IA</h4>
                <select 
                  value={miningStatus.selectedModel}
                  onChange={(e) => setMiningStatus({...miningStatus, selectedModel: e.target.value})}
                  disabled={miningStatus.isActive}
                >
                  <option value="">Seleccionar modelo...</option>
                  <option value="gemma-3-4b">Gemma 3 4B (Recomendado)</option>
                  <option value="mistral-3b">Mistral 3B</option>
                  <option value="qwen-3-4b">Qwen 3 4B</option>
                </select>
              </div>
              
              {miningStatus.isDownloading && (
                <div className="download-progress">
                  <h4>Descargando Modelo IA...</h4>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{width: `${miningStatus.downloadProgress}%`}}
                    ></div>
                  </div>
                  <p>{miningStatus.downloadProgress}% completado</p>
                </div>
              )}
              
              <div className="mining-controls">
                {!miningStatus.isActive ? (
                  <button 
                    className="start-mining-button"
                    disabled={!miningStatus.selectedModel || miningStatus.isDownloading}
                    onClick={() => {
                      alert('Funcionalidad de minería en desarrollo.\nSe integrará con los nodos IA del testnet.');
                    }}
                  >
                    🚀 Iniciar Minería
                  </button>
                ) : (
                  <button 
                    className="stop-mining-button"
                    onClick={() => setMiningStatus({...miningStatus, isActive: false})}
                  >
                    ⏹️ Detener Minería
                  </button>
                )}
              </div>
              
              <div className="mining-stats">
                <h4>Estadísticas de Minería</h4>
                <div className="stats-grid">
                  <div className="stat-item">
                    <span>Bloques Validados:</span>
                    <span>0</span>
                  </div>
                  <div className="stat-item">
                    <span>Recompensas Ganadas:</span>
                    <span>0.00 PRGLD</span>
                  </div>
                  <div className="stat-item">
                    <span>Tiempo Activo:</span>
                    <span>00:00:00</span>
                  </div>
                  <div className="stat-item">
                    <span>Reputación:</span>
                    <span>100%</span>
                  </div>
                </div>
              </div>
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
            <div style={{ fontSize: '12px', color: '#666' }}>
              Red: <span style={{ color: '#28a745' }}>●</span> Conectado
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              Sincronización: 100%
            </div>
          </div>
        </div>
        
        <div className="content-body">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;