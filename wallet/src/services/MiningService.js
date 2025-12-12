const AIModelService = require('./AIModelService');
const NetworkService = require('./NetworkService');
const BlockchainNodeService = require('./BlockchainNodeService');
const AIModelBootstrapIntegration = require('./AIModelBootstrapIntegration');

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
    this.blockchainNodeRunning = false;
    
    // Listen to blockchain node events
    BlockchainNodeService.onStatusChange((status) => {
      this.handleBlockchainNodeEvent(status);
    });
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
   * Handle blockchain node events
   */
  handleBlockchainNodeEvent(status) {
    console.log('🔗 Blockchain node event:', status);
    
    switch (status.event) {
      case 'node_started':
        this.blockchainNodeRunning = true;
        this.notifyStatusChange({
          event: 'blockchain_node_started',
          nodeId: status.nodeId,
          port: status.port
        });
        break;
        
      case 'node_stopped':
        this.blockchainNodeRunning = false;
        this.notifyStatusChange({
          event: 'blockchain_node_stopped'
        });
        break;
        
      case 'genesis_created':
        this.notifyStatusChange({
          event: 'genesis_block_created',
          message: '¡Bloque génesis creado! La red blockchain está activa.'
        });
        break;
        
      case 'peer_discovered':
        this.notifyStatusChange({
          event: 'peer_discovered',
          message: 'Otro nodo pionero descubierto. Preparando para crear bloque génesis...'
        });
        break;
        
      case 'node_error':
        this.notifyStatusChange({
          event: 'blockchain_node_error',
          error: status.error
        });
        break;
    }
  }

  /**
   * Check if system meets requirements for mining
   */
  async checkMiningRequirements() {
    const issues = [];
    const recommendations = [];
    
    // Check if any models are installed
    const installedModels = AIModelService.getInstalledModels();
    if (installedModels.length === 0) {
      issues.push('No hay modelos IA instalados');
      recommendations.push('Descarga al menos un modelo IA certificado');
      recommendations.push('Recomendamos Gemma 3 4B para hardware gaming');
    }

    // Check system requirements
    const systemCheck = this.checkSystemCapabilities();
    if (!systemCheck.adequate) {
      issues.push(...systemCheck.issues);
      recommendations.push(...systemCheck.recommendations);
    }
    
    // Check blockchain node requirements
    const nodeRequirements = await BlockchainNodeService.checkSystemRequirements();
    if (!nodeRequirements.canRun) {
      issues.push('Sistema blockchain no disponible');
      issues.push(...nodeRequirements.issues);
      recommendations.push(...nodeRequirements.recommendations);
    }

    if (issues.length > 0) {
      return {
        canMine: false,
        issues,
        recommendations
      };
    }

    return {
      canMine: true,
      installedModels: installedModels.length,
      blockchainNodeAvailable: nodeRequirements.canRun,
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
   * Start mining with specified model (with automatic preparation)
   */
  async startMining(modelId, walletAddress) {
    if (this.isMining) {
      throw new Error('Mining is already active');
    }

    if (!modelId || !walletAddress) {
      throw new Error('Model ID and wallet address are required');
    }

    try {
      console.log('🚀 Starting mining process with automatic model preparation...');
      
      // Step 1: Use AI Model Bootstrap Integration for automatic preparation
      this.notifyStatusChange({
        event: 'preparing_model',
        message: 'Preparando modelo IA y configurando red...'
      });
      
      // Set up progress tracking for model preparation
      const progressUnsubscribe = AIModelBootstrapIntegration.onPreparationProgress((progress) => {
        this.notifyStatusChange({
          event: 'model_preparation_progress',
          progress: progress.progress,
          message: progress.message,
          phase: progress.phase
        });
      });
      
      try {
        // Initiate mining with automatic model preparation and bootstrap integration
        const miningResult = await AIModelBootstrapIntegration.initiateMiningWithModelPreparation(
          walletAddress, 
          modelId
        );
        
        if (!miningResult.success) {
          throw new Error('Model preparation and mining initiation failed');
        }
        
        // Step 2: Start blockchain node if not running
        if (!this.blockchainNodeRunning) {
          console.log('🔗 Starting blockchain node...');
          this.notifyStatusChange({
            event: 'starting_blockchain_node',
            message: 'Iniciando nodo blockchain...'
          });
          
          const nodeResult = await BlockchainNodeService.startNode();
          if (!nodeResult.success) {
            throw new Error(`Failed to start blockchain node: ${nodeResult.error}`);
          }
          
          console.log('✅ Blockchain node started successfully');
          this.blockchainNodeRunning = true;
        }
        
        // Step 3: Initialize mining state with prepared model
        this.isMining = true;
        this.currentModel = {
          id: miningResult.mining.modelId,
          name: miningResult.mining.modelInfo.name,
          loadedAt: miningResult.mining.modelInfo.loadedAt || new Date().toISOString(),
          preparationTime: miningResult.mining.preparationTime
        };
        
        this.miningStats = {
          startTime: Date.now(),
          blocksValidated: 0,
          rewardsEarned: 0,
          challengesProcessed: 0,
          successRate: 100,
          reputation: 100
        };

        // Step 4: Start mining loop
        this.startMiningLoop(walletAddress);

        // Step 5: Notify successful start
        this.notifyStatusChange({
          event: 'mining_started',
          model: this.currentModel,
          walletAddress,
          bootstrap: miningResult.bootstrap,
          message: `Minería iniciada con ${this.currentModel.name}. Buscando otros nodos pioneros...`
        });

        console.log('✅ Mining started successfully with bootstrap integration');
        
        return {
          success: true,
          message: `Mining started with ${this.currentModel.name}`,
          model: this.currentModel,
          bootstrap: miningResult.bootstrap,
          blockchainNode: {
            running: this.blockchainNodeRunning,
            nodeId: BlockchainNodeService.nodeId,
            apiUrl: BlockchainNodeService.getApiUrl()
          }
        };
        
      } finally {
        progressUnsubscribe();
      }

    } catch (error) {
      // Cleanup on error
      this.isMining = false;
      this.currentModel = null;
      
      console.error('❌ Failed to start mining:', error);
      
      this.notifyStatusChange({
        event: 'mining_start_failed',
        error: error.message
      });
      
      throw error;
    }
  }

  /**
   * Update mining stats from real blockchain node
   */
  async updateRealMiningStats() {
    try {
      // Get current wallet address (we need this to query mining stats)
      const WalletService = require('./WalletService');
      const wallets = WalletService.store.get('wallets', []);
      
      if (wallets.length === 0) return;
      
      const currentWallet = wallets[0]; // Use first wallet for now
      const address = currentWallet.address;
      
      // Try to get stats from local blockchain node first
      if (this.blockchainNodeRunning) {
        try {
          const localBalance = await BlockchainNodeService.getBalance(address);
          if (localBalance.success) {
            // Update balance information
            this.notifyStatusChange({
              event: 'balance_updated',
              balance: localBalance.balance,
              source: 'local_node'
            });
          }
          
          // Get network status from local node
          const networkStatus = await BlockchainNodeService.getNetworkStatus();
          if (networkStatus.success) {
            const status = networkStatus.status;
            
            // Update mining stats based on network status
            if (status.blockchain) {
              const currentHeight = status.blockchain.height;
              const previousBlocks = this.miningStats.blocksValidated;
              
              if (currentHeight > previousBlocks) {
                this.miningStats.blocksValidated = currentHeight;
                
                this.notifyStatusChange({
                  event: 'block_validated',
                  blockNumber: currentHeight,
                  peers: status.p2p?.peer_count || 0,
                  source: 'local_node'
                });
              }
            }
          }
        } catch (localError) {
          console.warn('Could not get stats from local node:', localError.message);
        }
      }
      
      // Fallback to remote network service
      try {
        const response = await NetworkService.getMiningStats(address);
        
        if (response.success && !response.mock) {
          const realStats = response.mining_stats;
          const previousBlocks = this.miningStats.blocksValidated;
          const previousRewards = this.miningStats.rewardsEarned;
          
          // Update stats with real data
          this.miningStats.blocksValidated = realStats.blocks_validated;
          this.miningStats.rewardsEarned = realStats.rewards_earned;
          this.miningStats.challengesProcessed = realStats.challenges_processed;
          this.miningStats.successRate = realStats.success_rate;
          this.miningStats.reputation = realStats.reputation;
          
          // Notify if new blocks were validated
          if (realStats.blocks_validated > previousBlocks) {
            const newRewards = realStats.rewards_earned - previousRewards;
            this.notifyStatusChange({
              event: 'block_validated',
              reward: newRewards,
              blockNumber: realStats.blocks_validated,
              source: 'remote_network'
            });
          }
        }
      } catch (remoteError) {
        console.warn('Could not get stats from remote network:', remoteError.message);
      }
      
    } catch (error) {
      console.error('Error updating mining stats:', error);
    }
  }

  /**
   * Stop mining
   */
  async stopMining() {
    if (!this.isMining) {
      throw new Error('Mining is not active');
    }

    try {
      console.log('🛑 Stopping mining...');

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

      // Optionally stop blockchain node (ask user or keep running for other wallets)
      // For now, we'll keep the node running as other wallet instances might be using it
      
      // Notify status change
      this.notifyStatusChange({
        event: 'mining_stopped',
        finalStats,
        message: 'Minería detenida. El nodo blockchain sigue ejecutándose.'
      });

      console.log('✅ Mining stopped successfully');

      return {
        success: true,
        message: 'Mining stopped successfully',
        finalStats,
        blockchainNode: {
          running: this.blockchainNodeRunning,
          message: 'Blockchain node is still running for network participation'
        }
      };
      
    } catch (error) {
      console.error('❌ Error stopping mining:', error);
      throw error;
    }
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
        
        // Update real mining stats from blockchain node
        await this.updateRealMiningStats();

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