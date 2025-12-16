import React, { useState } from 'react';

const DeveloperTools = ({ onDataCleared }) => {
  const [isClearing, setIsClearing] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleClearData = async () => {
    if (!showConfirm) {
      setShowConfirm(true);
      return;
    }

    try {
      setIsClearing(true);
      
      if (window.electronAPI && window.electronAPI.clearWalletData) {
        const result = await window.electronAPI.clearWalletData();
        
        if (result.success) {
          console.log('✅ Wallet data cleared successfully');
          
          // Also clear localStorage fallback
          localStorage.removeItem('playerGoldWallets');
          
          // Notify parent component
          if (onDataCleared) {
            onDataCleared();
          }
          
          // Reload the page to reset state
          window.location.reload();
        } else {
          console.error('❌ Failed to clear wallet data:', result.error);
          alert('Error clearing data: ' + result.error);
        }
      } else {
        // Fallback for development
        localStorage.removeItem('playerGoldWallets');
        console.log('✅ LocalStorage cleared (development fallback)');
        
        if (onDataCleared) {
          onDataCleared();
        }
        
        window.location.reload();
      }
    } catch (error) {
      console.error('Error clearing data:', error);
      alert('Error clearing data: ' + error.message);
    } finally {
      setIsClearing(false);
      setShowConfirm(false);
    }
  };

  const handleCancel = () => {
    setShowConfirm(false);
  };

  // Only show in development mode
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      background: '#ff4444',
      color: 'white',
      padding: '10px',
      borderRadius: '5px',
      fontSize: '12px',
      zIndex: 9999,
      boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
    }}>
      <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>
        🔧 Developer Tools
      </div>
      
      {!showConfirm ? (
        <button
          onClick={handleClearData}
          disabled={isClearing}
          style={{
            background: '#cc0000',
            color: 'white',
            border: 'none',
            padding: '5px 10px',
            borderRadius: '3px',
            cursor: isClearing ? 'not-allowed' : 'pointer',
            fontSize: '11px'
          }}
        >
          {isClearing ? 'Clearing...' : 'Clear All Data'}
        </button>
      ) : (
        <div>
          <div style={{ marginBottom: '5px', fontSize: '11px' }}>
            ⚠️ This will delete ALL wallets!
          </div>
          <button
            onClick={handleClearData}
            disabled={isClearing}
            style={{
              background: '#cc0000',
              color: 'white',
              border: 'none',
              padding: '3px 8px',
              borderRadius: '3px',
              cursor: 'pointer',
              fontSize: '10px',
              marginRight: '5px'
            }}
          >
            Confirm
          </button>
          <button
            onClick={handleCancel}
            style={{
              background: '#666',
              color: 'white',
              border: 'none',
              padding: '3px 8px',
              borderRadius: '3px',
              cursor: 'pointer',
              fontSize: '10px'
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};

export default DeveloperTools;