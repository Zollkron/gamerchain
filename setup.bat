@echo off
title PlayerGold - Setup Completo
echo.
echo ===============================================
echo    PlayerGold - Setup Completo
echo    Hecho por gamers para gamers
echo ===============================================
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo.
    echo 💡 Solución:
    echo    1. Descarga Python desde: https://python.org/downloads/
    echo    2. Durante la instalación, marca "Add Python to PATH"
    echo    3. Reinicia tu computadora
    echo    4. Ejecuta este script de nuevo
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado:
python --version
echo.

REM Verificar pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: pip no está disponible
    echo 💡 Reinstala Python marcando "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ pip disponible
echo.

REM Mostrar opciones de setup
echo Selecciona el tipo de setup:
echo.
echo [1] Setup Completo (Backend + Wallet)
echo [2] Solo Backend (Nodo blockchain)
echo [3] Solo Wallet (Interfaz de usuario)
echo [4] Verificar Sistema
echo [5] Limpiar e Instalar Todo
echo.
set /p choice="Ingresa tu opcion (1-5): "

if "%choice%"=="1" goto full_setup
if "%choice%"=="2" goto backend_setup
if "%choice%"=="3" goto wallet_setup
if "%choice%"=="4" goto verify_system
if "%choice%"=="5" goto clean_install
echo Opcion invalida
pause
exit /b 1

:full_setup
echo.
echo ========================================
echo SETUP COMPLETO
echo ========================================
echo.
echo [1/4] Instalando dependencias Python...
pip install -r requirements.txt
if errorlevel 1 goto error

echo [2/4] Configurando wallet...
cd wallet
call npm install
if errorlevel 1 goto error_wallet

echo [3/4] Compilando wallet...
call npm run build
if errorlevel 1 goto error_wallet
cd ..

echo [4/4] Verificando instalación...
python -c "import torch, transformers, fastapi" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Algunas dependencias Python pueden no estar disponibles
    echo    Esto es normal si no tienes GPU compatible
)

echo.
echo ✅ Setup completo terminado
echo.
echo 🚀 Para iniciar:
echo    - Backend: python scripts/start_multinode_network.py
echo    - Wallet: cd wallet && npm start
echo    - Todo junto: wallet/build-complete.bat
goto end

:backend_setup
echo.
echo ========================================
echo SETUP BACKEND
echo ========================================
echo.
echo [1/2] Instalando dependencias Python...
pip install -r requirements.txt
if errorlevel 1 goto error

echo [2/2] Verificando instalación...
python -c "import asyncio, aiohttp, cryptography" >nul 2>&1
if errorlevel 1 goto error

echo.
echo ✅ Setup backend terminado
echo 🚀 Para iniciar: python scripts/start_multinode_network.py
goto end

:wallet_setup
echo.
echo ========================================
echo SETUP WALLET
echo ========================================
echo.
echo [1/3] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Node.js no encontrado
    echo 💡 Descarga desde: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js encontrado:
node --version
echo.

echo [2/3] Instalando dependencias...
cd wallet
call npm install
if errorlevel 1 goto error_wallet

echo [3/3] Compilando wallet...
call npm run build
if errorlevel 1 goto error_wallet
cd ..

echo.
echo ✅ Setup wallet terminado
echo 🚀 Para iniciar: cd wallet && npm start
goto end

:verify_system
echo.
echo ========================================
echo VERIFICACION DEL SISTEMA
echo ========================================
echo.

echo Verificando Python...
python --version
if errorlevel 1 (
    echo ❌ Python no disponible
    goto end
)
echo ✅ Python OK
echo.

echo Verificando pip...
pip --version
if errorlevel 1 (
    echo ❌ pip no disponible
    goto end
)
echo ✅ pip OK
echo.

echo Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js no disponible
) else (
    node --version
    echo ✅ Node.js OK
)
echo.

echo Verificando dependencias Python...
python -c "import asyncio, aiohttp, cryptography" >nul 2>&1
if errorlevel 1 (
    echo ❌ Dependencias Python faltantes
    echo 💡 Ejecuta: pip install -r requirements.txt
) else (
    echo ✅ Dependencias Python OK
)
echo.

echo Verificando dependencias avanzadas...
python -c "import torch, transformers" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Dependencias IA no disponibles (opcional)
    echo    Esto es normal si no tienes GPU compatible
) else (
    echo ✅ Dependencias IA OK
)
echo.

if exist "wallet\node_modules" (
    echo ✅ Dependencias Wallet OK
) else (
    echo ❌ Dependencias Wallet faltantes
    echo 💡 Ejecuta: cd wallet && npm install
)
echo.

echo ========================================
echo VERIFICACION COMPLETADA
echo ========================================
goto end

:clean_install
echo.
echo ========================================
echo LIMPIEZA E INSTALACION COMPLETA
echo ========================================
echo.
echo ⚠️  Esto eliminará todas las dependencias instaladas
set /p confirm="¿Estas seguro? (s/n): "
if /i not "%confirm%"=="s" goto end

echo [1/6] Limpiando cache pip...
pip cache purge

echo [2/6] Limpiando node_modules...
if exist "wallet\node_modules" rmdir /s /q "wallet\node_modules"
if exist "wallet\build" rmdir /s /q "wallet\build"

echo [3/6] Instalando dependencias Python...
pip install -r requirements.txt
if errorlevel 1 goto error

echo [4/6] Instalando dependencias Wallet...
cd wallet
call npm install
if errorlevel 1 goto error_wallet

echo [5/6] Compilando wallet...
call npm run build
if errorlevel 1 goto error_wallet
cd ..

echo [6/6] Verificando instalación...
python -c "import asyncio, aiohttp, cryptography" >nul 2>&1
if errorlevel 1 goto error

echo.
echo ✅ Instalación limpia completada
goto end

:error
echo.
echo ❌ ERROR: Fallo en la instalación de dependencias Python
echo 💡 Posibles soluciones:
echo    1. Verifica tu conexión a Internet
echo    2. Ejecuta como administrador
echo    3. Actualiza pip: python -m pip install --upgrade pip
echo    4. Si tienes problemas con torch: pip install torch --index-url https://download.pytorch.org/whl/cpu
echo.
pause
exit /b 1

:error_wallet
echo.
echo ❌ ERROR: Fallo en la instalación del wallet
echo 💡 Posibles soluciones:
echo    1. Verifica que Node.js esté instalado: https://nodejs.org/
echo    2. Verifica tu conexión a Internet
echo    3. Limpia cache: npm cache clean --force
echo    4. Ejecuta como administrador
echo.
cd ..
pause
exit /b 1

:end
echo.
echo ========================================
echo SETUP COMPLETADO
echo ========================================
echo.
echo 📋 Próximos pasos:
echo.
echo 🎮 Para usar PlayerGold:
echo    1. Backend: python scripts/start_multinode_network.py
echo    2. Wallet: cd wallet && npm start
echo    3. O usa: wallet/build-complete.bat para builds
echo.
echo 📚 Documentación:
echo    - docs/TESTNET_SETUP_GUIDE.md - Configurar red testnet
echo    - docs/DEVELOPMENT_HISTORY.md - Historial del proyecto
echo    - README.md - Información general
echo.
echo 🎯 ¡Listo para gaming blockchain!
echo.
pause