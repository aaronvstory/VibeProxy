@echo off
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║         VibeProxy + Droid - Simple Launcher           ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check tunnel
netstat -an | findstr ":8317" >nul
if errorlevel 1 (
    echo Starting tunnel...
    start /min powershell -ExecutionPolicy Bypass -File "%~dp0ssh-tunnel-vibeproxy.ps1"
    timeout /t 5 /nobreak >nul
) else (
    echo ✓ Tunnel already running
)

REM Set terminal environment
set TERM=xterm-256color
set COLORTERM=truecolor

echo.
echo Starting Droid CLI...
echo.

C:\Users\d0nbxx\bin\droid.exe

exit /b 0
