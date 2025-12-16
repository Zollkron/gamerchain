/**
 * Error Handling Service Tests
 * 
 * Tests for error message accuracy, user message clarity, and retry mechanisms
 * **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
 */

const { ErrorHandlingService, ErrorCategory, ErrorSeverity, RetryStrategy } = require('../ErrorHandlingService');

describe('ErrorHandlingService', () => {
  let errorHandler;

  beforeEach(() => {
    errorHandler = new ErrorHandlingService();
  });

  afterEach(() => {
    errorHandler.cleanup();
  });

  describe('Error Message Accuracy', () => {
    it('should provide accurate error messages for network disconnection', () => {
      const originalError = new Error('Network unreachable');
      const context = { operation: 'balance_query', address: 'PG123...' };
      
      const result = errorHandler.handleError('network_disconnected', originalError, context);
      
      expect(result.type).toBe('network_disconnected');
      expect(result.category).toBe(ErrorCategory.NETWORK);
      expect(result.severity).toBe(ErrorSeverity.HIGH);
      expect(result.title).toBe('Red Desconectada');
      expect(result.message).toContain('No se puede conectar a la red blockchain');
      expect(result.explanation).toContain('La wallet necesita conectarse a la red PlayerGold');
      expect(result.suggestedAction).toBe('Verificar conexión');
      expect(result.canRetry).toBe(true);
      expect(result.retryStrategy).toBe(RetryStrategy.EXPONENTIAL_BACKOFF);
    });

    it('should provide accurate error messages for genesis not found', () => {
      const originalError = new Error('Genesis block not found');
      const context = { operation: 'balance_query' };
      
      const result = errorHandler.handleError('genesis_not_found', originalError, context);
      
      expect(result.type).toBe('genesis_not_found');
      expect(result.category).toBe(ErrorCategory.GENESIS);
      expect(result.severity).toBe(ErrorSeverity.CRITICAL);
      expect(result.title).toBe('Blockchain No Inicializada');
      expect(result.message).toContain('El bloque génesis no existe');
      expect(result.explanation).toContain('Sin el bloque génesis, no pueden existir balances ni transacciones');
      expect(result.suggestedAction).toBe('Iniciar Bootstrap');
      expect(result.canRetry).toBe(false);
      expect(result.retryStrategy).toBe(RetryStrategy.NONE);
    });

    it('should provide accurate error messages for operation not allowed', () => {
      const originalError = new Error('Operation not permitted in current state');
      const context = { operation: 'send_transaction', networkState: 'bootstrap_pioneer' };
      
      const result = errorHandler.handleError('operation_not_allowed', originalError, context);
      
      expect(result.type).toBe('operation_not_allowed');
      expect(result.category).toBe(ErrorCategory.OPERATION);
      expect(result.severity).toBe(ErrorSeverity.MEDIUM);
      expect(result.title).toBe('Operación No Permitida');
      expect(result.message).toContain('Esta operación no está disponible en el estado actual');
      expect(result.explanation).toContain('Algunas operaciones solo están disponibles cuando la blockchain está completamente activa');
      expect(result.suggestedAction).toBe('Esperar activación');
      expect(result.canRetry).toBe(false);
    });

    it('should handle unknown error types gracefully', () => {
      const originalError = new Error('Unknown error occurred');
      const context = { operation: 'unknown_operation' };
      
      const result = errorHandler.handleError('unknown_error_type', originalError, context);
      
      expect(result.type).toBe('unknown_error');
      expect(result.category).toBe(ErrorCategory.SYSTEM);
      expect(result.severity).toBe(ErrorSeverity.MEDIUM);
      expect(result.title).toBe('Error Inesperado');
      expect(result.message).toBe('Unknown error occurred');
      expect(result.explanation).toContain('Este error no fue reconocido por el sistema');
      expect(result.canRetry).toBe(true);
    });
  });

  describe('User Message Clarity', () => {
    it('should provide clear status messages for different network states', () => {
      const networkState = 'bootstrap_pioneer';
      const genesisState = { exists: false };
      
      const statusMessage = errorHandler.getStatusMessage(networkState, genesisState);
      
      expect(statusMessage).toBe('Modo pionero - Configura tu cartera y modelo IA para comenzar');
    });

    it('should provide clear status messages for active network', () => {
      const networkState = 'active';
      const genesisState = { exists: true };
      
      const statusMessage = errorHandler.getStatusMessage(networkState, genesisState);
      
      expect(statusMessage).toBe('Blockchain activa - Todas las operaciones disponibles');
    });

    it('should provide clear status messages with error context', () => {
      const networkState = 'disconnected';
      const genesisState = { exists: false };
      const error = {
        type: 'network_timeout',
        originalError: new Error('Connection timeout'),
        context: { operation: 'balance_query' }
      };
      
      const statusMessage = errorHandler.getStatusMessage(networkState, genesisState, error);
      
      expect(statusMessage).toContain('Tiempo de Espera Agotado');
      expect(statusMessage).toContain('La conexión a la red tardó demasiado');
    });

    it('should provide clear loading messages for operations', () => {
      const loadingMessage = errorHandler.getLoadingMessage('balance_query', 'connecting');
      
      expect(loadingMessage).toBe('Consultando balance (conectando a la red)...');
    });

    it('should provide clear loading messages for bootstrap states', () => {
      const loadingMessage = errorHandler.getLoadingMessage('transaction_history', 'bootstrap_genesis');
      
      expect(loadingMessage).toBe('Cargando historial de transacciones (estableciendo red)...');
    });
  });

  describe('Retry Mechanisms', () => {
    it('should calculate correct delay for immediate retry', () => {
      const delay = errorHandler.calculateRetryDelay(RetryStrategy.IMMEDIATE, 0);
      expect(delay).toBe(0);
    });

    it('should calculate correct delay for linear backoff', () => {
      const delay1 = errorHandler.calculateRetryDelay(RetryStrategy.LINEAR_BACKOFF, 0);
      const delay2 = errorHandler.calculateRetryDelay(RetryStrategy.LINEAR_BACKOFF, 1);
      const delay3 = errorHandler.calculateRetryDelay(RetryStrategy.LINEAR_BACKOFF, 2);
      
      expect(delay1).toBe(1000); // baseRetryDelay * 1
      expect(delay2).toBe(2000); // baseRetryDelay * 2
      expect(delay3).toBe(3000); // baseRetryDelay * 3
    });

    it('should calculate correct delay for exponential backoff', () => {
      const delay1 = errorHandler.calculateRetryDelay(RetryStrategy.EXPONENTIAL_BACKOFF, 0);
      const delay2 = errorHandler.calculateRetryDelay(RetryStrategy.EXPONENTIAL_BACKOFF, 1);
      const delay3 = errorHandler.calculateRetryDelay(RetryStrategy.EXPONENTIAL_BACKOFF, 2);
      
      expect(delay1).toBe(1000); // baseRetryDelay * 2^0
      expect(delay2).toBe(2000); // baseRetryDelay * 2^1
      expect(delay3).toBe(4000); // baseRetryDelay * 2^2
    });

    it('should respect maximum retry delay', () => {
      // Set a low max delay for testing
      errorHandler.updateConfig({ maxRetryDelay: 5000 });
      
      const delay = errorHandler.calculateRetryDelay(RetryStrategy.EXPONENTIAL_BACKOFF, 10);
      
      expect(delay).toBe(5000); // Should be capped at maxRetryDelay
    });

    it('should successfully retry operations with exponential backoff', async () => {
      let attemptCount = 0;
      const mockOperation = jest.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 3) {
          throw new Error('Temporary failure');
        }
        return { success: true, data: 'success' };
      });

      // Speed up test by reducing delays
      errorHandler.updateConfig({ baseRetryDelay: 10, maxRetryDelay: 100 });

      const result = await errorHandler.retryOperation(
        'network_timeout',
        mockOperation,
        { operation: 'test' }
      );

      expect(result).toEqual({ success: true, data: 'success' });
      expect(mockOperation).toHaveBeenCalledTimes(3);
      expect(attemptCount).toBe(3);
    });

    it('should fail after maximum retry attempts', async () => {
      const mockOperation = jest.fn().mockRejectedValue(new Error('Persistent failure'));

      // Speed up test
      errorHandler.updateConfig({ baseRetryDelay: 1, maxRetries: 2 });

      await expect(
        errorHandler.retryOperation('network_timeout', mockOperation, { operation: 'test' })
      ).rejects.toThrow('Persistent failure');

      expect(mockOperation).toHaveBeenCalledTimes(3); // Initial attempt + 2 retries
    });

    it('should not retry non-retryable errors', async () => {
      const mockOperation = jest.fn().mockRejectedValue(new Error('Non-retryable error'));

      await expect(
        errorHandler.retryOperation('genesis_not_found', mockOperation, { operation: 'test' })
      ).rejects.toThrow('Error type genesis_not_found is not retryable');

      expect(mockOperation).not.toHaveBeenCalled();
    });

    it('should track retry attempts correctly', async () => {
      let attemptCount = 0;
      const mockOperation = jest.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 2) {
          throw new Error('Temporary failure');
        }
        return { success: true };
      });

      errorHandler.updateConfig({ baseRetryDelay: 1 });

      await errorHandler.retryOperation('network_timeout', mockOperation, { operation: 'test1' });

      const stats = errorHandler.getRetryStatistics();
      expect(stats.totalRetryKeys).toBe(0); // Should be cleared after success
    });

    it('should clear retry attempts for specific error types', async () => {
      // Set up some retry attempts
      const mockOperation = jest.fn().mockRejectedValue(new Error('Failure'));
      errorHandler.updateConfig({ baseRetryDelay: 1, maxRetries: 1 });

      try {
        await errorHandler.retryOperation('network_timeout', mockOperation, { operation: 'test1' });
      } catch (e) {
        // Expected to fail
      }

      try {
        await errorHandler.retryOperation('api_unavailable', mockOperation, { operation: 'test2' });
      } catch (e) {
        // Expected to fail
      }

      let stats = errorHandler.getRetryStatistics();
      expect(stats.totalRetryKeys).toBe(2);

      // Clear specific error type
      errorHandler.clearRetryAttempts('network_timeout', { operation: 'test1' });

      stats = errorHandler.getRetryStatistics();
      expect(stats.totalRetryKeys).toBe(1);

      // Clear all
      errorHandler.clearRetryAttempts();

      stats = errorHandler.getRetryStatistics();
      expect(stats.totalRetryKeys).toBe(0);
    });
  });

  describe('Error Categories and Severity', () => {
    it('should correctly categorize network errors', () => {
      expect(errorHandler.getErrorCategory('network_disconnected')).toBe(ErrorCategory.NETWORK);
      expect(errorHandler.getErrorCategory('network_timeout')).toBe(ErrorCategory.NETWORK);
      expect(errorHandler.getErrorCategory('api_unavailable')).toBe(ErrorCategory.NETWORK);
    });

    it('should correctly categorize genesis errors', () => {
      expect(errorHandler.getErrorCategory('genesis_not_found')).toBe(ErrorCategory.GENESIS);
      expect(errorHandler.getErrorCategory('genesis_invalid')).toBe(ErrorCategory.GENESIS);
    });

    it('should correctly categorize operation errors', () => {
      expect(errorHandler.getErrorCategory('operation_not_allowed')).toBe(ErrorCategory.OPERATION);
      expect(errorHandler.getErrorCategory('insufficient_balance')).toBe(ErrorCategory.OPERATION);
      expect(errorHandler.getErrorCategory('invalid_address')).toBe(ErrorCategory.OPERATION);
    });

    it('should correctly categorize system errors', () => {
      expect(errorHandler.getErrorCategory('wallet_not_found')).toBe(ErrorCategory.SYSTEM);
      expect(errorHandler.getErrorCategory('storage_error')).toBe(ErrorCategory.SYSTEM);
      expect(errorHandler.getErrorCategory('unknown_error')).toBe(ErrorCategory.SYSTEM);
    });
  });

  describe('Event Emission', () => {
    it('should emit errorHandled event when handling errors', (done) => {
      const originalError = new Error('Test error');
      const context = { operation: 'test' };

      errorHandler.on('errorHandled', (processedError) => {
        expect(processedError.type).toBe('network_timeout');
        expect(processedError.originalError.message).toBe('Test error');
        expect(processedError.context).toEqual(context);
        done();
      });

      errorHandler.handleError('network_timeout', originalError, context);
    });

    it('should emit retry events during retry operations', async () => {
      const events = [];
      let attemptCount = 0;

      const mockOperation = jest.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 2) {
          throw new Error('Temporary failure');
        }
        return { success: true };
      });

      errorHandler.on('retryAttempt', (data) => events.push({ type: 'attempt', data }));
      errorHandler.on('retrySuccess', (data) => events.push({ type: 'success', data }));
      errorHandler.on('retryFailed', (data) => events.push({ type: 'failed', data }));

      errorHandler.updateConfig({ baseRetryDelay: 1 });

      await errorHandler.retryOperation('network_timeout', mockOperation, { operation: 'test' });

      expect(events).toHaveLength(2); // One attempt, one success
      expect(events[0].type).toBe('attempt');
      expect(events[0].data.attempt).toBe(1);
      expect(events[1].type).toBe('success');
    });
  });

  describe('Configuration Updates', () => {
    it('should update configuration correctly', () => {
      const newConfig = {
        maxRetries: 5,
        baseRetryDelay: 2000,
        maxRetryDelay: 60000
      };

      errorHandler.updateConfig(newConfig);

      expect(errorHandler.config.maxRetries).toBe(5);
      expect(errorHandler.config.baseRetryDelay).toBe(2000);
      expect(errorHandler.config.maxRetryDelay).toBe(60000);
      expect(errorHandler.config.networkTimeout).toBe(10000); // Should preserve existing values
    });
  });

  describe('Cleanup', () => {
    it('should clean up resources properly', () => {
      // Add some retry attempts
      errorHandler.retryAttempts.set('test:key', 1);
      
      // Add event listeners
      const mockListener = jest.fn();
      errorHandler.on('test', mockListener);

      expect(errorHandler.retryAttempts.size).toBe(1);
      expect(errorHandler.listenerCount('test')).toBe(1);

      errorHandler.cleanup();

      expect(errorHandler.retryAttempts.size).toBe(0);
      expect(errorHandler.listenerCount('test')).toBe(0);
    });
  });
});