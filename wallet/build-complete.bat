@echo off
title PlayerGold Wallet - Build Completo
echo.
echo ===============================================
echo    PlayerGold Wallet - Build Completo
echo    Hecho por gamers para gamers
echo ===============================================
echo.

cd /d "%~dp0"

REM Mostrar opciones de build
echo Selecciona el tipo de build:
echo.
echo [1] Build Desarrollo (rapido)
echo [2] Build Produccion (completo)
echo [3] Build Portable (distribucion)
echo [4] Build Instalador Windows
echo [5] Limpiar todo y rebuild completo
echo.
set /p choice="Ingresa tu opcion (1-5): "

if "%choice%"=="1" goto dev_build
if "%choice%"=="2" goto prod_build
if "%choice%"=="3" goto portable_build
if "%choice%"=="4" goto installer_build
if "%choice%"=="5" goto clean_rebuild
echo Opcion invalida
pause
exit /b 1

:dev_build
echo.
echo ========================================
echo BUILD DESARROLLO
echo ========================================
echo.
echo [1/2] Instalando dependencias...
call npm install
if errorlevel 1 goto error

echo [2/2] Compilando React (desarrollo)...
call npm run build
if errorlevel 1 goto error

echo.
echo ✅ Build de desarrollo completado
echo 💡 Para probar: npm start
goto end

:prod_build
echo.
echo ========================================
echo BUILD PRODUCCION
echo ========================================
echo.
echo [1/3] Instalando dependencias...
call npm install
if errorlevel 1 goto error

echo [2/3] Compilando React (produccion)...
call npm run build
if errorlevel 1 goto error

echo [3/3] Compilando Electron...
call npm run electron-build
if errorlevel 1 goto error

echo.
echo ✅ Build de produccion completado
echo 📁 Archivos en: dist/windows/
goto end

:portable_build
echo.
echo ========================================
echo BUILD PORTABLE
echo ========================================
echo.
echo [1/4] Instalando dependencias...
call npm install
if errorlevel 1 goto error

echo [2/4] Compilando React...
call npm run build
if errorlevel 1 goto error

echo [3/4] Creando paquete portable...
call node scripts/build-portable.js
if errorlevel 1 goto error

echo [4/4] Validando paquete...
if exist "dist-portable\PlayerGold-Wallet.bat" (
    echo ✅ Paquete portable creado correctamente
    echo 📁 Ubicacion: dist-portable\
    echo 🚀 Para probar: cd dist-portable && PlayerGold-Wallet.bat
) else (
    echo ❌ Error: No se pudo crear el paquete portable
    goto error
)
goto end

:installer_build
echo.
echo ========================================
echo BUILD INSTALADOR WINDOWS
echo ========================================
echo.
echo ⚠️  NOTA: Requiere privilegios de administrador
echo.
set /p confirm="¿Continuar con el build del instalador? (s/n): "
if /i not "%confirm%"=="s" goto end

echo [1/4] Instalando dependencias...
call npm install
if errorlevel 1 goto error

echo [2/4] Compilando React...
call npm run build
if errorlevel 1 goto error

echo [3/4] Limpiando cache de electron-builder...
if exist "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign" (
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign" 2>nul
)

echo [4/4] Creando instalador NSIS...
set CSC_IDENTITY_AUTO_DISCOVERY=false
call npx electron-builder --win nsis --publish=never
if errorlevel 1 goto error

echo.
echo ✅ Instalador creado correctamente
echo 📁 Ubicacion: dist\windows\PlayerGold Wallet Setup 1.0.0.exe
goto end

:clean_rebuild
echo.
echo ========================================
echo LIMPIEZA Y REBUILD COMPLETO
echo ========================================
echo.
echo ⚠️  Esto eliminara todos los archivos compilados
set /p confirm="¿Estas seguro? (s/n): "
if /i not "%confirm%"=="s" goto end

echo [1/6] Limpiando directorios...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist dist-portable rmdir /s /q dist-portable
if exist node_modules rmdir /s /q node_modules

echo [2/6] Instalando dependencias frescas...
call npm install
if errorlevel 1 goto error

echo [3/6] Compilando React...
call npm run build
if errorlevel 1 goto error

echo [4/6] Compilando Electron...
call npm run electron-build
if errorlevel 1 goto error

echo [5/6] Creando paquete portable...
call node scripts/build-portable.js
if errorlevel 1 goto error

echo [6/6] Validando builds...
if exist "build\index.html" echo ✅ React build OK
if exist "dist\windows" echo ✅ Electron build OK  
if exist "dist-portable\PlayerGold-Wallet.bat" echo ✅ Portable build OK

echo.
echo ✅ Rebuild completo terminado
goto end

:error
echo.
echo ❌ ERROR: El build fallo
echo 💡 Posibles soluciones:
echo    1. Verifica tu conexion a Internet
echo    2. Ejecuta como administrador
echo    3. Limpia node_modules y reinstala: rmdir /s node_modules && npm install
echo    4. Verifica que tienes Node.js y npm actualizados
echo.
pause
exit /b 1

:end
echo.
echo ========================================
echo BUILD COMPLETADO
echo ========================================
echo.
echo 📋 Archivos disponibles:
if exist "build\index.html" echo   📱 React App: build\
if exist "dist\windows" echo   🖥️  Electron App: dist\windows\
if exist "dist-portable" echo   📦 Portable: dist-portable\
echo.
echo 🎮 ¡Listo para gaming!
echo.
pause