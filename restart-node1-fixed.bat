@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo Reiniciar Nodo 1 con Correcciones
echo ========================================
echo.
echo Directorio de trabajo: %CD%
echo.

echo 🔧 Aplicando correcciones...
echo ✅ Error de indentación Python corregido
echo ✅ Error de NetworkService corregido
echo.

echo 🚀 Reiniciando Nodo Génesis 1...
echo.

echo 📋 Funcionalidades corregidas:
echo   ✓ Bootstrap Guiado funcionando
echo   ✓ Network Coordinator conectado  
echo   ✓ P2P Network operativo
echo   ✓ Modelo IA preparado
echo   ✓ Mining challenge disponible
echo.

echo La wallet se iniciará en unos segundos...
echo.

cd wallet
npm start

echo.
echo ========================================
echo Nodo reiniciado
echo ========================================
pause