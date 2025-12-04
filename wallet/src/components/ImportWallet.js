import React, { useState } from 'react';

const ImportWallet = ({ onBack, onWalletImported }) => {
  const [mnemonic, setMnemonic] = useState('');
  const [walletName, setWalletName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleImport = async () => {
    try {
      setLoading(true);
      setError(null);

      // Validate mnemonic format
      const words = mnemonic.trim().split(/\s+/);
      if (words.length !== 12) {
        throw new Error('La frase de recuperación debe tener exactamente 12 palabras');
      }

      const result = await window.electronAPI.importWallet(mnemonic.trim());
      
      if (result.success) {
        // Update wallet name if provided
        if (walletName.trim()) {
          result.wallet.name = walletName.trim();
        }
        onWalletImported(result.wallet);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMnemonicChange = (e) => {
    setMnemonic(e.target.value);
    setError(null);
  };

  const importFromFile = async () => {
    try {
      const result = await window.electronAPI.showOpenDialog({
        title: 'Importar Frase de Recuperación',
        filters: [
          { name: 'Archivos de Texto', extensions: ['txt'] },
          { name: 'Todos los Archivos', extensions: ['*'] }
        ],
        properties: ['openFile']
      });

      if (!result.canceled && result.filePaths.length > 0) {
        const fs = require('fs');
        const content = fs.readFileSync(result.filePaths[0], 'utf8');
        
        // Try to extract mnemonic from file content
        const lines = content.split('\n');
        let extractedMnemonic = '';
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('PlayerGold') && 
              !trimmed.startsWith('Dirección:') && 
              !trimmed.startsWith('Fecha') &&
              !trimmed.startsWith('Frase de Recuperación') &&
              !trimmed.startsWith('IMPORTANTE') &&
              !trimmed.startsWith('-') &&
              !trimmed.startsWith('•')) {
            const words = trimmed.split(/\s+/);
            if (words.length === 12) {
              extractedMnemonic = trimmed;
              break;
            }
          }
        }
        
        if (extractedMnemonic) {
          setMnemonic(extractedMnemonic);
        } else {
          setError('No se pudo encontrar una frase de recuperación válida en el archivo');
        }
      }
    } catch (err) {
      setError('Error leyendo archivo: ' + err.message);
    }
  };

  return (
    <div className="wallet-setup">
      <div className="setup-container">
        <div className="setup-header">
          <h1>Importar Cartera</h1>
          <p>Ingresa tu frase de recuperación de 12 palabras</p>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <div className="form-group">
          <label>Nombre de la Cartera (Opcional)</label>
          <input
            type="text"
            className="form-input"
            value={walletName}
            onChange={(e) => setWalletName(e.target.value)}
            placeholder="Mi Cartera Importada"
          />
        </div>

        <div className="form-group">
          <label>Frase de Recuperación (12 palabras)</label>
          <textarea
            className="form-textarea"
            value={mnemonic}
            onChange={handleMnemonicChange}
            placeholder="palabra1 palabra2 palabra3 ... palabra12"
            rows={4}
          />
          <div style={{ marginTop: '10px' }}>
            <button 
              className="btn btn-secondary"
              onClick={importFromFile}
              style={{ fontSize: '12px', padding: '8px 16px' }}
            >
              📁 Importar desde Archivo
            </button>
          </div>
        </div>

        <div className="alert alert-warning">
          <strong>🔒 Seguridad:</strong> Tu frase de recuperación se almacena de forma encriptada 
          localmente. Nunca la compartimos ni la enviamos a ningún servidor.
        </div>

        <div className="form-actions">
          <button 
            className="btn btn-secondary"
            onClick={onBack}
            disabled={loading}
          >
            Volver
          </button>
          <button 
            className="btn btn-primary"
            onClick={handleImport}
            disabled={loading || !mnemonic.trim()}
          >
            {loading ? 'Importando...' : 'Importar Cartera'}
          </button>
        </div>

        <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
          <p><strong>Nota:</strong> Si no tienes una frase de recuperación, puedes crear una nueva cartera.</p>
        </div>
      </div>
    </div>
  );
};

export default ImportWallet;