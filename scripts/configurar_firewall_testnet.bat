@echo off
REM Script para configurar firewall de Windows para PlayerGold Testnet
REM Debe ejecutarse como Administrador

echo ============================================================
echo 🔥 Configurando Firewall para PlayerGold Testnet
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
echo 🔧 Agregando reglas de firewall para puerto 18333...

REM Regla de entrada (Inbound)
netsh advfirewall firewall add rule name="PlayerGold Testnet - Entrada" dir=in action=allow protocol=TCP localport=18333
if %errorLevel% == 0 (
    echo ✅ Regla de entrada agregada exitosamente
) else (
    echo ❌ Error agregando regla de entrada
)

REM Regla de salida (Outbound)
netsh advfirewall firewall add rule name="PlayerGold Testnet - Salida" dir=out action=allow protocol=TCP localport=18333
if %errorLevel% == 0 (
    echo ✅ Regla de salida agregada exitosamente
) else (
    echo ❌ Error agregando regla de salida
)

REM Regla adicional para conexiones remotas
netsh advfirewall firewall add rule name="PlayerGold Testnet - Remoto" dir=in action=allow protocol=TCP remoteport=18333
if %errorLevel% == 0 (
    echo ✅ Regla remota agregada exitosamente
) else (
    echo ❌ Error agregando regla remota
)

echo.
echo 🔍 Verificando reglas creadas...
netsh advfirewall firewall show rule name="PlayerGold Testnet - Entrada"
netsh advfirewall firewall show rule name="PlayerGold Testnet - Salida"
netsh advfirewall firewall show rule name="PlayerGold Testnet - Remoto"

echo.
echo ============================================================
echo 🎉 Configuración de firewall completada
echo ============================================================
echo.
echo 📋 Próximos pasos:
echo 1. Ejecutar este mismo script en la otra máquina (portátil)
echo 2. Iniciar los nodos testnet con los scripts .bat
echo 3. Los nodos deberían conectarse automáticamente
echo.
echo 🔍 Para verificar conectividad:
echo    python scripts\diagnostico_red_testnet.py
echo.

pause