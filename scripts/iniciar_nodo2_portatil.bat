@echo off
REM Script para iniciar el Nodo 2 en el portátil
REM Debe ejecutarse en el portátil (192.168.1.132)

echo ============================================================
echo 🖥️  INICIANDO NODO 2 TESTNET (PORTÁTIL)
echo ============================================================
echo.

REM Verificar si se ejecuta como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Ejecutándose como Administrador
) else (
    echo ❌ ERROR: Este script debe ejecutarse como Administrador
    echo.
    echo 💡 Clic derecho en el archivo y seleccionar "Ejecutar como administrador"
    pause
    exit /b 1
)

echo.
echo 🔧 Paso 1: Configurando firewall en portátil...
call scripts\configurar_firewall_testnet.bat

echo.
echo 🔍 Paso 2: Verificando conectividad...
python scripts\diagnostico_red_testnet.py

echo.
echo 🖥️  Paso 3: Iniciando Nodo 2...
echo.
echo ⚠️  IMPORTANTE: 
echo    - Asegúrate de que el Nodo 1 esté ejecutándose en 192.168.1.129
echo    - Este nodo se conectará automáticamente al Nodo 1
echo.

set /p continuar="¿Continuar con el inicio del Nodo 2? (S/N): "
if /i "%continuar%" neq "S" (
    echo Operación cancelada por el usuario
    pause
    exit /b 0
)

echo.
echo 🚀 Iniciando Nodo 2 (Portátil)...
scripts\start_node2_testnet.bat

echo.
echo ✅ Nodo 2 finalizado
pause