@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 🔧 CONFIGURAR DEPENDENCIAS NODO 2 (PORTÁTIL)
echo ========================================
echo.
echo 📦 Instalando dependencias de Python necesarias...
echo.

echo 1️⃣ Instalando dependencias básicas...
pip install base58
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error instalando base58
    goto :error
)
echo ✅ base58 instalado

echo.
echo 2️⃣ Instalando todas las dependencias del proyecto...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error instalando requirements.txt
    goto :error
)
echo ✅ requirements.txt instalado

echo.
echo 3️⃣ Instalando dependencias multinodo...
pip install -r requirements_multinode.txt
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error instalando requirements_multinode.txt
    goto :error
)
echo ✅ requirements_multinode.txt instalado

echo.
echo 4️⃣ Verificando instalación...
python -c "import base58; print('✅ base58 OK')"
python -c "import cryptography; print('✅ cryptography OK')"
python -c "import flask; print('✅ flask OK')"
python -c "import asyncio; print('✅ asyncio OK')"

echo.
echo ========================================
echo ✅ DEPENDENCIAS INSTALADAS CORRECTAMENTE
echo ========================================
echo.
echo 🚀 Ahora puedes ejecutar:
echo    start-node2-genesis.bat
echo.
goto :end

:error
echo.
echo ========================================
echo ❌ ERROR EN LA INSTALACIÓN
echo ========================================
echo.
echo 🔧 Soluciones posibles:
echo   1️⃣ Verificar que Python esté instalado
echo   2️⃣ Verificar que pip esté disponible
echo   3️⃣ Ejecutar como administrador
echo   4️⃣ Verificar conexión a internet
echo.

:end
pause