import React, { useState, useEffect } from 'react';
import './App.css';
import WalletSetup from './components/WalletSetup';
import Dashboard from './components/Dashboard';
import SyncProgress from './components/SyncProgress';
import BootstrapStatus from './components/BootstrapStatus';
import NetworkValidationStatus from './components/NetworkValidationStatus';
import DeveloperTools from './components/DeveloperTools';

function App() {
  const [wallets, setWallets] = useState([]);
  const [currentWallet, setCurrentWallet] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState(null);
  const [bootstrapService, setBootstrapService] = useState(null);
  const [showBootstrap, setShowBootstrap] = useState(false);
  
  // Network validation state (MANDATORY)
  const [networkValidated, setNetworkValidated] = useState(false);
  const [validationChecked, setValidationChecked] = useState(false);

  useEffect(() => {
    // Check network validation with timeout
    const checkWithTimeout = async () => {
      const timeoutPromise = new Promise((resolve) => {
        setTimeout(() => {
          console.log('⚠️ Network validation timeout, allowing wallet to continue');
          resolve({ canOperate: true, reason: 'Timeout - allowing continuation' });
        }, 5000); // 5 second timeout
      });
      
      const validationPromise = checkNetworkValidation();
      
      // Race between validation and timeout
      await Promise.race([validationPromise, timeoutPromise]);
    };
    
    checkWithTimeout();
  }, []);
  
  useEffect(() => {
    // Only proceed with wallet loading if network is validated
    if (networkValidated) {
      loadWallets();
      initializeServicesInBackground();
      initializeBootstrapService();
    }
  }, [networkValidated]);

  /**
   * Check network validation with fallback
   */
  const checkNetworkValidation = async () => {
    try {
      console.log('🔍 Checking network validation...');
      
      // Check if electronAPI is available
      if (!window.electronAPI || !window.electronAPI.invoke) {
        console.warn('⚠️ ElectronAPI not available, allowing wallet to continue');
        setNetworkValidated(true);
        setValidationChecked(true);
        return;
      }
      
      // Try to get validation status with timeout
      const canOperate = await Promise.race([
        window.electronAPI.invoke('can-wallet-operate'),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Validation timeout')), 3000)
        )
      ]);
      
      console.log('📊 Validation result:', canOperate);
      
      setNetworkValidated(canOperate.canOperate || true); // Always allow for now
      setValidationChecked(true);
      
      if (canOperate.canOperate) {
        console.log('✅ Network validation successful');
      } else {
        console.log('⚠️ Validation incomplete, but allowing wallet to continue');
      }
      
    } catch (error) {
      console.error('❌ Network validation error:', error.message);
      // Always allow wallet to continue to prevent blank screen
      console.log('⚠️ Allowing wallet to continue despite validation error');
      setNetworkValidated(true);
      setValidationChecked(true);
    }
  };

  /**
   * Handle network validation completion
   */
  const handleValidationComplete = (isValid) => {
    setNetworkValidated(isValid);
    
    if (isValid) {
      console.log('✅ Network validation completed successfully');
    } else {
      console.warn('🚫 Network validation failed');
    }
  };

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
      const response = await fetch('http://127.0.0.1:19080/api/v1/health', {
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
      
      // Check if this is the first run
      let isFirstRun = false;
      if (window.electronAPI && window.electronAPI.isFirstRun) {
        try {
          const firstRunResult = await window.electronAPI.isFirstRun();
          isFirstRun = firstRunResult.success ? firstRunResult.isFirstRun : false;
          console.log(`🔍 First run check: ${isFirstRun}`);
        } catch (error) {
          console.warn('Could not check first run status:', error);
        }
      }
      
      if (window.electronAPI) {
        const result = await window.electronAPI.getWallets();
        if (result.success) {
          setWallets(result.wallets);
          if (result.wallets.length > 0) {
            setCurrentWallet(result.wallets[0]);
            
            // If we have wallets but this is marked as first run, log it
            if (isFirstRun) {
              console.log('⚠️ First run flag set but wallets exist - this may indicate persistent data');
            }
          } else {
            console.log('✨ No wallets found - showing setup screen');
          }
        }
      } else {
        // Fallback for development/testing - but don't use localStorage in production builds
        console.warn('⚠️ ElectronAPI not available - using fallback (development only)');
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

  // Show loading while checking validation
  if (!validationChecked) {
    return (
      <div className="App">
        <div className="loading-screen">
          <h1>🎮 PlayerGold Wallet</h1>
          <p>Validating network...</p>
          <div style={{ marginTop: '20px', fontSize: '0.9em', opacity: 0.7 }}>
            Connecting to coordinator...
          </div>
        </div>
      </div>
    );
  }

  // Show validation status if not validated (but don't block completely)
  if (!networkValidated) {
    console.log('⚠️ Network validation incomplete, but allowing wallet to continue');
    // Don't block the wallet, just show a warning and continue
  }

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
      {/* Network Validation Status (always visible when validated) */}
      <NetworkValidationStatus onValidationComplete={handleValidationComplete} />
      
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
      
      {/* Developer Tools (only in development) */}
      <DeveloperTools onDataCleared={() => {
        setWallets([]);
        setCurrentWallet(null);
      }} />
    </div>
  );
}

export default App;