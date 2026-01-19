@echo off
setlocal EnableDelayedExpansion

echo.
echo ========================================================
echo     VibeProxy Quick Start - Tunnel + TUI Launcher
echo ========================================================
echo.

cd /d "%~dp0"

REM Check if tunnel is already running by checking port 8317
echo [1/3] Checking SSH tunnel status...
netstat -an 2>nul | findstr "8317" | findstr "LISTENING ESTABLISHED" >nul 2>&1
if %errorlevel% == 0 (
    echo    Tunnel already active on port 8317
    goto :start_tui
)
echo    No tunnel detected, will start one...

REM Start tunnel in background
echo [2/3] Starting SSH tunnel...
start "VibeProxy SSH Tunnel" /min powershell -NoExit -ExecutionPolicy Bypass -Command ^
"& '%~dp0ssh-tunnel-vibeproxy.ps1'"

REM Wait for tunnel to establish
timeout /t 3 /nobreak >nul

REM Verify tunnel - try curl first, fall back to PowerShell if needed
where curl >nul 2>&1
if %errorlevel% == 0 (
    curl -s -o nul http://localhost:8317/v1/models --connect-timeout 5 >nul 2>&1
) else (
    powershell -Command "(Invoke-WebRequest -Uri 'http://localhost:8317/v1/models' -TimeoutSec 5 -UseBasicParsing).StatusCode" >nul 2>&1
)
if %errorlevel% == 0 (
    echo    Tunnel active!
) else (
    echo    Warning: Tunnel may need more time to connect
)

:start_tui
echo.
echo [3/3] Starting VibeProxy Manager TUI...
echo.

REM Start TUI
python -m vibeproxy_manager

echo.
echo TUI closed. Tunnel is still running in background window.
pause
