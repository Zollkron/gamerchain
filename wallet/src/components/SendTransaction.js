import React, { useState, useEffect } from 'react';
import { WalletService } from '../services/WalletService';
import { TransactionService } from '../services/TransactionService';

const SendTransaction = ({ wallet, onTransactionSent }) => {
  const [formData, setFormData] = useState({
    toAddress: '',
    amount: '',
    memo: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [feeEstimate, setFeeEstimate] = useState(null);
  const [balance, setBalance] = useState('0');

  useEffect(() => {
    loadWalletBalance();
  }, [wallet]);

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