@echo off
echo ============================================================
echo 🌐 INICIANDO API WALLET PLAYERGOLD
echo ============================================================
echo.

echo 🔍 Liberando puerto 18080 si está ocupado...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18080') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo ✅ Puerto 18080 libre
echo.
echo 🚀 Iniciando API Wallet...
echo 💡 Las wallets podrán conectarse sin problemas
echo.

cd /d "%~dp0\.."
python scripts\wallet_api.py

pause