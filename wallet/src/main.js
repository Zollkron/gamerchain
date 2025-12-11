const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;

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