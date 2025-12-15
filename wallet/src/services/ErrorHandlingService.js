/**
 * Error Handling Service
 * 
 * Provides centralized error handling with clear messages, retry mechanisms,
 * and user-friendly explanations for different failure states.
 */

const EventEmitter = require('events');

/**
 * Error categories for different types of failures
 */
const ErrorCategory = {
  NETWORK: 'network',
  GENESIS: 'genesis',
  VALIDATION: 'validation',
  OPERATION: 'operation',
  SYSTEM: 'system'
};

/**
 * Error severity levels
 */
const ErrorSeverity = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

/**
 * Retry strategies for different error types
 */
const RetryStrategy = {
  NONE: 'none',
  IMMEDIATE: 'immediate',
  LINEAR_BACKOFF: 'linear_backoff',
  EXPONENTIAL_BACKOFF: 'exponential_backoff'
};

class ErrorHandlingService extends EventEmitter {
  constructor() {
    super();
    
    // Configuration
    this.config = {
      maxRetries: 3,
      baseRetryDelay: 1000, // 1 second
      maxRetryDelay: 30000, // 30 seconds
      retryMultiplier: 2,
      networkTimeout: 10000 // 10 seconds
    };
    
    // Error message templates
    this.errorMessages = this.initializeErrorMessages();
    
    // Retry tracking
    this.retryAttempts = new Map();
    
    console.log('ErrorHandlingService initialized');
  }

  /**
   * Initialize error message templates
   * @returns {Object} Error message templates
   */
  initializeErrorMessages() {
    return {
      // Network errors
      'network_disconnected': {
        title: 'Red Desconectada',
        message: 'No se puede conectar a la red blockchain. Verifica tu conexión a internet.',
        explanation: 'La wallet necesita conectarse a la red PlayerGold para mostrar balances y transacciones reales.',
        action: 'Verificar conexión',
        severity: ErrorSeverity.HIGH,
        retryStrategy: RetryStrategy.EXPONENTIAL_BACKOFF
      },
      'network_timeout': {
        title: 'Tiempo de Espera Agotado',
        message: 'La conexión a la red tardó demasiado en responder.',
        explanation: 'Esto puede deberse a problemas temporales de conectividad o alta carga en la red.',
        action: 'Reintentar',
        severity: ErrorSeverity.MEDIUM,
        retryStrategy: RetryStrategy.LINEAR_BACKOFF
      },
      'api_unavailable': {
        title: 'API No Disponible',
        message: 'Los servicios de la blockchain no están disponibles temporalmente.',
        explanation: 'Los servidores pueden estar en mantenimiento o experimentando problemas técnicos.',
        action: 'Intentar más tarde',
        severity: ErrorSeverity.HIGH,
        retryStrategy: RetryStrategy.EXPONENTIAL_BACKOFF
      },
      
      // Genesis errors
      'genesis_not_found': {
        title: 'Blockchain No Inicializada',
        message: 'El bloque génesis no existe. La blockchain no ha sido inicializada.',
        explanation: 'Sin el bloque génesis, no pueden existir balances ni transacciones. Necesitas participar en el proceso de bootstrap P2P.',
        action: 'Iniciar Bootstrap',
        severity: ErrorSeverity.CRITICAL,
        retryStrategy: RetryStrategy.NONE
      },
      'genesis_invalid': {
        title: 'Bloque Génesis Inválido',
        message: 'El bloque génesis encontrado no es válido.',
        explanation: 'Esto indica un problema serio con la integridad de la blockchain.',
        action: 'Contactar soporte',
        severity: ErrorSeverity.CRITICAL,
        retryStrategy: RetryStrategy.NONE
      },
      
      // Operation errors
      'operation_not_allowed': {
        title: 'Operación No Permitida',
        message: 'Esta operación no está disponible en el estado actual de la red.',
        explanation: 'Algunas operaciones solo están disponibles cuando la blockchain está completamente activa.',
        action: 'Esperar activación',
        severity: ErrorSeverity.MEDIUM,
        retryStrategy: RetryStrategy.NONE
      },
      'insufficient_balance': {
        title: 'Saldo Insuficiente',
        message: 'No tienes suficientes tokens para realizar esta transacción.',
        explanation: 'Verifica tu balance actual o solicita tokens del faucet de testnet.',
        action: 'Verificar balance',
        severity: ErrorSeverity.LOW,
        retryStrategy: RetryStrategy.NONE
      },
      'invalid_address': {
        title: 'Dirección Inválida',
        message: 'La dirección proporcionada no tiene un formato válido.',
        explanation: 'Las direcciones PlayerGold deben comenzar con "PG" y tener 40 caracteres.',
        action: 'Verificar dirección',
        severity: ErrorSeverity.LOW,
        retryStrategy: RetryStrategy.NONE
      },
      
      // System errors
      'wallet_not_found': {
        title: 'Cartera No Encontrada',
        message: 'La cartera especificada no existe.',
        explanation: 'Puede que la cartera haya sido eliminada o no se haya creado correctamente.',
        action: 'Crear nueva cartera',
        severity: ErrorSeverity.HIGH,
        retryStrategy: RetryStrategy.NONE
      },
      'storage_error': {
        title: 'Error de Almacenamiento',
        message: 'No se pudo acceder al almacenamiento local.',
        explanation: 'Esto puede deberse a permisos insuficientes o problemas con el disco.',
        action: 'Verificar permisos',
        severity: ErrorSeverity.HIGH,
        retryStrategy: RetryStrategy.IMMEDIATE
      }
    };
  }

  /**
   * Handle error with appropriate messaging and retry logic
   * @param {string} errorType - Type of error
   * @param {Error} originalError - Original error object
   * @param {Object} context - Additional context information
   * @returns {Object} Processed error information
   */
  handleError(errorType, originalError, context = {}) {
    const errorTemplate = this.errorMessages[errorType];
    
    if (!errorTemplate) {
      // Unknown error type - create generic error
      return this.createGenericError(originalError, context);
    }
    
    const processedError = {
      type: errorType,
      category: this.getErrorCategory(errorType),
      severity: errorTemplate.severity,
      title: errorTemplate.title,
      message: errorTemplate.message,
      explanation: errorTemplate.explanation,
      suggestedAction: errorTemplate.action,
      retryStrategy: errorTemplate.retryStrategy,
      canRetry: this.canRetry(errorType),
      retryCount: this.getRetryCount(errorType, context),
      timestamp: new Date().toISOString(),
      context: context,
      originalError: originalError ? {
        message: originalError.message,
        stack: originalError.stack
      } : null
    };
    
    // Log error for debugging
    console.error(`[${errorType}] ${errorTemplate.title}:`, {
      message: errorTemplate.message,
      context: context,
      originalError: originalError
    });
    
    // Emit error event
    this.emit('errorHandled', processedError);
    
    return processedError;
  }

  /**
   * Create generic error for unknown error types
   * @param {Error} originalError - Original error object
   * @param {Object} context - Additional context
   * @returns {Object} Generic error information
   */
  createGenericError(originalError, context) {
    return {
      type: 'unknown_error',
      category: ErrorCategory.SYSTEM,
      severity: ErrorSeverity.MEDIUM,
      title: 'Error Inesperado',
      message: originalError ? originalError.message : 'Ha ocurrido un error inesperado.',
      explanation: 'Este error no fue reconocido por el sistema. Por favor, reporta este problema.',
      suggestedAction: 'Reintentar operación',
      retryStrategy: RetryStrategy.LINEAR_BACKOFF,
      canRetry: true,
      retryCount: 0,
      timestamp: new Date().toISOString(),
      context: context,
      originalError: originalError ? {
        message: originalError.message,
        stack: originalError.stack
      } : null
    };
  }

  /**
   * Get error category based on error type
   * @param {string} errorType - Error type
   * @returns {string} Error category
   */
  getErrorCategory(errorType) {
    if (errorType.startsWith('network_') || errorType.startsWith('api_')) {
      return ErrorCategory.NETWORK;
    }
    if (errorType.startsWith('genesis_')) {
      return ErrorCategory.GENESIS;
    }
    if (errorType.startsWith('operation_') || errorType.includes('balance') || errorType.includes('address')) {
      return ErrorCategory.OPERATION;
    }
    if (errorType.includes('validation')) {
      return ErrorCategory.VALIDATION;
    }
    return ErrorCategory.SYSTEM;
  }

  /**
   * Check if error type can be retried
   * @param {string} errorType - Error type
   * @returns {boolean} True if retryable
   */
  canRetry(errorType) {
    const errorTemplate = this.errorMessages[errorType];
    return errorTemplate && errorTemplate.retryStrategy !== RetryStrategy.NONE;
  }

  /**
   * Get current retry count for error type and context
   * @param {string} errorType - Error type
   * @param {Object} context - Error context
   * @returns {number} Current retry count
   */
  getRetryCount(errorType, context) {
    const key = this.getRetryKey(errorType, context);
    return this.retryAttempts.get(key) || 0;
  }

  /**
   * Generate retry key for tracking attempts
   * @param {string} errorType - Error type
   * @param {Object} context - Error context
   * @returns {string} Retry key
   */
  getRetryKey(errorType, context) {
    const contextKey = context.operation || context.walletId || 'global';
    return `${errorType}:${contextKey}`;
  }

  /**
   * Attempt to retry an operation with appropriate backoff
   * @param {string} errorType - Error type
   * @param {Function} operation - Operation to retry
   * @param {Object} context - Operation context
   * @returns {Promise<Object>} Operation result or error
   */
  async retryOperation(errorType, operation, context = {}) {
    const errorTemplate = this.errorMessages[errorType];
    
    if (!errorTemplate || errorTemplate.retryStrategy === RetryStrategy.NONE) {
      throw new Error(`Error type ${errorType} is not retryable`);
    }
    
    const retryKey = this.getRetryKey(errorType, context);
    let currentRetries = this.retryAttempts.get(retryKey) || 0;
    
    // Try the operation first time
    try {
      const result = await operation();
      
      // Success on first try - clear any existing retry count
      this.retryAttempts.delete(retryKey);
      
      return result;
    } catch (error) {
      // First attempt failed, now start retry logic
      while (currentRetries < this.config.maxRetries) {
        // Calculate delay based on retry strategy
        const delay = this.calculateRetryDelay(errorTemplate.retryStrategy, currentRetries);
        
        // Update retry count
        currentRetries++;
        this.retryAttempts.set(retryKey, currentRetries);
        
        // Emit retry event
        this.emit('retryAttempt', {
          errorType,
          attempt: currentRetries,
          maxAttempts: this.config.maxRetries,
          delay,
          context
        });
        
        // Wait for calculated delay
        if (delay > 0) {
          await this.sleep(delay);
        }
        
        try {
          const result = await operation();
          
          // Success - clear retry count
          this.retryAttempts.delete(retryKey);
          
          this.emit('retrySuccess', {
            errorType,
            attempt: currentRetries,
            context
          });
          
          return result;
        } catch (retryError) {
          this.emit('retryFailed', {
            errorType,
            attempt: currentRetries,
            error: retryError.message,
            context
          });
          
          // If this was the last retry, throw the error
          if (currentRetries >= this.config.maxRetries) {
            throw retryError;
          }
          
          // Continue to next retry
        }
      }
      
      // This should not be reached, but just in case
      throw error;
    }
  }

  /**
   * Calculate retry delay based on strategy and attempt number
   * @param {string} strategy - Retry strategy
   * @param {number} attempt - Current attempt number
   * @returns {number} Delay in milliseconds
   */
  calculateRetryDelay(strategy, attempt) {
    switch (strategy) {
      case RetryStrategy.IMMEDIATE:
        return 0;
      
      case RetryStrategy.LINEAR_BACKOFF:
        return Math.min(
          this.config.baseRetryDelay * (attempt + 1),
          this.config.maxRetryDelay
        );
      
      case RetryStrategy.EXPONENTIAL_BACKOFF:
        return Math.min(
          this.config.baseRetryDelay * Math.pow(this.config.retryMultiplier, attempt),
          this.config.maxRetryDelay
        );
      
      default:
        return this.config.baseRetryDelay;
    }
  }

  /**
   * Sleep for specified milliseconds
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise} Promise that resolves after delay
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Clear retry attempts for specific error type or all
   * @param {string} errorType - Error type to clear (optional)
   * @param {Object} context - Context to clear (optional)
   */
  clearRetryAttempts(errorType = null, context = {}) {
    if (errorType) {
      const retryKey = this.getRetryKey(errorType, context);
      this.retryAttempts.delete(retryKey);
    } else {
      this.retryAttempts.clear();
    }
  }

  /**
   * Get user-friendly status message based on network state and error
   * @param {string} networkState - Current network state
   * @param {Object} genesisState - Genesis state information
   * @param {Object} error - Error information (optional)
   * @returns {string} Status message
   */
  getStatusMessage(networkState, genesisState, error = null) {
    // Handle error states first
    if (error) {
      const errorInfo = this.handleError(error.type || 'unknown_error', error.originalError, error.context);
      return `${errorInfo.title}: ${errorInfo.message}`;
    }
    
    // Handle genesis-related states
    if (!genesisState.exists) {
      switch (networkState) {
        case 'bootstrap_pioneer':
          return 'Modo pionero - Configura tu cartera y modelo IA para comenzar';
        case 'bootstrap_discovery':
          return 'Descubriendo peers para formar la red blockchain';
        case 'bootstrap_genesis':
          return 'Creando bloque génesis con otros usuarios pioneros';
        case 'disconnected':
          return 'Blockchain no inicializada - Se requiere proceso de bootstrap';
        case 'connecting':
          return 'Conectando a la red blockchain...';
        default:
          return 'Blockchain no disponible - Se requiere bloque génesis';
      }
    }
    
    // Handle active network states
    switch (networkState) {
      case 'active':
        return 'Blockchain activa - Todas las operaciones disponibles';
      case 'connecting':
        return 'Conectando a la blockchain activa...';
      case 'bootstrap_genesis':
        return 'Finalizando creación del bloque génesis...';
      default:
        return `Estado de red: ${networkState}`;
    }
  }

  /**
   * Get loading state message for operations
   * @param {string} operation - Operation being performed
   * @param {string} networkState - Current network state
   * @returns {string} Loading message
   */
  getLoadingMessage(operation, networkState) {
    const baseMessages = {
      'balance_query': 'Consultando balance',
      'transaction_history': 'Cargando historial de transacciones',
      'send_transaction': 'Enviando transacción',
      'faucet_request': 'Solicitando tokens del faucet',
      'network_status': 'Verificando estado de la red',
      'genesis_check': 'Verificando bloque génesis'
    };
    
    const baseMessage = baseMessages[operation] || 'Procesando operación';
    
    // Add network state context
    if (networkState === 'connecting') {
      return `${baseMessage} (conectando a la red)...`;
    } else if (networkState.startsWith('bootstrap_')) {
      return `${baseMessage} (estableciendo red)...`;
    } else {
      return `${baseMessage}...`;
    }
  }

  /**
   * Get retry statistics
   * @returns {Object} Retry statistics
   */
  getRetryStatistics() {
    const stats = {
      totalRetryKeys: this.retryAttempts.size,
      retryAttempts: []
    };
    
    for (const [key, attempts] of this.retryAttempts.entries()) {
      const [errorType, context] = key.split(':');
      stats.retryAttempts.push({
        errorType,
        context,
        attempts,
        maxAttempts: this.config.maxRetries
      });
    }
    
    return stats;
  }

  /**
   * Update configuration
   * @param {Object} newConfig - New configuration values
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
    console.log('ErrorHandlingService configuration updated:', this.config);
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    this.retryAttempts.clear();
    this.removeAllListeners();
    console.log('ErrorHandlingService cleaned up');
  }
}

module.exports = {
  ErrorHandlingService,
  ErrorCategory,
  ErrorSeverity,
  RetryStrategy
};