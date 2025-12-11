@echo off
echo ============================================================
echo 🧪 TESTING FAUCET IN WALLET
echo ============================================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "package.json" (
    echo ❌ Error: No se encuentra package.json
    echo 💡 Ejecuta este script desde el directorio wallet/
    pause
    exit /b 1
)

echo 🔨 Compilando aplicación...
call npm run build
if errorlevel 1 (
    echo ❌ Error en la compilación
    pause
    exit /b 1
)

echo ✅ Compilación exitosa
echo.
echo 🎮 Iniciando PlayerGold Wallet para test del faucet...
echo 💡 Revisa la consola de Electron para logs del faucet
echo.

call npm start

echo.
echo 🛑 Test completado
pause