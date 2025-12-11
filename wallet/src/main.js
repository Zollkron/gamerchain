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
    // In production, find the index.html in the app directory
    const execPath = process.execPath;
    const appDir = path.dirname(execPath);
    const indexPath = path.join(appDir, 'index.html');
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