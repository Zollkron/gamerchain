const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs').promises;
const EventEmitter = require('events');

class BlockchainSyncService extends EventEmitter {
  constructor() {
    super();
    this.isRunning = false;
    this.p2pProcess = null;
    this.apiProcess = null;
    this.syncStatus = {
      isConnected: false,
      isSyncing: false,
      currentBlock: 0,
      targetBlock: 0,
      syncProgress: 0,
      peers: 0,
      lastUpdate: null
    };
  }

  /**
   * Initialize and start all required services
   */
  async initialize() {
    try {
      this.emit('status', { type: 'info', message: 'Iniciando servicios de blockchain...' });
      
      // Check if we need admin privileges
      const needsAdmin = await this.checkAdminRequirements();
      if (needsAdmin) {
        this.emit('status', { 
          type: 'warning', 
          message: 'Se requieren permisos de administrador para iniciar los servicios de red' 
        });
        
        // Request admin privileges
        const hasAdmin = await this.requestAdminPrivileges();
        if (!hasAdmin) {
          throw new Error('Se requieren permisos de administrador para continuar');
        }
      }

      // Start P2P network service
      await this.startP2PService();
      
      // Wait for P2P to establish connections
      await this.waitForP2PConnection();
      
      // Sync blockchain
      await this.syncBlockchain();
      
      // Start API service
      await this.startAPIService();
      
      this.isRunning = true;
      this.emit('ready');
      
    } catch (error) {
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Check if admin privileges are required
   */
  async checkAdminRequirements() {
    // On Windows, we need admin for firewall and port binding
    if (process.platform === 'win32') {
      return true;
    }
    
    // On Linux/Mac, check if we need to bind to privileged ports
    return false;
  }

  /**
   * Request admin privileges
   */
  async requestAdminPrivileges() {
    return new Promise((resolve) => {
      if (process.platform === 'win32') {
        // On Windows, the app should be run as administrator
        // For now, we'll assume the user has the necessary privileges
        resolve(true);
      } else {
        // On Unix systems, we might need sudo
        resolve(true);
      }
    });
  }

  /**
   * Start P2P network service
   */
  async startP2PService() {
    return new Promise((resolve, reject) => {
      this.emit('status', { type: 'info', message: 'Iniciando servicio P2P...' });
      
      try {
        // Get the project root directory
        const projectRoot = path.resolve(__dirname, '../../../../');
        const scriptPath = path.join(projectRoot, 'scripts', 'start_testnet_node.py');
        
        // Start P2P node process
        this.p2pProcess = spawn('python', [scriptPath], {
          cwd: projectRoot,
          stdio: ['pipe', 'pipe', 'pipe'],
          env: { ...process.env, PYTHONPATH: projectRoot }
        });

        let startupComplete = false;

        this.p2pProcess.stdout.on('data', (data) => {
          const output = data.toString();
          console.log('P2P:', output);
          
          // Parse P2P status
          if (output.includes('P2P network started')) {
            if (!startupComplete) {
              startupComplete = true;
              this.emit('status', { type: 'success', message: 'Servicio P2P iniciado correctamente' });
              resolve();
            }
          }
          
          if (output.includes('Connected to bootstrap node')) {
            this.syncStatus.isConnected = true;
            this.updateSyncStatus();
          }
          
          // Parse peer count
          const peerMatch = output.match(/(\d+) peers, (\d+) connections/);
          if (peerMatch) {
            this.syncStatus.peers = parseInt(peerMatch[1]);
            this.updateSyncStatus();
          }
        });

        this.p2pProcess.stderr.on('data', (data) => {
          const error = data.toString();
          console.error('P2P Error:', error);
          
          if (error.includes('Permission denied') || error.includes('Access denied')) {
            reject(new Error('Permisos insuficientes para iniciar el servicio P2P'));
          }
        });

        this.p2pProcess.on('error', (error) => {
          console.error('P2P Process Error:', error);
          if (!startupComplete) {
            reject(error);
          }
        });

        this.p2pProcess.on('exit', (code) => {
          console.log(`P2P process exited with code ${code}`);
          this.syncStatus.isConnected = false;
          this.updateSyncStatus();
          
          if (!startupComplete && code !== 0) {
            reject(new Error(`P2P service failed to start (exit code: ${code})`));
          }
        });

        // Timeout after 30 seconds
        setTimeout(() => {
          if (!startupComplete) {
            reject(new Error('Timeout starting P2P service'));
          }
        }, 30000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Wait for P2P connection to be established
   */
  async waitForP2PConnection() {
    return new Promise((resolve, reject) => {
      this.emit('status', { type: 'info', message: 'Esperando conexión P2P...' });
      
      const checkConnection = () => {
        if (this.syncStatus.isConnected && this.syncStatus.peers > 0) {
          this.emit('status', { 
            type: 'success', 
            message: `Conectado a la red P2P (${this.syncStatus.peers} peers)` 
          });
          resolve();
        }
      };

      // Check immediately
      checkConnection();

      // Set up periodic check
      const interval = setInterval(() => {
        checkConnection();
      }, 2000);

      // Timeout after 60 seconds
      setTimeout(() => {
        clearInterval(interval);
        if (!this.syncStatus.isConnected) {
          reject(new Error('Timeout esperando conexión P2P'));
        }
      }, 60000);

      // Listen for connection updates
      this.on('syncStatusUpdate', () => {
        checkConnection();
        if (this.syncStatus.isConnected && this.syncStatus.peers > 0) {
          clearInterval(interval);
        }
      });
    });
  }

  /**
   * Sync blockchain with network
   */
  async syncBlockchain() {
    return new Promise((resolve, reject) => {
      this.emit('status', { type: 'info', message: 'Sincronizando blockchain...' });
      
      try {
        // Initialize blockchain service
        const BlockchainService = require('./BlockchainService');
        
        // Listen for blockchain service events
        BlockchainService.on('status', (status) => {
          this.emit('status', status);
        });
        
        BlockchainService.on('syncStatusUpdate', (status) => {
          this.syncStatus = { ...this.syncStatus, ...status };
          this.updateSyncStatus();
        });
        
        BlockchainService.on('ready', () => {
          this.syncStatus.isSyncing = false;
          this.syncStatus.syncProgress = 100;
          this.updateSyncStatus();
          resolve();
        });
        
        BlockchainService.on('error', (error) => {
          this.syncStatus.isSyncing = false;
          this.updateSyncStatus();
          reject(error);
        });
        
        // Start blockchain initialization
        BlockchainService.initialize().catch(reject);

      } catch (error) {
        this.syncStatus.isSyncing = false;
        this.updateSyncStatus();
        reject(error);
      }
    });
  }

  /**
   * Simulate blockchain synchronization
   */
  async simulateBlockchainSync() {
    // Simulate getting blockchain info from network
    await this.sleep(2000);
    
    this.emit('status', { 
      type: 'info', 
      message: 'Obteniendo información de blockchain de la red...' 
    });

    // Simulate discovering we need to sync blocks
    const localBlocks = 1; // Genesis block
    const networkBlocks = 150; // Simulate network has 150 blocks
    
    if (networkBlocks > localBlocks) {
      this.syncStatus.currentBlock = localBlocks;
      this.syncStatus.targetBlock = networkBlocks;
      this.updateSyncStatus();
      
      this.emit('status', { 
        type: 'info', 
        message: `Descargando ${networkBlocks - localBlocks} bloques...` 
      });

      // Simulate downloading blocks
      for (let i = localBlocks + 1; i <= networkBlocks; i++) {
        await this.sleep(100); // Simulate download time
        
        this.syncStatus.currentBlock = i;
        this.syncStatus.syncProgress = Math.round(((i - localBlocks) / (networkBlocks - localBlocks)) * 100);
        this.updateSyncStatus();
        
        this.emit('status', { 
          type: 'info', 
          message: `Descargando bloque ${i}/${networkBlocks} (${this.syncStatus.syncProgress}%)` 
        });
      }
    } else {
      this.emit('status', { 
        type: 'success', 
        message: 'Blockchain ya está sincronizado' 
      });
    }
  }

  /**
   * Start API service
   */
  async startAPIService() {
    return new Promise((resolve, reject) => {
      this.emit('status', { type: 'info', message: 'Iniciando API REST...' });
      
      try {
        // Get the project root directory
        const projectRoot = path.resolve(__dirname, '../../../../');
        const apiPath = path.join(projectRoot, 'api_final.py');
        
        // Start API process
        this.apiProcess = spawn('python', [apiPath], {
          cwd: projectRoot,
          stdio: ['pipe', 'pipe', 'pipe'],
          env: { ...process.env, PYTHONPATH: '' } // Clean PYTHONPATH
        });

        let startupComplete = false;

        this.apiProcess.stdout.on('data', (data) => {
          const output = data.toString();
          console.log('API:', output);
          
          if (output.includes('Running on http://127.0.0.1:18080')) {
            if (!startupComplete) {
              startupComplete = true;
              this.emit('status', { type: 'success', message: 'API REST iniciada correctamente' });
              resolve();
            }
          }
        });

        this.apiProcess.stderr.on('data', (data) => {
          const error = data.toString();
          console.error('API Error:', error);
        });

        this.apiProcess.on('error', (error) => {
          console.error('API Process Error:', error);
          if (!startupComplete) {
            reject(error);
          }
        });

        this.apiProcess.on('exit', (code) => {
          console.log(`API process exited with code ${code}`);
          if (!startupComplete && code !== 0) {
            reject(new Error(`API service failed to start (exit code: ${code})`));
          }
        });

        // Timeout after 15 seconds
        setTimeout(() => {
          if (!startupComplete) {
            reject(new Error('Timeout starting API service'));
          }
        }, 15000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Stop all services
   */
  async stop() {
    this.emit('status', { type: 'info', message: 'Deteniendo servicios...' });
    
    if (this.apiProcess) {
      this.apiProcess.kill();
      this.apiProcess = null;
    }
    
    if (this.p2pProcess) {
      this.p2pProcess.kill();
      this.p2pProcess = null;
    }
    
    this.isRunning = false;
    this.syncStatus.isConnected = false;
    this.syncStatus.isSyncing = false;
    this.updateSyncStatus();
    
    this.emit('status', { type: 'info', message: 'Servicios detenidos' });
  }

  /**
   * Get current sync status
   */
  getSyncStatus() {
    return { ...this.syncStatus };
  }

  /**
   * Update sync status and emit event
   */
  updateSyncStatus() {
    this.syncStatus.lastUpdate = new Date().toISOString();
    this.emit('syncStatusUpdate', this.syncStatus);
  }

  /**
   * Check if services are running
   */
  isServiceRunning() {
    return this.isRunning;
  }

  /**
   * Utility function to sleep
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = new BlockchainSyncService();