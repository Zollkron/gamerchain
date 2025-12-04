const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Wallet operations
  generateWallet: () => ipcRenderer.invoke('generate-wallet'),
  importWallet: (mnemonic) => ipcRenderer.invoke('import-wallet', mnemonic),
  exportWallet: (walletId) => ipcRenderer.invoke('export-wallet', walletId),
  getWallets: () => ipcRenderer.invoke('get-wallets'),
  
  // File dialogs
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  
  // Platform info
  platform: process.platform
});