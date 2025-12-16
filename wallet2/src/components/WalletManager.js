import React, { useState } from 'react';

const WalletManager = ({ wallets, currentWallet, onWalletChange, onWalletsUpdate }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showImportForm, setShowImportForm] = useState(false);
  const [editingWallet, setEditingWallet] = useState(null);
  const [newWalletName, setNewWalletName] = useState('');
  const [importMnemonic, setImportMnemonic] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCreateWallet = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await window.electronAPI.generateWallet();
      
      if (result.success) {
        await onWalletsUpdate();
        setShowCreateForm(false);
        setNewWalletName('');
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error creando cartera: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImportWallet = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await window.electronAPI.importWallet(importMnemonic.trim());
      
      if (result.success) {
        await onWalletsUpdate();
        setShowImportForm(false);
        setImportMnemonic('');
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error importando cartera: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExportWallet = async (walletId) => {
    try {
      const result = await window.electronAPI.exportWallet(walletId);
      
      if (result.success) {
        // Show export dialog
        const saveResult = await window.electronAPI.showSaveDialog({
          title: 'Exportar Frase de Recuperación',
          defaultPath: `playergold-wallet-${result.address.substring(0, 8)}.txt`,
          filters: [
            { name: 'Archivos de Texto', extensions: ['txt'] }
          ]
        });

        if (!saveResult.canceled) {
          const content = `PlayerGold Wallet - Frase de Recuperación
          
Dirección: ${result.address}
Fecha de Exportación: ${new Date().toISOString()}

Frase de Recuperación (12 palabras):
${result.mnemonic}

IMPORTANTE:
- Guarda esta frase en un lugar seguro
- Nunca la compartas con nadie
- Es la única forma de recuperar tu cartera
- PlayerGold no puede ayudarte a recuperarla si la pierdes`;

          // Note: In a real Electron app, you would use fs here
          // For now, we'll just copy to clipboard
          navigator.clipboard.writeText(content);
          alert('Frase de recuperación copiada al portapapeles');
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error exportando cartera: ' + err.message);
    }
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.substring(0, 12)}...${address.substring(address.length - 12)}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="wallet-manager">
      {error && (
        <div className="alert alert-error" style={{ marginBottom: '20px' }}>
          {error}
          <button 
            onClick={() => setError(null)}
            style={{ float: 'right', background: 'none', border: 'none', fontSize: '16px' }}
          >
            ×
          </button>
        </div>
      )}

      {/* Action Buttons */}
      <div className="manager-actions">
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateForm(true)}
          disabled={loading}
        >
          🆕 Nueva Cartera
        </button>
        <button 
          className="btn btn-secondary"
          onClick={() => setShowImportForm(true)}
          disabled={loading}
        >
          📥 Importar Cartera
        </button>
      </div>

      {/* Create Wallet Form */}
      {showCreateForm && (
        <div className="form-modal">
          <div className="form-content">
            <h3>Crear Nueva Cartera</h3>
            <div className="form-group">
              <label>Nombre de la Cartera</label>
              <input
                type="text"
                className="form-input"
                value={newWalletName}
                onChange={(e) => setNewWalletName(e.target.value)}
                placeholder="Mi Nueva Cartera"
              />
            </div>
            <div className="form-actions">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowCreateForm(false)}
                disabled={loading}
              >
                Cancelar
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleCreateWallet}
                disabled={loading}
              >
                {loading ? 'Creando...' : 'Crear'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Wallet Form */}
      {showImportForm && (
        <div className="form-modal">
          <div className="form-content">
            <h3>Importar Cartera</h3>
            <div className="form-group">
              <label>Frase de Recuperación (12 palabras)</label>
              <textarea
                className="form-textarea"
                value={importMnemonic}
                onChange={(e) => setImportMnemonic(e.target.value)}
                placeholder="palabra1 palabra2 palabra3 ..."
                rows={3}
              />
            </div>
            <div className="form-actions">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowImportForm(false)}
                disabled={loading}
              >
                Cancelar
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleImportWallet}
                disabled={loading || !importMnemonic.trim()}
              >
                {loading ? 'Importando...' : 'Importar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Wallets List */}
      <div className="wallets-list">
        <h3>Mis Carteras ({wallets.length})</h3>
        
        {wallets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">👛</div>
            <p>No tienes carteras creadas</p>
            <p style={{ fontSize: '14px', color: '#666' }}>
              Crea una nueva cartera o importa una existente para empezar
            </p>
          </div>
        ) : (
          <div className="wallets-grid">
            {wallets.map(wallet => (
              <div 
                key={wallet.id} 
                className={`wallet-item ${currentWallet?.id === wallet.id ? 'active' : ''}`}
              >
                <div className="wallet-header">
                  <div className="wallet-name">
                    {editingWallet === wallet.id ? (
                      <input
                        type="text"
                        value={newWalletName}
                        onChange={(e) => setNewWalletName(e.target.value)}
                        onBlur={() => setEditingWallet(null)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            // TODO: Update wallet name
                            setEditingWallet(null);
                          }
                        }}
                        autoFocus
                      />
                    ) : (
                      <span onClick={() => {
                        setEditingWallet(wallet.id);
                        setNewWalletName(wallet.name);
                      }}>
                        {wallet.name}
                      </span>
                    )}
                  </div>
                  <div className="wallet-status">
                    {currentWallet?.id === wallet.id && (
                      <span className="status-badge">Activa</span>
                    )}
                    {wallet.imported && (
                      <span className="imported-badge">Importada</span>
                    )}
                  </div>
                </div>
                
                <div className="wallet-address">
                  {formatAddress(wallet.address)}
                </div>
                
                <div className="wallet-balance">
                  <span className="balance-amount">{wallet.balance || '0.00'}</span>
                  <span className="balance-currency">PRGLD</span>
                </div>
                
                <div className="wallet-meta">
                  <span>Creada: {formatDate(wallet.createdAt)}</span>
                </div>
                
                <div className="wallet-actions">
                  {currentWallet?.id !== wallet.id && (
                    <button 
                      className="action-btn"
                      onClick={() => onWalletChange(wallet)}
                      title="Usar esta cartera"
                    >
                      ✓
                    </button>
                  )}
                  <button 
                    className="action-btn"
                    onClick={() => navigator.clipboard.writeText(wallet.address)}
                    title="Copiar dirección"
                  >
                    📋
                  </button>
                  <button 
                    className="action-btn"
                    onClick={() => handleExportWallet(wallet.id)}
                    title="Exportar frase de recuperación"
                  >
                    💾
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .wallet-manager {
          max-width: 1000px;
        }

        .manager-actions {
          display: flex;
          gap: 15px;
          margin-bottom: 30px;
        }

        .form-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }

        .form-content {
          background: white;
          padding: 30px;
          border-radius: 12px;
          max-width: 500px;
          width: 90%;
          max-height: 90vh;
          overflow-y: auto;
        }

        .form-content h3 {
          margin-bottom: 20px;
          color: #333;
        }

        .wallets-list h3 {
          margin-bottom: 20px;
          color: #333;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #666;
        }

        .empty-icon {
          font-size: 64px;
          margin-bottom: 20px;
        }

        .wallets-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 20px;
        }

        .wallet-item {
          background: white;
          border: 2px solid #e9ecef;
          border-radius: 12px;
          padding: 20px;
          transition: all 0.3s;
          cursor: pointer;
        }

        .wallet-item:hover {
          border-color: #667eea;
          box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
        }

        .wallet-item.active {
          border-color: #667eea;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .wallet-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .wallet-name {
          font-size: 18px;
          font-weight: 600;
        }

        .wallet-name input {
          background: transparent;
          border: 1px solid currentColor;
          border-radius: 4px;
          padding: 4px 8px;
          color: inherit;
          font-size: inherit;
          font-weight: inherit;
        }

        .wallet-status {
          display: flex;
          gap: 5px;
        }

        .status-badge {
          background: rgba(255, 255, 255, 0.2);
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 12px;
        }

        .imported-badge {
          background: #28a745;
          color: white;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 12px;
        }

        .wallet-item:not(.active) .imported-badge {
          background: #28a745;
          color: white;
        }

        .wallet-address {
          font-family: 'Courier New', monospace;
          font-size: 14px;
          opacity: 0.8;
          margin-bottom: 15px;
        }

        .wallet-balance {
          margin-bottom: 10px;
        }

        .balance-amount {
          font-size: 24px;
          font-weight: bold;
          margin-right: 8px;
        }

        .balance-currency {
          font-size: 14px;
          opacity: 0.8;
        }

        .wallet-meta {
          font-size: 12px;
          opacity: 0.7;
          margin-bottom: 15px;
        }

        .wallet-actions {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
        }

        .action-btn {
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 6px;
          padding: 6px 10px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.3s;
        }

        .wallet-item:not(.active) .action-btn {
          background: #f8f9fa;
          border-color: #e9ecef;
          color: #666;
        }

        .action-btn:hover {
          background: rgba(255, 255, 255, 0.2);
          border-color: rgba(255, 255, 255, 0.3);
        }

        .wallet-item:not(.active) .action-btn:hover {
          background: #e9ecef;
          border-color: #dee2e6;
        }

        @media (max-width: 768px) {
          .wallets-grid {
            grid-template-columns: 1fr;
          }
          
          .manager-actions {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default WalletManager;