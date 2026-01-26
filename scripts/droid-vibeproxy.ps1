<#
.SYNOPSIS
    Run Droid CLI with VibeProxy models (headless automation).

.DESCRIPTION
    Complete automation wrapper that:
    1. Ensures SSH tunnel is running
    2. Syncs models to Droid (optional)
    3. Runs droid exec with specified model

.PARAMETER Model
    Model ID to use (e.g., claude-sonnet-4-5-20250929, gpt-5.2-codex)
    The 'custom:' prefix is added automatically.

.PARAMETER Prompt
    The prompt to send to the model.

.PARAMETER Auto
    Autonomy level: low, medium, high (default: medium)

.PARAMETER SyncFirst
    Sync models from VibeProxy before running (default: false)

.PARAMETER NoTunnel
    Skip tunnel check (assume already running)

.EXAMPLE
    .\droid-vibeproxy.ps1 -Model "claude-sonnet-4-5-20250929" -Prompt "analyze this code"

.EXAMPLE
    .\droid-vibeproxy.ps1 -Model "gpt-5.2-codex" -Prompt "fix bugs" -Auto high

.EXAMPLE
    cat app.py | .\droid-vibeproxy.ps1 -Model "claude-opus-4-5-20251101" -Prompt "explain"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Model,

    [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
    [string]$Prompt,

    [ValidateSet("low", "medium", "high")]
    [string]$Auto = "medium",

    [switch]$SyncFirst,
    [switch]$NoTunnel
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

# Step 1: Ensure tunnel is running
if (-not $NoTunnel) {
    Write-Host "Checking SSH tunnel..." -ForegroundColor Cyan

    $tunnelScript = Join-Path $ScriptDir "start-tunnel-headless.py"
    $checkResult = python $tunnelScript --check-only 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Starting SSH tunnel..." -ForegroundColor Yellow
        python $tunnelScript --timeout 30

        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Failed to start tunnel" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Tunnel is running" -ForegroundColor Green
    }
}

# Step 2: Sync models if requested
if ($SyncFirst) {
    Write-Host "Syncing models to Droid..." -ForegroundColor Cyan
    $syncScript = Join-Path $ScriptDir "sync-models-to-droid.py"
    python $syncScript

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to sync models" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Run droid exec
Write-Host "Running Droid with model: custom:$Model" -ForegroundColor Cyan

$droidArgs = @(
    "exec",
    "-m", "custom:$Model",
    "--auto", $Auto
)

# Handle piped input
if ($input) {
    $pipedContent = $input | Out-String
    $pipedContent | droid @droidArgs $Prompt
} else {
    droid @droidArgs $Prompt
}
