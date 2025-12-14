const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;

// Portable mode detection and configuration
const isPortableMode = process.env.PLAYERGOLD_PORTABLE === 'true' || process.argv.includes('--portable');
const isPioneerMode = process.env.PLAYERGOLD_BOOTSTRAP_MODE === 'auto' || process.argv.includes('--pioneer-mode');
const portableDataDir = process.env.PLAYERGOLD_DATA_DIR || path.join(process.cwd(), 'data');

// Configure data directory for portable mode
if (isPortableMode) {
  console.log('🎁 Running in portable mode');
  console.log(`📁 Data directory: ${portableDataDir}`);
  
  // Ensure data directory exists
  if (!fs.existsSync(portableDataDir)) {
    fs.mkdirSync(portableDataDir, { recursive: true });
  }
  
  // Set app data path for portable mode
  app.setPath('userData', path.join(portableDataDir, 'app-data'));
  app.setPath('logs', path.join(portableDataDir, 'logs'));
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    titleBarStyle: 'default',
    show: false
  });

  // Load the app
  let startUrl;
  if (isDev) {
    startUrl = 'http://localhost:3000';
  } else {
    // In production, load from build directory
    const indexPath = path.join(__dirname, '../build/index.html');
    startUrl = `file://${indexPath}`;
  }
  
  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Set up blockchain sync events after window is ready
    setupBlockchainSyncEvents();
    
    // Initialize pioneer mode if this is a new portable installation
    if (isPortableMode && isPioneerMode) {
      initializePioneerModeForPortable();
    }
  });

  // Open DevTools in development only
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
  });
});

// Blockchain sync service handlers
ipcMain.handle('initialize-blockchain-services', async () => {
  try {
    const BlockchainSyncService = require('./services/BlockchainSyncService');
    return await BlockchainSyncService.initialize();
  } catch (error) {
    console.error('Error initializing blockchain services:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('stop-blockchain-services', async () => {
  try {
    const BlockchainSyncService = require('./services/BlockchainSyncService');
    return await BlockchainSyncService.stop();
  } catch (error) {
    console.error('Error stopping blockchain services:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-sync-status', async () => {
  try {
    const BlockchainSyncService = require('./services/BlockchainSyncService');
    return BlockchainSyncService.getSyncStatus();
  } catch (error) {
    console.error('Error getting sync status:', error);
    return {
      isConnected: false,
      isSyncing: false,
      currentBlock: 0,
      targetBlock: 0,
      syncProgress: 0,
      peers: 0
    };
  }
});

// Set up blockchain sync event forwarding
const setupBlockchainSyncEvents = () => {
  try {
    const BlockchainSyncService = require('./services/BlockchainSyncService');
    
    BlockchainSyncService.on('status', (status) => {
      if (mainWindow) {
        mainWindow.webContents.send('sync-status', status);
      }
    });
    
    BlockchainSyncService.on('syncStatusUpdate', (status) => {
      if (mainWindow) {
        mainWindow.webContents.send('sync-status-update', status);
      }
    });
    
    BlockchainSyncService.on('ready', () => {
      if (mainWindow) {
        mainWindow.webContents.send('sync-ready');
      }
    });
    
    BlockchainSyncService.on('error', (error) => {
      if (mainWindow) {
        mainWindow.webContents.send('sync-error', error);
      }
    });
    
  } catch (error) {
    console.error('Error setting up blockchain sync events:', error);
  }
};

/**
 * Initialize pioneer mode for portable installations
 */
function initializePioneerModeForPortable() {
  try {
    console.log('🚀 Initializing pioneer mode for portable installation');
    
    const bootstrapStatePath = path.join(portableDataDir, 'bootstrap-state.json');
    
    // Check if bootstrap state exists
    if (!fs.existsSync(bootstrapStatePath)) {
      // Create initial bootstrap state
      const initialState = {
        mode: 'pioneer',
        initialized: true,
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        portable: true,
        dataDir: portableDataDir
      };
      
      fs.writeFileSync(bootstrapStatePath, JSON.stringify(initialState, null, 2));
      console.log('✅ Pioneer mode initialized for new installation');
      
      // Notify renderer about pioneer mode
      if (mainWindow) {
        mainWindow.webContents.send('pioneer-mode-initialized', initialState);
      }
    } else {
      // Load existing bootstrap state
      const existingState = JSON.parse(fs.readFileSync(bootstrapStatePath, 'utf8'));
      console.log(`📋 Loaded existing bootstrap state: ${existingState.mode}`);
      
      if (mainWindow) {
        mainWindow.webContents.send('bootstrap-state-loaded', existingState);
      }
    }
  } catch (error) {
    console.error('❌ Error initializing pioneer mode:', error);
  }
}

// Portable mode and environment detection handlers
ipcMain.handle('get-portable-mode-info', async () => {
  return {
    isPortableMode,
    isPioneerMode,
    dataDir: portableDataDir,
    appVersion: app.getVersion(),
    platform: process.platform,
    arch: process.arch
  };
});

ipcMain.handle('check-system-requirements-portable', async () => {
  try {
    const { execSync } = require('child_process');
    
    // Check Python
    let pythonVersion = null;
    try {
      const pythonOutput = execSync('python --version', { encoding: 'utf8' });
      pythonVersion = pythonOutput.trim();
    } catch (error) {
      try {
        const python3Output = execSync('python3 --version', { encoding: 'utf8' });
        pythonVersion = python3Output.trim();
      } catch (error2) {
        // Python not found
      }
    }
    
    // Check Node.js
    let nodeVersion = null;
    try {
      const nodeOutput = execSync('node --version', { encoding: 'utf8' });
      nodeVersion = nodeOutput.trim();
    } catch (error) {
      // Node.js not found
    }
    
    // Check available memory
    const totalMemory = require('os').totalmem();
    const freeMemory = require('os').freemem();
    
    return {
      success: true,
      requirements: {
        python: {
          available: pythonVersion !== null,
          version: pythonVersion,
          required: 'Python 3.8+'
        },
        nodejs: {
          available: nodeVersion !== null,
          version: nodeVersion,
          required: 'Node.js 16+'
        },
        memory: {
          total: Math.round(totalMemory / (1024 * 1024 * 1024)),
          free: Math.round(freeMemory / (1024 * 1024 * 1024)),
          required: 4
        },
        storage: {
          dataDir: portableDataDir,
          exists: fs.existsSync(portableDataDir),
          writable: true // We'll assume writable if we got this far
        }
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('initialize-portable-environment', async () => {
  try {
    console.log('🔧 Initializing portable environment...');
    
    // Create necessary directories
    const directories = [
      path.join(portableDataDir, 'wallets'),
      path.join(portableDataDir, 'blockchain'),
      path.join(portableDataDir, 'logs'),
      path.join(portableDataDir, 'models'),
      path.join(portableDataDir, 'temp')
    ];
    
    for (const dir of directories) {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`📁 Created directory: ${dir}`);
      }
    }
    
    // Initialize bootstrap service if not already done
    if (isPioneerMode) {
      initializePioneerModeForPortable();
    }
    
    return {
      success: true,
      message: 'Portable environment initialized successfully',
      dataDir: portableDataDir,
      directories: directories.map(dir => ({
        path: dir,
        exists: fs.existsSync(dir)
      }))
    };
  } catch (error) {
    console.error('❌ Error initializing portable environment:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-bootstrap-state', async () => {
  try {
    const bootstrapStatePath = path.join(portableDataDir, 'bootstrap-state.json');
    
    if (fs.existsSync(bootstrapStatePath)) {
      const state = JSON.parse(fs.readFileSync(bootstrapStatePath, 'utf8'));
      return {
        success: true,
        state
      };
    } else {
      return {
        success: true,
        state: null
      };
    }
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('update-bootstrap-state', async (event, newState) => {
  try {
    const bootstrapStatePath = path.join(portableDataDir, 'bootstrap-state.json');
    
    // Merge with existing state if it exists
    let currentState = {};
    if (fs.existsSync(bootstrapStatePath)) {
      currentState = JSON.parse(fs.readFileSync(bootstrapStatePath, 'utf8'));
    }
    
    const updatedState = {
      ...currentState,
      ...newState,
      lastUpdated: new Date().toISOString()
    };
    
    fs.writeFileSync(bootstrapStatePath, JSON.stringify(updatedState, null, 2));
    
    return {
      success: true,
      state: updatedState
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

// IPC handlers for wallet operations
ipcMain.handle('generate-wallet', async () => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.generateWallet();
  } catch (error) {
    console.error('Error in generate-wallet:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('import-wallet', async (event, mnemonic) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.importWallet(mnemonic);
  } catch (error) {
    console.error('Error in import-wallet:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('export-wallet', async (event, walletId) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.exportWallet(walletId);
  } catch (error) {
    console.error('Error in export-wallet:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-wallets', async () => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.getWallets();
  } catch (error) {
    console.error('Error in get-wallets:', error);
    return {
      success: false,
      error: error.message,
      wallets: []
    };
  }
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

// Network and faucet handlers
ipcMain.handle('get-network-info', async () => {
  try {
    const WalletService = require('./services/WalletService');
    return WalletService.getNetworkInfo();
  } catch (error) {
    console.error('Error getting network info:', error);
    return {
      network: 'testnet',
      networkId: 'playergold-testnet-genesis',
      apiUrl: 'http://localhost:18080'
    };
  }
});

ipcMain.handle('switch-network', async (event, network) => {
  try {
    const WalletService = require('./services/WalletService');
    return WalletService.switchNetwork(network);
  } catch (error) {
    console.error('Error switching network:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('request-faucet-tokens', async (event, walletId, amount) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.requestFaucetTokens(walletId, amount);
  } catch (error) {
    console.error('Error requesting faucet tokens:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-wallet-balance', async (event, walletId) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.getWalletBalance(walletId);
  } catch (error) {
    console.error('Error getting wallet balance:', error);
    return {
      success: false,
      error: error.message,
      balance: '0'
    };
  }
});

ipcMain.handle('sync-wallet', async (event, walletId) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.syncWallet(walletId);
  } catch (error) {
    console.error('Error syncing wallet:', error);
    return {
      success: false,
      error: error.message
    };
  }
});
// Transaction handlers
ipcMain.handle('send-transaction', async (event, walletId, transactionData) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.sendTransaction(walletId, transactionData);
  } catch (error) {
    console.error('Error sending transaction:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-transaction-history', async (event, walletId, limit, offset) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.getTransactionHistory(walletId, limit || 50, offset || 0);
  } catch (error) {
    console.error('Error getting transaction history:', error);
    return {
      success: false,
      error: error.message,
      transactions: []
    };
  }
});

ipcMain.handle('get-pending-transactions', async (event, walletId) => {
  try {
    const WalletService = require('./services/WalletService');
    return WalletService.getPendingTransactions(walletId);
  } catch (error) {
    console.error('Error getting pending transactions:', error);
    return [];
  }
});

// Network status handler
ipcMain.handle('get-network-status', async () => {
  try {
    const NetworkService = require('./services/NetworkService');
    return await NetworkService.getNetworkStatus();
  } catch (error) {
    console.error('Error getting network status:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

// Wallet management handlers
ipcMain.handle('update-wallet-name', async (event, walletId, newName) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.updateWalletName(walletId, newName);
  } catch (error) {
    console.error('Error updating wallet name:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('delete-wallet', async (event, walletId) => {
  try {
    const WalletService = require('./services/WalletService');
    return await WalletService.deleteWallet(walletId);
  } catch (error) {
    console.error('Error deleting wallet:', error);
    return {
      success: false,
      error: error.message
    };
  }
});
// AI Model and Mining handlers
ipcMain.handle('get-certified-models', async () => {
  try {
    const AIModelService = require('./services/AIModelService');
    return {
      success: true,
      models: AIModelService.getCertifiedModels()
    };
  } catch (error) {
    console.error('Error getting certified models:', error);
    return {
      success: false,
      error: error.message,
      models: []
    };
  }
});

ipcMain.handle('get-installed-models', async () => {
  try {
    const AIModelService = require('./services/AIModelService');
    return {
      success: true,
      models: AIModelService.getInstalledModels()
    };
  } catch (error) {
    console.error('Error getting installed models:', error);
    return {
      success: false,
      error: error.message,
      models: []
    };
  }
});

ipcMain.handle('download-model', async (event, modelId) => {
  try {
    const AIModelService = require('./services/AIModelService');
    
    const result = await AIModelService.downloadModel(modelId, (progress) => {
      // Send progress updates to renderer
      event.sender.send('model-download-progress', {
        modelId,
        ...progress
      });
    });
    
    return result;
  } catch (error) {
    console.error('Error downloading model:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('uninstall-model', async (event, modelId) => {
  try {
    const AIModelService = require('./services/AIModelService');
    return await AIModelService.uninstallModel(modelId);
  } catch (error) {
    console.error('Error uninstalling model:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('check-system-requirements', async (event, modelId) => {
  try {
    const AIModelService = require('./services/AIModelService');
    return {
      success: true,
      requirements: AIModelService.checkSystemRequirements(modelId)
    };
  } catch (error) {
    console.error('Error checking system requirements:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

// Mining handlers
ipcMain.handle('get-mining-status', async () => {
  try {
    const MiningService = require('./services/MiningService');
    return {
      success: true,
      status: MiningService.getMiningStatus()
    };
  } catch (error) {
    console.error('Error getting mining status:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('check-mining-requirements', async () => {
  try {
    const MiningService = require('./services/MiningService');
    return {
      success: true,
      requirements: await MiningService.checkMiningRequirements()
    };
  } catch (error) {
    console.error('Error checking mining requirements:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('start-mining', async (event, modelId, walletAddress) => {
  try {
    const MiningService = require('./services/MiningService');
    
    // Set up status change listener
    const unsubscribe = MiningService.onStatusChange((status) => {
      event.sender.send('mining-status-change', status);
    });
    
    // Store unsubscribe function for cleanup
    event.sender.once('destroyed', unsubscribe);
    
    return await MiningService.startMining(modelId, walletAddress);
  } catch (error) {
    console.error('Error starting mining:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('stop-mining', async () => {
  try {
    const MiningService = require('./services/MiningService');
    return await MiningService.stopMining();
  } catch (error) {
    console.error('Error stopping mining:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-mining-stats', async () => {
  try {
    const MiningService = require('./services/MiningService');
    return {
      success: true,
      stats: MiningService.getMiningStats()
    };
  } catch (error) {
    console.error('Error getting mining stats:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('estimate-mining-rewards', async () => {
  try {
    const MiningService = require('./services/MiningService');
    return {
      success: true,
      rewards: MiningService.estimateMiningRewards()
    };
  } catch (error) {
    console.error('Error estimating mining rewards:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

// Blockchain Node Service handlers
ipcMain.handle('get-blockchain-node-status', async () => {
  try {
    const BlockchainNodeService = require('./services/BlockchainNodeService');
    return {
      success: true,
      status: BlockchainNodeService.getNodeStatus()
    };
  } catch (error) {
    console.error('Error getting blockchain node status:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('check-blockchain-node-requirements', async () => {
  try {
    const BlockchainNodeService = require('./services/BlockchainNodeService');
    return {
      success: true,
      requirements: await BlockchainNodeService.checkSystemRequirements()
    };
  } catch (error) {
    console.error('Error checking blockchain node requirements:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('start-blockchain-node', async (event) => {
  try {
    const BlockchainNodeService = require('./services/BlockchainNodeService');
    
    // Set up status change listener
    const unsubscribe = BlockchainNodeService.onStatusChange((status) => {
      event.sender.send('blockchain-node-status-change', status);
    });
    
    // Store unsubscribe function for cleanup
    event.sender.once('destroyed', unsubscribe);
    
    return await BlockchainNodeService.startNode();
  } catch (error) {
    console.error('Error starting blockchain node:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('stop-blockchain-node', async () => {
  try {
    const BlockchainNodeService = require('./services/BlockchainNodeService');
    return await BlockchainNodeService.stopNode();
  } catch (error) {
    console.error('Error stopping blockchain node:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

ipcMain.handle('get-blockchain-network-status', async () => {
  try {
    const BlockchainNodeService = require('./services/BlockchainNodeService');
    return await BlockchainNodeService.getNetworkStatus();
  } catch (error) {
    console.error('Error getting blockchain network status:', error);
    return {
      success: false,
      error: error.message
    };
  }
});