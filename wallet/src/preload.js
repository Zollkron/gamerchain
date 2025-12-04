const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Wallet operations
  generateWallet: () => ipcRenderer.invoke('generate-wallet'),
  importWallet: (mnemonic) => ipcRenderer.invoke('import-wallet', mnemonic),
  exportWallet: (walletId) => ipcRenderer.invoke('export-wallet', walletId),
  getWallets: () => ipcRenderer.invoke('get-wallets'),
  
  // File operations
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  
  // AI Model operations
  downloadModel: (modelId, onProgress) => ipcRenderer.invoke('download-model', modelId, onProgress),
  verifyModelHash: (modelId, filePath) => ipcRenderer.invoke('verify-model-hash', modelId, filePath),
  getInstalledModels: () => ipcRenderer.invoke('get-installed-models'),
  uninstallModel: (modelId) => ipcRenderer.invoke('uninstall-model', modelId),
  
  // Mining operations
  startMining: (modelId, walletAddress) => ipcRenderer.invoke('start-mining', modelId, walletAddress),
  stopMining: () => ipcRenderer.invoke('stop-mining'),
  getMiningStatus: () => ipcRenderer.invoke('get-mining-status'),
  
  // System information
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  checkSystemRequirements: () => ipcRenderer.invoke('check-system-requirements'),
  
  // Event listeners
  onMiningStatusChange: (callback) => {
    ipcRenderer.on('mining-status-change', callback);
    return () => ipcRenderer.removeListener('mining-status-change', callback);
  },
  
  onModelDownloadProgress: (callback) => {
    ipcRenderer.on('model-download-progress', callback);
    return () => ipcRenderer.removeListener('model-download-progress', callback);
  }
});