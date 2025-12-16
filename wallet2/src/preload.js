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
  getCertifiedModels: () => ipcRenderer.invoke('get-certified-models'),
  getInstalledModels: () => ipcRenderer.invoke('get-installed-models'),
  downloadModel: (modelId) => ipcRenderer.invoke('download-model', modelId),
  uninstallModel: (modelId) => ipcRenderer.invoke('uninstall-model', modelId),
  checkSystemRequirements: (modelId) => ipcRenderer.invoke('check-system-requirements', modelId),
  
  // Mining operations
  getMiningStatus: () => ipcRenderer.invoke('get-mining-status'),
  checkMiningRequirements: () => ipcRenderer.invoke('check-mining-requirements'),
  startMining: (modelId, walletAddress) => ipcRenderer.invoke('start-mining', modelId, walletAddress),
  stopMining: () => ipcRenderer.invoke('stop-mining'),
  getMiningStats: () => ipcRenderer.invoke('get-mining-stats'),
  estimateMiningRewards: () => ipcRenderer.invoke('estimate-mining-rewards'),
  
  // Network operations
  getNetworkInfo: () => ipcRenderer.invoke('get-network-info'),
  switchNetwork: (network) => ipcRenderer.invoke('switch-network', network),
  requestFaucetTokens: (walletId, amount) => ipcRenderer.invoke('request-faucet-tokens', walletId, amount),
  getWalletBalance: (walletId) => ipcRenderer.invoke('get-wallet-balance', walletId),
  syncWallet: (walletId) => ipcRenderer.invoke('sync-wallet', walletId),
  getNetworkStatus: () => ipcRenderer.invoke('get-network-status'),
  
  // Transaction operations
  sendTransaction: (walletId, transactionData) => ipcRenderer.invoke('send-transaction', walletId, transactionData),
  getTransactionHistory: (walletId, limit, offset) => ipcRenderer.invoke('get-transaction-history', walletId, limit, offset),
  getPendingTransactions: (walletId) => ipcRenderer.invoke('get-pending-transactions', walletId),
  
  // Wallet management
  updateWalletName: (walletId, newName) => ipcRenderer.invoke('update-wallet-name', walletId, newName),
  deleteWallet: (walletId) => ipcRenderer.invoke('delete-wallet', walletId),
  
  // Blockchain sync operations
  initializeBlockchainServices: () => ipcRenderer.invoke('initialize-blockchain-services'),
  stopBlockchainServices: () => ipcRenderer.invoke('stop-blockchain-services'),
  getSyncStatus: () => ipcRenderer.invoke('get-sync-status'),
  
  // Event listeners
  onMiningStatusChange: (callback) => {
    ipcRenderer.on('mining-status-change', callback);
    return () => ipcRenderer.removeListener('mining-status-change', callback);
  },
  
  onModelDownloadProgress: (callback) => {
    ipcRenderer.on('model-download-progress', callback);
    return () => ipcRenderer.removeListener('model-download-progress', callback);
  },
  
  // Blockchain sync event listeners
  onSyncStatus: (callback) => {
    ipcRenderer.on('sync-status', (event, status) => callback(status));
    return () => ipcRenderer.removeListener('sync-status', callback);
  },
  
  onSyncStatusUpdate: (callback) => {
    ipcRenderer.on('sync-status-update', (event, status) => callback(status));
    return () => ipcRenderer.removeListener('sync-status-update', callback);
  },
  
  onSyncReady: (callback) => {
    ipcRenderer.on('sync-ready', () => callback());
    return () => ipcRenderer.removeListener('sync-ready', callback);
  },
  
  onSyncError: (callback) => {
    ipcRenderer.on('sync-error', (event, error) => callback(error));
    return () => ipcRenderer.removeListener('sync-error', callback);
  },
  
  // ========================================
  // Network Validation Operations (MANDATORY)
  // ========================================
  
  // Network validation status
  getNetworkValidationStatus: () => ipcRenderer.invoke('get-network-validation-status'),
  getCanonicalNetworkMap: () => ipcRenderer.invoke('get-canonical-network-map'),
  getValidNodes: () => ipcRenderer.invoke('get-valid-nodes'),
  refreshNetworkValidation: () => ipcRenderer.invoke('refresh-network-validation'),
  forceNetworkRevalidation: () => ipcRenderer.invoke('force-network-revalidation'),
  canWalletOperate: () => ipcRenderer.invoke('can-wallet-operate'),
  
  // Blockchain Node Service operations
  getBlockchainNodeStatus: () => ipcRenderer.invoke('get-blockchain-node-status'),
  checkBlockchainNodeRequirements: () => ipcRenderer.invoke('check-blockchain-node-requirements'),
  startBlockchainNode: () => ipcRenderer.invoke('start-blockchain-node'),
  stopBlockchainNode: () => ipcRenderer.invoke('stop-blockchain-node'),
  getBlockchainNetworkStatus: () => ipcRenderer.invoke('get-blockchain-network-status'),
  
  // Blockchain node event listeners
  onBlockchainNodeStatusChange: (callback) => {
    const wrappedCallback = (event, status) => callback(status);
    ipcRenderer.on('blockchain-node-status-change', wrappedCallback);
    return () => ipcRenderer.removeListener('blockchain-node-status-change', wrappedCallback);
  },
  
  // Portable mode operations
  getPortableModeInfo: () => ipcRenderer.invoke('get-portable-mode-info'),
  checkSystemRequirementsPortable: () => ipcRenderer.invoke('check-system-requirements-portable'),
  initializePortableEnvironment: () => ipcRenderer.invoke('initialize-portable-environment'),
  getBootstrapState: () => ipcRenderer.invoke('get-bootstrap-state'),
  updateBootstrapState: (newState) => ipcRenderer.invoke('update-bootstrap-state', newState),
  
  // Pioneer mode event listeners
  onPioneerModeInitialized: (callback) => {
    const wrappedCallback = (event, state) => callback(state);
    ipcRenderer.on('pioneer-mode-initialized', wrappedCallback);
    return () => ipcRenderer.removeListener('pioneer-mode-initialized', wrappedCallback);
  },
  
  onBootstrapStateLoaded: (callback) => {
    const wrappedCallback = (event, state) => callback(state);
    ipcRenderer.on('bootstrap-state-loaded', wrappedCallback);
    return () => ipcRenderer.removeListener('bootstrap-state-loaded', wrappedCallback);
  },
  
  // Data management operations
  clearWalletData: () => ipcRenderer.invoke('clear-wallet-data'),
  isFirstRun: () => ipcRenderer.invoke('is-first-run'),
  
  // Generic invoke method for flexibility
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),
  
  // Generic event listener methods
  on: (channel, callback) => {
    const wrappedCallback = (event, ...args) => callback(...args);
    ipcRenderer.on(channel, wrappedCallback);
    return () => ipcRenderer.removeListener(channel, wrappedCallback);
  },
  
  removeListener: (channel, callback) => {
    ipcRenderer.removeListener(channel, callback);
  },
  
  // Event emitter for custom events
  emit: (eventName, data) => {
    // This is a placeholder for custom event emission
    console.log(`Event emitted: ${eventName}`, data);
  }
});