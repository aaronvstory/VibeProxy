@echo off
setlocal EnableDelayedExpansion

echo.
echo ========================================================
echo     VibeProxy Quick Start - Tunnel + TUI Launcher
echo ========================================================
echo.

cd /d "%~dp0"

REM Check if tunnel is already running
echo [1/3] Checking SSH tunnel status...
powershell -Command "try { $tunnel = Get-Process | Where-Object {$_.CommandLine -like '*ssh*8317*'} -ErrorAction SilentlyContinue; if ($tunnel) { Write-Host '   Tunnel already running (PID: ' $tunnel.Id ')' -ForegroundColor Green; exit 0 } else { exit 1 } } catch { exit 1 }"
if %errorlevel% == 0 goto :start_tui

REM Start tunnel in background
echo [2/3] Starting SSH tunnel...
start "VibeProxy SSH Tunnel" /min powershell -NoExit -ExecutionPolicy Bypass -Command ^
"& '%~dp0ssh-tunnel-vibeproxy.ps1'"

REM Wait for tunnel to establish
timeout /t 3 /nobreak >nul

REM Verify tunnel
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8317/v1/models' -TimeoutSec 5 -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host '   Tunnel active!' -ForegroundColor Green } } catch { Write-Host '   Warning: Tunnel may need more time' -ForegroundColor Yellow }"

:start_tui
echo.
echo [3/3] Starting VibeProxy Manager TUI...
echo.

REM Start TUI
python -m vibeproxy_manager

echo.
echo TUI closed. Tunnel is still running in background window.
pause
