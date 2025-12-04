import React, { useState } from 'react';
import WalletOverview from './WalletOverview';
import WalletManager from './WalletManager';

const Dashboard = ({ wallet, wallets, onWalletChange, onWalletsUpdate }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const navigationItems = [
    { id: 'overview', label: 'Resumen', icon: '🏠' },
    { id: 'send', label: 'Enviar', icon: '📤' },
    { id: 'receive', label: 'Recibir', icon: '📥' },
    { id: 'history', label: 'Historial', icon: '📋' },
    { id: 'mining', label: 'Minería', icon: '⛏️' },
    { id: 'wallets', label: 'Carteras', icon: '👛' },
    { id: 'settings', label: 'Configuración', icon: '⚙️' }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <WalletOverview wallet={wallet} />;
      case 'wallets':
        return (
          <WalletManager 
            wallets={wallets}
            currentWallet={wallet}
            onWalletChange={onWalletChange}
            onWalletsUpdate={onWalletsUpdate}
          />
        );
      case 'send':
        return <div className="content-placeholder">Funcionalidad de Envío - Próximamente</div>;
      case 'receive':
        return <div className="content-placeholder">Funcionalidad de Recepción - Próximamente</div>;
      case 'history':
        return <div className="content-placeholder">Historial de Transacciones - Próximamente</div>;
      case 'mining':
        return <div className="content-placeholder">Minería con IA - Próximamente</div>;
      case 'settings':
        return <div className="content-placeholder">Configuración - Próximamente</div>;
      default:
        return <WalletOverview wallet={wallet} />;
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