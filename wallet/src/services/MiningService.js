import { aiModelService } from './AIModelService';

class MiningService {
  constructor() {
    this.miningStatus = 'stopped';
    this.currentModel = null;
    this.nodeId = null;
    this.startTime = null;
    this.statusListeners = [];
    this.metricsInterval = null;
  }

  /**
   * Add status change listener
   */
  addStatusListener(callback) {
    this.statusListeners.push(callback);
  }

  /**
   * Remove status change listener
   */
  removeStatusListener(callback) {
    this.statusListeners = this.statusListeners.filter(cb => cb !== callback);
  }

  /**
   * Notify all status listeners
   */
  notifyStatusChange(status, data = {}) {
    this.statusListeners.forEach(callback => {
      try {
        callback(status, data);
      } catch (error) {
        console.error('Error in status listener:', error);
      }
    });
  }

  /**
   * Start mining with specified AI model
   */
  async startMining(modelId, walletAddress) {
    if (this.miningStatus !== 'stopped') {
      throw new Error('La minería ya está en progreso');
    }

    try {
      this.miningStatus = 'starting';
      this.notifyStatusChange('starting', { modelId });

      // Load the AI model
      const modelInfo = await aiModelService.loadModel(modelId);
      
      // Initialize mining node
      const nodeInfo = await this.initializeMiningNode(modelId, walletAddress);
      
      // Connect to P2P network
      await this.connectToNetwork(nodeInfo);
      
      // Start consensus participation
      await this.startConsensusParticipation();

      this.miningStatus = 'running';
      this.currentModel = modelInfo;
      this.nodeId = nodeInfo.nodeId;
      this.startTime = new Date();

      // Start metrics collection
      this.startMetricsCollection();

      this.notifyStatusChange('running', {
        modelId,
        nodeId: this.nodeId,
        startTime: this.startTime
      });

      return {
        success: true,
        nodeId: this.nodeId,
        model: modelInfo,
        status: 'running'
      };

    } catch (error) {
      this.miningStatus = 'stopped';
      this.notifyStatusChange('error', { error: error.message });
      throw error;
    }
  }

  /**
   * Stop mining
   */
  async stopMining() {
    if (this.miningStatus === 'stopped') {
      return { success: true, message: 'La minería ya está detenida' };
    }

    try {
      this.miningStatus = 'stopping';
      this.notifyStatusChange('stopping');

      // Stop metrics collection
      this.stopMetricsCollection();

      // Disconnect from consensus
      await this.stopConsensusParticipation();

      // Disconnect from P2P network
      await this.disconnectFromNetwork();

      // Unload AI model
      if (this.currentModel) {
        await aiModelService.unloadModel(this.currentModel.modelId);
      }

      // Reset state
      this.miningStatus = 'stopped';
      this.currentModel = null;
      this.nodeId = null;
      this.startTime = null;

      this.notifyStatusChange('stopped');

      return {
        success: true,
        message: 'Minería detenida correctamente'
      };

    } catch (error) {
      this.notifyStatusChange('error', { error: error.message });
      throw error;
    }
  }

  /**
   * Get current mining status
   */
  getMiningStatus() {
    return {
      status: this.miningStatus,
      model: this.currentModel,
      nodeId: this.nodeId,
      startTime: this.startTime,
      uptime: this.startTime ? Date.now() - this.startTime.getTime() : 0
    };
  }

  /**
   * Initialize mining node
   */
  async initializeMiningNode(modelId, walletAddress) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        // Simulate node initialization
        const success = Math.random() > 0.15; // 85% success rate
        
        if (success) {
          const nodeId = this.generateNodeId();
          resolve({
            nodeId,
            modelId,
            walletAddress,
            initialized: true,
            timestamp: new Date().toISOString()
          });
        } else {
          reject(new Error('Error inicializando nodo IA. Verifica los requisitos del sistema.'));
        }
      }, 2000);
    });
  }

  /**
   * Connect to P2P network
   */
  async connectToNetwork(nodeInfo) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        // Simulate network connection
        const success = Math.random() > 0.1; // 90% success rate
        
        if (success) {
          resolve({
            connected: true,
            peers: Math.floor(Math.random() * 20) + 8, // 8-28 peers
            networkId: 'playergold-mainnet',
            latency: Math.floor(Math.random() * 100) + 20 // 20-120ms
          });
        } else {
          reject(new Error('Error conectando a la red P2P. Verifica tu conexión a internet.'));
        }
      }, 1500);
    });
  }

  /**
   * Start consensus participation
   */
  async startConsensusParticipation() {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        // Simulate consensus participation
        const accepted = Math.random() > 0.2; // 80% acceptance rate
        
        if (accepted) {
          resolve({
            participating: true,
            validatorStatus: 'active',
            reputationScore: 75 + Math.random() * 20, // 75-95
            challengesReceived: 0
          });
        } else {
          reject(new Error('Nodo rechazado por la red. El modelo IA no pasó las pruebas de validación.'));
        }
      }, 1000);
    });
  }

  /**
   * Stop consensus participation
   */
  async stopConsensusParticipation() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          participating: false,
          validatorStatus: 'inactive',
          finalStats: this.getFinalMiningStats()
        });
      }, 1000);
    });
  }

  /**
   * Disconnect from P2P network
   */
  async disconnectFromNetwork() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          connected: false,
          peers: 0,
          disconnectedAt: new Date().toISOString()
        });
      }, 500);
    });
  }

  /**
   * Start metrics collection
   */
  startMetricsCollection() {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }

    this.metricsInterval = setInterval(() => {
      if (this.miningStatus === 'running' && this.currentModel) {
        const metrics = this.generateMiningMetrics();
        this.notifyStatusChange('metrics', metrics);
      }
    }, 5000); // Update every 5 seconds
  }

  /**
   * Stop metrics collection
   */
  stopMetricsCollection() {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = null;
    }
  }

  /**
   * Generate mining metrics
   */
  generateMiningMetrics() {
    const uptime = this.startTime ? Date.now() - this.startTime.getTime() : 0;
    const hours = uptime / (1000 * 60 * 60);
    
    return {
      nodeId: this.nodeId,
      status: 'validating',
      uptime,
      validationsCount: Math.floor(hours * 120) + Math.floor(Math.random() * 50), // ~120 per hour
      reputationScore: 75 + Math.random() * 20 + (hours * 0.5), // Increases over time
      peersConnected: 8 + Math.floor(Math.random() * 15),
      lastChallenge: new Date(Date.now() - Math.random() * 300000), // Within last 5 minutes
      earnings: {
        today: hours * 1.2 + Math.random() * 0.5, // ~1.2 PRGLD per hour
        total: this.getTotalEarnings() + (hours * 1.2)
      },
      performance: {
        challengeSuccessRate: 95 + Math.random() * 5, // 95-100%
        averageResponseTime: 45 + Math.random() * 25, // 45-70ms
        networkLatency: 20 + Math.random() * 80, // 20-100ms
        memoryUsage: 3.2 + Math.random() * 1.5, // GB
        cpuUsage: 25 + Math.random() * 35, // 25-60%
        gpuUsage: 65 + Math.random() * 25 // 65-90%
      }
    };
  }

  /**
   * Get total earnings from localStorage
   */
  getTotalEarnings() {
    try {
      const earnings = localStorage.getItem('totalMiningEarnings');
      return earnings ? parseFloat(earnings) : 0;
    } catch (error) {
      return 0;
    }
  }

  /**
   * Update total earnings
   */
  updateTotalEarnings(amount) {
    try {
      const current = this.getTotalEarnings();
      const updated = current + amount;
      localStorage.setItem('totalMiningEarnings', updated.toString());
      return updated;
    } catch (error) {
      console.error('Error updating earnings:', error);
      return 0;
    }
  }

  /**
   * Get final mining statistics
   */
  getFinalMiningStats() {
    if (!this.startTime) return null;

    const uptime = Date.now() - this.startTime.getTime();
    const hours = uptime / (1000 * 60 * 60);
    const earnings = hours * 1.2; // Approximate earnings

    // Update total earnings
    this.updateTotalEarnings(earnings);

    return {
      sessionDuration: uptime,
      validationsCompleted: Math.floor(hours * 120),
      earningsThisSession: earnings,
      averageReputationScore: 85 + Math.random() * 10,
      challengeSuccessRate: 95 + Math.random() * 5,
      networkContribution: 'Excellent'
    };
  }

  /**
   * Generate unique node ID
   */
  generateNodeId() {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 9);
    return `node_${timestamp}_${random}`;
  }

  /**
   * Get mining history
   */
  getMiningHistory() {
    try {
      const history = localStorage.getItem('miningHistory');
      return history ? JSON.parse(history) : [];
    } catch (error) {
      return [];
    }
  }

  /**
   * Add mining session to history
   */
  addMiningSession(sessionData) {
    try {
      const history = this.getMiningHistory();
      history.unshift({
        ...sessionData,
        id: Date.now(),
        timestamp: new Date().toISOString()
      });

      // Keep only last 50 sessions
      const trimmed = history.slice(0, 50);
      localStorage.setItem('miningHistory', JSON.stringify(trimmed));
      
      return trimmed;
    } catch (error) {
      console.error('Error saving mining session:', error);
      return [];
    }
  }

  /**
   * Get mining statistics
   */
  getMiningStatistics() {
    const history = this.getMiningHistory();
    const totalEarnings = this.getTotalEarnings();
    
    if (history.length === 0) {
      return {
        totalSessions: 0,
        totalUptime: 0,
        totalEarnings: 0,
        averageSessionDuration: 0,
        totalValidations: 0,
        averageSuccessRate: 0
      };
    }

    const totalUptime = history.reduce((sum, session) => sum + (session.sessionDuration || 0), 0);
    const totalValidations = history.reduce((sum, session) => sum + (session.validationsCompleted || 0), 0);
    const averageSuccessRate = history.reduce((sum, session) => sum + (session.challengeSuccessRate || 0), 0) / history.length;

    return {
      totalSessions: history.length,
      totalUptime,
      totalEarnings,
      averageSessionDuration: totalUptime / history.length,
      totalValidations,
      averageSuccessRate
    };
  }
}

export const miningService = new MiningService();
export default MiningService;