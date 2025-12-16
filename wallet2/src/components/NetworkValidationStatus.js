/**
 * Network Validation Status Component
 * 
 * Shows the mandatory network validation status and prevents wallet operation
 * if validation fails. This is critical for preventing blockchain forks.
 */

import React, { useState, useEffect } from 'react';
import './NetworkValidationStatus.css';

const NetworkValidationStatus = ({ onValidationComplete }) => {
  const [validationStatus, setValidationStatus] = useState({
    isValidated: false,
    canOperate: false,
    hasNetworkMap: false,
    mapAge: null,
    activeNodes: 0,
    genesisNodes: 0
  });
  
  const [validationResult, setValidationResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    checkValidationStatus();
    
    // Check validation status every 30 seconds
    const interval = setInterval(checkValidationStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const checkValidationStatus = async () => {
    try {
      setLoading(true);
      
      // Get validation status
      const statusResult = await window.electronAPI.invoke('get-network-validation-status');
      
      if (statusResult.success) {
        setValidationStatus(statusResult.status);
        setValidationResult(statusResult.validationResult);
        
        // Notify parent component about validation status
        if (onValidationComplete) {
          onValidationComplete(statusResult.status.canOperate);
        }
      } else {
        setError(statusResult.error);
      }
      
    } catch (err) {
      console.error('Failed to check validation status:', err);
      setError('Failed to check network validation status');
    } finally {
      setLoading(false);
    }
  };

  const handleRetryValidation = async () => {
    try {
      setRetrying(true);
      setError(null);
      
      const result = await window.electronAPI.invoke('force-network-revalidation');
      
      if (result.success) {
        await checkValidationStatus();
      } else {
        setError(result.error);
      }
      
    } catch (err) {
      console.error('Failed to retry validation:', err);
      setError('Failed to retry network validation');
    } finally {
      setRetrying(false);
    }
  };

  const handleRefreshMap = async () => {
    try {
      setLoading(true);
      
      const result = await window.electronAPI.invoke('refresh-network-validation');
      
      if (result.success) {
        await checkValidationStatus();
      } else {
        setError('Failed to refresh network map');
      }
      
    } catch (err) {
      console.error('Failed to refresh network map:', err);
      setError('Failed to refresh network map');
    } finally {
      setLoading(false);
    }
  };

  const formatMapAge = (ageHours) => {
    if (ageHours === null) return 'Unknown';
    
    if (ageHours < 1) {
      return `${Math.round(ageHours * 60)} minutes ago`;
    } else if (ageHours < 24) {
      return `${Math.round(ageHours)} hours ago`;
    } else {
      return `${Math.round(ageHours / 24)} days ago`;
    }
  };

  const getValidationIcon = () => {
    if (loading) return '🔄';
    if (!validationStatus.isValidated) return '❌';
    if (!validationStatus.canOperate) return '⚠️';
    return '✅';
  };

  const getValidationMessage = () => {
    if (loading) return 'Checking network validation...';
    if (!validationStatus.isValidated) return 'Network validation failed - Wallet cannot operate';
    if (!validationStatus.canOperate) return 'Network validation incomplete - Wallet cannot operate';
    return 'Network validation successful - Wallet can operate';
  };

  const getValidationClass = () => {
    if (loading) return 'validation-loading';
    if (!validationStatus.isValidated || !validationStatus.canOperate) return 'validation-failed';
    return 'validation-success';
  };

  // If validation failed completely, show blocking error
  if (!loading && (!validationStatus.isValidated || !validationStatus.canOperate)) {
    return (
      <div className="network-validation-blocker">
        <div className="validation-error-card">
          <div className="error-icon">🚫</div>
          <h2>Network Validation Required</h2>
          
          <div className="error-message">
            <p>PlayerGold requires internet connection to validate the canonical blockchain network.</p>
            <p>This prevents accidental forks and ensures you connect to the correct network.</p>
          </div>
          
          {error && (
            <div className="error-details">
              <strong>Error:</strong> {error}
            </div>
          )}
          
          <div className="validation-info">
            <div className="info-row">
              <span className="label">Network Map:</span>
              <span className="value">{validationStatus.hasNetworkMap ? 'Available' : 'Missing'}</span>
            </div>
            
            {validationStatus.hasNetworkMap && (
              <>
                <div className="info-row">
                  <span className="label">Map Age:</span>
                  <span className="value">{formatMapAge(validationStatus.mapAge)}</span>
                </div>
                
                <div className="info-row">
                  <span className="label">Active Nodes:</span>
                  <span className="value">{validationStatus.activeNodes}</span>
                </div>
                
                <div className="info-row">
                  <span className="label">Genesis Nodes:</span>
                  <span className="value">{validationStatus.genesisNodes}</span>
                </div>
              </>
            )}
          </div>
          
          <div className="validation-actions">
            <button 
              className="retry-button"
              onClick={handleRetryValidation}
              disabled={retrying}
            >
              {retrying ? '🔄 Retrying...' : '🔄 Retry Validation'}
            </button>
            
            {validationStatus.hasNetworkMap && (
              <button 
                className="refresh-button"
                onClick={handleRefreshMap}
                disabled={loading}
              >
                {loading ? '🔄 Refreshing...' : '↻ Refresh Map'}
              </button>
            )}
          </div>
          
          <div className="help-text">
            <p><strong>Need help?</strong></p>
            <ul>
              <li>Check your internet connection</li>
              <li>Ensure playergold.es is accessible</li>
              <li>Try disabling VPN or proxy</li>
              <li>Check firewall settings</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // If validation successful, show compact status
  return (
    <div className={`network-validation-status ${getValidationClass()}`}>
      <div className="validation-header">
        <span className="validation-icon">{getValidationIcon()}</span>
        <span className="validation-message">{getValidationMessage()}</span>
        
        <button 
          className="refresh-button-small"
          onClick={handleRefreshMap}
          disabled={loading}
          title="Refresh network map"
        >
          {loading ? '🔄' : '↻'}
        </button>
      </div>
      
      {validationStatus.hasNetworkMap && (
        <div className="validation-details">
          <div className="detail-item">
            <span className="label">Map Age:</span>
            <span className="value">{formatMapAge(validationStatus.mapAge)}</span>
          </div>
          
          <div className="detail-item">
            <span className="label">Active Nodes:</span>
            <span className="value">{validationStatus.activeNodes}</span>
          </div>
          
          <div className="detail-item">
            <span className="label">Genesis Nodes:</span>
            <span className="value">{validationStatus.genesisNodes}</span>
          </div>
        </div>
      )}
      
      {error && (
        <div className="validation-error">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
};

export default NetworkValidationStatus;