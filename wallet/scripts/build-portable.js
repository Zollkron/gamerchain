#!/usr/bin/env node
/**
 * Enhanced Portable Build Script for PlayerGold Wallet
 * 
 * Creates a complete portable distribution package with:
 * - Automatic environment detection and configuration
 * - Pioneer mode initialization for new installations
 * - No technical configuration requirements for users
 * - Single executable or simple folder structure
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🎁 PlayerGold Wallet - Enhanced Portable Builder');
console.log('===============================================');

const projectRoot = path.join(__dirname, '..', '..');
const walletRoot = path.join(__dirname, '..');
const distDir = path.join(walletRoot, 'dist-portable');

/**
 * Main build process
 */
async function buildPortableDistribution() {
  try {
    // Step 1: Clean and prepare
    await cleanAndPrepare();
    
    // Step 2: Build React application
    await buildReactApp();
    
    // Step 3: Copy essential files
    await copyEssentialFiles();
    
    // Step 4: Create enhanced launcher scripts
    await createEnhancedLaunchers();
    
    // Step 5: Create user documentation
    await createUserDocumentation();
    
    // Step 6: Create package metadata
    await createPackageMetadata();
    
    // Step 7: Validate package structure
    await validatePackageStructure();
    
    console.log('✅ Portable distribution created successfully!');
    console.log(`📁 Location: ${distDir}`);
    console.log('');
    console.log('🎯 Ready for distribution! Users can:');
    console.log('  1. Extract the package anywhere');
    console.log('  2. Run the launcher script');
    console.log('  3. Start using PlayerGold immediately!');
    
  } catch (error) {
    console.error('❌ Build failed:', error.message);
    process.exit(1);
  }
}

/**
 * Clean existing distribution and create fresh directory
 */
async function cleanAndPrepare() {
  console.log('🧹 Cleaning and preparing distribution directory...');
  
  if (fs.existsSync(distDir)) {
    fs.rmSync(distDir, { recursive: true, force: true });
  }
  
  fs.mkdirSync(distDir, { recursive: true });
}

/**
 * Build React application
 */
async function buildReactApp() {
  console.log('📦 Building React application...');
  
  try {
    execSync('npm run build', { 
      cwd: walletRoot, 
      stdio: 'inherit' 
    });
  } catch (error) {
    throw new Error(`Failed to build React app: ${error.message}`);
  }
}

/**
 * Copy essential files for portable distribution
 */
async function copyEssentialFiles() {
  console.log('📋 Copying essential files...');
  
  // Wallet files
  const walletFiles = [
    'build',
    'src/main.js',
    'src/preload.js', 
    'src/services',
    'package.json',
    'node_modules'
  ];
  
  console.log('  📱 Copying wallet files...');
  walletFiles.forEach(file => {
    const srcPath = path.join(walletRoot, file);
    const destPath = path.join(distDir, 'wallet', file);
    
    if (fs.existsSync(srcPath)) {
      console.log(`    📄 ${file}`);
      copyRecursive(srcPath, destPath);
    } else {
      console.warn(`    ⚠️  ${file} not found, skipping...`);
    }
  });
  
  // Backend files
  const backendFiles = [
    'src',
    'scripts/start_multinode_network.py',
    'scripts/setup_testnet_genesis.py',
    'requirements.txt',
    'api_final.py'
  ];
  
  console.log('  🐍 Copying backend files...');
  backendFiles.forEach(file => {
    const srcPath = path.join(projectRoot, file);
    const destPath = path.join(distDir, 'backend', file);
    
    if (fs.existsSync(srcPath)) {
      console.log(`    🐍 ${file}`);
      copyRecursive(srcPath, destPath);
    } else {
      console.warn(`    ⚠️  ${file} not found, skipping...`);
    }
  });
}

/**
 * Create enhanced launcher scripts with environment detection
 */
async function createEnhancedLaunchers() {
  console.log('📝 Creating enhanced launcher scripts...');
  
  // Windows launcher with full environment detection and pioneer mode
  const windowsLauncher = `@echo off
chcp 65001 >nul
title PlayerGold Wallet - Hecho por gamers para gamers
echo.
echo ===============================================
echo    PlayerGold Wallet - Starting...
echo    Hecho por gamers para gamers
echo ===============================================
echo.

REM Automatic Environment Detection and Configuration
echo Detectando entorno del sistema...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Por favor instala Python 3.8 o superior.
    echo    Descarga desde: https://www.python.org/downloads/
    echo    IMPORTANTE: Marca "Add Python to PATH" durante la instalacion.
    echo.
    echo    Despues de instalar Python, ejecuta este archivo de nuevo.
    pause
    exit /b 1
)

REM Check if Node.js is installed  
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no encontrado. Por favor instala Node.js.
    echo    Descarga desde: https://nodejs.org/
    echo    Recomendamos la version LTS.
    echo.
    echo    Despues de instalar Node.js, ejecuta este archivo de nuevo.
    pause
    exit /b 1
)

echo OK: Requisitos del sistema verificados correctamente.
echo.

REM Automatic Environment Configuration
echo Configurando entorno automaticamente...

REM Create comprehensive data directory structure
echo Creando estructura de directorios...
if not exist "data" mkdir data
if not exist "data\\wallets" mkdir data\\wallets
if not exist "data\\blockchain" mkdir data\\blockchain
if not exist "data\\logs" mkdir data\\logs
if not exist "data\\models" mkdir data\\models
if not exist "data\\temp" mkdir data\\temp

REM Pioneer Mode Initialization for New Installations
if not exist "data\\bootstrap-state.json" (
    echo Primera instalacion detectada - Inicializando modo pionero...
    echo {"mode":"pioneer","initialized":true,"timestamp":"%date% %time%","version":"1.0.0","portable":true} > data\\bootstrap-state.json
    echo OK: Modo pionero inicializado. Listo para crear la red!
    echo.
    echo Que significa esto?
    echo    - Eres un usuario pionero de PlayerGold
    echo    - Tu wallet buscara automaticamente otros usuarios
    echo    - Cuando encuentre otros pioneros, crearan la red juntos
    echo    - No necesitas hacer nada tecnico!
    echo.
)

REM Set environment variables for portable mode
set PLAYERGOLD_PORTABLE=true
set PLAYERGOLD_DATA_DIR=%cd%\\data
set PLAYERGOLD_BOOTSTRAP_MODE=auto
set NODE_ENV=production

REM Final system check
echo Verificacion final del sistema...
python -c "import sys; print('Python version:', sys.version)" 2>nul
node --version 2>nul
echo.

REM Check if wallet directory exists
if not exist "wallet" (
    echo ERROR: Directorio wallet no encontrado
    echo Verifica que la wallet este compilada correctamente
    pause
    exit /b 1
)

REM Start the wallet with enhanced portable mode support
echo Iniciando PlayerGold Wallet en modo portable...
echo    Modo: Pionero automatico
echo    Directorio de datos: %cd%\\data
echo.
cd wallet

REM Check if electron is available
if not exist "node_modules\\.bin\\electron.cmd" (
    echo Instalando dependencias de Electron...
    npm install electron
    if errorlevel 1 (
        echo ERROR: No se pudo instalar Electron
        echo Verifica tu conexion a Internet
        pause
        exit /b 1
    )
)

REM Start the wallet
echo Iniciando aplicacion Electron...
electron . --portable --pioneer-mode --no-sandbox

if errorlevel 1 (
    echo.
    echo ERROR: Error al iniciar la wallet.
    echo Posibles soluciones:
    echo    1. Reinicia tu computadora e intenta de nuevo
    echo    2. Ejecuta como administrador
    echo    3. Verifica que no hay antivirus bloqueando la aplicacion
    echo    4. Verifica que Electron este instalado correctamente
    echo.
)

pause
`;

  // Unix launcher with full environment detection and pioneer mode
  const unixLauncher = `#!/bin/bash
echo "==============================================="
echo "   PlayerGold Wallet - Starting..."
echo "   Hecho por gamers para gamers"
echo "==============================================="
echo

# Automatic Environment Detection and Configuration
echo "🔍 Detecting system environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8 or higher."
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "   macOS: brew install python3"
    echo "   Or download from: https://www.python.org/downloads/"
    echo
    echo "💡 After installing Python, run this script again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js."
    echo "   Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "   CentOS/RHEL: curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash - && sudo yum install -y nodejs"
    echo "   macOS: brew install node"
    echo "   Or download from: https://nodejs.org/"
    echo
    echo "💡 After installing Node.js, run this script again."
    exit 1
fi

echo "✅ System requirements verified successfully."
echo

# Automatic Environment Configuration
echo "⚙️ Configuring environment automatically..."

# Install Python dependencies if needed
if [ ! -d "backend/venv" ]; then
    echo "🐍 Setting up Python environment for the first time..."
    echo "   This may take a few minutes..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error installing Python dependencies."
        echo "   Please check your internet connection and try again."
        exit 1
    fi
    cd ..
    echo "✅ Python environment configured successfully."
fi

# Create comprehensive data directory structure
echo "📁 Creating directory structure..."
mkdir -p data/wallets
mkdir -p data/blockchain
mkdir -p data/logs
mkdir -p data/models
mkdir -p data/temp

# Pioneer Mode Initialization for New Installations
if [ ! -f "data/bootstrap-state.json" ]; then
    echo "🚀 First installation detected - Initializing pioneer mode..."
    echo "{\\"mode\\":\\"pioneer\\",\\"initialized\\":true,\\"timestamp\\":\\"$(date)\\",\\"version\\":\\"1.0.0\\",\\"portable\\":true}" > data/bootstrap-state.json
    echo "✅ Pioneer mode initialized. Ready to create the network!"
    echo
    echo "🎮 What does this mean?"
    echo "   - You are a PlayerGold pioneer user"
    echo "   - Your wallet will automatically search for other users"
    echo "   - When it finds other pioneers, you'll create the network together"
    echo "   - You don't need to do anything technical!"
    echo
fi

# Set environment variables for portable mode
export PLAYERGOLD_PORTABLE=true
export PLAYERGOLD_DATA_DIR="$(pwd)/data"
export PLAYERGOLD_BOOTSTRAP_MODE=auto
export NODE_ENV=production

# Final system check
echo "🔧 Final system verification..."
python3 --version 2>/dev/null
node --version 2>/dev/null
echo

# Start the wallet with enhanced portable mode support
echo "🚀 Starting PlayerGold Wallet in portable mode..."
echo "   Mode: Automatic Pioneer"
echo "   Data directory: $(pwd)/data"
echo
cd wallet
electron . --portable --pioneer-mode --no-sandbox

if [ $? -ne 0 ]; then
    echo
    echo "❌ Error starting the wallet."
    echo "💡 Possible solutions:"
    echo "   1. Restart your computer and try again"
    echo "   2. Run with sudo if needed"
    echo "   3. Check that no antivirus is blocking the application"
    echo
fi
`;

  // Write launcher scripts
  fs.writeFileSync(path.join(distDir, 'PlayerGold-Wallet.bat'), windowsLauncher);
  fs.writeFileSync(path.join(distDir, 'PlayerGold-Wallet.sh'), unixLauncher);
  
  // Make Unix launcher executable
  if (process.platform !== 'win32') {
    fs.chmodSync(path.join(distDir, 'PlayerGold-Wallet.sh'), '755');
  }
  
  console.log('  ✅ Enhanced launcher scripts created');
}

/**
 * Create comprehensive user documentation
 */
async function createUserDocumentation() {
  console.log('📖 Creating user documentation...');
  
  const userReadme = `# PlayerGold Wallet - Portable Edition

¡Bienvenido a PlayerGold! La primera criptomoneda hecha por gamers para gamers.

## 🚀 Inicio Rápido (¡Solo 2 pasos!)

### Windows
1. **Haz doble clic** en \`PlayerGold-Wallet.bat\`
2. **¡Listo!** La primera vez instalará todo automáticamente

### Linux/Mac
1. **Abre terminal** en esta carpeta y ejecuta: \`./PlayerGold-Wallet.sh\`
2. **¡Listo!** La primera vez instalará todo automáticamente

## 📋 Requisitos del Sistema

- **Python 3.8+** (se descarga gratis desde [python.org](https://python.org))
- **Node.js 16+** (se descarga gratis desde [nodejs.org](https://nodejs.org))
- **4GB RAM mínimo** (8GB recomendado para minería)
- **2GB espacio libre** en disco
- **Conexión a Internet**

## 🎮 ¿Cómo empezar? (Para no técnicos)

### Paso 1: Crear tu primera cartera
- Al abrir la wallet, haz clic en "Crear Nueva Cartera"
- Guarda bien tu frase de recuperación (¡es súper importante!)
- ¡Ya tienes tu dirección PlayerGold!

### Paso 2: Conseguir tokens de prueba
- Ve a la pestaña "Faucet" 
- Haz clic en "Solicitar PRGLD gratis"
- ¡Recibirás tokens para probar!

### Paso 3: Empezar a minar
- Ve a la pestaña "Minería"
- Descarga un modelo IA (recomendamos empezar con el más pequeño)
- Haz clic en "Iniciar Minería"

### Paso 4: ¡Conectar con otros!
- Cuando otro usuario haga lo mismo, ¡crearán la red automáticamente!
- No necesitas configurar nada, todo es automático

## 🤖 ¿Qué es la Minería con IA?

PlayerGold es diferente a otras criptomonedas:

- **🧠 Solo las IAs pueden validar** (no humanos)
- **⚖️ Es justo**: No importa cuánto dinero tengas
- **🌱 Es ecológico**: No necesita hardware especializado
- **🗳️ Es democrático**: Gestionado por IAs sin sesgos humanos

## 🌐 Red Distribuida (P2P)

- **🧪 Testnet**: Para pruebas (tokens gratis)
- **🌍 Mainnet**: Red principal (próximamente)
- **🔗 P2P**: Tu wallet se conecta directamente con otros usuarios
- **🏛️ Sin servidores centrales**: Verdaderamente descentralizado

## 🆘 Problemas Comunes y Soluciones

### "Python no encontrado"
1. Ve a [python.org/downloads](https://python.org/downloads)
2. Descarga Python 3.8 o superior
3. **⚠️ IMPORTANTE**: Marca "Add Python to PATH" durante la instalación
4. Reinicia tu computadora
5. Ejecuta PlayerGold de nuevo

### "Node.js no encontrado"  
1. Ve a [nodejs.org](https://nodejs.org)
2. Descarga la versión LTS (recomendada)
3. Instala normalmente
4. Reinicia tu computadora
5. Ejecuta PlayerGold de nuevo

### "No se puede conectar a la red"
- ✅ Verifica tu conexión a Internet
- ✅ Asegúrate de que no hay firewall bloqueando la aplicación
- ✅ En testnet, puedes usar IPs locales para probar con amigos
- ✅ Intenta reiniciar la aplicación

### "Error al iniciar minería"
- ✅ Verifica que tienes al menos 4GB de RAM libre
- ✅ Descarga un modelo IA desde la pestaña de minería
- ✅ Espera a que otro usuario se conecte para crear la red
- ✅ Cierra otros programas que usen mucha memoria

### "La aplicación no inicia"
- ✅ Ejecuta como administrador (Windows) o con sudo (Linux/Mac)
- ✅ Verifica que tu antivirus no esté bloqueando la aplicación
- ✅ Reinicia tu computadora
- ✅ Verifica que Python y Node.js estén instalados correctamente

## 📞 Soporte y Ayuda

- **📚 Documentación**: Revisa los archivos .md en la carpeta del proyecto
- **📝 Logs**: Los logs se guardan en la carpeta \`data/logs/\`
- **🌐 Comunidad**: PlayerGold es un proyecto de código abierto
- **🐛 Reportar problemas**: Usa GitHub Issues en el repositorio oficial

## 🎯 Filosofía PlayerGold

PlayerGold es:
- **🎮 Hecho por gamers para gamers**
- **🗽 Totalmente libre y democrático**
- **🚫 Sin censura ni restricciones ideológicas**
- **🤖 Gestionado por IA para eliminar sesgos humanos**
- **💰 Economía justa sin ventajas por dinero**

## 🔒 Seguridad y Privacidad

- **🔐 Tus claves privadas nunca salen de tu computadora**
- **🛡️ Comunicación P2P encriptada**
- **👤 Pseudónimo**: Solo se conoce tu dirección pública
- **💾 Respaldos locales**: Tú controlas tus datos

## 🚀 Próximas Funciones

- **🎮 Integración con juegos populares**
- **🏪 Marketplace de NFTs gaming**
- **⚡ Transacciones instantáneas**
- **🌍 Red principal (mainnet)**

---

**¡Disfruta de la verdadera libertad financiera en gaming!**

*PlayerGold Team - Diciembre 2025*

---

## 📋 Información Técnica (Para Desarrolladores)

### Estructura del Paquete
\`\`\`
PlayerGold-Wallet-Portable/
├── PlayerGold-Wallet.bat          # Launcher Windows
├── PlayerGold-Wallet.sh           # Launcher Unix/Mac
├── README.md                      # Esta documentación
├── package-info.json              # Metadatos del paquete
├── wallet/                        # Aplicación Electron
│   ├── build/                     # React app compilado
│   ├── src/                       # Código fuente
│   └── package.json               # Dependencias
├── backend/                       # Nodo blockchain Python
│   ├── src/                       # Código fuente Python
│   └── requirements.txt           # Dependencias Python
└── data/                          # Datos del usuario (se crea automáticamente)
    ├── wallets/                   # Carteras del usuario
    ├── blockchain/                # Datos de la blockchain
    ├── logs/                      # Archivos de log
    └── bootstrap-state.json       # Estado del bootstrap
\`\`\`

### Variables de Entorno
- \`PLAYERGOLD_PORTABLE=true\`: Modo portable activado
- \`PLAYERGOLD_DATA_DIR\`: Directorio de datos personalizado
- \`PLAYERGOLD_BOOTSTRAP_MODE=auto\`: Bootstrap automático
- \`NODE_ENV=production\`: Modo de producción

### Modo Pionero
El modo pionero se activa automáticamente en nuevas instalaciones:
1. Detecta si es la primera ejecución
2. Crea \`bootstrap-state.json\` con modo "pioneer"
3. Inicia búsqueda automática de peers
4. Forma la red cuando encuentra otros pioneros
`;

  fs.writeFileSync(path.join(distDir, 'README.md'), userReadme);
  
  console.log('  ✅ Comprehensive user documentation created');
}

/**
 * Create package metadata and information
 */
async function createPackageMetadata() {
  console.log('📋 Creating package metadata...');
  
  const packageInfo = {
    name: 'PlayerGold Wallet Portable',
    version: '1.0.0',
    description: 'Portable distribution of PlayerGold Wallet with integrated blockchain node and automatic P2P bootstrap',
    created: new Date().toISOString(),
    platform: process.platform,
    arch: process.arch,
    features: {
      portableMode: true,
      pioneerModeInitialization: true,
      automaticEnvironmentDetection: true,
      noTechnicalConfiguration: true,
      p2pAutoBootstrap: true
    },
    contents: {
      wallet: 'Electron wallet application with React UI',
      backend: 'Python blockchain node with P2P networking',
      launchers: 'Platform-specific startup scripts with environment detection',
      readme: 'Comprehensive user documentation in Spanish and English',
      dataStructure: 'Automatic data directory creation and management'
    },
    requirements: {
      python: '3.8+',
      nodejs: '16+',
      memory: '4GB minimum, 8GB recommended',
      storage: '2GB free space',
      network: 'Internet connection required'
    },
    supportedPlatforms: [
      'Windows 10/11',
      'macOS 10.15+',
      'Ubuntu 18.04+',
      'Debian 10+',
      'CentOS 7+',
      'Other Linux distributions with Python 3.8+ and Node.js 16+'
    ]
  };
  
  fs.writeFileSync(path.join(distDir, 'package-info.json'), JSON.stringify(packageInfo, null, 2));
  
  // Create version info file
  const versionInfo = {
    version: '1.0.0',
    buildDate: new Date().toISOString(),
    gitCommit: getGitCommit(),
    buildEnvironment: {
      node: process.version,
      platform: process.platform,
      arch: process.arch
    }
  };
  
  fs.writeFileSync(path.join(distDir, 'version.json'), JSON.stringify(versionInfo, null, 2));
  
  console.log('  ✅ Package metadata created');
}

/**
 * Validate the created package structure
 */
async function validatePackageStructure() {
  console.log('🔍 Validating package structure...');
  
  const requiredFiles = [
    'PlayerGold-Wallet.bat',
    'PlayerGold-Wallet.sh',
    'README.md',
    'package-info.json',
    'version.json',
    'wallet/package.json',
    'wallet/src/main.js',
    'wallet/build/index.html',
    'backend/requirements.txt'
  ];
  
  const requiredDirectories = [
    'wallet',
    'wallet/src',
    'wallet/build',
    'backend',
    'backend/src'
  ];
  
  // Check required files
  for (const file of requiredFiles) {
    const filePath = path.join(distDir, file);
    if (!fs.existsSync(filePath)) {
      throw new Error(`Required file missing: ${file}`);
    }
  }
  
  // Check required directories
  for (const dir of requiredDirectories) {
    const dirPath = path.join(distDir, dir);
    if (!fs.existsSync(dirPath) || !fs.statSync(dirPath).isDirectory()) {
      throw new Error(`Required directory missing: ${dir}`);
    }
  }
  
  // Validate launcher script permissions
  const unixLauncher = path.join(distDir, 'PlayerGold-Wallet.sh');
  if (process.platform !== 'win32') {
    const stats = fs.statSync(unixLauncher);
    if (!(stats.mode & parseInt('111', 8))) {
      throw new Error('Unix launcher script is not executable');
    }
  }
  
  // Validate package-info.json structure
  const packageInfoPath = path.join(distDir, 'package-info.json');
  const packageInfo = JSON.parse(fs.readFileSync(packageInfoPath, 'utf8'));
  
  const requiredFields = ['name', 'version', 'description', 'created', 'features', 'contents'];
  for (const field of requiredFields) {
    if (!packageInfo.hasOwnProperty(field)) {
      throw new Error(`Package info missing required field: ${field}`);
    }
  }
  
  console.log('  ✅ Package structure validation passed');
}

/**
 * Get current git commit hash
 */
function getGitCommit() {
  try {
    return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
  } catch (error) {
    return 'unknown';
  }
}

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

// Run the build process
if (require.main === module) {
  buildPortableDistribution();
}

module.exports = {
  buildPortableDistribution,
  cleanAndPrepare,
  buildReactApp,
  copyEssentialFiles,
  createEnhancedLaunchers,
  createUserDocumentation,
  createPackageMetadata,
  validatePackageStructure
};