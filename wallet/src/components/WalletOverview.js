import React from 'react';

const WalletOverview = ({ wallet }) => {
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // TODO: Add toast notification
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.substring(0, 8)}...${address.substring(address.length - 8)}`;
  };

  return (
    <div className="wallet-overview">
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
            {wallet.address}
          </div>
          <div className="wallet-balance">
            {wallet.balance || '0.00'}
          </div>
          <div className="balance-label">PRGLD</div>
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
            <div className="stat-value">0.00</div>
            <div className="stat-label">Balance Total</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">0</div>
            <div className="stat-label">Transacciones</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">⭐</div>
          <div className="stat-content">
            <div className="stat-value">0</div>
            <div className="stat-label">Reputación</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🏆</div>
          <div className="stat-content">
            <div className="stat-value">0.00</div>
            <div className="stat-label">Recompensas</div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="recent-activity">
        <h3>Actividad Reciente</h3>
        <div className="activity-list">
          <div className="activity-empty">
            <div className="empty-icon">📭</div>
            <p>No hay transacciones recientes</p>
            <p style={{ fontSize: '14px', color: '#666' }}>
              Tus transacciones aparecerán aquí una vez que empieces a usar tu cartera
            </p>
          </div>
        </div>
      </div>

      {/* Network Info */}
      <div className="network-info">
        <h3>Estado de la Red</h3>
        <div className="network-stats">
          <div className="network-stat">
            <span className="network-label">Nodos IA Activos:</span>
            <span className="network-value">156</span>
          </div>
          <div className="network-stat">
            <span className="network-label">TPS Actual:</span>
            <span className="network-value">87</span>
          </div>
          <div className="network-stat">
            <span className="network-label">Último Bloque:</span>
            <span className="network-value">#12,847</span>
          </div>
          <div className="network-stat">
            <span className="network-label">Supply Circulante:</span>
            <span className="network-value">9,876,543 PRGLD</span>
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