# VibeProxy + Droid Launcher (PowerShell)
# Fixes terminal rendering issues

Write-Host ""
Write-Host "VibeProxy + Droid Launcher" -ForegroundColor Cyan
Write-Host ""

# Check tunnel
$tunnel = Get-NetTCPConnection -LocalPort 8317 -ErrorAction SilentlyContinue
if (-not $tunnel) {
    Write-Host "[*] Starting SSH tunnel..." -ForegroundColor Yellow
    $scriptPath = Join-Path $PSScriptRoot "ssh-tunnel-vibeproxy.ps1"
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`"" -WindowStyle Minimized
    Start-Sleep -Seconds 5
    Write-Host "[OK] Tunnel started" -ForegroundColor Green
} else {
    Write-Host "[OK] Tunnel already running" -ForegroundColor Green
}

# Test connection
Write-Host ""
Write-Host "[*] Testing VibeProxy..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8317/v1/models" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] VibeProxy responding" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: VibeProxy not responding" -ForegroundColor Red
    Write-Host "    Make sure VibeProxy app is running on Mac" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[*] Launching Droid (rendering fixes applied)..." -ForegroundColor Yellow
Write-Host ""

# Set console to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# Set environment variables for proper rendering
$env:TERM = "xterm-256color"
$env:COLORTERM = "truecolor"
$env:FORCE_COLOR = "1"
$env:NO_COLOR = $null

# Clear screen before starting Droid
Clear-Host

# Launch Droid directly in this PowerShell window
& "C:\Users\d0nbxx\bin\droid.exe"
