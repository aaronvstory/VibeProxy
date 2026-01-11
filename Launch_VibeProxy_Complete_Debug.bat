@echo off
setlocal EnableDelayedExpansion

title VibeProxy + Droid CLI - Complete Launcher

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║         VibeProxy Complete Setup Launcher             ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo DEBUG MODE - Press any key at each step to continue
pause

echo.
echo Step 1: Checking if tunnel is running...
pause

powershell -Command "$tunnel = Get-NetTCPConnection -LocalPort 8317 -ErrorAction SilentlyContinue; if ($tunnel) { Write-Host 'Tunnel already active' -ForegroundColor Green; exit 0 } else { Write-Host 'No tunnel found' -ForegroundColor Yellow; exit 1 }"

echo ErrorLevel: %errorlevel%
pause

if %errorlevel% neq 0 (
    echo.
    echo Tunnel not running, would start it now...
    pause
) else (
    echo.
    echo Tunnel is active, skipping startup...
    pause
)

echo.
echo Script completed without crash!
pause
exit /b 0
