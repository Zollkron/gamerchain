import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import MiningTab from '../MiningTab';

// Mock the services
jest.mock('../../services/AIModelService', () => ({
  aiModelService: {
    getCertifiedModels: jest.fn(() => [
      {
        id: 'gemma-3-4b',
        name: 'Gemma 3 4B',
        sizeFormatted: '8.2 GB',
        requirements: { vram: 4, ram: 8, cores: 4 },
        description: 'Test model'
      }
    ]),
    checkSystemRequirements: jest.fn(() => Promise.resolve({
      compatible: true,
      vram: 8,
      ram: 16,
      cores: 8,
      gpu: 'Test GPU'
    })),
    getInstalledModels: jest.fn(() => Promise.resolve([])),
    downloadModel: jest.fn(() => Promise.resolve({
      success: true,
      path: '/test/path',
      hash: 'test-hash'
    })),
    verifyModelHash: jest.fn(() => Promise.resolve({ valid: true })),
    markModelInstalled: jest.fn(() => Promise.resolve()),
    uninstallModel: jest.fn(() => Promise.resolve())
  }
}));

jest.mock('../../services/MiningService', () => ({
  addStatusListener: jest.fn(),
  removeStatusListener: jest.fn(),
  getMiningStatus: jest.fn(() => ({ status: 'stopped' })),
  startMining: jest.fn(() => Promise.resolve()),
  stopMining: jest.fn(() => Promise.resolve()),
  generateMiningMetrics: jest.fn(() => ({}))
}));

const mockWallet = {
  id: 'test-wallet',
  address: '0x1234567890abcdef',
  balance: 100.5
};

describe('MiningTab', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders mining tab with wallet', async () => {
    render(<MiningTab wallet={mockWallet} />);
    
    await waitFor(() => {
      expect(screen.getByText('Minería con IA - Consenso PoAIP')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Convierte tu wallet en un nodo validador ejecutando una IA local certificada')).toBeInTheDocument();
  });

  test('shows no wallet message when wallet is null', () => {
    render(<MiningTab wallet={null} />);
    
    expect(screen.getByText('Cartera requerida')).toBeInTheDocument();
    expect(screen.getByText('Necesitas tener una cartera activa para participar en la minería con IA.')).toBeInTheDocument();
  });

  test('displays system requirements', async () => {
    render(<MiningTab wallet={mockWallet} />);
    
    await waitFor(() => {
      expect(screen.getByText('Requisitos del Sistema')).toBeInTheDocument();
    });
  });

  test('displays certified models dropdown', async () => {
    render(<MiningTab wallet={mockWallet} />);
    
    await waitFor(() => {
      expect(screen.getByText('Modelos IA Certificados')).toBeInTheDocument();
    });
    
    const dropdown = screen.getByRole('combobox');
    expect(dropdown).toBeInTheDocument();
  });

  test('shows model information when model is selected', async () => {
    render(<MiningTab wallet={mockWallet} />);
    
    await waitFor(() => {
      const dropdown = screen.getByRole('combobox');
      fireEvent.change(dropdown, { target: { value: 'gemma-3-4b' } });
    });

    await waitFor(() => {
      expect(screen.getByText('Gemma 3 4B')).toBeInTheDocument();
      expect(screen.getByText('Test model')).toBeInTheDocument();
    });
  });

  test('displays mining controls', async () => {
    render(<MiningTab wallet={mockWallet} />);
    
    await waitFor(() => {
      expect(screen.getByText('Control de Minería')).toBeInTheDocument();
    });
  });

  test('shows mining information section', async () => {
    render(<MiningTab wallet={mockWallet} />);
    
    await waitFor(() => {
      expect(screen.getByText('Información de Minería')).toBeInTheDocument();
      expect(screen.getByText('Solo IAs pueden minar:')).toBeInTheDocument();
      expect(screen.getByText('Recompensas equitativas:')).toBeInTheDocument();
      expect(screen.getByText('Verificación de modelos:')).toBeInTheDocument();
      expect(screen.getByText('Consenso distribuido:')).toBeInTheDocument();
    });
  });

  test('handles model selection and shows start mining button', async () => {
    render(<MiningTab wallet={mockWallet} />);
    
    await waitFor(() => {
      const dropdown = screen.getByRole('combobox');
      fireEvent.change(dropdown, { target: { value: 'gemma-3-4b' } });
    });

    await waitFor(() => {
      expect(screen.getByText('Descargar e Iniciar Minería')).toBeInTheDocument();
    });
  });
});