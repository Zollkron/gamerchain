@echo off
echo ============================================================
echo 🎮 INICIANDO PLAYERGOLD WALLET CON NODO GENESIS
echo ============================================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "package.json" (
    echo ❌ Error: No se encuentra package.json
    echo 💡 Ejecuta este script desde el directorio wallet/
    pause
    exit /b 1
)

echo 🔍 Verificando nodo génesis...
echo 💡 El nodo génesis debe estar corriendo en puerto 18080
echo.

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
echo 💡 Conectándose al nodo génesis en http://127.0.0.1:18080
echo 🚰 Prueba el botón "Solicitar Tokens Testnet" para ver el proceso completo
echo.

call npm start

echo.
echo 🛑 PlayerGold Wallet cerrado
pause