import React, { useState } from 'react';

const Dashboard = ({ wallet, wallets, onWalletChange, onWalletsUpdate }) => {
  const [activeTab, setActiveTab] = useState('overview');

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
            <h2>Resumen de la Cartera</h2>
            <div className="wallet-info">
              <p><strong>Nombre:</strong> {wallet.name || 'Sin nombre'}</p>
              <p><strong>Dirección:</strong> {wallet.address || 'No disponible'}</p>
              <p><strong>Balance:</strong> 0.00 PRGLD</p>
            </div>
            <button onClick={() => {
              localStorage.removeItem('playerGoldWallets');
              window.location.reload();
            }}>
              Reset Wallet (para testing)
            </button>
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
            <h2>Enviar Transacción</h2>
            <p>Funcionalidad de envío - Próximamente</p>
          </div>
        );
      case 'receive':
        return (
          <div className="tab-content">
            <h2>Recibir Transacción</h2>
            <p>Funcionalidad de recepción - Próximamente</p>
          </div>
        );
      case 'history':
        return (
          <div className="tab-content">
            <h2>Historial de Transacciones</h2>
            <p>Historial - Próximamente</p>
          </div>
        );
      case 'mining':
        return (
          <div className="tab-content">
            <h2>Minería PoAIP</h2>
            <p>Funcionalidad de minería - Próximamente</p>
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