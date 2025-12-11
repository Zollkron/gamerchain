@echo off
echo ============================================================
echo 📊 MONITOR DEL NODO GENESIS
echo ============================================================
echo.
echo 💡 Este script muestra los logs del nodo génesis en tiempo real
echo 🚰 Usa el wallet en otra ventana y observa aquí el proceso blockchain
echo.
echo Presiona Ctrl+C para salir
echo.
echo ============================================================

:loop
timeout /t 2 /nobreak >nul
cls
echo ============================================================
echo 📊 MONITOR DEL NODO GENESIS - %date% %time%
echo ============================================================
echo.
echo 🔄 Actualizando logs...
echo.

REM Aquí mostraremos información del nodo
echo 🌐 Nodo Genesis corriendo en: http://127.0.0.1:18080
echo 📋 Presiona Ctrl+C para salir
echo.
echo ============================================================
echo 📝 ÚLTIMOS LOGS:
echo ============================================================

goto loop