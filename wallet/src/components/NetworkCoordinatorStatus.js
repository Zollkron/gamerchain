/**
 * Network Coordinator Status Component
 * 
 * Displays the status of the Network Coordinator connection and network map information
 */

import React, { useState, useEffect } from 'react';
import './NetworkCoordinatorStatus.css';

const NetworkService = window.electronAPI ? null : require('../services/NetworkService');

const NetworkCoordinatorStatus = () => {
  const [coordinatorStatus, setCoordinatorStatus] = useState({
    nodeId: null,
    isRegistered: false,
    lastMapUpdate: null,
    coordinatorUrl: null,
    backupUrls: []
  });
  
  const [networkStats, setNetworkStats] = useState({
    total_nodes: 0,
    active_nodes: 0,
    genesis_nodes: 0,
    last_updated: null
  });
  
  const [networkMap, setNetworkMap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCoordinatorStatus();
    loadNetworkStats();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      loadCoordinatorStatus();
      loadNetworkStats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadCoordinatorStatus = async () => {
    try {
      if (window.electronAPI) {
        const status = await window.electronAPI.invoke('get-coordinator-status');
        setCoordinatorStatus(status);
      } else if (NetworkService) {
        const status = NetworkService.getCoordinatorStatus();
        setCoordinatorStatus(status);
      }
      
      setError(null);
    } catch (err) {
      console.error('Failed to load coordinator status:', err);
      setError('Failed to load coordinator status');
    }
  };

  const loadNetworkStats = async () => {
    try {
      setLoading(true);
      
      let result;
      if (window.electronAPI) {
        result = await window.electronAPI.invoke('get-network-coordinator-stats');
      } else if (NetworkService) {
        result = await NetworkService.getNetworkCoordinatorStats();
      }
      
      if (result && result.success) {
        setNetworkStats(result.stats);
      }
      
      // Also get network map
      let mapResult;
      if (window.electronAPI) {
        mapResult = await window.electronAPI.invoke('get-network-map');
      } else if (NetworkService) {
        mapResult = NetworkService.getNetworkMap();
      }
      
      if (mapResult) {
        setNetworkMap(mapResult);
      }
      
    } catch (err) {
      console.error('Failed to load network stats:', err);
      setError('Failed to load network statistics');
    } finally {
      setLoading(false);
    }
  };

  const refreshNetworkMap = async () => {
    try {
      setLoading(true);
      
      if (window.electronAPI) {
        await window.electronAPI.invoke('refresh-network-map');
      } else if (NetworkService) {
        await NetworkService.refreshNetworkMap();
      }
      
      await loadNetworkStats();
      
    } catch (err) {
      console.error('Failed to refresh network map:', err);
      setError('Failed to refresh network map');
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch (err) {
      return 'Invalid date';
    }
  };

  const getConnectionStatusIcon = () => {
    if (coordinatorStatus.isRegistered) {
      return <span className="status-icon connected">🟢</span>;
    } else {
      return <span className="status-icon disconnected">🔴</span>;
    }
  };

  const getConnectionStatusText = () => {
    if (coordinatorStatus.isRegistered) {
      return 'Connected to Network Coordinator';
    } else {
      return 'Not connected to Network Coordinator';
    }
  };

  if (loading && !coordinatorStatus.nodeId) {
    return (
      <div className="network-coordinator-status loading">
        <div className="loading-spinner"></div>
        <p>Loading network coordinator status...</p>
      </div>
    );
  }

  return (
    <div className="network-coordinator-status">
      <div className="coordinator-header">
        <h3>🌐 Network Coordinator</h3>
        <button 
          className="refresh-button"
          onClick={refreshNetworkMap}
          disabled={loading}
          title="Refresh network map"
        >
          {loading ? '🔄' : '↻'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="coordinator-info">
        <div className="status-row">
          {getConnectionStatusIcon()}
          <span className="status-text">{getConnectionStatusText()}</span>
        </div>

        {coordinatorStatus.nodeId && (
          <div className="node-info">
            <div className="info-row">
              <span className="label">Node ID:</span>
              <span className="value monospace">{coordinatorStatus.nodeId}</span>
            </div>
            
            <div className="info-row">
              <span className="label">Coordinator:</span>
              <span className="value">{coordinatorStatus.coordinatorUrl}</span>
            </div>
            
            <div className="info-row">
              <span className="label">Last Map Update:</span>
              <span className="value">{formatTimestamp(coordinatorStatus.lastMapUpdate)}</span>
            </div>
            
            {coordinatorStatus.backupUrls && coordinatorStatus.backupUrls.length > 0 && (
              <div className="info-row">
                <span className="label">Backup Coordinators:</span>
                <span className="value">{coordinatorStatus.backupUrls.length} available</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="network-stats">
        <h4>📊 Network Statistics</h4>
        
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-value">{networkStats.total_nodes || 0}</div>
            <div className="stat-label">Total Nodes</div>
          </div>
          
          <div className="stat-item">
            <div className="stat-value">{networkStats.active_nodes || 0}</div>
            <div className="stat-label">Active Nodes</div>
          </div>
          
          <div className="stat-item">
            <div className="stat-value">{networkStats.genesis_nodes || 0}</div>
            <div className="stat-label">Genesis Nodes</div>
          </div>
          
          {networkStats.average_blockchain_height && (
            <div className="stat-item">
              <div className="stat-value">{Math.round(networkStats.average_blockchain_height)}</div>
              <div className="stat-label">Avg Block Height</div>
            </div>
          )}
        </div>

        {networkStats.last_updated && (
          <div className="stats-footer">
            <small>Last updated: {formatTimestamp(networkStats.last_updated)}</small>
          </div>
        )}
      </div>

      {networkMap && (
        <div className="network-map-info">
          <h4>🗺️ Network Map</h4>
          
          <div className="map-stats">
            <div className="map-stat">
              <span className="label">Map Version:</span>
              <span className="value">{networkMap.version}</span>
            </div>
            
            <div className="map-stat">
              <span className="label">Generated:</span>
              <span className="value">{formatTimestamp(networkMap.timestamp)}</span>
            </div>
            
            <div className="map-stat">
              <span className="label">Active Nodes:</span>
              <span className="value">{networkMap.active_nodes}</span>
            </div>
            
            <div className="map-stat">
              <span className="label">Genesis Nodes:</span>
              <span className="value">{networkMap.genesis_nodes}</span>
            </div>
          </div>
        </div>
      )}

      <div className="coordinator-actions">
        <button 
          className="action-button"
          onClick={refreshNetworkMap}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh Network Map'}
        </button>
      </div>
    </div>
  );
};

export default NetworkCoordinatorStatus;