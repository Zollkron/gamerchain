@echo off
REM PlayerGold Wallet - Build Complete desde Cero
REM Este script genera la wallet completa desde cero en cualquier equipo
REM Actualizado para usar la estructura dist/ moderna

REM Habilitar logging detallado para diagnóstico
set LOGFILE=wallet-build-log.txt
echo [%DATE% %TIME%] Iniciando build de wallet > %LOGFILE%

REM Cambiar al directorio del script (soluciona problema de ejecución como admin)
echo [%DATE% %TIME%] Directorio inicial: %CD% >> %LOGFILE%
cd /d "%~dp0"
echo [%DATE% %TIME%] Directorio después de cd: %CD% >> %LOGFILE%

echo ========================================
echo PlayerGold Wallet - Build desde Cero
echo ========================================
echo.
echo 📁 Directorio de trabajo: %CD%
echo 📝 Log detallado: %LOGFILE%
echo.
echo Este script construye la wallet completa desde cero:
echo • Instala dependencias
echo • Construye la aplicación React
echo • Empaqueta con Electron
echo • Genera ejecutables listos para usar
echo.

REM Verificar que estamos en el directorio correcto
echo [%DATE% %TIME%] Verificando estructura del proyecto... >> %LOGFILE%
dir >> %LOGFILE% 2>&1

if not exist "wallet\package.json" (
    echo ❌ ERROR: No se encuentra wallet\package.json
    echo    Directorio actual: %CD%
    echo    Este script debe ejecutarse desde la raíz del proyecto PlayerGold
    echo    Asegúrate de que el archivo wallet\package.json existe
    echo.
    echo [%DATE% %TIME%] ERROR: wallet\package.json no encontrado en %CD% >> %LOGFILE%
    echo 💡 Solución:
    echo    1. Navega al directorio correcto del proyecto
    echo    2. Ejecuta el script desde ahí
    echo    3. O arrastra el script al directorio correcto
    echo.
    echo 📝 Revisa el archivo %LOGFILE% para más detalles
    pause
    exit /b 1
)

echo 🔍 Verificando requisitos del sistema...
echo [%DATE% %TIME%] Verificando Node.js y npm... >> %LOGFILE%

REM Verificar Node.js
echo Verificando Node.js...
node --version >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Node.js no está instalado
    echo    Descarga e instala Node.js desde: https://nodejs.org/
    echo [%DATE% %TIME%] ERROR: Node.js no encontrado >> %LOGFILE%
    echo.
    echo 📝 Revisa el archivo %LOGFILE% para más detalles
    pause
    exit /b 1
) else (
    echo ✅ Node.js: Detectado correctamente
    echo [%DATE% %TIME%] Node.js detectado correctamente >> %LOGFILE%
    node --version >> %LOGFILE% 2>&1
)

REM Verificar npm
echo Verificando npm...
echo [%DATE% %TIME%] Verificando npm... >> %LOGFILE%

REM Verificar npm de forma simple
npm --version >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ❌ ERROR: npm no está disponible
    echo [%DATE% %TIME%] ERROR: npm no encontrado >> %LOGFILE%
    echo.
    echo 📝 Revisa el archivo %LOGFILE% para más detalles
    pause
    exit /b 1
) else (
    echo ✅ npm: Detectado correctamente
    echo [%DATE% %TIME%] npm detectado correctamente >> %LOGFILE%
)

echo ✅ Requisitos del sistema verificados
echo [%DATE% %TIME%] Requisitos del sistema verificados >> %LOGFILE%

REM Pequeña pausa para asegurar que todo se procese correctamente
timeout /t 1 /nobreak >nul

REM Cambiar al directorio de la wallet
echo.
echo 📂 Cambiando al directorio wallet...
echo [%DATE% %TIME%] Cambiando al directorio wallet... >> %LOGFILE%
cd wallet
echo [%DATE% %TIME%] Directorio actual: %CD% >> %LOGFILE%

REM Verificar que el directorio wallet existe y tiene contenido
if not exist "package.json" (
    echo ❌ ERROR: No se encuentra package.json en el directorio wallet
    echo    Directorio actual: %CD%
    echo [%DATE% %TIME%] ERROR: package.json no encontrado en directorio wallet >> %LOGFILE%
    echo.
    echo 📝 Revisa el archivo %LOGFILE% para más detalles
    pause
    exit /b 1
)
echo ✅ Directorio wallet verificado

echo.
echo 🧹 Limpiando builds anteriores...
echo [%DATE% %TIME%] Limpiando directorios anteriores... >> %LOGFILE%
if exist "build" (
    echo    • Eliminando build/
    rmdir /s /q "build" >> %LOGFILE% 2>&1
)
if exist "dist" (
    echo    • Eliminando dist/
    rmdir /s /q "dist" >> %LOGFILE% 2>&1
)
if exist "node_modules\.cache" (
    echo    • Eliminando cache de node_modules
    rmdir /s /q "node_modules\.cache" >> %LOGFILE% 2>&1
)

echo.
echo 📦 Instalando dependencias de npm...
echo    Esto puede tomar varios minutos...
echo    💡 Si se cuelga aquí, presiona Ctrl+C y ejecuta: npm install --force
echo.
echo [%DATE% %TIME%] Iniciando npm install... >> %LOGFILE%
call npm install >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Falló la instalación de dependencias
    echo    Intenta ejecutar: npm install --force
    echo [%DATE% %TIME%] ERROR: npm install falló con código %errorlevel% >> %LOGFILE%
    echo.
    echo 📝 Revisa el archivo %LOGFILE% para más detalles
    pause
    exit /b 1
)
echo [%DATE% %TIME%] npm install completado exitosamente >> %LOGFILE%

echo.
echo ✅ Dependencias instaladas correctamente

echo.
echo 🔧 Construyendo aplicación React...
echo    Esto puede tomar varios minutos...
echo [%DATE% %TIME%] Iniciando npm run build... >> %LOGFILE%
call npm run build >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Falló la construcción de React
    echo    Revisa los errores anteriores
    echo [%DATE% %TIME%] ERROR: npm run build falló con código %errorlevel% >> %LOGFILE%
    echo.
    echo 📝 Revisa el archivo %LOGFILE% para más detalles
    pause
    exit /b 1
)
echo [%DATE% %TIME%] npm run build completado exitosamente >> %LOGFILE%

echo.
echo ✅ Aplicación React construida correctamente

echo.
echo 📱 Empaquetando con Electron Builder...
echo    Esto puede tomar varios minutos...
echo    💡 Si se cuelga aquí, es normal - Electron Builder es lento
echo.
echo [%DATE% %TIME%] Iniciando npm run electron-build... >> %LOGFILE%
call npm run electron-build >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Falló el empaquetado con Electron
    echo    Revisa los errores anteriores
    echo [%DATE% %TIME%] ERROR: npm run electron-build falló con código %errorlevel% >> %LOGFILE%
    echo.
    echo 📝 Revisa el archivo %LOGFILE% para más detalles
    pause
    exit /b 1
)
echo [%DATE% %TIME%] npm run electron-build completado exitosamente >> %LOGFILE%

echo.
echo ✅ Empaquetado completado exitosamente

REM Volver al directorio raíz
echo [%DATE% %TIME%] Volviendo al directorio raíz... >> %LOGFILE%
cd ..
echo [%DATE% %TIME%] Directorio actual: %CD% >> %LOGFILE%

echo.
echo 🔍 Verificando archivos generados...
echo [%DATE% %TIME%] Verificando archivos generados... >> %LOGFILE%
dir "wallet\dist" /s >> %LOGFILE% 2>&1

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
echo [%DATE% %TIME%] Build completado exitosamente >> %LOGFILE%
echo 📝 Log completo guardado en: %LOGFILE%
echo.
echo 🔧 DIAGNÓSTICO DE PROBLEMAS:
echo    Si el script se cerró inmediatamente:
echo    1. Revisa %LOGFILE% para ver dónde falló
echo    2. Asegúrate de tener Node.js instalado
echo    3. Ejecuta como administrador si es necesario
echo    4. Verifica que estás en el directorio correcto
echo.
pause