const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

class BlockchainNodeService {
  constructor() {
    this.nodeProcess = null;
    this.nodeId = null;
    this.isRunning = false;
    this.port = 18080; // Default testnet port
    this.apiPort = 19080; // API port
    this.statusCallbacks = new Set();
    
    // Auto-generate unique node ID
    this.nodeId = this.generateNodeId();
    
    // Node configuration
    this.config = {
      network: 'testnet',
      logLevel: 'INFO',
      autoStart: false
    };
    
    console.log(`🤖 BlockchainNodeService initialized with node ID: ${this.nodeId}`);
  }

  /**
   * Generate unique node ID for this wallet instance
   */
  generateNodeId() {
    // Try to load existing node ID from storage
    const nodeIdFile = path.join(process.cwd(), 'data', 'node_id.txt');
    
    try {
      if (fs.existsSync(nodeIdFile)) {
        const existingId = fs.readFileSync(nodeIdFile, 'utf8').trim();
        if (existingId) {
          console.log(`📂 Loaded existing node ID: ${existingId}`);
          return existingId;
        }
      }
    } catch (error) {
      console.warn('Could not load existing node ID:', error.message);
    }
    
    // Generate new node ID
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 8);
    const newNodeId = `pioneer_${timestamp}_${random}`;
    
    // Save node ID for future use
    try {
      const dataDir = path.dirname(nodeIdFile);
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }
      fs.writeFileSync(nodeIdFile, newNodeId);
      console.log(`💾 Saved new node ID: ${newNodeId}`);
    } catch (error) {
      console.warn('Could not save node ID:', error.message);
    }
    
    return newNodeId;
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
        console.error('Error in blockchain node status callback:', error);
      }
    });
  }

  /**
   * Get current node status
   */
  getNodeStatus() {
    return {
      isRunning: this.isRunning,
      nodeId: this.nodeId,
      port: this.port,
      apiPort: this.apiPort,
      network: this.config.network,
      processId: this.nodeProcess ? this.nodeProcess.pid : null
    };
  }

  /**
   * Check if Python and required dependencies are available
   */
  async checkSystemRequirements() {
    try {
      // Check if we can find the Python script
      const scriptPath = this.getNodeScriptPath();
      
      if (!fs.existsSync(scriptPath)) {
        return {
          canRun: false,
          issues: [
            'Backend blockchain script not found',
            `Expected location: ${scriptPath}`,
            'This is required for mining operations'
          ],
          recommendations: [
            'Ensure you are running from the correct directory',
            'Try running from the project root directory',
            'Check that scripts/start_multinode_network.py exists',
            'Use wallet mode: cd wallet && npm start'
          ],
          scriptPath,
          searchedPaths: this.getSearchedPaths()
        };
      }

      // Check if Python is available
      return new Promise((resolve) => {
        const pythonCheck = spawn('python', ['--version'], { 
          stdio: 'pipe',
          shell: true 
        });
        
        let pythonAvailable = false;
        
        pythonCheck.on('close', (code) => {
          if (code === 0 || pythonAvailable) {
            resolve({
              canRun: true,
              pythonAvailable: true,
              scriptPath
            });
          } else {
            resolve({
              canRun: false,
              issues: ['Python not found in system PATH'],
              recommendations: [
                'Install Python 3.8 or higher',
                'Ensure Python is added to system PATH',
                'Restart the wallet after installing Python'
              ],
              scriptPath
            });
          }
        });
        
        pythonCheck.stdout.on('data', (data) => {
          if (data.toString().includes('Python')) {
            pythonAvailable = true;
          }
        });
        
        pythonCheck.stderr.on('data', (data) => {
          if (data.toString().includes('Python')) {
            pythonAvailable = true;
          }
        });
        
        // Timeout after 5 seconds
        setTimeout(() => {
          pythonCheck.kill();
          resolve({
            canRun: false,
            issues: ['Python check timed out'],
            recommendations: [
              'Install Python 3.8 or higher',
              'Ensure Python is accessible from command line'
            ],
            scriptPath
          });
        }, 5000);
      });
      
    } catch (error) {
      return {
        canRun: false,
        issues: [`System check failed: ${error.message}`],
        recommendations: [
          'Check system configuration',
          'Ensure all dependencies are installed'
        ]
      };
    }
  }

  /**
   * Get path to the blockchain node script
   */
  getNodeScriptPath() {
    // Try different possible locations for the script
    const possiblePaths = [];
    
    // Production path (bundled with app) - only if resourcesPath is available
    if (process.resourcesPath) {
      possiblePaths.push(path.join(process.resourcesPath, 'scripts', 'start_multinode_network.py'));
    }
    
    // Development paths
    possiblePaths.push(
      // Development path (from wallet directory to parent scripts)
      path.join(process.cwd(), '..', 'scripts', 'start_multinode_network.py'),
      // Relative to wallet directory
      path.join(process.cwd(), 'scripts', 'start_multinode_network.py'),
      // Absolute path from project root
      path.resolve(process.cwd(), '..', 'scripts', 'start_multinode_network.py'),
      // Try from project root if we're in wallet subdirectory
      path.resolve(__dirname, '..', '..', '..', 'scripts', 'start_multinode_network.py')
    );
    
    console.log('🔍 Searching for blockchain script in:');
    for (const scriptPath of possiblePaths) {
      console.log(`   Checking: ${scriptPath}`);
      if (fs.existsSync(scriptPath)) {
        console.log(`✅ Found script at: ${scriptPath}`);
        return scriptPath;
      }
    }
    
    // If not found, return the most likely development path and let it fail with a clear error
    const fallbackPath = path.join(process.cwd(), '..', 'scripts', 'start_multinode_network.py');
    console.error(`❌ Script not found in any location. Using fallback: ${fallbackPath}`);
    return fallbackPath;
  }

  /**
   * Get list of paths searched for debugging
   */
  getSearchedPaths() {
    const paths = [];
    
    // Production path (only if resourcesPath is available)
    if (process.resourcesPath) {
      paths.push(path.join(process.resourcesPath, 'scripts', 'start_multinode_network.py'));
    }
    
    // Development paths
    paths.push(
      path.join(process.cwd(), '..', 'scripts', 'start_multinode_network.py'),
      path.join(process.cwd(), 'scripts', 'start_multinode_network.py'),
      path.resolve(process.cwd(), '..', 'scripts', 'start_multinode_network.py'),
      path.resolve(__dirname, '..', '..', '..', 'scripts', 'start_multinode_network.py')
    );
    
    return paths;
  }

  /**
   * Find available port for the node
   */
  async findAvailablePort(startPort = 18080) {
    const net = require('net');
    
    return new Promise((resolve) => {
      const server = net.createServer();
      
      server.listen(startPort, () => {
        const port = server.address().port;
        server.close(() => {
          resolve(port);
        });
      });
      
      server.on('error', () => {
        // Port is busy, try next one
        resolve(this.findAvailablePort(startPort + 1));
      });
    });
  }

  /**
   * Start the blockchain node
   */
  async startNode(options = {}) {
    if (this.isRunning) {
      throw new Error('Blockchain node is already running');
    }

    // Check system requirements
    const requirements = await this.checkSystemRequirements();
    if (!requirements.canRun) {
      throw new Error(`Cannot start node: ${requirements.issues.join(', ')}`);
    }

    try {
      console.log('🚀 Starting blockchain node...');
      
      // Find available port
      this.port = await this.findAvailablePort(18080);
      this.apiPort = this.port + 1000;
      
      console.log(`📡 Using P2P port: ${this.port}`);
      console.log(`🌐 Using API port: ${this.apiPort}`);
      
      // Prepare node arguments
      const scriptPath = this.getNodeScriptPath();
      const args = [
        scriptPath,
        '--node-id', this.nodeId,
        '--port', this.port.toString(),
        '--network', this.config.network,
        '--log-level', this.config.logLevel
      ];
      
      // Add bootstrap nodes if we're not the first node
      const bootstrapNodes = await this.discoverBootstrapNodes();
      if (bootstrapNodes.length > 0) {
        bootstrapNodes.forEach(node => {
          args.push('--bootstrap', node);
        });
        console.log(`🔗 Using bootstrap nodes: ${bootstrapNodes.join(', ')}`);
      } else {
        console.log('🏗️  No bootstrap nodes found - will be a pioneer node');
      }
      
      console.log(`🐍 Starting Python process: python ${args.join(' ')}`);
      
      // Start the Python process
      this.nodeProcess = spawn('python', args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true,
        cwd: path.dirname(scriptPath)
      });
      
      // Handle process output
      this.nodeProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`[NODE] ${output.trim()}`);
        
        // Parse important events
        if (output.includes('Multi-Node Network started successfully')) {
          this.isRunning = true;
          this.notifyStatusChange({
            event: 'node_started',
            nodeId: this.nodeId,
            port: this.port,
            apiPort: this.apiPort
          });
        }
        
        if (output.includes('Genesis block created')) {
          this.notifyStatusChange({
            event: 'genesis_created',
            nodeId: this.nodeId
          });
        }
        
        if (output.includes('Pioneer AI node discovered')) {
          this.notifyStatusChange({
            event: 'peer_discovered',
            nodeId: this.nodeId
          });
        }
      });
      
      this.nodeProcess.stderr.on('data', (data) => {
        const error = data.toString();
        console.error(`[NODE ERROR] ${error.trim()}`);
        
        // Notify about errors
        this.notifyStatusChange({
          event: 'node_error',
          error: error.trim()
        });
      });
      
      this.nodeProcess.on('close', (code) => {
        console.log(`[NODE] Process exited with code ${code}`);
        this.isRunning = false;
        this.nodeProcess = null;
        
        this.notifyStatusChange({
          event: 'node_stopped',
          exitCode: code
        });
      });
      
      this.nodeProcess.on('error', (error) => {
        console.error(`[NODE] Process error:`, error);
        this.isRunning = false;
        this.nodeProcess = null;
        
        this.notifyStatusChange({
          event: 'node_error',
          error: error.message
        });
      });
      
      // Wait a bit for the process to start
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Verify the node is responding
      const isHealthy = await this.checkNodeHealth();
      if (!isHealthy) {
        console.warn('⚠️ Node may not be responding correctly');
      }
      
      console.log('✅ Blockchain node started successfully');
      
      return {
        success: true,
        nodeId: this.nodeId,
        port: this.port,
        apiPort: this.apiPort,
        message: 'Blockchain node started successfully'
      };
      
    } catch (error) {
      console.error('❌ Failed to start blockchain node:', error);
      this.isRunning = false;
      this.nodeProcess = null;
      throw error;
    }
  }

  /**
   * Stop the blockchain node
   */
  async stopNode() {
    if (!this.isRunning || !this.nodeProcess) {
      throw new Error('Blockchain node is not running');
    }

    try {
      console.log('🛑 Stopping blockchain node...');
      
      // Send termination signal
      this.nodeProcess.kill('SIGTERM');
      
      // Wait for graceful shutdown
      await new Promise((resolve) => {
        const timeout = setTimeout(() => {
          // Force kill if not stopped gracefully
          if (this.nodeProcess) {
            console.log('🔨 Force killing node process...');
            this.nodeProcess.kill('SIGKILL');
          }
          resolve();
        }, 10000); // 10 second timeout
        
        this.nodeProcess.on('close', () => {
          clearTimeout(timeout);
          resolve();
        });
      });
      
      this.isRunning = false;
      this.nodeProcess = null;
      
      console.log('✅ Blockchain node stopped successfully');
      
      return {
        success: true,
        message: 'Blockchain node stopped successfully'
      };
      
    } catch (error) {
      console.error('❌ Failed to stop blockchain node:', error);
      throw error;
    }
  }

  /**
   * Check if the node is healthy and responding
   */
  async checkNodeHealth() {
    try {
      const response = await axios.get(`http://127.0.0.1:${this.apiPort}/api/v1/health`, {
        timeout: 5000
      });
      
      return response.status === 200 && response.data.status === 'healthy';
    } catch (error) {
      console.warn('Node health check failed:', error.message);
      return false;
    }
  }

  /**
   * Get node network status - For remote gamer scenario, return mock status
   */
  async getNetworkStatus() {
    // For remote gamer scenario, we don't run local blockchain nodes
    // Return a mock status that indicates remote coordination mode
    return {
      success: true,
      status: {
        mode: 'remote_coordination',
        network: 'testnet',
        ready: true,
        message: 'Using remote peer coordination through Network Coordinator'
      }
    };
  }

  /**
   * Discover other nodes on the local network for bootstrap
   */
  async discoverBootstrapNodes() {
    const bootstrapNodes = [];
    
    // Check common ports for other nodes
    const commonPorts = [18080, 18081, 18082, 18083];
    
    for (const port of commonPorts) {
      if (port === this.port) continue; // Skip our own port
      
      try {
        const response = await axios.get(`http://127.0.0.1:${port + 1000}/api/v1/health`, {
          timeout: 1000
        });
        
        if (response.status === 200) {
          bootstrapNodes.push(`127.0.0.1:${port}`);
          console.log(`🔍 Discovered node at port ${port}`);
        }
      } catch (error) {
        // Node not found on this port, continue
      }
    }
    
    return bootstrapNodes;
  }

  /**
   * Get API URL for this node
   */
  getApiUrl() {
    if (!this.isRunning) {
      return null;
    }
    
    return `http://127.0.0.1:${this.apiPort}`;
  }

  /**
   * Request faucet tokens (if node is running)
   */
  async requestFaucetTokens(address, amount = 1000) {
    try {
      if (!this.isRunning) {
        throw new Error('Node is not running');
      }
      
      const response = await axios.post(`http://127.0.0.1:${this.apiPort}/api/v1/faucet`, {
        address: address,
        amount: amount
      }, {
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      return {
        success: true,
        transactionId: response.data.transactionId || 'faucet_tx_' + Date.now(),
        amount: amount,
        address: address,
        message: response.data.message || `Requested ${amount} PRGLD from local node faucet`
      };
    } catch (error) {
      console.error('❌ Local faucet request failed:', error.message);
      
      return {
        success: false,
        error: `Local faucet request failed: ${error.message}`,
        details: error.response?.data || error.message
      };
    }
  }

  /**
   * Get balance from local node
   */
  async getBalance(address) {
    try {
      if (!this.isRunning) {
        return {
          success: false,
          error: 'Node is not running',
          balance: '0'
        };
      }
      
      const response = await axios.get(`http://127.0.0.1:${this.apiPort}/api/v1/balance/${address}`, {
        timeout: 5000
      });
      
      return {
        success: true,
        balance: response.data.balance || '0',
        address: address,
        network: 'local-node'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        balance: '0'
      };
    }
  }
}

module.exports = new BlockchainNodeService();