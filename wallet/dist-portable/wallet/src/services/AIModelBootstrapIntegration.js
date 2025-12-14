/**
 * AI Model Bootstrap Integration Service
 * 
 * Coordinates between AI model preparation and bootstrap process
 * Handles automatic model download, preparation, and mining readiness detection
 */

const AIModelService = require('./AIModelService');
const { BootstrapService } = require('./BootstrapService');
const { BootstrapLogger } = require('./BootstrapLogger');

class AIModelBootstrapIntegration {
  constructor() {
    this.logger = new BootstrapLogger('AIModelBootstrapIntegration');
    this.bootstrapService = null;
    this.currentModelPreparation = null;
    this.preparationCallbacks = new Set();
    
    this.logger.info('AI Model Bootstrap Integration initialized');
  }
  
  /**
   * Set the bootstrap service instance
   * @param {BootstrapService} bootstrapService - Bootstrap service instance
   */
  setBootstrapService(bootstrapService) {
    this.bootstrapService = bootstrapService;
    this.logger.info('Bootstrap service connected to AI model integration');
  }
  
  /**
   * Add preparation progress callback
   * @param {Function} callback - Progress callback function
   */
  onPreparationProgress(callback) {
    this.preparationCallbacks.add(callback);
    return () => this.preparationCallbacks.delete(callback);
  }
  
  /**
   * Notify preparation progress
   * @param {Object} progress - Progress information
   */
  notifyPreparationProgress(progress) {
    this.preparationCallbacks.forEach(callback => {
      try {
        callback(progress);
      } catch (error) {
        this.logger.error('Error in preparation progress callback:', error);
      }
    });
  }
  
  /**
   * Prepare AI model for mining and integrate with bootstrap
   * @param {string} modelId - Model ID to prepare
   * @param {string} walletAddress - Wallet address for mining
   * @returns {Promise<Object>} Preparation result
   */
  async prepareModelForMining(modelId, walletAddress) {
    if (!modelId || !walletAddress) {
      throw new Error('Model ID and wallet address are required');
    }
    
    if (this.currentModelPreparation) {
      throw new Error('Model preparation already in progress');
    }
    
    try {
      this.logger.info(`Starting model preparation for mining: ${modelId}`);
      
      this.currentModelPreparation = {
        modelId,
        walletAddress,
        startTime: Date.now(),
        phase: 'initializing'
      };
      
      // Phase 1: Check if model is already installed
      this.notifyPreparationProgress({
        phase: 'checking',
        message: 'Verificando disponibilidad del modelo...',
        progress: 10
      });
      
      const isInstalled = AIModelService.isModelInstalled(modelId);
      
      if (!isInstalled) {
        // Phase 2: Download model
        this.logger.info(`Model ${modelId} not installed, starting download`);
        
        this.notifyPreparationProgress({
          phase: 'downloading',
          message: 'Descargando modelo IA...',
          progress: 20
        });
        
        const downloadResult = await AIModelService.downloadModel(modelId, (progress) => {
          this.notifyPreparationProgress({
            phase: 'downloading',
            message: `Descargando modelo: ${progress.progress}%`,
            progress: 20 + (progress.progress * 0.5) // 20-70%
          });
        });
        
        if (!downloadResult.success) {
          throw new Error(`Model download failed: ${downloadResult.error}`);
        }
        
        this.logger.info(`Model ${modelId} downloaded successfully`);
      }
      
      // Phase 3: Load and verify model
      this.notifyPreparationProgress({
        phase: 'loading',
        message: 'Cargando y verificando modelo...',
        progress: 75
      });
      
      const loadResult = await AIModelService.loadModel(modelId);
      
      if (!loadResult.success) {
        throw new Error(`Model loading failed: ${loadResult.error}`);
      }
      
      // Phase 4: Integrate with bootstrap service
      this.notifyPreparationProgress({
        phase: 'integrating',
        message: 'Integrando con sistema de bootstrap...',
        progress: 90
      });
      
      const modelInfo = {
        id: modelId,
        name: loadResult.name,
        loadedAt: loadResult.loaded ? new Date().toISOString() : null,
        walletAddress: walletAddress
      };
      
      // Notify bootstrap service of mining readiness
      if (this.bootstrapService) {
        this.bootstrapService.onMiningReadiness(loadResult.path || `/models/${modelId}`, modelInfo);
      }
      
      // Phase 5: Complete
      this.notifyPreparationProgress({
        phase: 'completed',
        message: '¡Modelo preparado! Iniciando búsqueda de peers...',
        progress: 100
      });
      
      const result = {
        success: true,
        modelId,
        modelInfo,
        walletAddress,
        preparationTime: Date.now() - this.currentModelPreparation.startTime,
        message: `Model ${modelInfo.name} prepared successfully for mining`
      };
      
      this.logger.info(`Model preparation completed successfully: ${modelId}`);
      
      return result;
      
    } catch (error) {
      this.logger.error(`Model preparation failed: ${error.message}`, error);
      
      this.notifyPreparationProgress({
        phase: 'error',
        message: `Error: ${error.message}`,
        progress: 0,
        error: error.message
      });
      
      throw error;
      
    } finally {
      this.currentModelPreparation = null;
    }
  }
  
  /**
   * Check mining readiness state
   * @param {string} walletAddress - Wallet address to check
   * @returns {Object} Readiness state
   */
  checkMiningReadiness(walletAddress) {
    if (!walletAddress) {
      return {
        ready: false,
        reason: 'No wallet address provided',
        requirements: ['Valid wallet address', 'AI model selection', 'Model preparation']
      };
    }
    
    const installedModels = AIModelService.getInstalledModels();
    
    if (installedModels.length === 0) {
      return {
        ready: false,
        reason: 'No AI models installed',
        requirements: ['Download and install at least one AI model'],
        availableModels: AIModelService.getCertifiedModels()
      };
    }
    
    // Check if bootstrap service is ready
    if (this.bootstrapService) {
      const bootstrapState = this.bootstrapService.getState();
      
      if (bootstrapState.walletAddress && bootstrapState.selectedModel && bootstrapState.isReady) {
        return {
          ready: true,
          walletAddress: bootstrapState.walletAddress,
          selectedModel: bootstrapState.selectedModel,
          modelInfo: bootstrapState.modelInfo,
          bootstrapMode: bootstrapState.mode
        };
      }
    }
    
    return {
      ready: false,
      reason: 'Bootstrap service not ready',
      walletAddress,
      installedModels: installedModels.length,
      requirements: ['Complete model preparation', 'Bootstrap service initialization']
    };
  }
  
  /**
   * Get current preparation status
   * @returns {Object|null} Current preparation status or null
   */
  getCurrentPreparationStatus() {
    return this.currentModelPreparation ? {
      ...this.currentModelPreparation,
      elapsed: Date.now() - this.currentModelPreparation.startTime
    } : null;
  }
  
  /**
   * Cancel current model preparation
   */
  cancelPreparation() {
    if (this.currentModelPreparation) {
      this.logger.info(`Cancelling model preparation: ${this.currentModelPreparation.modelId}`);
      
      this.notifyPreparationProgress({
        phase: 'cancelled',
        message: 'Preparación cancelada',
        progress: 0
      });
      
      this.currentModelPreparation = null;
    }
  }
  
  /**
   * Get recommended model for user's system
   * @returns {Object|null} Recommended model or null
   */
  getRecommendedModel() {
    const certifiedModels = AIModelService.getCertifiedModels();
    
    // Simple recommendation logic - prefer Gemma 3 4B for gaming hardware
    const recommended = certifiedModels.find(model => model.id === 'gemma-3-4b');
    
    if (recommended) {
      return {
        ...recommended,
        reason: 'Optimizado para hardware gaming y minería eficiente'
      };
    }
    
    // Fallback to first available model
    return certifiedModels.length > 0 ? {
      ...certifiedModels[0],
      reason: 'Modelo disponible compatible'
    } : null;
  }
  
  /**
   * Initiate mining with automatic model preparation
   * @param {string} walletAddress - Wallet address for mining
   * @param {string} modelId - Optional specific model ID, uses recommended if not provided
   * @returns {Promise<Object>} Mining initiation result
   */
  async initiateMiningWithModelPreparation(walletAddress, modelId = null) {
    if (!walletAddress) {
      throw new Error('Wallet address is required for mining initiation');
    }
    
    // Use recommended model if none specified
    if (!modelId) {
      const recommended = this.getRecommendedModel();
      if (!recommended) {
        throw new Error('No AI models available for mining');
      }
      modelId = recommended.id;
      this.logger.info(`Using recommended model for mining: ${modelId}`);
    }
    
    try {
      // Prepare model for mining
      const preparationResult = await this.prepareModelForMining(modelId, walletAddress);
      
      // The bootstrap service should now be in peer discovery mode
      // due to the onMiningReadiness call in prepareModelForMining
      
      return {
        success: true,
        mining: {
          walletAddress,
          modelId,
          modelInfo: preparationResult.modelInfo,
          preparationTime: preparationResult.preparationTime
        },
        bootstrap: this.bootstrapService ? this.bootstrapService.getState() : null,
        message: 'Mining initiated successfully with automatic model preparation'
      };
      
    } catch (error) {
      this.logger.error(`Mining initiation failed: ${error.message}`, error);
      throw error;
    }
  }
}

module.exports = new AIModelBootstrapIntegration();