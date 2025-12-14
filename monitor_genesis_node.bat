@echo off
title PlayerGold - Monitor de Red
echo ============================================================
echo 📊 MONITOR DE RED PLAYERGOLD
echo ============================================================
echo.
echo 💡 Este script monitorea el estado de la red PlayerGold
echo 🚰 Usa el wallet en otra ventana y observa aquí el estado
echo.
echo Presiona Ctrl+C para salir
echo.
echo ============================================================

:loop
timeout /t 5 /nobreak >nul
cls
echo ============================================================
echo 📊 MONITOR DE RED PLAYERGOLD - %date% %time%
echo ============================================================
echo.

REM Verificar si el nodo está corriendo
curl -s http://127.0.0.1:18080/api/v1/status >nul 2>&1
if errorlevel 1 (
    echo ❌ Nodo no disponible en http://127.0.0.1:18080
    echo 💡 Inicia el nodo con: python scripts/start_multinode_network.py
) else (
    echo ✅ Nodo activo en: http://127.0.0.1:18080
    
    REM Obtener estadísticas básicas
    echo.
    echo 📊 Estadísticas de Red:
    curl -s http://127.0.0.1:18080/api/v1/blockchain/info 2>nul | python -m json.tool 2>nul || echo "   Obteniendo datos..."
)

echo.
echo ============================================================
echo 📝 LOGS RECIENTES:
echo ============================================================

REM Mostrar logs si existen
if exist "logs\node.log" (
    tail -n 10 "logs\node.log" 2>nul || echo "   No hay logs disponibles"
) else (
    echo "   Archivo de logs no encontrado"
)

echo.
echo 📋 Presiona Ctrl+C para salir
echo ============================================================

goto loop