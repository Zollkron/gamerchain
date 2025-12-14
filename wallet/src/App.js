import React, { useState, useEffect } from 'react';
import './App.css';
import WalletSetup from './components/WalletSetup';
import Dashboard from './components/Dashboard';
import SyncProgress from './components/SyncProgress';
import BootstrapStatus from './components/BootstrapStatus';

function App() {
  const [wallets, setWallets] = useState([]);
  const [currentWallet, setCurrentWallet] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState(null);
  const [bootstrapService, setBootstrapService] = useState(null);
  const [showBootstrap, setShowBootstrap] = useState(false);

  useEffect(() => {
    // Load wallets directly - no sync needed
    loadWallets();
    
    // Initialize services in background without blocking UI
    initializeServicesInBackground();
    
    // Initialize bootstrap service
    initializeBootstrapService();
  }, []);

  const initializeServicesInBackground = async () => {
    try {
      // Start services in background without waiting
      if (window.electronAPI && window.electronAPI.initializeBlockchainServices) {
        window.electronAPI.initializeBlockchainServices().catch(console.error);
      }
    } catch (error) {
      console.error('Error starting background services:', error);
    }
  };

  const initializeBootstrapService = async () => {
    try {
      if (window.electronAPI && window.electronAPI.getBootstrapService) {
        const service = await window.electronAPI.getBootstrapService();
        setBootstrapService(service);
        
        // Check if we need to show bootstrap UI
        const state = service.getState();
        setShowBootstrap(state.mode !== 'network');
      }
    } catch (error) {
      console.error('Error initializing bootstrap service:', error);
    }
  };

  const handleBootstrapComplete = () => {
    setShowBootstrap(false);
    // Refresh wallets and data after bootstrap completion
    loadWallets();
  };

  const checkServicesAndLoadWallets = async () => {
    try {
      // Quick check if services are running
      const response = await fetch('http://127.0.0.1:18080/api/v1/health', {
        method: 'GET',
        timeout: 3000
      });
      
      if (response.ok) {
        // Services are running, proceed to load wallets
        setIsSyncing(false);
        loadWallets();
      } else {
        // Services not responding
        setSyncError(new Error('Servicios blockchain no disponibles'));
      }
    } catch (error) {
      // Services not available
      setSyncError(new Error('No se puede conectar a los servicios blockchain'));
    }
  };

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

  const handleSyncComplete = () => {
    setIsSyncing(false);
    setSyncError(null);
  };

  const handleSyncError = (error) => {
    setSyncError(error);
    setIsSyncing(false);
  };

  // Show sync progress first
  if (isSyncing) {
    return (
      <div className="App">
        <SyncProgress 
          onSyncComplete={handleSyncComplete}
          onError={handleSyncError}
        />
      </div>
    );
  }

  // Show error if sync failed
  if (syncError) {
    return (
      <div className="App">
        <div className="loading-screen">
          <h1>❌ Error de Conexión</h1>
          <p>No se pudo conectar a la red blockchain</p>
          <p style={{ fontSize: '0.9em', opacity: 0.8, marginTop: '20px' }}>
            {syncError.message}
          </p>
          <button 
            onClick={() => {
              setSyncError(null);
              setIsSyncing(true);
            }}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Reintentar
          </button>
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

  // Show Dashboard when wallets exist
  return (
    <div className="App">
      <Dashboard 
        wallet={currentWallet}
        wallets={wallets}
        onWalletChange={handleWalletChange}
        onWalletsUpdate={handleWalletsUpdate}
      />
      
      {/* Bootstrap Status Overlay */}
      {showBootstrap && bootstrapService && (
        <BootstrapStatus 
          bootstrapService={bootstrapService}
          onBootstrapComplete={handleBootstrapComplete}
        />
      )}
    </div>
  );
}

export default App;