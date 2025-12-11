@echo off
echo ============================================================
echo 🎮 INICIANDO PLAYERGOLD WALLET
echo ============================================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "package.json" (
    echo ❌ Error: No se encuentra package.json
    echo 💡 Ejecuta este script desde el directorio wallet/
    pause
    exit /b 1
)

echo 🔍 Verificando dependencias...
if not exist "node_modules" (
    echo 📦 Instalando dependencias...
    call npm install
    if errorlevel 1 (
        echo ❌ Error instalando dependencias
        pause
        exit /b 1
    )
)

echo 🧹 Limpiando caché anterior...
if exist "build" rmdir /s /q "build"
if exist "node_modules\.cache" rmdir /s /q "node_modules\.cache"

echo 🔨 Compilando aplicación...
call npm run build
if errorlevel 1 (
    echo ❌ Error en la compilación
    pause
    exit /b 1
)

echo ✅ Compilación exitosa
echo.
echo 🎮 Iniciando PlayerGold Wallet...
echo 💡 La wallet iniciará con sincronización automática
echo.

call npm start

echo.
echo 🛑 PlayerGold Wallet cerrado
pause