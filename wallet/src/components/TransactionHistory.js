import React, { useState, useEffect } from 'react';
import WalletService from '../services/WalletService';
import TransactionService from '../services/TransactionService';

const TransactionHistory = ({ wallet }) => {
  const [transactions, setTransactions] = useState([]);
  const [pendingTransactions, setPendingTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);

  const ITEMS_PER_PAGE = 20;

  useEffect(() => {
    if (wallet) {
      loadTransactions();
      loadPendingTransactions();
      
      // Refresh every 30 seconds
      const interval = setInterval(() => {
        loadPendingTransactions();
      }, 30000);
      
      return () => clearInterval(interval);
    }
  }, [wallet, currentPage]);

  const loadTransactions = async () => {
    if (!wallet) return;
    
    setLoading(true);
    setError('');
    
    try {
      const offset = (currentPage - 1) * ITEMS_PER_PAGE;
      const result = await WalletService.getTransactionHistory(
        wallet.id, 
        ITEMS_PER_PAGE, 
        offset
      );
      
      if (result.success) {
        if (currentPage === 1) {
          setTransactions(result.transactions);
        } else {
          setTransactions(prev => [...prev, ...result.transactions]);
        }
        setHasMore(result.hasMore);
      } else {
        setError(result.error || 'Error al cargar el historial');
      }
    } catch (error) {
      setError('Error inesperado al cargar transacciones');
    } finally {
      setLoading(false);
    }
  };

  const loadPendingTransactions = () => {
    if (!wallet) return;
    
    const pending = WalletService.getPendingTransactions(wallet.id);
    setPendingTransactions(pending);
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      setCurrentPage(prev => prev + 1);
    }
  };

  const getTransactionType = (tx) => {
    if (tx.to_address === wallet.address) {
      return 'received';
    } else if (tx.from_address === wallet.address) {
      return 'sent';
    }
    return 'unknown';
  };

  const getTransactionIcon = (tx) => {
    const type = getTransactionType(tx);
    switch (type) {
      case 'received':
        return '📥';
      case 'sent':
        return '📤';
      default:
        return '🔄';
    }
  };

  const getTransactionColor = (tx) => {
    const type = getTransactionType(tx);
    switch (type) {
      case 'received':
        return 'green';
      case 'sent':
        return 'red';
      default:
        return 'gray';
    }
  };

  const formatAmount = (amount, tx) => {
    const type = getTransactionType(tx);
    const formattedAmount = TransactionService.formatAmount(amount);
    return type === 'received' ? `+${formattedAmount}` : `-${formattedAmount}`;
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAddress = (address) => {
    return `${address.slice(0, 8)}...${address.slice(-8)}`;
  };

  const getStatusBadge = (tx) => {
    const status = tx.status || 'confirmed';
    const statusText = TransactionService.getTransactionStatusText({ status });
    
    return (
      <span className={`status-badge ${status}`}>
        {statusText}
      </span>
    );
  };

  const filterTransactions = (txList) => {
    return txList.filter(tx => {
      if (filter === 'all') return true;
      if (filter === 'sent') return getTransactionType(tx) === 'sent';
      if (filter === 'received') return getTransactionType(tx) === 'received';
      if (filter === 'pending') return tx.status === 'pending';
      return true;
    });
  };

  const sortTransactions = (txList) => {
    return [...txList].sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return b.timestamp - a.timestamp;
        case 'amount':
          return parseFloat(b.amount) - parseFloat(a.amount);
        case 'status':
          return (a.status || 'confirmed').localeCompare(b.status || 'confirmed');
        default:
          return 0;
      }
    });
  };

  const allTransactions = [...pendingTransactions, ...transactions];
  const filteredTransactions = filterTransactions(allTransactions);
  const sortedTransactions = sortTransactions(filteredTransactions);

  const openTransactionDetails = (tx) => {
    setSelectedTx(tx);
  };

  const closeTransactionDetails = () => {
    setSelectedTx(null);
  };

  const copyTransactionHash = async (hash) => {
    try {
      await navigator.clipboard.writeText(hash);
      // Could add a toast notification here
    } catch (error) {
      console.error('Error copying hash:', error);
    }
  };

  return (
    <div className="transaction-history">
      <div className="history-header">
        <h2>Historial de Transacciones</h2>
        <div className="history-stats">
          <div className="stat">
            <span className="stat-label">Total:</span>
            <span className="stat-value">{allTransactions.length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Pendientes:</span>
            <span className="stat-value">{pendingTransactions.length}</span>
          </div>
        </div>
      </div>

      <div className="history-controls">
        <div className="filter-controls">
          <label>Filtrar:</label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">Todas</option>
            <option value="sent">Enviadas</option>
            <option value="received">Recibidas</option>
            <option value="pending">Pendientes</option>
          </select>
        </div>

        <div className="sort-controls">
          <label>Ordenar por:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="date">Fecha</option>
            <option value="amount">Cantidad</option>
            <option value="status">Estado</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      <div className="transactions-list">
        {sortedTransactions.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <h3>No hay transacciones</h3>
            <p>
              {filter === 'all' 
                ? 'Aún no tienes transacciones en esta cartera'
                : `No hay transacciones ${filter === 'sent' ? 'enviadas' : filter === 'received' ? 'recibidas' : 'pendientes'}`
              }
            </p>
          </div>
        ) : (
          <>
            {sortedTransactions.map((tx, index) => (
              <div
                key={tx.hash || index}
                className={`transaction-item ${getTransactionColor(tx)}`}
                onClick={() => openTransactionDetails(tx)}
              >
                <div className="tx-icon">
                  {getTransactionIcon(tx)}
                </div>
                
                <div className="tx-details">
                  <div className="tx-main">
                    <div className="tx-type">
                      {getTransactionType(tx) === 'received' ? 'Recibido de' : 'Enviado a'}
                    </div>
                    <div className="tx-address">
                      {formatAddress(
                        getTransactionType(tx) === 'received' 
                          ? tx.from_address 
                          : tx.to_address
                      )}
                    </div>
                  </div>
                  
                  <div className="tx-meta">
                    <div className="tx-date">
                      {formatDate(tx.timestamp)}
                    </div>
                    {getStatusBadge(tx)}
                  </div>
                </div>
                
                <div className="tx-amount">
                  <div className={`amount ${getTransactionColor(tx)}`}>
                    {formatAmount(tx.amount, tx)} PRGLD
                  </div>
                  {tx.fee && parseFloat(tx.fee) > 0 && (
                    <div className="tx-fee">
                      Comisión: {TransactionService.formatAmount(tx.fee)} PRGLD
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {hasMore && (
              <div className="load-more">
                <button
                  onClick={loadMore}
                  disabled={loading}
                  className="load-more-button"
                >
                  {loading ? 'Cargando...' : 'Cargar más'}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {selectedTx && (
        <div className="transaction-modal-overlay" onClick={closeTransactionDetails}>
          <div className="transaction-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Detalles de Transacción</h3>
              <button
                onClick={closeTransactionDetails}
                className="close-button"
              >
                ×
              </button>
            </div>
            
            <div className="modal-content">
              <div className="detail-row">
                <span>Hash:</span>
                <div className="hash-container">
                  <code>{selectedTx.hash}</code>
                  <button
                    onClick={() => copyTransactionHash(selectedTx.hash)}
                    className="copy-hash-button"
                    title="Copiar hash"
                  >
                    📋
                  </button>
                </div>
              </div>
              
              <div className="detail-row">
                <span>Tipo:</span>
                <span>
                  {getTransactionType(selectedTx) === 'received' ? 'Recibida' : 'Enviada'}
                </span>
              </div>
              
              <div className="detail-row">
                <span>Cantidad:</span>
                <strong>{TransactionService.formatAmount(selectedTx.amount)} PRGLD</strong>
              </div>
              
              <div className="detail-row">
                <span>Comisión:</span>
                <span>{TransactionService.formatAmount(selectedTx.fee || '0')} PRGLD</span>
              </div>
              
              <div className="detail-row">
                <span>De:</span>
                <code>{selectedTx.from_address}</code>
              </div>
              
              <div className="detail-row">
                <span>Para:</span>
                <code>{selectedTx.to_address}</code>
              </div>
              
              <div className="detail-row">
                <span>Fecha:</span>
                <span>{formatDate(selectedTx.timestamp)}</span>
              </div>
              
              <div className="detail-row">
                <span>Estado:</span>
                {getStatusBadge(selectedTx)}
              </div>
              
              {selectedTx.confirmations !== undefined && (
                <div className="detail-row">
                  <span>Confirmaciones:</span>
                  <span>{selectedTx.confirmations}/6</span>
                </div>
              )}
              
              {selectedTx.memo && (
                <div className="detail-row">
                  <span>Memo:</span>
                  <span>{selectedTx.memo}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionHistory;