@echo off
setlocal EnableDelayedExpansion

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║     VibeProxy SSH Tunnel - Auto-Connect Launcher      ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if tunnel is already running
powershell -Command "$tunnel = Get-Process | Where-Object {$_.CommandLine -like '*ssh*8317*'}; if ($tunnel) { Write-Host '✅ Tunnel already running (PID: ' $tunnel.Id ')' -ForegroundColor Green; exit 0 } else { exit 1 }"
if %errorlevel% == 0 (
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 0
)

REM Start tunnel in new window
echo 🔌 Starting SSH tunnel to Mac (192.168.50.70)...
echo.

start "VibeProxy SSH Tunnel" powershell -NoExit -ExecutionPolicy Bypass -Command ^
"& '%~dp0ssh-tunnel-vibeproxy.ps1'"

REM Wait for tunnel to establish
timeout /t 3 /nobreak >nul

REM Test connection
echo.
echo 🧪 Testing connection...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8317/v1/models' -TimeoutSec 5 -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host '✅ CONNECTION ACTIVE - VibeProxy is accessible!' -ForegroundColor Green } else { Write-Host '⚠️  Tunnel started but VibeProxy not responding' -ForegroundColor Yellow } } catch { Write-Host '⚠️  Tunnel started but connection test failed' -ForegroundColor Yellow; Write-Host '   Check that VibeProxy is running on Mac' -ForegroundColor Gray }"

echo.
echo 💡 Tunnel running in separate window. Close that window to disconnect.
echo.
pause
