import React, { useState, useEffect } from 'react';
import './App.css';
import WalletSetup from './components/WalletSetup';
import Dashboard from './components/Dashboard';

function App() {
  const [wallets, setWallets] = useState([]);
  const [currentWallet, setCurrentWallet] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadWallets();
  }, []);

  const loadWallets = async () => {
    try {
      setIsLoading(true);
      if (window.electronAPI) {
        const result = await window.electronAPI.getWallets();
        if (result.success) {
          setWallets(result.wallets);
          if (result.wallets.length > 0) {
            setCurrentWallet(result.wallets[0]);
          }
        }
      } else {
        // Fallback for development/testing
        const savedWallets = localStorage.getItem('playerGoldWallets');
        if (savedWallets) {
          const parsedWallets = JSON.parse(savedWallets);
          setWallets(parsedWallets);
          if (parsedWallets.length > 0) {
            setCurrentWallet(parsedWallets[0]);
          }
        }
      }
    } catch (error) {
      console.error('Error loading wallets:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleWalletCreated = (wallet) => {
    const newWallets = [...wallets, wallet];
    setWallets(newWallets);
    setCurrentWallet(wallet);
    // Also save to localStorage as backup
    localStorage.setItem('playerGoldWallets', JSON.stringify(newWallets));
  };

  const handleWalletImported = (wallet) => {
    const newWallets = [...wallets, wallet];
    setWallets(newWallets);
    setCurrentWallet(wallet);
    // Also save to localStorage as backup
    localStorage.setItem('playerGoldWallets', JSON.stringify(newWallets));
  };

  if (isLoading) {
    return (
      <div className="App">
        <div className="loading-screen">
          <h1>🎮 PlayerGold Wallet</h1>
          <p>Cargando...</p>
        </div>
      </div>
    );
  }

  // If no wallets exist, show setup
  if (wallets.length === 0) {
    return (
      <div className="App">
        <WalletSetup 
          onWalletCreated={handleWalletCreated}
          onWalletImported={handleWalletImported}
        />
      </div>
    );
  }

  const handleWalletChange = (wallet) => {
    setCurrentWallet(wallet);
  };

  const handleWalletsUpdate = () => {
    loadWallets();
  };

  // Show Dashboard when wallets exist
  return (
    <div className="App">
      <Dashboard 
        wallet={currentWallet}
        wallets={wallets}
        onWalletChange={handleWalletChange}
        onWalletsUpdate={handleWalletsUpdate}
      />
    </div>
  );
}

export default App;