import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import WalletSetup from './components/WalletSetup';
import Dashboard from './components/Dashboard';
import LoadingScreen from './components/LoadingScreen';
import SecurityLogin from './components/SecurityLogin';

function App() {
  const [wallets, setWallets] = useState([]);
  const [currentWallet, setCurrentWallet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    loadWallets();
  }, []);

  const loadWallets = async () => {
    try {
      setLoading(true);
      const result = await window.electronAPI.getWallets();
      
      if (result.success) {
        setWallets(result.wallets);
        if (result.wallets.length > 0) {
          setCurrentWallet(result.wallets[0]);
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error loading wallets: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleWalletCreated = (wallet) => {
    setWallets(prev => [...prev, wallet]);
    setCurrentWallet(wallet);
  };

  const handleWalletImported = (wallet) => {
    setWallets(prev => [...prev, wallet]);
    setCurrentWallet(wallet);
  };

  const handleAuthenticated = () => {
    setAuthenticated(true);
  };

  if (loading) {
    return <LoadingScreen />;
  }

  if (error) {
    return (
      <div className="error-screen">
        <div className="error-content">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  // Show security login if wallets exist but not authenticated
  if (wallets.length > 0 && !authenticated) {
    return <SecurityLogin onAuthenticated={handleAuthenticated} />;
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route 
            path="/setup" 
            element={
              <WalletSetup 
                onWalletCreated={handleWalletCreated}
                onWalletImported={handleWalletImported}
              />
            } 
          />
          <Route 
            path="/dashboard" 
            element={
              currentWallet ? (
                <Dashboard 
                  wallet={currentWallet}
                  wallets={wallets}
                  onWalletChange={setCurrentWallet}
                  onWalletsUpdate={loadWallets}
                />
              ) : (
                <Navigate to="/setup" replace />
              )
            } 
          />
          <Route 
            path="/" 
            element={
              <Navigate to={wallets.length > 0 ? "/dashboard" : "/setup"} replace />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;