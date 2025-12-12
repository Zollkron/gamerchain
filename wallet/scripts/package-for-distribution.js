#!/usr/bin/env node
/**
 * Package PlayerGold Wallet for Distribution
 * 
 * This script packages the wallet with the Python backend for end-user distribution.
 * Creates a portable package that users can simply extract and run.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🎁 PlayerGold Wallet - Distribution Packager');
console.log('==========================================');

const projectRoot = path.join(__dirname, '..', '..');
const walletRoot = path.join(__dirname, '..');
const distDir = path.join(walletRoot, 'dist-portable');

// Clean and create distribution directory
if (fs.existsSync(distDir)) {
  console.log('🧹 Cleaning existing distribution directory...');
  fs.rmSync(distDir, { recursive: true, force: true });
}

fs.mkdirSync(distDir, { recursive: true });

console.log('📦 Building React app...');
try {
  execSync('npm run build', { 
    cwd: walletRoot, 
    stdio: 'inherit' 
  });
} catch (error) {
  console.error('❌ Failed to build React app:', error.message);
  process.exit(1);
}

console.log('📋 Copying wallet files...');

// Copy essential wallet files
const walletFiles = [
  'build',
  'src/main.js',
  'src/preload.js',
  'src/services',
  'package.json',
  'node_modules'
];

walletFiles.forEach(file => {
  const srcPath = path.join(walletRoot, file);
  const destPath = path.join(distDir, 'wallet', file);
  
  if (fs.existsSync(srcPath)) {
    console.log(`  📄 Copying ${file}...`);
    copyRecursive(srcPath, destPath);
  } else {
    console.warn(`  ⚠️  ${file} not found, skipping...`);
  }
});

console.log('🐍 Copying Python backend...');

// Copy Python backend files
const backendFiles = [
  'src',
  'scripts/start_multinode_network.py',
  'requirements.txt',
  'api_final.py'
];

backendFiles.forEach(file => {
  const srcPath = path.join(projectRoot, file);
  const destPath = path.join(distDir, 'backend', file);
  
  if (fs.existsSync(srcPath)) {
    console.log(`  🐍 Copying ${file}...`);
    copyRecursive(srcPath, destPath);
  } else {
    console.warn(`  ⚠️  ${file} not found, skipping...`);
  }
});

console.log('📝 Creating launcher scripts...');

// Create Windows launcher
const windowsLauncher = `@echo off
title PlayerGold Wallet - Hecho por gamers para gamers
echo.
echo ===============================================
echo    PlayerGold Wallet - Starting...
echo    Hecho por gamers para gamers
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Por favor instala Python 3.8 o superior.
    echo    Descarga desde: https://www.python.org/downloads/
    echo    Asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js no encontrado. Por favor instala Node.js.
    echo    Descarga desde: https://nodejs.org/
    pause
    exit /b 1
)

REM Install Python dependencies if needed
if not exist "backend\\venv" (
    echo 🐍 Configurando entorno Python por primera vez...
    cd backend
    python -m venv venv
    call venv\\Scripts\\activate
    pip install -r requirements.txt
    cd ..
)

REM Create data directory
if not exist "data" mkdir data

REM Start the wallet
echo 🚀 Iniciando PlayerGold Wallet...
cd wallet
electron .

pause
`;

fs.writeFileSync(path.join(distDir, 'PlayerGold-Wallet.bat'), windowsLauncher);

// Create Linux/Mac launcher
const unixLauncher = `#!/bin/bash
echo "==============================================="
echo "   PlayerGold Wallet - Starting..."
echo "   Hecho por gamers para gamers"
echo "==============================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8 or higher."
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   macOS: brew install python3"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Install Python dependencies if needed
if [ ! -d "backend/venv" ]; then
    echo "🐍 Setting up Python environment for the first time..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Create data directory
mkdir -p data

# Start the wallet
echo "🚀 Starting PlayerGold Wallet..."
cd wallet
electron .
`;

fs.writeFileSync(path.join(distDir, 'PlayerGold-Wallet.sh'), unixLauncher);
fs.chmodSync(path.join(distDir, 'PlayerGold-Wallet.sh'), '755');

// Create README for users
const userReadme = `# PlayerGold Wallet - Portable Edition

¡Bienvenido a PlayerGold! La primera criptomoneda hecha por gamers para gamers.

## 🚀 Inicio Rápido

### Windows
1. Haz doble clic en \`PlayerGold-Wallet.bat\`
2. La primera vez instalará las dependencias automáticamente
3. ¡Listo! Tu wallet se abrirá

### Linux/Mac
1. Abre terminal en esta carpeta
2. Ejecuta: \`./PlayerGold-Wallet.sh\`
3. La primera vez instalará las dependencias automáticamente
4. ¡Listo! Tu wallet se abrirá

## 📋 Requisitos del Sistema

- **Python 3.8+** (se descarga gratis desde python.org)
- **Node.js** (se descarga gratis desde nodejs.org)
- **4GB RAM mínimo** (8GB recomendado para minería)
- **Conexión a Internet**

## 🎮 ¿Cómo empezar?

1. **Crear tu primera cartera**: Al abrir la wallet, crea una nueva cartera
2. **Conseguir tokens de prueba**: Usa el faucet de testnet para obtener PRGLD gratis
3. **Empezar a minar**: Ve a la pestaña "Minería" y descarga un modelo IA
4. **¡Conectar con otros!**: Cuando otro usuario haga lo mismo, crearán la red juntos

## 🤖 Minería con IA

PlayerGold usa Inteligencia Artificial para el consenso. Esto significa:
- Solo las IAs pueden validar transacciones (no humanos)
- Es justo: no importa cuánto dinero tengas
- Es ecológico: no necesita hardware especializado
- Es democrático: gestionado por IAs sin sesgos

## 🌐 Red Distribuida

- **Testnet**: Para pruebas (tokens gratis)
- **Mainnet**: Red principal (próximamente)
- **P2P**: Tu wallet se conecta directamente con otros usuarios
- **Sin servidores centrales**: Verdaderamente descentralizado

## 🆘 Problemas Comunes

### "Python no encontrado"
- Instala Python desde: https://www.python.org/downloads/
- ⚠️ IMPORTANTE: Marca "Add Python to PATH" durante la instalación

### "Node.js no encontrado"  
- Instala Node.js desde: https://nodejs.org/

### "No se puede conectar a la red"
- Verifica tu conexión a Internet
- Asegúrate de que no hay firewall bloqueando la aplicación
- En testnet, puedes usar IPs locales para probar con amigos

### "Error al iniciar minería"
- Verifica que tienes al menos 4GB de RAM libre
- Descarga un modelo IA desde la pestaña de minería
- Espera a que otro usuario se conecte para crear la red

## 📞 Soporte

- **Documentación**: Revisa los archivos .md en la carpeta del proyecto
- **Logs**: Los logs se guardan en la carpeta \`data/\`
- **Comunidad**: PlayerGold es un proyecto de código abierto

## 🎯 Filosofía

PlayerGold es:
- **Hecho por gamers para gamers**
- **Totalmente libre y democrático**
- **Sin censura ni restricciones ideológicas**
- **Gestionado por IA para eliminar sesgos humanos**

¡Disfruta de la verdadera libertad financiera en gaming!

---
PlayerGold Team - Diciembre 2025
`;

fs.writeFileSync(path.join(distDir, 'README.md'), userReadme);

// Create package info
const packageInfo = {
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
};

fs.writeFileSync(path.join(distDir, 'package-info.json'), JSON.stringify(packageInfo, null, 2));

console.log('✅ Distribution package created successfully!');
console.log(`📁 Location: ${distDir}`);
console.log('');
console.log('📋 Package contents:');
console.log('  📱 wallet/ - Electron application');
console.log('  🐍 backend/ - Python blockchain node');
console.log('  🚀 PlayerGold-Wallet.bat - Windows launcher');
console.log('  🚀 PlayerGold-Wallet.sh - Linux/Mac launcher');
console.log('  📖 README.md - User documentation');
console.log('');
console.log('🎁 Ready for distribution! Users can simply:');
console.log('  1. Extract the package');
console.log('  2. Run the launcher script');
console.log('  3. Start mining and creating the network!');

/**
 * Recursively copy files and directories
 */
function copyRecursive(src, dest) {
  const stat = fs.statSync(src);
  
  if (stat.isDirectory()) {
    // Create directory if it doesn't exist
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    
    // Copy all files in directory
    const files = fs.readdirSync(src);
    files.forEach(file => {
      copyRecursive(path.join(src, file), path.join(dest, file));
    });
  } else {
    // Copy file
    const destDir = path.dirname(dest);
    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
    }
    fs.copyFileSync(src, dest);
  }
}