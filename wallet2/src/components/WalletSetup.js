import React, { useState } from 'react';
import CreateWallet from './CreateWallet';
import ImportWallet from './ImportWallet';

const WalletSetup = ({ onWalletCreated, onWalletImported }) => {
  const [mode, setMode] = useState('menu'); // 'menu', 'create', 'import'

  const handleBack = () => {
    setMode('menu');
  };

  const handleWalletCreated = (wallet) => {
    onWalletCreated(wallet);
  };

  const handleWalletImported = (wallet) => {
    onWalletImported(wallet);
  };

  if (mode === 'create') {
    return (
      <CreateWallet 
        onBack={handleBack}
        onWalletCreated={handleWalletCreated}
      />
    );
  }

  if (mode === 'import') {
    return (
      <ImportWallet 
        onBack={handleBack}
        onWalletImported={handleWalletImported}
      />
    );
  }

  return (
    <div className="wallet-setup">
      <div className="setup-container">
        <div className="setup-header">
          <h1>PlayerGold Wallet</h1>
          <p>Hecho por gamers para gamers, totalmente libre, democrático y sin censura</p>
        </div>
        
        <div className="setup-options">
          <button 
            className="setup-button"
            onClick={() => setMode('create')}
          >
            <span>🆕</span>
            Crear Nueva Cartera
          </button>
          
          <button 
            className="setup-button secondary"
            onClick={() => setMode('import')}
          >
            <span>📥</span>
            Importar Cartera Existente
          </button>
        </div>
        
        <div style={{ marginTop: '30px', textAlign: 'center' }}>
          <p style={{ fontSize: '12px', color: '#666' }}>
            PlayerGold ($PRGLD) - Consenso PoAIP gestionado por IA
          </p>
        </div>
      </div>
    </div>
  );
};

export default WalletSetup;