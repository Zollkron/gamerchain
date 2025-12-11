@echo off
echo ============================================================
echo 🔄 REINICIANDO API WALLET PLAYERGOLD
echo ============================================================
echo.

echo 🛑 Deteniendo procesos Python existentes...
taskkill /F /IM python.exe >nul 2>&1

echo 🔍 Liberando puerto 18080...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18080') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo ⏳ Esperando 2 segundos...
timeout /t 2 /nobreak >nul

echo ✅ Puerto 18080 libre
echo.
echo 🚀 Iniciando API Wallet corregida...
echo 💡 Correcciones aplicadas:
echo    • Formato de transacciones corregido
echo    • Historial de transacciones mejorado
echo    • Validación de balances añadida
echo.

cd /d "%~dp0\.."
python scripts\wallet_api.py

pause