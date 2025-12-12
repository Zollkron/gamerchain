/**
 * Unit Tests for AI Model Bootstrap Integration Service
 */

const AIModelBootstrapIntegration = require('../AIModelBootstrapIntegration');
const AIModelService = require('../AIModelService');
const { BootstrapService } = require('../BootstrapService');

// Mock AIModelService
jest.mock('../AIModelService', () => ({
  isModelInstalled: jest.fn(),
  downloadModel: jest.fn(),
  loadModel: jest.fn(),
  getCertifiedModels: jest.fn(),
  getInstalledModels: jest.fn()
}));

describe('AIModelBootstrapIntegration', () => {
  let bootstrapService;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Create fresh bootstrap service
    bootstrapService = new BootstrapService();
    AIModelBootstrapIntegration.setBootstrapService(bootstrapService);
    
    // Setup default mock responses
    AIModelService.getCertifiedModels.mockReturnValue([
      { id: 'gemma-3-4b', name: 'Gemma 3 4B' },
      { id: 'mistral-3b', name: 'Mistral 3B' }
    ]);
    
    AIModelService.getInstalledModels.mockReturnValue([
      { id: 'gemma-3-4b', name: 'Gemma 3 4B', isInstalled: true }
    ]);
  });

  afterEach(() => {
    if (bootstrapService) {
      bootstrapService.removeAllListeners();
    }
    AIModelBootstrapIntegration.cancelPreparation();
  });

  describe('Model Preparation', () => {
    it('should prepare model when already installed', async () => {
      const modelId = 'gemma-3-4b';
      const walletAddress = 'PG1234567890abcdef1234567890abcdef12345678';
      
      // Mock model as already installed
      AIModelService.isModelInstalled.mockReturnValue(true);
      AIModelService.loadModel.mockResolvedValue({
        success: true,
        name: 'Gemma 3 4B',
        loaded: true,
        path: '/models/gemma-3-4b.bin'
      });
      
      const result = await AIModelBootstrapIntegration.prepareModelForMining(modelId, walletAddress);
      
      expect(result.success).toBe(true);
      expect(result.modelId).toBe(modelId);
      expect(result.walletAddress).toBe(walletAddress);
      expect(AIModelService.downloadModel).not.toHaveBeenCalled();
      expect(AIModelService.loadModel).toHaveBeenCalledWith(modelId);
    });

    it('should download and prepare model when not installed', async () => {
      const modelId = 'mistral-3b';
      const walletAddress = 'PG1234567890abcdef1234567890abcdef12345678';
      
      // Mock model as not installed
      AIModelService.isModelInstalled.mockReturnValue(false);
      AIModelService.downloadModel.mockResolvedValue({
        success: true,
        modelId,
        path: '/models/mistral-3b.bin'
      });
      AIModelService.loadModel.mockResolvedValue({
        success: true,
        name: 'Mistral 3B',
        loaded: true,
        path: '/models/mistral-3b.bin'
      });
      
      const result = await AIModelBootstrapIntegration.prepareModelForMining(modelId, walletAddress);
      
      expect(result.success).toBe(true);
      expect(AIModelService.downloadModel).toHaveBeenCalledWith(modelId, expect.any(Function));
      expect(AIModelService.loadModel).toHaveBeenCalledWith(modelId);
    });

    it('should integrate with bootstrap service after preparation', async () => {
      const modelId = 'gemma-3-4b';
      const walletAddress = 'PG1234567890abcdef1234567890abcdef12345678';
      
      AIModelService.isModelInstalled.mockReturnValue(true);
      AIModelService.loadModel.mockResolvedValue({
        success: true,
        name: 'Gemma 3 4B',
        loaded: true,
        path: '/models/gemma-3-4b.bin'
      });
      
      // Spy on bootstrap service method
      const onMiningReadinessSpy = jest.spyOn(bootstrapService, 'onMiningReadiness');
      
      await AIModelBootstrapIntegration.prepareModelForMining(modelId, walletAddress);
      
      expect(onMiningReadinessSpy).toHaveBeenCalledWith(
        '/models/gemma-3-4b.bin',
        expect.objectContaining({
          id: modelId,
          name: 'Gemma 3 4B',
          walletAddress
        })
      );
    });
  });

  describe('Mining Readiness Check', () => {
    it('should return not ready when no wallet address', () => {
      const readiness = AIModelBootstrapIntegration.checkMiningReadiness();
      
      expect(readiness.ready).toBe(false);
      expect(readiness.reason).toBe('No wallet address provided');
    });

    it('should return not ready when no models installed', () => {
      AIModelService.getInstalledModels.mockReturnValue([]);
      
      const readiness = AIModelBootstrapIntegration.checkMiningReadiness('PG123');
      
      expect(readiness.ready).toBe(false);
      expect(readiness.reason).toBe('No AI models installed');
    });

    it('should return ready when all conditions met', () => {
      const walletAddress = 'PG1234567890abcdef1234567890abcdef12345678';
      
      // Setup bootstrap service state
      bootstrapService.onWalletAddressCreated(walletAddress);
      bootstrapService.onMiningReadiness('/models/test.bin', { id: 'test', name: 'Test Model' });
      
      const readiness = AIModelBootstrapIntegration.checkMiningReadiness(walletAddress);
      
      expect(readiness.ready).toBe(true);
      expect(readiness.walletAddress).toBe(walletAddress);
    });
  });

  describe('Model Recommendation', () => {
    it('should recommend Gemma 3 4B when available', () => {
      const recommended = AIModelBootstrapIntegration.getRecommendedModel();
      
      expect(recommended.id).toBe('gemma-3-4b');
      expect(recommended.reason).toContain('gaming');
    });

    it('should fallback to first available model', () => {
      AIModelService.getCertifiedModels.mockReturnValue([
        { id: 'other-model', name: 'Other Model' }
      ]);
      
      const recommended = AIModelBootstrapIntegration.getRecommendedModel();
      
      expect(recommended.id).toBe('other-model');
    });

    it('should return null when no models available', () => {
      AIModelService.getCertifiedModels.mockReturnValue([]);
      
      const recommended = AIModelBootstrapIntegration.getRecommendedModel();
      
      expect(recommended).toBeNull();
    });
  });

  describe('Mining Initiation', () => {
    it('should initiate mining with automatic model preparation', async () => {
      const walletAddress = 'PG1234567890abcdef1234567890abcdef12345678';
      
      AIModelService.isModelInstalled.mockReturnValue(true);
      AIModelService.loadModel.mockResolvedValue({
        success: true,
        name: 'Gemma 3 4B',
        loaded: true,
        path: '/models/gemma-3-4b.bin'
      });
      
      const result = await AIModelBootstrapIntegration.initiateMiningWithModelPreparation(walletAddress);
      
      expect(result.success).toBe(true);
      expect(result.mining.walletAddress).toBe(walletAddress);
      expect(result.mining.modelId).toBe('gemma-3-4b'); // Should use recommended
    });

    it('should use specified model when provided', async () => {
      const walletAddress = 'PG1234567890abcdef1234567890abcdef12345678';
      const modelId = 'mistral-3b';
      
      AIModelService.isModelInstalled.mockReturnValue(true);
      AIModelService.loadModel.mockResolvedValue({
        success: true,
        name: 'Mistral 3B',
        loaded: true,
        path: '/models/mistral-3b.bin'
      });
      
      const result = await AIModelBootstrapIntegration.initiateMiningWithModelPreparation(walletAddress, modelId);
      
      expect(result.success).toBe(true);
      expect(result.mining.modelId).toBe(modelId);
    });
  });
});