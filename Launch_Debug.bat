@echo off
setlocal EnableDelayedExpansion

echo.
echo ========================================================
echo     VibeProxy Debug Launcher - Verbose Mode
echo ========================================================
echo.

cd /d "%~dp0"

REM Show Python version
echo [DEBUG] Python Version:
python --version

echo.
echo [DEBUG] Environment:
echo    PWD: %CD%
echo    PYTHONPATH: %PYTHONPATH%

echo.
echo [DEBUG] Tunnel Status:
netstat -an | findstr 8317
if %errorlevel% neq 0 (
    echo    Port 8317 is NOT listening
) else (
    echo    Port 8317 is listening
)

echo.
echo [DEBUG] Testing VibeProxy connection...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8317/v1/models' -TimeoutSec 5 -UseBasicParsing; Write-Host '   Status: ' $response.StatusCode -ForegroundColor Green; Write-Host '   Models: ' ($response.Content | ConvertFrom-Json).data.Count 'available' } catch { Write-Host '   Error: ' $_.Exception.Message -ForegroundColor Red }"

echo.
echo [DEBUG] Docker Status:
docker ps --filter "name=agent" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>nul
if %errorlevel% neq 0 (
    echo    Docker not running or not accessible
)

echo.
echo [DEBUG] Config Files:
dir /b configs\*.json 2>nul
if %errorlevel% neq 0 (
    echo    No config files found
)

echo.
echo ========================================================
echo    Starting TUI with debug output...
echo ========================================================
echo.

REM Set debug environment and run
set PYTHONVERBOSE=1
set TEXTUAL_LOG=debug.log
python -m vibeproxy_manager

echo.
echo [DEBUG] Session ended. Check debug.log for TUI logs.
if exist debug.log (
    echo.
    echo Last 20 lines of debug.log:
    powershell -Command "Get-Content debug.log -Tail 20"
)

pause
