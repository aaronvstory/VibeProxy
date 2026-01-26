# Provider Switching Script for A0 and Image-Manipulator
# Usage: .\switch-provider.ps1 [-Provider vibeproxy|openrouter] [-Target a0|image|both]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("vibeproxy", "openrouter")]
    [string]$Provider,

    [Parameter(Mandatory=$false)]
    [ValidateSet("a0", "image", "both")]
    [string]$Target = "both"
)

$A0_SETTINGS = "C:\claude\agent-zero-data\tmp\settings.json"
$IMAGE_ENV = "C:\claude\image-manipulator-main\.env"
$VIBEPROXY_CONFIGS = "F:\claude\VibeProxy\configs"

function Get-CurrentProvider {
    param([string]$ConfigType)

    if ($ConfigType -eq "a0") {
        if (Test-Path $A0_SETTINGS) {
            $content = Get-Content $A0_SETTINGS -Raw | ConvertFrom-Json
            # Handle both old format (chat_model_api_base) and new format (chat.api_base)
            $apiBase = $content.chat_model_api_base
            if (-not $apiBase -and $content.chat -and $content.chat.api_base) {
                $apiBase = $content.chat.api_base
            }
            if ($apiBase -like "*host.docker.internal:8317*" -or $apiBase -like "*localhost:8317*") {
                return "vibeproxy"
            } elseif ($apiBase -like "*openrouter*") {
                return "openrouter"
            }
        }
    }
    elseif ($ConfigType -eq "image") {
        if (Test-Path $IMAGE_ENV) {
            $content = Get-Content $IMAGE_ENV -Raw
            if ($content -match "OCR_PROVIDER=vibeproxy") {
                return "vibeproxy"
            } elseif ($content -match "OCR_PROVIDER=openrouter") {
                return "openrouter"
            }
        }
    }
    return "unknown"
}

function Show-Status {
    Write-Host "`n=== Current Provider Status ===" -ForegroundColor Cyan

    $a0Provider = Get-CurrentProvider "a0"
    $imageProvider = Get-CurrentProvider "image"

    if ($a0Provider -eq "vibeproxy") {
        Write-Host "Agent Zero:        " -NoNewline
        Write-Host "VibeProxy" -ForegroundColor Green
    } elseif ($a0Provider -eq "openrouter") {
        Write-Host "Agent Zero:        " -NoNewline
        Write-Host "OpenRouter" -ForegroundColor Yellow
    } else {
        Write-Host "Agent Zero:        " -NoNewline
        Write-Host "Unknown" -ForegroundColor Red
    }

    if ($imageProvider -eq "vibeproxy") {
        Write-Host "Image-Manipulator: " -NoNewline
        Write-Host "VibeProxy" -ForegroundColor Green
    } elseif ($imageProvider -eq "openrouter") {
        Write-Host "Image-Manipulator: " -NoNewline
        Write-Host "OpenRouter" -ForegroundColor Yellow
    } else {
        Write-Host "Image-Manipulator: " -NoNewline
        Write-Host "Unknown" -ForegroundColor Red
    }

    # Check tunnel status
    $tunnel = netstat -an 2>$null | Select-String ":8317\s+.*LISTENING"
    if ($tunnel) {
        Write-Host "SSH Tunnel:        " -NoNewline
        Write-Host "Active" -ForegroundColor Green
    } else {
        Write-Host "SSH Tunnel:        " -NoNewline
        Write-Host "Inactive" -ForegroundColor Red
    }
    Write-Host ""
}

function Switch-A0Provider {
    param([string]$NewProvider)

    if ($NewProvider -eq "vibeproxy") {
        $configFile = "$VIBEPROXY_CONFIGS\a0-claude-sonnet-4-5-20250929.json"
    } else {
        $configFile = "$VIBEPROXY_CONFIGS\a0-openrouter.json"
    }

    if (-not (Test-Path $configFile)) {
        Write-Host "Error: Config file not found: $configFile" -ForegroundColor Red
        return $false
    }

    Copy-Item $configFile $A0_SETTINGS -Force
    Write-Host "A0 switched to $NewProvider" -ForegroundColor Green

    # Restart A0 container
    Write-Host "Restarting Agent Zero container..." -ForegroundColor Yellow
    docker restart agent-zero 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Agent Zero restarted successfully" -ForegroundColor Green
    } else {
        Write-Host "Note: Could not restart Agent Zero (container may not be running)" -ForegroundColor Yellow
    }

    return $true
}

function Switch-ImageProvider {
    param([string]$NewProvider)

    $envFile = "C:\claude\image-manipulator-main\.env.$NewProvider"

    if (-not (Test-Path $envFile)) {
        Write-Host "Error: Env file not found: $envFile" -ForegroundColor Red
        return $false
    }

    Copy-Item $envFile $IMAGE_ENV -Force
    Write-Host "Image-Manipulator switched to $NewProvider" -ForegroundColor Green
    Write-Host "Note: Restart the Electron app to apply changes" -ForegroundColor Yellow

    return $true
}

# Main logic
if (-not $Provider) {
    # Interactive mode - show menu
    Show-Status

    Write-Host "=== Switch Provider ===" -ForegroundColor Cyan
    Write-Host "[1] Switch to VibeProxy (both)"
    Write-Host "[2] Switch to OpenRouter (both)"
    Write-Host "[3] Switch A0 only"
    Write-Host "[4] Switch Image-Manipulator only"
    Write-Host "[5] Show status"
    Write-Host "[Q] Quit"
    Write-Host ""

    $choice = Read-Host "Select option"

    switch ($choice) {
        "1" {
            $Provider = "vibeproxy"
            $Target = "both"
        }
        "2" {
            $Provider = "openrouter"
            $Target = "both"
        }
        "3" {
            Write-Host "Switch A0 to [V]ibeProxy or [O]penRouter?" -ForegroundColor Cyan
            $subChoice = Read-Host
            $Provider = if ($subChoice -match "^[vV]") { "vibeproxy" } else { "openrouter" }
            $Target = "a0"
        }
        "4" {
            Write-Host "Switch Image-Manipulator to [V]ibeProxy or [O]penRouter?" -ForegroundColor Cyan
            $subChoice = Read-Host
            $Provider = if ($subChoice -match "^[vV]") { "vibeproxy" } else { "openrouter" }
            $Target = "image"
        }
        "5" {
            Show-Status
            exit 0
        }
        default {
            exit 0
        }
    }
}

# Execute switch
Write-Host "`nSwitching to $Provider..." -ForegroundColor Cyan

if ($Target -eq "a0" -or $Target -eq "both") {
    Switch-A0Provider $Provider
}

if ($Target -eq "image" -or $Target -eq "both") {
    Switch-ImageProvider $Provider
}

Write-Host ""
Show-Status
