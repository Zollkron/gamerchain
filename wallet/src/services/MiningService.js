const AIModelService = require('./AIModelService');
const NetworkService = require('./NetworkService');

class MiningService {
  constructor() {
    this.isMining = false;
    this.currentModel = null;
    this.miningStats = {
      startTime: null,
      blocksValidated: 0,
      rewardsEarned: 0,
      challengesProcessed: 0,
      successRate: 100,
      reputation: 100
    };
    this.miningInterval = null;
    this.statusCallbacks = new Set();
  }

  /**
   * Add status change callback
   */
  onStatusChange(callback) {
    this.statusCallbacks.add(callback);
    return () => this.statusCallbacks.delete(callback);
  }

  /**
   * Notify status change
   */
  notifyStatusChange(status) {
    this.statusCallbacks.forEach(callback => {
      try {
        callback(status);
      } catch (error) {
        console.error('Error in mining status callback:', error);
      }
    });
  }

  /**
   * Get current mining status
   */
  getMiningStatus() {
    return {
      isMining: this.isMining,
      currentModel: this.currentModel,
      stats: {
        ...this.miningStats,
        uptime: this.miningStats.startTime ? 
          Date.now() - this.miningStats.startTime : 0
      },
      availableModels: AIModelService.getCertifiedModels(),
      installedModels: AIModelService.getInstalledModels()
    };
  }

  /**
   * Check if system meets requirements for mining
   */
  async checkMiningRequirements() {
    // Check network connectivity
    const networkStatus = await NetworkService.getNetworkStatus();
    if (!networkStatus.success) {
      return {
        canMine: false,
        issues: ['No hay conexión con la red testnet'],
        recommendations: [
          'Verifica que los nodos testnet estén ejecutándose',
          'Comprueba la conectividad de red'
        ]
      };
    }

    // Check if any models are installed
    const installedModels = AIModelService.getInstalledModels();
    if (installedModels.length === 0) {
      return {
        canMine: false,
        issues: ['No hay modelos IA instalados'],
        recommendations: [
          'Descarga al menos un modelo IA certificado',
          'Recomendamos Gemma 3 4B para hardware gaming'
        ]
      };
    }

    // Check system requirements (mock for now)
    const systemCheck = this.checkSystemCapabilities();
    if (!systemCheck.adequate) {
      return {
        canMine: false,
        issues: systemCheck.issues,
        recommendations: systemCheck.recommendations
      };
    }

    return {
      canMine: true,
      installedModels: installedModels.length,
      networkStatus: 'connected',
      systemStatus: 'adequate'
    };
  }

  /**
   * Check system capabilities (mock implementation)
   */
  checkSystemCapabilities() {
    // In a real implementation, this would check actual hardware
    return {
      adequate: true,
      gpu: 'RTX 4070 - 12GB VRAM',
      ram: '16GB available',
      cpu: '8 cores available',
      issues: [],
      recommendations: []
    };
  }

  /**
   * Start mining with specified model
   */
  async startMining(modelId, walletAddress) {
    if (this.isMining) {
      throw new Error('Mining is already active');
    }

    // Verify model is installed
    if (!AIModelService.isModelInstalled(modelId)) {
      throw new Error(`Model ${modelId} is not installed`);
    }

    // Check mining requirements
    const requirements = await this.checkMiningRequirements();
    if (!requirements.canMine) {
      throw new Error(`Cannot start mining: ${requirements.issues.join(', ')}`);
    }

    try {
      // Load the AI model
      console.log(`Loading AI model: ${modelId}`);
      const loadResult = await AIModelService.loadModel(modelId);
      if (!loadResult.success) {
        throw new Error(`Failed to load model: ${loadResult.error}`);
      }

      // Initialize mining state
      this.isMining = true;
      this.currentModel = {
        id: modelId,
        name: loadResult.name,
        loadedAt: new Date().toISOString()
      };
      
      this.miningStats = {
        startTime: Date.now(),
        blocksValidated: 0,
        rewardsEarned: 0,
        challengesProcessed: 0,
        successRate: 100,
        reputation: 100
      };

      // Start mining loop
      this.startMiningLoop(walletAddress);

      // Notify status change
      this.notifyStatusChange({
        event: 'mining_started',
        model: this.currentModel,
        walletAddress
      });

      return {
        success: true,
        message: `Mining started with ${loadResult.name}`,
        model: this.currentModel
      };

    } catch (error) {
      // Cleanup on error
      this.isMining = false;
      this.currentModel = null;
      throw error;
    }
  }

  /**
   * Stop mining
   */
  async stopMining() {
    if (!this.isMining) {
      throw new Error('Mining is not active');
    }

    // Stop mining loop
    if (this.miningInterval) {
      clearInterval(this.miningInterval);
      this.miningInterval = null;
    }

    // Update state
    const wasActive = this.isMining;
    this.isMining = false;
    const finalStats = { ...this.miningStats };
    this.currentModel = null;

    // Notify status change
    this.notifyStatusChange({
      event: 'mining_stopped',
      finalStats
    });

    return {
      success: true,
      message: 'Mining stopped successfully',
      finalStats
    };
  }

  /**
   * Start the mining loop
   */
  startMiningLoop(walletAddress) {
    // Simulate mining activity every 10 seconds
    this.miningInterval = setInterval(async () => {
      if (!this.isMining) return;

      try {
        await this.processMiningCycle(walletAddress);
      } catch (error) {
        console.error('Error in mining cycle:', error);
        // Continue mining despite errors
      }
    }, 10000); // 10 seconds per cycle
  }

  /**
   * Process a single mining cycle
   */
  async processMiningCycle(walletAddress) {
    if (!this.isMining || !this.currentModel) return;

    try {
      // Simulate receiving a challenge from the network
      const challenge = this.generateMockChallenge();
      
      // Process challenge with AI
      const result = await AIModelService.processChallenge(
        this.currentModel.id, 
        challenge
      );

      if (result.success) {
        // Update stats
        this.miningStats.challengesProcessed++;
        
        // Simulate occasional block validation (10% chance)
        if (Math.random() < 0.1) {
          this.miningStats.blocksValidated++;
          this.miningStats.rewardsEarned += 10 + Math.random() * 5; // 10-15 PRGLD
          
          this.notifyStatusChange({
            event: 'block_validated',
            reward: 10 + Math.random() * 5,
            blockNumber: this.miningStats.blocksValidated
          });
        }

        // Update success rate
        const successRate = (this.miningStats.challengesProcessed > 0) ?
          (this.miningStats.challengesProcessed / this.miningStats.challengesProcessed) * 100 : 100;
        this.miningStats.successRate = Math.min(successRate, 100);

        // Notify challenge processed
        this.notifyStatusChange({
          event: 'challenge_processed',
          challenge: challenge.id,
          processingTime: result.solution.processingTime,
          stats: this.miningStats
        });

      } else {
        console.error('Failed to process challenge:', result.error);
      }

    } catch (error) {
      console.error('Error in mining cycle:', error);
    }
  }

  /**
   * Generate mock challenge for testing
   */
  generateMockChallenge() {
    return {
      id: `challenge_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'mathematical',
      difficulty: 'medium',
      data: {
        problem: 'Solve mathematical optimization problem',
        constraints: ['constraint1', 'constraint2'],
        expectedTime: 200 // 200ms max
      },
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Get mining statistics
   */
  getMiningStats() {
    return {
      ...this.miningStats,
      uptime: this.miningStats.startTime ? 
        Date.now() - this.miningStats.startTime : 0,
      uptimeFormatted: this.formatUptime(
        this.miningStats.startTime ? 
        Date.now() - this.miningStats.startTime : 0
      )
    };
  }

  /**
   * Format uptime in human readable format
   */
  formatUptime(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    const h = hours % 24;
    const m = minutes % 60;
    const s = seconds % 60;

    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  /**
   * Estimate mining rewards
   */
  estimateMiningRewards() {
    // Mock estimation based on network conditions
    return {
      hourly: 5.2,
      daily: 125,
      weekly: 875,
      monthly: 3750,
      currency: 'PRGLD',
      factors: [
        'Network difficulty: Medium',
        'Your model: Efficient',
        'Hardware: Optimal',
        'Network participation: High'
      ]
    };
  }
}

module.exports = new MiningService();