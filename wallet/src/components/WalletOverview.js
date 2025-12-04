import React, { useState, useEffect } from 'react';
import { WalletService } from '../services/WalletService';
import { NetworkService } from '../services/NetworkService';
import { TransactionService } from '../services/TransactionService';

const WalletOverview = ({ wallet }) => {
  const [balance, setBalance] = useState({
    confirmed: '0.00',
    pending: '0.00',
    total: '0.00'
  });
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [networkStatus, setNetworkStatus] = useState({
    connected: false,
    syncProgress: 0,
    blockHeight: 0,
    tps: 0,
    connectedPeers: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (wallet) {
      loadWalletData();
      
      // Refresh data every 30 seconds
      const interval = setInterval(loadWalletData, 30000);
      
      // Listen to network events
      NetworkService.on('connected', handleNetworkConnected);
      NetworkService.on('disconnected', handleNetworkDisconnected);
      NetworkService.on('statsUpdated', handleStatsUpdated);
      
      return () => {
        clearInterval(interval);
        NetworkService.off('connected', handleNetworkConnected);
        NetworkService.off('disconnected', handleNetworkDisconnected);
        NetworkService.off('statsUpdated', handleStatsUpdated);
      };
    }
  }, [wallet]);

  const loadWalletData = async () => {
    if (!wallet) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Load balance
      const balanceResult = await WalletService.getWalletBalance(wallet.id);
      if (balanceResult.success) {
        setBalance({
          confirmed: balanceResult.balance || '0.00',
          pending: balanceResult.pending || '0.00',
          total: (parseFloat(balanceResult.balance || '0') + parseFloat(balanceResult.pending || '0')).toString()
        });
      }

      // Load recent transactions
      const historyResult = await WalletService.getTransactionHistory(wallet.id, 5, 0);
      if (historyResult.success) {
        setRecentTransactions(historyResult.transactions || []);
      }

      // Get network status
      const status = NetworkService.getConnectionStatus();
      setNetworkStatus(status);
      
    } catch (error) {
      setError('Error al cargar datos de la cartera');
    } finally {
      setLoading(false);
    }
  };

  const handleNetworkConnected = (stats) => {
    setNetworkStatus(prev => ({ ...prev, connected: true, ...stats }));
  };

  const handleNetworkDisconnected = () => {
    setNetworkStatus(prev => ({ ...prev, connected: false }));
  };

  const handleStatsUpdated = (stats) => {
    setNetworkStatus(prev => ({ ...prev, ...stats }));
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      // TODO: Add toast notification
    } catch (error) {
      console.error('Error copying to clipboard:', error);
    }
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.substring(0, 8)}...${address.substring(address.length - 8)}`;
  };

  const formatAmount = (amount) => {
    return TransactionService.formatAmount(amount);
  };

  const getTransactionType = (tx) => {
    return tx.to_address === wallet.address ? 'received' : 'sent';
  };

  const getTransactionIcon = (tx) => {
    return getTransactionType(tx) === 'received' ? '📥' : '📤';
  };

  return (
    <div className="wallet-overview">
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={loadWalletData} className="retry-button">
            Reintentar
          </button>
        </div>
      )}

      {/* Main Wallet Card */}
      <div className="wallet-card">
        <div className="wallet-info">
          <h3>{wallet.name}</h3>
          <div 
            className="wallet-address"
            onClick={() => copyToClipboard(wallet.address)}
            style={{ cursor: 'pointer' }}
            title="Click para copiar dirección completa"
          >
            {formatAddress(wallet.address)}
          </div>
          <div className="wallet-balance">
            {loading ? (
              <span className="loading-spinner"></span>
            ) : (
              formatAmount(balance.total)
            )}
          </div>
          <div className="balance-label">PRGLD</div>
          <div className="network-status">
            <span className={`status-indicator ${networkStatus.connected ? 'connected' : 'disconnected'}`}>
              {networkStatus.connected ? '🟢' : '🔴'}
            </span>
            <span className="status-text">
              {networkStatus.connected ? 'Conectado' : 'Desconectado'}
            </span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <div className="action-grid">
          <button className="action-button">
            <span className="action-icon">📤</span>
            <span className="action-label">Enviar</span>
          </button>
          <button className="action-button">
            <span className="action-icon">📥</span>
            <span className="action-label">Recibir</span>
          </button>
          <button className="action-button">
            <span className="action-icon">⛏️</span>
            <span className="action-label">Minar</span>
          </button>
          <button className="action-button">
            <span className="action-icon">🔥</span>
            <span className="action-label">Quemar</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <div className="stat-value">{formatAmount(balance.confirmed)}</div>
            <div className="stat-label">Balance Confirmado</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div className="stat-content">
            <div className="stat-value">{formatAmount(balance.pending)}</div>
            <div className="stat-label">Balance Pendiente</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{recentTransactions.length}</div>
            <div className="stat-label">Transacciones Recientes</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🌐</div>
          <div className="stat-content">
            <div className="stat-value">{networkStatus.connectedPeers || 0}</div>
            <div className="stat-label">Peers Conectados</div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="recent-activity">
        <h3>Actividad Reciente</h3>
        <div className="activity-list">
          {loading ? (
            <div className="loading-transactions">
              <span className="loading-spinner"></span>
              Cargando transacciones...
            </div>
          ) : recentTransactions.length > 0 ? (
            <div className="transactions-preview">
              {recentTransactions.slice(0, 3).map((tx, index) => (
                <div key={tx.hash || index} className="transaction-preview">
                  <div className="tx-icon">
                    {getTransactionIcon(tx)}
                  </div>
                  <div className="tx-details">
                    <div className="tx-type">
                      {getTransactionType(tx) === 'received' ? 'Recibido' : 'Enviado'}
                    </div>
                    <div className="tx-address">
                      {formatAddress(
                        getTransactionType(tx) === 'received' 
                          ? tx.from_address 
                          : tx.to_address
                      )}
                    </div>
                    <div className="tx-date">
                      {new Date(tx.timestamp * 1000).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="tx-amount">
                    <span className={getTransactionType(tx) === 'received' ? 'positive' : 'negative'}>
                      {getTransactionType(tx) === 'received' ? '+' : '-'}
                      {formatAmount(tx.amount)} PRGLD
                    </span>
                  </div>
                </div>
              ))}
              <button className="view-all-button">
                Ver todas las transacciones
              </button>
            </div>
          ) : (
            <div className="activity-empty">
              <div className="empty-icon">📭</div>
              <p>No hay transacciones recientes</p>
              <p style={{ fontSize: '14px', color: '#666' }}>
                Tus transacciones aparecerán aquí una vez que empieces a usar tu cartera
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Network Info */}
      <div className="network-info">
        <h3>Estado de la Red</h3>
        <div className="network-stats">
          <div className="network-stat">
            <span className="network-label">Altura del Bloque:</span>
            <span className="network-value">#{networkStatus.blockHeight || 0}</span>
          </div>
          <div className="network-stat">
            <span className="network-label">TPS Actual:</span>
            <span className="network-value">{networkStatus.tps || 0}</span>
          </div>
          <div className="network-stat">
            <span className="network-label">Peers Conectados:</span>
            <span className="network-value">{networkStatus.connectedPeers || 0}</span>
          </div>
          <div className="network-stat">
            <span className="network-label">Sincronización:</span>
            <span className="network-value">{networkStatus.syncProgress || 0}%</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        .wallet-overview {
          max-width: 1200px;
        }

        .quick-actions {
          margin-bottom: 30px;
        }

        .action-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 15px;
        }

        .action-button {
          background: white;
          border: 2px solid #e9ecef;
          border-radius: 12px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.3s;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }

        .action-button:hover {
          border-color: #667eea;
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }

        .action-icon {
          font-size: 24px;
        }

        .action-label {
          font-size: 14px;
          font-weight: 500;
          color: #333;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .stat-card {
          background: white;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 15px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        .stat-icon {
          font-size: 32px;
          width: 60px;
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f8f9fa;
          border-radius: 12px;
        }

        .stat-content {
          flex: 1;
        }

        .stat-value {
          font-size: 24px;
          font-weight: bold;
          color: #333;
          margin-bottom: 4px;
        }

        .stat-label {
          font-size: 14px;
          color: #666;
        }

        .recent-activity {
          background: white;
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 30px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        .recent-activity h3 {
          margin-bottom: 20px;
          color: #333;
        }

        .activity-empty {
          text-align: center;
          padding: 40px 20px;
          color: #666;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 15px;
        }

        .network-info {
          background: white;
          border-radius: 12px;
          padding: 25px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        .network-info h3 {
          margin-bottom: 20px;
          color: #333;
        }

        .network-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }

        .network-stat {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid #f0f0f0;
        }

        .network-stat:last-child {
          border-bottom: none;
        }

        .network-label {
          font-size: 14px;
          color: #666;
        }

        .network-value {
          font-size: 14px;
          font-weight: 600;
          color: #333;
        }

        @media (max-width: 768px) {
          .action-grid {
            grid-template-columns: repeat(2, 1fr);
          }
          
          .stats-grid {
            grid-template-columns: 1fr;
          }
          
          .network-stats {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default WalletOverview;