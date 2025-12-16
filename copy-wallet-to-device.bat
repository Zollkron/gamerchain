@echo off
REM PlayerGold Wallet - Copia a Otro Dispositivo
REM Este script prepara la wallet para copiar a otro equipo

echo ========================================
echo PlayerGold Wallet - Copia a Dispositivo
echo ========================================
echo.
echo Este script prepara los archivos necesarios para
echo copiar la wallet a otro equipo (portátil, etc.)
echo.

REM Verificar que existe la wallet construida
if not exist "wallet\dist\windows\win-unpacked\PlayerGold-Wallet.exe" (
    echo ❌ ERROR: Wallet no encontrada
    echo    Primero ejecuta: build-wallet-from-scratch.bat
    pause
    exit /b 1
)

echo 🔍 Verificando archivos de la wallet...

REM Crear directorio temporal para la copia
set COPY_DIR=PlayerGold-Wallet-Portable
if exist "%COPY_DIR%" rmdir /s /q "%COPY_DIR%"
mkdir "%COPY_DIR%"

echo.
echo 📦 Preparando archivos para copia...

REM Copiar la wallet ejecutable completa
echo    • Copiando ejecutable y dependencias...
xcopy "wallet\dist\windows\win-unpacked\*" "%COPY_DIR%\" /E /I /H /Y >nul
if errorlevel 1 (
    echo ❌ ERROR: No se pudo copiar la wallet
    pause
    exit /b 1
)

REM Copiar certificado AES si existe
if exist "wallet\.AES_certificate\" (
    echo    • Copiando certificado AES...
    mkdir "%COPY_DIR%\.AES_certificate"
    xcopy "wallet\.AES_certificate\*" "%COPY_DIR%\.AES_certificate\" /E /I /H /Y >nul
    echo ✅ Certificado AES incluido
) else (
    echo ⚠️  Certificado AES no encontrado
    echo    La wallet funcionará pero sin conexión al coordinador
)

REM Crear archivo de instrucciones
echo    • Creando instrucciones...
(
echo PlayerGold Wallet - Instrucciones de Uso
echo ========================================
echo.
echo EJECUCIÓN:
echo • Ejecutar: PlayerGold-Wallet.exe
echo • No requiere instalación
echo • Funciona de forma portable
echo.
echo CERTIFICADO AES:
if exist "wallet\.AES_certificate\" (
echo • ✅ Incluido - Conexión al coordinador habilitada
echo • La wallet se conectará automáticamente al coordinador
echo • Podrá descubrir otros nodos en la red
) else (
echo • ❌ No incluido - Solo modo local
echo • Para habilitar coordinador:
echo   1. Obtener certificado del servidor
echo   2. Copiarlo a la carpeta .AES_certificate/
)
echo.
echo FUNCIONALIDADES:
echo • Gestión completa de wallets
echo • Transacciones seguras
echo • Interfaz moderna
echo • Descubrimiento automático de peers ^(con certificado^)
echo.
echo REQUISITOS:
echo • Windows 10/11
echo • No requiere instalación adicional
echo • Todas las dependencias incluidas
echo.
echo ¡Disfruta usando PlayerGold Wallet!
) > "%COPY_DIR%\INSTRUCCIONES.txt"

REM Crear script de ejecución rápida
(
echo @echo off
echo echo Iniciando PlayerGold Wallet...
echo start PlayerGold-Wallet.exe
) > "%COPY_DIR%\Ejecutar-Wallet.bat"

echo.
echo 📊 Calculando tamaño...
for /f "tokens=3" %%a in ('dir "%COPY_DIR%" /s /-c ^| find "bytes"') do set SIZE=%%a
set /a SIZE_MB=%SIZE% / 1048576

echo.
echo ========================================
echo ✅ PREPARACIÓN COMPLETADA
echo ========================================

echo.
echo 📁 Directorio creado: %COPY_DIR%\
echo 📊 Tamaño total: ~%SIZE_MB% MB
echo.
echo 📋 Contenido preparado:
echo    • PlayerGold-Wallet.exe (Ejecutable principal)
echo    • Todas las dependencias necesarias
if exist "wallet\.AES_certificate\" (
echo    • Certificado AES (Conexión al coordinador)
) else (
echo    • Sin certificado AES (Solo modo local)
)
echo    • INSTRUCCIONES.txt (Guía de uso)
echo    • Ejecutar-Wallet.bat (Acceso rápido)
echo.

echo 💡 PRÓXIMOS PASOS:
echo.
echo 1. COPIAR A OTRO EQUIPO:
echo    • Copiar toda la carpeta: %COPY_DIR%\
echo    • Usar USB, red compartida, o cualquier método
echo.
echo 2. EN EL OTRO EQUIPO:
echo    • Extraer la carpeta a cualquier ubicación
echo    • Ejecutar: PlayerGold-Wallet.exe
echo    • O usar: Ejecutar-Wallet.bat
echo.
echo 3. PARA HABILITAR COORDINADOR (Opcional):
echo    • Si no tienes certificado AES:
echo      - Generar en servidor: sudo python3 scripts/setup_coordinator_aes_certificate.py
echo      - Copiar certificado a .AES_certificate/
echo.

echo 🎯 VENTAJAS DE ESTA VERSIÓN:
echo    • Completamente portable
echo    • No requiere instalación
echo    • Todas las dependencias incluidas
echo    • Funciona en cualquier Windows 10/11
echo    • Certificado AES incluido (si estaba disponible)
echo.

echo ✅ ¡Lista para copiar a otro equipo!
echo.
pause