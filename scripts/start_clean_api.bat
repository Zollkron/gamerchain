@echo off
echo ============================================================
echo 🌐 INICIANDO API WALLET LIMPIA
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

echo 🚀 Copiando API a directorio temporal...
if not exist "%TEMP%\playergold_api" mkdir "%TEMP%\playergold_api"
copy "%~dp0\..\wallet_api_standalone.py" "%TEMP%\playergold_api\api.py" >nul

echo 🌐 Iniciando API desde directorio limpio...
cd /d "%TEMP%\playergold_api"
python api.py

pause