@echo off
REM ============================================================
REM  Admin Launcher Template - UAC Elevation Pattern
REM  Use this template for scripts that need administrator rights
REM ============================================================

REM Check for admin rights
net session >nul 2>&1
if %errorlevel% == 0 goto :admin

REM Not admin - relaunch with elevation
echo Requesting administrator privileges...
powershell -Command "Start-Process cmd -ArgumentList '/c %~f0' -Verb RunAs"
exit /b

:admin
REM === ADMIN CODE BELOW THIS LINE ===

echo.
echo Running with Administrator privileges
echo.

cd /d "%~dp0"

REM Example: Windows Terminal with PowerShell script
where wt.exe >nul 2>&1
if %errorlevel% == 0 (
    REM Windows Terminal available - use it
    echo Launching in Windows Terminal...
    wt.exe -p "Windows PowerShell" powershell -NoExit -ExecutionPolicy Bypass -Command "Write-Host 'Admin session active' -ForegroundColor Green; Write-Host 'Replace this with your script'; pause"
) else (
    REM Fallback to regular PowerShell
    echo Launching in PowerShell...
    powershell -NoExit -ExecutionPolicy Bypass -Command "Write-Host 'Admin session active' -ForegroundColor Green; Write-Host 'Replace this with your script'; pause"
)

REM To use with a specific script, replace the Write-Host commands with:
REM   wt.exe -p "Windows PowerShell" powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0YOUR_SCRIPT.ps1"
REM   or
REM   powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0YOUR_SCRIPT.ps1"
