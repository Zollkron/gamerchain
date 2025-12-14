import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from '../Dashboard';

// Mock the BlockchainNodeStatus component
jest.mock('../BlockchainNodeStatus', () => {
  return function MockBlockchainNodeStatus() {
    return <div data-testid="blockchain-node-status">Blockchain Node Status</div>;
  };
});

// Mock bootstrap service
class MockBootstrapService {
  constructor() {
    this.listeners = {};
    this.state = {
      mode: 'pioneer',
      walletAddress: null,
      selectedModel: null,
      discoveredPeers: [],
      genesisBlock: null,
      networkConfig: null,
      lastError: null,
      isReady: false
    };
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  removeListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  getState() {
    return { ...this.state };
  }

  setState(updates) {
    this.state = { ...this.state, ...updates };
    this.emit('stateChanged', this.state);
  }

  async onWalletAddressCreated(address) {
    this.state.walletAddress = address;
  }

  async onMiningReadiness(modelPath, modelInfo) {
    this.state.selectedModel = modelPath;
    this.state.modelInfo = modelInfo;
    this.state.isReady = true;
  }

  async startPeerDiscovery() {
    this.setState({ mode: 'discovery' });
  }
}

// Mock window.alert
global.alert = jest.fn();

// Mock window.electronAPI
const mockElectronAPI = {
  getBootstrapService: jest.fn(),
  getWalletBalance: jest.fn(),
  getTransactionHistory: jest.fn(),
  getNetworkStatus: jest.fn(),
  getMiningStatus: jest.fn(),
  getCertifiedModels: jest.fn(),
  estimateMiningRewards: jest.fn(),
  startMining: jest.fn(),
  stopMining: jest.fn(),
  downloadModel: jest.fn(),
  sendTransaction: jest.fn(),
  requestFaucetTokens: jest.fn(),
  onMiningStatusChange: jest.fn(),
  onModelDownloadProgress: jest.fn()
};

// Mock wallet data
const mockWallet = {
  id: 'wallet-1',
  name: 'Test Wallet',
  address: 'PG1abc123def456ghi789',
  createdAt: new Date().toISOString()
};

const mockWallets = [mockWallet];

describe('Dashboard Bootstrap Integration', () => {
  let mockBootstrapService;

  beforeEach(() => {
    mockBootstrapService = new MockBootstrapService();
    
    // Setup window.electronAPI mock
    Object.defineProperty(window, 'electronAPI', {
      value: mockElectronAPI,
      writable: true
    });

    // Setup default mock responses
    mockElectronAPI.getBootstrapService.mockResolvedValue(mockBootstrapService);
    mockElectronAPI.getWalletBalance.mockResolvedValue({ success: true, balance: '100.50' });
    mockElectronAPI.getTransactionHistory.mockResolvedValue({ success: true, transactions: [] });
    mockElectronAPI.getNetworkStatus.mockResolvedValue({ success: true, status: { syncStatus: 'synced' } });
    mockElectronAPI.getMiningStatus.mockResolvedValue({ 
      success: true, 
      status: { 
        isMining: false, 
        currentModel: null, 
        stats: {
          blocksValidated: 0,
          rewardsEarned: 0,
          challengesProcessed: 0,
          successRate: 100,
          uptime: 0,
          reputation: 100
        }
      }
    });
    mockElectronAPI.getCertifiedModels.mockResolvedValue({ 
      success: true, 
      models: [
        {
          id: 'gemma-3-4b',
          name: 'Gemma 3 4B',
          description: 'Test model',
          size: '4GB',
          requirements: { vram: '4GB' },
          isInstalled: true
        }
      ]
    });
    mockElectronAPI.estimateMiningRewards.mockResolvedValue({ 
      success: true, 
      rewards: { hourly: 10, daily: 240, weekly: 1680, monthly: 7200 }
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Bootstrap Status Display in Header', () => {
    test('shows bootstrap status in header when not in network mode', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Bootstrap:/)).toBeInTheDocument();
        expect(screen.getAllByText(/Modo Pionero/)[0]).toBeInTheDocument();
        expect(screen.getByText(/Estableciendo/)).toBeInTheDocument();
      });
    });

    test('shows network status when in network mode', async () => {
      mockBootstrapService.setState({ mode: 'network' });

      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.queryByText(/Bootstrap:/)).not.toBeInTheDocument();
        expect(screen.getByText(/Conectado/)).toBeInTheDocument();
        expect(screen.getByText(/100%/)).toBeInTheDocument();
      });
    });

    test('updates header status when bootstrap state changes', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getAllByText(/Modo Pionero/)[0]).toBeInTheDocument();
      });

      // Change to discovery mode
      mockBootstrapService.setState({ mode: 'discovery' });

      await waitFor(() => {
        expect(screen.getByText(/Descubriendo Peers/)).toBeInTheDocument();
      });
    });
  });

  describe('Bootstrap Status Card in Overview', () => {
    test('displays bootstrap status card in overview tab', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('🚀 Estado del Bootstrap P2P')).toBeInTheDocument();
        expect(screen.getByText('🏴‍☠️')).toBeInTheDocument(); // Pioneer mode icon
        expect(screen.getByText('Modo Pionero')).toBeInTheDocument();
      });
    });

    test('shows pioneer mode instructions correctly', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Próximos pasos:')).toBeInTheDocument();
        expect(screen.getByText(/✅ Cartera creada:/)).toBeInTheDocument();
        expect(screen.getByText(/PG1abc123def456ghi789/)).toBeInTheDocument();
        expect(screen.getByText(/Ve a "Minería" y selecciona un modelo IA/)).toBeInTheDocument();
      });
    });

    test('shows discovery mode status correctly', async () => {
      mockBootstrapService.setState({ 
        mode: 'discovery',
        discoveredPeers: [
          { id: 'peer1', address: '192.168.1.100', port: 8080 },
          { id: 'peer2', address: '192.168.1.101', port: 8080 }
        ]
      });

      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('🔍')).toBeInTheDocument(); // Discovery mode icon
        expect(screen.getByText('Descubrimiento P2P')).toBeInTheDocument();
        expect(screen.getByText((content, element) => {
          return element && element.textContent === 'Peers encontrados: 2';
        })).toBeInTheDocument();
      });
    });

    test('shows genesis mode status correctly', async () => {
      mockBootstrapService.setState({ 
        mode: 'genesis',
        discoveredPeers: [
          { id: 'peer1', address: '192.168.1.100', port: 8080 },
          { id: 'peer2', address: '192.168.1.101', port: 8080 },
          { id: 'peer3', address: '192.168.1.102', port: 8080 }
        ]
      });

      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('⚡')).toBeInTheDocument(); // Genesis mode icon
        expect(screen.getByText('Creación del Génesis')).toBeInTheDocument();
        expect(screen.getByText((content, element) => {
          return element && element.textContent === 'Participantes: 3';
        })).toBeInTheDocument();
      });
    });

    test('hides bootstrap status card in network mode', async () => {
      mockBootstrapService.setState({ mode: 'network' });

      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.queryByText('🚀 Estado del Bootstrap P2P')).not.toBeInTheDocument();
      });
    });
  });

  describe('Bootstrap-Aware Mining Controls', () => {
    // Remove the beforeEach that was causing issues

    test('shows bootstrap P2P button in pioneer mode', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      // Switch to mining tab
      const miningTab = await screen.findByText('Minería');
      fireEvent.click(miningTab);

      await waitFor(() => {
        expect(screen.getByText('🚀 Iniciar Bootstrap P2P')).toBeInTheDocument();
        expect(screen.getByText('🚀 Modo Bootstrap P2P')).toBeInTheDocument();
      });
    });

    test('shows bootstrap mining info in pioneer mode', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      // Switch to mining tab
      const miningTab = await screen.findByText('Minería');
      fireEvent.click(miningTab);

      await waitFor(() => {
        expect(screen.getByText('🚀 Modo Bootstrap P2P')).toBeInTheDocument();
        expect(screen.getByText(/Selecciona un modelo e inicia la minería/)).toBeInTheDocument();
      });
    });

    test('shows mining notice during bootstrap phases', async () => {
      mockBootstrapService.setState({ mode: 'discovery' });

      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      // Switch to mining tab
      const miningTab = await screen.findByText('Minería');
      fireEvent.click(miningTab);

      await waitFor(() => {
        expect(screen.getByText(/Minería disponible después de establecer la red/)).toBeInTheDocument();
      });
    });

    test('handles bootstrap mining start correctly', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      // Switch to mining tab and select a model
      const miningTab = await screen.findByText('Minería');
      fireEvent.click(miningTab);
      
      await waitFor(() => {
        const selectButton = screen.getByText('Seleccionar');
        fireEvent.click(selectButton);
      });

      // Click start bootstrap button
      await waitFor(() => {
        const startButton = screen.getByText('🚀 Iniciar Bootstrap P2P');
        fireEvent.click(startButton);
      });

      // Verify bootstrap service methods were called
      expect(mockBootstrapService.state.walletAddress).toBe(mockWallet.address);
      expect(mockBootstrapService.state.selectedModel).toBe('gemma-3-4b');
      expect(mockBootstrapService.state.mode).toBe('discovery');
    });
  });

  describe('Feature Restrictions During Bootstrap', () => {
    test('disables faucet button during bootstrap', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        const faucetButton = screen.getByText('🚰 Solicitar Tokens Testnet');
        expect(faucetButton).toBeDisabled();
        expect(faucetButton).toHaveAttribute('title', 'Disponible después del bootstrap');
      });
    });

    test('enables faucet button in network mode', async () => {
      mockBootstrapService.setState({ mode: 'network' });

      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        const faucetButton = screen.getByText('🚰 Solicitar Tokens Testnet');
        expect(faucetButton).not.toBeDisabled();
      });
    });

    test('shows normal mining button in network mode', async () => {
      mockBootstrapService.setState({ mode: 'network' });

      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      // Switch to mining tab
      const miningTab = await screen.findByText('Minería');
      fireEvent.click(miningTab);

      await waitFor(() => {
        expect(screen.getByText('🚀 Iniciar Minería')).toBeInTheDocument();
        expect(screen.queryByText('🚀 Iniciar Bootstrap P2P')).not.toBeInTheDocument();
      });
    });
  });

  describe('Bootstrap Service Integration', () => {
    test('initializes bootstrap service on mount', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(mockElectronAPI.getBootstrapService).toHaveBeenCalled();
      });
    });

    test('handles bootstrap service initialization failure gracefully', async () => {
      mockElectronAPI.getBootstrapService.mockRejectedValue(new Error('Service unavailable'));

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Error initializing bootstrap service:', expect.any(Error));
      });

      consoleSpy.mockRestore();
    });

    test('updates UI when bootstrap state changes', async () => {
      render(
        <Dashboard 
          wallet={mockWallet}
          wallets={mockWallets}
          onWalletChange={jest.fn()}
          onWalletsUpdate={jest.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Modo Pionero')).toBeInTheDocument();
      });

      // Simulate state change
      mockBootstrapService.setState({ mode: 'discovery' });

      await waitFor(() => {
        expect(screen.getByText('Descubrimiento P2P')).toBeInTheDocument();
      });
    });
  });
});