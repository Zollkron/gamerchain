import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BootstrapStatus from '../BootstrapStatus';

// Mock EventEmitter for bootstrap service
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
}

describe('BootstrapStatus Component', () => {
  let mockBootstrapService;
  let mockOnBootstrapComplete;

  beforeEach(() => {
    mockBootstrapService = new MockBootstrapService();
    mockOnBootstrapComplete = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Bootstrap Status Display', () => {
    test('displays pioneer mode status correctly', () => {
      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(screen.getByText('🚀 Auto-Bootstrap P2P Network')).toBeInTheDocument();
      expect(screen.getByText('Modo Pionero')).toBeInTheDocument();
      expect(screen.getByText(/Esperando que crees tu cartera/)).toBeInTheDocument();
    });

    test('displays discovery mode status correctly', () => {
      mockBootstrapService.setState({ mode: 'discovery' });

      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(screen.getByText('Descubrimiento P2P')).toBeInTheDocument();
      expect(screen.getAllByText(/Buscando otros usuarios pioneros/)[0]).toBeInTheDocument();
      expect(screen.getByText('🔍 Descubrimiento de Peers')).toBeInTheDocument();
    });

    test('displays genesis mode status correctly', () => {
      mockBootstrapService.setState({ mode: 'genesis' });

      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(screen.getByText('Creación del Génesis')).toBeInTheDocument();
      expect(screen.getByText(/Coordinando con otros peers/)).toBeInTheDocument();
      expect(screen.getByText('⚡ Creación del Bloque Génesis')).toBeInTheDocument();
    });

    test('hides component when in network mode', () => {
      mockBootstrapService.setState({ mode: 'network' });

      const { container } = render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Progress Indicators', () => {
    test('shows peer discovery progress correctly', async () => {
      mockBootstrapService.setState({ mode: 'discovery' });

      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      // Simulate peer discovery status update
      const peerDiscoveryStatus = {
        phase: 'discovering',
        peers: [
          { id: 'peer1', address: '192.168.1.100', port: 8080, isReady: true },
          { id: 'peer2', address: '192.168.1.101', port: 8080, isReady: false }
        ],
        elapsed: 5000,
        message: 'Peer encontrado: 192.168.1.100:8080'
      };

      mockBootstrapService.emit('peerDiscoveryStatus', peerDiscoveryStatus);

      await waitFor(() => {
        expect(screen.getByText('Peers encontrados: 2')).toBeInTheDocument();
        expect(screen.getByText('Tiempo transcurrido: 5s')).toBeInTheDocument();
        expect(screen.getByText('192.168.1.100:8080')).toBeInTheDocument();
        expect(screen.getByText('✅ Listo')).toBeInTheDocument();
        expect(screen.getByText('⏳ Preparando')).toBeInTheDocument();
      });
    });

    test('shows genesis creation progress correctly', async () => {
      mockBootstrapService.setState({ mode: 'genesis' });

      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      // Simulate genesis progress update
      const genesisProgress = {
        phase: 'creating',
        percentage: 60,
        message: 'Creando bloque génesis...',
        participants: ['PG1abc...', 'PG2def...', 'PG3ghi...']
      };

      mockBootstrapService.emit('genesisProgress', genesisProgress);

      await waitFor(() => {
        expect(screen.getAllByText('Creando bloque génesis...')[0]).toBeInTheDocument();
        expect(screen.getByText('60%')).toBeInTheDocument();
        expect(screen.getByText('Participantes del Génesis:')).toBeInTheDocument();
        expect(screen.getByText('PG1abc...')).toBeInTheDocument();
      });
    });

    test('displays loading animation during active phases', () => {
      mockBootstrapService.setState({ mode: 'discovery' });

      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(screen.getByText('Procesando... Por favor mantén la aplicación abierta')).toBeInTheDocument();
      expect(document.querySelector('.spinner')).toBeInTheDocument();
    });
  });

  describe('User Instructions', () => {
    test('displays correct instructions for pioneer mode', () => {
      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(screen.getByText(/1\. Crea tu dirección de cartera/)).toBeInTheDocument();
      expect(screen.getByText(/2\. Ve a la pestaña "Minería"/)).toBeInTheDocument();
      expect(screen.getByText(/3\. Haz clic en "Iniciar Minería"/)).toBeInTheDocument();
    });

    test('displays correct instructions for discovery mode', () => {
      mockBootstrapService.setState({ mode: 'discovery' });

      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(screen.getByText(/1\. Buscando otros usuarios pioneros/)).toBeInTheDocument();
      expect(screen.getByText(/2\. Asegúrate de que otros dispositivos/)).toBeInTheDocument();
      expect(screen.getByText(/3\. El proceso puede tomar unos minutos/)).toBeInTheDocument();
    });

    test('displays correct instructions for genesis mode', () => {
      mockBootstrapService.setState({ mode: 'genesis' });

      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(screen.getByText(/1\. Coordinando con peers encontrados/)).toBeInTheDocument();
      expect(screen.getByText(/2\. Negociando parámetros de la red/)).toBeInTheDocument();
      expect(screen.getByText(/3\. Este proceso es automático/)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('displays error information correctly', async () => {
      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      const error = {
        type: 'network_timeout',
        message: 'Network timeout during peer discovery',
        timestamp: new Date().toISOString(),
        canRetry: true
      };

      mockBootstrapService.setState({ lastError: error });

      await waitFor(() => {
        expect(screen.getByText('⚠️ Error')).toBeInTheDocument();
        expect(screen.getByText('network_timeout')).toBeInTheDocument();
        expect(screen.getByText('Network timeout during peer discovery')).toBeInTheDocument();
        expect(screen.getByText(/El sistema reintentará automáticamente/)).toBeInTheDocument();
      });
    });

    test('shows error messages in status messages', async () => {
      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      mockBootstrapService.emit('error', { message: 'Connection failed' });

      await waitFor(() => {
        expect(screen.getByText('Connection failed')).toBeInTheDocument();
        expect(screen.getByText('❌')).toBeInTheDocument();
      });
    });
  });

  describe('Bootstrap Completion', () => {
    test('calls onBootstrapComplete when transitioning to network mode', async () => {
      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      mockBootstrapService.setState({ mode: 'network' });

      await waitFor(() => {
        expect(mockOnBootstrapComplete).toHaveBeenCalledTimes(1);
      });
    });

    test('hides component after bootstrap completion', async () => {
      const { rerender } = render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(screen.getByText('Modo Pionero')).toBeInTheDocument();

      mockBootstrapService.setState({ mode: 'network' });

      rerender(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      await waitFor(() => {
        expect(screen.queryByText('Modo Pionero')).not.toBeInTheDocument();
      });
    });
  });

  describe('Status Messages', () => {
    test('displays and manages status messages correctly', async () => {
      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      // Add different types of messages
      mockBootstrapService.emit('success', 'Operation successful');
      mockBootstrapService.emit('error', { message: 'Operation failed' });

      await waitFor(() => {
        expect(screen.getByText('Operation successful')).toBeInTheDocument();
        expect(screen.getByText('Operation failed')).toBeInTheDocument();
        expect(screen.getByText('✅')).toBeInTheDocument();
        expect(screen.getByText('❌')).toBeInTheDocument();
      });
    });

    test('limits status messages to last 10 entries', async () => {
      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      // Add 12 messages
      for (let i = 1; i <= 12; i++) {
        mockBootstrapService.emit('success', `Message ${i}`);
      }

      await waitFor(() => {
        expect(screen.queryByText('Message 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Message 2')).not.toBeInTheDocument();
        expect(screen.getByText('Message 3')).toBeInTheDocument();
        expect(screen.getByText('Message 12')).toBeInTheDocument();
      });
    });
  });

  describe('Component Lifecycle', () => {
    test('sets up event listeners on mount', () => {
      const onSpy = jest.spyOn(mockBootstrapService, 'on');
      
      render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(onSpy).toHaveBeenCalledWith('stateChanged', expect.any(Function));
      expect(onSpy).toHaveBeenCalledWith('peerDiscoveryStatus', expect.any(Function));
      expect(onSpy).toHaveBeenCalledWith('genesisProgress', expect.any(Function));
      expect(onSpy).toHaveBeenCalledWith('error', expect.any(Function));
      expect(onSpy).toHaveBeenCalledWith('success', expect.any(Function));
    });

    test('cleans up event listeners on unmount', () => {
      const removeListenerSpy = jest.spyOn(mockBootstrapService, 'removeListener');
      
      const { unmount } = render(
        <BootstrapStatus 
          bootstrapService={mockBootstrapService}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      unmount();

      expect(removeListenerSpy).toHaveBeenCalledWith('stateChanged', expect.any(Function));
      expect(removeListenerSpy).toHaveBeenCalledWith('peerDiscoveryStatus', expect.any(Function));
      expect(removeListenerSpy).toHaveBeenCalledWith('genesisProgress', expect.any(Function));
      expect(removeListenerSpy).toHaveBeenCalledWith('error', expect.any(Function));
      expect(removeListenerSpy).toHaveBeenCalledWith('success', expect.any(Function));
    });

    test('handles missing bootstrap service gracefully', () => {
      const { container } = render(
        <BootstrapStatus 
          bootstrapService={null}
          onBootstrapComplete={mockOnBootstrapComplete}
        />
      );

      expect(container.firstChild).toBeNull();
    });
  });
});