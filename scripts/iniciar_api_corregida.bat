@echo off
echo ============================================================
echo 🌐 INICIANDO API WALLET CORREGIDA
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
echo 🚀 Iniciando API corregida...
echo 💡 Problemas solucionados:
echo    • Error 400 en transacciones: CORREGIDO
echo    • Historial mal formateado: CORREGIDO  
echo    • Imports conflictivos: SOLUCIONADO
echo.

cd /d "%~dp0\.."
python api_final.py

pause