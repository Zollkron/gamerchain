@echo off
echo Limpiando cache de Electron y reconstruyendo...
cd /d "%~dp0"

REM Limpiar cache de Electron
if exist "%APPDATA%\playergold-wallet" (
    echo Eliminando cache de aplicacion...
    rmdir /s /q "%APPDATA%\playergold-wallet"
)

if exist "%APPDATA%\PlayerGold Wallet" (
    echo Eliminando cache de aplicacion...
    rmdir /s /q "%APPDATA%\PlayerGold Wallet"
)

REM Reconstruir aplicacion
echo Reconstruyendo aplicacion...
call npm run build

REM Iniciar aplicacion
echo Iniciando PlayerGold Wallet...
call npm start

pause