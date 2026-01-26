<#
.SYNOPSIS
    Test VibeProxy connection through SSH tunnel

.DESCRIPTION
    Verifies that the SSH tunnel is working and VibeProxy is accessible.

.EXAMPLE
    .\test-connection.ps1
#>

Write-Host "VibeProxy Connection Test" -ForegroundColor Cyan
Write-Host ""

$ConfigPath = Join-Path $PSScriptRoot "vibeproxy-config.json"
$Port = 8317
if (Test-Path $ConfigPath) {
    try {
        $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        if ($cfg.LocalPort) { $Port = [int]$cfg.LocalPort }
    } catch {
        # Use default port if config is invalid
    }
}
$TestsPassed = 0
$TotalTests = 3

# Test 1: Check if port is listening
Write-Host "Test 1/3: Checking if port $Port is listening..." -ForegroundColor Yellow
$PortListening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($PortListening) {
    Write-Host "✅ PASS: Port $Port is listening" -ForegroundColor Green
    Write-Host "   Process ID: $($PortListening.OwningProcess)" -ForegroundColor Gray
    $TestsPassed++
} else {
    Write-Host "❌ FAIL: Port $Port is NOT listening" -ForegroundColor Red
    Write-Host "   → Is SSH tunnel running? Run: .\ssh-tunnel-vibeproxy.ps1" -ForegroundColor Yellow
}
Write-Host ""

# Test 2: Check health or models endpoint
Write-Host "Test 2/3: Testing VibeProxy endpoint..." -ForegroundColor Yellow
$test2Passed = $false
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:$Port/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($Response.StatusCode -eq 200) {
        Write-Host "✅ PASS: Health endpoint responded" -ForegroundColor Green
        Write-Host "   Status: $($Response.StatusCode)" -ForegroundColor Gray
        Write-Host "   Content: $($Response.Content)" -ForegroundColor Gray
        $test2Passed = $true
    } else {
        Write-Host "⚠️  WARNING: Unexpected status code: $($Response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    if ($_.Exception.Message -like "*404*") {
        Write-Host "⚠️  Health endpoint returned 404" -ForegroundColor Yellow
    } else {
        Write-Host "❌ FAIL: Health endpoint unreachable" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
    }
}

if (-not $test2Passed) {
    try {
        $models = Invoke-RestMethod -Uri "http://localhost:$Port/v1/models" -TimeoutSec 5 -ErrorAction Stop
        $count = if ($models.data) { $models.data.Count } else { 0 }
        Write-Host "✅ PASS: Models endpoint responded ($count models)" -ForegroundColor Green
        $test2Passed = $true
    } catch {
        Write-Host "❌ FAIL: Models endpoint unreachable" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
        Write-Host "   → Check if VibeProxy is running on Mac" -ForegroundColor Yellow
    }
}

if ($test2Passed) { $TestsPassed++ }
Write-Host ""

# Test 3: Check if SSH process exists
Write-Host "Test 3/3: Checking SSH tunnel process..." -ForegroundColor Yellow
$TunnelProc = $null
if ($PortListening) {
    $TunnelProc = Get-Process -Id $PortListening.OwningProcess -ErrorAction SilentlyContinue
}
if ($TunnelProc) {
    Write-Host "✅ PASS: Tunnel process found" -ForegroundColor Green
    Write-Host "   PID: $($TunnelProc.Id) ($($TunnelProc.ProcessName))" -ForegroundColor Gray
    $TestsPassed++
} else {
    Write-Host "❌ FAIL: No tunnel process found" -ForegroundColor Red
    Write-Host "   → Start tunnel with: .\ssh-tunnel-vibeproxy.ps1" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "Results: $TestsPassed/$TotalTests tests passed" -ForegroundColor White
Write-Host ""

if ($TestsPassed -eq $TotalTests) {
    Write-Host "🎉 SUCCESS! VibeProxy is ready to use!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Configure Factory Droid: notepad ~/.factory/config.json" -ForegroundColor Gray
    Write-Host "  2. Start Droid: droid" -ForegroundColor Gray
    Write-Host "  3. Select model: /model" -ForegroundColor Gray
    exit 0
} elseif ($TestsPassed -gt 0) {
    Write-Host "⚠️  PARTIAL SUCCESS - Some tests failed" -ForegroundColor Yellow
    Write-Host "   Review errors above and troubleshoot" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "❌ FAILURE - All tests failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting checklist:" -ForegroundColor Yellow
    Write-Host "  ☐ SSH tunnel running? .\ssh-tunnel-vibeproxy.ps1" -ForegroundColor Gray
    Write-Host "  ☐ VibeProxy running on Mac?" -ForegroundColor Gray
    Write-Host "  ☐ Mac IP correct in vibeproxy-config.json (or ssh-tunnel-vibeproxy.ps1)?" -ForegroundColor Gray
    Write-Host "  ☐ SSH enabled on Mac? (System Settings → Sharing)" -ForegroundColor Gray
    exit 2
}
