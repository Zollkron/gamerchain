/**
 * User Feedback Manager - Real-time status updates for auto-bootstrap operations
 * 
 * Provides animated progress indicators, status messages, and error handling
 * for the bootstrap process to keep users informed of system activity.
 */

const EventEmitter = require('events');
const { BootstrapLogger } = require('./BootstrapLogger');

/**
 * Progress status types for different bootstrap phases
 */
const ProgressType = {
  SCANNING: 'scanning',
  DISCOVERY: 'discovery', 
  GENESIS: 'genesis',
  ERROR: 'error',
  SUCCESS: 'success'
};

/**
 * Animation states for progress indicators
 */
const AnimationState = {
  IDLE: 'idle',
  ACTIVE: 'active',
  PULSING: 'pulsing',
  COMPLETE: 'complete'
};

class UserFeedbackManager extends EventEmitter {
  constructor() {
    super();
    
    // Initialize state
    this.state = {
      currentProgress: null,
      activeAnimations: new Set(),
      messageHistory: [],
      isVisible: false
    };
    
    // Configuration
    this.config = {
      maxMessageHistory: 50,
      animationDuration: 2000,
      progressUpdateInterval: 100,
      messageDisplayDuration: 5000
    };
    
    // Logging
    this.logger = new BootstrapLogger('UserFeedbackManager');
    
    // Animation timers
    this.animationTimers = new Map();
    
    this.logger.info('UserFeedbackManager initialized');
  }
  
  /**
   * Show scanning progress with animated indicators
   * @param {Object} progress - Scan progress information
   * @param {number} progress.percentage - Completion percentage (0-100)
   * @param {string} progress.currentRange - Current IP range being scanned
   * @param {number} progress.peersFound - Number of peers found so far
   * @param {string} progress.status - Current status message
   */
  showScanningProgress(progress) {
    if (!this.validateScanProgress(progress)) {
      this.logger.warn('Invalid scan progress data provided', { progress });
      return;
    }
    
    this.logger.debug('Showing scanning progress', progress);
    
    const progressData = {
      type: ProgressType.SCANNING,
      percentage: Math.min(100, Math.max(0, progress.percentage)),
      currentRange: progress.currentRange,
      peersFound: progress.peersFound,
      status: progress.status,
      timestamp: new Date().toISOString(),
      animation: this.getAnimationForProgress(progress.percentage)
    };
    
    this.updateCurrentProgress(progressData);
    this.addStatusMessage({
      type: 'info',
      message: `Escaneando ${progress.currentRange} - ${progress.peersFound} peers encontrados`,
      timestamp: progressData.timestamp,
      progress: progress.percentage
    });
    
    // Start scanning animation
    this.startAnimation('scanning', AnimationState.ACTIVE);
    
    this.emit('scanningProgress', progressData);
    this.emit('progressUpdate', progressData);
  }
  
  /**
   * Display peer discovery status with real-time updates
   * @param {Object} status - Discovery status information
   * @param {string} status.phase - Current discovery phase
   * @param {Array} status.peers - Currently discovered peers
   * @param {number} status.elapsed - Elapsed time in milliseconds
   * @param {string} status.message - Status message
   */
  displayPeerDiscoveryStatus(status) {
    if (!this.validateDiscoveryStatus(status)) {
      this.logger.warn('Invalid discovery status data provided', { status });
      return;
    }
    
    this.logger.debug('Displaying peer discovery status', status);
    
    const statusData = {
      type: ProgressType.DISCOVERY,
      phase: status.phase,
      peers: status.peers || [],
      elapsed: status.elapsed,
      message: status.message,
      timestamp: new Date().toISOString(),
      animation: this.getAnimationForDiscovery(status.phase)
    };
    
    this.updateCurrentProgress(statusData);
    this.addStatusMessage({
      type: 'info',
      message: `${status.message} (${this.formatElapsedTime(status.elapsed)})`,
      timestamp: statusData.timestamp,
      peerCount: status.peers ? status.peers.length : 0
    });
    
    // Update animation based on discovery phase
    this.updateDiscoveryAnimation(status.phase, status.peers);
    
    this.emit('discoveryStatus', statusData);
    this.emit('progressUpdate', statusData);
  }
  
  /**
   * Show genesis creation progress with coordination indicators
   * @param {Object} progress - Genesis progress information
   * @param {string} progress.phase - Current genesis creation phase
   * @param {number} progress.percentage - Completion percentage (0-100)
   * @param {string} progress.message - Progress message
   * @param {Array} progress.participants - Participating peer addresses
   */
  showGenesisCreationProgress(progress) {
    if (!this.validateGenesisProgress(progress)) {
      this.logger.warn('Invalid genesis progress data provided', { progress });
      return;
    }
    
    this.logger.debug('Showing genesis creation progress', progress);
    
    const progressData = {
      type: ProgressType.GENESIS,
      phase: progress.phase,
      percentage: Math.min(100, Math.max(0, progress.percentage)),
      message: progress.message,
      participants: progress.participants || [],
      timestamp: new Date().toISOString(),
      animation: this.getAnimationForGenesis(progress.phase)
    };
    
    this.updateCurrentProgress(progressData);
    this.addStatusMessage({
      type: 'info',
      message: `${progress.message} (${progress.participants.length} participantes)`,
      timestamp: progressData.timestamp,
      progress: progress.percentage
    });
    
    // Start genesis coordination animation
    this.startAnimation('genesis', AnimationState.PULSING);
    
    this.emit('genesisProgress', progressData);
    this.emit('progressUpdate', progressData);
  }
  
  /**
   * Display error message with appropriate styling and actions
   * @param {Object} error - Bootstrap error information
   * @param {string} error.type - Error type from BootstrapErrorType
   * @param {string} error.message - User-friendly error message
   * @param {Error} error.originalError - Original error object
   * @param {string} error.timestamp - ISO timestamp when error occurred
   * @param {string} error.state - Bootstrap state when error occurred
   */
  displayErrorMessage(error) {
    if (!this.validateBootstrapError(error)) {
      this.logger.warn('Invalid error data provided', { error });
      return;
    }
    
    this.logger.error('Displaying error message', error.originalError);
    
    const errorData = {
      type: ProgressType.ERROR,
      errorType: error.type,
      message: error.message,
      timestamp: error.timestamp,
      state: error.state,
      animation: AnimationState.IDLE
    };
    
    this.updateCurrentProgress(errorData);
    this.addStatusMessage({
      type: 'error',
      message: error.message,
      timestamp: error.timestamp,
      errorType: error.type,
      canRetry: this.canRetryError(error.type)
    });
    
    // Stop active animations on error
    this.stopAllAnimations();
    
    this.emit('errorMessage', errorData);
    this.emit('progressUpdate', errorData);
  }
  
  /**
   * Show success message with celebration animation
   * @param {string} message - Success message to display
   */
  showSuccessMessage(message) {
    if (!message || typeof message !== 'string') {
      this.logger.warn('Invalid success message provided', { message });
      return;
    }
    
    this.logger.info('Showing success message', { message });
    
    const successData = {
      type: ProgressType.SUCCESS,
      message: message,
      timestamp: new Date().toISOString(),
      animation: AnimationState.COMPLETE
    };
    
    this.updateCurrentProgress(successData);
    this.addStatusMessage({
      type: 'success',
      message: message,
      timestamp: successData.timestamp
    });
    
    // Start success animation
    this.startAnimation('success', AnimationState.COMPLETE);
    
    // Auto-hide after delay
    setTimeout(() => {
      this.hideProgress();
    }, this.config.messageDisplayDuration);
    
    this.emit('successMessage', successData);
    this.emit('progressUpdate', successData);
  }
  
  /**
   * Get current progress state
   * @returns {Object|null} Current progress data
   */
  getCurrentProgress() {
    return this.state.currentProgress;
  }
  
  /**
   * Get message history
   * @returns {Array} Array of status messages
   */
  getMessageHistory() {
    return [...this.state.messageHistory];
  }
  
  /**
   * Clear all progress and messages
   */
  clearProgress() {
    this.logger.debug('Clearing all progress');
    
    this.state.currentProgress = null;
    this.state.messageHistory = [];
    this.stopAllAnimations();
    
    this.emit('progressCleared');
  }
  
  /**
   * Hide progress display
   */
  hideProgress() {
    this.logger.debug('Hiding progress display');
    
    this.state.isVisible = false;
    this.stopAllAnimations();
    
    this.emit('progressHidden');
  }
  
  /**
   * Show progress display
   */
  showProgress() {
    this.logger.debug('Showing progress display');
    
    this.state.isVisible = true;
    
    this.emit('progressShown');
  }
  
  /**
   * Check if progress is currently visible
   * @returns {boolean} True if visible
   */
  isProgressVisible() {
    return this.state.isVisible;
  }
  
  // Private helper methods
  
  /**
   * Update current progress state
   * @param {Object} progressData - New progress data
   */
  updateCurrentProgress(progressData) {
    this.state.currentProgress = progressData;
    this.state.isVisible = true;
  }
  
  /**
   * Add message to history
   * @param {Object} message - Status message
   */
  addStatusMessage(message) {
    const messageWithId = {
      ...message,
      id: Date.now() + Math.random()
    };
    
    this.state.messageHistory.push(messageWithId);
    
    // Trim history if too long
    if (this.state.messageHistory.length > this.config.maxMessageHistory) {
      this.state.messageHistory = this.state.messageHistory.slice(-this.config.maxMessageHistory);
    }
    
    this.emit('messageAdded', messageWithId);
  }
  
  /**
   * Start animation for specific element
   * @param {string} elementId - Animation element identifier
   * @param {string} animationState - Animation state
   */
  startAnimation(elementId, animationState) {
    this.state.activeAnimations.add(elementId);
    
    // Clear existing timer
    if (this.animationTimers.has(elementId)) {
      clearTimeout(this.animationTimers.get(elementId));
    }
    
    this.emit('animationStart', { elementId, animationState });
    
    // Auto-stop animation after duration
    const timer = setTimeout(() => {
      this.stopAnimation(elementId);
    }, this.config.animationDuration);
    
    this.animationTimers.set(elementId, timer);
  }
  
  /**
   * Stop specific animation
   * @param {string} elementId - Animation element identifier
   */
  stopAnimation(elementId) {
    this.state.activeAnimations.delete(elementId);
    
    if (this.animationTimers.has(elementId)) {
      clearTimeout(this.animationTimers.get(elementId));
      this.animationTimers.delete(elementId);
    }
    
    this.emit('animationStop', { elementId });
  }
  
  /**
   * Stop all active animations
   */
  stopAllAnimations() {
    for (const elementId of this.state.activeAnimations) {
      this.stopAnimation(elementId);
    }
  }
  
  /**
   * Get animation state for progress percentage
   * @param {number} percentage - Progress percentage
   * @returns {string} Animation state
   */
  getAnimationForProgress(percentage) {
    if (percentage === 0) return AnimationState.IDLE;
    if (percentage === 100) return AnimationState.COMPLETE;
    return AnimationState.ACTIVE;
  }
  
  /**
   * Get animation state for discovery phase
   * @param {string} phase - Discovery phase
   * @returns {string} Animation state
   */
  getAnimationForDiscovery(phase) {
    switch (phase) {
      case 'scanning': return AnimationState.ACTIVE;
      case 'connecting': return AnimationState.PULSING;
      case 'complete': return AnimationState.COMPLETE;
      default: return AnimationState.IDLE;
    }
  }
  
  /**
   * Get animation state for genesis phase
   * @param {string} phase - Genesis phase
   * @returns {string} Animation state
   */
  getAnimationForGenesis(phase) {
    switch (phase) {
      case 'negotiating': return AnimationState.PULSING;
      case 'creating': return AnimationState.ACTIVE;
      case 'distributing': return AnimationState.ACTIVE;
      case 'complete': return AnimationState.COMPLETE;
      default: return AnimationState.IDLE;
    }
  }
  
  /**
   * Update discovery animation based on phase and peers
   * @param {string} phase - Discovery phase
   * @param {Array} peers - Discovered peers
   */
  updateDiscoveryAnimation(phase, peers) {
    const peerCount = peers ? peers.length : 0;
    
    if (peerCount === 0) {
      this.startAnimation('discovery', AnimationState.ACTIVE);
    } else if (peerCount >= 2) {
      this.startAnimation('discovery', AnimationState.COMPLETE);
    } else {
      this.startAnimation('discovery', AnimationState.PULSING);
    }
  }
  
  /**
   * Format elapsed time for display
   * @param {number} elapsed - Elapsed time in milliseconds
   * @returns {string} Formatted time string
   */
  formatElapsedTime(elapsed) {
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  }
  
  /**
   * Check if error type can be retried
   * @param {string} errorType - Error type
   * @returns {boolean} True if retryable
   */
  canRetryError(errorType) {
    const retryableErrors = [
      'network_timeout',
      'peer_disconnection',
      'insufficient_peers'
    ];
    return retryableErrors.includes(errorType);
  }
  
  // Validation methods
  
  /**
   * Validate scan progress data
   * @param {Object} progress - Progress data to validate
   * @returns {boolean} True if valid
   */
  validateScanProgress(progress) {
    return progress &&
           typeof progress.percentage === 'number' &&
           typeof progress.currentRange === 'string' &&
           typeof progress.peersFound === 'number' &&
           typeof progress.status === 'string';
  }
  
  /**
   * Validate discovery status data
   * @param {Object} status - Status data to validate
   * @returns {boolean} True if valid
   */
  validateDiscoveryStatus(status) {
    return status &&
           typeof status.phase === 'string' &&
           typeof status.elapsed === 'number' &&
           typeof status.message === 'string' &&
           (status.peers === undefined || Array.isArray(status.peers));
  }
  
  /**
   * Validate genesis progress data
   * @param {Object} progress - Progress data to validate
   * @returns {boolean} True if valid
   */
  validateGenesisProgress(progress) {
    return progress &&
           typeof progress.phase === 'string' &&
           typeof progress.percentage === 'number' &&
           typeof progress.message === 'string' &&
           (progress.participants === undefined || Array.isArray(progress.participants));
  }
  
  /**
   * Validate bootstrap error data
   * @param {Object} error - Error data to validate
   * @returns {boolean} True if valid
   */
  validateBootstrapError(error) {
    return error &&
           typeof error.type === 'string' &&
           typeof error.message === 'string' &&
           typeof error.timestamp === 'string';
  }
}

module.exports = {
  UserFeedbackManager,
  ProgressType,
  AnimationState
};