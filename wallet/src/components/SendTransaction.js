import React, { useState, useEffect } from 'react';
import WalletService from '../services/WalletService';
import TransactionService from '../services/TransactionService';
import AddressBookService from '../services/AddressBookService';

// Mini AddressBook component for dropdown
const AddressBookMini = ({ onAddressSelect }) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAddresses();
  }, []);

  const loadAddresses = async () => {
    setLoading(true);
    const result = await AddressBookService.getAddresses();
    if (result.success) {
      setAddresses(result.addresses.slice(0, 10)); // Show only first 10
    }
    setLoading(false);
  };

  if (loading) {
    return <div className="loading-mini">Cargando direcciones...</div>;
  }

  if (addresses.length === 0) {
    return <div className="empty-mini">No hay direcciones guardadas</div>;
  }

  return (
    <div className="address-list-mini">
      {addresses.map(address => (
        <div
          key={address.id}
          className="address-item-mini"
          onClick={() => onAddressSelect(address)}
        >
          <div className="address-label">{address.label}</div>
          <div className="address-string">{address.address}</div>
        </div>
      ))}
    </div>
  );
};

const SendTransaction = ({ wallet, onTransactionSent, prefilledAddress = '' }) => {
  const [formData, setFormData] = useState({
    toAddress: prefilledAddress,
    amount: '',
    memo: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [feeEstimate, setFeeEstimate] = useState(null);
  const [balance, setBalance] = useState('0');
  const [showAddressBook, setShowAddressBook] = useState(false);
  const [savedAddresses, setSavedAddresses] = useState([]);

  useEffect(() => {
    loadWalletBalance();
    loadSavedAddresses();
  }, [wallet]);

  useEffect(() => {
    if (prefilledAddress) {
      setFormData(prev => ({ ...prev, toAddress: prefilledAddress }));
    }
  }, [prefilledAddress]);

  useEffect(() => {
    if (formData.toAddress && formData.amount) {
      estimateTransactionFee();
    } else {
      setFeeEstimate(null);
    }
  }, [formData.toAddress, formData.amount]);

  const loadWalletBalance = async () => {
    if (!wallet) return;
    
    try {
      const result = await WalletService.getWalletBalance(wallet.id);
      if (result.success) {
        setBalance(result.balance);
      }
    } catch (error) {
      console.error('Error loading balance:', error);
    }
  };

  const loadSavedAddresses = async () => {
    try {
      const result = await AddressBookService.getFrequentlyUsed(5);
      if (result.success) {
        setSavedAddresses(result.addresses);
      }
    } catch (error) {
      console.error('Error loading saved addresses:', error);
    }
  };

  const estimateTransactionFee = async () => {
    try {
      const result = await TransactionService.estimateFee({
        from: wallet.address,
        to: formData.toAddress,
        amount: formData.amount,
        type: 'transfer'
      });

      if (result.success) {
        setFeeEstimate(result);
      }
    } catch (error) {
      console.error('Error estimating fee:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
    setSuccess('');
  };

  const validateForm = () => {
    if (!formData.toAddress.trim()) {
      setError('La dirección de destino es requerida');
      return false;
    }

    if (!TransactionService.isValidAddress(formData.toAddress)) {
      setError('Formato de dirección inválido');
      return false;
    }

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      setError('El monto debe ser mayor a 0');
      return false;
    }

    const amount = parseFloat(formData.amount);
    const fee = feeEstimate ? parseFloat(feeEstimate.fee) : 0.01;
    const total = amount + fee;

    if (total > parseFloat(balance)) {
      setError(`Saldo insuficiente. Requerido: ${total.toFixed(8)} PRGLD, Disponible: ${balance} PRGLD`);
      return false;
    }

    if (formData.toAddress === wallet.address) {
      setError('No puedes enviar a tu propia dirección');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const result = await WalletService.sendTransaction(wallet.id, {
        toAddress: formData.toAddress,
        amount: formData.amount,
        memo: formData.memo,
        transactionType: 'transfer'
      });

      if (result.success) {
        setSuccess(`Transacción enviada exitosamente! Hash: ${result.transactionHash}`);
        setFormData({ toAddress: '', amount: '', memo: '' });
        
        // Refresh balance
        await loadWalletBalance();
        
        // Mark address as used in address book
        await AddressBookService.markAddressAsUsed(formData.toAddress);
        
        // Notify parent component
        if (onTransactionSent) {
          onTransactionSent(result);
        }
      } else {
        setError(result.error || 'Error al enviar la transacción');
      }
    } catch (error) {
      setError('Error inesperado al enviar la transacción');
    } finally {
      setLoading(false);
    }
  };

  const handleMaxAmount = () => {
    const fee = feeEstimate ? parseFloat(feeEstimate.fee) : 0.01;
    const maxAmount = Math.max(0, parseFloat(balance) - fee);
    
    setFormData(prev => ({
      ...prev,
      amount: maxAmount.toString()
    }));
  };

  const formatAmount = (amount) => {
    return TransactionService.formatAmount(amount);
  };

  const handleAddressSelect = (address) => {
    setFormData(prev => ({ ...prev, toAddress: address.address }));
    setShowAddressBook(false);
  };

  const handleSaveAddress = async () => {
    if (!formData.toAddress) return;
    
    const label = prompt('Ingresa una etiqueta para esta dirección:');
    if (!label) return;
    
    const result = await AddressBookService.addAddress({
      address: formData.toAddress,
      label: label,
      category: 'general'
    });
    
    if (result.success) {
      alert('Dirección guardada en la libreta');
      loadSavedAddresses();
    } else {
      alert('Error al guardar: ' + result.error);
    }
  };

  return (
    <div className="send-transaction">
      <div className="transaction-header">
        <h2>Enviar PlayerGold ($PRGLD)</h2>
        <div className="balance-info">
          <span>Saldo disponible: </span>
          <strong>{formatAmount(balance)} PRGLD</strong>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="transaction-form">
        <div className="form-group">
          <label htmlFor="toAddress">Dirección de destino</label>
          <div className="address-input-group">
            <input
              type="text"
              id="toAddress"
              name="toAddress"
              value={formData.toAddress}
              onChange={handleInputChange}
              placeholder="PG1234567890abcdef..."
              className="form-input"
              disabled={loading}
            />
            <button
              type="button"
              onClick={() => setShowAddressBook(!showAddressBook)}
              className="address-book-button"
              disabled={loading}
              title="Seleccionar de libreta de direcciones"
            >
              📇
            </button>
            {formData.toAddress && (
              <button
                type="button"
                onClick={handleSaveAddress}
                className="save-address-button"
                disabled={loading}
                title="Guardar en libreta de direcciones"
              >
                💾
              </button>
            )}
          </div>
          
          {/* Frequently used addresses */}
          {savedAddresses.length > 0 && (
            <div className="frequent-addresses">
              <small>Direcciones frecuentes:</small>
              <div className="address-chips">
                {savedAddresses.map(addr => (
                  <button
                    key={addr.id}
                    type="button"
                    className="address-chip"
                    onClick={() => handleAddressSelect(addr)}
                    disabled={loading}
                  >
                    {addr.label}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Address book dropdown */}
          {showAddressBook && (
            <div className="address-book-dropdown">
              <div className="dropdown-header">
                <span>Seleccionar dirección guardada</span>
                <button
                  type="button"
                  onClick={() => setShowAddressBook(false)}
                  className="close-dropdown"
                >
                  ×
                </button>
              </div>
              <AddressBookMini onAddressSelect={handleAddressSelect} />
            </div>
          )}
          
          <small className="form-help">
            Dirección PlayerGold válida (comienza con 'PG')
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="amount">Cantidad</label>
          <div className="amount-input-group">
            <input
              type="number"
              id="amount"
              name="amount"
              value={formData.amount}
              onChange={handleInputChange}
              placeholder="0.00"
              step="0.00000001"
              min="0"
              className="form-input"
              disabled={loading}
            />
            <button
              type="button"
              onClick={handleMaxAmount}
              className="max-button"
              disabled={loading}
            >
              MAX
            </button>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="memo">Memo (opcional)</label>
          <input
            type="text"
            id="memo"
            name="memo"
            value={formData.memo}
            onChange={handleInputChange}
            placeholder="Nota opcional para la transacción"
            maxLength="100"
            className="form-input"
            disabled={loading}
          />
        </div>

        {feeEstimate && (
          <div className="fee-estimate">
            <div className="fee-info">
              <div className="fee-row">
                <span>Comisión estimada:</span>
                <strong>{formatAmount(feeEstimate.fee)} PRGLD</strong>
              </div>
              <div className="fee-row">
                <span>Congestión de red:</span>
                <span className={`congestion-level ${feeEstimate.congestionLevel}`}>
                  {feeEstimate.congestionLevel === 'low' && 'Baja'}
                  {feeEstimate.congestionLevel === 'medium' && 'Media'}
                  {feeEstimate.congestionLevel === 'high' && 'Alta'}
                  {feeEstimate.congestionLevel === 'critical' && 'Crítica'}
                </span>
              </div>
              <div className="fee-row">
                <span>Tiempo estimado:</span>
                <span>{feeEstimate.estimatedTime || 30} segundos</span>
              </div>
              <div className="fee-row total">
                <span>Total a enviar:</span>
                <strong>
                  {formatAmount(
                    (parseFloat(formData.amount) || 0) + parseFloat(feeEstimate.fee)
                  )} PRGLD
                </strong>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {success && (
          <div className="success-message">
            <span className="success-icon">✅</span>
            {success}
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            className="send-button"
            disabled={loading || !formData.toAddress || !formData.amount}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Enviando...
              </>
            ) : (
              'Enviar Transacción'
            )}
          </button>
        </div>
      </form>

      <div className="transaction-info">
        <h3>Información importante</h3>
        <ul>
          <li>Las transacciones son irreversibles una vez confirmadas</li>
          <li>Verifica cuidadosamente la dirección de destino</li>
          <li>Las comisiones se distribuyen: 20% liquidez, 80% quema</li>
          <li>Tiempo de confirmación típico: 30-60 segundos</li>
        </ul>
      </div>
    </div>
  );
};

export default SendTransaction;