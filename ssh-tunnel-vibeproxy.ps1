<#
.SYNOPSIS
    Auto-reconnecting SSH tunnel for VibeProxy with password storage

.DESCRIPTION
    Creates an SSH tunnel from Windows to MacBook running VibeProxy.
    Automatically reconnects if connection drops. Password stored in config.

.PARAMETER MacUser
    Your username on the MacBook (default: danielba)

.PARAMETER MacIP
    Your MacBook's local IP address (default: 192.168.50.70)

.PARAMETER Password
    SSH password (if not provided, will read from config or prompt)

.NOTES
    Port: Windows localhost:8317 → Mac localhost:8317
    Keep this window open while using Factory Droid!
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$MacUser,

    [Parameter(Mandatory=$false)]
    [string]$MacIP,

    [Parameter(Mandatory=$false)]
    [int]$LocalPort,

    [Parameter(Mandatory=$false)]
    [int]$RemotePort,

    [Parameter(Mandatory=$false)]
    [string]$Password,

    [Parameter(Mandatory=$false)]
    [switch]$NoAutoReconnect
)

# Configuration
$ConfigPath = Join-Path $PSScriptRoot "vibeproxy-config.json"
$DefaultConfig = [pscustomobject]@{
    MacUser = "danielba"
    MacIP = "192.168.50.70"
    LocalPort = 8317
    RemotePort = 8317
    SSHPassword = ""
}

# Load or create config
function Get-Config {
    $config = [pscustomobject]@{
        MacUser = $DefaultConfig.MacUser
        MacIP = $DefaultConfig.MacIP
        LocalPort = $DefaultConfig.LocalPort
        RemotePort = $DefaultConfig.RemotePort
        SSHPassword = $DefaultConfig.SSHPassword
    }
    if (Test-Path $ConfigPath) {
        try {
            $fileConfig = Get-Content $ConfigPath -Raw | ConvertFrom-Json
            if ($fileConfig) {
                foreach ($prop in $fileConfig.PSObject.Properties) {
                    $config | Add-Member -NotePropertyName $prop.Name -NotePropertyValue $prop.Value -Force
                }
            }
        } catch {
            # Ignore parse errors and use defaults.
        }
    }
    return $config
}

function Save-Config {
    param($Config)
    $Config | ConvertTo-Json | Set-Content $ConfigPath
}

# Load config and apply defaults
$config = Get-Config
if ([string]::IsNullOrWhiteSpace($MacUser)) { $MacUser = $config.MacUser }
if ([string]::IsNullOrWhiteSpace($MacIP)) { $MacIP = $config.MacIP }
if (-not $LocalPort -or $LocalPort -le 0) { $LocalPort = [int]$config.LocalPort }
if (-not $RemotePort -or $RemotePort -le 0) { $RemotePort = [int]$config.RemotePort }

$passwordUpdated = $false

# Get password
if ([string]::IsNullOrWhiteSpace($Password)) {
    $savedPassword = $config.SSHPassword
    if ([string]::IsNullOrWhiteSpace($savedPassword)) {
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host "                   VibeProxy SSH Tunnel - Auto-Reconnect                       " -ForegroundColor Cyan
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host ""
        $securePassword = Read-Host "Enter SSH password for $MacUser@$MacIP" -AsSecureString
        $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword))

        # Save password
        $passwordUpdated = $true
        Write-Host "✓ Password saved for future sessions" -ForegroundColor Green
    } else {
        $Password = $savedPassword
    }
} else {
    $passwordUpdated = $true
}

# Persist config updates if needed
$updated = $false
if ($config.MacUser -ne $MacUser) { $config.MacUser = $MacUser; $updated = $true }
if ($config.MacIP -ne $MacIP) { $config.MacIP = $MacIP; $updated = $true }
if ($config.LocalPort -ne $LocalPort) { $config.LocalPort = $LocalPort; $updated = $true }
if ($config.RemotePort -ne $RemotePort) { $config.RemotePort = $RemotePort; $updated = $true }
if ($passwordUpdated -or ($config.SSHPassword -ne $Password)) { $config.SSHPassword = $Password; $updated = $true }

if ($updated -or -not (Test-Path $ConfigPath)) {
    Save-Config $config
}

# Banner
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                   VibeProxy SSH Tunnel - Auto-Reconnect                       " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  🔌 Configuration:" -ForegroundColor White
Write-Host "     Mac Target      : $MacUser@$MacIP" -ForegroundColor Gray
Write-Host "     Local Port      : $LocalPort" -ForegroundColor Gray
Write-Host "     Remote Port     : $RemotePort" -ForegroundColor Gray
Write-Host "     Auto-Reconnect  : $(-not $NoAutoReconnect)" -ForegroundColor Gray
Write-Host "     Password        : (saved)" -ForegroundColor Gray
Write-Host ""
Write-Host "  💡 Usage Tips:" -ForegroundColor Yellow
Write-Host "     • Keep this window OPEN while using VibeProxy, Factory Droid, or Agent Zero" -ForegroundColor Gray
Write-Host "     • Press Ctrl+C to disconnect" -ForegroundColor Gray
Write-Host "     • Test connection: curl http://localhost:8317/health" -ForegroundColor Gray
Write-Host ""

# Check if SSH is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ERROR: SSH not found!" -ForegroundColor Red
    Write-Host "   Install OpenSSH client (Windows 10/11 includes it)" -ForegroundColor Yellow
    exit 1
}

# Check if port is already in use
$PortInUse = Get-NetTCPConnection -LocalPort $LocalPort -ErrorAction SilentlyContinue
if ($PortInUse) {
    Write-Host "⚠️  WARNING: Port $LocalPort is already in use!" -ForegroundColor Yellow
    Write-Host "   Process: $($PortInUse.OwningProcess)" -ForegroundColor Gray
    Write-Host ""
    $Response = Read-Host "Kill existing process and continue? (y/n)"
    if ($Response -eq 'y') {
        Stop-Process -Id $PortInUse.OwningProcess -Force
        Write-Host "✅ Process killed" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } else {
        Write-Host "❌ Exiting..." -ForegroundColor Red
        exit 1
    }
}

# Check if plink is available (PuTTY's SSH client - better for password auth)
$usePlink = $false
$plinkPath = $null
$plinkLocations = @(
    "C:\Program Files\PuTTY\plink.exe",
    "C:\Program Files (x86)\PuTTY\plink.exe",
    "$env:ProgramFiles\PuTTY\plink.exe",
    "${env:ProgramFiles(x86)}\PuTTY\plink.exe"
)

foreach ($loc in $plinkLocations) {
    if (Test-Path $loc) {
        $plinkPath = $loc
        $usePlink = $true
        break
    }
}

# Connection attempt counter
$AttemptCount = 0
$LastConnectTime = Get-Date

# Main connection loop
while ($true) {
    $AttemptCount++
    $Timestamp = Get-Date -Format 'HH:mm:ss'

    try {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "Attempt #$AttemptCount - Connecting..." -ForegroundColor Green

        if ($usePlink) {
            # Use plink with -pw parameter (PuTTY syntax, not OpenSSH)
            & $plinkPath -ssh -batch `
                -hostkey "SHA256:5XgC3h/+waae885A5/IORHon1HPf3QLQXbF84V+mj0Y" `
                -L "${LocalPort}:localhost:${RemotePort}" `
                -pw "$Password" `
                "${MacUser}@${MacIP}" -N
        } else {
            # Fallback to sshpass if available, otherwise prompt
            if (Get-Command sshpass -ErrorAction SilentlyContinue) {
                sshpass -p "$Password" ssh `
                    -o "ServerAliveInterval=60" `
                    -o "ServerAliveCountMax=3" `
                    -o "StrictHostKeyChecking=no" `
                    -o "UserKnownHostsFile=/dev/null" `
                    -o "ExitOnForwardFailure=yes" `
                    -L "${LocalPort}:localhost:${RemotePort}" `
                    "${MacUser}@${MacIP}" -N
            } else {
                # Regular SSH (will prompt for password each time)
                ssh -o "ServerAliveInterval=60" `
                    -o "ServerAliveCountMax=3" `
                    -o "StrictHostKeyChecking=no" `
                    -o "UserKnownHostsFile=/dev/null" `
                    -o "ExitOnForwardFailure=yes" `
                    -L "${LocalPort}:localhost:${RemotePort}" `
                    "${MacUser}@${MacIP}" -N
            }
        }

    } catch {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "❌ Connection error: $_" -ForegroundColor Red
    }

    # Connection ended (either error or user killed it)
    $CurrentTime = Get-Date
    $Duration = ($CurrentTime - $LastConnectTime).TotalSeconds

    if ($Duration -lt 5) {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "⚠️  Connection failed immediately!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  ───────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
        Write-Host "  Possible issues:" -ForegroundColor Yellow
        Write-Host "    1. Mac IP wrong or unreachable: $MacIP" -ForegroundColor Gray
        Write-Host "    2. SSH not enabled on Mac" -ForegroundColor Gray
        Write-Host "    3. Firewall blocking connection" -ForegroundColor Gray
        Write-Host "    4. Wrong username: $MacUser" -ForegroundColor Gray
        Write-Host "    5. Wrong password (delete vibeproxy-config.json to re-enter)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Verify on Mac:" -ForegroundColor Cyan
        Write-Host "    • System Settings → Sharing → Remote Login = ON" -ForegroundColor Gray
        Write-Host "    • Terminal: ipconfig getifaddr en0" -ForegroundColor Gray
        Write-Host "  ───────────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
        Write-Host ""
    } else {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "🔌 Connection lost after $([math]::Round($Duration))s" -ForegroundColor Yellow
    }

    # Exit if auto-reconnect disabled
    if ($NoAutoReconnect) {
        Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "Auto-reconnect disabled. Exiting." -ForegroundColor Red
        exit 0
    }

    # Wait before reconnecting
    Write-Host "[$Timestamp] " -NoNewline -ForegroundColor Gray
    Write-Host "🔄 Reconnecting in 5 seconds... (Ctrl+C to cancel)" -ForegroundColor Cyan
    Start-Sleep -Seconds 5

    $LastConnectTime = Get-Date
}
