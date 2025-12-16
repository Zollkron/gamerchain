@echo off
REM PlayerGold Wallet - Build Complete desde Cero
REM Este script genera la wallet completa desde cero en cualquier equipo
REM Actualizado para usar la estructura dist/ moderna

echo ========================================
echo PlayerGold Wallet - Build desde Cero
echo ========================================
echo.
echo Este script construye la wallet completa desde cero:
echo • Instala dependencias
echo • Construye la aplicación React
echo • Empaqueta con Electron
echo • Genera ejecutables listos para usar
echo.

REM Verificar que estamos en el directorio correcto
if not exist "wallet\package.json" (
    echo ❌ ERROR: No se encuentra wallet\package.json
    echo    Ejecuta este script desde la raíz del proyecto PlayerGold
    pause
    exit /b 1
)

echo 🔍 Verificando requisitos del sistema...

REM Verificar Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Node.js no está instalado
    echo    Descarga e instala Node.js desde: https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: npm no está disponible
    pause
    exit /b 1
)

echo ✅ Node.js y npm detectados correctamente

REM Cambiar al directorio de la wallet
cd wallet

echo.
echo 🧹 Limpiando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "node_modules\.cache" rmdir /s /q "node_modules\.cache"

echo.
echo 📦 Instalando dependencias de npm...
echo    Esto puede tomar varios minutos...
call npm install
if errorlevel 1 (
    echo ❌ ERROR: Falló la instalación de dependencias
    echo    Intenta ejecutar: npm install --force
    pause
    exit /b 1
)

echo.
echo ✅ Dependencias instaladas correctamente

echo.
echo 🔧 Construyendo aplicación React...
call npm run build
if errorlevel 1 (
    echo ❌ ERROR: Falló la construcción de React
    echo    Revisa los errores anteriores
    pause
    exit /b 1
)

echo.
echo ✅ Aplicación React construida correctamente

echo.
echo 📱 Empaquetando con Electron Builder...
echo    Esto puede tomar varios minutos...
call npm run electron-build
if errorlevel 1 (
    echo ❌ ERROR: Falló el empaquetado con Electron
    echo    Revisa los errores anteriores
    pause
    exit /b 1
)

echo.
echo ✅ Empaquetado completado exitosamente

REM Volver al directorio raíz
cd ..

echo.
echo 🔍 Verificando archivos generados...

REM Verificar que se generaron los archivos
if exist "wallet\dist\windows\win-unpacked\PlayerGold-Wallet.exe" (
    echo ✅ Ejecutable portable: wallet\dist\windows\win-unpacked\PlayerGold-Wallet.exe
) else (
    echo ❌ No se encontró el ejecutable portable
)

if exist "wallet\dist\windows\PlayerGold Wallet Setup 1.0.0.exe" (
    echo ✅ Instalador: wallet\dist\windows\PlayerGold Wallet Setup 1.0.0.exe
) else (
    echo ❌ No se encontró el instalador
)

echo.
echo ========================================
echo ✅ BUILD COMPLETADO EXITOSAMENTE
echo ========================================

echo.
echo 📋 Archivos generados:
echo.
echo 🚀 EJECUTABLE PORTABLE (Recomendado):
echo    📁 wallet\dist\windows\win-unpacked\PlayerGold-Wallet.exe
echo    • No requiere instalación
echo    • Ejecutar directamente
echo    • Ideal para pruebas
echo.
echo 📦 INSTALADOR:
echo    📁 wallet\dist\windows\PlayerGold Wallet Setup 1.0.0.exe
echo    • Instala la aplicación en el sistema
echo    • Crea accesos directos
echo    • Ideal para uso permanente
echo.

echo 🔐 CERTIFICADO AES:
if exist "wallet\.AES_certificate\master_key.bin" (
    echo    ✅ Certificado AES encontrado: wallet\.AES_certificate\
    echo    • La wallet puede conectar al coordinador
    echo    • Comunicación cifrada habilitada
) else (
    echo    ❌ Certificado AES NO encontrado
    echo    • Para habilitar comunicación con coordinador:
    echo    • 1. Ejecutar en servidor: sudo python3 scripts/setup_coordinator_aes_certificate.py
    echo    • 2. Descargar paquete del servidor
    echo    • 3. Ejecutar: python3 scripts/install_wallet_aes_certificate.py [paquete]
)

echo.
echo 💡 PRÓXIMOS PASOS:
echo.
echo 1. PARA PRUEBAS RÁPIDAS:
echo    • Ejecutar: wallet\dist\windows\win-unpacked\PlayerGold-Wallet.exe
echo.
echo 2. PARA INSTALACIÓN PERMANENTE:
echo    • Ejecutar: wallet\dist\windows\PlayerGold Wallet Setup 1.0.0.exe
echo.
echo 3. PARA HABILITAR COORDINADOR (Opcional):
echo    • Copiar certificado AES desde otro equipo
echo    • O generar nuevo certificado en servidor
echo.

echo 🎯 FUNCIONALIDADES INCLUIDAS:
echo    • Gestión completa de wallets
echo    • Transacciones seguras
echo    • Integración con blockchain
echo    • Conexión automática al coordinador (con certificado)
echo    • Descubrimiento automático de peers
echo    • Interfaz moderna y fácil de usar
echo.

echo ✅ ¡Wallet lista para usar!
echo.
pause