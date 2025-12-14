@echo off
title PlayerGold Wallet
echo.
echo PlayerGold Wallet - Starting...
echo.

echo Checking system requirements...

node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js found - OK

echo Creating data directories...
if not exist "data" mkdir data
if not exist "data\wallets" mkdir data\wallets

echo Setting environment variables...
set PLAYERGOLD_PORTABLE=true
set PLAYERGOLD_DATA_DIR=%cd%\data
set NODE_ENV=production

echo Starting wallet...
cd wallet
node_modules\.bin\electron . --portable --no-sandbox

pause