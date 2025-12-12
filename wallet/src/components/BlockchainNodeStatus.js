import React, { useState, useEffect } from 'react';

const BlockchainNodeStatus = () => {
  const [nodeStatus, setNodeStatus] = useState({
    isRunning: false,
    nodeId: null,
    port: null,
    apiPort: null,
    network: 'testnet'
  });
  const [networkStatus, setNetworkStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load initial status
    loadNodeStatus();
    
    // Listen for blockchain node status changes
    const handleStatusChange = (event, status) => {
      console.log('Blockchain node status change:', status);
      
      switch (status.event) {
        case 'node_started':
          setNodeStatus(prev => ({
            ...prev,
            isRunning: true,
            nodeId: status.nodeId,
            port: status.port,
            apiPort: status.apiPort
          }));
          setError(null);
          break;
          
        case 'node_stopped':
          setNodeStatus(prev => ({
            ...prev,
            isRunning: false
          }));
          setNetworkStatus(null);
          break;
          
        case 'genesis_created':
          setError(null);
          loadNetworkStatus(); // Refresh network status
          break;
          
        case 'peer_discovered':
          setError(null);
          loadNetworkStatus(); // Refresh network status
          break;
          
        case 'node_error':
          setError(status.error);
          break;
      }
    };

    window.electronAPI.on('blockchain-node-status-change', handleStatusChange);

    // Cleanup
    return () => {
      window.electronAPI.removeListener('blockchain-node-status-change', handleStatusChange);
    };
  }, []);

  const loadNodeStatus = async () => {
    try {
      const result = await window.electronAPI.invoke('get-blockchain-node-status');
      if (result.success) {
        setNodeStatus(result.status);
        
        // If node is running, also load network status
        if (result.status.isRunning) {
          loadNetworkStatus();
        }
      }
    } catch (error) {
      console.error('Error loading node status:', error);
    }
  };

  const loadNetworkStatus = async () => {
    try {
      const result = await window.electronAPI.invoke('get-blockchain-network-status');
      if (result.success) {
        setNetworkStatus(result.status);
      }
    } catch (error) {
      console.error('Error loading network status:', error);
    }
  };

  const startNode = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await window.electronAPI.invoke('start-blockchain-node');
      if (!result.success) {
        setError(result.error);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const stopNode = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await window.electronAPI.invoke('stop-blockchain-node');
      if (!result.success) {
        setError(result.error);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = () => {
    if (nodeStatus.isRunning) {
      return networkStatus?.blockchain?.height > 0 ? 'green' : 'orange';
    }
    return 'red';
  };

  const getStatusText = () => {
    if (!nodeStatus.isRunning) {
      return 'Nodo detenido';
    }
    
    if (!networkStatus) {
      return 'Iniciando...';
    }
    
    if (networkStatus.blockchain?.height === 0) {
      return 'Esperando génesis';
    }
    
    const peers = networkStatus.p2p?.peer_count || 0;
    const height = networkStatus.blockchain?.height || 0;
    
    return `Activo - ${peers} peers, ${height} bloques`;
  };

  return (
    <div className="blockchain-node-status">
      <div className="status-header">
        <div className="status-indicator">
          <div 
            className={`status-dot ${getStatusColor()}`}
            title={getStatusText()}
          />
          <span className="status-text">{getStatusText()}</span>
        </div>
        
        <div className="node-controls">
          {!nodeStatus.isRunning ? (
            <button 
              onClick={startNode} 
              disabled={isLoading}
              className="btn btn-primary btn-sm"
            >
              {isLoading ? 'Iniciando...' : 'Iniciar Nodo'}
            </button>
          ) : (
            <button 
              onClick={stopNode} 
              disabled={isLoading}
              className="btn btn-secondary btn-sm"
            >
              {isLoading ? 'Deteniendo...' : 'Detener Nodo'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="error-message">
          <small className="text-danger">
            ⚠️ {error}
          </small>
        </div>
      )}

      {nodeStatus.isRunning && (
        <div className="node-details">
          <div className="detail-row">
            <small>
              <strong>ID:</strong> {nodeStatus.nodeId}
            </small>
          </div>
          
          {networkStatus && (
            <>
              <div className="detail-row">
                <small>
                  <strong>Red:</strong> {networkStatus.network || 'testnet'}
                  {networkStatus.p2p && (
                    <span> • <strong>Peers:</strong> {networkStatus.p2p.peer_count}</span>
                  )}
                </small>
              </div>
              
              {networkStatus.blockchain && (
                <div className="detail-row">
                  <small>
                    <strong>Blockchain:</strong> {networkStatus.blockchain.height} bloques
                    {networkStatus.bootstrap?.genesis_created && (
                      <span className="genesis-indicator"> • ✅ Génesis creado</span>
                    )}
                  </small>
                </div>
              )}
              
              {networkStatus.bootstrap?.pioneer_count > 0 && (
                <div className="detail-row">
                  <small>
                    <strong>Pioneros:</strong> {networkStatus.bootstrap.pioneer_count}/2
                    {networkStatus.bootstrap.pioneer_count === 1 && (
                      <span className="waiting-indicator"> • ⏳ Esperando otro pionero...</span>
                    )}
                  </small>
                </div>
              )}
            </>
          )}
        </div>
      )}

      <style jsx>{`
        .blockchain-node-status {
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 12px;
          margin: 10px 0;
        }

        .status-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .status-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .status-dot.green {
          background-color: #28a745;
          box-shadow: 0 0 8px rgba(40, 167, 69, 0.5);
        }

        .status-dot.orange {
          background-color: #fd7e14;
          box-shadow: 0 0 8px rgba(253, 126, 20, 0.5);
        }

        .status-dot.red {
          background-color: #dc3545;
        }

        .status-text {
          font-weight: 500;
          color: #495057;
        }

        .node-controls {
          display: flex;
          gap: 8px;
        }

        .btn {
          padding: 4px 12px;
          border: none;
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary {
          background-color: #007bff;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background-color: #0056b3;
        }

        .btn-secondary {
          background-color: #6c757d;
          color: white;
        }

        .btn-secondary:hover:not(:disabled) {
          background-color: #545b62;
        }

        .error-message {
          margin-top: 8px;
          padding: 6px;
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 4px;
        }

        .node-details {
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid #dee2e6;
        }

        .detail-row {
          margin-bottom: 4px;
        }

        .detail-row:last-child {
          margin-bottom: 0;
        }

        .genesis-indicator {
          color: #28a745;
          font-weight: 500;
        }

        .waiting-indicator {
          color: #fd7e14;
          font-weight: 500;
        }

        .text-danger {
          color: #dc3545;
        }
      `}</style>
    </div>
  );
};

export default BlockchainNodeStatus;