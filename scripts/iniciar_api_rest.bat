@echo off
echo ============================================================
echo 🌐 INICIANDO API REST PLAYERGOLD
echo ============================================================
echo.

echo 🔍 Verificando si puerto 18080 está libre...
netstat -ano | findstr :18080 >nul
if %errorLevel% == 0 (
    echo ❌ Puerto 18080 está ocupado
    echo 🔧 Liberando puerto...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18080') do (
        taskkill /PID %%a /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)

echo ✅ Puerto 18080 libre
echo.
echo 🚀 Iniciando API REST en puerto 18080...
echo 💡 Las wallets podrán conectarse a http://localhost:18080
echo.

cd /d "%~dp0\.."
python scripts\start_api_only.py

pause