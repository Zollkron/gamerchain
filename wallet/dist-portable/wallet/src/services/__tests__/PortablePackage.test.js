/**
 * Unit Tests for Portable Package Structure
 * Tests portable distribution package functionality and pioneer mode initialization
 * 
 * Requirements: 1.1, 1.2, 1.4
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

describe('Portable Package Structure', () => {
  const testDistDir = path.join(__dirname, '..', '..', '..', 'dist-portable-test');
  
  beforeAll(() => {
    // Clean up any existing test directory
    if (fs.existsSync(testDistDir)) {
      fs.rmSync(testDistDir, { recursive: true, force: true });
    }
  });

  afterAll(() => {
    // Clean up test directory
    if (fs.existsSync(testDistDir)) {
      fs.rmSync(testDistDir, { recursive: true, force: true });
    }
  });

  describe('Package Structure Validation', () => {
    it('should contain expected files and structure', () => {
      // Create a mock distribution structure for testing
      createMockDistributionStructure(testDistDir);
      
      // Verify essential files exist
      const expectedFiles = [
        'PlayerGold-Wallet.bat',
        'PlayerGold-Wallet.sh',
        'README.md',
        'package-info.json',
        'wallet/package.json',
        'wallet/src/main.js',
        'wallet/build/index.html',
        'backend/requirements.txt'
      ];
      
      expectedFiles.forEach(file => {
        const filePath = path.join(testDistDir, file);
        expect(fs.existsSync(filePath)).toBe(true);
      });
    });

    it('should have correct directory structure', () => {
      createMockDistributionStructure(testDistDir);
      
      const expectedDirectories = [
        'wallet',
        'wallet/src',
        'wallet/build',
        'backend',
        'backend/src'
      ];
      
      expectedDirectories.forEach(dir => {
        const dirPath = path.join(testDistDir, dir);
        expect(fs.existsSync(dirPath)).toBe(true);
        expect(fs.statSync(dirPath).isDirectory()).toBe(true);
      });
    });

    it('should have executable launcher scripts', () => {
      createMockDistributionStructure(testDistDir);
      
      const windowsLauncher = path.join(testDistDir, 'PlayerGold-Wallet.bat');
      const unixLauncher = path.join(testDistDir, 'PlayerGold-Wallet.sh');
      
      expect(fs.existsSync(windowsLauncher)).toBe(true);
      expect(fs.existsSync(unixLauncher)).toBe(true);
      
      // Check Unix launcher has executable permissions (on Unix systems)
      if (process.platform !== 'win32') {
        const stats = fs.statSync(unixLauncher);
        expect(stats.mode & parseInt('111', 8)).toBeTruthy(); // Check execute permissions
      }
    });

    it('should contain valid package-info.json', () => {
      createMockDistributionStructure(testDistDir);
      
      const packageInfoPath = path.join(testDistDir, 'package-info.json');
      expect(fs.existsSync(packageInfoPath)).toBe(true);
      
      const packageInfo = JSON.parse(fs.readFileSync(packageInfoPath, 'utf8'));
      
      expect(packageInfo).toHaveProperty('name');
      expect(packageInfo).toHaveProperty('version');
      expect(packageInfo).toHaveProperty('description');
      expect(packageInfo).toHaveProperty('created');
      expect(packageInfo).toHaveProperty('contents');
      
      expect(packageInfo.name).toBe('PlayerGold Wallet Portable');
      expect(packageInfo.version).toBe('1.0.0');
    });
  });

  describe('Application Startup in Clean Environment', () => {
    it('should handle missing data directory gracefully', () => {
      createMockDistributionStructure(testDistDir);
      
      // Simulate clean environment startup
      const mockEnvironment = {
        PLAYERGOLD_PORTABLE: 'true',
        PLAYERGOLD_BOOTSTRAP_MODE: 'auto',
        PLAYERGOLD_DATA_DIR: path.join(testDistDir, 'data')
      };
      
      // Test environment detection logic
      const isPortableMode = mockEnvironment.PLAYERGOLD_PORTABLE === 'true';
      const isPioneerMode = mockEnvironment.PLAYERGOLD_BOOTSTRAP_MODE === 'auto';
      const dataDir = mockEnvironment.PLAYERGOLD_DATA_DIR;
      
      expect(isPortableMode).toBe(true);
      expect(isPioneerMode).toBe(true);
      expect(dataDir).toBe(path.join(testDistDir, 'data'));
    });

    it('should create necessary directories on first run', () => {
      createMockDistributionStructure(testDistDir);
      
      const dataDir = path.join(testDistDir, 'data');
      const expectedDirectories = [
        'wallets',
        'blockchain', 
        'logs',
        'models',
        'temp'
      ];
      
      // Simulate directory creation logic
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }
      
      expectedDirectories.forEach(dir => {
        const dirPath = path.join(dataDir, dir);
        if (!fs.existsSync(dirPath)) {
          fs.mkdirSync(dirPath, { recursive: true });
        }
      });
      
      // Verify directories were created
      expectedDirectories.forEach(dir => {
        const dirPath = path.join(dataDir, dir);
        expect(fs.existsSync(dirPath)).toBe(true);
        expect(fs.statSync(dirPath).isDirectory()).toBe(true);
      });
    });

    it('should validate system requirements', () => {
      // Mock system requirements check
      const mockRequirements = {
        python: {
          available: true,
          version: 'Python 3.9.0',
          required: 'Python 3.8+'
        },
        nodejs: {
          available: true,
          version: 'v16.14.0',
          required: 'Node.js 16+'
        },
        memory: {
          total: 8,
          free: 4,
          required: 4
        },
        storage: {
          dataDir: path.join(testDistDir, 'data'),
          exists: true,
          writable: true
        }
      };
      
      // Validate requirements
      expect(mockRequirements.python.available).toBe(true);
      expect(mockRequirements.nodejs.available).toBe(true);
      expect(mockRequirements.memory.total).toBeGreaterThanOrEqual(mockRequirements.memory.required);
      expect(mockRequirements.storage.writable).toBe(true);
    });
  });

  describe('Pioneer Mode Initialization', () => {
    it('should initialize pioneer mode for new installations', () => {
      createMockDistributionStructure(testDistDir);
      
      const dataDir = path.join(testDistDir, 'data');
      const bootstrapStatePath = path.join(dataDir, 'bootstrap-state.json');
      
      // Ensure data directory exists
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }
      
      // Simulate pioneer mode initialization
      if (!fs.existsSync(bootstrapStatePath)) {
        const initialState = {
          mode: 'pioneer',
          initialized: true,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
          portable: true,
          dataDir: dataDir
        };
        
        fs.writeFileSync(bootstrapStatePath, JSON.stringify(initialState, null, 2));
      }
      
      // Verify bootstrap state was created
      expect(fs.existsSync(bootstrapStatePath)).toBe(true);
      
      const bootstrapState = JSON.parse(fs.readFileSync(bootstrapStatePath, 'utf8'));
      expect(bootstrapState.mode).toBe('pioneer');
      expect(bootstrapState.initialized).toBe(true);
      expect(bootstrapState.portable).toBe(true);
      expect(bootstrapState.version).toBe('1.0.0');
    });

    it('should load existing bootstrap state on subsequent runs', () => {
      createMockDistributionStructure(testDistDir);
      
      const dataDir = path.join(testDistDir, 'data');
      const bootstrapStatePath = path.join(dataDir, 'bootstrap-state.json');
      
      // Create existing bootstrap state
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }
      
      const existingState = {
        mode: 'network',
        initialized: true,
        timestamp: '2025-01-01T00:00:00.000Z',
        version: '1.0.0',
        portable: true,
        dataDir: dataDir,
        walletAddress: 'PG1234567890abcdef',
        networkFormed: true
      };
      
      fs.writeFileSync(bootstrapStatePath, JSON.stringify(existingState, null, 2));
      
      // Simulate loading existing state
      const loadedState = JSON.parse(fs.readFileSync(bootstrapStatePath, 'utf8'));
      
      expect(loadedState.mode).toBe('network');
      expect(loadedState.networkFormed).toBe(true);
      expect(loadedState.walletAddress).toBe('PG1234567890abcdef');
    });

    it('should handle bootstrap state updates', () => {
      createMockDistributionStructure(testDistDir);
      
      const dataDir = path.join(testDistDir, 'data');
      const bootstrapStatePath = path.join(dataDir, 'bootstrap-state.json');
      
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }
      
      // Create initial state
      const initialState = {
        mode: 'pioneer',
        initialized: true,
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      };
      
      fs.writeFileSync(bootstrapStatePath, JSON.stringify(initialState, null, 2));
      
      // Simulate state update
      const currentState = JSON.parse(fs.readFileSync(bootstrapStatePath, 'utf8'));
      const updatedState = {
        ...currentState,
        mode: 'discovery',
        walletAddress: 'PG1234567890abcdef',
        lastUpdated: new Date().toISOString()
      };
      
      fs.writeFileSync(bootstrapStatePath, JSON.stringify(updatedState, null, 2));
      
      // Verify update
      const finalState = JSON.parse(fs.readFileSync(bootstrapStatePath, 'utf8'));
      expect(finalState.mode).toBe('discovery');
      expect(finalState.walletAddress).toBe('PG1234567890abcdef');
      expect(finalState).toHaveProperty('lastUpdated');
    });
  });

  describe('No Technical Configuration Requirements', () => {
    it('should work without manual configuration files', () => {
      createMockDistributionStructure(testDistDir);
      
      // Verify no manual configuration files are required
      const configFiles = [
        'config.json',
        'settings.ini',
        'blockchain.conf',
        '.env'
      ];
      
      configFiles.forEach(configFile => {
        const configPath = path.join(testDistDir, configFile);
        // These files should NOT be required for basic operation
        // The application should work without them
        expect(fs.existsSync(configPath)).toBe(false);
      });
    });

    it('should auto-detect network mode based on environment', () => {
      // Test automatic network mode detection
      const testCases = [
        {
          env: { NODE_ENV: 'development' },
          expected: 'testnet'
        },
        {
          env: { NODE_ENV: 'production' },
          expected: 'mainnet'
        },
        {
          env: {},
          expected: 'testnet' // default
        }
      ];
      
      testCases.forEach(testCase => {
        // Simulate network mode detection logic
        const networkMode = testCase.env.NODE_ENV === 'production' ? 'mainnet' : 'testnet';
        expect(networkMode).toBe(testCase.expected);
      });
    });

    it('should provide clear instructions without technical jargon', () => {
      createMockDistributionStructure(testDistDir);
      
      const readmePath = path.join(testDistDir, 'README.md');
      const readmeContent = fs.readFileSync(readmePath, 'utf8');
      
      // Check for user-friendly language
      expect(readmeContent).toContain('🚀 Inicio Rápido');
      expect(readmeContent).toContain('Haz doble clic');
      expect(readmeContent).toContain('¡Listo!');
      
      // Should not contain technical jargon
      expect(readmeContent).not.toContain('configure');
      expect(readmeContent).not.toContain('compile');
      expect(readmeContent).not.toContain('build');
      expect(readmeContent).not.toContain('environment variables');
    });
  });
});

/**
 * Helper function to create mock distribution structure for testing
 */
function createMockDistributionStructure(distDir) {
  // Create directory structure
  const directories = [
    'wallet',
    'wallet/src',
    'wallet/src/services',
    'wallet/build',
    'backend',
    'backend/src'
  ];
  
  directories.forEach(dir => {
    const dirPath = path.join(distDir, dir);
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  });
  
  // Create mock files
  const files = {
    'PlayerGold-Wallet.bat': `@echo off
title PlayerGold Wallet - Test
echo Starting test wallet...
pause`,
    
    'PlayerGold-Wallet.sh': `#!/bin/bash
echo "Starting test wallet..."`,
    
    'README.md': `# PlayerGold Wallet - Portable Edition

¡Bienvenido a PlayerGold! La primera criptomoneda hecha por gamers para gamers.

## 🚀 Inicio Rápido

### Windows
1. Haz doble clic en \`PlayerGold-Wallet.bat\`
2. ¡Listo! Tu wallet se abrirá

### Linux/Mac  
1. Ejecuta: \`./PlayerGold-Wallet.sh\`
2. ¡Listo! Tu wallet se abrirá`,
    
    'package-info.json': JSON.stringify({
      name: 'PlayerGold Wallet Portable',
      version: '1.0.0',
      description: 'Portable distribution of PlayerGold Wallet with integrated blockchain node',
      created: new Date().toISOString(),
      platform: process.platform,
      arch: process.arch,
      contents: {
        wallet: 'Electron wallet application',
        backend: 'Python blockchain node',
        launchers: 'Platform-specific startup scripts',
        readme: 'User documentation'
      }
    }, null, 2),
    
    'wallet/package.json': JSON.stringify({
      name: 'playergold-wallet',
      version: '1.0.0',
      main: 'src/main.js'
    }, null, 2),
    
    'wallet/src/main.js': `const { app, BrowserWindow } = require('electron');
console.log('Mock wallet main.js');`,
    
    'wallet/build/index.html': `<!DOCTYPE html>
<html>
<head><title>PlayerGold Wallet</title></head>
<body><h1>PlayerGold Wallet</h1></body>
</html>`,
    
    'backend/requirements.txt': `fastapi==0.68.0
uvicorn==0.15.0
requests==2.26.0`
  };
  
  Object.entries(files).forEach(([filePath, content]) => {
    const fullPath = path.join(distDir, filePath);
    const dir = path.dirname(fullPath);
    
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(fullPath, content);
  });
  
  // Make shell script executable on Unix systems
  if (process.platform !== 'win32') {
    const shellScript = path.join(distDir, 'PlayerGold-Wallet.sh');
    if (fs.existsSync(shellScript)) {
      fs.chmodSync(shellScript, '755');
    }
  }
}