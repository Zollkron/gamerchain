import React, { useState } from 'react';
import WalletOverview from './WalletOverview';
import WalletManager from './WalletManager';
import SendTransaction from './SendTransaction';
import ReceiveTransaction from './ReceiveTransaction';
import TransactionHistory from './TransactionHistory';
import MiningTab from './MiningTab';

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
        return (
          <SendTransaction 
            wallet={wallet}
            onTransactionSent={handleTransactionSent}
          />
        );
      case 'receive':
        return <ReceiveTransaction wallet={wallet} />;
      case 'history':
        return <TransactionHistory wallet={wallet} />;
      case 'mining':
        return <MiningTab wallet={wallet} />;
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