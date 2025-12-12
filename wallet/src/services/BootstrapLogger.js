/**
 * Bootstrap Logger - Enhanced logging for auto-bootstrap operations
 * Provides structured logging with different levels and user-friendly messages
 */

const LogLevel = {
  ERROR: 'error',
  WARN: 'warn', 
  INFO: 'info',
  DEBUG: 'debug'
};

class BootstrapLogger {
  constructor(component = 'Bootstrap') {
    this.component = component;
    this.logLevel = LogLevel.INFO;
    this.listeners = new Set();
  }
  
  /**
   * Set logging level
   * @param {string} level - Log level from LogLevel enum
   */
  setLevel(level) {
    this.logLevel = level;
  }
  
  /**
   * Add log listener for UI updates
   * @param {Function} listener - Function to call with log entries
   */
  addListener(listener) {
    this.listeners.add(listener);
  }
  
  /**
   * Remove log listener
   * @param {Function} listener - Listener function to remove
   */
  removeListener(listener) {
    this.listeners.delete(listener);
  }
  
  /**
   * Log error message
   * @param {string} message - Error message
   * @param {Error} error - Optional error object
   * @param {Object} context - Additional context
   */
  error(message, error = null, context = {}) {
    this._log(LogLevel.ERROR, message, error, context);
  }
  
  /**
   * Log warning message
   * @param {string} message - Warning message
   * @param {Object} context - Additional context
   */
  warn(message, context = {}) {
    this._log(LogLevel.WARN, message, null, context);
  }
  
  /**
   * Log info message
   * @param {string} message - Info message
   * @param {Object} context - Additional context
   */
  info(message, context = {}) {
    this._log(LogLevel.INFO, message, null, context);
  }
  
  /**
   * Log debug message
   * @param {string} message - Debug message
   * @param {Object} context - Additional context
   */
  debug(message, context = {}) {
    this._log(LogLevel.DEBUG, message, null, context);
  }
  
  /**
   * Internal logging method
   * @param {string} level - Log level
   * @param {string} message - Log message
   * @param {Error} error - Optional error object
   * @param {Object} context - Additional context
   */
  _log(level, message, error = null, context = {}) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      component: this.component,
      message,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack
      } : null,
      context
    };
    
    // Console output
    const consoleMessage = `[${logEntry.timestamp}] ${level.toUpperCase()} [${this.component}] ${message}`;
    
    switch (level) {
      case LogLevel.ERROR:
        console.error(consoleMessage, error || '', context);
        break;
      case LogLevel.WARN:
        console.warn(consoleMessage, context);
        break;
      case LogLevel.INFO:
        console.info(consoleMessage, context);
        break;
      case LogLevel.DEBUG:
        console.debug(consoleMessage, context);
        break;
    }
    
    // Notify listeners
    this.listeners.forEach(listener => {
      try {
        listener(logEntry);
      } catch (err) {
        console.error('Error in log listener:', err);
      }
    });
  }
  
  /**
   * Create child logger with specific component name
   * @param {string} childComponent - Child component name
   * @returns {BootstrapLogger} New logger instance
   */
  child(childComponent) {
    const childLogger = new BootstrapLogger(`${this.component}:${childComponent}`);
    childLogger.setLevel(this.logLevel);
    return childLogger;
  }
}

/**
 * Error handler utility for bootstrap operations
 */
class BootstrapErrorHandler {
  constructor(logger) {
    this.logger = logger;
    this.retryAttempts = new Map();
  }
  
  /**
   * Handle error with retry logic
   * @param {string} operation - Operation name
   * @param {Error} error - Error that occurred
   * @param {Object} options - Retry options
   * @returns {Object} Error handling result
   */
  handleError(operation, error, options = {}) {
    const {
      maxRetries = 3,
      backoffMs = 1000,
      exponentialBackoff = true,
      userMessage = null
    } = options;
    
    const attempts = this.retryAttempts.get(operation) || 0;
    this.retryAttempts.set(operation, attempts + 1);
    
    const shouldRetry = attempts < maxRetries;
    const nextRetryDelay = exponentialBackoff 
      ? backoffMs * Math.pow(2, attempts)
      : backoffMs;
    
    const errorInfo = {
      operation,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      attempts: attempts + 1,
      maxRetries,
      shouldRetry,
      nextRetryDelay,
      userMessage: userMessage || this.generateUserMessage(operation, error)
    };
    
    this.logger.error(
      `Operation '${operation}' failed (attempt ${attempts + 1}/${maxRetries})`,
      error,
      { shouldRetry, nextRetryDelay }
    );
    
    return errorInfo;
  }
  
  /**
   * Reset retry counter for operation
   * @param {string} operation - Operation name
   */
  resetRetries(operation) {
    this.retryAttempts.delete(operation);
  }
  
  /**
   * Generate user-friendly error message
   * @param {string} operation - Operation that failed
   * @param {Error} error - Error object
   * @returns {string} User-friendly message
   */
  generateUserMessage(operation, error) {
    const operationMessages = {
      'peer_discovery': 'Unable to find other users on the network. Please check your internet connection and try again.',
      'genesis_creation': 'Failed to establish the network with other users. This may be due to connectivity issues.',
      'wallet_creation': 'Could not create your wallet address. Please try again.',
      'model_preparation': 'Failed to prepare the AI model for mining. Please check available storage space.',
      'network_formation': 'Unable to connect with other users to form the network. Please ensure your firewall allows the application.'
    };
    
    return operationMessages[operation] || `An error occurred during ${operation}. Please try again.`;
  }
}

module.exports = {
  BootstrapLogger,
  BootstrapErrorHandler,
  LogLevel
};