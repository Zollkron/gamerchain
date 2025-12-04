import React from 'react';

const LoadingScreen = () => {
  return (
    <div className="loading-screen">
      <div className="loading-content">
        <div className="loading-spinner"></div>
        <h2>PlayerGold Wallet</h2>
        <p>Cargando...</p>
      </div>
    </div>
  );
};

export default LoadingScreen;