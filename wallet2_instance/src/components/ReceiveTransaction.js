import React, { useState, useRef } from 'react';

const ReceiveTransaction = ({ wallet }) => {
  const [copied, setCopied] = useState(false);
  const [qrSize, setQrSize] = useState(200);
  const addressRef = useRef(null);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(wallet.address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      // Fallback for older browsers
      if (addressRef.current) {
        addressRef.current.select();
        document.execCommand('copy');
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    }
  };

  const generateQRCode = () => {
    // Simple QR code generation using a service
    // In production, use a proper QR code library
    const qrData = encodeURIComponent(wallet.address);
    return `https://api.qrserver.com/v1/create-qr-code/?size=${qrSize}x${qrSize}&data=${qrData}`;
  };

  const formatAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 10)}...${address.slice(-10)}`;
  };

  const shareAddress = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Mi dirección PlayerGold',
          text: `Envíame PlayerGold ($PRGLD) a esta dirección: ${wallet.address}`,
          url: `playergold:${wallet.address}`
        });
      } catch (error) {
        console.log('Error sharing:', error);
      }
    } else {
      // Fallback to copying
      copyToClipboard();
    }
  };

  return (
    <div className="receive-transaction">
      <div className="receive-header">
        <h2>Recibir PlayerGold ($PRGLD)</h2>
        <p>Comparte tu dirección para recibir pagos</p>
      </div>

      <div className="receive-content">
        <div className="qr-section">
          <div className="qr-container">
            <img
              src={generateQRCode()}
              alt="QR Code de la dirección"
              className="qr-code"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <div className="qr-controls">
              <label htmlFor="qr-size">Tamaño QR:</label>
              <select
                id="qr-size"
                value={qrSize}
                onChange={(e) => setQrSize(parseInt(e.target.value))}
                className="qr-size-select"
              >
                <option value="150">Pequeño</option>
                <option value="200">Mediano</option>
                <option value="300">Grande</option>
              </select>
            </div>
          </div>
        </div>

        <div className="address-section">
          <div className="address-container">
            <label>Tu dirección PlayerGold:</label>
            <div className="address-display">
              <input
                ref={addressRef}
                type="text"
                value={wallet.address}
                readOnly
                className="address-input"
              />
              <button
                onClick={copyToClipboard}
                className={`copy-button ${copied ? 'copied' : ''}`}
                title="Copiar dirección"
              >
                {copied ? '✓' : '📋'}
              </button>
            </div>
            <div className="address-formatted">
              {formatAddress(wallet.address)}
            </div>
          </div>

          <div className="action-buttons">
            <button
              onClick={copyToClipboard}
              className="action-button primary"
            >
              {copied ? 'Copiado!' : 'Copiar Dirección'}
            </button>
            
            <button
              onClick={shareAddress}
              className="action-button secondary"
            >
              Compartir
            </button>
          </div>
        </div>
      </div>

      <div className="receive-info">
        <h3>Información sobre recibir pagos</h3>
        <div className="info-grid">
          <div className="info-item">
            <div className="info-icon">🔒</div>
            <div className="info-content">
              <h4>Seguridad</h4>
              <p>Tu dirección es pública y segura para compartir. Nunca compartas tu frase de recuperación.</p>
            </div>
          </div>
          
          <div className="info-item">
            <div className="info-icon">⚡</div>
            <div className="info-content">
              <h4>Confirmaciones</h4>
              <p>Los pagos aparecen inmediatamente pero se confirman en 30-60 segundos.</p>
            </div>
          </div>
          
          <div className="info-item">
            <div className="info-icon">🌐</div>
            <div className="info-content">
              <h4>Red Global</h4>
              <p>Puedes recibir PlayerGold desde cualquier parte del mundo, 24/7.</p>
            </div>
          </div>
          
          <div className="info-item">
            <div className="info-icon">💰</div>
            <div className="info-content">
              <h4>Sin Comisiones</h4>
              <p>Recibir pagos es completamente gratuito. Solo el remitente paga comisiones.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="recent-transactions-preview">
        <h3>Transacciones recientes</h3>
        <div className="transactions-placeholder">
          <p>Las transacciones recientes aparecerán aquí automáticamente</p>
          <button className="view-history-button">
            Ver historial completo
          </button>
        </div>
      </div>

      <div className="wallet-info">
        <div className="wallet-details">
          <div className="detail-row">
            <span>Cartera:</span>
            <strong>{wallet.name}</strong>
          </div>
          <div className="detail-row">
            <span>Saldo actual:</span>
            <strong>{wallet.balance || '0.00'} PRGLD</strong>
          </div>
          <div className="detail-row">
            <span>Creada:</span>
            <span>{new Date(wallet.createdAt).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReceiveTransaction;