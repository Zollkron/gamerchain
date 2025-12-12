#!/usr/bin/env node
/**
 * Python Environment Setup for PlayerGold Wallet
 * 
 * This script automatically sets up the Python environment and dependencies
 * needed for the blockchain node to run.
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class PythonEnvironmentSetup {
  constructor() {
    this.projectRoot = path.join(__dirname, '..', '..');
    this.backendDir = path.join(this.projectRoot, 'backend');
    this.venvDir = path.join(this.backendDir, 'venv');
    this.requirementsFile = path.join(this.backendDir, 'requirements.txt');
  }

  /**
   * Check if Python is available
   */
  async checkPython() {
    console.log('🐍 Checking Python installation...');
    
    const pythonCommands = ['python', 'python3', 'py'];
    
    for (const cmd of pythonCommands) {
      try {
        const version = execSync(`${cmd} --version`, { 
          encoding: 'utf8',
          timeout: 5000 
        }).trim();
        
        console.log(`✅ Found Python: ${version}`);
        
        // Check if version is 3.8+
        const versionMatch = version.match(/Python (\d+)\.(\d+)/);
        if (versionMatch) {
          const major = parseInt(versionMatch[1]);
          const minor = parseInt(versionMatch[2]);
          
          if (major >= 3 && minor >= 8) {
            return { available: true, command: cmd, version };
          } else {
            console.warn(`⚠️ Python version ${major}.${minor} is too old (need 3.8+)`);
          }
        }
      } catch (error) {
        // Command not found, try next one
        continue;
      }
    }
    
    return { 
      available: false, 
      error: 'Python 3.8+ not found in system PATH' 
    };
  }

  /**
   * Create virtual environment
   */
  async createVirtualEnvironment(pythonCommand) {
    console.log('📦 Creating Python virtual environment...');
    
    try {
      // Create backend directory if it doesn't exist
      if (!fs.existsSync(this.backendDir)) {
        fs.mkdirSync(this.backendDir, { recursive: true });
      }
      
      // Create virtual environment
      execSync(`${pythonCommand} -m venv "${this.venvDir}"`, {
        cwd: this.backendDir,
        stdio: 'inherit'
      });
      
      console.log('✅ Virtual environment created successfully');
      return true;
      
    } catch (error) {
      console.error('❌ Failed to create virtual environment:', error.message);
      return false;
    }
  }

  /**
   * Install Python dependencies
   */
  async installDependencies(pythonCommand) {
    console.log('📚 Installing Python dependencies...');
    
    try {
      // Determine pip command based on platform
      const isWindows = process.platform === 'win32';
      const venvPython = isWindows 
        ? path.join(this.venvDir, 'Scripts', 'python.exe')
        : path.join(this.venvDir, 'bin', 'python');
      
      const venvPip = isWindows
        ? path.join(this.venvDir, 'Scripts', 'pip.exe')
        : path.join(this.venvDir, 'bin', 'pip');
      
      // Upgrade pip first
      console.log('⬆️ Upgrading pip...');
      execSync(`"${venvPip}" install --upgrade pip`, {
        cwd: this.backendDir,
        stdio: 'inherit'
      });
      
      // Install requirements if file exists
      if (fs.existsSync(this.requirementsFile)) {
        console.log('📋 Installing from requirements.txt...');
        execSync(`"${venvPip}" install -r requirements.txt`, {
          cwd: this.backendDir,
          stdio: 'inherit'
        });
      } else {
        // Install essential dependencies manually
        console.log('📋 Installing essential dependencies...');
        const essentialPackages = [
          'flask>=2.0.0',
          'requests>=2.25.0',
          'cryptography>=3.4.0',
          'asyncio-mqtt>=0.11.0'
        ];
        
        for (const pkg of essentialPackages) {
          console.log(`  Installing ${pkg}...`);
          execSync(`"${venvPip}" install "${pkg}"`, {
            cwd: this.backendDir,
            stdio: 'inherit'
          });
        }
      }
      
      console.log('✅ Dependencies installed successfully');
      return { success: true, venvPython, venvPip };
      
    } catch (error) {
      console.error('❌ Failed to install dependencies:', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * Verify installation
   */
  async verifyInstallation() {
    console.log('🔍 Verifying installation...');
    
    try {
      const isWindows = process.platform === 'win32';
      const venvPython = isWindows 
        ? path.join(this.venvDir, 'Scripts', 'python.exe')
        : path.join(this.venvDir, 'bin', 'python');
      
      // Test Python in virtual environment
      const testScript = `
import sys
print(f"Python version: {sys.version}")

# Test essential imports
try:
    import flask
    print("✅ Flask available")
except ImportError as e:
    print(f"❌ Flask not available: {e}")

try:
    import requests
    print("✅ Requests available")
except ImportError as e:
    print(f"❌ Requests not available: {e}")

try:
    import cryptography
    print("✅ Cryptography available")
except ImportError as e:
    print(f"❌ Cryptography not available: {e}")

print("🎉 Python environment verification complete")
`;
      
      // Write test script
      const testScriptPath = path.join(this.backendDir, 'test_env.py');
      fs.writeFileSync(testScriptPath, testScript);
      
      // Run test script
      execSync(`"${venvPython}" test_env.py`, {
        cwd: this.backendDir,
        stdio: 'inherit'
      });
      
      // Clean up test script
      fs.unlinkSync(testScriptPath);
      
      console.log('✅ Installation verification successful');
      return true;
      
    } catch (error) {
      console.error('❌ Installation verification failed:', error.message);
      return false;
    }
  }

  /**
   * Run complete setup process
   */
  async setup() {
    console.log('🚀 Starting Python environment setup...');
    console.log('=====================================');
    
    try {
      // Step 1: Check Python
      const pythonCheck = await this.checkPython();
      if (!pythonCheck.available) {
        console.error('❌ Python setup failed:', pythonCheck.error);
        console.log('');
        console.log('📋 To fix this:');
        console.log('  1. Install Python 3.8+ from https://www.python.org/downloads/');
        console.log('  2. Make sure to check "Add Python to PATH" during installation');
        console.log('  3. Restart this application');
        return { success: false, error: pythonCheck.error };
      }
      
      // Step 2: Create virtual environment if it doesn't exist
      if (!fs.existsSync(this.venvDir)) {
        const venvResult = await this.createVirtualEnvironment(pythonCheck.command);
        if (!venvResult) {
          return { success: false, error: 'Failed to create virtual environment' };
        }
      } else {
        console.log('✅ Virtual environment already exists');
      }
      
      // Step 3: Install dependencies
      const installResult = await this.installDependencies(pythonCheck.command);
      if (!installResult.success) {
        return { success: false, error: installResult.error };
      }
      
      // Step 4: Verify installation
      const verifyResult = await this.verifyInstallation();
      if (!verifyResult) {
        return { success: false, error: 'Installation verification failed' };
      }
      
      console.log('');
      console.log('🎉 Python environment setup completed successfully!');
      console.log('✅ PlayerGold blockchain node is ready to run');
      
      return { 
        success: true, 
        pythonCommand: pythonCheck.command,
        venvPath: this.venvDir
      };
      
    } catch (error) {
      console.error('❌ Setup failed:', error.message);
      return { success: false, error: error.message };
    }
  }
}

// Run setup if called directly
if (require.main === module) {
  const setup = new PythonEnvironmentSetup();
  setup.setup().then(result => {
    if (!result.success) {
      process.exit(1);
    }
  });
}

module.exports = PythonEnvironmentSetup;