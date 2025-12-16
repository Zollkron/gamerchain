import React, { useState } from 'react';

const CreateWallet = ({ onBack, onWalletCreated }) => {
  const [step, setStep] = useState(1); // 1: generating, 2: show mnemonic, 3: confirm
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [walletName, setWalletName] = useState('');

  const generateWallet = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await window.electronAPI.generateWallet();
      
      if (result.success) {
        setWallet(result.wallet);
        setStep(2);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Error generando cartera: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (confirmed) {
      setStep(3);
    }
  };

  const handleFinish = () => {
    onWalletCreated(wallet);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const exportWallet = async () => {
    try {
      const result = await window.electronAPI.showSaveDialog({
        title: 'Guardar Frase de Recuperación',
        defaultPath: `playergold-wallet-${wallet.address.substring(0, 8)}.txt`,
        filters: [
          { name: 'Archivos de Texto', extensions: ['txt'] }
        ]
      });

      if (!result.canceled) {
        const fs = require('fs');
        const content = `PlayerGold Wallet - Frase de Recuperación
        
Dirección: ${wallet.address}
Fecha de Creación: ${wallet.createdAt}

Frase de Recuperación (12 palabras):
${wallet.mnemonic}

IMPORTANTE:
- Guarda esta frase en un lugar seguro
- Nunca la compartas con nadie
- Es la única forma de recuperar tu cartera
- PlayerGold no puede ayudarte a recuperarla si la pierdes`;

        fs.writeFileSync(result.filePath, content);
      }
    } catch (err) {
      setError('Error exportando cartera: ' + err.message);
    }
  };

  if (step === 1) {
    return (
      <div className="wallet-setup">
        <div className="setup-container">
          <div className="setup-header">
            <h1>Crear Nueva Cartera</h1>
            <p>Generaremos una nueva cartera segura para ti</p>
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
              placeholder="Mi Cartera PlayerGold"
            />
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
              onClick={generateWallet}
              disabled={loading}
            >
              {loading ? 'Generando...' : 'Generar Cartera'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 2) {
    return (
      <div className="wallet-setup">
        <div className="setup-container">
          <div className="setup-header">
            <h1>Frase de Recuperación</h1>
            <p>Guarda estas 12 palabras en un lugar seguro</p>
          </div>

          <div className="alert alert-warning">
            <strong>⚠️ Muy Importante:</strong> Esta frase es la única forma de recuperar tu cartera. 
            Guárdala en un lugar seguro y nunca la compartas con nadie.
          </div>

          <div className="mnemonic-display">
            <div className="mnemonic-words">
              {wallet.mnemonic.split(' ').map((word, index) => (
                <div key={index} className="mnemonic-word">
                  {index + 1}. {word}
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
              <button 
                className="btn btn-secondary"
                onClick={() => copyToClipboard(wallet.mnemonic)}
                style={{ flex: 1 }}
              >
                📋 Copiar
              </button>
              <button 
                className="btn btn-secondary"
                onClick={exportWallet}
                style={{ flex: 1 }}
              >
                💾 Exportar
              </button>
            </div>

            <div className="mnemonic-warning">
              <h4>🔒 Consejos de Seguridad</h4>
              <p>• Escribe estas palabras en papel y guárdalas en un lugar seguro</p>
              <p>• No las guardes en tu computadora o en la nube</p>
              <p>• Nunca las compartas con nadie</p>
              <p>• PlayerGold no puede recuperar tu cartera si pierdes esta frase</p>
            </div>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              He guardado mi frase de recuperación en un lugar seguro
            </label>
          </div>

          <div className="form-actions">
            <button 
              className="btn btn-secondary"
              onClick={() => setStep(1)}
            >
              Volver
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleConfirm}
              disabled={!confirmed}
            >
              Continuar
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 3) {
    return (
      <div className="wallet-setup">
        <div className="setup-container">
          <div className="setup-header">
            <h1>¡Cartera Creada!</h1>
            <p>Tu cartera PlayerGold ha sido creada exitosamente</p>
          </div>

          <div className="alert alert-success">
            Tu cartera está lista para usar. Puedes empezar a recibir y enviar tokens PlayerGold ($PRGLD).
          </div>

          <div className="wallet-card">
            <div className="wallet-info">
              <h3>{wallet.name}</h3>
              <div className="wallet-address">{wallet.address}</div>
              <div className="wallet-balance">0.00</div>
              <div className="balance-label">PRGLD</div>
            </div>
          </div>

          <div className="form-actions">
            <button 
              className="btn btn-primary"
              onClick={handleFinish}
              style={{ width: '100%' }}
            >
              Ir al Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default CreateWallet;