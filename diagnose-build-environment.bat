@echo off
REM PlayerGold Wallet - Diagnóstico del Entorno de Build
REM Este script ayuda a identificar problemas cuando build-wallet-from-scratch.bat falla

REM Cambiar al directorio del script
cd /d "%~dp0"

set DIAGFILE=diagnostico-build.txt
echo ========================================> %DIAGFILE%
echo PlayerGold Wallet - Diagnóstico Build>> %DIAGFILE%
echo Fecha: %DATE% %TIME%>> %DIAGFILE%
echo ========================================>> %DIAGFILE%
echo.>> %DIAGFILE%

echo ========================================
echo PlayerGold Wallet - Diagnóstico Build
echo ========================================
echo.
echo 🔍 Ejecutando diagnóstico completo...
echo 📝 Guardando resultados en: %DIAGFILE%
echo.

REM 1. Información del sistema
echo 1. INFORMACIÓN DEL SISTEMA>> %DIAGFILE%
echo ================================>> %DIAGFILE%
echo Directorio actual: %CD%>> %DIAGFILE%
echo Usuario: %USERNAME%>> %DIAGFILE%
echo Computadora: %COMPUTERNAME%>> %DIAGFILE%
echo Sistema: %OS%>> %DIAGFILE%
echo.>> %DIAGFILE%

echo ✓ Información del sistema recopilada

REM 2. Verificar estructura del proyecto
echo 2. ESTRUCTURA DEL PROYECTO>> %DIAGFILE%
echo ===============================>> %DIAGFILE%
echo Contenido del directorio actual:>> %DIAGFILE%
dir >> %DIAGFILE% 2>&1
echo.>> %DIAGFILE%

if exist "wallet" (
    echo ✓ Directorio wallet encontrado>> %DIAGFILE%
    echo Contenido de wallet/:>> %DIAGFILE%
    dir wallet >> %DIAGFILE% 2>&1
    echo.>> %DIAGFILE%
    
    if exist "wallet\package.json" (
        echo ✓ wallet\package.json encontrado>> %DIAGFILE%
        echo ✓ Estructura del proyecto correcta
    ) else (
        echo ❌ wallet\package.json NO encontrado>> %DIAGFILE%
        echo ❌ Estructura del proyecto incorrecta
    )
) else (
    echo ❌ Directorio wallet NO encontrado>> %DIAGFILE%
    echo ❌ No estás en el directorio correcto del proyecto
)
echo.>> %DIAGFILE%

echo ✓ Estructura del proyecto verificada

REM 3. Verificar Node.js
echo 3. VERIFICACIÓN DE NODE.JS>> %DIAGFILE%
echo ============================>> %DIAGFILE%
node --version >> %DIAGFILE% 2>&1
if errorlevel 1 (
    echo ❌ Node.js NO está instalado>> %DIAGFILE%
    echo ❌ Node.js no encontrado - INSTALAR REQUERIDO
) else (
    for /f "tokens=*" %%i in ('node --version 2^>nul') do (
        echo ✓ Node.js instalado: %%i>> %DIAGFILE%
        echo ✓ Node.js encontrado: %%i
    )
)
echo.>> %DIAGFILE%

REM 4. Verificar npm
echo 4. VERIFICACIÓN DE NPM>> %DIAGFILE%
echo =======================>> %DIAGFILE%
npm --version >> %DIAGFILE% 2>&1
if errorlevel 1 (
    echo ❌ npm NO está disponible>> %DIAGFILE%
    echo ❌ npm no encontrado - PROBLEMA CON NODE.JS
) else (
    for /f "tokens=*" %%i in ('npm --version 2^>nul') do (
        echo ✓ npm instalado: %%i>> %DIAGFILE%
        echo ✓ npm encontrado: %%i
    )
)
echo.>> %DIAGFILE%

echo ✓ Herramientas de desarrollo verificadas

REM 5. Verificar permisos
echo 5. VERIFICACIÓN DE PERMISOS>> %DIAGFILE%
echo =============================>> %DIAGFILE%
echo Intentando crear archivo de prueba...>> %DIAGFILE%
echo test > test_permisos.tmp 2>> %DIAGFILE%
if exist "test_permisos.tmp" (
    echo ✓ Permisos de escritura: OK>> %DIAGFILE%
    echo ✓ Permisos de escritura correctos
    del test_permisos.tmp >> %DIAGFILE% 2>&1
) else (
    echo ❌ Sin permisos de escritura>> %DIAGFILE%
    echo ❌ Permisos insuficientes - EJECUTAR COMO ADMINISTRADOR
)
echo.>> %DIAGFILE%

echo ✓ Permisos verificados

REM 6. Verificar espacio en disco
echo 6. VERIFICACIÓN DE ESPACIO>> %DIAGFILE%
echo ============================>> %DIAGFILE%
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do (
    set /a FREE_GB=%%a / 1073741824
    echo Espacio libre: !FREE_GB! GB>> %DIAGFILE%
    if !FREE_GB! LSS 5 (
        echo ❌ Espacio insuficiente ^(!FREE_GB! GB^) - MÍNIMO 5 GB>> %DIAGFILE%
        echo ❌ Espacio insuficiente: !FREE_GB! GB ^(mínimo 5 GB^)
    ) else (
        echo ✓ Espacio suficiente: !FREE_GB! GB>> %DIAGFILE%
        echo ✓ Espacio en disco suficiente: !FREE_GB! GB
    )
)
echo.>> %DIAGFILE%

echo ✓ Espacio en disco verificado

REM 7. Verificar builds anteriores
echo 7. BUILDS ANTERIORES>> %DIAGFILE%
echo =====================>> %DIAGFILE%
if exist "wallet\dist" (
    echo ✓ Directorio wallet\dist encontrado>> %DIAGFILE%
    echo Contenido de wallet\dist:>> %DIAGFILE%
    dir "wallet\dist" /s >> %DIAGFILE% 2>&1
    echo ✓ Builds anteriores encontrados
) else (
    echo ❌ No hay builds anteriores>> %DIAGFILE%
    echo ℹ️  No hay builds anteriores (normal en primera ejecución)
)
echo.>> %DIAGFILE%

if exist "wallet\node_modules" (
    echo ✓ Directorio wallet\node_modules encontrado>> %DIAGFILE%
    echo ✓ Dependencias npm previamente instaladas
) else (
    echo ❌ No hay node_modules>> %DIAGFILE%
    echo ℹ️  Dependencias npm no instaladas (normal en primera ejecución)
)
echo.>> %DIAGFILE%

echo ✓ Estado de builds verificado

REM Resumen final
echo.
echo ========================================
echo 📋 RESUMEN DEL DIAGNÓSTICO
echo ========================================
echo.

REM Leer y mostrar problemas críticos
findstr /C:"❌" %DIAGFILE% > nul
if not errorlevel 1 (
    echo 🚨 PROBLEMAS ENCONTRADOS:
    echo.
    findstr /C:"❌" %DIAGFILE%
    echo.
    echo 💡 SOLUCIONES RECOMENDADAS:
    echo.
    findstr /C:"Node.js NO está instalado" %DIAGFILE% > nul
    if not errorlevel 1 echo    • Instalar Node.js desde: https://nodejs.org/
    
    findstr /C:"wallet\package.json NO encontrado" %DIAGFILE% > nul
    if not errorlevel 1 echo    • Ejecutar desde el directorio raíz del proyecto PlayerGold
    
    findstr /C:"Sin permisos de escritura" %DIAGFILE% > nul
    if not errorlevel 1 echo    • Ejecutar como administrador
    
    findstr /C:"Espacio insuficiente" %DIAGFILE% > nul
    if not errorlevel 1 echo    • Liberar espacio en disco ^(mínimo 5 GB^)
    
    echo.
) else (
    echo ✅ ¡No se encontraron problemas críticos!
    echo    El entorno parece estar listo para el build.
    echo.
    echo 💡 Si build-wallet-from-scratch.bat sigue fallando:
    echo    1. Ejecuta como administrador
    echo    2. Revisa wallet-build-log.txt para errores específicos
    echo    3. Intenta npm install --force manualmente
    echo.
)

echo 📝 Diagnóstico completo guardado en: %DIAGFILE%
echo.
echo 🔧 PRÓXIMOS PASOS:
echo    1. Revisa los problemas encontrados arriba
echo    2. Aplica las soluciones recomendadas
echo    3. Ejecuta build-wallet-from-scratch.bat nuevamente
echo    4. Si sigue fallando, envía %DIAGFILE% para análisis
echo.

pause