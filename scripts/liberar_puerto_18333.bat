@echo off
REM Script para liberar el puerto 18333 si está ocupado
REM Debe ejecutarse como Administrador

echo ============================================================
echo 🔧 LIBERANDO PUERTO 18333 - PLAYERGOLD TESTNET
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
echo 🔍 Buscando procesos que usan el puerto 18333...

REM Buscar qué proceso está usando el puerto 18333
netstat -ano | findstr :18333
if %errorLevel% == 0 (
    echo.
    echo ⚠️  Puerto 18333 está siendo usado por los procesos mostrados arriba
    echo.
    
    REM Obtener PIDs que usan el puerto 18333
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18333') do (
        echo 🔍 Proceso encontrado con PID: %%a
        
        REM Obtener nombre del proceso
        for /f "tokens=1" %%b in ('tasklist /fi "pid eq %%a" /fo csv /nh ^| findstr /v "INFO:"') do (
            set "proceso_nombre=%%b"
            set "proceso_nombre=!proceso_nombre:"=!"
            echo 📋 Nombre del proceso: !proceso_nombre!
            
            REM Preguntar si terminar el proceso
            set /p terminar="¿Terminar proceso !proceso_nombre! (PID: %%a)? (S/N): "
            if /i "!terminar!" == "S" (
                echo 🔄 Terminando proceso %%a...
                taskkill /PID %%a /F
                if !errorLevel! == 0 (
                    echo ✅ Proceso %%a terminado exitosamente
                ) else (
                    echo ❌ Error terminando proceso %%a
                )
            ) else (
                echo ⏭️  Proceso %%a no terminado
            )
        )
        echo.
    )
) else (
    echo ✅ Puerto 18333 está libre
)

echo.
echo 🔍 Verificando estado final del puerto 18333...
netstat -ano | findstr :18333
if %errorLevel% == 0 (
    echo ⚠️  Puerto 18333 aún está ocupado
    echo.
    echo 💡 Opciones adicionales:
    echo    1. Reiniciar la máquina
    echo    2. Cambiar puerto en configuración
    echo    3. Identificar manualmente el proceso problemático
) else (
    echo ✅ Puerto 18333 ahora está libre
    echo.
    echo 🚀 Puedes iniciar el nodo testnet:
    echo    scripts\start_node1_testnet.bat
)

echo.
echo 📋 Información adicional:
echo    - Si el problema persiste, puede ser un proceso del sistema
echo    - Considera usar un puerto diferente (ej: 18334)
echo    - O reinicia la máquina para limpiar todos los procesos
echo.

pause