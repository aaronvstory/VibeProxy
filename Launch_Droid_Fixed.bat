@echo off
REM VibeProxy Droid CLI Launcher - Fixes flickering/disappearing text issue
REM This launcher ensures proper terminal rendering for Factory Droid

setlocal EnableDelayedExpansion

REM Check if tunnel is running
powershell -Command "$tunnel = Get-NetTCPConnection -LocalPort 8317 -ErrorAction SilentlyContinue; if (-not $tunnel) { Write-Host '❌ VibeProxy tunnel not running!' -ForegroundColor Red; Write-Host '   Run start-vibeproxy-tunnel.bat first' -ForegroundColor Yellow; exit 1 }"
if %errorlevel% neq 0 (
    echo.
    pause
    exit /b 1
)

REM Set environment variables for proper rendering
set TERM=xterm-256color
set COLORTERM=truecolor
set FORCE_COLOR=1

REM Disable Windows Console legacy mode (fixes flickering)
set ENABLE_VIRTUAL_TERMINAL_PROCESSING=1

REM Check if Windows Terminal is available
where wt.exe >nul 2>&1
if %errorlevel% == 0 (
    REM Launch in Windows Terminal with proper profile
    wt.exe -p "Windows PowerShell" cmd /k "cd /d "%CD%" && set TERM=xterm-256color && set COLORTERM=truecolor && C:\Users\d0nbxx\bin\droid.exe %*"
) else (
    REM Fallback to cmd with VT processing enabled
    echo ✅ VibeProxy tunnel active
    echo 🤖 Launching Droid CLI with fixed rendering...
    echo.

    REM Enable VT processing in current console
    powershell -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8"

    REM Launch Droid
    C:\Users\d0nbxx\bin\droid.exe %*
)
